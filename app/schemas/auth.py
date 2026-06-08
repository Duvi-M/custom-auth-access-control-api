from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel


class UserRegister(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=72)
    password_repeat: str = Field(min_length=8, max_length=72)

    @field_validator("password_repeat")
    @classmethod
    def passwords_match(cls, password_repeat: str, info) -> str:
        if password_repeat != info.data.get("password"):
            raise ValueError("passwords do not match")
        return password_repeat

    @field_validator("email")
    @classmethod
    def valid_email(cls, email: str) -> str:
        email = email.strip().lower()
        if "@" not in email or "." not in email.rsplit("@", maxsplit=1)[-1]:
            raise ValueError("invalid email address")
        return email


class UserLogin(BaseModel):
    email: str = Field(max_length=255)
    password: str

    @field_validator("email")
    @classmethod
    def valid_email(cls, email: str) -> str:
        email = email.strip().lower()
        if "@" not in email or "." not in email.rsplit("@", maxsplit=1)[-1]:
            raise ValueError("invalid email address")
        return email


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class UserRead(ORMModel):
    id: int
    first_name: str
    last_name: str
    middle_name: str | None
    email: str
    is_active: bool
    role_id: int
    role_name: str | None


class ProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)