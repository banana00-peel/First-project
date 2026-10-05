"""就绪探针 /ready 的测试"""
import app.main as main_module


def test_ready_all_up(client, monkeypatch):
    """DB（临时 SQLite）可达 + Redis 模拟可达 → 200 ready"""
    monkeypatch.setattr(main_module, "_check_redis", lambda: None)
    resp = client.get("/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["checks"] == {"database": "ok", "redis": "ok"}


def test_ready_redis_down(client, monkeypatch):
    """Redis 不可达 → 503 not_ready，checks 里带 redis 错误信息"""

    def _boom():
        raise ConnectionError("redis unreachable")

    monkeypatch.setattr(main_module, "_check_redis", _boom)
    resp = client.get("/ready")
    assert resp.status_code == 503
    body = resp.json()
    assert body["status"] == "not_ready"
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["redis"] == "redis unreachable"
