"""
Tests for Veritas Phase 5 - Event API

Tests the standardized event handling for inter-agent communication.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.logic.brain import VeritasBrain, get_brain


client = TestClient(app)


class TestAuditRequestEvent:
    """Tests for audit-request event type."""

    def test_audit_request_basic(self):
        """Test basic audit-request event."""
        response = client.post("/event", json={
            "event_type": "audit-request",
            "source": "sky",
            "payload": {"text": "This is a test statement."}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["event_type"] == "audit-request"
        assert "result" in data
        assert "summary" in data["result"]
        assert "details" in data["result"]

    def test_audit_request_with_correlation_id(self):
        """Test that correlation_id is echoed back."""
        response = client.post("/event", json={
            "event_type": "audit-request",
            "source": "sky",
            "payload": {"text": "Test text"},
            "correlation_id": "test-123-abc"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["correlation_id"] == "test-123-abc"

    def test_audit_request_detects_fallacy(self):
        """Test that audit-request detects logical fallacies."""
        response = client.post("/event", json={
            "event_type": "audit-request",
            "source": "sky",
            # Use text that triggers ad hominem detection: "you are X so Y" pattern
            "payload": {"text": "You are stupid, therefore your argument is invalid."}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        # Should detect ad hominem or at least unsupported claims
        audit = data["result"]["details"]["audit"]
        # Check for any detected issues (fallacies or unsupported jumps)
        has_issues = (
            len(audit["logical_fallacies"]) > 0 or
            len(audit["unsupported_jumps"]) > 0
        )
        assert has_issues, "Expected fallacies or unsupported jumps to be detected"

    def test_audit_request_from_different_sources(self):
        """Test events from different source agents."""
        for source in ["sky", "apollo", "mercury", "congress"]:
            response = client.post("/event", json={
                "event_type": "audit-request",
                "source": source,
                "payload": {"text": "Test from " + source}
            })
            assert response.status_code == 200
            assert response.json()["ok"] is True


class TestBillLogicCheckEvent:
    """Tests for bill-logic-check event type."""

    def test_bill_logic_check_with_bill_text(self):
        """Test bill-logic-check using bill_text field."""
        response = client.post("/event", json={
            "event_type": "bill-logic-check",
            "source": "congress",
            "payload": {
                "bill_text": "All citizens must pay taxes. Tax evaders will be punished."
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["event_type"] == "bill-logic-check"
        assert data["result"]["task_type"] == "audit_text"

    def test_bill_logic_check_with_text_field(self):
        """Test bill-logic-check using text field instead of bill_text."""
        response = client.post("/event", json={
            "event_type": "bill-logic-check",
            "source": "congress",
            "payload": {
                "text": "This bill proposes new regulations."
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_bill_logic_check_detects_bias(self):
        """Test that bill-logic-check detects emotional bias."""
        response = client.post("/event", json={
            "event_type": "bill-logic-check",
            "source": "congress",
            "payload": {
                "bill_text": "This absolutely terrible law must be stopped! "
                             "Obviously everyone knows this is wrong and dangerous!"
            }
        })
        assert response.status_code == 200
        data = response.json()
        bias = data["result"]["details"]["bias"]
        assert bias["emotional_bias"] > 0.3
        assert bias["certainty_overconfidence"] > 0.3


class TestArgumentIntegrityCheckEvent:
    """Tests for argument-integrity-check event type."""

    def test_argument_integrity_basic(self):
        """Test basic argument-integrity-check event."""
        response = client.post("/event", json={
            "event_type": "argument-integrity-check",
            "source": "apollo",
            "payload": {
                "steps": [
                    "All mammals are warm-blooded",
                    "Dogs are mammals",
                    "Therefore dogs are warm-blooded"
                ]
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["event_type"] == "argument-integrity-check"
        assert data["result"]["task_type"] == "validate_chain"
        assert data["result"]["details"]["chain"] is not None

    def test_argument_integrity_with_chain_key(self):
        """Test argument-integrity-check using chain key instead of steps."""
        response = client.post("/event", json={
            "event_type": "argument-integrity-check",
            "source": "mercury",
            "payload": {
                "chain": [
                    "Premise A",
                    "Premise B",
                    "Conclusion C"
                ]
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["details"]["chain"] is not None

    def test_argument_integrity_detects_flawed_premise(self):
        """Test that flawed premises are detected."""
        response = client.post("/event", json={
            "event_type": "argument-integrity-check",
            "source": "aero",
            "payload": {
                "steps": [
                    "Assume that all politicians are corrupt",
                    "John is a politician",
                    "Therefore John is corrupt"
                ]
            }
        })
        assert response.status_code == 200
        data = response.json()
        chain = data["result"]["details"]["chain"]
        assert len(chain["flawed_premises"]) > 0


class TestSourceIntegrityCheckEvent:
    """Tests for source-integrity-check event type."""

    def test_source_integrity_basic(self):
        """Test basic source-integrity-check event."""
        response = client.post("/event", json={
            "event_type": "source-integrity-check",
            "source": "apollo",
            "payload": {
                "sources": [
                    "https://www.nature.com/articles/test",
                    "https://www.reuters.com/article/test"
                ]
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["event_type"] == "source-integrity-check"
        assert data["result"]["task_type"] == "check_sources"
        assert data["result"]["details"]["sources"] is not None

    def test_source_integrity_ranks_confidence(self):
        """Test that sources are ranked by confidence."""
        response = client.post("/event", json={
            "event_type": "source-integrity-check",
            "source": "mercury",
            "payload": {
                "sources": [
                    "https://www.nature.com/articles/test",
                    "https://random-blog.blogspot.com/post"
                ]
            }
        })
        assert response.status_code == 200
        data = response.json()
        sources = data["result"]["details"]["sources"]
        ranked = sources["ranked_confidence"]
        # Nature should have higher confidence than blogspot
        nature_conf = next(r["confidence"] for r in ranked if "nature.com" in r["source"])
        blog_conf = next(r["confidence"] for r in ranked if "blogspot" in r["source"])
        assert nature_conf > blog_conf

    def test_source_integrity_detects_invalid(self):
        """Test that invalid sources are detected."""
        response = client.post("/event", json={
            "event_type": "source-integrity-check",
            "source": "congress",
            "payload": {
                "sources": [
                    "not a valid url",
                    "https://valid.com/page"
                ]
            }
        })
        assert response.status_code == 200
        data = response.json()
        sources = data["result"]["details"]["sources"]
        assert len(sources["unverifiable"]) > 0


class TestCompositeAuditEvent:
    """Tests for composite-audit event type."""

    def test_composite_audit_text_and_sources(self):
        """Test composite-audit with text and sources."""
        response = client.post("/event", json={
            "event_type": "composite-audit",
            "source": "sky",
            "payload": {
                "text": "Climate change is real and requires immediate action.",
                "sources": [
                    "https://www.nature.com/climate",
                    "https://www.ipcc.ch/report"
                ]
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["task_type"] == "composite_audit"
        assert data["result"]["details"]["audit"] is not None
        assert data["result"]["details"]["sources"] is not None

    def test_composite_audit_text_and_steps(self):
        """Test composite-audit with text and reasoning steps."""
        response = client.post("/event", json={
            "event_type": "composite-audit",
            "source": "sky",
            "payload": {
                "text": "The economy is improving based on GDP growth.",
                "steps": [
                    "GDP increased by 3%",
                    "Unemployment decreased",
                    "Therefore the economy is improving"
                ]
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["task_type"] == "composite_audit"
        assert data["result"]["details"]["audit"] is not None
        assert data["result"]["details"]["chain"] is not None

    def test_composite_audit_all_three(self):
        """Test composite-audit with text, steps, and sources."""
        response = client.post("/event", json={
            "event_type": "composite-audit",
            "source": "sky",
            "payload": {
                "text": "Vaccines are safe and effective.",
                "steps": [
                    "Clinical trials showed efficacy",
                    "Side effects are rare",
                    "Benefits outweigh risks"
                ],
                "sources": [
                    "https://www.cdc.gov/vaccines",
                    "https://www.who.int/vaccines"
                ]
            },
            "correlation_id": "composite-test-456"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["correlation_id"] == "composite-test-456"
        assert data["result"]["details"]["audit"] is not None
        assert data["result"]["details"]["bias"] is not None
        assert data["result"]["details"]["chain"] is not None
        assert data["result"]["details"]["sources"] is not None


class TestUnknownEventType:
    """Tests for unknown/invalid event types."""

    def test_unknown_event_type_returns_error(self):
        """Test that unknown event type returns ok=False."""
        response = client.post("/event", json={
            "event_type": "unknown-event",
            "source": "test",
            "payload": {"text": "test"}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert data["event_type"] == "unknown-event"
        assert "error" in data["result"]
        assert "Unknown event_type" in data["result"]["error"]

    def test_invalid_event_type_lists_valid_options(self):
        """Test that error message lists valid event types."""
        response = client.post("/event", json={
            "event_type": "invalid-type",
            "source": "test",
            "payload": {}
        })
        data = response.json()
        assert data["ok"] is False
        error_msg = data["result"]["error"]
        assert "audit-request" in error_msg or "Valid types" in error_msg


class TestEventValidation:
    """Tests for event request validation."""

    def test_missing_event_type_fails(self):
        """Test that missing event_type fails validation."""
        response = client.post("/event", json={
            "source": "sky",
            "payload": {"text": "test"}
        })
        assert response.status_code == 422  # Validation error

    def test_missing_source_fails(self):
        """Test that missing source fails validation."""
        response = client.post("/event", json={
            "event_type": "audit-request",
            "payload": {"text": "test"}
        })
        assert response.status_code == 422  # Validation error

    def test_empty_payload_allowed(self):
        """Test that empty payload is allowed."""
        response = client.post("/event", json={
            "event_type": "audit-request",
            "source": "sky",
            "payload": {}
        })
        assert response.status_code == 200
        assert response.json()["ok"] is True


class TestBrainHandleEvent:
    """Direct tests for VeritasBrain.handle_event method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.brain = VeritasBrain()

    def test_handle_event_audit_request(self):
        """Test handle_event with audit-request."""
        result = self.brain.handle_event(
            "audit-request",
            {"text": "Test statement"},
            "test-source"
        )
        assert result["ok"] is True
        assert result["task_type"] == "audit_text"
        assert "summary" in result
        assert "details" in result

    def test_handle_event_bill_logic_check(self):
        """Test handle_event with bill-logic-check."""
        result = self.brain.handle_event(
            "bill-logic-check",
            {"bill_text": "This bill proposes..."},
            "congress"
        )
        assert result["ok"] is True
        assert result["task_type"] == "audit_text"

    def test_handle_event_argument_integrity(self):
        """Test handle_event with argument-integrity-check."""
        result = self.brain.handle_event(
            "argument-integrity-check",
            {"steps": ["Step 1", "Step 2", "Conclusion"]},
            "apollo"
        )
        assert result["ok"] is True
        assert result["task_type"] == "validate_chain"

    def test_handle_event_source_integrity(self):
        """Test handle_event with source-integrity-check."""
        result = self.brain.handle_event(
            "source-integrity-check",
            {"sources": ["https://example.com"]},
            "mercury"
        )
        assert result["ok"] is True
        assert result["task_type"] == "check_sources"

    def test_handle_event_composite(self):
        """Test handle_event with composite-audit."""
        result = self.brain.handle_event(
            "composite-audit",
            {
                "text": "Test text",
                "sources": ["https://example.com"]
            },
            "sky"
        )
        assert result["ok"] is True
        assert result["task_type"] == "composite_audit"

    def test_handle_event_unknown_raises_error(self):
        """Test that unknown event type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            self.brain.handle_event("unknown-type", {}, "test")
        assert "Unknown event_type" in str(exc_info.value)

    def test_handle_event_valid_types(self):
        """Test all valid event types are handled."""
        valid_types = [
            "audit-request",
            "bill-logic-check",
            "argument-integrity-check",
            "source-integrity-check",
            "composite-audit"
        ]
        for event_type in valid_types:
            result = self.brain.handle_event(event_type, {"text": "test"}, "test")
            assert result["ok"] is True


class TestEventResponseStructure:
    """Tests for VeritasResponse structure."""

    def test_response_has_required_fields(self):
        """Test that response has all required fields."""
        response = client.post("/event", json={
            "event_type": "audit-request",
            "source": "sky",
            "payload": {"text": "Test"}
        })
        data = response.json()
        assert "ok" in data
        assert "event_type" in data
        assert "correlation_id" in data
        assert "result" in data

    def test_result_has_summary_and_details(self):
        """Test that result contains summary and details."""
        response = client.post("/event", json={
            "event_type": "audit-request",
            "source": "sky",
            "payload": {"text": "Test statement"}
        })
        data = response.json()
        result = data["result"]
        assert "summary" in result
        assert "details" in result
        assert "task_type" in result

    def test_summary_has_issue_tracking(self):
        """Test that summary tracks issues."""
        response = client.post("/event", json={
            "event_type": "audit-request",
            "source": "sky",
            "payload": {"text": "You're stupid so you're wrong. Obviously!"}
        })
        data = response.json()
        summary = data["result"]["summary"]
        assert "has_major_issues" in summary
        assert "issue_types" in summary
        assert "confidence_estimate" in summary


class TestLegacyEventEndpoint:
    """Tests for legacy /event/legacy endpoint."""

    def test_legacy_endpoint_still_works(self):
        """Test that legacy endpoint still functions."""
        response = client.post("/event/legacy", json={
            "event_type": "analyze",
            "data": {"text": "Test text for analysis"}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["processed"] is True

    def test_legacy_endpoint_logs_non_processable(self):
        """Test that legacy endpoint logs non-processable events."""
        response = client.post("/event/legacy", json={
            "event_type": "notification",
            "data": {"message": "Hello"}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["processed"] is False
