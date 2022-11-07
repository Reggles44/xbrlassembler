import json
import os
import re
import pytest

from conftest import XBRL_RESOURCE_FILES
from tests import makes_exception, fetch_resource_files, RESOURCE_DIR
from xbrlassembler import XBRLAssembler, XBRLElement, FinancialStatement


BASE_XBRL_URL = 'https://www.sec.gov/Archives/edgar/data/1781983/0001558370-20-006741-index.htm'


def test_xbrl_assembler():
    xbrl_assembler = XBRLAssembler.parse_dir(XBRL_RESOURCE_FILES)

    for uri, ele in xbrl_assembler.items():
        assert isinstance(ele, XBRLElement)
        assert ele.head
        assert isinstance(ele.head, XBRLElement)

    income_statement = xbrl_assembler.get(FinancialStatement.INCOME_STATEMENT)
    assert income_statement.find()
    for sub_ele in income_statement.find(first=False):
        assert isinstance(sub_ele, XBRLElement)

    for sub_ele in income_statement.find(first=False, uri=re.compile('cash')):
        assert isinstance(sub_ele, XBRLElement)


def test_json():
    with open(os.path.join(RESOURCE_DIR, "test.json"), 'w+') as json_file:
        json.dump(XBRLAssembler.parse_dir(XBRL_RESOURCE_FILES), json_file)

    with open(os.path.join(RESOURCE_DIR, "test.json"), 'r') as json_file:
        XBRLAssembler.parse_json(json_file)


@pytest.mark.parametrize('dir', ('Inavlid Dir', None))
def test_invalid_dir(dir):
    assert makes_exception(XBRLAssembler.parse_dir, dir)


def test_invalid_json():
    assert makes_exception(XBRLAssembler.parse_json, None)
