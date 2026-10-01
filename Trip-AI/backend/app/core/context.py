"""请求级上下文（contextvars）。

request_id 由 RequestContextMiddleware 写入，供日志、trace、错误响应共享，
把同一次请求的日志与链路串起来。
"""
import contextvars

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
