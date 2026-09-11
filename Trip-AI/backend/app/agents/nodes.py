"""LangGraph 节点函数"""
import asyncio
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from app.agents.prompts import PLANNER_SYSTEM, build_planner_prompt
from app.agents.state import PlannerState
from app.schemas.trip import TripPlan
from app.services.amap_mcp import gather_amap_data, geocode, get_route
from app.services.images import get_image_service


async def gather(state: PlannerState, tools) -> Dict[str, Any]:
    """节点：确定性调用高德 MCP 工具，收集景点/天气/酒店真实数据（含坐标）"""
    logger.info("开始调用高德 MCP 工具取数: {}", state.get("city"))
    attractions, weather, hotels = await gather_amap_data(state.get("city", ""), tools)
    return {"attractions": attractions, "weather": weather, "hotels": hotels}


def _schema_without_routes() -> str:
    """生成给 LLM 的目标 JSON Schema，剔除 routes 字段。

    routes 由 enrich 节点确定性补充，不应交给 LLM 生成，否则 LLM 可能乱填。
    """
    schema = TripPlan.model_json_schema()
    days = schema.get("properties", {}).get("days", {})
    items = days.get("items", {})
    props = items.get("properties", {})
    props.pop("routes", None)
    return json.dumps(schema, ensure_ascii=False)


async def plan(state: PlannerState, llm) -> Dict[str, Any]:
    """节点：综合数据，生成结构化计划。

    使用 JSON 输出模式（response_format=json_object）而非 function calling：
    DeepSeek 对深层嵌套 schema 的 function calling 会返回不完整结果，JSON 模式更稳定。
    """
    prompt = build_planner_prompt(dict(state))

    context_lines = [
        "=== 景点数据 ===",
        str(state.get("attractions", [])),
        "=== 天气数据 ===",
        str(state.get("weather", [])),
        "=== 酒店数据 ===",
        str(state.get("hotels", [])),
    ]
    json_instr = (
        "\n\n请严格按照以下 JSON Schema 输出一份完整的旅行计划。"
        "仅输出一个 JSON 对象，不要包含 markdown 代码块或任何其他文字：\n"
        + _schema_without_routes()
    )
    full_prompt = prompt + "\n\n" + "\n".join(context_lines) + json_instr

    logger.info("调用 LLM 生成结构化计划...")
    json_llm = llm.bind(response_format={"type": "json_object"}, max_tokens=8000)
    resp = await json_llm.ainvoke(
        [{"role": "system", "content": PLANNER_SYSTEM}, {"role": "user", "content": full_prompt}]
    )

    plan_dict = _parse_plan_json(resp.content)
    plan_dict = await _attach_images(plan_dict)
    return {"plan": plan_dict}


async def enrich(state: PlannerState, tools) -> Dict[str, Any]:
    """节点：后处理——坐标回填 + 每日路线规划（确定性，无 LLM）。

    1) 坐标回填：LLM 重写计划时常常丢失/编造坐标，这里按名称把真实坐标回填到
       景点/酒店；匹配不到时用地址地理编码兜底。
    2) 路线规划：对每天相邻景点调用方向工具，产出 distance/duration/步骤。
    """
    plan_dict = state.get("plan")
    if not plan_dict:
        return {}

    city = state.get("city", "")
    transportation = state.get("transportation", "公共交通")
    attractions_db = state.get("attractions", [])
    hotels_db = state.get("hotels", [])

    await _backfill_locations(plan_dict, city, attractions_db, hotels_db, tools)
    await _attach_routes(plan_dict, transportation, city, tools)
    return {"plan": plan_dict}


# ---------- 坐标回填 ----------

# 把名字的格式进行处理，去空格，变小写
def _normalize_name(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"[（(].*?[)）]", "", s)
    s = re.sub(r"[\s\-·—_、，,。.：:【】\[\]「」《》\"']+", "", s)
    return s.lower()

