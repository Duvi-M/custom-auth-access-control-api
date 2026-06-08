from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.auth import AccessRule, BusinessElement, Role, User
from app.schemas.admin import (
    AccessRuleCreate,
    AccessRuleRead,
    AccessRuleUpdate,
    BusinessElementCreate,
    BusinessElementRead,
    BusinessElementUpdate,
    RoleCreate,
    RoleRead,
    RoleUpdate,
)
from app.schemas.auth import UserRead
from app.schemas.common import Message

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _get_or_404(db: Session, model: type, item_id: int):
    obj = db.get(model, item_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found")
    return obj


def _commit_or_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Object with these unique fields already exists",
        ) from None


@router.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)).all())


@router.post("/roles", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
def create_role(payload: RoleCreate, db: Session = Depends(get_db)) -> Role:
    role = Role(**payload.model_dump())
    db.add(role)
    _commit_or_conflict(db)
    db.refresh(role)
    return role


@router.get("/roles", response_model=list[RoleRead])
def list_roles(db: Session = Depends(get_db)) -> list[Role]:
    return list(db.scalars(select(Role).order_by(Role.id)).all())


@router.get("/roles/{role_id}", response_model=RoleRead)
def get_role(role_id: int, db: Session = Depends(get_db)) -> Role:
    return _get_or_404(db, Role, role_id)


@router.patch("/roles/{role_id}", response_model=RoleRead)
def update_role(role_id: int, payload: RoleUpdate, db: Session = Depends(get_db)) -> Role:
    role = _get_or_404(db, Role, role_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(role, field, value)
    db.add(role)
    _commit_or_conflict(db)
    db.refresh(role)
    return role


@router.delete("/roles/{role_id}", response_model=Message)
def delete_role(role_id: int, db: Session = Depends(get_db)) -> Message:
    role = _get_or_404(db, Role, role_id)
    db.delete(role)
    db.commit()
    return Message(detail="Role deleted")


@router.post(
    "/business-elements",
    response_model=BusinessElementRead,
    status_code=status.HTTP_201_CREATED,
)
def create_business_element(
    payload: BusinessElementCreate, db: Session = Depends(get_db)
) -> BusinessElement:
    element = BusinessElement(**payload.model_dump())
    db.add(element)
    _commit_or_conflict(db)
    db.refresh(element)
    return element


@router.get("/business-elements", response_model=list[BusinessElementRead])
def list_business_elements(db: Session = Depends(get_db)) -> list[BusinessElement]:
    return list(db.scalars(select(BusinessElement).order_by(BusinessElement.id)).all())


@router.get("/business-elements/{element_id}", response_model=BusinessElementRead)
def get_business_element(element_id: int, db: Session = Depends(get_db)) -> BusinessElement:
    return _get_or_404(db, BusinessElement, element_id)


@router.patch("/business-elements/{element_id}", response_model=BusinessElementRead)
def update_business_element(
    element_id: int,
    payload: BusinessElementUpdate,
    db: Session = Depends(get_db),
) -> BusinessElement:
    element = _get_or_404(db, BusinessElement, element_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(element, field, value)
    db.add(element)
    _commit_or_conflict(db)
    db.refresh(element)
    return element


@router.delete("/business-elements/{element_id}", response_model=Message)
def delete_business_element(element_id: int, db: Session = Depends(get_db)) -> Message:
    element = _get_or_404(db, BusinessElement, element_id)
    db.delete(element)
    db.commit()
    return Message(detail="Business element deleted")


@router.post("/access-rules", response_model=AccessRuleRead, status_code=status.HTTP_201_CREATED)
def create_access_rule(payload: AccessRuleCreate, db: Session = Depends(get_db)) -> AccessRule:
    rule = AccessRule(**payload.model_dump())
    db.add(rule)
    _commit_or_conflict(db)
    db.refresh(rule)
    return rule


@router.get("/access-rules", response_model=list[AccessRuleRead])
def list_access_rules(db: Session = Depends(get_db)) -> list[AccessRule]:
    return list(db.scalars(select(AccessRule).order_by(AccessRule.id)).all())


@router.get("/access-rules/{rule_id}", response_model=AccessRuleRead)
def get_access_rule(rule_id: int, db: Session = Depends(get_db)) -> AccessRule:
    return _get_or_404(db, AccessRule, rule_id)


@router.patch("/access-rules/{rule_id}", response_model=AccessRuleRead)
def update_access_rule(
    rule_id: int,
    payload: AccessRuleUpdate,
    db: Session = Depends(get_db),
) -> AccessRule:
    rule = _get_or_404(db, AccessRule, rule_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    db.add(rule)
    _commit_or_conflict(db)
    db.refresh(rule)
    return rule


@router.delete("/access-rules/{rule_id}", response_model=Message)
def delete_access_rule(rule_id: int, db: Session = Depends(get_db)) -> Message:
    rule = _get_or_404(db, AccessRule, rule_id)
    db.delete(rule)
    db.commit()
    return Message(detail="Access rule deleted")
