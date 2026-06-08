from enum import StrEnum

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.auth import AccessRule, BusinessElement, User


class PermissionAction(StrEnum):
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class PermissionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_rule(self, user: User, element_name: str) -> AccessRule | None:
        stmt = (
            select(AccessRule)
            .join(BusinessElement)
            .where(AccessRule.role_id == user.role_id, BusinessElement.name == element_name)
        )
        return self.db.scalar(stmt)

    def collection_scope(self, user: User, element_name: str) -> str:
        rule = self.get_rule(user, element_name)
        if rule is None or not (rule.read_permission or rule.read_all_permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Read permission denied")
        return "all" if rule.read_all_permission else "owned"

    def assert_create(self, user: User, element_name: str) -> None:
        rule = self.get_rule(user, element_name)
        if rule is None or not rule.create_permission:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Create permission denied")

    def assert_object_access(
        self,
        user: User,
        element_name: str,
        action: PermissionAction,
        owner_id: int,
    ) -> None:
        rule = self.get_rule(user, element_name)
        if rule is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

        basic_attr = f"{action.value}_permission"
        all_attr = f"{action.value}_all_permission"
        has_basic = bool(getattr(rule, basic_attr, False))
        has_all = bool(getattr(rule, all_attr, False))

        if has_all:
            return

        if has_basic and owner_id == user.id:
            return

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
