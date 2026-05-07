from __future__ import annotations

from http import HTTPStatus
from uuid import uuid4

from flask import Flask, Response, g, jsonify, request
from sqlalchemy.orm import Session

from app.api.request_context import get_correlation_id
from app.api.routes import (
    admin_blueprint,
    auth_blueprint,
    health_blueprint,
    jobs_blueprint,
    uploads_blueprint,
)
from app.core import FailureCode, Settings, configure_logging, get_logger, get_settings
from app.core.errors import ApiError
from app.db import create_session


def create_app(settings: Settings | None = None, testing: bool = False) -> Flask:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)

    app = Flask(__name__)
    app.config["TESTING"] = testing
    app.extensions["pdfextract_settings"] = resolved_settings

    _register_request_lifecycle(app, resolved_settings)
    _register_error_handlers(app)

    app.register_blueprint(health_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(uploads_blueprint)
    app.register_blueprint(jobs_blueprint)
    app.register_blueprint(admin_blueprint)
    return app


def _register_request_lifecycle(app: Flask, settings: Settings) -> None:
    logger = get_logger("pdfextract.request")

    @app.before_request
    def before_request() -> None:
        g.settings = settings
        g.correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        g.db_session = create_session(settings)
        logger.info(
            "request_started",
            extra={
                "context": {
                    "correlation_id": g.correlation_id,
                    "method": request.method,
                    "path": request.path,
                }
            },
        )

    @app.after_request
    def after_request(response: Response) -> Response:
        _apply_cors_headers(response, settings)
        response.headers["X-Correlation-ID"] = get_correlation_id()
        logger.info(
            "request_finished",
            extra={
                "context": {
                    "correlation_id": get_correlation_id(),
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                }
            },
        )
        return response

    @app.teardown_request
    def teardown_request(_exception: BaseException | None) -> None:
        session = getattr(g, "db_session", None)
        if not isinstance(session, Session):
            return

        if session.in_transaction():
            session.rollback()
        session.close()


def _register_error_handlers(app: Flask) -> None:
    logger = get_logger("pdfextract.errors")

    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):  # type: ignore[no-untyped-def]
        logger.warning(
            "api_error",
            extra={
                "context": {
                    "correlation_id": get_correlation_id(),
                    "error_code": error.code,
                    "status_code": error.status_code,
                }
            },
        )
        return jsonify(error.to_dict(get_correlation_id())), error.status_code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):  # type: ignore[no-untyped-def]
        logger.exception(
            "unexpected_error",
            extra={"context": {"correlation_id": get_correlation_id()}},
        )
        api_error = ApiError(
            code=FailureCode.INTERNAL_ERROR,
            message="An unexpected backend error occurred.",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
        return jsonify(api_error.to_dict(get_correlation_id())), api_error.status_code


def _apply_cors_headers(response: Response, settings: Settings) -> None:
    request_origin = request.headers.get("Origin", "").strip()
    if not request_origin:
        return

    allowed_origins = settings.allowed_cors_origins
    if "*" not in allowed_origins and request_origin not in allowed_origins:
        return

    response.headers["Access-Control-Allow-Origin"] = (
        request_origin if "*" not in allowed_origins else "*"
    )
    response.headers["Access-Control-Allow-Headers"] = (
        "Authorization, Content-Type, X-Correlation-ID"
    )
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Vary"] = "Origin"


app = create_app()
