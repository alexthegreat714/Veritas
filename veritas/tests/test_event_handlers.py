"""
Tests for Veritas Phase 4 Event Handlers

Tests for /event/congress endpoint and Congress event handling.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestCongressEventEndpoint:
    """Tests for /event/congress endpoint."""

    def test_bill_for_review_event(self):
        """Test bill_for_review event type."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "bill_for_review",
                "payload": {
                    "bill_id": "BILL-TEST-001",
                    "text": "This bill establishes guidelines for data governance."
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["event_type"] == "bill_for_review"
        assert "result" in data
        assert data["result"]["item_type"] == "bill"
        assert data["result"]["id"] == "BILL-TEST-001"

    def test_statement_for_audit_event(self):
        """Test statement_for_audit event type."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "statement_for_audit",
                "payload": {
                    "statement_id": "STMT-TEST-001",
                    "text": "The committee approved the proposal unanimously."
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["event_type"] == "statement_for_audit"
        assert "result" in data
        assert data["result"]["item_type"] == "statement"
        assert data["result"]["id"] == "STMT-TEST-001"

    def test_dispute_for_analysis_basic(self):
        """Test dispute_for_analysis event type (Phase 8 implementation)."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "dispute_for_analysis",
                "payload": {
                    "agent_A": {
                        "agent": "Sky",
                        "text": "The proposal is valid.",
                        "metadata": {}
                    },
                    "agent_B": {
                        "agent": "Mercury",
                        "text": "The proposal has issues.",
                        "metadata": {}
                    }
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["event_type"] == "dispute_for_analysis"
        # Phase 8: Full dispute analysis result
        assert "agents" in data["result"]
        assert "issues" in data["result"]
        assert "needs_escalation" in data["result"]

    def test_unknown_event_type_returns_400(self):
        """Test that unknown event type returns 400."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "unknown_type",
                "payload": {}
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert data["ok"] is False
        assert "error" in data
        assert "supported_types" in data
        assert "bill_for_review" in data["supported_types"]
        assert "statement_for_audit" in data["supported_types"]

    def test_bill_review_returns_recommendation(self):
        """Test that bill review includes recommendation."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "bill_for_review",
                "payload": {
                    "bill_id": "BILL-TEST-002",
                    "text": "A clear policy document with well-defined objectives."
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        result = data["result"]
        assert "recommendation" in result
        assert result["recommendation"] in ["approve", "reject", "revise"]
        assert "notes" in result

    def test_bill_review_returns_audit_structure(self):
        """Test that bill review includes full audit structure."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "bill_for_review",
                "payload": {
                    "bill_id": "BILL-TEST-003",
                    "text": "The proposed regulation aims to improve transparency."
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        result = data["result"]

        # Check audit structure
        assert "audit" in result
        audit = result["audit"]
        assert "audit" in audit  # AuditWithSourcesResult.audit
        assert "retrieved_docs" in audit
        assert "source_validation" in audit

    def test_statement_review_returns_audit_structure(self):
        """Test that statement review includes full audit structure."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "statement_for_audit",
                "payload": {
                    "statement_id": "STMT-TEST-002",
                    "text": "Economic indicators show positive trends."
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        result = data["result"]

        # Check audit structure
        assert "audit" in result
        audit = result["audit"]
        assert "audit" in audit
        inner_audit = audit["audit"]
        assert "original_text" in inner_audit
        assert "logical_issues" in inner_audit
        assert "bias_flags" in inner_audit
        assert "confidence" in inner_audit

    def test_empty_text_returns_error(self):
        """Test that empty text returns error in result."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "bill_for_review",
                "payload": {
                    "bill_id": "BILL-EMPTY",
                    "text": ""
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        # Error should be in the result, not a 400
        assert "error" in data["result"]

    def test_biased_text_gets_appropriate_recommendation(self):
        """Test that biased text gets reject or revise."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "bill_for_review",
                "payload": {
                    "bill_id": "BILL-BIASED",
                    "text": """
                    This TERRIBLE policy will DESTROY everything!
                    OBVIOUSLY this is COMPLETELY wrong!
                    Everyone KNOWS we MUST reject this IMMEDIATELY!
                    """
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        result = data["result"]
        # Should recommend reject or revise
        assert result["recommendation"] in ["reject", "revise"]


class TestStatusEndpoint:
    """Tests for /status endpoint updates."""

    def test_status_shows_phase_8(self):
        """Test that status shows phase 8."""
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert data["phase"] == 9
        assert data["version"] == "0.9.0"

    def test_status_shows_congress_integration(self):
        """Test that status shows Congress integration active."""
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert "congress_integration" in data["components"]
        assert data["components"]["congress_integration"] == "active"

    def test_status_shows_structured_output(self):
        """Test that status shows structured output active."""
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert "structured_output" in data["components"]
        assert data["components"]["structured_output"] == "active"

    def test_status_shows_tools_list(self):
        """Test that status includes tools list."""
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "review_bill" in data["tools"]
        assert "review_statement" in data["tools"]


class TestIntegrationWithExistingEvents:
    """Tests for integration with existing event system."""

    def test_new_event_endpoint_coexists_with_standard_event(self):
        """Test that /event/congress coexists with /event."""
        # Test standard /event endpoint still works
        response = client.post(
            "/event",
            json={
                "event_type": "audit-request",
                "source": "test-suite",
                "payload": {
                    "text": "Test text for audit."
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_congress_event_does_not_interfere_with_legacy(self):
        """Test that Congress events don't interfere with legacy events."""
        # Test legacy endpoint still works
        response = client.post(
            "/event/legacy",
            json={
                "event_type": "audit",
                "data": {
                    "text": "Test text."
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True


class TestCongressReviewNotes:
    """Tests for advisory notes in Congress reviews."""

    def test_notes_include_advisory_prefix(self):
        """Test that notes include ADVISORY prefix."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "bill_for_review",
                "payload": {
                    "bill_id": "BILL-ADV",
                    "text": "A policy document for testing advisory notes."
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        result = data["result"]
        assert "ADVISORY" in result["notes"]

    def test_notes_describe_issues(self):
        """Test that notes describe found issues."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "bill_for_review",
                "payload": {
                    "bill_id": "BILL-ISSUES",
                    "text": """
                    This HORRIBLE policy is OBVIOUSLY terrible!
                    Everyone KNOWS this will DESTROY everything!
                    """
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        result = data["result"]
        # Notes should mention something about issues or bias
        assert len(result["notes"]) > 20  # Non-trivial notes
