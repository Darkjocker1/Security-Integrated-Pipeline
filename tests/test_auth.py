"""Tests for registration, login, and token refresh."""

from tests.conftest import TEST_PASSWORD, TEST_USERNAME, register_and_login


def test_register_success(client):
    response = client.post(
        "/api/auth/register",
        json={"username": "newuser", "password": "averylongpassword"},
    )
    assert response.status_code == 201
    data = response.get_json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_register_duplicate_username(client):
    payload = {"username": "dupe", "password": "averylongpassword"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 409


def test_register_rejects_short_password(client):
    response = client.post("/api/auth/register", json={"username": "shorty", "password": "short"})
    assert response.status_code == 400


def test_register_rejects_invalid_username(client):
    response = client.post(
        "/api/auth/register",
        json={"username": "bad name!", "password": "averylongpassword"},
    )
    assert response.status_code == 400


def test_login_success(client):
    client.post(
        "/api/auth/register",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    response = client.post(
        "/api/auth/login",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    assert "access_token" in response.get_json()


def test_login_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    response = client.post(
        "/api/auth/login",
        json={"username": TEST_USERNAME, "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_login_unknown_user_same_error_as_wrong_password(client):
    """Both failure modes must return an identical generic error."""
    response = client.post(
        "/api/auth/login",
        json={"username": "ghost", "password": "whatever123"},
    )
    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid credentials."


def test_refresh_token_issues_new_access_token(client):
    _, refresh_token = register_and_login(client)
    response = client.post(
        "/api/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert response.status_code == 200
    assert "access_token" in response.get_json()


def test_refresh_rejects_access_token(client):
    headers, _ = register_and_login(client)
    response = client.post("/api/auth/refresh", headers=headers)
    assert response.status_code == 422
