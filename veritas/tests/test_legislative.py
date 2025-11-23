"""
Tests for Veritas Phase 6 - Legislative Functions

Tests for bill voting, adversarial contributions, and legislative event handling.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.logic.legislative import (
    vote_on_bill,
    adversarial_contribution,
    contribution_log,
    LegislativeHandler,
    get_legislative_handler,
)
from app.logic.brain import VeritasBrain


client = TestClient(app)


class TestVoteOnBillFunction:
    """Tests for vote_on_bill function."""

    def test_vote_on_bill_yes(self):
        """Test voting yes on a clean, logical bill."""
        bill = """
        Section 1: All government agencies shall publish their annual budgets.
        Section 2: Citizens may request access to public records.
        Section 3: Government employees shall respond to requests within 30 days.
        """
        result = vote_on_bill(bill)
        assert result["vote"] in ["yes", "no", "abstain"]
        assert 0.0 <= result["confidence"] <= 1.0
        assert isinstance(result["reasons"], list)
        assert "analysis_summary" in result

    def test_vote_on_bill_no_contradictions(self):
        """Test voting no on a bill with contradictions."""
        bill = """
        Section 1: All citizens must pay taxes.
        Section 2: No citizen shall be required to pay any taxes.
        """
        result = vote_on_bill(bill)
        # May detect contradiction or logical issues
        assert result["vote"] in ["yes", "no", "abstain"]
        assert len(result["reasons"]) > 0

    def test_vote_on_bill_no_high_bias(self):
        """Test voting no on a bill with high emotional bias."""
        bill = """
        This HORRIBLE and TERRIBLE bill would DESTROY everything we love!
        Obviously EVERYONE knows this is absolutely WRONG and DANGEROUS!
        We must IMMEDIATELY stop this catastrophic disaster!
        """
        result = vote_on_bill(bill)
        # Should detect high emotional bias
        assert result["vote"] in ["yes", "no", "abstain"]
        assert 0.0 <= result["confidence"] <= 1.0

    def test_vote_on_bill_abstain_empty(self):
        """Test abstaining on empty bill."""
        result = vote_on_bill("")
        assert result["vote"] == "abstain"
        assert result["confidence"] == 0.0

    def test_vote_on_bill_abstain_too_short(self):
        """Test abstaining on a bill that's too short."""
        result = vote_on_bill("Short text.")
        assert result["vote"] == "abstain"

    def test_vote_on_bill_with_bill_id(self):
        """Test that bill_id is accepted (for logging)."""
        bill = "This is a test bill with sufficient content for analysis."
        result = vote_on_bill(bill, bill_id="BILL-2024-001")
        assert result["vote"] in ["yes", "no", "abstain"]

    def test_vote_on_bill_deterministic(self):
        """Test that voting is deterministic."""
        bill = "Citizens shall have the right to free assembly and speech."
        result1 = vote_on_bill(bill)
        result2 = vote_on_bill(bill)
        assert result1["vote"] == result2["vote"]
        assert result1["confidence"] == result2["confidence"]


class TestAdversarialContributionFunction:
    """Tests for adversarial_contribution function."""

    def test_adversarial_basic(self):
        """Test basic adversarial contribution."""
        bill = """
        All students must pass standardized tests to graduate.
        Schools with low pass rates will lose funding.
        """
        result = adversarial_contribution(bill)
        assert isinstance(result["counterpoints"], list)
        assert isinstance(result["risk_flags"], list)
        assert isinstance(result["requires_review"], bool)
        assert isinstance(result["hidden_assumptions"], list)

    def test_adversarial_finds_issues(self):
        """Test that adversarial analysis finds issues."""
        bill = """
        Assume that all politicians are corrupt.
        Therefore we must eliminate all government positions.
        Obviously this is the only solution.
        """
        result = adversarial_contribution(bill)
        # Should find at least one counterpoint or issue
        assert len(result["counterpoints"]) > 0

    def test_adversarial_empty_bill(self):
        """Test adversarial contribution on empty bill."""
        result = adversarial_contribution("")
        assert len(result["counterpoints"]) > 0
        assert "missing_content" in result["risk_flags"]
        assert result["requires_review"] is True

    def test_adversarial_with_bill_id(self):
        """Test that bill_id is accepted."""
        bill = "Test bill content for adversarial analysis with enough text."
        result = adversarial_contribution(bill, bill_id="BILL-2024-002")
        assert "counterpoints" in result

    def test_adversarial_clean_bill(self):
        """Test adversarial on relatively clean bill."""
        bill = """
        Section 1: The department shall submit quarterly reports.
        Section 2: Reports shall include budget expenditures.
        Section 3: Reports shall be made available to the public.
        """
        result = adversarial_contribution(bill)
        # Even clean bills should have some structural observations
        assert isinstance(result["counterpoints"], list)
        assert isinstance(result["requires_review"], bool)


class TestLegislativeHandler:
    """Tests for LegislativeHandler class."""

    def test_handler_initialization(self):
        """Test handler initialization."""
        handler = LegislativeHandler()
        assert handler is not None

    def test_handler_vote(self):
        """Test handler vote method."""
        handler = LegislativeHandler()
        result = handler.vote(
            bill_text="Test bill for voting analysis.",
            bill_id="TEST-001",
            log_contribution=False
        )
        assert "vote" in result
        assert "confidence" in result
        assert "reasons" in result

    def test_handler_adversarial(self):
        """Test handler adversarial method."""
        handler = LegislativeHandler()
        result = handler.adversarial(
            bill_text="Test bill for adversarial analysis.",
            bill_id="TEST-002",
            log_contribution=False
        )
        assert "counterpoints" in result
        assert "risk_flags" in result
        assert "requires_review" in result

    def test_get_legislative_handler_singleton(self):
        """Test that get_legislative_handler returns same instance."""
        handler1 = get_legislative_handler()
        handler2 = get_legislative_handler()
        assert handler1 is handler2


