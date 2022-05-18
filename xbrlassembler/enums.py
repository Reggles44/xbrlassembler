import re
from datetime import datetime
from enum import Enum


class FinancialStatement(Enum):
    """A wrapper enum for common and tested regex to find specific documents"""
    INCOME_STATEMENT = (
        'operation',
        'income',
        'earnings',
        'revenues',
        'loss'
    )
    BALANCE_SHEET = (
        'balance',
        'condition',
        'position',
        'assets'
    )
    DOCUMENT_INFORMATION = (
        'information',
    )
    STOCK_HOLDER = (
        'stockholder',
    )
    CASH_FLOW = (
        'cash.flow',
    )
    NOTE = (
        'statement.note',
    )
    INVALID = ()

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            value = value.lower()
            for stmt in cls:
                if any(re.search(kw, value) for kw in stmt.value):
                    return stmt
        return cls.INVALID


class XBRLType(Enum):
    """A functional enum for categorizing XBRL documents into their respective use cases"""
    CALC = ("cal",)
    DEF = ("def",)
    PRE = ("pre",)
    LABEL = ("lab",)
    SCHEMA = ("sch", "xsd")
    DATA = ("xml", "ins")

    @classmethod
    def _missing_(cls, value: object):
        """
        Class method to allow for categorization by string
        :param item: A string or object that can do `in` comparisons with a string
        :return:
        """
        if isinstance(value, str):
            value = value.lower()[-7:]
            for xbrl_type in cls:
                if any(t in value for t in xbrl_type.value):
                    return xbrl_type
