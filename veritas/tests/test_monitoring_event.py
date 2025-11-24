"""
Tests for Veritas Phase 6 Monitoring Event

Tests for /event/congress with monitoring_cycle event type.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestMonitoringCycleEvent:
    """Tests for /event/congress with monitoring_cycle."""

    def test_monitoring_cycle_basic(self):
        """Test basic monitoring cycle event."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "monitoring_cycle",
                "payload": {}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["event_type"] == "monitoring_cycle"
        assert "result" in data

    def test_monitoring_cycle_with_limit(self):
        """Test monitoring cycle with custom limit."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "monitoring_cycle",
                "payload": {"limit": 5}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "result" in data

    def test_monitoring_cycle_returns_expected_structure(self):
        """Test monitoring cycle returns expected result structure."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "monitoring_cycle",
                "payload": {}
            }
        )

        assert response.status_code == 200
        data = response.json()
        result = data["result"]

        # Check all expected keys
        assert "logical_drift" in result
        assert "bias_trends" in result
        assert "anomalies" in result
        assert "overall_status" in result
        assert "timestamp" in result
        assert "audits_analyzed" in result
        assert "storage" in result

    def test_monitoring_cycle_drift_structure(self):
        """Test logical drift structure in result."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "monitoring_cycle",
                "payload": {}
            }
        )

        assert response.status_code == 200
        data = response.json()
        drift = data["result"]["logical_drift"]

        assert "drift_score" in drift
        assert "increasing_issue_types" in drift
        assert "possible_causes" in drift
        assert "is_concerning" in drift

    def test_monitoring_cycle_bias_structure(self):
        """Test bias trends structure in result."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "monitoring_cycle",
                "payload": {}
            }
        )

        assert response.status_code == 200
        data = response.json()
        bias = data["result"]["bias_trends"]

        assert "bias_trend_score" in bias
        assert "bias_types_increasing" in bias
        assert "summary" in bias
        assert "is_concerning" in bias

    def test_monitoring_cycle_anomalies_structure(self):
        """Test anomalies structure in result."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "monitoring_cycle",
                "payload": {}
            }
        )

        assert response.status_code == 200
        data = response.json()
        anomalies = data["result"]["anomalies"]

        assert "anomaly_detected" in anomalies
        assert "anomalies" in anomalies

    def test_monitoring_cycle_storage_structure(self):
        """Test storage structure in result."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "monitoring_cycle",
                "payload": {}
            }
        )

        assert response.status_code == 200
        data = response.json()
        storage = data["result"]["storage"]

        assert "stored" in storage
        assert storage["stored"] is True
        assert "file_path" in storage
        assert "snapshot_id" in storage

    def test_monitoring_cycle_valid_status(self):
        """Test that overall_status is valid."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "monitoring_cycle",
                "payload": {}
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["result"]["overall_status"] in ["stable", "warning", "critical"]

    def test_monitoring_cycle_zero_limit(self):
        """Test monitoring cycle with zero limit."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "monitoring_cycle",
                "payload": {"limit": 0}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["audits_analyzed"] == 0
        assert data["result"]["overall_status"] == "stable"


class TestMonitoringCycleIntegration:
    """Integration tests for monitoring cycle with other events."""

    def test_monitoring_after_bill_review(self):
        """Test monitoring after bill review event."""
        # First, do a bill review
        client.post(
            "/event/congress",
            json={
                "event_type": "bill_for_review",
                "payload": {
                    "bill_id": "BILL-MON-001",
                    "text": "This bill establishes monitoring requirements."
                }
            }
        )

        # Then run monitoring
        response = client.post(
            "/event/congress",
            json={
                "event_type": "monitoring_cycle",
                "payload": {}
            }
        )

        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_monitoring_after_statement_audit(self):
        """Test monitoring after statement audit event."""
        # First, do a statement audit
        client.post(
            "/event/congress",
            json={
                "event_type": "statement_for_audit",
                "payload": {
                    "statement_id": "STMT-MON-001",
                    "text": "This statement needs monitoring."
                }
            }
        )

        # Then run monitoring
        response = client.post(
            "/event/congress",
            json={
                "event_type": "monitoring_cycle",
                "payload": {}
            }
        )

        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_monitoring_after_dispute(self):
        """Test monitoring after dispute analysis event."""
        # First, do a dispute analysis
        client.post(
            "/event/congress",
            json={
                "event_type": "dispute_for_analysis",
                "payload": {
                    "agent_A": {
                        "agent": "Sky",
                        "text": "Monitoring is good.",
                        "metadata": {}
                    },
                    "agent_B": {
                        "agent": "Mercury",
                        "text": "Monitoring is bad.",
                        "metadata": {}
                    }
                }
            }
        )

        # Then run monitoring
        response = client.post(
            "/event/congress",
            json={
                "event_type": "monitoring_cycle",
                "payload": {}
            }
        )

        assert response.status_code == 200
        assert response.json()["ok"] is True


class TestMonitoringCycleSupported:
    """Tests for monitoring_cycle in supported types."""

    def test_monitoring_cycle_is_supported(self):
        """Test that monitoring_cycle is in supported types."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "unknown_type",
                "payload": {}
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "monitoring_cycle" in data["supported_types"]


class TestStatusEndpointPhase9:
    """Tests for status endpoint at Phase 9."""

    def test_status_phase_9(self):
        """Test status shows phase 9."""
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert data["phase"] == 11

    def test_status_version_0_9_0(self):
        """Test status shows version 0.10.0."""
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "0.11.0"

    def test_status_monitoring_engine_active(self):
        """Test status shows monitoring_engine active."""
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert data["components"]["monitoring_engine"] == "active"

    def test_status_run_monitoring_in_tools(self):
        """Test status shows run_monitoring in tools."""
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert "run_monitoring" in data["tools"]


class TestMonitoringCycleEdgeCases:
    """Edge case tests for monitoring cycle event."""

    def test_monitoring_with_empty_payload(self):
        """Test monitoring with completely empty payload."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "monitoring_cycle",
                "payload": {}
            }
        )

        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_monitoring_with_extra_fields(self):
        """Test monitoring with extra fields in payload."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "monitoring_cycle",
                "payload": {
                    "limit": 10,
                    "extra_field": "ignored",
                    "another": 123
                }
            }
        )

        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_monitoring_with_large_limit(self):
        """Test monitoring with very large limit."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "monitoring_cycle",
                "payload": {"limit": 1000}
            }
        )

        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_monitoring_returns_timestamp(self):
        """Test monitoring returns valid timestamp."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "monitoring_cycle",
                "payload": {}
            }
        )

        assert response.status_code == 200
        data = response.json()

        timestamp = data["result"]["timestamp"]
        assert timestamp is not None
        assert "T" in timestamp  # ISO format contains T
