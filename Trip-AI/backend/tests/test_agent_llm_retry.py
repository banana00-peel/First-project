"""LLM 重试谓词测试（_is_retryable_llm_error）。"""
import openai

from app.agents.nodes import _is_retryable_llm_error


class _FakeAPIError(Exception):
    """带 status_code 的假异常，模拟 openai.APIStatusError 的兜底判断分支"""

    def __init__(self, status_code):
        self.status_code = status_code


def test_openai_rate_limit_is_retryable():
    # __new__ 绕过 __init__（真实构造需 httpx.Response，测试里无必要）
    err = openai.RateLimitError.__new__(openai.RateLimitError)
    assert _is_retryable_llm_error(err) is True


def test_status_429_is_retryable():
    assert _is_retryable_llm_error(_FakeAPIError(429)) is True


def test_status_5xx_is_retryable():
    assert _is_retryable_llm_error(_FakeAPIError(503)) is True


def test_business_4xx_not_retryable():
    assert _is_retryable_llm_error(_FakeAPIError(400)) is False


def test_plain_exception_not_retryable():
    assert _is_retryable_llm_error(ValueError("boom")) is False
