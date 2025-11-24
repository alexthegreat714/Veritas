"""
Tests for Veritas Phase 8 Status Endpoint

Tests for expanded status endpoint with feature flags and rate limits.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestStatusEndpointExpanded:
    """Tests for expanded status endpoint."""

    def test_status_returns_ok(self):
        """Test status endpoint returns ok."""
        response = client.get("/status")
        data = response.json()

        assert response.status_code == 200
        assert data["ok"] == True

    def test_status_includes_agent(self):
        """Test status includes agent name."""
        response = client.get("/status")
        data = response.json()

        assert data["agent"] == "veritas"

    def test_status_includes_version(self):
        """Test status includes version."""
        response = client.get("/status")
        data = response.json()

        assert data["version"] == "0.11.0"

    def test_status_includes_phase(self):
        """Test status includes phase."""
        response = client.get("/status")
        data = response.json()

        assert data["phase"] == 11

    def test_status_includes_feature_flags(self):
        """Test status includes feature flags."""
        response = client.get("/status")
        data = response.json()

        assert "feature_flags" in data
        assert "rag_enabled" in data["feature_flags"]
        assert "monitoring_enabled" in data["feature_flags"]
        assert "reporting_enabled" in data["feature_flags"]
        assert "strict_mode" in data["feature_flags"]

    def test_status_includes_rate_limits(self):
        """Test status includes rate limits."""
        response = client.get("/status")
        data = response.json()

        assert "rate_limits" in data
        assert "events_per_minute" in data["rate_limits"]
        assert "tools_per_minute" in data["rate_limits"]

    def test_status_includes_components(self):
        """Test status includes all components."""
        response = client.get("/status")
        data = response.json()

        components = data["components"]
        assert "brain" in components
        assert "auditor" in components
        assert "bias_detector" in components
        assert "chain_validator" in components
        assert "source_checker" in components
        assert "rag" in components
        assert "monitoring_engine" in components
        assert "reporting_engine" in components
        assert "error_handler" in components

    def test_status_includes_tools(self):
        """Test status includes tools list."""
        response = client.get("/status")
        data = response.json()

        assert "tools" in data
        assert "review_bill" in data["tools"]
        assert "run_monitoring" in data["tools"]
        assert "generate_report" in data["tools"]

    def test_status_no_secrets_exposed(self):
        """Test that status doesn't expose secrets."""
        response = client.get("/status")
        data = response.json()
        data_str = str(data).lower()

        # Should not contain sensitive patterns
        assert "password" not in data_str
        assert "secret" not in data_str
        assert "token" not in data_str
        assert "key=" not in data_str

    def test_status_no_file_paths_exposed(self):
        """Test that status doesn't expose file paths."""
        response = client.get("/status")
        data = response.json()
        data_str = str(data)

        # Should not contain absolute paths
        assert "/home/" not in data_str
        assert "/root/" not in data_str
        assert "/etc/" not in data_str

    def test_status_no_stack_traces(self):
        """Test that status doesn't contain stack traces."""
        response = client.get("/status")
        data = response.json()
        data_str = str(data).lower()

        # Should not contain traceback indicators
        assert "traceback" not in data_str
        assert "line " not in data_str  # "line 123" style


class TestStatusFeatureFlagReflection:
    """Tests that status reflects feature flag states."""

    def test_rag_enabled_reflected(self):
        """Test RAG enabled state is reflected."""
        response = client.get("/status")
        data = response.json()

        assert data["rag_enabled"] == data["feature_flags"]["rag_enabled"]

    def test_monitoring_enabled_reflected(self):
        """Test monitoring enabled state is reflected."""
        response = client.get("/status")
        data = response.json()

        assert data["monitoring_enabled"] == data["feature_flags"]["monitoring_enabled"]

    def test_reporting_enabled_reflected(self):
        """Test reporting enabled state is reflected."""
        response = client.get("/status")
        data = response.json()

        assert data["reporting_enabled"] == data["feature_flags"]["reporting_enabled"]
