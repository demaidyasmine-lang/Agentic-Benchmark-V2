def is_valid_email(email):
    if not email:
        return False

    local, domain = email.rsplit('@', 1)
    if not domain:
        return False

    return bool(local and domain)