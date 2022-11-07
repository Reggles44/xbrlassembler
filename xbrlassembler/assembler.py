import collections
import logging
import os
import re
import typing
import json
from copy import copy
from functools import lru_cache
from io import TextIOWrapper

from bs4 import BeautifulSoup

from xbrlassembler.enums import XBRLType
from xbrlassembler.error import XBRLAssemblerFromDirectoryError
from xbrlassembler.utils import parse_datetime

logger = logging.getLogger('xbrl-assembler')

URI_RE = re.compile(r'(?:lab_)?((us-gaap|source|dei|[a-z]{3,4})[_:][A-Za-z]{5,})', re.IGNORECASE)


class XBRLElement(dict):
    """
    An element to represent a single point on a tree.
    Specific data values are geared towards xbrl relevent information
    While relational data is close to that of an XML tree element
    """
    def __init__(self, **kwargs):
        """Constructor Method"""
        if not kwargs.get('uri'):
            raise

        children = kwargs.get('children')
        if children and isinstance(children, list):
            kwargs['children'] = [XBRLElement(**data) for data in kwargs.get('children')]
            for child in children:
                child.parent = self
        else:
            kwargs['children'] = []

        kwargs.setdefault('date', parse_datetime(kwargs.get('ref')))

        self.parent = None
        super().__init__(self, **kwargs)

    @property
    def children(self) -> typing.List["XBRLElement"]:
        return self.setdefault('children', [])

    @property
    def head(self) -> "XBRLElement":
        """
        Return the top element of the tree
        :return: XBRLElement
        """
        return self.parent and self.parent.head or self

    def find(self, *, first=True, **kwargs) -> typing.Union[typing.Iterator["XBRLElement"], "XBRLElement"]:
        """
        A find function to find specific node that has a value that matches any of the kwargs

        .. highlight:: python
        .. code-block:: python

            ticker = entity_info.find(uri=re.compile('trading.?symbol', re.IGNORECASE),
                                        value=re.compile(r'^[A-Z]{1,6}$'))
            ticker = entity_info.find(uri="FooBar")

        :param first: A boolean to either return the first value or yield all values
        :param kwargs: Pass in find terms as kwargs which will be match by kw to `XBRLElement` values
        :return: The first matching `XBRLElement`
        """
        for key, search_term in kwargs.items():
            if key in self and search_term is not None:
                regex = re.compile(search_term)
                if regex.search(self[key]):
                    if first:
                        return self
                    else:
                        yield self
                        break

        for child in self.children:
            child_search = child.find(**kwargs)
            if child_search:
                if first:
                    return child_search
                else:
                    yield child_search


class XBRLAssembler(dict):
    """
    XBRLAssembler is a data object that is comprised of a map of trees which represent various financial statements.
    The primary functionality of this class is for loading and saving data, but also selecting specific data trees.
    """
    @classmethod
    def parse(cls, file_dict, ref_doc=XBRLType.PRE) -> "XBRLAssembler":
        """
        Create a new XBRLAssembler from raw XBRL files.

        :param file_dict: A `dict` with file names as keys and either file paths, `TextIOWrapper`,
        :param ref_doc: Optional class`xbrl-assembler.XBRLType` used to specify the requested reference document

        :return: A class:`xbrl-assembler.XBRLAssembler`
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
        :param ref_doc: Optional class`xbrl-assembler.XBRLType` used to specify the requested reference document

        :return: A class:`xbrl-assembler.XBRLAssembler`
        """
        file_map = {}
        for item in os.listdir(path):
            if re.search(r'.*\.(xml|xsd)', item):
                xbrl_type = XBRLType(item)
                if xbrl_type:
                    file_map[xbrl_type] = BeautifulSoup(open(os.path.join(path, item), 'r'), 'lxml')

        return cls.parse(file_dict=file_map, ref_doc=ref_doc)

    @classmethod
    def parse_json(cls, path) -> "XBRLAssembler":
        raw = json.load(path)
        return cls(**{uri: XBRLElement(**raw_ele) for uri, raw_ele in raw.items()})

    def get(self, __key) -> typing.Union['XBRLElement', None]:
        if isinstance(__key, re.Pattern):
            return next((ele for uri, ele in self.items() if __key.search(uri)), None)
        return super().get(__key)

    def __parse_schema(self, schema_soup):
        """
        Parsing function for XBRL schema and adding it to the XBRLAssembler top level elements

        This establishes the access point for other documents as URI's from this find relevent data in the
        reference document
        """
        for role_type in schema_soup.find_all("link:roletype"):
            uri = role_type['roleuri']
            label = role_type.find("link:definition").text
            if "Parenthetical" not in label:  # "Statement" in label and
                text = label.split(" - ")
                ele = XBRLElement(uri=uri, label=text[-1], ref=text[0])
                self[uri] = ele

    @staticmethod
    def __parse_labels(label_soup):
        """
        Parsing function for XBRL label file to provide readable labels to all elements
        """
        def uri_search(raw):
            uri_match = URI_RE.search(raw)
            return uri_match and uri_match.group(1) or raw

        labels = {}
        for lab in label_soup.find_all(re.compile('label$', re.IGNORECASE)):
            try:
                uri_match = uri_search(lab['xlink:label']).lower()
                label_key = uri_match if uri_match != lab['xlink:label'] else uri_search(lab['id'])
                labels[label_key] = lab.text
            except KeyError:
                continue

        return labels

    @staticmethod
    def __parse_cells(data_soup):
        """
        Parsing function for the base XML data document for low level data
        """
        cells = collections.defaultdict(list)
        for node in data_soup.find_all(attrs={"contextref": True}):
            uri = node.name.replace(':', '_')
            ele = XBRLElement(uri=uri, value=node.text, ref=node['contextref'])
            cells[uri].append(ele)
        return cells

    def __parse_ref(self, labels, cells, ref_soup):
        """
        The combination tool of all xbrl documents.
        After all schema, labels, and cells are parsed the reference document is used to establish relationships.
        These relationships are then formed into a tree structure of `XBRLElement` creating financial statment trees.
        """
        for doc_uri, doc_ele in self.items():
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

                if uri in cells:
                    for cell in cells[uri]:
                        references[cell.ref] += 1

            if not references:
                continue

            # Find and create parent/child relationships between new elements
            for arc in def_link.find_all(re.compile(r'\w*arc', re.IGNORECASE)):
                parent, child, order = eles[arc['xlink:from']], eles[arc['xlink:to']], arc['order']
                child['order'] = order or 0
                parent['children'].append(child)
                child.parent = parent

            # Clean out incorrect refences
            most_used = max(references.values())
            references = set(ref for ref, count in references.items() if count == most_used)

            # Determine top and bottom level elements in the document (put under header or fill in cells)
            for order, ele in enumerate(eles.values()):
                if ele.parent is None:
                    doc_ele.add_child(new_child=ele, order=order)

                uri = ele.get('uri', '').lower()
                if uri in cells:
                    possible_cells = cells[uri]

                    for cell in possible_cells:
                        if cell.ref in references:
                            ele['children'].append(cell)
                            cell.parent = ele
