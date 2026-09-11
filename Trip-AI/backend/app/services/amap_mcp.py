"""高德地图官方 MCP 工具接入（本地 stdio 子进程）

通过 langchain-mcp-adapters 的 MultiServerMCPClient 以 stdio 传输方式拉起高德官方
MCP 服务器（@amap/amap-maps-mcp-server，npx 子进程），获取地图工具并确定性调用
text_search / search_detail / weather / direction_* 取真实数据，供下游规划节点使用。

与早期「托管 SSE 端点」方案相比，本地 stdio 子进程连接稳定，不存在「长连接被服务端
断开（ClosedResourceError）」的问题。

关键事实（实测）：
- maps_text_search 只返回 id/name/address/typecode/photos，不返回坐标；
  坐标需通过 maps_search_detail(id) 或 maps_geo(address) 二次获取。
- maps_weather(city) 一步到位返回预报，无需先查 adcode。
- 三个方向工具（步行/驾车/公交）返回 distance(米) + duration(秒) + steps，
  但不含 polyline 轨迹，前端用「景点直线连线」呈现路线。
"""
import re
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from loguru import logger

from app.config import get_settings

# 官方 MCP 服务器：npx 拉起 stdio 子进程，API key 通过环境变量注入
MCP_SERVER_PACKAGE = "@amap/amap-maps-mcp-server"

_client: Optional[MultiServerMCPClient] = None
_session_ctx: Optional[Any] = None  # stdio 会话的 async context manager
_tools: Optional[Dict[str, BaseTool]] = None

# 本流程需要的工具：文本搜索、POI 详情、天气、三种路线规划、地理编码（坐标兜底）
TOOL_TEXT_SEARCH = "maps_text_search"
TOOL_SEARCH_DETAIL = "maps_search_detail"
TOOL_WEATHER = "maps_weather"
TOOL_GEO = "maps_geo"
DIRECTION_TOOLS = {
    "walking": "maps_direction_walking",
    "driving": "maps_direction_driving",
    "transit": "maps_direction_transit_integrated",
}

# 取数数量上限（search_detail 每 POI 一次调用，控制总量与耗时）
ATTRACTION_LIMIT = 12
HOTEL_LIMIT = 8


def _get_amap_mcp_env() -> Dict[str, str]:
    s = get_settings()
    if not s.amap_api_key:
        raise ValueError("未配置 AMAP_API_KEY，无法启动高德 MCP 服务器")
    return {"AMAP_MAPS_API_KEY": s.amap_api_key}


async def get_amap_tools() -> Dict[str, BaseTool]:
    """懒加载单例：启动高德官方 MCP 子进程并缓存工具（name -> tool）。

    stdio 子进程生命周期与应用一致：启动时拉起一次，后续所有请求复用，
    应用关停时通过 close_amap_mcp() 关闭。
    """
    global _client, _session_ctx, _tools
    if _tools is not None:
        return _tools

    logger.info("启动高德官方 MCP 服务器（stdio）：{}", MCP_SERVER_PACKAGE)
    _client = MultiServerMCPClient(
        {
            "amap": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", MCP_SERVER_PACKAGE],
                "env": _get_amap_mcp_env(),
            }
        }
    )
    _session_ctx = _client.session("amap")
    session = await _session_ctx.__aenter__()
    all_tools = await load_mcp_tools(session)
    _tools = {t.name: t for t in all_tools}
    logger.info("高德 MCP 工具加载完成，共 {} 个: {}", len(_tools), list(_tools.keys()))
    return _tools


async def close_amap_mcp() -> None:
    """关闭高德 MCP 子进程会话（应用关停时调用）"""
    global _client, _session_ctx, _tools
    if _session_ctx is not None:
        try:
            await _session_ctx.__aexit__(None, None, None)
        except Exception as e:
            logger.warning("关闭高德 MCP 会话失败: {}", e)
    _client = None
    _session_ctx = None
    _tools = None


async def reset_amap_mcp() -> None:
    """子进程异常退出时重建：关闭旧会话并清空单例，下次请求重新拉起"""
    logger.info("重置高德 MCP 会话")
    await close_amap_mcp()


# ---------- 工具返回结果解析 ----------

def _extract_json(text: str) -> Any:
    """从工具返回字符串中解析 JSON（剥离可能的前缀/包裹）"""
    if not text:
        return None
    text = text.strip()
    import json

    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    decoder = json.JSONDecoder()
    for match in re.finditer(r"[\[{]", text):
        try:
            obj, _ = decoder.raw_decode(text[match.start():])
            return obj
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def parse_tool_result(result: Any) -> Dict[str, Any]:
    """从工具调用返回值中提取 JSON 对象（兼容 str / content block 列表 / dict）"""
    import json

    if isinstance(result, str):
        text = result
    elif isinstance(result, list):
        parts = []
        for block in result:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            else:
                parts.append(str(block))
        text = "\n".join(parts)
    elif isinstance(result, dict):
        text = result.get("text", json.dumps(result, ensure_ascii=False))
    else:
        text = str(result)
    return _extract_json(text) or {}


