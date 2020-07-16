import collections
import json
import logging
import os
import re

import requests
from bs4 import BeautifulSoup

from xbrlassembler.enums import XBRLType, FinancialStatement, DateParser
from xbrlassembler.error import XBRLError

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
    def __init__(self, uri, label=None, value=None, ref=None):
        """Constructor Method"""
        self.uri = uri
        self.label = label
        self.ref = ref
        self.value = value

        # Convert to float to remove any issues with comparing string representations of numbers
        try:
            self.value = float(value)
        except (TypeError, ValueError):
            if isinstance(value, str):
                self.value = value.replace('\n', '')
            logger.info(f"XBRLElement value convert to float failure for {self.value}")

        self._children = {}
        self._parent = None

    def __repr__(self):
        """
        :return: Returns a string representation of various aspects of the non relational data
        """
        return f"{self.uri} (label={self.label}, ref={self.ref}, value={self.value})"

    def add_child(self, child, order=-1):
        """
        Essential function for establishing relationships between elements.
        This function ensures that the relationship is set on both parent and child
        elements without duplication or Nones

        Args:
            :param child: An XBRLElement that is going to be under this element in the tree
            :param order: An optional argument to add order to child elements
        """
        if not isinstance(child, XBRLElement):
            return

        if child in self._children:
            return

        for already_child in self._children:
            if already_child.uri == child.uri and already_child.ref == child.ref:
                self.merge(child)
                return

        try:
            order = int(float(order))
        except Exception as e:
            logger.info(f"order to float to int failed {order}, {e}")
            return

        self._children[child] = order
        child._parent = self

    def merge(self, other):
        """
        Attempts to merge one XBRLElement with another resulting in one element with more complete information
        :param other: An `XBRLElement` to be absorbed
        :return:
        """
        if not isinstance(other, XBRLElement):
            return

        if self.label is None and other.label is not None:
            self.label = other.label

        if self.value is None and other.value is not None:
            self.value = other.value

        if self._parent is None and other._parent is not None:
            self._parent = other._parent

        for new_child, order in other._children.items():
            self.add_child(new_child, order)

    def visualize(self) -> str:
        """
        A function to create a printable representation of the tree from this point
        :return: A multiline string
        """
        vis = f"\n{self.__repr__()}"
        if self._children:
            for child in self._children:
                cvis = child.visualize().replace('\n', '\n\t')
                vis += cvis
        return vis

    def references(self) -> dict:
        """
        A quick utility function to pull and parse all bottom level references in the tree
        :return: A dict mapping old references to parsed ones
        """
        refs = {}
        for atr, cells in self.to_dict().items():
            for cell in cells:
                if cell.ref not in refs.keys() and cell.ref is not None:
                    refs[cell.ref] = DateParser.parse(cell.ref)
        return refs

    def ids(self):
        """
        Recursive function to access all uri label pairs
        :return: A dictionary where keys are uri strings and values are label strings or None is there is no label
        """
        ids = {self.uri: self.label}
        for child in self._children:
            ids.update(child.ids())
        return ids

    def search(self, term):
        """
        A search function to find specific node that has a uri or label that matches
        :param term: String, re.pattern, or anything that can go into a search
        :return: A specific node from the tree
        """
        if (re.search(term, self.uri) if self.uri else False) or (re.search(term, self.label) if self.label else False):
            return self
        else:
            for child in self._children:
                child_search = child.search(term)
                if child_search:
                    return child_search

    def to_list(self) -> list:
        """
        Recursive function to return a list of all elements in the tree
        :return: A list of each XBRLElement in the tree
        """
        lst = [self]
        for child in self._children:
            lst.extend(child.to_list())
        return lst

    def to_dict(self) -> dict:
        """
        A recursive function to return a dictionary representation of the tree from this point downward
        :return: A dictionary where keys are labels and cells are bottem level xbrl elements
        """
        dic = {self.uri: []}
        if all(not child._children for child in self._children.keys()):
            dic[self.uri] = [ele for ele in self._children.keys()]
        else:
            for ele, o in sorted(self._children.items(), key=lambda item: item[1] or -1):
                dic.update(ele.to_dict())
        return dic

    def to_json(self) -> dict:
        """
        Creates a json representation of the tree
        :return: A dictionary representation of the tree
        """
        json = {'uri': self.uri,
                'label': self.label,
                'ref': self.ref,
                'value': self.value,
                'children': []}

        for child in self._children:
            json['children'].append(child.to_json())

        return json

    @classmethod
    def from_json(cls, data: dict):
        """
        Creates an XBRLElement tree from json data
        :param data: A dict of data loaded from a json file
        :return:
        """
        element = cls(uri=data['uri'], label=data['label'], ref=data['ref'], value=data['value'])

        for child_data in data['children']:
            element.add_child(cls.from_json(child_data))

        return element


