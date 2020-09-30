import os

import pytest

from tests import assembler_test, test_files_directory, save_index
from xbrlassembler import XBRLAssembler, XBRLError


@pytest.mark.xfail(raises=XBRLError)
def test_merge():
    urls = ["https://www.sec.gov/Archives/edgar/data/1084869/0001437749-20-002005-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-19-018360-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-19-022111-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-19-009426-index.htm,"
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-20-019622-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-20-009975-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-19-002107-index.htm"]

    json_path = os.path.join(test_files_directory, "test.json")

    for i, url in enumerate(urls):
        directory = save_index(url)
        assembler = XBRLAssembler.from_dir(directory)
        assembler.get_all()
        assembler.to_json(json_path)

    assembler = XBRLAssembler.from_json(json_path)
    assembler_test(assembler)
