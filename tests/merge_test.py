import os

import pytest

from tests import assembler_test, test_files_directory, save_index
from xbrlassembler import XBRLAssembler, XBRLError


def test_merge():
    urls = ["https://www.sec.gov/Archives/edgar/data/1084869/0001437749-20-002005-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-19-018360-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-19-022111-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-19-009426-index.htm,"
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-20-019622-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-20-009975-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-19-002107-index.htm"]

    assemblers = [XBRLAssembler.from_sec_index(url) for url in urls]

    main = assemblers[0]
    for other in assemblers[1:]:
        main.merge(other)

    assembler_test(main)
