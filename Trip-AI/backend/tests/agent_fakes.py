"""Agent 测试假件：假 LLM / 假高德 MCP 工具 / 空图片服务，驱动 LangGraph 链离线回归。

test_agent_chain.py 与 test_eval_set.py 共用，全程不触网、不耗真实 LLM/地图 key。
"""
import json
from datetime import date, timedelta


class FakeLLM:
    """bind 返回自身，ainvoke 返回指定 TripPlan 的 JSON（模拟已训练好的规划模型）"""

    def __init__(self, plan: dict):
        self._plan = plan

    def bind(self, **kwargs):
        return self

    async def ainvoke(self, messages):
        return _FakeResp(json.dumps(self._plan, ensure_ascii=False))


class _FakeResp:
    def __init__(self, content):
        self.content = content


class FakeTool:
    """ainvoke 返回 JSON 字符串，可被 parse_tool_result 解析。

    固定结果传 result；需按入参分发时传 fn(args)->dict。
    """

    def __init__(self, result=None, fn=None):
        self._result = result
        self._fn = fn

    async def ainvoke(self, args):
        data = self._fn(args) if self._fn else self._result
        return json.dumps(data, ensure_ascii=False)


class EmptyImageService:
    def search_images(self, query, per_page=1):
        return []


def make_fake_tools(attractions, hotels=None, weather=None, detail_by_id=None):
    """构造高德 MCP 工具假件。

    - text_search 按 keywords 分发：景点 → attractions，酒店 → hotels（默认空）。
    - search_detail 按 id 查 detail_by_id，缺省给固定坐标 116.397,39.908（供坐标回填断言非 0,0）。
    - 三种方向工具返回可被 _parse_direction 解析的最小结构。
    """
    hotels = hotels or []
    detail_by_id = detail_by_id or {}
    forecasts = weather or [{
        "date": "2026-10-01", "week": "1", "dayweather": "晴", "nightweather": "晴",
        "daytemp": "20", "nighttemp": "10", "daywind": "北风", "nightwind": "北风",
        "daypower": "3", "nightpower": "3",
    }]
    default_detail = {"type": "景点", "rating": "4.5", "location": "116.397,39.908", "photos": []}

    def _text_search(args):
        pois = attractions if "景点" in args.get("keywords", "") else hotels
        return {"pois": pois}

    def _search_detail(args):
        return detail_by_id.get(args.get("id", ""), default_detail)

    def _direction_transit(args):
        return {
            "route": {
                "distance": 1000,
                "transits": [{"duration": 300, "walking_distance": 200, "segments": []}],
            }
        }

    def _direction_paths(args):
        return {
            "route": {
                "paths": [{"distance": 1000, "duration": 300, "steps": [{"instruction": "直行"}]}],
            }
        }

    def _geo(args):
        return {"geocodes": [{"location": "116.397,39.908"}]}

    return {
        "maps_text_search": FakeTool(fn=_text_search),
        "maps_search_detail": FakeTool(fn=_search_detail),
        "maps_weather": FakeTool({"forecasts": forecasts}),
        "maps_geo": FakeTool(fn=_geo),
        "maps_direction_transit_integrated": FakeTool(fn=_direction_transit),
        "maps_direction_driving": FakeTool(fn=_direction_paths),
        "maps_direction_walking": FakeTool(fn=_direction_paths),
    }


def make_plan(city: str, travel_days: int, names: list, start: str = "2026-10-01") -> dict:
    """构造合法 TripPlan dict：每天 2 个景点，景点名从 names 依次取（保证来自真实数据）。"""
    start_d = date.fromisoformat(start)
    days = []
    for d in range(1, travel_days + 1):
        day_names = names[(d - 1) * 2 : (d - 1) * 2 + 2]
        while len(day_names) < 2:
            day_names.append(names[(len(day_names) + (d - 1) * 2) % len(names)])
        days.append({
            "day": d,
            "date": (start_d + timedelta(days=d - 1)).isoformat(),
            "title": f"第{d}天",
            "attractions": [{"name": n} for n in day_names],
            "meals": [],
            "routes": [],
        })
    return {
        "city": city,
        "start_date": start,
        "end_date": (start_d + timedelta(days=travel_days - 1)).isoformat(),
        "travel_days": travel_days,
        "days": days,
        "weather": [],
    }
