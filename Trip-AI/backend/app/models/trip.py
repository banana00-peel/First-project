"""行程模型"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    city: Mapped[str] = mapped_column(String(64), nullable=False)
    start_date: Mapped[str] = mapped_column(String(10), nullable=False)
    end_date: Mapped[str] = mapped_column(String(10), nullable=False)
    travel_days: Mapped[int] = mapped_column(Integer, default=1)

    transportation: Mapped[str] = mapped_column(String(32), default="公共交通")
    accommodation: Mapped[str] = mapped_column(String(32), default="经济型酒店")
    preferences: Mapped[list] = mapped_column(JSON, default=list)
    free_text: Mapped[str] = mapped_column(Text, default="")

    plan: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="completed")  # completed / failed

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    owner = relationship("User", back_populates="trips")
    share_links = relationship("ShareLink", back_populates="trip", cascade="all, delete-orphan")
