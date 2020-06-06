import logging
import random
import re

import requests

from tests import assembler_test
from xbrlassembler import XBRLAssembler

logger = logging.getLogger('xbrlassembler')
logger.setLevel(logging.ERROR)

test_files = []


def test_index():
    crawler = requests.get('https://www.sec.gov/Archives/edgar/full-index/crawler.idx')
    for item in random.choices(crawler.text.split('\n')[5:], k=10):
        if '10-k ' in item.lower() or '10-q ' in item.lower():
            item = re.split(r'\s{2,}', item)
            name, url = item[0], item[4]

            assembler_test(XBRLAssembler.from_sec_index(index_url=url))
