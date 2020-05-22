import re

import pandas
import requests
from bs4 import BeautifulSoup

from xbrlassembler import XBRLAssembler, FinancialStatement


def test_main():
    crawler = requests.get('https://www.sec.gov/Archives/edgar/full-index/crawler.idx')

    item = next(
        re.split('\s{2,}', i) for i in crawler.text.split('\n')[5:] if '10-k ' in i.lower() or '10-q ' in i.lower())
    name, url = item[0], item[4]

    index_soup = BeautifulSoup(requests.get(url).text, 'lxml')

    files = {}
    for row in index_soup.find('table', {'summary': 'Data Files'})('tr')[1:]:
        row = row.find_all('td')
        files[row[3].text] = requests.get("https://www.sec.gov" + row[2].find('a')['href']).text

    xbrl_assembler = XBRLAssembler(files)

    income_statement = xbrl_assembler.get(FinancialStatement.INCOME_STATEMENT)
    balance_sheet = xbrl_assembler.get(FinancialStatement.BALANCE_SHEET)

    assert type(income_statement) == type(balance_sheet) == pandas.DataFrame
    assert not income_statement.empty and not balance_sheet.empty


if __name__ == '__main__':
    test_main()
