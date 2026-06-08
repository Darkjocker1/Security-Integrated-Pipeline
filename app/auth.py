import bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token
from app.extensions import db
from app.models import User


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(plain_password: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed.encode("utf-8"))


def register_user(username: str, email: str, password: str):
    if User.query.filter_by(username=username).first():
        return None, "Username already taken"
    if User.query.filter_by(email=email).first():
        return None, "Email already registered"

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
    )
    db.session.add(user)
    db.session.commit()
    return user, None


def login_user(username: str, password: str):
    user = User.query.filter_by(username=username).first()
    if not user or not check_password(password, user.password_hash):
        return None, None, "Invalid username or password"

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    return access_token, refresh_token, None
