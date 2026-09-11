"""分享相关 schema"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ShareCreateRequest(BaseModel):
    expires_in_days: Optional[int] = None  # None 表示永久


class ShareLinkOut(BaseModel):
    token: str
    url: str
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True
