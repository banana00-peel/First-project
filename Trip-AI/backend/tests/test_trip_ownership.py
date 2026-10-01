"""行程归属隔离：A/B 两用户互不可见，越权访问返回 404（隐藏资源存在性）"""


def _register(client, email, username):
    r = client.post(
        "/api/auth/register",
        json={"email": email, "username": username, "password": "pass1234"},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _create_trip(client, headers, city="北京"):
    payload = {
        "city": city,
        "start_date": "2026-10-01",
        "end_date": "2026-10-03",
        "travel_days": 3,
        "transportation": "公共交通",
        "accommodation": "经济型酒店",
        "preferences": [],
        "free_text": "",
        "plan": {"city": city, "days": []},
    }
    r = client.post("/api/trips", json=payload, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_owner_isolation(client):
    a = _register(client, "a@test.com", "alice")
    b = _register(client, "b@test.com", "bob")
    trip_id = _create_trip(client, a)

    # A 能看到自己的行程
    assert any(t["id"] == trip_id for t in client.get("/api/trips", headers=a).json())

    # B 列表为空，看不到 A 的行程
    assert client.get("/api/trips", headers=b).json() == []

    # B 访问/删除 A 的行程 → 404（不暴露资源存在性）
    assert client.get(f"/api/trips/{trip_id}", headers=b).status_code == 404
    assert client.delete(f"/api/trips/{trip_id}", headers=b).status_code == 404

    # A 删除成功
    r = client.delete(f"/api/trips/{trip_id}", headers=a)
    assert r.status_code == 200
    assert r.json()["success"] is True


def test_unauthenticated_crud(client):
    a = _register(client, "a@test.com", "alice")
    trip_id = _create_trip(client, a)
    assert client.get("/api/trips").status_code == 401
    assert client.get(f"/api/trips/{trip_id}").status_code == 401
    assert client.delete(f"/api/trips/{trip_id}").status_code == 401
