import re
from enum import Enum

from xbrlassembler.assembler import XBRLAssembler, XBRLElement
from xbrlassembler.error import XBRLError


class FinancialStatement:
    INCOME_STATEMENT = re.compile('(operation|income|earnings|revenues|loss)', re.IGNORECASE)
    BALANCE_SHEET = re.compile('(balance|condition|position|assets)', re.IGNORECASE)
    DOCUMENT_INFORMATION = re.compile('(information)', re.IGNORECASE)
    STOCK_HOLDER = re.compile('(stockholder)', re.IGNORECASE)
    CASH_FLOW = re.compile('(cash.flow)', re.IGNORECASE)
    NOTE = re.compile('(statement.note)', re.IGNORECASE)
    INVALID = re.compile('\A(?!x)x')