class XBRLAssembler:
    """
    The main object to compile XBRL documents into complete sets of data by establishing a tree of information
    """
    uri_re = re.compile(r'(?:lab_)?((us-gaap|source|dei|[a-z]{3,4})[_:][A-Za-z]{5,})', re.IGNORECASE)

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

        self.xbrl_elements = {}

        # Used for storing data of supporting documents
        self.labels = {}
        self.cells = collections.defaultdict(list)

        self.ref = None


    @classmethod
    def from_sec_index(cls, index_url, ref_doc=XBRLType.PRE, *args, **kwargs):
        """
        Alternative constructor that takes a url as a string and attempts to pull and parse all relevent documents

        :param index_url: A string for a url to an sec index
        :param ref_doc: An class:`xbrlassembler.XBRLType` to specify the type of reference document

        :return: A class:`xbrlassembler.XBRLAssembler`
        """
        if not index_url.startswith("https://www.sec.gov/Archives/edgar/data/"):
            raise XBRLError(f"{index_url} is not a url for an SEC index")

        index_soup = BeautifulSoup(requests.get(index_url).text, 'lxml')

        data_files_table = index_soup.find('table', {'summary': 'Data Files'})

        if not data_files_table:
            raise XBRLError(f"{index_url} does not appear to have any data files")

        file_map = {}
        for row in data_files_table('tr')[1:]:
            row = row.find_all('td')
            soup = BeautifulSoup(requests.get("https://www.sec.gov" + row[2].find('a')['href']).text, 'lxml')
            file_map[XBRLType.get(row[3].text)] = soup

        try:
            xbrl_assembler = cls(*args, **kwargs)

            ref = next((ref for ref in [ref_doc, XBRLType.PRE, XBRLType.DEF, XBRLType.CALC] if ref in file_map), None)
            xbrl_assembler.ref = file_map[ref]

            xbrl_assembler.parse_schema(file_map[XBRLType.SCHEMA])
            xbrl_assembler.parse_labels(file_map[XBRLType.LABEL])
            xbrl_assembler.parse_cells(file_map[XBRLType.DATA])

            return xbrl_assembler
        except KeyError:
            raise XBRLError(f"Could not find all document from {index_url}")

    @classmethod
    def from_dir(cls, directory, ref_doc=XBRLType.PRE, *args, **kwargs):
        """
        Alternative constructor that will attempt to search the specific directory for a set of xbrl documents

        :param directory: A string to a directory that will be scanned for xbrl documents
        :param ref_doc: Optional class`xbrlassembler.XBRLType` used to specify the requested reference document

        :return: A class:`xbrlassembler.XBRLAssembler`
        """
        if not os.path.isdir(directory):
            raise XBRLError(f"{directory} is not a valid directory")

        file_map = {}
        for item in os.listdir(directory):
            if re.search(r'.*\.(xml|xsd)', item):
                file_map[XBRLType.get(item)] = BeautifulSoup(open(os.path.join(directory, item), 'r'), 'lxml')

        try:
            xbrl_assembler = cls(*args, **kwargs)

            ref = next((ref for ref in [ref_doc, XBRLType.PRE, XBRLType.DEF, XBRLType.CALC] if ref in file_map), None)
            xbrl_assembler.ref = file_map[ref]

            xbrl_assembler.parse_schema(file_map[XBRLType.SCHEMA])
            xbrl_assembler.parse_labels(file_map[XBRLType.LABEL])
            xbrl_assembler.parse_cells(file_map[XBRLType.DATA])

            return xbrl_assembler
        except KeyError:
            raise XBRLError(f"Could not find all document from {directory}")

    @classmethod
    def from_json(cls, file_path, *args, **kwargs):
        if not isinstance(file_path, str):
            raise TypeError(f"XBRLAssembler.from_json needs a file_path string not {file_path}")

        xbrl_assembler = cls(*args, **kwargs)

        with open(file_path, 'r') as file:
            data_dict = {uri: XBRLElement.from_json(ele) for uri, ele in json.load(file).items()}
        xbrl_assembler.xbrl_elements.update(data_dict)

        return xbrl_assembler

    def to_json(self, file_path):
        """
        A write function to store all data in a json file
        :param file_path: A string to a file
        """
        data = {}

        if os.path.isfile(file_path):
            with open(file_path, 'r') as file:
                data = {uri: XBRLElement.from_json(dat) for uri, dat in json.load(file).items()}

        for uri, ele in self.xbrl_elements.items():
            if uri in data.keys():
                data[uri].merge(ele)
            else:
                data[uri] = ele

        with open(file_path, 'w+') as file:
            json.dump({uri: ele.to_json() for uri, ele in data.items()}, file)

    def uri(self, raw):
        """
        Used to standardize uri's across mutliple documents
        :param raw: A non standard URI string
        :return: A parsed string or raw
        """
        uri_re = re.search(self.uri_re, raw)
        return uri_re.group(1) if uri_re else raw

    def parse_schema(self, schema):
        """
        Parsing function for XBRL schema and adding it to the XBRLAssembler top level elements

        This establishes the access point for other documents as URI's from this find relevent data in the
        reference document
        :param schema: A `BeautifulSoup` object
        :return:
        """
        if not isinstance(schema, BeautifulSoup):
            raise XBRLError(f"XBRLAssembler.parse_schema requires a BeautifulSoup not {schema}")

        for role_type in schema.find_all("link:roletype"):
            uri = role_type['roleuri']
            label = role_type.find("link:definition").text
            if "Parenthetical" not in label:  # "Statement" in label and
                text = label.split(" - ")
                ele = XBRLElement(uri=uri, label=text[-1], ref=text[0])
                self.xbrl_elements[uri] = ele

    def parse_labels(self, labels):
        """
        Parsing function for XBRL label file to provide readable labels to all elements
        :param labels: A `BeautifulSoup` object
        :return:
        """
        if not isinstance(labels, BeautifulSoup):
            raise XBRLError(f"XBRLAssembler.parse_schema requires a BeautifulSoup not {labels}")

        for lab in labels.find_all(re.compile('label$', re.IGNORECASE)):
            uri = self.uri(lab['xlink:label']).lower()
            if uri == lab['xlink:label']:
                uri = self.uri(lab['id'])
            self.labels[uri] = lab.text

    def parse_cells(self, data):
        """
        Parsing function for the base XML data document for low level data
        :param data: A `BeautifulSoup` object
        """
        if not isinstance(data, BeautifulSoup):
            raise XBRLError(f"XBRLAssembler.parse_schema requires a BeautifulSoup not {data}")

        for node in data.find_all(attrs={"contextref": True}):
            uri = node.name.replace(':', '_')
            ele = XBRLElement(uri=uri,
                              value=node.text,
                              ref=node['contextref'])
            self.cells[uri].append(ele)

    def get_all(self):
        """
        A shortcut command to parse all documents against the reference document
        """
        for ele in self.xbrl_elements.values():
            if not ele._children:
                try:
                    self.__assemble(ele)
                except XBRLError as e:
                    logger.debug(e)

        return self.xbrl_elements

    def get(self, search) -> XBRLElement:
        """
        Main access function that will take a variety of search criteria and attempt to create and
            return the document tree relevent to the search

        :param search: Regex, string, or FinancialStatement enum to search with

        :return: class:`xbrlassembler.XBRLElement` for the top of a tree representing the requested document
        """
        search_data = sorted(self.xbrl_elements.items(), key=lambda item: item[1].ref)

        if isinstance(search, re.Pattern):
            doc_ele = next((ele for uri, ele in search_data if re.search(search, uri) or re.search(search, ele.label)))
        elif isinstance(search, str):
            doc_ele = next((ele for uri, ele in search_data if search in uri or search in ele.label))
        elif isinstance(search, FinancialStatement):
            search = search.value
            doc_ele = next((ele for uri, ele in search_data if re.search(search, uri) or re.search(search, ele.label)))
        else:
            raise ValueError(f"XBRLAssembler.get() search term should be "
                             f"re.Pattern, string, or FinancialStatement not {search}")

        if doc_ele is None:
            raise XBRLError(f"No match found for {search} in names.\n\t"
                            f"Names available {[name for name in self.xbrl_elements.keys()]}]")

        if not doc_ele._children:
            self.__assemble(doc_ele)

        return doc_ele

    def __assemble(self, doc_ele):
        if self.ref is None:
            return

        # Find desired section in reference document
        def_link = self.ref.find(re.compile(r'link', re.IGNORECASE), attrs={'xlink:role': doc_ele.uri})
        if not def_link:
            raise XBRLError(f"Refernce document doesn't contain any information for {doc_ele.uri}")

        # Pull all elements and create XBRLElements out of them
        eles = {}
        cols = collections.defaultdict(int)
        for loc in def_link.find_all(re.compile(r'loc', re.IGNORECASE)):
            uri = loc['xlink:href'].split('#')[1]
            label = self.labels[uri.lower()] if uri.lower() in self.labels else None
            ele = XBRLElement(uri=uri, label=label)
            eles[loc['xlink:label']] = ele

            if ele.uri.lower() in self.cells:
                for cell in self.cells[ele.uri.lower()]:
                    cols[cell.ref] += 1

        if not cols:
            raise XBRLError(f'{doc_ele.label} could not find any columns for cells')

        # Find and create parent/child relationships between new elements
        for arc in def_link.find_all(re.compile(r'\w*arc', re.IGNORECASE)):
            parent, child, order = eles[arc['xlink:from']], eles[arc['xlink:to']], arc['order']
            parent.add_child(child=child, order=order)

        most_used = max(cols.values())
        cols = {DateParser.parse(ref): ref for ref, count in cols.items() if count == most_used}
        cols = set(cols.values())

        # Determine top and bottom level elements in the document and either fill in cells or
        #   link them to the overall document element
        for order, ele in enumerate(eles.values()):
            if ele._parent is None:
                doc_ele.add_child(child=ele, order=order)

            if ele.uri.lower() in self.cells:
                for cell in self.cells[ele.uri.lower()]:
                    if cell.ref in cols:
                        ele.add_child(cell)
