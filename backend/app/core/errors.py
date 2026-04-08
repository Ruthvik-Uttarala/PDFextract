from __future__ import annotations


class BackendError(Exception):
    """Base class for recoverable backend errors."""


class ConfigurationError(BackendError):
    """Raised when environment configuration is incomplete or invalid."""


class DependencyError(BackendError):
    """Raised when a required external dependency is unavailable."""


class AuthenticationError(BackendError):
    """Raised when Firebase authentication fails."""
