"""
Veritas Error Handler

Phase 8: Centralized exception handling for production hardening.

This module provides:
- Custom exception classes for different error types
- Global FastAPI exception handlers
- Structured JSON error responses
- Error logging to logs/ folder

IMPORTANT: Veritas monitors only — never intervenes or takes autonomous actions.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from logging.handlers import RotatingFileHandler


# Configure error logger
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

error_logger = logging.getLogger("veritas.errors")
error_logger.setLevel(logging.ERROR)

if not error_logger.handlers:
    handler = RotatingFileHandler(
        LOG_DIR / "veritas_errors.log",
        maxBytes=5_000_000,
        backupCount=5
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    error_logger.addHandler(handler)


# ============================================================================
# Custom Exception Classes
# ============================================================================


class VeritasError(Exception):
    """Base exception for all Veritas errors."""

    def __init__(self, message: str, code: str = "VERITAS_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()


class InvalidPayloadError(VeritasError):
    """Raised when request payload is invalid or malformed."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="INVALID_PAYLOAD", details=details)


class ToolExecutionError(VeritasError):
    """Raised when a tool fails to execute properly."""

    def __init__(self, message: str, tool_name: str = "unknown", details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details["tool_name"] = tool_name
        super().__init__(message, code="TOOL_EXECUTION_ERROR", details=details)


class MemoryAccessError(VeritasError):
    """Raised when memory/storage operations fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="MEMORY_ACCESS_ERROR", details=details)


class RAGSafetyError(VeritasError):
    """Raised when RAG query appears unsafe or malicious."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="RAG_SAFETY_ERROR", details=details)


class RateLimitError(VeritasError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, limit: int = 0, window_seconds: int = 60, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details["limit"] = limit
        details["window_seconds"] = window_seconds
        super().__init__(message, code="RATE_LIMIT_EXCEEDED", details=details)


class PayloadSizeError(VeritasError):
    """Raised when payload exceeds size limit."""

    def __init__(self, message: str, max_kb: int = 0, actual_kb: float = 0, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details["max_kb"] = max_kb
        details["actual_kb"] = actual_kb
        super().__init__(message, code="PAYLOAD_TOO_LARGE", details=details)


class FeatureDisabledError(VeritasError):
    """Raised when a feature is disabled via config."""

    def __init__(self, message: str, feature: str = "", details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details["feature"] = feature
        super().__init__(message, code="FEATURE_DISABLED", details=details)


# ============================================================================
# Error Response Builder
# ============================================================================


def build_error_response(
    error: Exception,
    status_code: int = 500,
    request_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build a structured error response.

    Never exposes stack traces or internal details.

    Args:
        error: The exception that occurred.
        status_code: HTTP status code.
        request_path: Optional request path for context.

    Returns:
        Structured error response dictionary.
    """
    if isinstance(error, VeritasError):
        return {
            "ok": False,
            "error": {
                "code": error.code,
                "message": error.message,
                "timestamp": error.timestamp,
            },
            "request_path": request_path,
        }

    # Generic error - don't expose details
    return {
        "ok": False,
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An internal error occurred",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "request_path": request_path,
    }


def log_error(
    error: Exception,
    request_path: Optional[str] = None,
    additional_context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log error to structured JSON log file.

    Args:
        error: The exception to log.
        request_path: Optional request path.
        additional_context: Additional context to include.
    """
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "error_type": type(error).__name__,
        "message": str(error),
        "request_path": request_path,
    }

    if isinstance(error, VeritasError):
        log_entry["code"] = error.code
        log_entry["details"] = error.details

    if additional_context:
        log_entry["context"] = additional_context

    error_logger.error(json.dumps(log_entry))


# ============================================================================
# FastAPI Exception Handlers
# ============================================================================


async def veritas_error_handler(request: Request, exc: VeritasError) -> JSONResponse:
    """Handle VeritasError exceptions."""
    log_error(exc, request_path=str(request.url.path))

    # Determine status code based on error type
    status_code = 500
    if isinstance(exc, InvalidPayloadError):
        status_code = 400
    elif isinstance(exc, RateLimitError):
        status_code = 429
    elif isinstance(exc, PayloadSizeError):
        status_code = 413
    elif isinstance(exc, FeatureDisabledError):
        status_code = 503
    elif isinstance(exc, RAGSafetyError):
        status_code = 400

    return JSONResponse(
        status_code=status_code,
        content=build_error_response(exc, status_code, str(request.url.path))
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions."""
    log_error(exc, request_path=str(request.url.path))

    return JSONResponse(
        status_code=500,
        content=build_error_response(exc, 500, str(request.url.path))
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register global FastAPI exception handlers.

    - Returns structured JSON for all errors
    - Never exposes stack traces
    - Logs errors to logs/ folder

    Args:
        app: FastAPI application instance.
    """
    app.add_exception_handler(VeritasError, veritas_error_handler)
    app.add_exception_handler(InvalidPayloadError, veritas_error_handler)
    app.add_exception_handler(ToolExecutionError, veritas_error_handler)
    app.add_exception_handler(MemoryAccessError, veritas_error_handler)
    app.add_exception_handler(RAGSafetyError, veritas_error_handler)
    app.add_exception_handler(RateLimitError, veritas_error_handler)
    app.add_exception_handler(PayloadSizeError, veritas_error_handler)
    app.add_exception_handler(FeatureDisabledError, veritas_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)
