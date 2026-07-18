"""Shared pytest fixtures."""

import pytest

from app import create_app
from app.extensions import db

TEST_USERNAME = "tester"
TEST_PASSWORD = "S3curePass!x"


@pytest.fixture()
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def register_and_login(client, username=TEST_USERNAME, password=TEST_PASSWORD):
    """Register a user and return (access_headers, refresh_token)."""
    client.post("/api/auth/register", json={"username": username, "password": password})
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    data = response.get_json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    return headers, data["refresh_token"]


@pytest.fixture()
def auth_headers(client):
    headers, _ = register_and_login(client)
    return headers
