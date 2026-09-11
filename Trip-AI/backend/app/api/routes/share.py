"""分享路由"""
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.share import ShareLink
from app.models.trip import Trip
from app.models.user import User
from app.schemas.share import ShareCreateRequest, ShareLinkOut

router = APIRouter(prefix="/share", tags=["分享"])


def _build_url(request: Request, token: str) -> str:
    base = request.base_url
    return f"{base}share/{token}"


@router.post("/trips/{trip_id}", response_model=ShareLinkOut, summary="创建分享链接")
def create_share(
    trip_id: int,
    payload: ShareCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")

    token = secrets.token_urlsafe(32)
    expires_at = None
    if payload.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=payload.expires_in_days)

    link = ShareLink(trip_id=trip.id, token=token, created_by=user.id, expires_at=expires_at)
    db.add(link)
    db.commit()
    db.refresh(link)

    return ShareLinkOut(token=link.token, url=_build_url(request, token), expires_at=link.expires_at)


@router.get("/trips/{trip_id}/links", response_model=list[ShareLinkOut], summary="行程的分享链接列表")
def list_links(trip_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")
    links = db.query(ShareLink).filter(ShareLink.trip_id == trip_id).all()
    return [ShareLinkOut(token=l.token, url=_build_url(request, l.token), expires_at=l.expires_at) for l in links]


@router.get("/{token}", summary="通过 token 查看分享的行程（无需登录）")
def view_share(token: str, db: Session = Depends(get_db)):
    link = db.query(ShareLink).filter(ShareLink.token == token).first()
    if not link:
        raise HTTPException(status_code=404, detail="分享链接不存在")

    # SQLite 不保存时区信息，读回的 datetime 为 naive，需补齐 UTC 时区后再比较
    expires_at = link.expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at and expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="分享链接已过期")

    trip = db.get(Trip, link.trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")

    return {
        "city": trip.city,
        "start_date": trip.start_date,
        "end_date": trip.end_date,
        "travel_days": trip.travel_days,
        "transportation": trip.transportation,
        "accommodation": trip.accommodation,
        "preferences": trip.preferences,
        "free_text": trip.free_text,
        "plan": trip.plan,
        "shared_at": link.created_at.isoformat() if link.created_at else "",
    }
