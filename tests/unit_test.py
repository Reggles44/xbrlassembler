from tests import assembler_test
from xbrlassembler import XBRLAssembler, FinancialStatement


def test_assembler():
    url = "https://www.sec.gov/Archives/edgar/data/1781983/0001558370-20-006741-index.htm"

    assembler_test(XBRLAssembler.from_sec_index(url))
