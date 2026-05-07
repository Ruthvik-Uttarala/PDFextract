from __future__ import annotations

from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Any


class BackendError(Exception):
    """Base class for recoverable backend errors."""


@dataclass
class ApiError(BackendError):
    code: str
    message: str
    status_code: int = HTTPStatus.BAD_REQUEST
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, correlation_id: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "error": {
                "code": self.code,
                "message": self.message,
                "correlation_id": correlation_id,
            }
        }
        if self.details:
            payload["error"]["details"] = self.details
        return payload


class ConfigurationError(BackendError):
    """Raised when environment configuration is incomplete or invalid."""


class DependencyError(BackendError):
    """Raised when a required external dependency is unavailable."""


class AuthenticationError(BackendError):
    """Raised when Firebase authentication fails."""


class AuthorizationError(BackendError):
    """Raised when the authenticated user is not permitted to access a resource."""
