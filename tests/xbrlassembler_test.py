import json
import os
import re
from typing import Iterable

import pytest

from conftest import XBRL_RESOURCE_FILES
from tests import makes_exception, fetch_resource_files, RESOURCE_DIR
from xbrlassembler import XBRLAssembler, XBRLElement, FinancialStatement


BASE_XBRL_URL = 'https://www.sec.gov/Archives/edgar/data/1781983/0001558370-20-006741-index.htm'


def test_xbrl_assembler():
    xbrl_assembler = XBRLAssembler.parse_dir(XBRL_RESOURCE_FILES)

    assert isinstance(xbrl_assembler.__repr__(), str)
    for uri, ele in xbrl_assembler.xbrl_elements.items():
        assert isinstance(ele, XBRLElement)
        # assert isinstance(ele.search(uri=lambda _: True), XBRLElement)
        # assert all(isinstance(ele, XBRLElement) for ele in ele.findall(lambda _: True))
        assert isinstance(ele.head(), XBRLElement)
        assert isinstance(ele.to_json(), dict)
        assert isinstance(ele.refs(), Iterable)
        assert isinstance(ele.iter(), Iterable)
        assert isinstance(ele.visualize(), str)

    income_statement = xbrl_assembler.get(FinancialStatement.INCOME_STATEMENT)
    assert income_statement.find()
    for sub_ele in income_statement.findall():
        assert isinstance(sub_ele, XBRLElement)

    for sub_ele in income_statement.findall(uri=re.compile('cash')):
        assert isinstance(sub_ele, XBRLElement)


def test_json():
    with open(os.path.join(RESOURCE_DIR, "test.json"), 'w') as json_file:
        json.dump(XBRLAssembler.parse_dir(XBRL_RESOURCE_FILES).to_json(), json_file)

    with open(os.path.join(RESOURCE_DIR, "test.json"), 'r') as json_file:
        XBRLAssembler.from_json(json.load(json_file))


@pytest.mark.parametrize('dir', ('Inavlid Dir', None))
def test_invalid_dir(dir):
    assert makes_exception(XBRLAssembler.parse_dir, dir)


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

    assemblers = []
    for i, url in enumerate(urls, 1):
        assemblers.append(fetch_resource_files(url, os.path.join(RESOURCE_DIR, 'merge', str(i))))

    main = assemblers[0]
    main.merge(*assemblers[1:])
