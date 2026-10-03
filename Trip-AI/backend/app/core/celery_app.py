"""Celery 应用与任务队列配置。

- broker 使用 Redis；结果不落 Redis（task_ignore_result），统一持久化到数据库的
  generation_tasks 表，由轮询接口读取——避免 plan 大 JSON 在 Redis 双写与过期不一致。
- task_acks_late + prefetch=1：worker 崩溃时未确认的任务会被重新投递，配合幂等的
  任务体实现崩溃恢复。
"""
from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "trip_ai",
    broker=settings.redis_url,
    include=["app.tasks.generate"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    task_ignore_result=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    # 硬超时兜底：正常生成约 60–90s，此处 15 分钟上限确保意外死锁不会永久占住 worker
    task_time_limit=900,
)
