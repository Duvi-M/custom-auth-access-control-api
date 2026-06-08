from datetime import UTC, datetime, timedelta
from uuid import uuid4

import bcrypt
from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("bcrypt passwords must be 72 bytes or fewer")
    try:
        return pwd_context.hash(password)
    except (AttributeError, ValueError):
        # Some local bcrypt/passlib version combinations fail passlib's backend
        # probe. Direct bcrypt keeps hashing behavior available and explicit.
        pass
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > 72:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (AttributeError, ValueError):
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))


def create_access_token(subject: str) -> tuple[str, str, datetime]:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    jti = str(uuid4())
    payload = {
        "sub": subject,
        "jti": jti,
        "exp": expires_at,
        "iat": datetime.now(UTC),
        "type": "access",
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expires_at


def decode_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])