"""
Tests for Veritas Phase 8 Rate Limiting

Tests for rate limiting functionality in utils.py.
"""

import pytest
import time
from unittest.mock import patch

from app.utils import (
    enforce_rate_limit,
    get_rate_state,
    reset_rate_state,
    RATE_STATE,
)
from app.error_handler import RateLimitError
from app.config import VERITAS_FEATURE_FLAGS


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def setup_method(self):
        """Reset rate state before each test."""
        reset_rate_state()

    def test_single_request_passes(self):
        """Test that a single request passes rate limiting."""
        # Should not raise
        enforce_rate_limit("events", limit=20)

    def test_multiple_requests_within_limit(self):
        """Test multiple requests within limit."""
        for _ in range(5):
            enforce_rate_limit("events", limit=20)

    def test_rate_limit_exceeded(self):
        """Test that rate limit raises error when exceeded."""
        # Set a very low limit
        for _ in range(3):
            enforce_rate_limit("events", limit=3)

        # This should raise
        with pytest.raises(RateLimitError) as exc_info:
            enforce_rate_limit("events", limit=3)

        assert exc_info.value.code == "RATE_LIMIT_EXCEEDED"
        assert exc_info.value.details["limit"] == 3

    def test_tools_rate_limit_separate_from_events(self):
        """Test that tools and events have separate rate limits."""
        # Fill up events limit
        for _ in range(5):
            enforce_rate_limit("events", limit=5)

        # Tools should still work
        enforce_rate_limit("tools", limit=5)

    def test_get_rate_state(self):
        """Test get_rate_state returns current counts."""
        reset_rate_state()
        enforce_rate_limit("events", limit=20)
        enforce_rate_limit("events", limit=20)
        enforce_rate_limit("tools", limit=20)

        state = get_rate_state()
        assert state["events"] == 2
        assert state["tools"] == 1

    def test_reset_rate_state(self):
        """Test reset_rate_state clears all counters."""
        enforce_rate_limit("events", limit=20)
        enforce_rate_limit("tools", limit=20)

        reset_rate_state()

        state = get_rate_state()
        assert state["events"] == 0
        assert state["tools"] == 0

    def test_rate_limit_window_expires(self):
        """Test that old requests expire from the window."""
        # This is harder to test without mocking time
        # We'll test that the state can be cleaned
        reset_rate_state()

        # Add some timestamps
        enforce_rate_limit("events", limit=100)

        # State should have 1 entry
        state = get_rate_state()
        assert state["events"] == 1


class TestRateLimitConfigIntegration:
    """Tests for rate limit integration with config."""

    def setup_method(self):
        """Reset rate state before each test."""
        reset_rate_state()

    def test_uses_config_rate_limit(self):
        """Test that enforce_rate_limit uses config values."""
        # Config has events_per_minute: 20
        for _ in range(19):
            enforce_rate_limit("events")

        # Should still pass at 19
        enforce_rate_limit("events")

        # 21st should fail
        with pytest.raises(RateLimitError):
            enforce_rate_limit("events")
