import re

import bcrypt
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)

from app.extensions import db
from app.models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,80}$")
MIN_PASSWORD_LENGTH = 8


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _extract_credentials(payload: dict | None) -> tuple[str, str]:
    payload = payload or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    return username, password


@auth_bp.post("/register")
def register():
    username, password = _extract_credentials(request.get_json(silent=True))

    if not USERNAME_RE.match(username):
        return (
            jsonify(error="Username must be 3-80 chars: letters, digits, underscore."),
            400,
        )
    if len(password) < MIN_PASSWORD_LENGTH:
        return (
            jsonify(error=f"Password must be at least {MIN_PASSWORD_LENGTH} characters."),
            400,
        )
    if User.query.filter_by(username=username).first():
        return jsonify(error="Username already taken."), 409

    user = User(username=username, password_hash=hash_password(password))
    db.session.add(user)
    db.session.commit()

    return (
        jsonify(
            message="Account created.",
            access_token=create_access_token(identity=str(user.id)),
            refresh_token=create_refresh_token(identity=str(user.id)),
        ),
        201,
    )


@auth_bp.post("/login")
def login():
    username, password = _extract_credentials(request.get_json(silent=True))

    user = User.query.filter_by(username=username).first()
    # Single generic error for both unknown user and bad password
    # (prevents username enumeration).
    if user is None or not verify_password(password, user.password_hash):
        return jsonify(error="Invalid credentials."), 401

    return jsonify(
        access_token=create_access_token(identity=str(user.id)),
        refresh_token=create_refresh_token(identity=str(user.id)),
    )


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    return jsonify(access_token=create_access_token(identity=identity))
