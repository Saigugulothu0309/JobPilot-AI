"""Password hashing, token handling, and current-user resolution."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.session import get_db_session
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository

password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    return password_hash.verify(password, stored_hash)


def _auth_secret() -> str:
    secret = get_settings().auth_secret
    if not secret:
        raise RuntimeError("AUTH_SECRET must be configured for authentication.")
    return secret


def create_access_token(user_id: UUID, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.auth_token_expire_minutes)
    )
    return jwt.encode({"sub": str(user_id), "exp": expires_at}, _auth_secret(), algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_db_session),
) -> User:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if credentials is None:
        raise unauthorized
    try:
        payload = jwt.decode(credentials.credentials, _auth_secret(), algorithms=[ALGORITHM])
        user_id = UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise unauthorized from None

    user = UserRepository(session).get_by_id(user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user
