"""worker 持久事件循环的单元测试（无需 Redis / DB / 网络）。

验证核心机制：协程从调用线程提交到常驻事件循环上执行并同步拿到结果，
且循环可安全关闭——这是让 async 的 LangGraph/MCP 栈在同步 Celery worker 中
复用的关键，必须确保不依赖外部服务即可验证。
"""
import asyncio

from app.tasks import worker_loop


def test_run_async_on_persistent_loop():
    worker_loop._on_worker_process_init()
    try:
        async def _answer() -> int:
            await asyncio.sleep(0)
            return 42

        assert worker_loop.run_async(_answer()) == 42
    finally:
        worker_loop._on_worker_process_shutdown()


def test_loop_reinitializes_after_shutdown():
    worker_loop._on_worker_process_init()
    worker_loop._on_worker_process_shutdown()
    assert worker_loop._loop is None
    # 再次初始化应能拿到一个新的可用循环
    worker_loop._on_worker_process_init()
    try:
        async def _echo(x: str) -> str:
            return x

        assert worker_loop.run_async(_echo("ok")) == "ok"
    finally:
        worker_loop._on_worker_process_shutdown()
