"""限流测试：生成接口超过阈值返回 429 + 统一错误信封"""
from app.core.ratelimit import limiter


def test_generate_rate_limited(client, monkeypatch):
    # 入队是慢操作且测试环境无 broker，mock 掉以让请求快速、确定地完成
    from app.core.celery_app import celery_app

    monkeypatch.setattr(celery_app, "send_task", lambda *a, **k: None)
    # 清空计数，避免与其他用例/多次运行串扰
    limiter.reset()

    payload = {
        "city": "北京",
        "start_date": "2026-10-01",
        "end_date": "2026-10-02",
        "travel_days": 2,
        "transportation": "公共交通",
        "accommodation": "经济型酒店",
        "preferences": [],
        "free_text": "",
    }

    # 默认阈值 5/minute：前 5 次在阈值内正常返回 202
    for _ in range(5):
        resp = client.post("/api/trips/generate", json=payload)
        assert resp.status_code == 202, resp.text

    # 第 6 次超阈值，返回 429 + 统一错误信封
    resp = client.post("/api/trips/generate", json=payload)
    assert resp.status_code == 429, resp.text
    data = resp.json()
    assert data["code"] == 10007
    assert "频繁" in data["message"]

    limiter.reset()
