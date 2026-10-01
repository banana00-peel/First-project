"""Langfuse 链路追踪接入（可选，默认关闭）"""
from typing import Any, Dict, Optional

from app.config import get_settings


def get_langfuse_handler(metadata: Optional[Dict[str, Any]] = None):
    """返回 Langfuse CallbackHandler；未启用时返回 None。

    每个任务/请求构造一个 handler，作为一条独立 trace；callbacks 会经 LangGraph run config
    自动下传到各节点与 LLM 调用，因此无需改动 get_llm / nodes.py。
    """
    s = get_settings()
    if not s.langfuse_enabled:
        return None

    from langfuse.langchain import CallbackHandler

    return CallbackHandler(
        public_key=s.langfuse_public_key,
        secret_key=s.langfuse_secret_key,
        host=s.langfuse_host,
        trace_name="trip_generation",
        session_id=(metadata or {}).get("task_id"),
        tags=["trip-ai", "generation"],
        metadata=metadata,
    )
