from app import is_valid_email

def test_reject_email_without_domain():
    assert is_valid_email("user@") is False

def test_accept_valid_email():
    assert is_valid_email("user@example.com") is True
