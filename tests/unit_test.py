from tests import assembler_test
from xbrlassembler import XBRLAssembler


def test_assembler():
    url = "https://www.sec.gov/Archives/edgar/data/842013/0001213900-20-009083-index.htm"

    assembler_test(XBRLAssembler.from_sec_index(url))
