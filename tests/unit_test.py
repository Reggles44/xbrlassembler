from tests import assembler_test
from xbrlassembler import XBRLAssembler, FinancialStatement


def test_assembler():
    url = "https://www.sec.gov/Archives/edgar/data/775057/0001445866-20-000590-index.htm"

    assembler_test(XBRLAssembler.from_sec_index(url))
