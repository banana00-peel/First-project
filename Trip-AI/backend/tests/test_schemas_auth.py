"""app.schemas.auth 的单元测试"""
import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut


def test_register_request_valid():
    """合法输入应能正常构造"""
    req = RegisterRequest(email="a@b.com", username="张三", password="123456")
    assert req.email == "a@b.com"
    assert req.username == "张三"


def test_register_request_rejects_invalid_email():
    """非法邮箱应抛 ValidationError"""
    with pytest.raises(ValidationError):
        RegisterRequest(email="not-an-email", username="张三", password="123456")


def test_register_request_rejects_short_password():
    """密码少于 6 位应被拒绝"""
    with pytest.raises(ValidationError):
        RegisterRequest(email="a@b.com", username="张三", password="123")


def test_register_request_rejects_short_username():
    """用户名少于 2 个字符应被拒绝"""
    with pytest.raises(ValidationError):
        RegisterRequest(email="a@b.com", username="张", password="123456")


def test_register_request_rejects_long_username():
    """用户名超过 32 个字符应被拒绝"""
    with pytest.raises(ValidationError):
        RegisterRequest(email="a@b.com", username="x" * 33, password="123456")


def test_login_request_valid():
    """合法登录请求应能正常构造"""
    req = LoginRequest(email="a@b.com", password="123456")
    assert req.email == "a@b.com"


def test_login_request_rejects_invalid_email():
    """登录邮箱非法应被拒绝"""
    with pytest.raises(ValidationError):
        LoginRequest(email="bad", password="123456")


def test_token_response_defaults():
    """TokenResponse 的 token_type 默认应为 bearer"""
    token = TokenResponse(
        access_token="abc",
        user=UserOut(id=1, email="a@b.com", username="u"),
    )
    assert token.token_type == "bearer"
    assert token.user.id == 1
