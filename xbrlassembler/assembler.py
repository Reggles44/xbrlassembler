import collections
import json
import logging
import os
import re
from functools import lru_cache

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

        self.children = {}
        self.parent = None

    def __repr__(self):
        """
        :return: Returns a string representation of various aspects of the non relational data
        """
        return f"{self.uri} (label={self.label}, ref={self.ref}, value={self.value})"

    @lru_cache(maxsize=512)
    def head(self):
        """
        Return the top element of the tree
        :return: XBRLElement
        """
        return self if self.parent is None else self.parent.head()

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

        for already_child in self.children:
            if already_child.uri == child.uri and already_child.ref == child.ref:
                self.merge(child)
                return

        try:
            order = int(float(order))
        except Exception as e:
            logger.info(f"order to float to int failed {order}, {e}")
            return

        self.children[child] = order
        child.parent = self

    def merge(self, other):
        """
        Attempts to merge one XBRLElement with another resulting in one element with more complete information
        :param other: An `XBRLElement` to be absorbed
        :return:
        """
        self.label = self.label or other.label
        self.value = self.value or other.value
        self.parent = self.parent or other.parent

        for new_child, order in other.children.items():
            self.add_child(new_child, order)

    @lru_cache(maxsize=512)
    def visualize(self) -> str:
        """
        A function to create a printable representation of the tree from this point
        :return: A multiline string
        """
        vis = f"\n{self.__repr__()}"
        if self.children:
            for child in self.children:
                vis += child.visualize().replace('\n', '\n\t')
        return vis

    @lru_cache(maxsize=512)
    def references(self) -> dict:
        """
        A quick utility function to pull and parse all bottom level references in the tree
        :return: A dict mapping old references to parsed ones
        """
        ref_map = {self.ref: DateParser.parse(self.ref)}
        for child in self.children:
            ref_map.update(child.references())
        return ref_map

    @lru_cache(maxsize=512)
    def ids(self):
        """
        Recursive function to access all uri label pairs
        :return: A dictionary where keys are uri strings and values are label strings or None is there is no label
        """
        ids = {self.uri: self.label}
        for child in self.children:
            ids.update(child.ids())
        return ids

    @lru_cache(maxsize=512)
    def search(self, term):
        """
        A search function to find specific node that has a uri or label that matches
        :param term: String, re.pattern, or anything that can go into a search
        :return: A specific node from the tree
        """
        if (re.search(term, self.uri) if self.uri else False) or (re.search(term, self.label) if self.label else False):
            return self
        else:
            for child in self.children:
                child_search = child.search(term)
                if child_search:
                    return child_search

    @lru_cache(maxsize=512)
    def items(self):
        """
        A recursive function iterator allowing access to loop over the entire dataset as a list
        :return: Yields  Uri, Label, Ref, Value
        """
        yield self
        for child in self.children.keys():
            for ele in child.items():
                yield ele

    @lru_cache(maxsize=512)
    def data(self):
        """
        A recursive function iterator returning all low level elements
        :return: Yields XBRLElement
        """
        if all(child.value is not None and len(child.children) == 0 for child in self.children):
            yield self

        for child in self.children.keys():
            for ele in child.data():
                yield ele

    @lru_cache(maxsize=512)
    def to_json(self) -> dict:
        """
        Creates a json representation of the tree
        :return: A dictionary representation of the tree
        """
        json = {'u': self.uri, 'l': self.label, 'r': self.ref, 'v': self.value, 'c': []}
        for child in self.children:
            json['c'].append(child.to_json())
        return json

    @classmethod
    def from_json(cls, data: dict):
        """
        Creates an XBRLElement tree from json data
        :param data: A dict of data loaded from a json file
        :return:
        """
        element = cls(uri=data['u'], label=data['l'], ref=data['r'], value=data['v'])
        for child_data in data['c']:
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

            ref = next((ref for ref in [ref_doc, XBRLType.PRE, XBRLType.DEF, XBRLType.CALC] if ref in file_map))
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

            ref = next((ref for ref in [ref_doc, XBRLType.PRE, XBRLType.DEF, XBRLType.CALC] if ref in file_map))
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

    def to_json(self, file_path, mode='w+'):
        """
        A write function to store all data in a json file
        :param file_path: A string to a file
        """
        with open(file_path, mode) as file:
            file.write(json.dumps({uri: ele.to_json() for uri, ele in self.xbrl_elements.items()}, indent=4))
            #json.dump({uri: ele.to_json() for uri, ele in data.items()}, file)

    def merge(self, *others):
        for other in others:
            if not isinstance(other, XBRLAssembler):
                raise XBRLError(f"XBRLAssembler must merge with another XBRLAssembler not {type(other)}")

            for uri, header_ele in self.xbrl_elements.items():
                uri_prefix = uri.split('/')[-1]
                uri_lookup = next((uri for uri in other.xbrl_elements.keys() if uri_prefix in uri), None)
                if not uri_lookup:
                    continue

                other_doc = other.xbrl_elements[uri_lookup]

                for other_ele in other_doc.data():
                    search_ele = header_ele.search(other_ele.uri)
                    if search_ele:
                        search_ele.merge(other_ele)

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
            if not ele.children:
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

        if isinstance(search, re.Pattern) or isinstance(search, str):
            search_term = search
        elif isinstance(search, FinancialStatement):
            search_term = search.value
        else:
            raise ValueError(f"XBRLAssembler.get() search term should be "
                             f"re.Pattern, string, or FinancialStatement not {search}")

        doc_ele = next((ele for uri, ele in search_data if re.search(search_term, uri) or re.search(search_term, ele.label)))
        if doc_ele is None:
            raise XBRLError(f"No match found for {search} in names.\n\t"
                            f"Names available {[name for name in self.xbrl_elements.keys()]}]")

        if not doc_ele.children:
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
        references = collections.defaultdict(int)
        for loc in def_link.find_all(re.compile(r'loc', re.IGNORECASE)):
            uri = loc['xlink:href'].split('#')[1]
            label = self.labels[uri.lower()] if uri.lower() in self.labels else None
            ele = XBRLElement(uri=uri, label=label)
            eles[loc['xlink:label']] = ele

            if ele.uri.lower() in self.cells:
                for cell in self.cells[ele.uri.lower()]:
                    references[cell.ref] += 1

        if not references:
            raise XBRLError(f'{doc_ele.label} could not find any columns for cells')

        # Find and create parent/child relationships between new elements
        for arc in def_link.find_all(re.compile(r'\w*arc', re.IGNORECASE)):
            parent, child, order = eles[arc['xlink:from']], eles[arc['xlink:to']], arc['order']
            parent.add_child(child=child, order=order)

        # Clean out incorrect refences
        most_used = max(references.values())
        references = set(ref for ref, count in references.items() if count == most_used)

        # Determine top and bottom level elements in the document (put under header or fill in cells)
        for order, ele in enumerate(eles.values()):
            if ele.parent is None:
                doc_ele.add_child(child=ele, order=order)

            if ele.uri.lower() in self.cells:
                possible_cells = self.cells[ele.uri.lower()]

                if all(cell.ref not in references for cell in possible_cells):
                    cells = possible_cells
                else:
                    cells = [cell for cell in possible_cells if cell.ref in references]

                for cell in cells:
                    ele.add_child(cell)
