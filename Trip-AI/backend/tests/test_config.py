"""app.config 的单元测试"""
import pytest
from pydantic import ValidationError

from app.config import Settings


def test_get_cors_origins_list_splits_and_trims():
    """CORS 列表应按逗号拆分并去除两端空白"""
    s = Settings(cors_origins=" a , b ,c ")
    assert s.get_cors_origins_list() == ["a", "b", "c"]


def test_get_cors_origins_list_empty():
    """空字符串应返回空列表"""
    s = Settings(cors_origins="")
    assert s.get_cors_origins_list() == []


def test_jwt_secret_default_placeholder_rejected():
    """默认占位符 change-me 应被拒绝"""
    with pytest.raises(ValidationError):
        Settings(jwt_secret="change-me")


def test_jwt_secret_short_rejected():
    """长度不足 32 的密钥应被拒绝"""
    with pytest.raises(ValidationError):
        Settings(jwt_secret="too-short")


def test_jwt_secret_empty_rejected():
    """空密钥应被拒绝"""
    with pytest.raises(ValidationError):
        Settings(jwt_secret="")


def test_jwt_secret_strong_accepted():
    """≥ 32 字符的强密钥应通过校验"""
    s = Settings(jwt_secret="x" * 32)
    assert s.jwt_secret == "x" * 32
