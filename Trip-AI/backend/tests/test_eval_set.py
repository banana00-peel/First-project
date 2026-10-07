"""离线评测集：参数化多城市场景，回归断言 agent 链的确定性后处理。

面试亮点：改 prompt 或编排逻辑后跑一遍这里，就能知道有没有把输出改坏——
JSON 合法、天数正确、景点不编造（来自真实取数）、坐标已回填、路线已生成，
全程不触网、不耗真实 LLM / 地图 key。
"""
import asyncio
from datetime import date, timedelta

import pytest

from app.agents.graph import reset_graph, run_planner
from tests.agent_fakes import EmptyImageService, FakeLLM, make_fake_tools, make_plan


def _state(city: str, days: int, transport: str) -> dict:
    start = date(2026, 10, 1)
    return {
        "city": city,
        "start_date": start.isoformat(),
        "end_date": (start + timedelta(days=days - 1)).isoformat(),
        "travel_days": days,
        "transportation": transport,
        "accommodation": "经济型酒店",
        "preferences": [],
        "free_text": "",
    }


def _attractions(names):
    return [
        {"id": f"P{i}", "name": n, "address": f"{n}地址", "type": "景点", "photos": []}
        for i, n in enumerate(names)
    ]


def _expected_mode(transport: str) -> str:
    if "步行" in transport:
        return "walking"
    if "自驾" in transport or "驾车" in transport:
        return "driving"
    return "transit"


# (城市, 天数, 交通方式, 假景点名列表) —— 景点名来自假 MCP 取数，保证「防编造」断言成立
CASES = [
    ("北京", 2, "公共交通", ["故宫", "天安门", "颐和园", "长城"]),
    ("上海", 3, "自驾", ["外滩", "豫园", "东方明珠", "迪士尼", "南京路", "田子坊"]),
    ("杭州", 1, "步行", ["西湖", "灵隐寺"]),
    (
        "成都", 4, "公共交通",
        ["宽窄巷子", "锦里", "大熊猫基地", "武侯祠", "杜甫草堂", "青城山", "都江堰", "春熙路"],
    ),
]


@pytest.mark.parametrize("city,days,transport,names", CASES)
def test_eval_case(monkeypatch, city, days, transport, names):
    plan = make_plan(city, days, names)

    async def _get_tools():
        return make_fake_tools(_attractions(names))

    monkeypatch.setattr("app.agents.graph.get_llm", lambda: FakeLLM(plan))
    monkeypatch.setattr("app.services.amap_mcp.get_amap_tools", _get_tools)
    monkeypatch.setattr("app.agents.nodes.get_image_service", lambda: EmptyImageService())

    async def _run():
        await reset_graph()
        return await run_planner(_state(city, days, transport))

    result = asyncio.run(_run())
    plan_out = result["plan"]

    # 1) 结构：城市、天数一致，天数按计划拆开
    assert plan_out["city"] == city
    assert plan_out["travel_days"] == days
    assert len(plan_out["days"]) == days

    # 2) 逐天断言：防编造 / 坐标回填 / 路线生成
    real_names = set(names)
    total_routes = 0
    for day in plan_out["days"]:
        for attr in day["attractions"]:
            assert attr["name"] in real_names, f"景点 {attr['name']} 不在真实取数中（疑似编造）"
            loc = attr["location"]
            assert (
                loc and loc["longitude"] != 0.0 and loc["latitude"] != 0.0
            ), f"{attr['name']} 坐标未回填"
        assert len(day["routes"]) == len(day["attractions"]) - 1
        for r in day["routes"]:
            assert r["mode"] == _expected_mode(transport)
        total_routes += len(day["routes"])
    assert total_routes > 0
