def calculate_cart_total(items, tax_rate):
    subtotal = sum(
        item["price"] * item["quantity"]
        for item in items
    )

    if not items:
        return 0

    tax = subtotal * tax_rate

    return round(subtotal + tax, 2)