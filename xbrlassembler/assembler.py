import collections
import logging
import os
import re

import dateparser
import pandas
import requests
from bs4 import BeautifulSoup

from xbrlassembler.enums import XBRLType, FinancialStatement
from xbrlassembler.error import XBRLSchemaError, XBRLLabelError, XBRLCellsError, XBRLIndexError, XBRLRefDocError

logger = logging.getLogger('xbrlassembler')


class XBRLElement:
    def __init__(self, uri, label=None, value=None, ref=None):
        self.uri = uri
        self.label = label
        self.value = value
        self.ref = ref

        self.children = {}
        self.parent = None

    def add_child(self, child, order=None):
        if not child:
            return

        if child in self.children:
            return

        self.children[child] = order
        child.parent = self

    def to_dict(self):
        dic = {self.label: []}
        if all(not child.children for child in self.children.keys()):
            dic[self.label] = [ele for ele in self.children.keys()]
        else:
            for ele, o in sorted(self.children.items(), key=lambda item: item[1] or -1):
                dic.update(ele.to_dict())
        return dic

    def visualize(self):
        vis = f"\n{self.__str__()}"
        if self.children:
            for child in self.children:
                cvis = child.visualize().replace('\n', '\n\t')
                vis += cvis
        return vis

    def __str__(self):
        return f"{self.uri} (label={self.label}, value={self.value}, ref={self.ref}, " \
               f"children={[c.label for c in self.children.keys()]}) "


