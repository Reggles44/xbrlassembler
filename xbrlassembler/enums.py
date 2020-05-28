import re
from enum import Enum


class FinancialStatement(Enum):
    INCOME_STATEMENT = re.compile(r"operation|income|earnings|revenues|loss", re.IGNORECASE)
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
    def get(cls, item):
        if isinstance(item, cls):
            return item

        item = item.lower()
        for xbrl_type in cls:
            if any([t.lower() in item for t in xbrl_type.value[0]]):
                return xbrl_type
