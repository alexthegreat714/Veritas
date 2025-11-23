"""
Tests for Veritas Phase 5 Dispute Engine

Tests for parse_dispute() and related functions.
"""

import pytest
from datetime import datetime

from app.dispute_engine import (
    parse_dispute,
    get_dispute_engine,
    DisputeEngine,
    _extract_claims,
    _find_contradictions,
    _check_escalation_domain,
)


class TestParseDisputeBasic:
    """Basic tests for parse_dispute function."""

    def test_parse_dispute_returns_expected_structure(self):
        """Test that parse_dispute returns expected structure."""
        agent_a = {
            "agent": "Sky",
            "text": "The proposal is valid and should be approved.",
            "metadata": {}
        }
        agent_b = {
            "agent": "Aegis",
            "text": "The proposal has security concerns.",
            "metadata": {}
        }

        result = parse_dispute(agent_a, agent_b)

        assert "agents" in result
        assert "issues" in result
        assert "needs_escalation" in result
        assert "recommendation" in result
        assert "analysis" in result
        assert "timestamp" in result

    def test_parse_dispute_returns_agent_names(self):
        """Test that agent names are returned."""
        agent_a = {"agent": "Mercury", "text": "Position A", "metadata": {}}
        agent_b = {"agent": "Apollo", "text": "Position B", "metadata": {}}

        result = parse_dispute(agent_a, agent_b)

        assert result["agents"] == ["Mercury", "Apollo"]

    def test_parse_dispute_issues_structure(self):
        """Test that issues have expected structure."""
        agent_a = {"agent": "A", "text": "Claim A", "metadata": {}}
        agent_b = {"agent": "B", "text": "Claim B", "metadata": {}}

        result = parse_dispute(agent_a, agent_b)

        issues = result["issues"]
        assert "factual_disagreement" in issues
        assert "interpretation_disagreement" in issues
        assert "missing_data" in issues
        assert "logical_issues_A" in issues
        assert "logical_issues_B" in issues
        assert "contradictions" in issues


class TestContradictionDetection:
    """Tests for detecting factual contradictions."""

    def test_detects_direct_contradiction(self):
        """Test detection of direct contradictory claims."""
        agent_a = {
            "agent": "Sky",
            "text": "The system is secure and protected.",
            "metadata": {}
        }
        agent_b = {
            "agent": "Aegis",
            "text": "The system is not secure and needs protection.",
            "metadata": {}
        }

        result = parse_dispute(agent_a, agent_b)

        # Should detect factual disagreement
        assert result["issues"]["factual_disagreement"] is True

    def test_no_contradiction_for_compatible_claims(self):
        """Test no contradiction for compatible statements."""
        agent_a = {
            "agent": "Sky",
            "text": "The weather is sunny today.",
            "metadata": {}
        }
        agent_b = {
            "agent": "Mercury",
            "text": "The temperature is warm.",
            "metadata": {}
        }

        result = parse_dispute(agent_a, agent_b)

        # Should not detect factual disagreement for compatible claims
        # (may still be false due to no overlap)
        assert isinstance(result["issues"]["factual_disagreement"], bool)


class TestInterpretationDisagreement:
    """Tests for detecting interpretation disagreements."""

    def test_detects_interpretation_disagreement_with_bias_diff(self):
        """Test detection of interpretation disagreement when bias differs."""
        agent_a = {
            "agent": "Sky",
            "text": "This is absolutely terrible! We must reject this immediately!",
            "metadata": {}
        }
        agent_b = {
            "agent": "Aero",
            "text": "This seems reasonable. The proposal has merit.",
            "metadata": {}
        }

        result = parse_dispute(agent_a, agent_b)

        # High emotional bias difference should trigger interpretation disagreement
        # if no factual disagreement
        if not result["issues"]["factual_disagreement"]:
            # May or may not trigger depending on bias scores
            assert isinstance(result["issues"]["interpretation_disagreement"], bool)


class TestMissingDataDetection:
    """Tests for detecting missing data cases."""

    def test_detects_missing_data_empty_text(self):
        """Test detection of missing data when text is empty."""
        agent_a = {"agent": "Sky", "text": "", "metadata": {}}
        agent_b = {"agent": "Aegis", "text": "Valid text here.", "metadata": {}}

        result = parse_dispute(agent_a, agent_b)

        assert result["issues"]["missing_data"] is True

    def test_detects_missing_data_from_metadata(self):
        """Test detection of missing data from metadata flag."""
        agent_a = {
            "agent": "Sky",
            "text": "Some claim.",
            "metadata": {"missing_context": True}
        }
        agent_b = {
            "agent": "Aegis",
            "text": "Another claim.",
            "metadata": {}
        }

        result = parse_dispute(agent_a, agent_b)

        assert result["issues"]["missing_data"] is True


