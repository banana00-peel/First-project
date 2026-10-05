"""数据库会话管理（同步 SQLAlchemy）"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import BASE_DIR, get_settings

settings = get_settings()

_connect_args = {}
if settings.database_url.startswith("sqlite"):
    # check_same_thread：FastAPI 多线程访问 SQLite；timeout：web + worker 多进程并发写时等待锁
    _connect_args = {"check_same_thread": False, "timeout": 30}

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
    """启动时执行数据库迁移（Alembic 升级到 head）。

    迁移脚本位于 backend/alembic，数据库 URL 由 alembic/env.py 从 app.config 读取。
    """
    from alembic.config import Config

    from alembic import command

    # noqa: F401 —— 导入模型以注册到 Base.metadata（Alembic autogenerate 依赖）
    from app.models import generation_task, share, trip, user  # noqa: F401

    cfg = Config(str(BASE_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BASE_DIR / "alembic"))
    command.upgrade(cfg, "head")
