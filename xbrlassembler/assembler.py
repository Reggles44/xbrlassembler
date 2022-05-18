import collections
import logging
import os
import re
import typing
from copy import copy
from functools import lru_cache
from io import TextIOWrapper

from bs4 import BeautifulSoup

from xbrlassembler.enums import XBRLType, FinancialStatement
from xbrlassembler.error import XBRLAssemblerFromDirectoryError
from xbrlassembler.utils import parse_datetime

logger = logging.getLogger('xbrlassembler')


class XBRLElement:
    """
    An element to represent a single point on a tree.
    Specific data values are geared towards xbrl relevent information
    While relational data is close to that of an XML tree element

    Args:
        :param uri: A unique identifier for this specific point

    Kwargs:
        :param label: Printable and readable identifier
        :param value: Data that sits on a specific point, mostly used for elements at the bottem of the tree
        :param ref: Reference data that gives context to the value
    """

    def __init__(self, uri, label='', value='', ref=''):
        """Constructor Method"""
        self.uri = uri.split("/")[-1]
        self.label = label
        self.ref = ref
        self.value = value

        self.date = None

        # Convert to float to remove any issues with comparing string representations of numbers
        try:
            self.value = float(value)
        except (TypeError, ValueError):
            self.value = value

        self.children = {}
        self.parent = None

    def __repr__(self):
        """
        :return: Returns a string representation of various aspects of the non relational data
        """
        return f"{self.uri} (label={self.label}, ref={self.ref}, value={self.value})"

    @lru_cache(maxsize=512)
    def head(self) -> "XBRLElement":
        """
        Return the top element of the tree
        :return: XBRLElement
        """
        return self if self.parent is None else self.parent.head()

    def add_child(self, new_child, order=-1):
        """
        Essential function for establishing relationships between elements.
        This function ensures that the relationship is set on both parent and child
        elements without duplication or Nones

        Args:
            :param new_child: An XBRLElement that is going to be under this element in the tree
            :param order: An optional argument to add order to child elements
        """
        if not isinstance(new_child, XBRLElement):
            return

        for child in self.children:
            if child.uri == new_child.uri and child.ref == new_child.ref:
                self.label = self.label or new_child.label
                self.value = self.value or new_child.value

                for new_child, order in copy(new_child.children).items():
                    child.add_child(new_child, order)

        try:
            order = int(float(order))
        except Exception as e:
            logger.info(f"order to float to int failed {order}, {e}")
            return

        self.children[new_child] = order
        new_child.parent = self

    @lru_cache(maxsize=512)
    def visualize(self) -> str:
        """
        A function to create a printable representation of the tree from this point
        :return: A multiline string
        """
        return f"\n{self.__repr__()}" + ''.join(c.visualize().replace('\n', '\n\t') for c in self.children)

    @lru_cache(maxsize=512)
    def refs(self) -> dict:
        """
        A quick utility function to pull and parse all bottom level references in the tree
        :return: A dict mapping old references to parsed ones
        """
        self.date = self.date or parse_datetime(self.ref)

        ref_map = {self.ref: self.date}
        for child in self.children:
            ref_map.update(child.refs())
        return ref_map

    @lru_cache(maxsize=512)
    def find(self, **kwargs) -> "XBRLElement":
        """
        A find function to find specific node that has a value that matches any of the kwargs

        .. highlight:: python
        .. code-block:: python

            ticker = entity_info.find(uri=re.compile('trading.?symbol', re.IGNORECASE),
                                        value=re.compile(r'^[A-Z]{1,6}$'))
            ticker = entity_info.find(uri="FooBar")

        :param kwargs: Pass in find terms as kwargs which will be match by kw to `XBRLElement` values
        :return: The first matching `XBRLElement`
        """
        def match(value, srch):
            if callable(srch):
                return srch(value)
            elif isinstance(srch, re.Pattern):
                return srch.search(value)
            return srch == value

        smap = {srch: str(self.__dict__[x]) for x, srch in kwargs.items() if x in self.__dict__ and srch is not None}
        if all(match(v, s) for s, v in smap.items()):
            return self

        for child in self.children:
            child_search = child.find(**kwargs)
            if child_search:
                return child_search

    def findall(self, **kwargs) -> typing.Generator['XBRLElement', None, None]:
        """
        A find function to find all nodes that has a value that matches any of the kwargs

        .. highlight:: python
        .. code-block:: python

            ticker = entity_info.findall(uri=re.compile('trading.?symbol', re.IGNORECASE),
                                        value=re.compile(r'^[A-Z]{1,6}$'))
            ticker = entity_info.findall(uri="FooBar")

        :param kwargs: Pass in find terms as kwargs which will be match by kw to `XBRLElement` values
        :return: The first matching `XBRLElement`
        """
        def match(value, srch):
            if callable(srch):
                return srch(value)
            elif isinstance(srch, re.Pattern):
                return srch.search(value)
            return srch == value

        smap = {srch: str(self.__dict__[x]) for x, srch in kwargs.items() if x in self.__dict__ and srch is not None}
        if all(match(v, s) for s, v in smap.items()):
            return self

        for child in self.children:
            child_search = child.find(**kwargs)
            if child_search:
                yield child_search

    def iter(self):
        """
        Allows iteration of all elements in a tree

        :return: Yields `XBRLElement` in the
        """
        if self.head() is self:
            yield self

        for child in self.children:
            yield child

    def to_json(self) -> dict:
        """
        Creates a json representation of the tree
        :return: A dictionary representation of the tree
        """
        json_data = {'uri': self.uri, 'label': self.label, 'ref': self.ref, 'value': self.value, 'children': []}
        for child in self.children:
            json_data['children'].append(child.to_json())
        return json_data

    @classmethod
    def from_json(cls, data):
        """
        Creates an XBRLElement tree from json data
        :param data: A dict of data loaded from a json file
        :return:
        """
        children = data.pop('children')
        element = cls(**data)
        for child in children:
            element.add_child(cls.from_json(child))
        return element


