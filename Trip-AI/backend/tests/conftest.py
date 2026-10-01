"""Pytest 共享 fixtures：临时 SQLite + TestClient + 依赖覆盖。

关键点：
- 用 tmp_path 下的临时 SQLite 文件库，函数级隔离，不碰真实 trip.db。
- TestClient(app) 不加 with：跳过 lifespan，避免对真实库跑 init_db()（Alembic 迁移）。
- 只 override get_db 一处：路由与 get_current_user 内部都 Depends(get_db)，一并生效。
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base, get_db
from app.main import app


@pytest.fixture()
def engine(tmp_path):
    eng = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    # app.main 导入时已注册全部模型（user/trip/share/generation_task）
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def session_factory(engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture()
def db(session_factory):
    """直接操作测试库的会话（用于插入数据，如过期分享链接）"""
    session = session_factory()
    yield session
    session.close()


@pytest.fixture()
def client(session_factory):
    def _override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    """注册一个测试用户，返回带 Bearer token 的请求头"""
    resp = client.post(
        "/api/auth/register",
        json={"email": "user@test.com", "username": "usera", "password": "pass1234"},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
