"""工具调用超时与异常收敛测试（_call_tool）。"""
import asyncio
import json

from app.services.amap_mcp import _call_tool


class _FakeTool:
    """可配置 ainvoke 行为：返回结果 / 抛异常 / 延迟（模拟卡死）"""

    def __init__(self, result=None, exc=None, delay=0.0):
        self.name = "fake_tool"
        self._result = result
        self._exc = exc
        self._delay = delay

    async def ainvoke(self, args):
        if self._delay:
            await asyncio.sleep(self._delay)
        if self._exc is not None:
            raise self._exc
        return self._result


def test_call_tool_returns_parsed_dict():
    tool = _FakeTool(result=json.dumps({"pois": [{"id": "1"}]}, ensure_ascii=False))
    result = asyncio.run(_call_tool(tool, {}))
    assert result == {"pois": [{"id": "1"}]}


def test_call_tool_timeout_returns_none():
    tool = _FakeTool(delay=10.0)
    result = asyncio.run(_call_tool(tool, {}, timeout=0.05))
    assert result is None


def test_call_tool_exception_returns_none():
    tool = _FakeTool(exc=RuntimeError("boom"))
    result = asyncio.run(_call_tool(tool, {}))
    assert result is None
