"""生成任务模型与 schema 的纯单元测试（不连库）"""
from app.models.generation_task import TaskStatus
from app.schemas.trip import TaskAcceptedResponse, TaskStatusResponse


def test_task_status_values():
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.PROCESSING.value == "processing"
    assert TaskStatus.COMPLETED.value == "completed"
    assert TaskStatus.FAILED.value == "failed"


def test_task_accepted_response():
    resp = TaskAcceptedResponse(task_id="abc123", status="pending")
    assert resp.task_id == "abc123"
    assert resp.status == "pending"


def test_task_status_response_pending():
    resp = TaskStatusResponse(task_id="abc123", status="processing", plan=None, error=None)
    assert resp.plan is None
    assert resp.error is None


def test_task_status_response_failed():
    resp = TaskStatusResponse(task_id="abc123", status="failed", plan=None, error="boom")
    assert resp.error == "boom"
