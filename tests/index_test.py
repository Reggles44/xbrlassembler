from tests import assembler_test
from xbrlassembler import XBRLAssembler


def test_index():
    google_index = "https://www.sec.gov/Archives/edgar/data/1781983/0001558370-20-006741-index.htm"
    assembler_test(XBRLAssembler.from_sec_index(index_url=google_index))
