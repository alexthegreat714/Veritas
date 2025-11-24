"""
Tests for Veritas Phase 8 Feature Flags

Tests for feature flag functionality in config.py.
"""

import pytest
from unittest.mock import patch

from app.config import (
    VERITAS_FEATURE_FLAGS,
    get_feature_flag,
    is_feature_enabled,
    get_rate_limit,
    get_max_payload_size_kb,
    is_strict_mode,
)


class TestFeatureFlags:
    """Tests for feature flag functions."""

    def test_get_feature_flag_existing(self):
        """Test getting an existing feature flag."""
        assert get_feature_flag("enable_rag") == True

    def test_get_feature_flag_nonexistent(self):
        """Test getting a non-existent feature flag."""
        assert get_feature_flag("nonexistent_flag") is None

    def test_is_feature_enabled_rag(self):
        """Test is_feature_enabled for RAG."""
        assert is_feature_enabled("rag") == True

    def test_is_feature_enabled_monitoring(self):
        """Test is_feature_enabled for monitoring."""
        assert is_feature_enabled("monitoring") == True

    def test_is_feature_enabled_reporting(self):
        """Test is_feature_enabled for reporting."""
        assert is_feature_enabled("reporting") == True

    def test_is_feature_enabled_nonexistent(self):
        """Test is_feature_enabled for non-existent feature."""
        assert is_feature_enabled("nonexistent") == False

    def test_get_rate_limit_events(self):
        """Test getting rate limit for events."""
        limit = get_rate_limit("events")
        assert limit == 20

    def test_get_rate_limit_tools(self):
        """Test getting rate limit for tools."""
        limit = get_rate_limit("tools")
        assert limit == 30

    def test_get_rate_limit_unknown(self):
        """Test getting rate limit for unknown type."""
        limit = get_rate_limit("unknown")
        assert limit == 100  # Default

    def test_get_max_payload_size_kb(self):
        """Test getting max payload size."""
        size = get_max_payload_size_kb()
        assert size == 64

    def test_is_strict_mode_default(self):
        """Test is_strict_mode default value."""
        assert is_strict_mode() == False


class TestFeatureFlagsStructure:
    """Tests for feature flags structure."""

    def test_feature_flags_has_enable_rag(self):
        """Test that feature flags has enable_rag."""
        assert "enable_rag" in VERITAS_FEATURE_FLAGS

    def test_feature_flags_has_enable_monitoring(self):
        """Test that feature flags has enable_monitoring."""
        assert "enable_monitoring" in VERITAS_FEATURE_FLAGS

    def test_feature_flags_has_enable_reporting(self):
        """Test that feature flags has enable_reporting."""
        assert "enable_reporting" in VERITAS_FEATURE_FLAGS

    def test_feature_flags_has_strict_mode(self):
        """Test that feature flags has strict_mode."""
        assert "strict_mode" in VERITAS_FEATURE_FLAGS

    def test_feature_flags_has_max_payload_size(self):
        """Test that feature flags has max_payload_size_kb."""
        assert "max_payload_size_kb" in VERITAS_FEATURE_FLAGS

    def test_feature_flags_has_rate_limits(self):
        """Test that feature flags has rate_limits."""
        assert "rate_limits" in VERITAS_FEATURE_FLAGS
        assert "events_per_minute" in VERITAS_FEATURE_FLAGS["rate_limits"]
        assert "tools_per_minute" in VERITAS_FEATURE_FLAGS["rate_limits"]


class TestFeatureFlagDisableTools:
    """Tests for disabled features."""

    def test_monitoring_disabled_raises_error(self):
        """Test that disabled monitoring raises FeatureDisabledError."""
        from app.tools import tool_run_monitoring
        from app.error_handler import FeatureDisabledError

        with patch.dict(VERITAS_FEATURE_FLAGS, {"enable_monitoring": False}):
            with pytest.raises(FeatureDisabledError) as exc_info:
                tool_run_monitoring({})

            assert exc_info.value.details["feature"] == "monitoring"

    def test_reporting_disabled_raises_error(self):
        """Test that disabled reporting raises FeatureDisabledError."""
        from app.tools import tool_generate_report
        from app.error_handler import FeatureDisabledError

        with patch.dict(VERITAS_FEATURE_FLAGS, {"enable_reporting": False}):
            with pytest.raises(FeatureDisabledError) as exc_info:
                tool_generate_report({})

            assert exc_info.value.details["feature"] == "reporting"

    def test_rag_disabled_returns_empty(self):
        """Test that disabled RAG returns empty results."""
        from app.rag.query import query_relevant_documents

        with patch.dict(VERITAS_FEATURE_FLAGS, {"enable_rag": False}):
            result = query_relevant_documents("test query")

            assert result["hits"] == []
            assert result.get("disabled") == True
