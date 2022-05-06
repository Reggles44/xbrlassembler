import os
import re
from typing import Iterable

import pytest

from conftest import XBRL_RESOURCE_FILES
from tests import makes_exception, fetch_resource_files, RESOURCE_DIR
from xbrlassembler import XBRLAssembler, XBRLElement, FinancialStatement


BASE_XBRL_URL = 'https://www.sec.gov/Archives/edgar/data/1781983/0001558370-20-006741-index.htm'


def assembler_test(xbrl_assembler: XBRLAssembler):
    assert isinstance(xbrl_assembler.__repr__(), str)
    for uri, ele in xbrl_assembler.xbrl_elements.items():
        assert isinstance(ele, XBRLElement)
        # assert isinstance(ele.search(uri=lambda _: True), XBRLElement)
        # assert all(isinstance(ele, XBRLElement) for ele in ele.findall(lambda _: True))
        assert isinstance(ele.head(), XBRLElement)
        assert isinstance(ele.to_json(), dict)
        assert isinstance(ele.refs(), Iterable)
        assert isinstance(ele.visualize(), str)


def test_xbrl_assembler():
    assembler = XBRLAssembler.from_dir(XBRL_RESOURCE_FILES)
    assembler_test(assembler)
    assert assembler.find(uri=re.compile('us-gaap_cash', re.IGNORECASE))


@pytest.mark.parametrize('dir', ('Inavlid Dir', None))
def test_invalid_dir(dir):
    assert makes_exception(XBRLAssembler.from_dir, dir)


def test_invalid_json():
    assert makes_exception(XBRLAssembler.from_json, None)


def test_merge():
    urls = ["https://www.sec.gov/Archives/edgar/data/1084869/0001437749-20-002005-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-19-018360-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-19-022111-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-19-009426-index.htm,"
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-20-019622-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-20-009975-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-19-002107-index.htm"]

    assemblers = [fetch_resource_files(url, os.path.join(RESOURCE_DIR, 'merge', str(i))) for i, url in enumerate(urls, 1)]

    main = assemblers[0]
    main.merge(*assemblers[1:])

    assembler_test(main)


def test_json():
    json_file = os.path.join(RESOURCE_DIR, "test.json")
    XBRLAssembler.from_dir(XBRL_RESOURCE_FILES).to_json(json_file)
    assembler_test(XBRLAssembler.from_json(json_file))
