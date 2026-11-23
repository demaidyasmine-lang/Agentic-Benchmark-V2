def filter_active_users(users):
    return [
        user for user in users
        if user.get("active") is False
    ]
