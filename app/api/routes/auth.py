from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context, get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.schemas.auth import ProfileUpdate, TokenResponse, UserLogin, UserRead, UserRegister
from app.schemas.common import Message
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)) -> User:
    return AuthService(db).register(payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    token, _, expires_at = AuthService(db).login(payload.email, payload.password)
    return TokenResponse(access_token=token, expires_at=expires_at)


@router.post("/logout", response_model=Message)
def logout(auth: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> Message:
    AuthService(db).blacklist_token(auth.jti, auth.user.id, auth.expires_at)
    return Message(detail="Logged out successfully")


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/me", response_model=UserRead)
def update_me(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    return AuthService(db).update_profile(user, payload)


@router.delete("/me", response_model=Message)
def delete_me(auth: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> Message:
    AuthService(db).soft_delete(auth.user, auth.jti, auth.expires_at)
    return Message(detail="Account deactivated and token revoked")
