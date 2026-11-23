from app import calculate_discount


def test_discount_calculation():
    assert calculate_discount(100, 0.20) == 80


def test_half_discount():
    assert calculate_discount(100, 0.50) == 50
