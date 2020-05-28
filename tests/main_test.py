import logging
import os
import re
import random
import traceback

import pandas
import requests
from bs4 import BeautifulSoup

from xbrlassembler import XBRLAssembler, FinancialStatement, XBRLError
from xbrlassembler.error import XBRLIndexError

file = os.path.join(os.getcwd(), 'parse_success.csv')
crawler = requests.get('https://www.sec.gov/Archives/edgar/full-index/crawler.idx')

logger = logging.getLogger('xbrlassembler')
logger.setLevel(logging.ERROR)

test_files = []


def get_files(tested={}, amount=0):
    for i, item in enumerate(crawler.text.split('\n')[5:]):
        if '10-k ' in item.lower() or '10-q ' in item.lower():
            item = re.split(r'\s{2,}', item)
            name, url = item[0], item[4]
            if url not in tested.keys():
                test_files.append((name, url))

            if i > amount if amount else False:
                break


def parse_files():
    if not test_files:
        get_files(amount=5)

    for name, url in test_files:
        print(name, url, ' ', end='')
        exception = parse(url)
        print(exception or "PASSED")
        yield name, url, exception


def parse(url):
    try:
        xbrl_assembler = XBRLAssembler.from_sec_index(index_url=url)
        income_statement = xbrl_assembler.get(FinancialStatement.INCOME_STATEMENT)
        balance_sheet = xbrl_assembler.get(FinancialStatement.BALANCE_SHEET)

        assert type(income_statement) == type(balance_sheet) == pandas.DataFrame
        assert not income_statement.empty and not balance_sheet.empty
    except XBRLIndexError:
        return None
    except Exception as e:
        return e


def test_main():
    for name, url, exc in parse_files():
        if exc:
            raise exc


if __name__ == '__main__':
    with open(file, 'r') as passed:
        tested = {}
        for l in passed.readlines():
            name, index_url = l.split(', ')
            tested[index_url.strip()] = name

    get_files(tested=tested)

    with open(file, 'a') as passed:
        for name, url, exc in parse_files():
            if not exc:
                passed.write(f"{name.replace(',', '')}, {url}\n")

