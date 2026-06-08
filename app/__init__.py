from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from app.config import get_config
from app.extensions import db, jwt


def create_app():
    app = Flask(__name__)
    app.config.from_object(get_config())

    db.init_app(app)
    jwt.init_app(app)

    with app.app_context():
        import app.models  # noqa: F401 — registers tables with SQLAlchemy
        from app.routes import api
        app.register_blueprint(api, url_prefix="/api")

    return app
