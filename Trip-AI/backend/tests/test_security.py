"""app.core.security 的单元测试"""
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_is_not_plaintext():
    """哈希结果不应等于明文密码"""
    assert hash_password("123456") != "123456"


def test_hash_password_is_random_each_time():
    """两次哈希同一密码，结果应不同（随机盐）"""
    assert hash_password("123456") != hash_password("123456")


def test_verify_password_with_correct_password():
    """正确密码应通过校验"""
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True


def test_verify_password_with_wrong_password():
    """错误密码应校验失败"""
    hashed = hash_password("mypassword")
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_token_roundtrip():
    """JWT 生成后能解回原始 user_id"""
    token = create_access_token(user_id=42)
    payload = decode_token(token)
    assert payload["sub"] == "42"
