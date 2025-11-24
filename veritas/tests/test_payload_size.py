"""
Tests for Veritas Phase 8 Payload Size Enforcement

Tests for payload size validation in utils.py.
"""

import pytest

from app.utils import (
    enforce_payload_size,
    validate_required_fields,
    validate_string_field,
    validate_numeric_field,
    sanitize_string,
)
from app.error_handler import PayloadSizeError, InvalidPayloadError


class TestPayloadSizeEnforcement:
    """Tests for enforce_payload_size function."""

    def test_small_payload_passes(self):
        """Test that small payloads pass validation."""
        payload = {"text": "Small text"}
        # Should not raise
        enforce_payload_size(payload, max_kb=64)

    def test_large_payload_fails(self):
        """Test that large payloads raise PayloadSizeError."""
        # Create a large payload (>1KB)
        large_text = "x" * 2000
        payload = {"text": large_text}

        with pytest.raises(PayloadSizeError) as exc_info:
            enforce_payload_size(payload, max_kb=1)

        assert exc_info.value.code == "PAYLOAD_TOO_LARGE"
        assert exc_info.value.details["max_kb"] == 1

    def test_empty_payload_passes(self):
        """Test that empty payloads pass validation."""
        payload = {}
        enforce_payload_size(payload, max_kb=64)

    def test_uses_default_max_from_config(self):
        """Test that default max comes from config."""
        payload = {"text": "Small text"}
        # Should use config default (64KB)
        enforce_payload_size(payload)

    def test_invalid_payload_type(self):
        """Test that circular references raise InvalidPayloadError."""
        # Create a circular reference that can't be serialized
        payload = {"text": "hello"}
        payload["self"] = payload  # Circular reference

        with pytest.raises(InvalidPayloadError):
            enforce_payload_size(payload)


class TestValidateRequiredFields:
    """Tests for validate_required_fields function."""

    def test_all_fields_present(self):
        """Test validation passes when all fields present."""
        payload = {"text": "hello", "source": "test"}
        # Should not raise
        validate_required_fields(payload, ["text", "source"])

    def test_missing_field_raises_error(self):
        """Test validation fails when field missing."""
        payload = {"text": "hello"}

        with pytest.raises(InvalidPayloadError) as exc_info:
            validate_required_fields(payload, ["text", "source"])

        assert "source" in exc_info.value.details["missing_fields"]

    def test_empty_required_list(self):
        """Test validation passes with empty required list."""
        payload = {"text": "hello"}
        validate_required_fields(payload, [])


class TestValidateStringField:
    """Tests for validate_string_field function."""

    def test_valid_string_passes(self):
        """Test validation passes for valid string."""
        payload = {"text": "hello"}
        validate_string_field(payload, "text")

    def test_non_string_raises_error(self):
        """Test validation fails for non-string."""
        payload = {"text": 123}

        with pytest.raises(InvalidPayloadError) as exc_info:
            validate_string_field(payload, "text")

        assert exc_info.value.details["field"] == "text"

    def test_empty_string_fails_by_default(self):
        """Test validation fails for empty string by default."""
        payload = {"text": "   "}

        with pytest.raises(InvalidPayloadError):
            validate_string_field(payload, "text")

    def test_empty_string_allowed(self):
        """Test validation passes for empty string when allowed."""
        payload = {"text": ""}
        validate_string_field(payload, "text", allow_empty=True)

    def test_max_length_enforced(self):
        """Test validation fails when exceeding max length."""
        payload = {"text": "hello world"}

        with pytest.raises(InvalidPayloadError) as exc_info:
            validate_string_field(payload, "text", max_length=5)

        assert exc_info.value.details["max_length"] == 5

    def test_missing_field_skipped(self):
        """Test validation skips missing fields."""
        payload = {}
        # Should not raise
        validate_string_field(payload, "text")


class TestValidateNumericField:
    """Tests for validate_numeric_field function."""

    def test_valid_int_passes(self):
        """Test validation passes for valid int."""
        payload = {"count": 10}
        validate_numeric_field(payload, "count")

    def test_valid_float_passes(self):
        """Test validation passes for valid float."""
        payload = {"score": 0.75}
        validate_numeric_field(payload, "score")

    def test_non_numeric_raises_error(self):
        """Test validation fails for non-numeric."""
        payload = {"count": "ten"}

        with pytest.raises(InvalidPayloadError) as exc_info:
            validate_numeric_field(payload, "count")

        assert exc_info.value.details["field"] == "count"

    def test_min_value_enforced(self):
        """Test validation fails when below min."""
        payload = {"count": -5}

        with pytest.raises(InvalidPayloadError) as exc_info:
            validate_numeric_field(payload, "count", min_value=0)

        assert exc_info.value.details["min_value"] == 0

    def test_max_value_enforced(self):
        """Test validation fails when above max."""
        payload = {"count": 150}

        with pytest.raises(InvalidPayloadError) as exc_info:
            validate_numeric_field(payload, "count", max_value=100)

        assert exc_info.value.details["max_value"] == 100


class TestSanitizeString:
    """Tests for sanitize_string function."""

    def test_removes_html_tags(self):
        """Test that HTML tags are removed."""
        result = sanitize_string("<p>Hello</p> <b>World</b>")
        assert "<p>" not in result
        assert "<b>" not in result
        assert "Hello" in result
        assert "World" in result

    def test_removes_null_bytes(self):
        """Test that null bytes are removed."""
        result = sanitize_string("Hello\x00World")
        assert "\x00" not in result
        assert "HelloWorld" == result

    def test_strips_whitespace(self):
        """Test that whitespace is stripped."""
        result = sanitize_string("  Hello World  ")
        assert result == "Hello World"

    def test_removes_script_tags(self):
        """Test that script tags are removed."""
        result = sanitize_string("<script>alert('xss')</script>Hello")
        assert "<script>" not in result
        assert "</script>" not in result
        # Note: Content between tags may remain after basic tag stripping
        # This is a basic sanitizer, not a full HTML parser