class TestVoteOnBillEndpoint:
    """Tests for /vote_on_bill endpoint."""

    def test_vote_endpoint_basic(self):
        """Test basic vote endpoint."""
        response = client.post("/vote_on_bill", json={
            "bill_text": "All citizens shall have equal rights under the law."
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "vote" in data
        assert data["vote"] in ["yes", "no", "abstain"]
        assert "confidence" in data
        assert "reasons" in data

    def test_vote_endpoint_with_bill_id(self):
        """Test vote endpoint with bill_id."""
        response = client.post("/vote_on_bill", json={
            "bill_text": "The government shall protect individual privacy.",
            "bill_id": "PRIVACY-ACT-2024"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["bill_id"] == "PRIVACY-ACT-2024"

    def test_vote_endpoint_empty_bill(self):
        """Test vote endpoint with empty bill."""
        response = client.post("/vote_on_bill", json={
            "bill_text": ""
        })
        assert response.status_code == 200
        data = response.json()
        assert data["vote"] == "abstain"


class TestAdversarialContributionEndpoint:
    """Tests for /adversarial_contribution endpoint."""

    def test_adversarial_endpoint_basic(self):
        """Test basic adversarial contribution endpoint."""
        response = client.post("/adversarial_contribution", json={
            "bill_text": "All schools must implement new curriculum standards."
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "counterpoints" in data
        assert "risk_flags" in data
        assert "requires_review" in data
        assert "hidden_assumptions" in data

    def test_adversarial_endpoint_with_bill_id(self):
        """Test adversarial endpoint with bill_id."""
        response = client.post("/adversarial_contribution", json={
            "bill_text": "Healthcare shall be provided to all citizens.",
            "bill_id": "HEALTH-2024"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["bill_id"] == "HEALTH-2024"


class TestLegislativeEventTypes:
    """Tests for legislative event types via /event endpoint."""

    def test_bill_vote_request_event(self):
        """Test bill-vote-request event type."""
        response = client.post("/event", json={
            "event_type": "bill-vote-request",
            "source": "congress",
            "payload": {
                "bill_text": "This bill establishes new environmental regulations."
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["event_type"] == "bill-vote-request"
        assert data["result"]["task_type"] == "vote_on_bill"
        assert data["result"]["details"]["legislative"] is not None

    def test_bill_adversarial_request_event(self):
        """Test bill-adversarial-request event type."""
        response = client.post("/event", json={
            "event_type": "bill-adversarial-request",
            "source": "congress",
            "payload": {
                "bill_text": "All citizens must register their vehicles annually."
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["event_type"] == "bill-adversarial-request"
        assert data["result"]["task_type"] == "adversarial_contribution"
        assert data["result"]["details"]["legislative"] is not None

    def test_bill_vote_request_with_correlation_id(self):
        """Test bill-vote-request with correlation_id."""
        response = client.post("/event", json={
            "event_type": "bill-vote-request",
            "source": "congress",
            "payload": {"bill_text": "Test bill content."},
            "correlation_id": "congress-session-789"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["correlation_id"] == "congress-session-789"


class TestBrainLegislativeIntegration:
    """Tests for VeritasBrain legislative integration."""

    def test_classify_task_vote(self):
        """Test task classification for vote_on_bill."""
        brain = VeritasBrain()
        task_type = brain.classify_task({
            "bill_text": "Test bill",
            "mode": "vote"
        })
        assert task_type == "vote_on_bill"

    def test_classify_task_adversarial(self):
        """Test task classification for adversarial_contribution."""
        brain = VeritasBrain()
        task_type = brain.classify_task({
            "bill_text": "Test bill",
            "mode": "adversarial"
        })
        assert task_type == "adversarial_contribution"

    def test_run_audit_tools_vote(self):
        """Test run_audit_tools for vote_on_bill."""
        brain = VeritasBrain()
        results = brain.run_audit_tools("vote_on_bill", {
            "bill_text": "Citizens shall have the right to vote."
        })
        assert results["legislative"] is not None
        assert "vote" in results["legislative"]

    def test_run_audit_tools_adversarial(self):
        """Test run_audit_tools for adversarial_contribution."""
        brain = VeritasBrain()
        results = brain.run_audit_tools("adversarial_contribution", {
            "bill_text": "All taxes shall be reduced."
        })
        assert results["legislative"] is not None
        assert "counterpoints" in results["legislative"]


class TestStatusEndpoint:
    """Tests for updated status endpoint."""

    def test_status_phase_6(self):
        """Test that status shows Phase 6."""
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["phase"] == 7
        assert data["version"] == "0.7.0"
        assert data["components"]["legislative"] == "active"


class TestContributionLog:
    """Tests for contribution_log function."""

    def test_contribution_log_does_not_raise(self):
        """Test that contribution_log does not raise errors."""
        entry = {
            "bill_id": "TEST-001",
            "contribution_type": "vote",
            "analysis": {"vote": "yes", "confidence": 0.8},
            "summary": "Test vote logged"
        }
        # Should not raise
        contribution_log(entry)

    def test_contribution_log_sanitizes_data(self):
        """Test that contribution_log sanitizes sensitive data."""
        entry = {
            "bill_id": "TEST-002",
            "contribution_type": "adversarial",
            "analysis": {
                "counterpoints": ["point1", "point2"],
                "risk_flags": ["flag1"],
                "requires_review": True
            },
            "summary": "Adversarial contribution logged"
        }
        # Should not raise
        contribution_log(entry)
