"""行程生成任务（Celery）：后台执行 LangGraph 规划并回写任务状态。"""
from loguru import logger

from app.agents.graph import _is_connection_error, run_planner
from app.core.celery_app import celery_app
from app.core.context import request_id_var
from app.core.db import SessionLocal
from app.models.generation_task import GenerationTask, TaskStatus
from app.tasks.worker_loop import run_async


@celery_app.task(
    bind=True,
    name="app.tasks.generate.generate_trip_task",
    max_retries=1,
    default_retry_delay=5,
)
def generate_trip_task(self, task_id: str) -> None:
    """执行一次行程生成，并把结果/错误写回 generation_tasks 表。

    任务体幂等：重跑只会覆盖 plan/status，不会产生副作用，配合 task_acks_late
    在 worker 崩溃后安全重投。
    """
    db = SessionLocal()
    token = None
    try:
        task = db.get(GenerationTask, task_id)
        if task is None:
            logger.warning("生成任务不存在: {}", task_id)
            return

        # 恢复请求级 request_id，让 worker 侧日志与 HTTP 侧用同一个 id 关联
        token = request_id_var.set(task.request_id) if task.request_id else None
        task.status = TaskStatus.PROCESSING.value
        db.commit()

        result = run_async(
            run_planner(
                task.request,
                trace_metadata={"task_id": task.id, "trace_name": "trip_generation"},
            )
        )
        plan = result.get("plan")
        if not plan:
            raise ValueError("LLM 未返回有效计划")

        task.plan = plan
        task.status = TaskStatus.COMPLETED.value
        task.error = None
        db.commit()
        logger.info("生成任务完成: {}", task_id)
    except Exception as e:  # noqa: BLE001
        db.rollback()
        # 连接类瞬时错误且未达重试上限：交回 broker 重试；其余标记失败
        if self.request.retries < self.max_retries and _is_connection_error(e):
            logger.warning("生成任务遇到连接错误，将重试: {} ({})", task_id, e)
            raise self.retry(exc=e) from e
        task = db.get(GenerationTask, task_id)
        if task is not None:
            task.status = TaskStatus.FAILED.value
            task.error = str(e)
            db.commit()
        logger.exception("生成任务失败: {}", task_id)
    finally:
        if token is not None:
            request_id_var.reset(token)
        db.close()
