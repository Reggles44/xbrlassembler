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


def test_main():
    tested = {}
    with open(file, 'r') as passed:
        for l in passed.readlines():
            name, index_url = l.split(', ')
            tested[index_url.strip()] = name

    with open(file, 'a') as passed:
        files = []
        for i in crawler.text.split('\n')[5:]:
            if '10-k ' in i.lower() or '10-q ' in i.lower():
                item = re.split('\s{2,}', i)
                name, url = item[0], item[4]
                if url not in tested.keys():
                    files.append((name, url))

        for name, url in files:
            try:
                print(name, ' ', end='')
                parse(name, url)
                print("PASSED")
                passed.write(f'{name.replace(",", "")}, {url}\n')
            except XBRLIndexError as e:
                print("Index Error", url)
            except Exception as e:
                print("URL", url)
                #traceback.print_exc()
                #break


def parse(name, url):
    xbrl_assembler = XBRLAssembler.from_sec_index(index_url=url)
    income_statement = xbrl_assembler.get(FinancialStatement.INCOME_STATEMENT)
    balance_sheet = xbrl_assembler.get(FinancialStatement.BALANCE_SHEET)

    #print("Type Check = ", type(income_statement) == type(balance_sheet) == pandas.DataFrame)
    #print("Empty Check = ", not income_statement.empty and not balance_sheet.empty)

    #print(income_statement)
    #print(balance_sheet)

    assert type(income_statement) == type(balance_sheet) == pandas.DataFrame
    assert not income_statement.empty and not balance_sheet.empty


if __name__ == '__main__':
    test_main()
