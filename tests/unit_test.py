import pytest

from tests import assembler_test
from xbrlassembler import XBRLAssembler, XBRLError


@pytest.mark.xfail(raises=XBRLError)
def test_assembler():
    url = "https://www.sec.gov/Archives/edgar/data/712537/0000712537-20-000012-index.htm"

    assembler_test(XBRLAssembler.from_sec_index(url))
