import re
from datetime import datetime
from enum import Enum


class FinancialStatement(Enum):
    """A wrapper enum for common and tested regex to find specific documents"""
    INCOME_STATEMENT = re.compile(r"operation|income|earnings|revenues|loss", re.IGNORECASE)
    BALANCE_SHEET = re.compile(r"balance|condition|position|assets", re.IGNORECASE)
    DOCUMENT_INFORMATION = re.compile(r"cover.page|information", re.IGNORECASE)
    STOCK_HOLDER = re.compile(r"stockholder", re.IGNORECASE)
    CASH_FLOW = re.compile(r"cash.flow", re.IGNORECASE)
    NOTE = re.compile(r"statement.note", re.IGNORECASE)


class XBRLType(Enum):
    """A functional enum for categorizing XBRL documents into their respective use cases"""
    CALC = ("cal",)
    DEF = ("def",)
    PRE = ("pre",)
    LABEL = ("lab",)
    SCHEMA = ("sch", "xsd")
    DATA = ("xml", "ins")

    @classmethod
    def get(cls, item):
        """
        Class method to allow for categorization by string
        :param item: A string or object that can do `in` comparisons with a string
        :return:
        """
        item_ref = item.lower()[-7:]
        for xbrl_type in cls:
            if any(t in item_ref for t in xbrl_type.value):
                return xbrl_type


_year_digit = str(datetime.now().year)[-1]
_re_map = {'%Y': r'(2[0-2][0-9]{2})',
           '%y': fr'(0[1-9]|1[0-9]|2[0-{_year_digit}])',
           '%m': r'(0[1-9]|1[0-2])',
           '%d': r'(0[1-9]|[1-2][0-9]|30|31)',
           '%b': r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'}
_quarter_map = {'Q1': '0331',
                'Q2': '0630',
                'Q3': '0930',
                'Q4': '1231'}


class DateParser(Enum):
    """
    Functional enum that ties together regex with datetime format strings to
        allow for parsing strings into datetime objects
    """
    MONTH_STRING_DAY_YEAR = '%b%d%Y'
    YEAR_MONTH_DAY = '%Y%m%d'
    YEAR_HALF_MONTH_DAY = '%y%m%d'
    MONTH_DAY_YEAR = '%m%d%Y'
    DAY_MONTH_HALF_YEAR = '%d%b%Y'

    def pattern(self):
        """
        Creates a regex pattern based on a datetime string format
        :return: A regex compile of the assembled term
        """
        re_list = [_re_map[f'%{char}'] for char in str(self.value).split('%') if char]
        return re.compile(fr"({'.?'.join(re_list)})")

    @classmethod
    def find_format(cls, string):
        """
        Search function to fire a proper parser
        :param string: Raw date string to match to a parser
        :return: class:`xbrlassembler.DateParser` matching the string
        """
        for datetype in cls:
            if re.search(datetype.pattern(), string):
                return datetype

    @classmethod
    def make_date(cls, date_format, res):
        return datetime.strptime(f"{res[1]}{res[2]}{res[3]}", date_format.value)

    @classmethod
    def parse(cls, string):
        """
        Overarching parse function including all other functions

        :param string: Raw string that might include dates
        :return: Tuple of class:`datetime.datetime` objects found
        """
        if string is None:
            return

        for qtr, month_day in _quarter_map.items():
            string = string.replace(qtr, month_day)

        date_format = cls.find_format(string)
        if date_format:
            return tuple(cls.make_date(date_format, res) for res in re.findall(date_format.pattern(), string))
