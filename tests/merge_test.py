import urllib3
from bs4 import BeautifulSoup

from tests import assembler_test
from xbrlassembler import XBRLAssembler, XBRLType

http = urllib3.PoolManager(maxsize=10, block=True)


def mkass(url):
    file_map = {}

    index_request = http.request('GET', url)
    index_soup = BeautifulSoup(index_request.data, 'lxml')
    data_files_table = index_soup.find('table', {'summary': 'Data Files'})
    if data_files_table:

        for row in data_files_table('tr')[1:]:
            link = "https://www.sec.gov" + row.find_all('td')[2].find('a')['href']

            xbrl_type = XBRLType.get(link.rsplit('/', 1)[1])
            if xbrl_type:
                xbrl_request = http.request('GET', link)
                file_map[xbrl_type] = BeautifulSoup(xbrl_request.data, 'lxml')

    return XBRLAssembler._mta(file_map=file_map, info=url, ref_doc=XBRLType.PRE)


def test_merge():
    urls = ["https://www.sec.gov/Archives/edgar/data/1084869/0001437749-20-002005-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-19-018360-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-19-022111-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-19-009426-index.htm,"
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-20-019622-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-20-009975-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-19-002107-index.htm"]

    assemblers = [mkass(url) for url in urls]

    main = assemblers[0].merge(*assemblers[1:])

    for other in assemblers[1:]:
        main.merge(other)

    assembler_test(main)


if __name__ == '__main__':
    test_merge()
