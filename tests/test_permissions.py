import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import login, product_id_by_name


def test_missing_token_returns_401(client: TestClient) -> None:
    response = client.get("/products")
    assert response.status_code == 401


def test_user_can_only_list_owned_products(client: TestClient) -> None:
    token = login(client, "user@example.com", "User123!")
    response = client.get("/products", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert names == {"User product"}


def test_user_cannot_update_someone_elses_product(
    client: TestClient,
    db_session: Session,
) -> None:
    token = login(client, "user@example.com", "User123!")
    admin_product_id = product_id_by_name(db_session, "Admin product")

    response = client.patch(
        f"/products/{admin_product_id}",
        json={"name": "Changed"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_manager_can_read_all_but_not_update_others(
    client: TestClient,
    db_session: Session,
) -> None:
    token = login(client, "manager@example.com", "Manager123!")

    listing = client.get("/products", headers={"Authorization": f"Bearer {token}"})
    assert listing.status_code == 200
    assert {item["name"] for item in listing.json()} == {"Admin product", "User product"}

    admin_product_id = product_id_by_name(db_session, "Admin product")
    update = client.patch(
        f"/products/{admin_product_id}",
        json={"name": "Manager changed"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update.status_code == 403


def test_admin_can_list_users(client: TestClient) -> None:
    token = login(client, "admin@example.com", "Admin123!")

    response = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) == 4


def test_regular_user_cannot_list_admin_users(client: TestClient) -> None:
    token = login(client, "user@example.com", "User123!")

    response = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_unauthenticated_user_cannot_list_admin_users(client: TestClient) -> None:
    response = client.get("/admin/users")
    assert response.status_code == 401


@pytest.mark.parametrize("email,password", [
    ("manager@example.com", "Manager123!"),
    ("user@example.com", "User123!"),
    ("guest@example.com", "Guest123!"),
])
@pytest.mark.parametrize("path", [
    "/admin/users",
    "/admin/roles",
    "/admin/business-elements",
    "/admin/access-rules",
])
def test_non_admin_roles_cannot_access_admin_routes(
    client: TestClient,
    email: str,
    password: str,
    path: str,
) -> None:
    token = login(client, email, password)

    response = client.get(path, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
