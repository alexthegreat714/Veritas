"""
Tests for Veritas Phase 7 Generate Report Event

Tests for the /event/congress endpoint with generate_veritas_report event type.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestGenerateReportEventEndpoint:
    """Tests for generate_veritas_report via /event/congress endpoint."""

    def test_endpoint_accepts_generate_veritas_report(self):
        """Test that endpoint accepts generate_veritas_report event type."""
        with patch("app.trend_engine.load_all_audits", return_value=[]):
            with patch("app.trend_engine.load_all_audits", return_value=[]):
                with tempfile.TemporaryDirectory() as tmpdir:
                    with patch("app.reporting.REPORTS_DIR", Path(tmpdir)):
                        response = client.post(
                            "/event/congress",
                            json={
                                "event_type": "generate_veritas_report",
                                "payload": {},
                            },
                        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] == True
        assert data["event_type"] == "generate_veritas_report"

    def test_endpoint_returns_full_report_structure(self):
        """Test that endpoint returns full report structure."""
        with patch("app.trend_engine.load_all_audits", return_value=[]):
            with patch("app.trend_engine.load_all_audits", return_value=[]):
                with tempfile.TemporaryDirectory() as tmpdir:
                    with patch("app.reporting.REPORTS_DIR", Path(tmpdir)):
                        response = client.post(
                            "/event/congress",
                            json={
                                "event_type": "generate_veritas_report",
                                "payload": {},
                            },
                        )

        data = response.json()
        result = data["result"]

        assert "meta" in result
        assert "trends" in result
        assert "monitoring" in result
        assert "performance" in result
        assert "chart_data" in result
        assert "summary" in result
        assert "recommendations" in result

    def test_endpoint_stores_report_by_default(self):
        """Test that endpoint stores report by default."""
        with patch("app.trend_engine.load_all_audits", return_value=[]):
            with patch("app.trend_engine.load_all_audits", return_value=[]):
                with tempfile.TemporaryDirectory() as tmpdir:
                    with patch("app.reporting.REPORTS_DIR", Path(tmpdir)):
                        response = client.post(
                            "/event/congress",
                            json={
                                "event_type": "generate_veritas_report",
                                "payload": {},
                            },
                        )

        data = response.json()
        result = data["result"]

        assert "storage" in result
        assert result["storage"]["stored"] == True

    def test_endpoint_respects_store_false_payload(self):
        """Test that endpoint respects store=False in payload."""
        with patch("app.trend_engine.load_all_audits", return_value=[]):
            with patch("app.trend_engine.load_all_audits", return_value=[]):
                response = client.post(
                    "/event/congress",
                    json={
                        "event_type": "generate_veritas_report",
                        "payload": {"store": False},
                    },
                )

        data = response.json()
        result = data["result"]

        assert result["storage"]["stored"] == False

    def test_endpoint_returns_performance_score(self):
        """Test that endpoint returns performance score."""
        with patch("app.trend_engine.load_all_audits", return_value=[]):
            with patch("app.trend_engine.load_all_audits", return_value=[]):
                with tempfile.TemporaryDirectory() as tmpdir:
                    with patch("app.reporting.REPORTS_DIR", Path(tmpdir)):
                        response = client.post(
                            "/event/congress",
                            json={
                                "event_type": "generate_veritas_report",
                                "payload": {},
                            },
                        )

        data = response.json()
        result = data["result"]

        assert "score" in result["performance"]
        assert "grades" in result["performance"]
        assert "stability_index" in result["performance"]

    def test_endpoint_returns_meta_with_version(self):
        """Test that endpoint returns meta with version info."""
        with patch("app.trend_engine.load_all_audits", return_value=[]):
            with patch("app.trend_engine.load_all_audits", return_value=[]):
                with tempfile.TemporaryDirectory() as tmpdir:
                    with patch("app.reporting.REPORTS_DIR", Path(tmpdir)):
                        response = client.post(
                            "/event/congress",
                            json={
                                "event_type": "generate_veritas_report",
                                "payload": {},
                            },
                        )

        data = response.json()
        meta = data["result"]["meta"]

        assert meta["agent"] == "veritas"
        assert meta["version"] == "0.10.0"
        assert meta["phase"] == 10

    def test_endpoint_returns_chart_data(self):
        """Test that endpoint returns chart-ready data."""
        with patch("app.trend_engine.load_all_audits", return_value=[]):
            with patch("app.trend_engine.load_all_audits", return_value=[]):
                with tempfile.TemporaryDirectory() as tmpdir:
                    with patch("app.reporting.REPORTS_DIR", Path(tmpdir)):
                        response = client.post(
                            "/event/congress",
                            json={
                                "event_type": "generate_veritas_report",
                                "payload": {},
                            },
                        )

        data = response.json()
        chart_data = data["result"]["chart_data"]

        assert "bias_over_time" in chart_data
        assert "logic_issues_over_time" in chart_data
        assert "source_rates" in chart_data

    def test_endpoint_returns_recommendations(self):
        """Test that endpoint returns recommendations list."""
        with patch("app.trend_engine.load_all_audits", return_value=[]):
            with patch("app.trend_engine.load_all_audits", return_value=[]):
                with tempfile.TemporaryDirectory() as tmpdir:
                    with patch("app.reporting.REPORTS_DIR", Path(tmpdir)):
                        response = client.post(
                            "/event/congress",
                            json={
                                "event_type": "generate_veritas_report",
                                "payload": {},
                            },
                        )

        data = response.json()
        recommendations = data["result"]["recommendations"]

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        # Should always include the advisory note
        assert any("advisory" in r.lower() for r in recommendations)


class TestGenerateReportEventValidation:
    """Tests for event validation."""

    def test_unknown_event_type_rejected(self):
        """Test that unknown event types are rejected."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "unknown_event",
                "payload": {},
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert data["ok"] == False
        assert "supported_types" in data

    def test_supported_types_list(self):
        """Test that supported types list is returned on error."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "invalid_type",
                "payload": {},
            },
        )

        data = response.json()
        supported = data["supported_types"]

        assert "generate_veritas_report" in supported
        assert "bill_for_review" in supported
        assert "monitoring_cycle" in supported

    def test_event_type_in_status_endpoint(self):
        """Test that generate_report is in status endpoint tools."""
        response = client.get("/status")

        data = response.json()

        assert "generate_report" in data["tools"]


class TestGenerateReportEventIntegration:
    """Integration tests for generate_veritas_report event."""

    def test_full_report_generation_flow(self):
        """Test complete report generation flow through endpoint."""
        # Create mock audits
        mock_audits = [
            {
                "timestamp": "2024-01-01T10:00:00Z",
                "audit": {
                    "logical_issues": [],
                    "bias_flags": [],
                    "confidence": "high",
                },
                "source_validation": [],
            },
            {
                "timestamp": "2024-01-08T10:00:00Z",
                "audit": {
                    "logical_issues": [{"type": "contradiction", "description": "test"}],
                    "bias_flags": [{"type": "emotional_language", "explanation": "test"}],
                    "confidence": "medium",
                },
                "source_validation": [],
            },
        ]

        with patch("app.trend_engine.load_all_audits", return_value=mock_audits):
            with patch("app.trend_engine.load_all_audits", return_value=mock_audits):
                with patch("app.trend_engine.load_all_audits", return_value=mock_audits):
                    with tempfile.TemporaryDirectory() as tmpdir:
                        with patch("app.reporting.REPORTS_DIR", Path(tmpdir)):
                            response = client.post(
                                "/event/congress",
                                json={
                                    "event_type": "generate_veritas_report",
                                    "payload": {},
                                },
                            )

        assert response.status_code == 200
        data = response.json()
        result = data["result"]

        # Should have analyzed 2 audits
        assert result["trends"]["audits_analyzed"] == 2

    def test_report_includes_monitoring_fallback(self):
        """Test that report includes monitoring fallback when no snapshots."""
        with patch("app.trend_engine.load_all_audits", return_value=[]):
            with patch("app.trend_engine.load_all_audits", return_value=[]):
                with patch("app.reporting._load_recent_monitoring_snapshot", return_value=None):
                    with tempfile.TemporaryDirectory() as tmpdir:
                        with patch("app.reporting.REPORTS_DIR", Path(tmpdir)):
                            response = client.post(
                                "/event/congress",
                                json={
                                    "event_type": "generate_veritas_report",
                                    "payload": {},
                                },
                            )

        data = response.json()
        monitoring = data["result"]["monitoring"]

        assert monitoring["overall_status"] == "unknown"
        assert "No recent monitoring" in monitoring.get("message", "")


class TestCongressEventTypes:
    """Tests for CONGRESS_EVENT_TYPES registry."""

    def test_generate_veritas_report_in_registry(self):
        """Test that generate_veritas_report is in CONGRESS_EVENT_TYPES."""
        from app.routes.veritas import CONGRESS_EVENT_TYPES

        assert "generate_veritas_report" in CONGRESS_EVENT_TYPES

    def test_registry_maps_to_correct_tool(self):
        """Test that registry maps to tool_generate_report."""
        from app.routes.veritas import CONGRESS_EVENT_TYPES
        from app.tools import tool_generate_report

        assert CONGRESS_EVENT_TYPES["generate_veritas_report"] is tool_generate_report


class TestStatusEndpointPhase10:
    """Tests for status endpoint Phase 10 updates."""

    def test_status_version(self):
        """Test status endpoint returns version 0.10.0."""
        response = client.get("/status")
        data = response.json()

        assert data["version"] == "0.10.0"

    def test_status_phase(self):
        """Test status endpoint returns phase 10."""
        response = client.get("/status")
        data = response.json()

        assert data["phase"] == 10

    def test_status_components_include_new_engines(self):
        """Test status includes trend_engine and reporting_engine."""
        response = client.get("/status")
        data = response.json()

        components = data["components"]
        assert components.get("trend_engine") == "active"
        assert components.get("reporting_engine") == "active"
