"""Celery worker 进程内的持久 asyncio 事件循环。

Celery 任务是同步执行的，但项目的 LangGraph / MCP 栈是 async，且其内部
（ChatOpenAI 客户端、编译后的图、MCP stdio 会话）都是模块级单例，绑定在首次
创建它们的那个事件循环上。若每个任务各自 asyncio.run() 开新 loop，第二个任务
会复用绑死在已关闭 loop 上的单例而报错（"Event loop is closed"）。

因此为每个 worker 进程启动一个常驻事件循环（后台线程 run_forever），任务协程
用 run_async() 提交上去执行——单例只创建一次、常驻同一 loop，与 FastAPI 进程的
行为一致，graph.py / amap_mcp.py 内部无需任何改动。
"""
import asyncio
import os
import threading
from typing import Any, Coroutine, Optional

from celery.signals import worker_process_init, worker_process_shutdown
from loguru import logger

_loop: Optional[asyncio.AbstractEventLoop] = None
_thread: Optional[threading.Thread] = None


@worker_process_init.connect
def _on_worker_process_init(**kwargs) -> None:
    global _loop, _thread
    if _loop is not None:
        return
    _loop = asyncio.new_event_loop()
    _thread = threading.Thread(target=_loop.run_forever, name="celery-asyncio-loop", daemon=True)
    _thread.start()
    logger.info("worker 持久事件循环已启动（pid {}）", os.getpid())


@worker_process_shutdown.connect
def _on_worker_process_shutdown(**kwargs) -> None:
    global _loop, _thread
    if _loop is None or not _loop.is_running():
        _loop = None
        return
    try:
        from app.services.amap_mcp import close_amap_mcp

        async def _close() -> None:
            await close_amap_mcp()

        asyncio.run_coroutine_threadsafe(_close(), _loop).result(timeout=10)
    except Exception as e:  # noqa: BLE001 —— 关停阶段尽力而为
        logger.warning("worker 关闭 MCP 会话失败: {}", e)
    finally:
        _loop.call_soon_threadsafe(_loop.stop)
    _loop = None
    _thread = None


def run_async(coro: Coroutine[Any, Any, Any]) -> Any:
    """把协程提交到 worker 进程的持久事件循环上执行，并同步等待结果。"""
    assert _loop is not None, "worker 事件循环尚未初始化"
    return asyncio.run_coroutine_threadsafe(coro, _loop).result()
