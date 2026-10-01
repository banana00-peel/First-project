"""FastAPI 依赖：获取当前用户"""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import BizError, ErrorCode
from app.core.security import decode_token
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise BizError(ErrorCode.UNAUTHORIZED)
    try:
        payload = decode_token(credentials.credentials)
        user_id = int(payload.get("sub"))
    except Exception:
        raise BizError(ErrorCode.TOKEN_INVALID)

    user = db.get(User, user_id)
    if not user:
        raise BizError(ErrorCode.USER_NOT_FOUND)
    return user
