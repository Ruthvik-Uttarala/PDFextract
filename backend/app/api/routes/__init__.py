from .admin_routes import admin_blueprint
from .auth_routes import auth_blueprint
from .health_routes import health_blueprint
from .jobs_routes import jobs_blueprint
from .uploads_routes import uploads_blueprint

__all__ = [
    "admin_blueprint",
    "auth_blueprint",
    "health_blueprint",
    "jobs_blueprint",
    "uploads_blueprint",
]
