from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.auth import AccessRule, BusinessElement, Role, User
from app.models.resources import Order, Product, Store

ROLE_NAMES = ("admin", "manager", "user", "guest")
ELEMENT_NAMES = ("users", "products", "orders", "stores", "access_rules")


def get_or_create_role(db: Session, name: str) -> Role:
    role = db.scalar(select(Role).where(Role.name == name))
    if role is None:
        role = Role(name=name, description=f"{name.title()} role")
        db.add(role)
        db.flush()
    return role


def get_or_create_element(db: Session, name: str) -> BusinessElement:
    element = db.scalar(select(BusinessElement).where(BusinessElement.name == name))
    if element is None:
        element = BusinessElement(name=name, description=f"{name.replace('_', ' ').title()} element")
        db.add(element)
        db.flush()
    return element


def upsert_user(
    db: Session,
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: Role,
) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None:
        user = User(
            email=email.lower(),
            first_name=first_name,
            last_name=last_name,
            middle_name=None,
            hashed_password=hash_password(password),
            is_active=True,
            role_id=role.id,
        )
        db.add(user)
    else:
        user.role_id = role.id
        user.is_active = True
    db.flush()
    return user


def upsert_rule(db: Session, role: Role, element: BusinessElement, **permissions: bool) -> None:
    rule = db.scalar(
        select(AccessRule).where(AccessRule.role_id == role.id, AccessRule.element_id == element.id)
    )
    if rule is None:
        rule = AccessRule(role_id=role.id, element_id=element.id)
        db.add(rule)
    for field in (
        "read_permission",
        "read_all_permission",
        "create_permission",
        "update_permission",
        "update_all_permission",
        "delete_permission",
        "delete_all_permission",
    ):
        setattr(rule, field, permissions.get(field, False))


def seed_access_rules(
    db: Session,
    roles: dict[str, Role],
    elements: dict[str, BusinessElement],
) -> None:
    for element in elements.values():
        upsert_rule(
            db,
            roles["admin"],
            element,
            read_permission=True,
            read_all_permission=True,
            create_permission=True,
            update_permission=True,
            update_all_permission=True,
            delete_permission=True,
            delete_all_permission=True,
        )

    for name in ("products", "orders", "stores"):
        upsert_rule(
            db,
            roles["manager"],
            elements[name],
            read_permission=True,
            read_all_permission=True,
            create_permission=True,
            update_permission=True,
            delete_permission=True,
        )
        upsert_rule(
            db,
            roles["user"],
            elements[name],
            read_permission=True,
            create_permission=True,
            update_permission=True,
            delete_permission=True,
        )

    upsert_rule(db, roles["manager"], elements["users"], read_permission=True)
    upsert_rule(db, roles["guest"], elements["products"], read_permission=True)


def create_samples(db: Session, admin: User, manager: User, regular_user: User) -> None:
    samples = [
        Product(
            owner_id=admin.id,
            name="Admin laptop",
            description="Seed product owned by admin",
            price=Decimal("1499.00"),
            stock=5,
        ),
        Product(
            owner_id=regular_user.id,
            name="User keyboard",
            description="Seed product owned by regular user",
            price=Decimal("99.00"),
            stock=12,
        ),
        Order(
            owner_id=manager.id,
            name="Manager sample order",
            description="Seed order owned by manager",
            total_amount=Decimal("250.00"),
            status="paid",
        ),
        Order(
            owner_id=regular_user.id,
            name="User sample order",
            description="Seed order owned by regular user",
            total_amount=Decimal("75.50"),
            status="new",
        ),
        Store(
            owner_id=manager.id,
            name="Manager downtown store",
            description="Seed store owned by manager",
            address="100 Main Street",
        ),
        Store(
            owner_id=regular_user.id,
            name="User pop-up store",
            description="Seed store owned by regular user",
            address="200 Market Street",
        ),
    ]

    for sample in samples:
        exists = db.scalar(select(type(sample)).where(type(sample).name == sample.name))
        if exists is None:
            db.add(sample)


def main() -> None:
    settings = get_settings()
    with SessionLocal() as db:
        roles = {name: get_or_create_role(db, name) for name in ROLE_NAMES}
        elements = {name: get_or_create_element(db, name) for name in ELEMENT_NAMES}

        admin = upsert_user(
            db,
            email=settings.admin_email,
            password=settings.admin_password,
            first_name="Admin",
            last_name="User",
            role=roles["admin"],
        )
        manager = upsert_user(
            db,
            email=settings.manager_email,
            password=settings.manager_password,
            first_name="Manager",
            last_name="User",
            role=roles["manager"],
        )
        regular_user = upsert_user(
            db,
            email=settings.user_email,
            password=settings.user_password,
            first_name="Regular",
            last_name="User",
            role=roles["user"],
        )

        seed_access_rules(db, roles, elements)
        create_samples(db, admin, manager, regular_user)
        db.commit()

    print("Seed data created or updated.")
    print("Seed credentials and roles:")
    print(f"- {settings.admin_email} / {settings.admin_password} -> admin")
    print(f"- {settings.manager_email} / {settings.manager_password} -> manager")
    print(f"- {settings.user_email} / {settings.user_password} -> user")


if __name__ == "__main__":
    main()