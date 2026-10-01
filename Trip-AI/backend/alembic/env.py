"""Alembic 迁移环境。

- 数据库 URL 从 app.config 读取（与运行时代码同一来源，避免两处配置不一致）。
- 绑定 app 模型的 metadata 作为 autogenerate 的对比目标。
- 不调用 fileConfig，避免覆盖应用的 loguru 日志配置。
"""
import os
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

# 确保 backend/ 在 sys.path，使 `app` 可导入（CLI 与程序化调用均适用）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings  # noqa: E402
from app.core.db import Base  # noqa: E402
from app.models import generation_task, share, trip, user  # noqa: F401,E402  # 注册模型到 metadata

config = context.config
target_metadata = Base.metadata

# 数据库 URL 单一来源：app.config 的 settings（可被环境变量 DATABASE_URL 覆盖）
config.set_main_option("sqlalchemy.url", get_settings().database_url)


def run_migrations_offline() -> None:
    """离线模式：仅生成 SQL，不连接数据库"""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式：连接数据库执行迁移"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
