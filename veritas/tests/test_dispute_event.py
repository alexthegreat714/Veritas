"""
Tests for Veritas Phase 5 Dispute Event Handling

Tests for /event/congress with dispute_for_analysis event type.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.tools import tool_parse_dispute


client = TestClient(app)


class TestDisputeEventEndpoint:
    """Tests for /event/congress with dispute_for_analysis."""

    def test_dispute_for_analysis_basic(self):
        """Test basic dispute analysis event."""
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
                        "agent": "Aegis",
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
        assert "result" in data

    def test_dispute_returns_expected_structure(self):
        """Test dispute analysis returns expected structure."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "dispute_for_analysis",
                "payload": {
                    "agent_A": {
                        "agent": "Mercury",
                        "text": "Position A.",
                        "metadata": {}
                    },
                    "agent_B": {
                        "agent": "Apollo",
                        "text": "Position B.",
                        "metadata": {}
                    }
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        result = data["result"]

        assert "agents" in result
        assert "issues" in result
        assert "needs_escalation" in result
        assert "recommendation" in result
        assert "analysis" in result

    def test_dispute_returns_agent_names(self):
        """Test dispute returns correct agent names."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "dispute_for_analysis",
                "payload": {
                    "agent_A": {
                        "agent": "Aero",
                        "text": "Aero's position.",
                        "metadata": {}
                    },
                    "agent_B": {
                        "agent": "Veritas",
                        "text": "Veritas's position.",
                        "metadata": {}
                    }
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["result"]["agents"] == ["Aero", "Veritas"]

    def test_dispute_with_contradictory_claims(self):
        """Test dispute with contradictory claims."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "dispute_for_analysis",
                "payload": {
                    "agent_A": {
                        "agent": "Sky",
                        "text": "The system is secure.",
                        "metadata": {}
                    },
                    "agent_B": {
                        "agent": "Aegis",
                        "text": "The system is not secure.",
                        "metadata": {}
                    }
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        result = data["result"]

        # Should detect factual disagreement
        assert result["issues"]["factual_disagreement"] is True

    def test_dispute_escalation_to_sophia(self):
        """Test dispute escalation to Sophia for ethical content."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "dispute_for_analysis",
                "payload": {
                    "agent_A": {
                        "agent": "Sky",
                        "text": "This raises ethical concerns about moral rights.",
                        "metadata": {}
                    },
                    "agent_B": {
                        "agent": "Mercury",
                        "text": "The legal and justice implications are significant.",
                        "metadata": {}
                    }
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["result"]["needs_escalation"] == "sophia"
        assert data["result"]["recommendation"] == "forward_to_sophia"

    def test_dispute_escalation_to_aegis(self):
        """Test dispute escalation to Aegis for security content."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "dispute_for_analysis",
                "payload": {
                    "agent_A": {
                        "agent": "Sky",
                        "text": "Security vulnerability detected in the system.",
                        "metadata": {}
                    },
                    "agent_B": {
                        "agent": "Mercury",
                        "text": "The threat level is dangerous and could cause damage.",
                        "metadata": {}
                    }
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["result"]["needs_escalation"] == "aegis"
        assert data["result"]["recommendation"] == "forward_to_aegis"

    def test_dispute_escalation_to_congress(self):
        """Test dispute escalation to Congress for political content."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "dispute_for_analysis",
                "payload": {
                    "agent_A": {
                        "agent": "Sky",
                        "text": "The policy change affects budget allocation.",
                        "metadata": {}
                    },
                    "agent_B": {
                        "agent": "Mercury",
                        "text": "This political decision requires legislative authority.",
                        "metadata": {}
                    }
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["result"]["needs_escalation"] == "congress"
        assert data["result"]["recommendation"] == "mediation_by_congress"

    def test_dispute_with_missing_data(self):
        """Test dispute with missing data."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "dispute_for_analysis",
                "payload": {
                    "agent_A": {
                        "agent": "Sky",
                        "text": "",
                        "metadata": {}
                    },
                    "agent_B": {
                        "agent": "Mercury",
                        "text": "Valid position.",
                        "metadata": {}
                    }
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        # Should request more data due to empty text
        assert data["result"]["recommendation"] == "request_more_data"

    def test_dispute_stores_analysis(self):
        """Test that dispute analysis is stored."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "dispute_for_analysis",
                "payload": {
                    "agent_A": {
                        "agent": "Sky",
                        "text": "Position A for storage test.",
                        "metadata": {}
                    },
                    "agent_B": {
                        "agent": "Mercury",
                        "text": "Position B for storage test.",
                        "metadata": {}
                    }
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        result = data["result"]

        # Should have storage info
        assert "storage" in result
        assert result["storage"]["stored"] is True


class TestToolParseDispute:
    """Tests for tool_parse_dispute function directly."""

    def test_tool_parse_dispute_basic(self):
        """Test tool_parse_dispute basic functionality."""
        payload = {
            "agent_A": {
                "agent": "Sky",
                "text": "Test position A.",
                "metadata": {}
            },
            "agent_B": {
                "agent": "Mercury",
                "text": "Test position B.",
                "metadata": {}
            }
        }

        result = tool_parse_dispute(payload)

        assert "agents" in result
        assert "issues" in result
        assert "needs_escalation" in result
        assert "recommendation" in result

    def test_tool_parse_dispute_missing_agent_a(self):
        """Test tool_parse_dispute with missing agent_A."""
        payload = {
            "agent_B": {
                "agent": "Mercury",
                "text": "Position B.",
                "metadata": {}
            }
        }

        result = tool_parse_dispute(payload)

        assert "error" in result

    def test_tool_parse_dispute_missing_text(self):
        """Test tool_parse_dispute with missing text."""
        payload = {
            "agent_A": {
                "agent": "Sky",
                "text": "",
                "metadata": {}
            },
            "agent_B": {
                "agent": "Mercury",
                "text": "Position B.",
                "metadata": {}
            }
        }

        result = tool_parse_dispute(payload)

        assert result["recommendation"] == "request_more_data"


class TestStatusEndpoint:
    """Tests for /status endpoint updates."""

    def test_status_shows_phase_8(self):
        """Test that status shows phase 8."""
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert data["phase"] == 8
        assert data["version"] == "0.8.0"

    def test_status_shows_dispute_engine(self):
        """Test that status shows dispute_engine active."""
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert "dispute_engine" in data["components"]
        assert data["components"]["dispute_engine"] == "active"

    def test_status_shows_parse_dispute_tool(self):
        """Test that status includes parse_dispute in tools list."""
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert "parse_dispute" in data["tools"]


class TestDisputeRecommendationValues:
    """Tests for valid recommendation values."""

    def test_valid_recommendation_values(self):
        """Test that recommendations are valid values."""
        valid_recommendations = [
            "request_more_data",
            "forward_to_sophia",
            "forward_to_aegis",
            "mediation_by_congress",
            "minimal_issue_detected",
            "inconclusive",
        ]

        response = client.post(
            "/event/congress",
            json={
                "event_type": "dispute_for_analysis",
                "payload": {
                    "agent_A": {"agent": "Sky", "text": "Position A.", "metadata": {}},
                    "agent_B": {"agent": "Mercury", "text": "Position B.", "metadata": {}}
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["result"]["recommendation"] in valid_recommendations


class TestDisputeEscalationValues:
    """Tests for valid escalation values."""

    def test_valid_escalation_values(self):
        """Test that escalation is one of valid values."""
        valid_escalations = ["none", "sophia", "aegis", "congress"]

        response = client.post(
            "/event/congress",
            json={
                "event_type": "dispute_for_analysis",
                "payload": {
                    "agent_A": {"agent": "Sky", "text": "Position A.", "metadata": {}},
                    "agent_B": {"agent": "Mercury", "text": "Position B.", "metadata": {}}
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["result"]["needs_escalation"] in valid_escalations


class TestDisputeVeritasDoesNotEscalate:
    """Tests to verify Veritas does NOT actually escalate."""

    def test_veritas_only_reports_escalation_need(self):
        """Test that Veritas only reports, doesn't escalate."""
        response = client.post(
            "/event/congress",
            json={
                "event_type": "dispute_for_analysis",
                "payload": {
                    "agent_A": {
                        "agent": "Sky",
                        "text": "Security threat with dangerous vulnerability.",
                        "metadata": {}
                    },
                    "agent_B": {
                        "agent": "Mercury",
                        "text": "Attack and breach detected.",
                        "metadata": {}
                    }
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        result = data["result"]

        # Veritas reports escalation need
        assert result["needs_escalation"] == "aegis"

        # But the response is just data - no actual escalation happens
        # The result is returned to the caller who decides what to do
        assert "ok" in data
        assert data["ok"] is True
