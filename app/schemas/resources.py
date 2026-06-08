from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import Timestamped


class OwnedResourceRead(Timestamped):
    owner_id: int
    name: str
    description: str | None


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    price: Decimal = Field(default=Decimal("0.00"), ge=0)
    stock: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)


class ProductRead(OwnedResourceRead):
    price: Decimal
    stock: int


class OrderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    total_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    status: str = Field(default="new", max_length=40)


class OrderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    total_amount: Decimal | None = Field(default=None, ge=0)
    status: str | None = Field(default=None, max_length=40)


class OrderRead(OwnedResourceRead):
    total_amount: Decimal
    status: str


class StoreCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    address: str | None = Field(default=None, max_length=255)


class StoreUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    address: str | None = Field(default=None, max_length=255)


class StoreRead(OwnedResourceRead):
    address: str | None
