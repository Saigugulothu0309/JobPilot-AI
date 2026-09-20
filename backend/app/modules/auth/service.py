"""Authentication business operations."""

from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository
from app.security.auth import hash_password, verify_password


class DuplicateEmailError(Exception):
    """Raised when a registration email is already in use."""


class AuthenticationService:
    def __init__(self, session: Session) -> None:
        self.repository = UserRepository(session)

    def register(self, email: str, password: str) -> User:
        normalized_email = email.lower()
        if self.repository.get_by_email(normalized_email) is not None:
            raise DuplicateEmailError
        return self.repository.create(normalized_email, hash_password(password))

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.repository.get_by_email(email.lower())
        if user is None or not user.is_active or not verify_password(password, user.password_hash):
            return None
        return user
