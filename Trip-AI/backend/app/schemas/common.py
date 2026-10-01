"""通用 schema：统一错误响应、通用消息响应"""
from typing import Any, Optional

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """统一错误响应体：所有错误（业务错误/校验错误/未捕获异常）都返回该结构"""

    code: int                      # 业务错误码（见 app.core.errors.ErrorCode）
    message: str                   # 人类可读的错误说明
    detail: Any = None             # 附加信息（字段级校验错误等）
    request_id: Optional[str] = None  # 关联日志与链路追踪


class MessageResponse(BaseModel):
    """通用成功消息响应（删除等无需返回实体数据的接口）"""

    success: bool = True
    message: str = ""
