"""
Tests for Veritas Phase 8 Error Handling

Tests for error_handler.py, custom exceptions, and structured error responses.
"""

import pytest
from datetime import datetime

from app.error_handler import (
    VeritasError,
    InvalidPayloadError,
    ToolExecutionError,
    MemoryAccessError,
    RAGSafetyError,
    RateLimitError,
    PayloadSizeError,
    FeatureDisabledError,
    build_error_response,
    log_error,
)


class TestCustomExceptions:
    """Tests for custom exception classes."""

    def test_veritas_error_basic(self):
        """Test VeritasError with basic message."""
        error = VeritasError("Test error")
        assert error.message == "Test error"
        assert error.code == "VERITAS_ERROR"
        assert error.details == {}
        assert error.timestamp is not None

    def test_veritas_error_with_details(self):
        """Test VeritasError with details."""
        error = VeritasError("Test error", code="TEST_CODE", details={"key": "value"})
        assert error.code == "TEST_CODE"
        assert error.details["key"] == "value"

    def test_invalid_payload_error(self):
        """Test InvalidPayloadError."""
        error = InvalidPayloadError("Invalid payload")
        assert error.code == "INVALID_PAYLOAD"
        assert str(error) == "Invalid payload"

    def test_tool_execution_error(self):
        """Test ToolExecutionError."""
        error = ToolExecutionError("Tool failed", tool_name="test_tool")
        assert error.code == "TOOL_EXECUTION_ERROR"
        assert error.details["tool_name"] == "test_tool"

    def test_memory_access_error(self):
        """Test MemoryAccessError."""
        error = MemoryAccessError("Memory access failed")
        assert error.code == "MEMORY_ACCESS_ERROR"

    def test_rag_safety_error(self):
        """Test RAGSafetyError."""
        error = RAGSafetyError("Unsafe query detected")
        assert error.code == "RAG_SAFETY_ERROR"

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError("Rate limit exceeded", limit=20, window_seconds=60)
        assert error.code == "RATE_LIMIT_EXCEEDED"
        assert error.details["limit"] == 20
        assert error.details["window_seconds"] == 60

    def test_payload_size_error(self):
        """Test PayloadSizeError."""
        error = PayloadSizeError("Payload too large", max_kb=64, actual_kb=100.5)
        assert error.code == "PAYLOAD_TOO_LARGE"
        assert error.details["max_kb"] == 64
        assert error.details["actual_kb"] == 100.5

    def test_feature_disabled_error(self):
        """Test FeatureDisabledError."""
        error = FeatureDisabledError("Feature disabled", feature="monitoring")
        assert error.code == "FEATURE_DISABLED"
        assert error.details["feature"] == "monitoring"


class TestBuildErrorResponse:
    """Tests for build_error_response function."""

    def test_veritas_error_response(self):
        """Test response for VeritasError."""
        error = VeritasError("Test error", code="TEST_CODE")
        response = build_error_response(error, status_code=500)

        assert response["ok"] == False
        assert response["error"]["code"] == "TEST_CODE"
        assert response["error"]["message"] == "Test error"
        assert "timestamp" in response["error"]

    def test_generic_error_response(self):
        """Test response for generic Exception."""
        error = Exception("Something went wrong")
        response = build_error_response(error, status_code=500)

        assert response["ok"] == False
        assert response["error"]["code"] == "INTERNAL_ERROR"
        assert response["error"]["message"] == "An internal error occurred"

    def test_response_includes_request_path(self):
        """Test that response includes request path."""
        error = VeritasError("Test error")
        response = build_error_response(error, status_code=500, request_path="/test")

        assert response["request_path"] == "/test"


class TestLogError:
    """Tests for log_error function."""

    def test_log_error_does_not_raise(self):
        """Test that log_error doesn't raise exceptions."""
        error = VeritasError("Test error")
        # Should not raise
        log_error(error, request_path="/test", additional_context={"key": "value"})

    def test_log_error_with_generic_exception(self):
        """Test log_error with generic exception."""
        error = Exception("Generic error")
        # Should not raise
        log_error(error)
