from tests import assembler_test
from xbrlassembler import XBRLAssembler, FinancialStatement


def test_assembler():
    url = "https://www.sec.gov/Archives/edgar/data/38723/0001376474-20-000115-index.htm"

    assembler_test(XBRLAssembler.from_sec_index(url))
