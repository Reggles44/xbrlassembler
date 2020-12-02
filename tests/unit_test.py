from tests import assembler_test, mkass
from xbrlassembler import FinancialStatement


def test_assembler():
    url = "https://www.sec.gov/Archives/edgar/data/1084869/000143774920009975/0001437749-20-009975-index.htm"

    assembler = mkass(url)
    assembler_test(assembler)