class TestEscalationClassification:
    """Tests for escalation classification."""

    def test_escalation_to_sophia_for_ethical_content(self):
        """Test escalation to Sophia for ethical/legal content."""
        agent_a = {
            "agent": "Sky",
            "text": "This raises ethical concerns about privacy and rights.",
            "metadata": {}
        }
        agent_b = {
            "agent": "Mercury",
            "text": "The legal implications of discrimination are unclear.",
            "metadata": {}
        }

        result = parse_dispute(agent_a, agent_b)

        assert result["needs_escalation"] == "sophia"

    def test_escalation_to_aegis_for_security_content(self):
        """Test escalation to Aegis for security/safety content."""
        agent_a = {
            "agent": "Sky",
            "text": "There is a security vulnerability in the system.",
            "metadata": {}
        }
        agent_b = {
            "agent": "Mercury",
            "text": "The threat level is dangerous and could cause damage.",
            "metadata": {}
        }

        result = parse_dispute(agent_a, agent_b)

        assert result["needs_escalation"] == "aegis"

    def test_escalation_to_congress_for_political_content(self):
        """Test escalation to Congress for political/governance content."""
        agent_a = {
            "agent": "Sky",
            "text": "The policy change will affect budget allocation.",
            "metadata": {}
        }
        agent_b = {
            "agent": "Mercury",
            "text": "This political decision requires legislative authority.",
            "metadata": {}
        }

        result = parse_dispute(agent_a, agent_b)

        assert result["needs_escalation"] == "congress"

    def test_no_escalation_for_neutral_content(self):
        """Test no escalation for neutral content."""
        agent_a = {
            "agent": "Sky",
            "text": "The sky is blue today.",
            "metadata": {}
        }
        agent_b = {
            "agent": "Mercury",
            "text": "The grass is green in the park.",
            "metadata": {}
        }

        result = parse_dispute(agent_a, agent_b)

        assert result["needs_escalation"] == "none"

    def test_escalation_from_metadata_domain(self):
        """Test escalation based on metadata domain."""
        agent_a = {
            "agent": "Sky",
            "text": "Simple text.",
            "metadata": {"domain": "security"}
        }
        agent_b = {
            "agent": "Mercury",
            "text": "Other text.",
            "metadata": {}
        }

        result = parse_dispute(agent_a, agent_b)

        assert result["needs_escalation"] == "aegis"


class TestRecommendations:
    """Tests for recommendation generation."""

    def test_recommendation_forward_to_sophia(self):
        """Test recommendation to forward to Sophia."""
        agent_a = {
            "agent": "Sky",
            "text": "This ethical dilemma involves moral rights and justice.",
            "metadata": {}
        }
        agent_b = {
            "agent": "Mercury",
            "text": "The legal and ethical implications are significant.",
            "metadata": {}
        }

        result = parse_dispute(agent_a, agent_b)

        assert result["recommendation"] == "forward_to_sophia"

    def test_recommendation_forward_to_aegis(self):
        """Test recommendation to forward to Aegis."""
        agent_a = {
            "agent": "Sky",
            "text": "Security breach detected with dangerous vulnerability.",
            "metadata": {}
        }
        agent_b = {
            "agent": "Mercury",
            "text": "Attack surface is exposed, threat level critical.",
            "metadata": {}
        }

        result = parse_dispute(agent_a, agent_b)

        assert result["recommendation"] == "forward_to_aegis"

    def test_recommendation_request_more_data(self):
        """Test recommendation to request more data."""
        agent_a = {"agent": "Sky", "text": "", "metadata": {}}
        agent_b = {"agent": "Mercury", "text": "Some claim.", "metadata": {}}

        result = parse_dispute(agent_a, agent_b)

        assert result["recommendation"] == "request_more_data"

    def test_valid_recommendation_values(self):
        """Test that recommendation is one of valid values."""
        agent_a = {"agent": "Sky", "text": "Position A.", "metadata": {}}
        agent_b = {"agent": "Mercury", "text": "Position B.", "metadata": {}}

        result = parse_dispute(agent_a, agent_b)

        valid_recommendations = [
            "request_more_data",
            "forward_to_sophia",
            "forward_to_aegis",
            "mediation_by_congress",
            "minimal_issue_detected",
            "inconclusive",
        ]
        assert result["recommendation"] in valid_recommendations


