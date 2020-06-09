from tests import assembler_test
from xbrlassembler import XBRLAssembler, FinancialStatement


def test_assembler():
    url = "https://www.sec.gov/Archives/edgar/data/1095073/0001095073-20-000018-index.htm"

    assembler_test(XBRLAssembler.from_sec_index(url))
