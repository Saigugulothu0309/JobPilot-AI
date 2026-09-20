"""Authentication HTTP endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db_session
from app.modules.auth.models import User
from app.modules.auth.schemas import LoginRequest, RegistrationRequest, TokenResponse, UserResponse
from app.modules.auth.service import AuthenticationService, DuplicateEmailError
from app.security.auth import create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegistrationRequest, session: Session = Depends(get_db_session)) -> User:
    try:
        return AuthenticationService(session).register(payload.email, payload.password)
    except DuplicateEmailError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        ) from None


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_db_session)) -> TokenResponse:
    user = AuthenticationService(session).authenticate(payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
