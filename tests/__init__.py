import logging
import os
import re
from collections.abc import Iterable
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from xbrlassembler import XBRLElement, FinancialStatement, XBRLAssembler

logging.basicConfig(level=logging.ERROR)
logging.getLogger('xbrlassembler')

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


def assembler_test(xbrl_assembler: XBRLAssembler):
    xbrl_assembler.get(FinancialStatement.DOCUMENT_INFORMATION)
    xbrl_assembler.get_all()

    for uri, ele in xbrl_assembler.xbrl_elements.items():
        assert isinstance(ele, XBRLElement)
        assert isinstance(ele.search(re.compile('.')), XBRLElement)
        assert isinstance(ele.head(), XBRLElement)
        assert isinstance(ele.items(), Iterable)
        assert isinstance(ele.to_json(), dict)
        assert isinstance(ele.ids(), dict)
        assert isinstance(ele.references(), Iterable)
