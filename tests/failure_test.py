from xbrlassembler import XBRLElement, XBRLAssembler


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

    assert makes_exception(XBRLAssembler, "info", "schema", "data", "label", "ref")
    assert makes_exception(XBRLAssembler.from_sec_index, "google index please")