from app import normalize_name

def test_normalize_multiple_spaces():
    assert normalize_name("  Alice   Smith  ") == "alice-smith"

def test_normalize_uppercase():
    assert normalize_name("JOHN DOE") == "john-doe"
