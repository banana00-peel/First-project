"""日志配置：loguru 统一格式 + request_id 自动注入"""
import sys

from loguru import logger

from app.config import get_settings
from app.core.context import request_id_var


def _inject_request_id(record) -> None:
    """loguru patcher：把当前请求的 request_id 注入每条日志，无需改动现有 log 语句"""
    record["extra"]["request_id"] = request_id_var.get() or "-"


def setup_logging() -> None:
    """初始化日志：去掉默认 sink，按统一格式输出到 stderr，每行带 request_id"""
    settings = get_settings()
    logger.remove()
    # patcher 是 loguru 的全局配置（非 add 参数）：给每条记录注入当前 request_id
    logger.configure(patcher=_inject_request_id)
    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{extra[request_id]}</cyan> | "
        "<level>{message}</level>"
    )
    logger.add(sys.stderr, level=settings.log_level, format=fmt)
