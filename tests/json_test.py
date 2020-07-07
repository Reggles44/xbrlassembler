import os

from tests import assembler_test
from xbrlassembler import XBRLAssembler, FinancialStatement


def test_json():
    google_index = "https://www.sec.gov/Archives/edgar/data/1781983/0001558370-20-006741-index.htm"
    test_file = os.path.join(os.getcwd(), 'test.json')

    download_assembler = XBRLAssembler.from_sec_index(index_url=google_index)
    download_assembler.get_all()
    download_assembler.to_json(test_file)

    assembler_test(XBRLAssembler.from_json(test_file))

