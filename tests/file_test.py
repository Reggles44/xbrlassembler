import os

import pandas
import requests
from bs4 import BeautifulSoup

from xbrlassembler import XBRLAssembler, FinancialStatement, XBRLElement


def test_files():
    directory = os.path.abspath(os.path.join(os.getcwd(), 'test files'))
    os.makedirs(directory, exist_ok=True)

    google_index = "https://www.sec.gov/Archives/edgar/data/1652044/0001652044-20-000021-index.htm"
    index_soup = BeautifulSoup(requests.get(google_index).text, 'lxml')

    for row in index_soup.find('table', {'summary': 'Data Files'})('tr')[1:]:
        row = row.find_all('td')
        link = "https://www.sec.gov" + row[2].find('a')['href']
        file_name = link.rsplit('/', 1)[1]
        with open(os.path.abspath(os.path.join(directory, file_name)), 'w+') as file:
            file.write(requests.get(link).text)

    xbrl_assembler = XBRLAssembler.from_dir(directory=directory)
    income_statement = xbrl_assembler.get(FinancialStatement.INCOME_STATEMENT)
    balance_sheet = xbrl_assembler.get(FinancialStatement.BALANCE_SHEET)

    assert type(income_statement) == type(balance_sheet) == XBRLElement
    assert income_statement._children and balance_sheet._children
    assert type(income_statement.to_dataframe()) == type(balance_sheet.to_dataframe()) == pandas.Dataframe
    assert type(income_statement.to_dict()) == type(balance_sheet.to_dict()) == dict

