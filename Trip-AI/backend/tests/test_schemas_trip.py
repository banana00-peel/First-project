"""app.schemas.trip 的单元测试"""
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.trip import TripRequest, TripSaveRequest, TripSummary, WeatherInfo


def test_trip_request_defaults():
    """未填写的交通/住宿/偏好应使用默认值"""
    req = TripRequest(
        city="北京", start_date="2026-09-01", end_date="2026-09-03", travel_days=3
    )
    assert req.transportation == "公共交通"
    assert req.accommodation == "经济型酒店"
    assert req.preferences == []


def test_trip_request_rejects_empty_city():
    """城市为空应被拒绝"""
    with pytest.raises(ValidationError):
        TripRequest(city="", start_date="2026-09-01", end_date="2026-09-03", travel_days=3)


def test_trip_request_rejects_too_many_days():
    """行程天数超过 30 天应被拒绝"""
    with pytest.raises(ValidationError):
        TripRequest(
            city="北京", start_date="2026-09-01", end_date="2026-09-03", travel_days=31
        )


def test_trip_save_request_plan_default():
    """保存行程时 plan 默认应为空字典"""
    req = TripSaveRequest(
        city="北京", start_date="2026-09-01", end_date="2026-09-03", travel_days=3
    )
    assert req.plan == {}


def test_weather_info_strips_celsius():
    """温度应剥离 °C / ℃ 单位"""
    assert WeatherInfo(date="2026-09-01", temperature="28°C").temperature == "28"
    assert WeatherInfo(date="2026-09-01", temperature=" 30℃ ").temperature == "30"


def test_trip_summary_serializes_datetime():
    """created_at 传入 datetime 时应序列化为 isoformat 字符串"""
    dt = datetime(2026, 9, 1, 12, 0, 0)
    s = TripSummary(
        id=1,
        city="北京",
        start_date="2026-09-01",
        end_date="2026-09-03",
        travel_days=3,
        status="completed",
        created_at=dt,
    )
    assert s.created_at == dt.isoformat()
