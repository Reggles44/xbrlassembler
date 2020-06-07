import re
from datetime import datetime
from enum import Enum


class FinancialStatement(Enum):
    """A wrapper enum for common and tested regex to find specific documents"""
    INCOME_STATEMENT = re.compile(r"operation|income|earnings|revenues|loss", re.IGNORECASE)
    BALANCE_SHEET = re.compile(r"balance|condition|position|assets", re.IGNORECASE)


class XBRLType(Enum):
    """A functional enum for categorizing XBRL documents into their respective use cases"""
    # Choose One
    CALC = ("CAL",), "calculation"
    DEF = ("DEF",), "definition"
    PRE = ("PRE",), "presentation"

    # Required
    LAB = ("LAB",), None
    SCHEMA = ("SCH", "XSD"), None
    DATA = ("XML", "INS"), None

    @classmethod
    def get(cls, item):
        """
        Class method to allow for categorization by string
        :param item:
        :return:
        """
        item = item.lower()
        for xbrl_type in cls:
            if any([t.lower() in item for t in xbrl_type.value[0]]):
                return xbrl_type


_re_map = {'%Y': r'(2[0-2][0-9]{2})',
           '%y': r'(0[1-9]|[1-2][0-9])',
           '%m': r'(0[1-9]|1[0-2])',
           '%d': r'(0[1-9]|[1-2][0-9]|31|30)',
           '%b': r'([A-Z][a-z]{2}|[a-z]{3})'}
_quarter_map = {'Q1': '0331',
                'Q2': '0630',
                'Q3': '0930',
                'Q4': '1231'}

class DateParser(Enum):
    """
    Functional enum that ties together regex with datetime format strings to
        allow for parsing strings into datetime objects
    """
    YEAR_MONTH_DAY = '%Y%m%d'
    YEAR_HALF_MONTH_DAY = '%y%m%d'
    MONTH_DAY_YEAR = '%m%d%Y'
    MONTH_STRING_DAY_YEAR = '%b%d%Y'

    def pattern(self):
        """
        Creates a regex pattern based on a datetime string format
        :param date_pattern: A datetime string format
        :return: A regex compile of the assembled term
        """
        re_list = [_re_map[f'%{char}'] for char in str(self.value).split('%') if char]
        return re.compile(fr"({'.?'.join(re_list)})")

    def get_date(self, raw):
        """
        Parser function to remove unwanted characters and attempt to turn the string into a datetime object
        :param raw: String containing a date
        :return: class:`datetime.datetime` with the specified date
        """
        cleaned = re.sub(r'[^0-9A-Za-z]', '', raw)
        return datetime.strptime(cleaned, self.value)

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
    def parse(cls, string):
        """
        Overarching parse function including all other functions

        :param string: Raw string that might include dates
        :return: Tuple of class:`datetime.datetime` objects found
        """
        for qtr, month_day in _quarter_map.items():
            string = string.replace(qtr, month_day)

        date_re = cls.find_format(string)
        if not date_re:
            return (None,)

        return tuple([date_re.get_date(raw_date[0]) for raw_date in re.findall(date_re.pattern(), string)])
