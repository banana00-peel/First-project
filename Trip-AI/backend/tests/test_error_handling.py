"""验证 P0-5：统一错误响应 {code, message, detail, request_id} 与业务错误码分段"""


def _register(client, email, username):
    return client.post(
        "/api/auth/register",
        json={"email": email, "username": username, "password": "pass1234"},
    )


def test_duplicate_email(client):
    assert _register(client, "dup@test.com", "alice").status_code == 200
    r = _register(client, "dup@test.com", "bob")
    assert r.status_code == 409
    body = r.json()
    assert body["code"] == 20001
    assert body["message"] == "该邮箱已被注册"
    assert body["request_id"]  # 统一结构含 request_id，关联日志


def test_duplicate_username(client):
    assert _register(client, "a@test.com", "alice").status_code == 200
    r = _register(client, "b@test.com", "alice")
    assert r.status_code == 409
    assert r.json()["code"] == 20002


def test_param_validation_shape(client):
    r = client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "username": "a", "password": "x"},
    )
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == 10001
    assert body["message"] == "参数校验失败"
    assert isinstance(body["detail"], list)  # 字段级明细
    assert body["request_id"]


def test_unauthenticated(client):
    r = client.get("/api/trips")
    assert r.status_code == 401
    assert r.json()["code"] == 10002


def test_trip_not_found(client, auth_headers):
    r = client.get("/api/trips/999999", headers=auth_headers)
    assert r.status_code == 404
    assert r.json()["code"] == 30001


def test_generation_task_not_found(client):
    r = client.get("/api/trips/generate/does-not-exist")
    assert r.status_code == 404
    assert r.json()["code"] == 30002


def test_route_not_found(client):
    """框架级 404（路由不存在）→ 通用 NOT_FOUND 错误码"""
    r = client.get("/api/no-such-route")
    assert r.status_code == 404
    assert r.json()["code"] == 10005


def test_request_id_echo(client):
    """中间件透传/回写 X-Request-ID"""
    r = client.get("/health", headers={"X-Request-ID": "req-abc-123"})
    assert r.headers["X-Request-ID"] == "req-abc-123"
