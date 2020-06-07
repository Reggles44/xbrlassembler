from tests import assembler_test
from xbrlassembler import XBRLAssembler, FinancialStatement


def test_assembler():
    url = "https://www.sec.gov/Archives/edgar/data/732717/0001562762-20-000171-index.htm"

    assembler_test(XBRLAssembler.from_sec_index(url))
