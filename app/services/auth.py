from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.auth import Role, TokenBlacklist, User
from app.schemas.auth import ProfileUpdate, UserRegister


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def register(self, payload: UserRegister) -> User:
        existing = self.db.scalar(select(User).where(User.email == payload.email.lower()))
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        role = self.db.scalar(select(Role).where(Role.name == "user"))
        if role is None:
            raise HTTPException(status_code=500, detail="Default role is not configured")

        user = User(
            first_name=payload.first_name,
            last_name=payload.last_name,
            middle_name=payload.middle_name,
            email=payload.email.lower(),
            hashed_password=hash_password(payload.password),
            role_id=role.id,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, email: str, password: str) -> tuple[str, str, datetime]:
        user = self.db.scalar(select(User).where(User.email == email.lower()))
        if user is None or not user.is_active or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        return create_access_token(str(user.id))

    def blacklist_token(self, jti: str, user_id: int | None, expires_at: datetime) -> None:
        exists = self.db.scalar(select(TokenBlacklist).where(TokenBlacklist.jti == jti))
        if exists is None:
            self.db.add(TokenBlacklist(jti=jti, user_id=user_id, expires_at=expires_at))
            self.db.commit()

    def update_profile(self, user: User, payload: ProfileUpdate) -> User:
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(user, field, value)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def soft_delete(self, user: User, jti: str, expires_at: datetime) -> None:
        user.is_active = False
        self.db.add(user)
        self.db.flush()
        self.blacklist_token(jti=jti, user_id=user.id, expires_at=expires_at)