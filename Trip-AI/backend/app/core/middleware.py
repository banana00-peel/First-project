"""请求上下文中间件：为每个请求生成/透传 X-Request-ID"""
import uuid

from starlette.middleware.base import BaseHTTPMiddleware

from app.core.context import request_id_var


class RequestContextMiddleware(BaseHTTPMiddleware):
    """读入或生成 X-Request-ID，写入 contextvar，并回写到响应头。

    这样日志、错误响应、链路追踪都能用同一个 request_id 把一次请求串起来。
    """

    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_var.reset(token)