class XBRLAssembler:
    """
    XBRLAssembler is a data object that is comprised of a map of trees which represent various financial statements.
    The primary functionality of this class is for loading and saving data, but also selecting specific data trees.
    """
    def __init__(self):
        self.xbrl_elements = {}

    @classmethod
    def parse(cls, file_dict, ref_doc=XBRLType.PRE) -> "XBRLAssembler":
        """
        Create a new XBRLAssembler from raw XBRL files.

        :param file_dict: A `dict` with file names as keys and either file paths, `TextIOWrapper`,
        :param ref_doc: Optional class`xbrlassembler.XBRLType` used to specify the requested reference document

        :return: A class:`xbrlassembler.XBRLAssembler`
        """
        if all(isinstance(v, str) and os.path.isfile(v) for v in file_dict.values()):
            file_dict = {file_name: BeautifulSoup(open(file_path, 'r'), 'lxml') for file_name, file_path in file_dict.items()}
        elif all(isinstance(v, TextIOWrapper) for v in file_dict.values()):
            file_dict = {file_name: BeautifulSoup(file, 'lxml') for file_name, file in file_dict.items()}

        if any(not isinstance(v, BeautifulSoup) for v in file_dict.values()):
            raise ValueError("XBRLAssembler.__init__ only accepts a file_dict where keys are file names and values "
                             "are file paths, TextIOWrapper, or BeautifulSoup objects")

        file_map = {XBRLType(file_name): soup for file_name, soup in file_dict.items()}

        try:
            schema = file_map[XBRLType.SCHEMA]
            label = file_map[XBRLType.LABEL]
            cell = file_map[XBRLType.DATA]

            ref_type = next(ref for ref in {ref_doc, XBRLType.PRE, XBRLType.DEF, XBRLType.CALC} if ref in file_map)
            ref = file_map[ref_type]

            assembler = cls()
            assembler.__parse_schema(schema)
            assembler.__parse_ref(
                labels=assembler.__parse_labels(label),
                cells=assembler.__parse_cells(cell),
                ref_soup=ref
            )

            return assembler

        except Exception:
            raise XBRLAssemblerFromDirectoryError(f"Error creating XBRLAssembler")

    @classmethod
    def parse_dir(cls, path, ref_doc=XBRLType.PRE) -> "XBRLAssembler":
        """
        Alternative constructor that will attempt to search the specific directory for a set of xbrl documents

        :param path: A string to a directory that will be scanned for xbrl documents
        :param ref_doc: Optional class`xbrlassembler.XBRLType` used to specify the requested reference document

        :return: A class:`xbrlassembler.XBRLAssembler`
        """
        file_map = {}
        for item in os.listdir(path):
            if re.search(r'.*\.(xml|xsd)', item):
                xbrl_type = XBRLType(item)
                if xbrl_type:
                    file_map[xbrl_type] = BeautifulSoup(open(os.path.join(path, item), 'r'), 'lxml')

        return cls.parse(file_dict=file_map, ref_doc=ref_doc)

    @classmethod
    def from_json(cls, data: dict) -> "XBRLAssembler":
        """
        Creates a XBRLAssembler from a nested dictionary

        :param data: A dict containing data
        :return: A `XBRLAssembler` object
        """
        xbrl_assembler = cls()
        xbrl_assembler.xbrl_elements.update({k: XBRLElement.from_json(v) for k, v in data.items()})
        return xbrl_assembler

    def to_json(self) -> dict:
        """
        A write function to store all data in a json file

        :return: A `dict` containing all data
        """
        return {uri: ele.to_json() for uri, ele in self.xbrl_elements.items()}

    def merge(self, *others):
        """
        Attempts to merge an `XBRLAssembler` with another `XBRLAssembler`
        The merge is aimed to take bottom level elements of other trees and match them
        with bottom level elements of existing trees.

        :param others: One or many `XBRLAssemblers`
        """
        if not all(isinstance(o, XBRLAssembler) for o in others):
            raise ValueError('XBRLAssembler.merge only accepts other XBRLAssembler objects')

        xbrl_type_map = {FinancialStatement(uri): head for uri, head in self.xbrl_elements.items()}
        for other in others:
            other_xbrl_type_map = {FinancialStatement(uri): head for uri, head in other.xbrl_elements.items()}
            matching_keys = set(xbrl_type_map.keys()).intersection(set(other_xbrl_type_map.keys()))
            matching_keys.remove(FinancialStatement.INVALID)
            for key in matching_keys:
                for element in other_xbrl_type_map[key].iter():
                    match = xbrl_type_map[key].find(uri=element.uri)
                    if match and match.parent:
                        match.parent.add_child(element)

    def __parse_schema(self, schema_soup):
        """
        Parsing function for XBRL schema and adding it to the XBRLAssembler top level elements

        This establishes the access point for other documents as URI's from this find relevent data in the
        reference document
        :param schema_soup: A `BeautifulSoup` object
        :return:
        """
        for role_type in schema_soup.find_all("link:roletype"):
            uri = role_type['roleuri']
            label = role_type.find("link:definition").text
            if "Parenthetical" not in label:  # "Statement" in label and
                text = label.split(" - ")
                ele = XBRLElement(uri=uri, label=text[-1], ref=text[0])
                self.xbrl_elements[uri] = ele

    @staticmethod
    def __parse_labels(label_soup):
        """
        Parsing function for XBRL label file to provide readable labels to all elements
        :param label_soup: A `BeautifulSoup` object
        :return: A dict of labels
        """

        def uri_search(raw):
            uri_re = re.compile(r'(?:lab_)?((us-gaap|source|dei|[a-z]{3,4})[_:][A-Za-z]{5,})', re.IGNORECASE)
            uris = re.search(uri_re, raw)
            return uris.group(1) if uris else raw

        labels = {}
        for lab in label_soup.find_all(re.compile('label$', re.IGNORECASE)):
            try:
                u = uri_search(lab['xlink:label']).lower()
                labels[u if u != lab['xlink:label'] else uri_search(lab['id'])] = lab.text
            except KeyError:
                continue

        return labels

    @staticmethod
    def __parse_cells(data_soup):
        """
        Parsing function for the base XML data document for low level data
        :param data_soup: A `BeautifulSoup` object
        """
        cells = collections.defaultdict(list)
        for node in data_soup.find_all(attrs={"contextref": True}):
            uri = node.name.replace(':', '_')
            ele = XBRLElement(uri=uri,
                              value=node.text,
                              ref=node['contextref'])
            cells[uri].append(ele)
        return cells

    def __parse_ref(self, labels, cells, ref_soup):
        """
        The combination tool of all xbrl documents.
        After all schema, labels, and cells are parsed the reference document is used to establish relationships.
        These relationships are then formed into a tree structure of `XBRLElement` creating financial statment trees.

        :param labels: A map of uri's to label strings
        :param cells: A map of uri's to a list of XBRLElements with values
        :param ref_soup: A `BeautifulSoup` object representing the reference document
        """
        for doc_uri, doc_ele in self.xbrl_elements.items():
            # Find desired section in reference document
            def_link = ref_soup.find(re.compile(r'link', re.IGNORECASE), attrs={'xlink:role': doc_uri})
            if not def_link:
                continue

            # Pull all elements and create XBRLElements out of them
            eles = {}
            references = collections.defaultdict(int)
            for loc in def_link.find_all(re.compile(r'loc', re.IGNORECASE)):
                uri = loc['xlink:href'].split('#')[1]
                label = labels[uri.lower()] if uri.lower() in labels else None
                ele = XBRLElement(uri=uri, label=label)
                eles[loc['xlink:label']] = ele

                if ele.uri.lower() in cells:
                    for cell in cells[ele.uri.lower()]:
                        references[cell.ref] += 1

            if not references:
                continue

            # Find and create parent/child relationships between new elements
            for arc in def_link.find_all(re.compile(r'\w*arc', re.IGNORECASE)):
                parent, child, order = eles[arc['xlink:from']], eles[arc['xlink:to']], arc['order']
                parent.add_child(new_child=child, order=order)

            # Clean out incorrect refences
            most_used = max(references.values())
            references = set(ref for ref, count in references.items() if count == most_used)

            # Determine top and bottom level elements in the document (put under header or fill in cells)
            for order, ele in enumerate(eles.values()):
                if ele.parent is None:
                    doc_ele.add_child(new_child=ele, order=order)

                if ele.uri.lower() in cells:
                    possible_cells = cells[ele.uri.lower()]

                    for cell in possible_cells:
                        if cell.ref in references:
                            ele.add_child(cell)

    def get(self, item) -> XBRLElement:
        """
        Main access function that will take a variety of search criteria and attempt to create and
            return the document tree relevent to the search

        :param search: Regex, string, or FinancialStatement enum to search with

        :return: class:`xbrlassembler.XBRLElement` for the top of a tree representing the requested document
        """

        if isinstance(item, FinancialStatement):
            return {FinancialStatement(uri): head for uri, head in self.xbrl_elements.items()}[item]
        elif isinstance(item, (str, re.Pattern)):
            for ele in self.xbrl_elements.values():
                if ele.find(uri=item) or ele.find(label=item):
                    return ele
        else:
            raise ValueError(f"XBRLAssembler.get() search term should be re.Pattern, string, or FinancialStatement not {item}")

        return next((ele for ele in self.xbrl_elements.values() if st.find(ele.uri) or st.find(ele.label)), None)
