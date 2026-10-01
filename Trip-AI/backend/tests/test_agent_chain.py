"""Agent 链集成测试：跑真实 gather → plan → enrich（mock LLM/MCP/图片，不触网）。

简历亮点：用假 LLM 与假 MCP 工具驱动整条 LangGraph 链，验证取数、结构化规划、
坐标回填、路线生成的编排正确性，不依赖高德 key / Unsplash / 真实 LLM。
"""
import asyncio
import json

from app.agents.graph import reset_graph, run_planner
from app.schemas.trip import Attraction, DayPlan, TripPlan


class _FakeResp:
    def __init__(self, content):
        self.content = content


class FakeLLM:
    """bind 返回自身，ainvoke 返回合法 TripPlan JSON"""

    def __init__(self, plan):
        self._plan = plan

    def bind(self, **kwargs):
        return self

    async def ainvoke(self, messages):
        return _FakeResp(json.dumps(self._plan, ensure_ascii=False))


class FakeTool:
    """ainvoke 返回 JSON 字符串，可被 parse_tool_result 解析"""

    def __init__(self, result):
        self._result = result

    async def ainvoke(self, args):
        return json.dumps(self._result, ensure_ascii=False)


class _EmptyImageService:
    def search_images(self, query, per_page=1):
        return []


async def _fake_tools():
    return {
        "maps_text_search": FakeTool(
            {
                "pois": [
                    {"id": "B001", "name": "故宫", "address": "北京市东城区", "type": "景点", "photos": []},
                    {"id": "B002", "name": "天安门", "address": "北京市东城区", "type": "景点", "photos": []},
                ]
            }
        ),
        "maps_search_detail": FakeTool(
            {"type": "景点", "rating": "4.5", "location": "116.397,39.908", "photos": []}
        ),
        "maps_weather": FakeTool(
            {
                "forecasts": [
                    {
                        "date": "2026-10-01", "week": "1", "dayweather": "晴", "nightweather": "晴",
                        "daytemp": "20", "nighttemp": "10", "daywind": "北风", "nightwind": "北风",
                        "daypower": "3", "nightpower": "3",
                    }
                ]
            }
        ),
        "maps_geo": FakeTool({"geocodes": [{"location": "116.397,39.908"}]}),
        "maps_direction_transit_integrated": FakeTool(
            {
                "route": {
                    "distance": 1000,
                    "transits": [{"duration": 300, "walking_distance": 200, "segments": []}],
                }
            }
        ),
    }


def _plan() -> dict:
    return TripPlan(
        city="北京",
        start_date="2026-10-01",
        end_date="2026-10-02",
        travel_days=2,
        days=[
            DayPlan(
                day=1,
                date="2026-10-01",
                title="第一天",
                attractions=[Attraction(name="故宫"), Attraction(name="天安门")],
            )
        ],
    ).model_dump()


def test_agent_chain_end_to_end(monkeypatch):
    monkeypatch.setattr("app.agents.graph.get_llm", lambda: FakeLLM(_plan()))
    monkeypatch.setattr("app.services.amap_mcp.get_amap_tools", _fake_tools)
    monkeypatch.setattr("app.agents.nodes.get_image_service", lambda: _EmptyImageService())

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
