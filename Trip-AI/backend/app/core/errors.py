"""统一异常处理：业务错误码 + BizError + 全局异常处理器注册。

约定：
- 所有业务错误统一抛 BizError（携带 ErrorCode），由全局处理器转成统一结构：
  {"code": int, "message": str, "detail": Any, "request_id": str | None}
- 成功响应保持 typed 模型不变，只有错误走这个信封。
"""
from enum import IntEnum
from typing import Any, Dict, Tuple

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.core.context import request_id_var
from app.schemas.common import ErrorResponse


class ErrorCode(IntEnum):
    """业务错误码（分段编码，稳定可编程）"""

    # 通用 1xxxx
    PARAM_VALIDATION = 10001      # 参数校验失败
    UNAUTHORIZED = 10002          # 未登录
    TOKEN_INVALID = 10003         # 登录凭证无效或已过期
    FORBIDDEN = 10004             # 无权限
    NOT_FOUND = 10005             # 资源不存在
    INTERNAL_ERROR = 10006        # 服务器内部错误

    # 用户/认证 2xxxx
    EMAIL_ALREADY_REGISTERED = 20001   # 该邮箱已被注册
    USERNAME_TAKEN = 20002             # 该用户名已被占用
    INVALID_CREDENTIALS = 20003        # 邮箱或密码错误
    USER_NOT_FOUND = 20004             # 用户不存在

    # 行程 3xxxx
    TRIP_NOT_FOUND = 30001
    GENERATION_TASK_NOT_FOUND = 30002

    # 分享 4xxxx
    SHARE_NOT_FOUND = 40001
    SHARE_EXPIRED = 40002

    # 生成 5xxxx
    PLAN_GENERATION_FAILED = 50001


# 每个错误码的默认 HTTP 状态与默认 message
_META: Dict[ErrorCode, Tuple[int, str]] = {
    ErrorCode.PARAM_VALIDATION: (422, "参数校验失败"),
    ErrorCode.UNAUTHORIZED: (401, "未登录"),
    ErrorCode.TOKEN_INVALID: (401, "登录凭证无效或已过期"),
    ErrorCode.FORBIDDEN: (403, "无权限"),
    ErrorCode.NOT_FOUND: (404, "资源不存在"),
    ErrorCode.INTERNAL_ERROR: (500, "服务器内部错误"),
    ErrorCode.EMAIL_ALREADY_REGISTERED: (409, "该邮箱已被注册"),
    ErrorCode.USERNAME_TAKEN: (409, "该用户名已被占用"),
    ErrorCode.INVALID_CREDENTIALS: (401, "邮箱或密码错误"),
    ErrorCode.USER_NOT_FOUND: (401, "用户不存在"),
    ErrorCode.TRIP_NOT_FOUND: (404, "行程不存在"),
    ErrorCode.GENERATION_TASK_NOT_FOUND: (404, "生成任务不存在"),
    ErrorCode.SHARE_NOT_FOUND: (404, "分享链接不存在"),
    ErrorCode.SHARE_EXPIRED: (410, "分享链接已过期"),
    ErrorCode.PLAN_GENERATION_FAILED: (500, "行程生成失败"),
}


class BizError(Exception):
    """业务异常：携带错误码，由全局处理器统一转成 ErrorResponse"""

    def __init__(self, code: ErrorCode, message: str | None = None, detail: Any = None):
        http_status, default_message = _META[code]
        self.code = code
        self.http_status = http_status
        self.message = message or default_message
        self.detail = detail
        super().__init__(self.message)


def _error_response(code: int, http_status: int, message: str, detail: Any = None) -> JSONResponse:
    return JSONResponse(
        status_code=http_status,
        content=ErrorResponse(
            code=code, message=message, detail=detail, request_id=request_id_var.get()
        ).model_dump(),
    )


# 框架级 HTTPException（路由不存在 404 / 方法不允许 405 等）到错误码的映射
_HTTP_STATUS_TO_CODE: Dict[int, Tuple[ErrorCode, str]] = {
    401: (ErrorCode.UNAUTHORIZED, "未登录"),
    403: (ErrorCode.FORBIDDEN, "无权限"),
    404: (ErrorCode.NOT_FOUND, "资源不存在"),
    405: (ErrorCode.NOT_FOUND, "请求方法不允许"),
}


def install_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器（在 app 创建后调用一次）"""

    @app.exception_handler(BizError)
    async def _biz_error_handler(request: Request, exc: BizError):
        return _error_response(int(exc.code), exc.http_status, exc.message, exc.detail)

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(request: Request, exc: RequestValidationError):
        detail = jsonable_encoder(exc.errors())
        return _error_response(int(ErrorCode.PARAM_VALIDATION), 422, "参数校验失败", detail)

    @app.exception_handler(StarletteHTTPException)
    async def _http_handler(request: Request, exc: StarletteHTTPException):
        if exc.status_code in _HTTP_STATUS_TO_CODE:
            code, message = _HTTP_STATUS_TO_CODE[exc.status_code]
        elif exc.status_code >= 500:
            code, message = ErrorCode.INTERNAL_ERROR, "服务器内部错误"
        else:
            code, message = ErrorCode.NOT_FOUND, "请求处理失败"
        return _error_response(int(code), exc.status_code, message)

    @app.exception_handler(Exception)
    async def _unhandled_handler(request: Request, exc: Exception):
        logger.exception("未处理的异常: {} {}", request.method, request.url.path)
        detail = str(exc) if get_settings().debug else None
        return _error_response(int(ErrorCode.INTERNAL_ERROR), 500, "服务器内部错误", detail)
