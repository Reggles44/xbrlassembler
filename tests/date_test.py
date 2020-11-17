from xbrlassembler import DateParser


def test_date():
    invalid_date = "foobar"
    valid_date = "01012020"

    assert DateParser.parse(valid_date) is not None
    assert DateParser.parse(invalid_date) is None
