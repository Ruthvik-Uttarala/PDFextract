from __future__ import annotations

from flask import Flask

from app.api.routes import auth_blueprint, health_blueprint
from app.core.config import Settings, get_settings


def create_app(settings: Settings | None = None, testing: bool = False) -> Flask:
    app = Flask(__name__)
    app.config["TESTING"] = testing
    app.extensions["pdfextract_settings"] = settings or get_settings()
    app.register_blueprint(health_blueprint)
    app.register_blueprint(auth_blueprint)
    return app


app = create_app()
