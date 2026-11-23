def safe_divide(a, b):
    try:
        return float(a) / float(b)
    except ZeroDivisionError:
        return None
