import re

import requests
from bs4 import BeautifulSoup

from xbrlassembler import XBRLElement, XBRLAssembler, DateParser, XBRLType


def makes_exception(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
        return False
    except Exception:
        return True

def test_failure():
    test_element = XBRLElement(uri="Test123")
    test_child = XBRLElement(uri="Test_child")
    test_element.add_child("Idk something but not an element")
    test_element.add_child(test_child, order='first please')
    test_element.add_child(test_child)
    test_element.add_child(test_child)

    assert makes_exception(XBRLAssembler.from_sec_index, "google index please")
    assert makes_exception(XBRLAssembler.from_dir, 'Yolo directory')
    assert makes_exception(XBRLAssembler.from_sec_index, "https://www.sec.gov/Archives/edgar/data/1652044/0001652044-20-00002-index.htm")
    assert makes_exception(XBRLAssembler.from_json, None)

    google_index = "https://www.sec.gov/Archives/edgar/data/1652044/0001652044-20-000021-index.htm"
    google_assembler = XBRLAssembler.from_sec_index(google_index)
    google_assembler.merge(google_assembler)
    assert makes_exception(google_assembler.merge, None)
    assert makes_exception(google_assembler.get, 1)

    index_soup = BeautifulSoup(requests.get(google_index).text, 'lxml')

    data_files_table = index_soup.find('table', {'summary': 'Data Files'})

    file_map = {}
    for row in data_files_table('tr')[1:]:
        row = row.find_all('td')
        soup = BeautifulSoup(requests.get("https://www.sec.gov" + row[2].find('a')['href']).text, 'lxml')
        file_map[XBRLType.get(row[3].text)] = soup

    fm0 = {}
    fm1 = {XBRLType.SCHEMA: "None"}
    fm2 = {XBRLType.SCHEMA: file_map[XBRLType.SCHEMA], XBRLType.LABEL: "None"}
    fm3 = {XBRLType.SCHEMA: file_map[XBRLType.SCHEMA], XBRLType.LABEL: file_map[XBRLType.LABEL], XBRLType.DATA: "None"}
    fm4 = {XBRLType.SCHEMA: file_map[XBRLType.SCHEMA], XBRLType.LABEL: file_map[XBRLType.LABEL], XBRLType.DATA: file_map[XBRLType.DATA], XBRLType.PRE: "None"}

    for fm in [fm0, fm1, fm2, fm3, fm4]:
        assert makes_exception(XBRLAssembler._mta, file_map=fm, info=None, ref_doc=XBRLType.PRE)
