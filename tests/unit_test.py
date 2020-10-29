import pytest

from tests import assembler_test
from xbrlassembler import XBRLAssembler, XBRLError, FinancialStatement


def test_assembler():
    url = "https://www.sec.gov/Archives/edgar/data/1084869/000143774920009975/0001437749-20-009975-index.htm"

    assembler = XBRLAssembler.from_sec_index(url)
    assembler_test(assembler)

    print(assembler.cells["dei_EntityCommonStockSharesOutstanding".lower()])

    print(assembler.get(FinancialStatement.DOCUMENT_INFORMATION).visualize())
