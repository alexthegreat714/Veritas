"""
Veritas API Endpoint Tests

This module tests all API endpoints for proper response codes and JSON structure.
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
        assert "message" in data
        assert "components" in data

    def test_run_task(self, client):
        """Test the run_task endpoint accepts task requests."""
        response = client.post(
            "/run_task",
            json={"task_type": "test_task", "payload": {"key": "value"}}
        )
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert data["ok"] is True
        assert "message" in data
        assert data["task_type"] == "test_task"

    def test_shutdown(self, client):
        """Test the shutdown endpoint returns stub response."""
        response = client.post("/shutdown")
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert data["ok"] is True
        assert "message" in data

    def test_event(self, client):
        """Test the event endpoint accepts event submissions."""
        response = client.post(
            "/event",
            json={"event_type": "test_event", "data": {"info": "test"}}
        )
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert data["ok"] is True
        assert "event_type" in data

    def test_audit_text(self, client):
        """Test the audit_text endpoint accepts text for auditing."""
        response = client.post(
            "/audit_text",
            json={"text": "This is a test statement to audit."}
        )
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert data["ok"] is True
        assert "audit_result" in data
        assert "text_length" in data

    def test_validate_chain(self, client):
        """Test the validate_chain endpoint accepts reasoning chains."""
        response = client.post(
            "/validate_chain",
            json={
                "chain": ["Premise 1", "Therefore, Conclusion"],
                "context": "Test context"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert data["ok"] is True
        assert "validation_result" in data
        assert "chain_length" in data
        assert data["chain_length"] == 2

    def test_check_sources(self, client):
        """Test the check_sources endpoint accepts source lists."""
        response = client.post(
            "/check_sources",
            json={
                "sources": ["https://example.com/source1", "https://example.com/source2"],
                "claims": ["Test claim 1"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert data["ok"] is True
        assert "check_result" in data
        assert "sources_count" in data
        assert data["sources_count"] == 2


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

    def test_validate_chain_requires_chain(self, client):
        """Test that validate_chain requires chain field."""
        response = client.post("/validate_chain", json={"context": "test"})
        assert response.status_code == 422

    def test_check_sources_requires_sources(self, client):
        """Test that check_sources requires sources field."""
        response = client.post("/check_sources", json={"claims": []})
        assert response.status_code == 422
