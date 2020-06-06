import os

import requests
from bs4 import BeautifulSoup

from tests import assembler_test
from xbrlassembler import XBRLAssembler


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

    assembler_test(XBRLAssembler.from_dir(directory=directory))

