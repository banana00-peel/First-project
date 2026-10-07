"""Agent 链集成测试：跑真实 gather → plan → enrich（mock LLM/MCP/图片，不触网）。

简历亮点：用假 LLM 与假 MCP 工具驱动整条 LangGraph 链，验证取数、结构化规划、
坐标回填、路线生成的编排正确性，不依赖高德 key / Unsplash / 真实 LLM。
"""
import asyncio

from app.agents.graph import reset_graph, run_planner
from tests.agent_fakes import EmptyImageService, FakeLLM, make_fake_tools, make_plan


def _attractions():
    return [
        {"id": "B001", "name": "故宫", "address": "北京市东城区", "type": "景点", "photos": []},
        {"id": "B002", "name": "天安门", "address": "北京市东城区", "type": "景点", "photos": []},
    ]


def test_agent_chain_end_to_end(monkeypatch):
    plan = make_plan("北京", 2, ["故宫", "天安门"])

    async def _get_tools():
        return make_fake_tools(_attractions())

    monkeypatch.setattr("app.agents.graph.get_llm", lambda: FakeLLM(plan))
    monkeypatch.setattr("app.services.amap_mcp.get_amap_tools", _get_tools)
    monkeypatch.setattr("app.agents.nodes.get_image_service", lambda: EmptyImageService())

    async def _run():
        await reset_graph()
        return await run_planner(
            {
                "city": "北京",
                "start_date": "2026-10-01",
                "end_date": "2026-10-02",
                "travel_days": 2,
                "transportation": "公共交通",
                "accommodation": "经济型酒店",
                "preferences": [],
                "free_text": "",
            }
        )

    result = asyncio.run(_run())

    plan = result["plan"]
    assert plan["city"] == "北京"
    day = plan["days"][0]
    # 坐标回填：故宫/天安门 从假 MCP 详情拿到 116.397,39.908
    assert day["attractions"][0]["location"]["longitude"] == 116.397
    assert day["attractions"][0]["location"]["latitude"] == 39.908
    # 路线生成：两个有坐标的相邻景点之间产出 1 段公交路线
    assert len(day["routes"]) == 1
    assert day["routes"][0]["mode"] == "transit"
