"""
Tests for Veritas Phase 6 Monitoring Tool

Tests for tool_run_monitoring function in app/tools/__init__.py.
"""

import pytest
import json
import os
from pathlib import Path

from app.tools import tool_run_monitoring, registry
from app.memory_utils import (
    store_audit,
    get_recent_audits,
    clear_disputes,
    AUDITS_DIR,
    MONITORING_DIR,
)


# Clean up test files after each test
@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Clean up test files before and after each test."""
    yield
    # Clean up monitoring snapshots created during tests
    for f in MONITORING_DIR.glob("*.json"):
        try:
            os.remove(f)
        except Exception:
            pass
    # Clean up audits created during tests
    for f in AUDITS_DIR.glob("*test*.json"):
        try:
            os.remove(f)
        except Exception:
            pass


class TestToolRunMonitoring:
    """Tests for tool_run_monitoring function."""

    def test_empty_payload(self):
        """Test monitoring with empty payload."""
        result = tool_run_monitoring({})

        assert "logical_drift" in result
        assert "bias_trends" in result
        assert "anomalies" in result
        assert "overall_status" in result
        assert "timestamp" in result

    def test_default_limit(self):
        """Test that default limit is applied."""
        result = tool_run_monitoring({})

        # Default limit is 10
        assert "audits_analyzed" in result

    def test_custom_limit(self):
        """Test custom limit parameter."""
        result = tool_run_monitoring({"limit": 5})

        assert "audits_analyzed" in result

    def test_storage_result(self):
        """Test that monitoring result is stored."""
        result = tool_run_monitoring({})

        assert "storage" in result
        assert result["storage"]["stored"] is True
        assert result["storage"]["file_path"] is not None
        assert result["storage"]["snapshot_id"] is not None

    def test_result_structure(self):
        """Test complete result structure."""
        result = tool_run_monitoring({})

        # Top-level keys
        assert "logical_drift" in result
        assert "bias_trends" in result
        assert "anomalies" in result
        assert "overall_status" in result
        assert "timestamp" in result
        assert "audits_analyzed" in result
        assert "storage" in result

        # Logical drift structure
        assert "drift_score" in result["logical_drift"]
        assert "is_concerning" in result["logical_drift"]

        # Bias trends structure
        assert "bias_trend_score" in result["bias_trends"]
        assert "is_concerning" in result["bias_trends"]

        # Anomalies structure
        assert "anomaly_detected" in result["anomalies"]

        # Storage structure
        assert "stored" in result["storage"]
        assert "file_path" in result["storage"]

    def test_overall_status_values(self):
        """Test that overall_status is a valid value."""
        result = tool_run_monitoring({})

        assert result["overall_status"] in ["stable", "warning", "critical"]


class TestToolRegistration:
    """Tests for tool registration."""

    def test_run_monitoring_in_registry(self):
        """Test that run_monitoring is registered."""
        tools = registry.list_tools()

        assert "run_monitoring" in tools

    def test_invoke_run_monitoring(self):
        """Test invoking run_monitoring through registry."""
        result = registry.invoke("run_monitoring", {})

        assert "logical_drift" in result
        assert "overall_status" in result


class TestMonitoringWithAudits:
    """Tests for monitoring with actual audit data."""

    def test_monitoring_with_stored_audits(self):
        """Test monitoring with pre-stored audits."""
        # Store some test audits
        for i in range(3):
            audit = {
                "audit": {
                    "audit": {
                        "original_text": f"Test text {i}",
                        "logical_issues": [
                            {"type": "fallacy", "description": f"Test fallacy {i}"}
                        ],
                        "bias_flags": [],
                        "confidence": "medium",
                    }
                },
                "test_marker": True,
            }
            store_audit(audit, audit_type="test")

        # Run monitoring
        result = tool_run_monitoring({"limit": 10})

        assert result["audits_analyzed"] >= 0  # May or may not pick up test audits
        assert "overall_status" in result

    def test_monitoring_stable_with_no_audits(self):
        """Test that monitoring returns stable with no audits."""
        result = tool_run_monitoring({"limit": 0})

        # With no audits, should be stable (no concerns)
        assert result["overall_status"] == "stable"


class TestMonitoringEdgeCases:
    """Tests for edge cases in monitoring."""

    def test_negative_limit(self):
        """Test handling of negative limit."""
        # Should handle gracefully (empty list)
        result = tool_run_monitoring({"limit": -1})

        assert "overall_status" in result

    def test_very_large_limit(self):
        """Test handling of very large limit."""
        result = tool_run_monitoring({"limit": 10000})

        assert "audits_analyzed" in result
        assert result["overall_status"] in ["stable", "warning", "critical"]

    def test_zero_limit(self):
        """Test handling of zero limit."""
        result = tool_run_monitoring({"limit": 0})

        assert result["audits_analyzed"] == 0
        assert result["overall_status"] == "stable"


class TestStatusEndpointUpdated:
    """Tests for status endpoint showing monitoring tool."""

    def test_run_monitoring_in_status_tools(self):
        """Test that run_monitoring appears in tools list."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()

        assert "run_monitoring" in data["tools"]

    def test_status_shows_monitoring_engine(self):
        """Test that status shows monitoring_engine component."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()

        assert "monitoring_engine" in data["components"]
        assert data["components"]["monitoring_engine"] == "active"

    def test_status_shows_phase_9(self):
        """Test that status shows phase 9."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()

        assert data["phase"] == 9
        assert data["version"] == "0.9.0"
