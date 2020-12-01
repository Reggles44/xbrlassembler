import os

from tests import test_files_directory, assembler_test, mkass
from xbrlassembler import XBRLAssembler


def test_json():
    google_index = "https://www.sec.gov/Archives/edgar/data/1781983/0001558370-20-006741-index.htm"

    json_file = os.path.join(test_files_directory, "test.json")

    mkass(google_index).to_json(json_file)
    assembler_test(XBRLAssembler.from_json(json_file))
