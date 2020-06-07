from tests import assembler_test
from xbrlassembler import XBRLAssembler, FinancialStatement


def test_assembler():
    url = "https://www.sec.gov/Archives/edgar/data/764180/0000764180-20-000048-index.htm"

    assembler_test(XBRLAssembler.from_sec_index(url))
