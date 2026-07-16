from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Note

api_bp = Blueprint("api", __name__, url_prefix="/api")
health_bp = Blueprint("health", __name__)

MAX_TITLE_LENGTH = 120
MAX_CONTENT_LENGTH = 10_000


def _current_user_id() -> int:
    return int(get_jwt_identity())


def _validate_note_payload(payload: dict | None, require_title: bool = True):
    """Return (title, content, error_response)."""
    payload = payload or {}
    title = payload.get("title")
    content = payload.get("content", "")

    if title is not None:
        title = str(title).strip()
    if require_title and not title:
        return None, None, (jsonify(error="Field 'title' is required."), 400)
    if title is not None and len(title) > MAX_TITLE_LENGTH:
        return (
            None,
            None,
            (
                jsonify(error=f"Title exceeds {MAX_TITLE_LENGTH} characters."),
                400,
            ),
        )

    content = str(content)
    if len(content) > MAX_CONTENT_LENGTH:
        return (
            None,
            None,
            (
                jsonify(error=f"Content exceeds {MAX_CONTENT_LENGTH} characters."),
                400,
            ),
        )

    return title, content, None


def _get_owned_note(note_id: int) -> Note | None:
    return Note.query.filter_by(id=note_id, user_id=_current_user_id()).first()


@api_bp.get("/notes")
@jwt_required()
def list_notes():
    notes = Note.query.filter_by(user_id=_current_user_id()).order_by(Note.created_at.desc()).all()
    return jsonify([note.to_dict() for note in notes])


@api_bp.post("/notes")
@jwt_required()
def create_note():
    title, content, error = _validate_note_payload(request.get_json(silent=True))
    if error:
        return error

    note = Note(user_id=_current_user_id(), title=title, content=content)
    db.session.add(note)
    db.session.commit()
    return jsonify(note.to_dict()), 201


@api_bp.get("/notes/<int:note_id>")
@jwt_required()
def get_note(note_id: int):
    note = _get_owned_note(note_id)
    if note is None:
        return jsonify(error="Note not found."), 404
    return jsonify(note.to_dict())


@api_bp.put("/notes/<int:note_id>")
@jwt_required()
def update_note(note_id: int):
    note = _get_owned_note(note_id)
    if note is None:
        return jsonify(error="Note not found."), 404

    payload = request.get_json(silent=True) or {}
    title, content, error = _validate_note_payload(payload, require_title=False)
    if error:
        return error

    if title:
        note.title = title
    if "content" in payload:
        note.content = content
    db.session.commit()
    return jsonify(note.to_dict())


@api_bp.delete("/notes/<int:note_id>")
@jwt_required()
def delete_note(note_id: int):
    note = _get_owned_note(note_id)
    if note is None:
        return jsonify(error="Note not found."), 404

    db.session.delete(note)
    db.session.commit()
    return jsonify(message="Note deleted.")


@health_bp.get("/health")
def health():
    return jsonify(status="ok")


@api_bp.get("/version")
def version():
    return jsonify(version=current_app.config["APP_VERSION"])
