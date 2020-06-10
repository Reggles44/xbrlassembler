import random
import re

import pytest
import requests

from tests import assembler_test
from xbrlassembler import XBRLAssembler, XBRLError


@pytest.mark.xfail(raises=XBRLError)
def test_index():
    crawler = requests.get('https://www.sec.gov/Archives/edgar/full-index/crawler.idx')
    files = []
    for item in crawler.text.split('\n')[5:]:
        if '10-k ' in item.lower() or '10-q ' in item.lower():
            files.append(re.split(r'\s{2,}', item)[4])

    for url in random.choices(files, k=10):
        assembler_test(XBRLAssembler.from_sec_index(index_url=url))
