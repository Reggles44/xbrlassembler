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


def test_main():
    passed = open(file, 'a') if __name__ == '__main__' else None
    if not test_files:
        get_files(5)

    for i, (name, url) in enumerate(test_files):
        try:
            print(name, ' ', end='')
            parse(name, url)
            if __name__ == '__main__':
                passed.write(f'{name.replace(",", "")}, {url}\n')
            print("PASSED")
        except XBRLIndexError as e:
            print("Index Error", url)
        except Exception as e:
            print("URL", url)
            #traceback.print_exc()

def get_files(amount=0):
    tested = {}
    if __name__ == '__main__':
        with open(file, 'r') as passed:
            for l in passed.readlines():
                name, index_url = l.split(', ')
                tested[index_url.strip()] = name

    for i, item in enumerate(crawler.text.split('\n')[5:]):
        if '10-k ' in item.lower() or '10-q ' in item.lower():
            item = re.split('\s{2,}', item)
            name, url = item[0], item[4]
            if url not in tested.keys():
                test_files.append((name, url))

            if i > amount if amount else False:
                break


def parse(name, url):
    xbrl_assembler = XBRLAssembler.from_sec_index(index_url=url)
    income_statement = xbrl_assembler.get(FinancialStatement.INCOME_STATEMENT)
    balance_sheet = xbrl_assembler.get(FinancialStatement.BALANCE_SHEET)

    assert type(income_statement) == type(balance_sheet) == pandas.DataFrame
    assert not income_statement.empty and not balance_sheet.empty


if __name__ == '__main__':
    get_files()
    test_main()
