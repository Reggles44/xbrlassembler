from tests import assembler_test, save_index
from xbrlassembler import XBRLAssembler


def test_files():
    google_index = "https://www.sec.gov/Archives/edgar/data/1781983/0001558370-20-006741-index.htm"
    assembler_test(XBRLAssembler.from_dir(save_index(google_index)))


if __name__ == '__main__':
    test_files()
