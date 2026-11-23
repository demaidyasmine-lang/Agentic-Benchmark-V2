def calculate_discount(price, discount_rate):
    if price < 0 or discount_rate < 0 or discount_rate > 1:
        raise ValueError("Invalid price or discount rate")

    return price * (1 - discount_rate)