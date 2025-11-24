"""
Veritas Utilities

Phase 8: Production utilities for payload validation and rate limiting.

IMPORTANT: Veritas monitors only — never intervenes or takes autonomous actions.
"""

import json
import re
import time
from typing import Any, Dict, List

from app.config import get_max_payload_size_kb, get_rate_limit
from app.error_handler import (
    PayloadSizeError,
    RateLimitError,
    InvalidPayloadError,
)


# ============================================================================
# Rate Limiting State
# ============================================================================

RATE_STATE: Dict[str, List[float]] = {
    "events": [],
    "tools": []
}

RATE_WINDOW_SECONDS = 60


def _clean_old_timestamps(action_type: str) -> None:
    """Remove timestamps older than the rate window."""
    current_time = time.time()
    cutoff = current_time - RATE_WINDOW_SECONDS
    RATE_STATE[action_type] = [
        ts for ts in RATE_STATE[action_type]
        if ts > cutoff
    ]


def enforce_rate_limit(action_type: str, limit: int = None) -> None:
    """
    Enforce rate limit for an action type.

    Uses a rolling window of 60 seconds.

    Args:
        action_type: Type of action ("events" or "tools").
        limit: Optional override for rate limit.

    Raises:
        RateLimitError: If rate limit is exceeded.
    """
    if action_type not in RATE_STATE:
        RATE_STATE[action_type] = []

    # Get limit from config if not provided
    if limit is None:
        limit = get_rate_limit(action_type)

    # Clean old timestamps
    _clean_old_timestamps(action_type)

    # Check if limit exceeded
    current_count = len(RATE_STATE[action_type])
    if current_count >= limit:
        raise RateLimitError(
            f"Rate limit exceeded for {action_type}. "
            f"Maximum {limit} requests per minute.",
            limit=limit,
            window_seconds=RATE_WINDOW_SECONDS
        )

    # Record this request
    RATE_STATE[action_type].append(time.time())


def get_rate_state() -> Dict[str, int]:
    """
    Get current rate state (counts within window).

    Returns:
        Dictionary with current counts for each action type.
    """
    result = {}
    for action_type in RATE_STATE:
        _clean_old_timestamps(action_type)
        result[action_type] = len(RATE_STATE[action_type])
    return result


def reset_rate_state() -> None:
    """Reset all rate limiting state (for testing)."""
    global RATE_STATE
    RATE_STATE = {
        "events": [],
        "tools": []
    }


# ============================================================================
# Payload Size Enforcement
# ============================================================================


def enforce_payload_size(payload: Dict[str, Any], max_kb: int = None) -> None:
    """
    Enforce payload size limit.

    Args:
        payload: The payload dictionary to check.
        max_kb: Optional override for maximum size in KB.

    Raises:
        PayloadSizeError: If payload exceeds size limit.
    """
    if max_kb is None:
        max_kb = get_max_payload_size_kb()

    # Serialize to JSON to get actual size
    try:
        serialized = json.dumps(payload, default=str)
        size_bytes = len(serialized.encode('utf-8'))
        size_kb = size_bytes / 1024
    except (TypeError, ValueError) as e:
        raise InvalidPayloadError(
            f"Payload cannot be serialized: {str(e)}"
        )

    if size_kb > max_kb:
        raise PayloadSizeError(
            f"Payload size ({size_kb:.2f} KB) exceeds maximum ({max_kb} KB)",
            max_kb=max_kb,
            actual_kb=size_kb
        )


# ============================================================================
# Input Validation Utilities
# ============================================================================


def validate_required_fields(
    payload: Dict[str, Any],
    required: List[str]
) -> None:
    """
    Validate that required fields are present in payload.

    Args:
        payload: The payload to validate.
        required: List of required field names.

    Raises:
        InvalidPayloadError: If required fields are missing.
    """
    missing = [field for field in required if field not in payload]
    if missing:
        raise InvalidPayloadError(
            f"Missing required fields: {', '.join(missing)}",
            details={"missing_fields": missing}
        )


def validate_string_field(
    payload: Dict[str, Any],
    field: str,
    max_length: int = None,
    allow_empty: bool = False
) -> None:
    """
    Validate a string field in the payload.

    Args:
        payload: The payload containing the field.
        field: Name of the field to validate.
        max_length: Optional maximum length.
        allow_empty: Whether empty strings are allowed.

    Raises:
        InvalidPayloadError: If validation fails.
    """
    if field not in payload:
        return  # Not present, skip validation

    value = payload[field]

    if not isinstance(value, str):
        raise InvalidPayloadError(
            f"Field '{field}' must be a string",
            details={"field": field, "type": type(value).__name__}
        )

    if not allow_empty and not value.strip():
        raise InvalidPayloadError(
            f"Field '{field}' cannot be empty",
            details={"field": field}
        )

    if max_length and len(value) > max_length:
        raise InvalidPayloadError(
            f"Field '{field}' exceeds maximum length ({max_length})",
            details={"field": field, "max_length": max_length, "actual_length": len(value)}
        )


def validate_numeric_field(
    payload: Dict[str, Any],
    field: str,
    min_value: float = None,
    max_value: float = None
) -> None:
    """
    Validate a numeric field in the payload.

    Args:
        payload: The payload containing the field.
        field: Name of the field to validate.
        min_value: Optional minimum value.
        max_value: Optional maximum value.

    Raises:
        InvalidPayloadError: If validation fails.
    """
    if field not in payload:
        return  # Not present, skip validation

    value = payload[field]

    if not isinstance(value, (int, float)):
        raise InvalidPayloadError(
            f"Field '{field}' must be a number",
            details={"field": field, "type": type(value).__name__}
        )

    if min_value is not None and value < min_value:
        raise InvalidPayloadError(
            f"Field '{field}' must be >= {min_value}",
            details={"field": field, "min_value": min_value, "actual": value}
        )

    if max_value is not None and value > max_value:
        raise InvalidPayloadError(
            f"Field '{field}' must be <= {max_value}",
            details={"field": field, "max_value": max_value, "actual": value}
        )


def sanitize_string(value: str) -> str:
    """
    Sanitize a string by removing potentially dangerous content.

    Args:
        value: String to sanitize.

    Returns:
        Sanitized string.
    """
    # Remove HTML tags
    value = re.sub(r'<[^>]+>', '', value)

    # Remove script tags content
    value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)

    # Remove null bytes
    value = value.replace('\x00', '')

    return value.strip()
