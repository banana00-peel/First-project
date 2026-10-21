"""request_id 跨 HTTP → Celery 边界的链路追踪测试"""
from app.core.celery_app import celery_app
from app.core.context import request_id_var
from app.core.ratelimit import limiter
from app.models.generation_task import GenerationTask


def _payload():
    return {
        "city": "北京",
        "start_date": "2026-10-01",
        "end_date": "2026-10-02",
        "travel_days": 2,
        "transportation": "公共交通",
        "accommodation": "经济型酒店",
        "preferences": [],
        "free_text": "",
    }


def test_generate_persists_request_id_from_header(client, db, monkeypatch):
    """带 X-Request-ID 头时，request_id 落库到 generation_tasks 行并回显响应头"""
    monkeypatch.setattr(celery_app, "send_task", lambda *a, **k: None)
    limiter.reset()

    resp = client.post(
        "/api/trips/generate",
        json=_payload(),
        headers={"X-Request-ID": "trace-abc-123"},
    )
    assert resp.status_code == 202, resp.text

    task = db.query(GenerationTask).filter(GenerationTask.id == resp.json()["task_id"]).first()
    assert task is not None
    assert task.request_id == "trace-abc-123"
    assert resp.headers["x-request-id"] == "trace-abc-123"


def test_generate_generates_request_id_without_header(client, db, monkeypatch):
    """未带头时中间件生成 request_id，同样落库"""
    monkeypatch.setattr(celery_app, "send_task", lambda *a, **k: None)
    limiter.reset()

    resp = client.post("/api/trips/generate", json=_payload())
    assert resp.status_code == 202, resp.text

    task = db.query(GenerationTask).filter(GenerationTask.id == resp.json()["task_id"]).first()
    assert task is not None
    assert task.request_id and task.request_id != ""


def test_worker_restores_request_id_contextvar(db, session_factory, monkeypatch):
    """worker 执行时把行的 request_id 恢复到 contextvar，供日志 patcher 读取"""
    task = GenerationTask(request=_payload(), request_id="trace-worker-1")
    db.add(task)
    db.flush()
    task_id = task.id
    db.commit()

    captured = {}

    def fake_run_async(coro):
        captured["request_id"] = request_id_var.get()
        return {"plan": {"city": "北京"}}

    # worker 内 SessionLocal 指向真实库，测试里换成测试 SQLite 的 sessionmaker
    monkeypatch.setattr("app.tasks.generate.SessionLocal", session_factory)
    monkeypatch.setattr(
        "app.tasks.generate.run_planner", lambda state, trace_metadata=None: None
    )
    monkeypatch.setattr("app.tasks.generate.run_async", fake_run_async)

    from app.tasks.generate import generate_trip_task

    generate_trip_task.apply(args=[task_id])

    assert captured["request_id"] == "trace-worker-1"
    assert request_id_var.get() is None  # finally 已 reset，不泄漏到后续上下文


def test_worker_tolerates_missing_request_id(db, session_factory, monkeypatch):
    """历史行 request_id 为 NULL 时 worker 不报错、不 set contextvar"""
    task = GenerationTask(request=_payload(), request_id=None)
    db.add(task)
    db.flush()
    task_id = task.id
    db.commit()

    monkeypatch.setattr("app.tasks.generate.SessionLocal", session_factory)
    monkeypatch.setattr(
        "app.tasks.generate.run_planner", lambda state, trace_metadata=None: None
    )
    monkeypatch.setattr(
        "app.tasks.generate.run_async", lambda coro: {"plan": {"city": "北京"}}
    )

    from app.tasks.generate import generate_trip_task

    generate_trip_task.apply(args=[task_id])  # 不应抛异常
    assert request_id_var.get() is None
