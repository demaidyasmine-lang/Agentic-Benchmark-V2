def is_valid_email(email):
    if not email:
        return False

    return "@" in email
