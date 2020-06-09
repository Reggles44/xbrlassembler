from tests import assembler_test, directory, save_index
from xbrlassembler import XBRLAssembler


def test_files():
    google_index = "https://www.sec.gov/Archives/edgar/data/1781983/0001558370-20-006741-index.htm"
    save_index(google_index)

    assembler_test(XBRLAssembler.from_dir(directory=directory))

