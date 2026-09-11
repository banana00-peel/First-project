"""LangGraph 状态定义"""
from typing import Any, Dict, List, Optional, TypedDict


class PlannerState(TypedDict, total=False):
    """旅行规划状态"""

    # 输入
    city: str
    start_date: str
    end_date: str
    travel_days: int
    transportation: str
    accommodation: str
    preferences: List[str]
    free_text: str

    # 并行节点产出
    attractions: List[Dict[str, Any]]
    weather: List[Dict[str, Any]]
    hotels: List[Dict[str, Any]]

    # 计划产出
    plan: Optional[Dict[str, Any]]
