"""分享路由集成测试：创建链接、无鉴权查看、404/410 分支"""

from datetime import datetime, timedelta, timezone

from app.models.share import ShareLink


def _register(client, email, username):
    r = client.post(
        "/api/auth/register",
        json={"email": email, "username": username, "password": "pass1234"},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}, r.json()["user"]["id"]


def _create_trip(client, headers):
    r = client.post(
        "/api/trips",
        json={
            "city": "北京",
            "start_date": "2026-10-01",
            "end_date": "2026-10-03",
            "travel_days": 3,
            "plan": {"city": "北京", "days": []},
        },
        headers=headers,
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_create_and_view_share(client):
    headers, _ = _register(client, "a@test.com", "alice")
    trip_id = _create_trip(client, headers)

    r = client.post(f"/api/share/trips/{trip_id}", json={"expires_in_days": 7}, headers=headers)
    assert r.status_code == 200, r.text
    token = r.json()["token"]
    assert r.json()["url"].endswith(f"/share/{token}")

    # 无鉴权查看
    r2 = client.get(f"/api/share/{token}")
    assert r2.status_code == 200
    assert r2.json()["city"] == "北京"


def test_view_share_not_found(client):
    r = client.get("/api/share/no-such-token")
    assert r.status_code == 404
    assert r.json()["code"] == 40001


def test_view_share_expired(client, db):
    headers, user_id = _register(client, "a@test.com", "alice")
    trip_id = _create_trip(client, headers)

    # 直接插入一条已过期的分享链接（SQLite 存回的 expires_at 为 naive，路由内会补 UTC）
    link = ShareLink(
        trip_id=trip_id,
        token="expired-token",
        created_by=user_id,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db.add(link)
    db.commit()

    r = client.get("/api/share/expired-token")
    assert r.status_code == 410
    assert r.json()["code"] == 40002
