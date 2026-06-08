from typing import Any, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.models.resources import Order, Product, Store
from app.schemas.common import Message
from app.schemas.resources import (
    OrderCreate,
    OrderRead,
    OrderUpdate,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    StoreCreate,
    StoreRead,
    StoreUpdate,
)
from app.services.permissions import PermissionAction, PermissionService

ResourceT = TypeVar("ResourceT", Product, Order, Store)


def build_resource_router(
    *,
    prefix: str,
    tag: str,
    model: type[ResourceT],
    element_name: str,
    create_schema: type[BaseModel],
    update_schema: type[BaseModel],
    read_schema: type[BaseModel],
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[tag])

    @router.get("", response_model=list[read_schema])  # type: ignore[valid-type]
    def list_items(
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> list[ResourceT]:
        scope = PermissionService(db).collection_scope(user, element_name)
        stmt = select(model).order_by(model.id)
        if scope == "owned":
            stmt = stmt.where(model.owner_id == user.id)
        stmt = stmt.limit(limit).offset(offset)
        return list(db.scalars(stmt).all())

    @router.get("/{item_id}", response_model=read_schema)  # type: ignore[valid-type]
    def get_item(
        item_id: int,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> ResourceT:
        item = db.get(model, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found")
        PermissionService(db).assert_object_access(user, element_name, PermissionAction.READ, item.owner_id)
        return item

    @router.post("", response_model=read_schema, status_code=status.HTTP_201_CREATED)  # type: ignore[valid-type]
    def create_item(
        payload: create_schema,  # type: ignore[valid-type]
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> ResourceT:
        PermissionService(db).assert_create(user, element_name)
        item = model(**payload.model_dump(), owner_id=user.id)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @router.patch("/{item_id}", response_model=read_schema)  # type: ignore[valid-type]
    def update_item(
        item_id: int,
        payload: update_schema,  # type: ignore[valid-type]
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> ResourceT:
        item = db.get(model, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found")
        PermissionService(db).assert_object_access(
            user, element_name, PermissionAction.UPDATE, item.owner_id
        )
        data: dict[str, Any] = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(item, field, value)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @router.delete("/{item_id}", response_model=Message)
    def delete_item(
        item_id: int,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Message:
        item = db.get(model, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found")
        PermissionService(db).assert_object_access(
            user, element_name, PermissionAction.DELETE, item.owner_id
        )
        db.delete(item)
        db.commit()
        return Message(detail=f"{tag.title()} item deleted")

    return router


products_router = build_resource_router(
    prefix="/products",
    tag="products",
    model=Product,
    element_name="products",
    create_schema=ProductCreate,
    update_schema=ProductUpdate,
    read_schema=ProductRead,
)
orders_router = build_resource_router(
    prefix="/orders",
    tag="orders",
    model=Order,
    element_name="orders",
    create_schema=OrderCreate,
    update_schema=OrderUpdate,
    read_schema=OrderRead,
)
stores_router = build_resource_router(
    prefix="/stores",
    tag="stores",
    model=Store,
    element_name="stores",
    create_schema=StoreCreate,
    update_schema=StoreUpdate,
    read_schema=StoreRead,
)
