from app import safe_divide

def test_division_by_zero():
    assert safe_divide(10, 0) is None

def test_invalid_input():
    assert safe_divide("abc", 2) is None