async def _call_tool(tool: BaseTool, args: Dict[str, Any]) -> Dict[str, Any]:
    """调用单个 MCP 工具并解析返回 JSON"""
    raw = await tool.ainvoke(args)
    return parse_tool_result(raw)


def _to_int(v: Any) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def _parse_location(location: Any) -> Tuple[float, float]:
    """解析 'lng,lat' 为 (lng, lat)，失败返回 (0.0, 0.0)"""
    if not location:
        return 0.0, 0.0
    try:
        lng, lat = str(location).split(",")
        return float(lng), float(lat)
    except (ValueError, AttributeError):
        return 0.0, 0.0


def _pick_photo(photos: Any) -> str:
    """从 photos 字段提取第一张图片 URL（兼容 str / dict / list）"""
    if not photos:
        return ""
    url = ""
    if isinstance(photos, dict):
        url = photos.get("url", "")
    elif isinstance(photos, list):
        for p in photos:
            if isinstance(p, dict):
                url = p.get("url", "")
            elif isinstance(p, str):
                url = p
            if url:
                break
    else:
        url = str(photos)
    if isinstance(url, list):
        return url[0] if url else ""
    return url or ""


def _parse_weather(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """解析 maps_weather 返回的天气预报（forecasts 每天一条）"""
    result = []
    for cast in data.get("forecasts", []) or []:
        result.append(
            {
                "date": cast.get("date", ""),
                "week": cast.get("week", ""),
                "day_weather": cast.get("dayweather", ""),
                "night_weather": cast.get("nightweather", ""),
                "day_temp": cast.get("daytemp", ""),
                "night_temp": cast.get("nighttemp", ""),
                "day_wind": cast.get("daywind", ""),
                "night_wind": cast.get("nightwind", ""),
                "day_power": cast.get("daypower", ""),
                "night_power": cast.get("nightpower", ""),
            }
        )
    return result


def _dedupe(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for it in items:
        key = it.get("name", "")
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        out.append(it)
    return out


# ---------- 取数 ----------

async def gather_amap_data(city: str, tools: Dict[str, BaseTool]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """确定性调用高德 MCP 工具取数：景点搜索 + 天气 + 酒店搜索。

    text_search 不返回坐标，这里对每个 POI 再调 search_detail 补齐
    location / type / rating / 图片。返回 (attractions, weather, hotels)。
    """
    text_search = tools.get(TOOL_TEXT_SEARCH)
    detail_tool = tools.get(TOOL_SEARCH_DETAIL)
    weather_tool = tools.get(TOOL_WEATHER)

    async def _search_and_enrich(keywords: str, limit: int) -> List[Dict[str, Any]]:
        if text_search is None:
            return []
        res = await _call_tool(text_search, {"keywords": keywords, "city": city})
        pois = res.get("pois", []) or []
        out: List[Dict[str, Any]] = []
        for p in pois[:limit]:
            item = {
                "id": p.get("id", ""),
                "name": p.get("name", ""),
                "address": p.get("address", ""),
                "type": p.get("type", ""),
                "longitude": 0.0,
                "latitude": 0.0,
                "rating": "",
                "image_url": _pick_photo(p.get("photos")),
            }
            # 用 POI 详情补坐标与评分
            if detail_tool is not None and item["id"]:
                try:
                    d = await _call_tool(detail_tool, {"id": item["id"]})
                except Exception as e:
                    logger.warning("POI 详情获取失败 {}: {}", item["id"], e)
                    d = {}
                item["type"] = d.get("type", item["type"])
                item["rating"] = d.get("rating", "")
                item["image_url"] = item["image_url"] or _pick_photo(d.get("photos"))
                item["longitude"], item["latitude"] = _parse_location(d.get("location"))
            out.append(item)
        return _dedupe(out)

    attractions = await _search_and_enrich("景点", ATTRACTION_LIMIT)
    hotels = await _search_and_enrich("酒店", HOTEL_LIMIT)

    weather: List[Dict[str, Any]] = []
    if weather_tool is not None:
        weather = _parse_weather(await _call_tool(weather_tool, {"city": city}))[:4]

    logger.info(
        "高德 MCP 取数结果 → 景点 {} / 天气 {} / 酒店 {}",
        len(attractions), len(weather), len(hotels),
    )
    return attractions, weather, hotels


# ---------- 路线规划 ----------

def _fmt_distance(m: int) -> str:
    if not m:
        return "未知"
    if m < 1000:
        return f"{m}米"
    return f"{m / 1000:.1f}公里"


def _fmt_duration(s: int) -> str:
    if not s:
        return "未知"
    minutes = round(s / 60)
    if minutes < 60:
        return f"{minutes}分钟"
    h, m = divmod(minutes, 60)
    return f"{h}小时{m}分钟" if m else f"{h}小时"


def pick_mode(transportation: str) -> str:
    """根据用户交通偏好选择方向工具类型"""
    t = (transportation or "").strip()
    if "步行" in t:
        return "walking"
    if "自驾" in t or "驾车" in t:
        return "driving"
    return "transit"  # 公共交通 / 混合 默认公交


def _parse_direction(data: Dict[str, Any], mode: str) -> Optional[Dict[str, Any]]:
    """解析方向工具返回，统一为 {mode, distance_m, duration_s, summary, steps}"""
    route = data.get("route") or {}
    if mode == "transit":
        distance = _to_int(route.get("distance"))
        transits = route.get("transits") or []
        duration = walking = 0
        steps: List[str] = []
        if transits:
            t0 = transits[0]
            duration = _to_int(t0.get("duration"))
            walking = _to_int(t0.get("walking_distance"))
            walking_duration = 0
            for seg in t0.get("segments", [])[:8]:
                if not isinstance(seg, dict):
                    continue
                w = seg.get("walking")
                if isinstance(w, dict):
                    walking_duration += _to_int(w.get("duration"))
                    for s in (w.get("steps") or [])[:3]:
                        if isinstance(s, dict) and s.get("instruction"):
                            steps.append(s["instruction"])
            # 兜底：短途纯步行结果可能不返回 transits[0].duration，用步行段累计
            if not duration:
                duration = walking_duration
        # 兜底：仍无有效时长（如 transits 为空），按步行速度估算（约 1.2 m/s）
        if not duration and distance:
            duration = int(distance / 1.2)
        summary = f"公共交通约{_fmt_distance(distance)}/{_fmt_duration(duration)}"
        if walking:
            summary += f"（含步行约{_fmt_distance(walking)}）"
        return {
            "mode": "transit", "distance_m": distance, "duration_s": duration,
            "summary": summary, "steps": steps[:6],
        }

    paths = route.get("paths") or []
    if not paths:
        return None
    p0 = paths[0]
    distance = _to_int(p0.get("distance"))
    duration = _to_int(p0.get("duration"))
    steps = [
        s.get("instruction", "")
        for s in (p0.get("steps") or [])[:6]
        if isinstance(s, dict) and s.get("instruction")
    ]
    label = "步行" if mode == "walking" else "驾车"
    return {
        "mode": mode, "distance_m": distance, "duration_s": duration,
        "summary": f"{label}约{_fmt_distance(distance)}/{_fmt_duration(duration)}",
        "steps": steps,
    }


def _fmt_point(pt: Any) -> str:
    if isinstance(pt, dict):
        lng = pt.get("longitude", 0.0)
        lat = pt.get("latitude", 0.0)
    else:
        lng, lat = pt
    return f"{lng},{lat}"


async def get_route(
    origin: Any,
    destination: Any,
    transportation: str,
    city: str,
    tools: Dict[str, BaseTool],
) -> Optional[Dict[str, Any]]:
    """规划两点之间的路线，返回统一结构；失败返回 None（不阻断整体）"""
    mode = pick_mode(transportation)
    tool = tools.get(DIRECTION_TOOLS.get(mode, ""))
    if tool is None:
        return None
    args = {"origin": _fmt_point(origin), "destination": _fmt_point(destination)}
    if mode == "transit":
        args["city"] = city
        args["cityd"] = city
    try:
        data = await _call_tool(tool, args)
    except Exception as e:
        logger.warning("路线规划失败 {}->{}: {}", origin, destination, e)
        return None
    return _parse_direction(data, mode)


async def geocode(address: str, city: str, tools: Dict[str, BaseTool]) -> Tuple[float, float]:
    """地址 → 坐标（坐标回填的兜底手段），失败返回 (0.0, 0.0)"""
    tool = tools.get(TOOL_GEO)
    if tool is None or not address:
        return 0.0, 0.0
    try:
        data = await _call_tool(tool, {"address": address, "city": city})
        ret = data.get("return") or data.get("geocodes") or []
        if ret and isinstance(ret[0], dict):
            return _parse_location(ret[0].get("location"))
    except Exception as e:
        logger.warning("地理编码失败 {}: {}", address, e)
    return 0.0, 0.0
