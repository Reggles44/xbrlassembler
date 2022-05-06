import logging
import os
import requests
from bs4 import BeautifulSoup

from xbrlassembler import XBRLAssembler

logger = logging.getLogger()

RESOURCE_DIR = os.path.join(os.getcwd(), 'resource_dir')
os.makedirs(RESOURCE_DIR, exist_ok=True)

XBRL_RESOURCE_FILES = os.path.join(RESOURCE_DIR, 'xbrl')
os.makedirs(XBRL_RESOURCE_FILES, exist_ok=True)


def makes_exception(func,  *args, **kwargs):
    try:
        func(*args, **kwargs)
        return False
    except:
        return True


def get(url):
    logger.debug(url)
    response = requests.get(url, headers={'User-Agent': 'Company Name myname@company.com'})
    response.raise_for_status()
    return response


def fetch_resource_files(index_url, dir=XBRL_RESOURCE_FILES):
    os.makedirs(dir, exist_ok=True)

    index_response = get(index_url)
    if not index_response:
        return

    index_soup = BeautifulSoup(index_response.content, 'lxml')
    data_files_table = index_soup.find('table', {'summary': 'Data Files'})
    if not data_files_table:
        return

    for row in data_files_table('tr')[1:]:
        link = "https://www.sec.gov" + row.find_all('td')[2].find('a')['href']
        file_name = link.rsplit('/', 1)[1]
        file_path = os.path.join(dir, file_name)
        if os.path.isfile(file_path):
            continue

        file = get(link)
        if not file:
            continue

        open(file_path, 'wb+').write(file.content)

    return XBRLAssembler.from_dir(dir)