class XBRLAssembler:

    uri_re = re.compile(r'(?:lab_)?((us-gaap|source|dei|[a-z]{3,4})[_:][A-Za-z]{5,})', re.IGNORECASE)
    date_re = re.compile('((2[0-2][0-9]{2}).?(0[1-9]|1[1-2]).?(0[1-9]|[1-2][0-9]|31|30))')
    date_settings = {'DATE_ORDER': 'YMD', 'PREFER_DATES_FROM': 'past'}

    def __init__(self, info, schema, data, label, ref):

        self.info = info

        for t, name in [(schema, "schema"),
                        (data, "data"),
                        (label, "label"),
                        (ref, "ref")]:
            if not isinstance(t, BeautifulSoup) or t is None:
                raise ValueError(f"{type(t)} is not a BeautifulSoup")

        self.schema = schema
        self.data = data
        self.label = label
        self.ref = ref

        self._docs = self.get_docs()
        self._labels = self.get_labels()
        self._cells = self.get_cells()

        # print("Docs", self._docs)
        # print("Labels", self._labels)
        # print("Docs", self._cells)

    @classmethod
    def from_sec_index(cls, index_url, ref_doc=XBRLType.PRE):
        index_soup = BeautifulSoup(requests.get(index_url).text, 'lxml')

        data_files_table = index_soup.find('table', {'summary': 'Data Files'})

        if not data_files_table:
            raise XBRLIndexError(index_url)

        file_map = {}
        for row in data_files_table('tr')[1:]:
            row = row.find_all('td')
            soup = BeautifulSoup(requests.get("https://www.sec.gov" + row[2].find('a')['href']).text, 'lxml')
            file_map[XBRLType.get(row[3].text)] = soup

        return cls(info=index_url,
                   schema=file_map[XBRLType.SCHEMA],
                   data=file_map[XBRLType.DATA],
                   label=file_map[XBRLType.LAB],
                   ref=file_map[ref_doc])

    @classmethod
    def from_dir(cls, directory, ref_doc=XBRLType.PRE):
        file_map = {}
        for item in os.listdir(directory):
            if re.search(r'.*\.(xml|xsd)', item):
                file_map[XBRLType.get(item)] = BeautifulSoup(open(item), 'lxml')

        return cls(info=directory,
                   schema=file_map[XBRLType.SCHEMA],
                   data=file_map[XBRLType.DATA],
                   label=file_map[XBRLType.LAB],
                   ref=file_map[ref_doc])

    def uri(self, raw):
        uri_re = re.search(self.uri_re, raw)
        if uri_re:
            return uri_re.group(1)
        return raw

    def get_docs(self):
        try:
            docs = {}
            for roletype in self.schema.find_all("link:roletype"):
                uri = roletype['roleuri']
                label = roletype.find("link:definition").text
                if "Statement" in label and "Parenthetical" not in label:
                    text = label.split(" - ")
                    docs[uri] = XBRLElement(uri=uri, label=text[-1], ref=text[0])

            if not docs:
                raise AttributeError

            return docs
        except AttributeError:
            raise XBRLSchemaError(self.info)

    def get_labels(self):
        try:
            labels = {}
            label_link = self.label.find(re.compile('.*labellink', re.IGNORECASE))
            if not label_link:
                raise AttributeError

            for lab in label_link.find_all(re.compile('label$')):
                uri = self.uri(lab['xlink:label']).lower()
                # print(xlink_label, uri)
                labels[uri] = lab.text

            for lab in label_link.find_all(re.compile('loc$')):
                label_uri = lab['xlink:label'].lower()
                if label_uri not in labels:
                    continue

                uri = lab['xlink:href'].split('#')[1].lower()
                if uri in labels:
                    continue

                labels[uri] = labels[label_uri]

            if not labels:
                raise AttributeError

            return labels
        except (AttributeError, TypeError):
            raise XBRLLabelError(self.info)

    def get_cells(self):
        try:
            cells = collections.defaultdict(list)

            for node in self.data.find_all(attrs={"contextref": True}):

                uri = node.name.replace(':', '_')

                ref = []
                for re_date in re.findall(self.date_re, node['contextref']):
                    date = dateparser.parse(re_date[0], settings=self.date_settings)
                    ref.append(date)
                ref = tuple(ref) if len(ref) > 1 else (*ref, None)

                ele = XBRLElement(uri=uri,
                                  value=node.text,
                                  ref=ref)

                cells[uri].append(ele)

            if not cells:
                raise AttributeError
            return cells
        except AttributeError:
            raise XBRLCellsError(self.info)

    def find_doc(self, search):
        for uri, ele in sorted(self._docs.items(), key=lambda item: item[1].ref):
            if search(uri):
                return ele

    def get(self, search):
        if isinstance(search, re.Pattern):
            doc_ele = self.find_doc(lambda name: re.search(search, name))
        elif isinstance(search, str):
            doc_ele = self.find_doc(lambda name: search in name)
        elif isinstance(search, FinancialStatement):
            doc_ele = self.find_doc(lambda name: re.search(search.value, name))
        else:
            raise ValueError(f"")

        if not doc_ele:
            raise ValueError(f"No match found for {search} in names.\n\t"
                             f"Names available {[name for name in self._docs.keys()]}]")

        if not doc_ele.children:
            self.__assemble(doc_ele)

        return self.__dataframe(doc_ele)

    def __assemble(self, doc_ele):
        # Find desired section in reference document
        def_link = self.ref.find(re.compile(r'\w*link', re.IGNORECASE), attrs={'xlink:role': doc_ele.uri})
        if not def_link:
            raise XBRLRefDocError(self.info)

        # Pull all elements and create XBRLElements out of them
        eles = {}
        for loc in def_link.find_all(re.compile(r'loc', re.IGNORECASE)):
            uri = loc['xlink:href'].split('#')[1]
            label = self._labels[uri.lower()] if uri.lower() in self._labels else None
            ele = XBRLElement(uri=uri, label=label)
            # print(ele)
            eles[loc['xlink:label']] = ele

        # Find and create parent/child relationships between new elements
        for arc in def_link.find_all(re.compile(r'\w*arc', re.IGNORECASE)):
            parent, child, order = eles[arc['xlink:from']], eles[arc['xlink:to']], arc['order']
            parent.add_child(child=child, order=order)
            # print(parent)

        # Determine top and bottom level elements in the document and either fill in cells or
        #   link them to the overall document element
        for order, ele in enumerate(eles.values()):
            if ele.parent and ele.children:
                continue
            elif not ele.parent:
                doc_ele.add_child(child=ele, order=order)

            if ele.uri.lower() in self._cells:
                for cell in self._cells[ele.uri.lower()]:
                    ele.add_child(cell)
                    # print(ele)

    @staticmethod
    def __dataframe(doc_ele):
        rows = doc_ele.to_dict()

        # print(doc_ele.visualize())

        cols = collections.defaultdict(int)
        for atr, cells in rows.items():
            for c in cells:
                if c.ref:
                    cols[c.ref] += 1

        # Remove columns that are not used typically
        cols = set([c for c, count in cols.items() if count > 2])

        # Chop off incorrect columns and reformat rows to reflect that
        for atr, cells in rows.items():
            rmap = {c.ref: c for c in cells if c.ref in cols}

            row_values = []
            for col in cols:
                try:
                    value = float(rmap[col].value) if col in rmap.keys() else None
                    row_values.append(value)
                except ValueError:
                    logger.info(f"Error parsing {rmap[col].value}")
            rows[atr] = row_values

        return pandas.DataFrame.from_dict(rows, columns=cols, orient='index', dtype=float)
