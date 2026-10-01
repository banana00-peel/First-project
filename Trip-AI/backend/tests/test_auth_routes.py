"""认证路由集成测试：注册/登录/me 正常与异常分支"""


def test_register_returns_token_and_user(client):
    r = client.post(
        "/api/auth/register",
        json={"email": "alice@test.com", "username": "alice", "password": "secret1"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "alice@test.com"
    assert body["user"]["username"] == "alice"
    # 密码哈希不外泄
    assert "password" not in str(body)


def test_login_success(client):
    client.post(
        "/api/auth/register",
        json={"email": "alice@test.com", "username": "alice", "password": "secret1"},
    )
    r = client.post(
        "/api/auth/login", json={"email": "alice@test.com", "password": "secret1"}
    )
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_login_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={"email": "alice@test.com", "username": "alice", "password": "secret1"},
    )
    r = client.post("/api/auth/login", json={"email": "alice@test.com", "password": "wrong"})
    assert r.status_code == 401
    assert r.json()["code"] == 20003


def test_login_unknown_user(client):
    r = client.post("/api/auth/login", json={"email": "nobody@test.com", "password": "whatever"})
    assert r.status_code == 401
    assert r.json()["code"] == 20003


def test_me_requires_auth(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_returns_current_user(client, auth_headers):
    r = client.get("/api/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["email"] == "user@test.com"
