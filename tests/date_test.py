from xbrlassembler.utils import parse_datetime


def test_date():
    invalid_date = "foobar"
    valid_date = "01012020-12312020"

    assert parse_datetime(None) is None
    assert parse_datetime(valid_date) is not None
    assert parse_datetime(invalid_date) is None
