import logging
import os
import re
from collections.abc import Iterable

import requests
from bs4 import BeautifulSoup

from xbrlassembler import XBRLElement, XBRLAssembler

logging.basicConfig(level=logging.ERROR)
logging.getLogger('xbrlassembler').setLevel(logging.DEBUG)
logging.getLogger('xbrlassembler').debug("Starting Test")

test_files_directory = os.path.abspath(os.path.join(os.getcwd(), 'test files'))
os.makedirs(test_files_directory, exist_ok=True)


def save_index(index_url):
    id = index_url[index_url.rfind('/')+1:].replace("-index.htm", "")
    directory = os.path.join(test_files_directory, id)
    os.makedirs(directory, exist_ok=True)

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

    index_soup = BeautifulSoup(requests.get(index_url).text, 'lxml')

    for row in index_soup.find('table', {'summary': 'Data Files'})('tr')[1:]:
        row = row.find_all('td')
        link = "https://www.sec.gov" + row[2].find('a')['href']
        file_name = link.rsplit('/', 1)[1]
        with open(os.path.abspath(os.path.join(directory, file_name)), 'w+') as file:
            file.write(requests.get(link).text)

    return directory


def assembler_test(xbrl_assembler: XBRLAssembler):
    for uri, ele in xbrl_assembler.xbrl_elements.items():
        assert isinstance(ele, XBRLElement)
        assert isinstance(ele.search(re.compile('.')), XBRLElement)
        assert isinstance(ele.head(), XBRLElement)
        assert isinstance(ele.items(), Iterable)
        assert isinstance(ele.to_json(), dict)
        assert isinstance(ele.ids(), dict)
        assert isinstance(ele.references(), Iterable)
        assert isinstance(ele.visualize(), str)
        assert isinstance(ele.ids(), dict)
        assert isinstance([x for x in ele.items()], list)
