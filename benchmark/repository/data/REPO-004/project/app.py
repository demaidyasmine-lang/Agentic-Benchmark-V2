def sort_products(products):
    return sorted(
        products,
        key=lambda product: product["price"]
    )