# 拿一个名字，去真实景点列表 db 里找对应的那条记录。返回的是记录对象
def _match_poi(name: str, db: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not name or not db:
        return None
    tn = _normalize_name(name)
    for p in db:
        if _normalize_name(p.get("name", "")) == tn:
            return p # 返回的是记录对象
    # LLM 可能加前后缀，做互为子串的宽松匹配
    for p in db:
        pn = _normalize_name(p.get("name", ""))
        if tn and pn and (tn in pn or pn in tn):
            return p # 返回的是记录对象
    return None

# 判断这个位置有没有坐标
def _has_coord(loc: Any) -> bool:
    return isinstance(loc, dict) and bool(loc.get("longitude") and loc.get("latitude"))

# 坐标回填
async def _backfill_locations(
    plan_dict: Dict[str, Any],
    city: str,
    attractions_db: List[Dict[str, Any]],
    hotels_db: List[Dict[str, Any]],
    tools,
) -> None:
    for day in plan_dict.get("days", []) or []:
        for attr in day.get("attractions", []) or []:
            m = _match_poi(attr.get("name", ""), attractions_db)
            if m:
                if not _has_coord(attr.get("location")):
                    attr["location"] = {
                        "name": m.get("name", attr.get("name", "")),
                        "address": m.get("address", attr.get("address", "")),
                        "longitude": m.get("longitude", 0.0),
                        "latitude": m.get("latitude", 0.0),
                    }
                if not attr.get("address"):
                    attr["address"] = m.get("address", "")
                if not attr.get("image_url"):
                    attr["image_url"] = m.get("image_url", "")
            if not _has_coord(attr.get("location")) and attr.get("address"):
                lng, lat = await geocode(attr.get("address"), city, tools)
                if lng or lat:
                    attr["location"] = {
                        "name": attr.get("name", ""),
                        "address": attr.get("address", ""),
                        "longitude": lng,
                        "latitude": lat,
                    }

        hotel = day.get("hotel")
        if hotel:
            m = _match_poi(hotel.get("name", ""), hotels_db)
            if m:
                if not _has_coord(hotel.get("location")):
                    hotel["location"] = {
                        "name": m.get("name", hotel.get("name", "")),
                        "address": m.get("address", hotel.get("address", "")),
                        "longitude": m.get("longitude", 0.0),
                        "latitude": m.get("latitude", 0.0),
                    }
                if not hotel.get("address"):
                    hotel["address"] = m.get("address", "")
            if not _has_coord(hotel.get("location")) and hotel.get("address"):
                lng, lat = await geocode(hotel.get("address"), city, tools)
                if lng or lat:
                    hotel["location"] = {
                        "name": hotel.get("name", ""),
                        "address": hotel.get("address", ""),
                        "longitude": lng,
                        "latitude": lat,
                    }


# ---------- 路线规划 ----------

# 算每日相邻景点的路线
async def _attach_routes(
    plan_dict: Dict[str, Any],
    transportation: str,
    city: str,
    tools,
) -> None:
    for day in plan_dict.get("days", []) or []:
        attrs = day.get("attractions", []) or []
        valid = [
            a for a in attrs
            if _has_coord(a.get("location"))
        ]
        routes = []
        for i in range(len(valid) - 1):
            a, b = valid[i], valid[i + 1]
            seg = await get_route(a["location"], b["location"], transportation, city, tools)
            if seg:
                seg["from_name"] = a.get("name", "")
                seg["to_name"] = b.get("name", "")
                routes.append(seg)
        if routes:
            day["routes"] = routes


# ---------- 图片与 JSON 解析 ----------

async def _attach_images(plan_dict: Dict[str, Any]) -> Dict[str, Any]:
    """为景点补充图片（可选，Unsplash 无 key 时跳过；AMap 图片已由坐标回填补入）"""

    def _run():
        image_svc = get_image_service()
        days = plan_dict.get("days", [])
        for day in days:
            for attr in day.get("attractions", []):
                if not attr.get("image_url"):
                    urls = image_svc.search_images(attr.get("name", ""), per_page=1)
                    if urls:
                        attr["image_url"] = urls[0]
        return plan_dict

    return await asyncio.to_thread(_run)


def _parse_plan_json(text: str) -> Dict[str, Any]:
    """解析 LLM 返回的 JSON 文本，并用 TripPlan 校验结构"""
    if not text:
        raise ValueError("LLM 返回内容为空")
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("无法解析 LLM 返回的 JSON 内容")
        data = json.loads(text[start : end + 1])
    return TripPlan.model_validate(data).model_dump()
