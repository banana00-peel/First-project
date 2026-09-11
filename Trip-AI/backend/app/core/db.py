"""数据库会话管理（同步 SQLAlchemy）"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()

_connect_args = {}
if settings.database_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    """FastAPI 依赖：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """启动时建表（MVP 用 create_all；后续引入 Alembic 迁移）"""
    # noqa: F401 —— 导入模型以注册到 Base.metadata
    from app.models import user, trip, share  # noqa: F401

    Base.metadata.create_all(bind=engine)
