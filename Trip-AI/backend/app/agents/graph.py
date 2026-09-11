"""LangGraph 图编排：取数节点 → 结构化规划节点 → 坐标回填/路线节点"""
from functools import partial
from typing import Any, Dict, List

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from app.agents.nodes import enrich, gather, plan
from app.agents.state import PlannerState
from app.config import get_settings

_llm = None
_app = None


def get_llm() -> ChatOpenAI:
    """获取 LLM 实例（单例）"""
    global _llm
    if _llm is None:
        s = get_settings()
        _llm = ChatOpenAI(
            model=s.llm_model,
            api_key=s.llm_api_key,
            base_url=s.llm_base_url,
            temperature=s.llm_temperature,
            timeout=120,
            max_retries=2,
        )
    return _llm


def build_graph(tools: Dict[str, Any]) -> Any:
    """构建旅行规划图：gather（取数）→ plan（JSON 模式）→ enrich（坐标回填/路线）"""
    llm = get_llm()

    graph = StateGraph(PlannerState)
    graph.add_node("gather", partial(gather, tools=tools))
    graph.add_node("plan", partial(plan, llm=llm))
    graph.add_node("enrich", partial(enrich, tools=tools))
    graph.add_edge(START, "gather")
    graph.add_edge("gather", "plan")
    graph.add_edge("plan", "enrich")
    graph.add_edge("enrich", END)
    return graph.compile()


async def get_graph():
    """获取已编译的图（懒加载单例，首次加载 MCP 工具）"""
    global _app
    if _app is None:
        from app.services.amap_mcp import get_amap_tools
        tools = await get_amap_tools()
        _app = build_graph(tools)
    return _app


async def reset_graph():
    """清空已编译的图（MCP 子进程异常时调用，下次请求重建）"""
    global _app
    _app = None


def _is_connection_error(e: Exception) -> bool:
    """判断是否为高德 MCP 子进程/传输层异常（而非业务/LLM 错误）"""
    msg = str(e).lower()
    return (
        "closed" in msg
        or "broken" in msg
        or "process" in msg
        or "subprocess" in msg
        or "mcp" in type(e).__module__.lower()
        or "anyio" in type(e).__module__.lower()
        or isinstance(e, (BrokenPipeError, ConnectionError, ProcessLookupError))
    )


async def run_planner(state: Dict[str, Any]) -> Dict[str, Any]:
    """执行旅行规划，返回最终状态；MCP 子进程异常时重建会话并重试一次"""
    from loguru import logger

    try:
        graph = await get_graph()
        return await graph.ainvoke(state)
    except Exception as e:
        if _is_connection_error(e):
            logger.warning("检测到 MCP 子进程异常，重建会话后重试: {}", e)
            from app.services.amap_mcp import reset_amap_mcp
            await reset_amap_mcp()
            await reset_graph()# 清理旧的图
            graph = await get_graph()# 新建图
            return await graph.ainvoke(state)
        raise
