import io
import os
import collections
import re
from enum import Enum

import dateparser
import pandas
from bs4 import BeautifulSoup


class FinancialStatement(Enum):
    INCOME_STATEMENT = re.compile(r"operation|income|earnings|revenues", re.IGNORECASE)
    BALANCE_SHEET = re.compile(r"balance|condition|position|assets", re.IGNORECASE)


class XBRLType(Enum):
    # Choose One
    CALC = ("CAL",), "calculation"
    DEF = ("DEF",), "definition"
    PRE = ("PRE",), "presentation"

    # Required
    LAB = ("LAB",), None
    SCHEMA = ("SCH", "XSD"), None
    DATA = ("XML", "INS"), None

    @classmethod
    def get(self, item):
        if isinstance(item, XBRLType):
            return item

        item = item.lower()
        for xbrl_type in XBRLType:
            if any([t.lower() in item for t in xbrl_type.value[0]]):
                return xbrl_type


class XBRLAssembler:
    def __init__(self, files, ref_doc=XBRLType.DEF):

        file_map = {XBRLType.get(t): f for t, f in files.items()}

        try:
            self.schema = BeautifulSoup(self._docdata(file_map[XBRLType.SCHEMA]), 'lxml')
            self.data = BeautifulSoup(self._docdata(file_map[XBRLType.DATA]), 'lxml')
            self.lab = BeautifulSoup(self._docdata(file_map[XBRLType.LAB]), 'lxml')
            self.ref = BeautifulSoup(self._docdata(file_map[ref_doc]), 'lxml')
            self.ref_doc = ref_doc
        except KeyError:
            raise ValueError("Error finding all required documents\n\t"
                             "Make sure files are in a dict with relevent key and"
                             " a value that is a path str or valid data\n\t")

        self.__doc_map = {}
        for roletype in self.schema.find_all("link:roletype"):
            self.__doc_map[roletype.find("link:definition").text.split(" - ")[-1]] = roletype['roleuri']

        uri_re = re.compile(r'((us-gaap|source|dei)[_|:]\w*)')

        self.labels = {}
        for l in self.lab.find('link:labellink').find_all(re.compile('(label$)')):
            uri = re.search(uri_re, l['xlink:label'])
            if uri:
                self.labels[uri.group(1).lower()] = l.text

        self.cells = collections.defaultdict(list)
        for node in self.data.find_all(uri_re):
            self.cells[node.name.replace(':', '_').lower()].append(node)

    def _docdata(self, x):
        try:
            if os.path.isfile(x):
                return open(x)
        finally:
            return x

    def get(self, search):
        if isinstance(search, re.Pattern):
            doc, name = next(((uri, name) for name, uri in self.__doc_map.items() if re.search(search, name)), (None, None))
        elif isinstance(search, str):
            doc, name = next(((uri, name) for name, uri in self.__doc_map.items() if search in name), (None, None))
        elif isinstance(search, FinancialStatement):
            doc, name = next(((uri, name) for name, uri in self.__doc_map.items() if re.search(search.value, name)), (None, None))
        else:
            raise ValueError(f"")

        if not doc:
            raise ValueError(f"No match found for {search} in names.\n\t"
                             f"Names available {[name for name in self.__doc_map.keys()]}]")

        if not isinstance(doc, pandas.DataFrame):
            doc = self.__assemble(doc)
            self.__doc_map[name] = doc

        return doc

    def __assemble(self, roleuri):
        class Loc:
            def __init__(self, label, id):
                self.label = label
                self.id = id

                self.order = None
                self.f = None
                self.t = []

            def to(self, to, order):
                if not (to in self.t or to.f):
                    self.t.append(to)
                    to.f = self
                    to.order = int(order)

            def list(self):
                l = [self.label]
                for loc in sorted(self.t, key=lambda l: l.order):
                    l.extend(loc.list())
                return l

            def __str__(self):
                return self.id


        prefix = self.ref_doc.value[1]
        def_link = self.ref.find(re.compile(fr'({prefix}link)', re.IGNORECASE), attrs={'xlink:role': roleuri})

        # Get Locs
        locs = {}
        for l in def_link.find_all(re.compile(r'loc', re.IGNORECASE)):
            label = l['xlink:href'].split('#')[1].lower()
            id = l['xlink:label'].lower()
            locs[id] = Loc(label, id)

        #print(1, locs)

        # Get arcs and make connections between locs
        arcs = set()
        for l in def_link.find_all(re.compile(fr'({prefix}arc)', re.IGNORECASE)):
            fro, to, order = locs[l['xlink:from'].lower()], locs[l['xlink:to'].lower()], l['order']
            fro.to(to, order)
            arcs.add(fro)

        #print(2, arcs)

        # Compress into a list of Rows
        rows = collections.OrderedDict()
        for top in [a for a in arcs if not a.f]:
            for atr in top.list():
                if atr.lower() in self.cells.keys():
                    rows[atr] = self.cells[atr.lower()]

        #print(3, rows)

        # Get all columns
        date_re = re.compile('((2[0-2][0-9]{2}).?(0[1-9]|1[1-2]).?(0[1-9]|[1-2][0-9]|31|30))')
        date_settings = {'DATE_ORDER': 'YMD', 'PREFER_DATES_FROM': 'past'}
        cols = collections.defaultdict(int)
        for atr, cells in rows.items():
            if cells:
                for c in cells:
                    ref = [dateparser.parse(r[0], settings=date_settings) for r in re.findall(date_re, c['contextref'])]
                    ref = tuple(ref) if len(ref) > 1 else (*ref, None)
                    c['contextref'] = ref
                    cols[ref] += 1

        # Remove columns that are not used typically
        cols = set([c for c, count in cols.items() if count > 2])

        #print(4, cols)

        # Chop off incorrect columns and reformat rows to reflect that
        for atr, cells in rows.items():
            if cells is not None:
                r = [c for c in cells if c['contextref'] in cols]
                rmap = {c['contextref']: c for c in r}
                rows[atr] = [rmap[col].text if col in rmap.keys() else None for col in cols]

        rows = {self.labels[atr]: [float(c) if c else None for c in cells] for atr, cells in rows.items()}
        return pandas.DataFrame.from_dict(rows, columns=cols, orient='index', dtype=float)

