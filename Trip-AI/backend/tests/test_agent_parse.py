"""_parse_plan_json 纯单测：正常 / markdown 围栏 / 带前后缀 / 非法输入"""

import json

import pytest

from app.agents.nodes import _parse_plan_json
from app.schemas.trip import TripPlan


def _minimal_plan() -> dict:
    return TripPlan(
        city="北京", start_date="2026-10-01", end_date="2026-10-03", travel_days=3
    ).model_dump()


def test_parse_valid_json():
    data = _parse_plan_json(json.dumps(_minimal_plan(), ensure_ascii=False))
    assert data["city"] == "北京"
    assert data["travel_days"] == 3


def test_parse_markdown_fenced():
    text = "```json\n" + json.dumps(_minimal_plan(), ensure_ascii=False) + "\n```"
    data = _parse_plan_json(text)
    assert data["city"] == "北京"


def test_parse_json_with_prefix_suffix():
    text = (
        "好的，以下是计划：\n"
        + json.dumps(_minimal_plan(), ensure_ascii=False)
        + "\n希望对你有帮助"
    )
    data = _parse_plan_json(text)
    assert data["city"] == "北京"


def test_parse_empty_raises():
    with pytest.raises(ValueError):
        _parse_plan_json("")


def test_parse_garbage_raises():
    with pytest.raises(ValueError):
        _parse_plan_json("这不是 JSON")
