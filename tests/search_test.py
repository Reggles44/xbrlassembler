import re

from tests import assembler_test, mkass
from xbrlassembler import FinancialStatement


def test_assembler():
    url = "https://www.sec.gov/Archives/edgar/data/1084869/000143774920022923/0001437749-20-022923-index.htm"

    assembler = mkass(url)

    info = assembler.get(FinancialStatement.DOCUMENT_INFORMATION)
    ticker = info.search(uri=re.compile('trading.?symbol'), value=re.compile(r'^[A-Z]{1,6}$'))
    assert ticker
