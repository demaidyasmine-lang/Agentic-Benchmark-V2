def safe_divide(a, b):
    try:
        if not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
            return None
        return float(a) / float(b)
    except ZeroDivisionError:
        return None