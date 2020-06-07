import os
from collections import Iterable
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from xbrlassembler import XBRLElement, FinancialStatement

directory = os.path.abspath(os.path.join(os.getcwd(), 'test files'))
os.makedirs(directory, exist_ok=True)


def delete_dir():
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)


def save_index(index_url):
    delete_dir()
    index_soup = BeautifulSoup(requests.get(index_url).text, 'lxml')

    for row in index_soup.find('table', {'summary': 'Data Files'})('tr')[1:]:
        row = row.find_all('td')
        link = "https://www.sec.gov" + row[2].find('a')['href']
        file_name = link.rsplit('/', 1)[1]
        with open(os.path.abspath(os.path.join(directory, file_name)), 'w+') as file:
            file.write(requests.get(link).text)


def assembler_test(xbrl_assembler):
    income_statement = xbrl_assembler.get(FinancialStatement.INCOME_STATEMENT)
    balance_sheet = xbrl_assembler.get(FinancialStatement.BALANCE_SHEET)

    for uri, date in income_statement.references().items():
        print(uri, date)
    print(income_statement.visualize())

    for uri, date in balance_sheet.references().items():
        print(uri, date)
    print(balance_sheet.visualize())

    assert type(income_statement) == type(balance_sheet) == XBRLElement
    assert income_statement._children and balance_sheet._children
    assert type(income_statement.to_dict()) == type(balance_sheet.to_dict()) == dict

    income_ref = income_statement.references()
    balance_ref = balance_sheet.references()

    assert isinstance(income_ref, Iterable) or isinstance(balance_ref, Iterable)

    for ref, date in income_ref.items():
        print(ref, date, type(date[0]))
    for ref, date in balance_ref.items():
        print(ref, date, type(date[0]))

    assert all(isinstance(ref[0], datetime) or ref[0] == None for ref in income_ref.values()) and \
           all(isinstance(ref[0], datetime) or ref[0] == None for ref in balance_ref.values())
