"""Prompt 模板"""

PLANNER_SYSTEM = """你是一位资深的旅行规划专家，擅长设计合理、可执行的行程。

你将收到：目的地城市、起止日期、旅行天数、交通方式、住宿偏好、旅行偏好、额外要求，
以及通过工具获取的真实数据（景点、天气、酒店）。

请严格依据这些信息，生成一份结构化、可直接使用的旅行计划，要求：
1. 按天规划，每天包含 2-4 个景点，行程松紧适度，考虑景点间距离与开放时间。
2. 每天给出早中晚三餐推荐（结合当地特色）。
3. 推荐住宿，优先选择市中心或交通便利区域。
4. 结合天气给出着装与出行建议。
5. 给出预算估算（交通/住宿/餐饮/门票）。
6. 景点与酒店应优先从下方提供的真实数据中选取，并尽量保留原始名称与地址（不要改写、不要编造未提供的景点/酒店）。
7. 输出使用中文。

请直接返回符合给定结构的数据，不要输出任何多余文本。"""


def build_planner_prompt(state: dict) -> str:
    """构建发给 LLM 的用户消息"""
    lines = [
        f"目的地城市：{state.get('city')}",
        f"起止日期：{state.get('start_date')} ~ {state.get('end_date')}",
        f"旅行天数：{state.get('travel_days')} 天",
        f"交通方式：{state.get('transportation')}",
        f"住宿偏好：{state.get('accommodation')}",
        f"旅行偏好：{'、'.join(state.get('preferences', [])) or '无特别偏好'}",
        f"额外要求：{state.get('free_text') or '无'}",
    ]
    return "\n".join(lines)
