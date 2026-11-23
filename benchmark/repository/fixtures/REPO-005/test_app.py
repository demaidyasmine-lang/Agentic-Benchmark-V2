from app import filter_active_users

def test_filter_only_active_users():
    users = [
        {"name": "Alice", "active": True},
        {"name": "Bob", "active": False},
        {"name": "Charlie", "active": True},
    ]
    result = filter_active_users(users)
    assert [user["name"] for user in result] == ["Alice", "Charlie"]

def test_empty_users():
    assert filter_active_users([]) == []
