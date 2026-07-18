"""Tests for notes CRUD, tenant isolation, and utility endpoints."""

from tests.conftest import register_and_login


def _create_note(client, headers, title="First note", content="hello"):
    return client.post("/api/notes", json={"title": title, "content": content}, headers=headers)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_version_endpoint(client):
    response = client.get("/api/version")
    assert response.status_code == 200
    assert "version" in response.get_json()


def test_notes_require_authentication(client):
    assert client.get("/api/notes").status_code == 401
    assert client.post("/api/notes", json={"title": "x"}).status_code == 401


def test_create_and_list_notes(client, auth_headers):
    response = _create_note(client, auth_headers)
    assert response.status_code == 201
    note = response.get_json()
    assert note["title"] == "First note"

    response = client.get("/api/notes", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.get_json()) == 1


def test_create_note_requires_title(client, auth_headers):
    response = client.post("/api/notes", json={"content": "no title"}, headers=auth_headers)
    assert response.status_code == 400


def test_create_note_rejects_oversized_title(client, auth_headers):
    response = _create_note(client, auth_headers, title="x" * 500)
    assert response.status_code == 400


def test_get_update_delete_note(client, auth_headers):
    note_id = _create_note(client, auth_headers).get_json()["id"]

    response = client.get(f"/api/notes/{note_id}", headers=auth_headers)
    assert response.status_code == 200

    response = client.put(
        f"/api/notes/{note_id}",
        json={"title": "Updated", "content": "new body"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.get_json()["title"] == "Updated"

    response = client.delete(f"/api/notes/{note_id}", headers=auth_headers)
    assert response.status_code == 200
    assert client.get(f"/api/notes/{note_id}", headers=auth_headers).status_code == 404


def test_missing_note_returns_404(client, auth_headers):
    assert client.get("/api/notes/9999", headers=auth_headers).status_code == 404


def test_users_cannot_access_each_others_notes(client):
    """IDOR protection: notes are scoped to their owner."""
    headers_a, _ = register_and_login(client, username="alice")
    headers_b, _ = register_and_login(client, username="bob")

    note_id = _create_note(client, headers_a, title="Alice's note").get_json()["id"]

    assert client.get(f"/api/notes/{note_id}", headers=headers_b).status_code == 404
    assert client.delete(f"/api/notes/{note_id}", headers=headers_b).status_code == 404
    # Owner still has access
    assert client.get(f"/api/notes/{note_id}", headers=headers_a).status_code == 200