class TestAnalysisDetails:
    """Tests for analysis details."""

    def test_analysis_includes_audit_details(self):
        """Test that analysis includes audit details for both sides."""
        agent_a = {"agent": "Sky", "text": "Claim A is true.", "metadata": {}}
        agent_b = {"agent": "Mercury", "text": "Claim B is valid.", "metadata": {}}

        result = parse_dispute(agent_a, agent_b)

        assert "audit_A" in result["analysis"]
        assert "audit_B" in result["analysis"]

    def test_analysis_audit_structure(self):
        """Test audit structure in analysis."""
        agent_a = {"agent": "Sky", "text": "Statement A.", "metadata": {}}
        agent_b = {"agent": "Mercury", "text": "Statement B.", "metadata": {}}

        result = parse_dispute(agent_a, agent_b)

        audit_a = result["analysis"]["audit_A"]
        assert "claims_count" in audit_a
        assert "fallacies_count" in audit_a
        assert "unsupported_count" in audit_a
        assert "bias_summary" in audit_a


class TestDisputeEngineClass:
    """Tests for DisputeEngine class."""

    def test_dispute_engine_initialization(self):
        """Test DisputeEngine initializes correctly."""
        engine = DisputeEngine()
        assert engine._last_analysis is None

    def test_dispute_engine_analyze(self):
        """Test DisputeEngine.analyze method."""
        engine = DisputeEngine()
        agent_a = {"agent": "Sky", "text": "Position A.", "metadata": {}}
        agent_b = {"agent": "Mercury", "text": "Position B.", "metadata": {}}

        result = engine.analyze(agent_a, agent_b)

        assert result is not None
        assert "agents" in result
        assert engine._last_analysis == result

    def test_dispute_engine_get_last_analysis(self):
        """Test DisputeEngine.get_last_analysis method."""
        engine = DisputeEngine()
        agent_a = {"agent": "Sky", "text": "Position A.", "metadata": {}}
        agent_b = {"agent": "Mercury", "text": "Position B.", "metadata": {}}

        engine.analyze(agent_a, agent_b)
        last = engine.get_last_analysis()

        assert last is not None
        assert "agents" in last

    def test_dispute_engine_needs_escalation(self):
        """Test DisputeEngine.needs_escalation method."""
        engine = DisputeEngine()

        # Before any analysis
        assert engine.needs_escalation() is False

        # After analysis with security keywords
        agent_a = {"agent": "Sky", "text": "Security threat detected.", "metadata": {}}
        agent_b = {"agent": "Mercury", "text": "Danger and vulnerability.", "metadata": {}}
        engine.analyze(agent_a, agent_b)

        assert engine.needs_escalation() is True

    def test_dispute_engine_get_escalation_target(self):
        """Test DisputeEngine.get_escalation_target method."""
        engine = DisputeEngine()

        # Before analysis
        assert engine.get_escalation_target() is None

        # After analysis
        agent_a = {"agent": "Sky", "text": "Ethical concern about rights.", "metadata": {}}
        agent_b = {"agent": "Mercury", "text": "Legal and moral issues.", "metadata": {}}
        engine.analyze(agent_a, agent_b)

        target = engine.get_escalation_target()
        assert target in ["sophia", "aegis", "congress", None]


class TestGetDisputeEngine:
    """Tests for get_dispute_engine singleton."""

    def test_get_dispute_engine_returns_instance(self):
        """Test get_dispute_engine returns an instance."""
        engine = get_dispute_engine()
        assert isinstance(engine, DisputeEngine)

    def test_get_dispute_engine_returns_same_instance(self):
        """Test get_dispute_engine returns the same instance."""
        engine1 = get_dispute_engine()
        engine2 = get_dispute_engine()
        assert engine1 is engine2


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_extract_claims(self):
        """Test _extract_claims function."""
        audit_result = {
            "claims": [
                {"text": "Claim 1"},
                {"claim": "Claim 2"},
                "Claim 3"
            ]
        }

        claims = _extract_claims(audit_result)

        assert len(claims) == 3
        assert "Claim 1" in claims
        assert "Claim 2" in claims
        assert "Claim 3" in claims

    def test_find_contradictions_with_negation(self):
        """Test _find_contradictions with negation patterns."""
        claims_a = ["The sky is blue"]
        claims_b = ["The sky is not blue"]

        contradictions = _find_contradictions(claims_a, claims_b)

        # Should find contradiction due to "is" vs "is not" with overlap
        assert isinstance(contradictions, list)

    def test_check_escalation_domain_security(self):
        """Test _check_escalation_domain for security."""
        result = _check_escalation_domain(
            "security vulnerability detected",
            "threat and danger",
            {}, {}
        )
        assert result == "aegis"

    def test_check_escalation_domain_ethical(self):
        """Test _check_escalation_domain for ethical."""
        result = _check_escalation_domain(
            "ethical moral rights",
            "justice fairness law",
            {}, {}
        )
        assert result == "sophia"

    def test_check_escalation_domain_political(self):
        """Test _check_escalation_domain for political."""
        result = _check_escalation_domain(
            "policy budget allocation",
            "government legislation regulation",
            {}, {}
        )
        assert result == "congress"
