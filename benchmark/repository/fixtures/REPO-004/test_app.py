from app import sort_products

def test_sort_products_ascending():
    products = [
        {"name": "B", "price": 20},
        {"name": "A", "price": 10},
        {"name": "C", "price": 30},
    ]
    result = sort_products(products)
    assert [p["price"] for p in result] == [10, 20, 30]

def test_sort_empty_products():
    assert sort_products([]) == []
