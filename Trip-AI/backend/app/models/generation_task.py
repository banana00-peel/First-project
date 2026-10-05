"""生成任务模型（异步行程生成的持久化状态）"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TaskStatus(str, enum.Enum):
    """生成任务状态机：pending → processing → completed / failed"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


def _gen_task_id() -> str:
    return uuid.uuid4().hex


class GenerationTask(Base):  # type: ignore[misc, valid-type]
    __tablename__ = "generation_tasks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_gen_task_id)
    request: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), default=TaskStatus.PENDING.value, nullable=False
    )
    plan: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
