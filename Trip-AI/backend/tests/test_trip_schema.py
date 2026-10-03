"""TripRequest 输入长度上限测试。"""
import pytest
from pydantic import ValidationError

from app.schemas.trip import TripRequest


def _req(**overrides):
    base = {
        "city": "北京",
        "start_date": "2026-10-01",
        "end_date": "2026-10-02",
        "travel_days": 2,
    }
    base.update(overrides)
    return base


def test_valid_request_ok():
    TripRequest(**_req())


def test_free_text_too_long_rejected():
    with pytest.raises(ValidationError):
        TripRequest(**_req(free_text="a" * 2001))


def test_preferences_too_many_rejected():
    with pytest.raises(ValidationError):
        TripRequest(**_req(preferences=[f"p{i}" for i in range(21)]))


def test_preference_item_too_long_rejected():
    with pytest.raises(ValidationError):
        TripRequest(**_req(preferences=["a" * 65]))


def test_transportation_too_long_rejected():
    with pytest.raises(ValidationError):
        TripRequest(**_req(transportation="a" * 33))
