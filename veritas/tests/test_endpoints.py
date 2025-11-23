"""
Veritas API Endpoint Tests

This module tests all API endpoints for proper response codes and JSON structure.
Phase 6: Tests for VeritasBrain integration, Event API, and Legislative functions.
"""

import pytest


class TestRootEndpoints:
    """Tests for root-level endpoints."""

    def test_root(self, client):
        """Test the root endpoint returns service information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "status" in data

    def test_health_check(self, client):
        """Test the health check endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data


class TestVeritasEndpoints:
    """Tests for Veritas-specific endpoints."""

    def test_status(self, client):
        """Test the status endpoint returns component status."""
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert data["ok"] is True
        assert "components" in data
        assert data["components"]["brain"] == "active"
        assert data["components"]["auditor"] == "active"
        assert data["components"]["bias_detector"] == "active"
        assert data["components"]["rag"] == "active"
        assert data["components"]["event_api"] == "active"
        assert data["components"]["legislative"] == "active"
        assert data["phase"] == 6

    def test_run_task_audit(self, client):
        """Test the run_task endpoint with audit_text task."""
        response = client.post(
            "/run_task",
            json={
                "task_type": "audit_text",
                "payload": {"text": "This is a test statement."}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert data["ok"] is True
        assert data["task_type"] == "audit_text"
        assert "summary" in data
        assert "details" in data

    def test_run_task_with_text_returns_summary(self, client):
        """Test that run_task with text returns proper summary structure."""
        response = client.post(
            "/run_task",
            json={
                "task_type": "audit_text",
                "payload": {"text": "Simple test text"}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "has_major_issues" in data["summary"]
        assert "issue_types" in data["summary"]
        assert "confidence_estimate" in data["summary"]

    def test_run_task_with_steps_returns_chain_validation(self, client):
        """Test that run_task with steps returns chain validation."""
        response = client.post(
            "/run_task",
            json={
                "task_type": "validate_chain",
                "payload": {"steps": ["Step A", "Step B"]}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["task_type"] == "validate_chain"
        assert data["details"]["chain"] is not None

    def test_run_task_with_sources_returns_source_check(self, client):
        """Test that run_task with sources returns source check."""
        response = client.post(
            "/run_task",
            json={
                "task_type": "check_sources",
                "payload": {"sources": ["http://example.com"]}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["task_type"] == "check_sources"
        assert data["details"]["sources"] is not None

    def test_run_task_composite(self, client):
        """Test that run_task handles composite payloads."""
        response = client.post(
            "/run_task",
            json={
                "task_type": "composite",
                "payload": {
                    "text": "Test text",
                    "steps": ["A", "B"],
                    "sources": ["http://example.com"]
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["task_type"] == "composite_audit"
        assert data["details"]["audit"] is not None
        assert data["details"]["chain"] is not None
        assert data["details"]["sources"] is not None

    def test_shutdown(self, client):
        """Test the shutdown endpoint returns response."""
        response = client.post("/shutdown")
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert data["ok"] is True

    def test_event(self, client):
        """Test the event endpoint accepts event submissions (Phase 5 format)."""
        response = client.post(
            "/event",
            json={
                "event_type": "audit-request",
                "source": "test",
                "payload": {"text": "Test text"}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert data["ok"] is True
        assert "event_type" in data

    def test_event_analyze_processes_data(self, client):
        """Test the legacy event endpoint processes analyze events."""
        response = client.post(
            "/event/legacy",
            json={"event_type": "analyze", "data": {"text": "Text to analyze"}}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["processed"] is True
        assert "summary" in data
        assert "details" in data

    def test_event_audit_processes_data(self, client):
        """Test the legacy event endpoint processes audit events."""
        response = client.post(
            "/event/legacy",
            json={"event_type": "audit", "data": {"text": "Text to audit"}}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["processed"] is True

    def test_event_non_processable_logged_only(self, client):
        """Test non-processable events are logged but not processed."""
        response = client.post(
            "/event/legacy",
            json={"event_type": "notification", "data": {"msg": "info"}}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["processed"] is False
        assert "message" in data


class TestAuditTextEndpoint:
    """Tests for the audit_text endpoint."""

    def test_audit_text_basic(self, client):
        """Test audit_text endpoint returns analysis results."""
        response = client.post(
            "/audit_text",
            json={"text": "This is a test statement that makes a claim."}
        )
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert data["ok"] is True
        assert "claims" in data
        assert "logical_fallacies" in data
        assert "inconsistencies" in data
        assert "unsupported_jumps" in data
        assert isinstance(data["claims"], list)
        assert isinstance(data["logical_fallacies"], list)

    def test_audit_text_detects_fallacy(self, client):
        """Test audit_text detects logical fallacies."""
        response = client.post(
            "/audit_text",
            json={"text": "You are stupid, therefore your argument is wrong."}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["logical_fallacies"]) > 0

    def test_audit_text_empty(self, client):
        """Test audit_text handles empty text."""
        response = client.post(
            "/audit_text",
            json={"text": ""}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["claims"] == []
        assert data["logical_fallacies"] == []

    def test_audit_text_extracts_claims(self, client):
        """Test audit_text extracts claims from text."""
        response = client.post(
            "/audit_text",
            json={"text": "The sky is blue. Water is wet. All humans need oxygen."}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["claims"]) > 0


class TestDetectBiasEndpoint:
    """Tests for the detect_bias endpoint."""

    def test_detect_bias_basic(self, client):
        """Test detect_bias endpoint returns bias scores."""
        response = client.post(
            "/detect_bias",
            json={"text": "This is a neutral statement."}
        )
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert data["ok"] is True
        assert "political_bias" in data
        assert "emotional_bias" in data
        assert "motivational_bias" in data
        assert "certainty_overconfidence" in data

    def test_detect_bias_scores_are_floats(self, client):
        """Test that bias scores are floats between 0 and 1."""
        response = client.post(
            "/detect_bias",
            json={"text": "This is absolutely amazing and incredible!"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["political_bias"], float)
        assert isinstance(data["emotional_bias"], float)
        assert 0.0 <= data["political_bias"] <= 1.0
        assert 0.0 <= data["emotional_bias"] <= 1.0

    def test_detect_bias_emotional_content(self, client):
        """Test detect_bias flags emotional content."""
        response = client.post(
            "/detect_bias",
            json={"text": "This is absolutely terrible and disgusting! A complete disaster!"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["emotional_bias"] > 0.0

    def test_detect_bias_certainty_markers(self, client):
        """Test detect_bias flags certainty markers."""
        response = client.post(
            "/detect_bias",
            json={"text": "Obviously this is true. Clearly everyone knows this. Undoubtedly correct."}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["certainty_overconfidence"] > 0.0

    def test_detect_bias_empty(self, client):
        """Test detect_bias handles empty text."""
        response = client.post(
            "/detect_bias",
            json={"text": ""}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["political_bias"] == 0.0
        assert data["emotional_bias"] == 0.0


class TestValidateChainEndpoint:
    """Tests for the validate_chain endpoint."""

    def test_validate_chain_basic(self, client):
        """Test validate_chain endpoint returns validation results."""
        response = client.post(
            "/validate_chain",
            json={
                "chain": ["Premise one", "Therefore, conclusion"],
                "context": "Test context"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert data["ok"] is True
        assert "gaps" in data
        assert "contradictions" in data
        assert "circular_logic" in data
        assert "flawed_premises" in data
        assert isinstance(data["gaps"], list)

    def test_validate_chain_empty(self, client):
        """Test validate_chain handles empty chain."""
        response = client.post(
            "/validate_chain",
            json={"chain": []}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["chain_length"] == 0
        assert data["gaps"] == []

    def test_validate_chain_detects_flawed_premise(self, client):
        """Test validate_chain detects flawed premises."""
        response = client.post(
            "/validate_chain",
            json={
                "chain": [
                    "Assume that all birds can fly",
                    "Penguins are birds",
                    "Therefore penguins can fly"
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        # Should detect assumption in first premise
        assert len(data["flawed_premises"]) > 0


class TestCheckSourcesEndpoint:
    """Tests for the check_sources endpoint."""

    def test_check_sources_basic(self, client):
        """Test check_sources endpoint returns check results."""
        response = client.post(
            "/check_sources",
            json={
                "sources": ["https://example.com/article"],
                "claims": ["Test claim"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert data["ok"] is True
        assert "missing_sources" in data
        assert "unverifiable" in data
        assert "ranked_confidence" in data
        assert isinstance(data["ranked_confidence"], list)

    def test_check_sources_empty(self, client):
        """Test check_sources handles empty sources list."""
        response = client.post(
            "/check_sources",
            json={"sources": []}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sources_count"] == 0

    def test_check_sources_trusted_domain(self, client):
        """Test check_sources gives high score to trusted domains."""
        response = client.post(
            "/check_sources",
            json={"sources": ["https://www.nature.com/articles/test"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["ranked_confidence"]) > 0
        assert data["ranked_confidence"][0]["confidence"] >= 0.7

    def test_check_sources_invalid_url(self, client):
        """Test check_sources handles invalid URLs."""
        response = client.post(
            "/check_sources",
            json={"sources": ["not a valid url", "also invalid"]}
        )
        assert response.status_code == 200
        data = response.json()
        # Should classify as unverifiable or low confidence
        assert (len(data["unverifiable"]) > 0 or
                all(s["confidence"] < 0.5 for s in data["ranked_confidence"]))


class TestEndpointValidation:
    """Tests for endpoint input validation."""

    def test_run_task_requires_task_type(self, client):
        """Test that run_task requires task_type field."""
        response = client.post("/run_task", json={"payload": {}})
        assert response.status_code == 422

    def test_audit_text_requires_text(self, client):
        """Test that audit_text requires text field."""
        response = client.post("/audit_text", json={})
        assert response.status_code == 422

    def test_detect_bias_requires_text(self, client):
        """Test that detect_bias requires text field."""
        response = client.post("/detect_bias", json={})
        assert response.status_code == 422

    def test_validate_chain_requires_chain(self, client):
        """Test that validate_chain requires chain field."""
        response = client.post("/validate_chain", json={"context": "test"})
        assert response.status_code == 422

    def test_check_sources_requires_sources(self, client):
        """Test that check_sources requires sources field."""
        response = client.post("/check_sources", json={"claims": []})
        assert response.status_code == 422
