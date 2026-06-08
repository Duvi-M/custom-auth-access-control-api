from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.security import hash_password
from app.db.base import Base
from app.main import app
from app.models.auth import AccessRule, BusinessElement, Role, User
from app.models.resources import Product


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    with TestingSessionLocal() as session:
        seed_test_data(session)
        yield session

    Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def seed_test_data(db: Session) -> None:
    admin_role = Role(name="admin")
    manager_role = Role(name="manager")
    user_role = Role(name="user")
    guest_role = Role(name="guest")
    db.add_all([admin_role, manager_role, user_role, guest_role])
    db.flush()

    products = BusinessElement(name="products")
    users = BusinessElement(name="users")
    access_rules = BusinessElement(name="access_rules")
    db.add_all([products, users, access_rules])
    db.flush()

    for element in (products, users, access_rules):
        db.add(
            AccessRule(
                role_id=admin_role.id,
                element_id=element.id,
                read_permission=True,
                read_all_permission=True,
                create_permission=True,
                update_permission=True,
                update_all_permission=True,
                delete_permission=True,
                delete_all_permission=True,
            )
        )

    db.add(
        AccessRule(
            role_id=manager_role.id,
            element_id=products.id,
            read_permission=True,
            read_all_permission=True,
            create_permission=True,
            update_permission=True,
            delete_permission=True,
        )
    )
    db.add(
        AccessRule(
            role_id=user_role.id,
            element_id=products.id,
            read_permission=True,
            create_permission=True,
            update_permission=True,
            delete_permission=True,
        )
    )

    admin = User(
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        hashed_password=hash_password("Admin123!"),
        role_id=admin_role.id,
    )
    manager = User(
        first_name="Manager",
        last_name="User",
        email="manager@example.com",
        hashed_password=hash_password("Manager123!"),
        role_id=manager_role.id,
    )
    user = User(
        first_name="Regular",
        last_name="User",
        email="user@example.com",
        hashed_password=hash_password("User123!"),
        role_id=user_role.id,
    )
    guest = User(
        first_name="Guest",
        last_name="User",
        email="guest@example.com",
        hashed_password=hash_password("Guest123!"),
        role_id=guest_role.id,
    )
    db.add_all([admin, manager, user, guest])
    db.flush()

    db.add_all(
        [
            Product(owner_id=admin.id, name="Admin product", price=10, stock=1),
            Product(owner_id=user.id, name="User product", price=20, stock=2),
        ]
    )
    db.commit()


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def product_id_by_name(db: Session, name: str) -> int:
    return db.scalar(select(Product.id).where(Product.name == name))


def role_id_by_name(db: Session, name: str) -> int:
    return db.scalar(select(Role.id).where(Role.name == name))


def element_id_by_name(db: Session, name: str) -> int:
    return db.scalar(select(BusinessElement.id).where(BusinessElement.name == name))


def first_access_rule_id(db: Session) -> int:
    return db.scalar(select(AccessRule.id).order_by(AccessRule.id))
