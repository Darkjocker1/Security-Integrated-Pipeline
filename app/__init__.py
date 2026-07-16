import os

from flask import Flask, jsonify

from app.config import get_config
from app.extensions import db, jwt


def create_app(config_name: str | None = None) -> Flask:
    config_name = config_name or os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    if config_name == "production":
        _require_production_secrets(app)

    db.init_app(app)
    jwt.init_app(app)

    _register_blueprints(app)
    _register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


def _require_production_secrets(app: Flask) -> None:
    missing = [
        key
        for key in ("SECRET_KEY", "JWT_SECRET_KEY", "SQLALCHEMY_DATABASE_URI")
        if not app.config.get(key)
    ]
    if missing:
        raise RuntimeError(
            "Missing required production settings (set via environment): " + ", ".join(missing)
        )


def _register_blueprints(app: Flask) -> None:
    from app.auth import auth_bp
    from app.routes import api_bp, health_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(health_bp)


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(_error):
        return jsonify(error="Resource not found."), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify(error="Method not allowed."), 405

    @app.errorhandler(500)
    def internal_error(_error):
        db.session.rollback()
        return jsonify(error="Internal server error."), 500
