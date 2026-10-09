"""分享相关 schema"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class ShareCreateRequest(BaseModel):
    expires_in_days: Optional[int] = None  # None 表示永久


class ShareLinkOut(BaseModel):
    token: str
    url: str
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ShareViewResponse(BaseModel):
    """分享行程只读视图（view_share 返回，无需登录）"""

    city: str
    start_date: str
    end_date: str
    travel_days: int
    transportation: str
    accommodation: str
    preferences: List[Any]
    free_text: str
    plan: Dict[str, Any]
    shared_at: str
