from fastapi.testclient import TestClient

from tests.conftest import login


def test_register_login_and_me(client: TestClient) -> None:
    register = client.post(
        "/auth/register",
        json={
            "first_name": "New",
            "last_name": "Person",
            "middle_name": None,
            "email": "new@example.com",
            "password": "Password123!",
            "password_repeat": "Password123!",
        },
    )
    assert register.status_code == 201

    token = login(client, "new@example.com", "Password123!")
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "new@example.com"


def test_logout_blacklists_token(client: TestClient) -> None:
    token = login(client, "user@example.com", "User123!")

    logout = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout.status_code == 200

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 401


def test_soft_deleted_user_cannot_login_again(client: TestClient) -> None:
    token = login(client, "user@example.com", "User123!")

    deleted = client.delete("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert deleted.status_code == 200

    login_again = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "User123!"},
    )
    assert login_again.status_code == 401
