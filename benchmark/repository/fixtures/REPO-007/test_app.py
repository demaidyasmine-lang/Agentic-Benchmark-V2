from app import calculate_cart_total

def test_cart_total_with_tax():
    items = [
        {"price": 10, "quantity": 2},
        {"price": 5, "quantity": 1},
    ]
    assert calculate_cart_total(items, 0.10) == 27.5

def test_empty_cart():
    assert calculate_cart_total([], 0.20) == 0
