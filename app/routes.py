from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from app.extensions import db
from app.models import Note
from app.auth import register_user, login_user

api = Blueprint("api", __name__)


@api.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@api.route("/version")
def version():
    return jsonify({"version": "1.0.0"}), 200


# --- Auth ---

@api.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"error": "username, email, and password are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    user, error = register_user(username, email, password)
    if error:
        return jsonify({"error": error}), 409

    return jsonify({"message": "User created", "username": user.username}), 201


@api.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    access_token, refresh_token, error = login_user(username, password)
    if error:
        return jsonify({"error": error}), 401

    return jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200


@api.route("/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({"access_token": access_token}), 200


# --- Notes ---

@api.route("/notes", methods=["GET"])
@jwt_required()
def get_notes():
    user_id = int(get_jwt_identity())
    notes = Note.query.filter_by(user_id=user_id).all()
    return jsonify([
        {
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "created_at": n.created_at.isoformat(),
            "updated_at": n.updated_at.isoformat(),
        }
        for n in notes
    ]), 200


@api.route("/notes", methods=["POST"])
@jwt_required()
def create_note():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    note = Note(title=title, content=data.get("content", ""), user_id=user_id)
    db.session.add(note)
    db.session.commit()
    return jsonify({"id": note.id, "title": note.title}), 201


@api.route("/notes/<int:note_id>", methods=["GET"])
@jwt_required()
def get_note(note_id):
    user_id = int(get_jwt_identity())
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note:
        return jsonify({"error": "Note not found"}), 404

    return jsonify({
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "created_at": note.created_at.isoformat(),
        "updated_at": note.updated_at.isoformat(),
    }), 200


@api.route("/notes/<int:note_id>", methods=["PUT"])
@jwt_required()
def update_note(note_id):
    user_id = int(get_jwt_identity())
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note:
        return jsonify({"error": "Note not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    if "title" in data:
        title = data["title"].strip()
        if not title:
            return jsonify({"error": "title cannot be empty"}), 400
        note.title = title

    if "content" in data:
        note.content = data["content"]

    db.session.commit()
    return jsonify({"id": note.id, "title": note.title}), 200


@api.route("/notes/<int:note_id>", methods=["DELETE"])
@jwt_required()
def delete_note(note_id):
    user_id = int(get_jwt_identity())
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if not note:
        return jsonify({"error": "Note not found"}), 404

    db.session.delete(note)
    db.session.commit()
    return jsonify({"message": "Note deleted"}), 200
