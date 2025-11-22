"""
Veritas Logic Auditor Tests

This module tests the logic auditor functionality.
Phase 2: Tests for actual auditing implementation.
"""

import pytest

from app.logic.auditor import LogicAuditor, audit_text


class TestAuditTextFunction:
    """Tests for the audit_text function."""

    def test_audit_text_returns_dict(self):
        """Test that audit_text returns a dictionary."""
        result = audit_text("Test text")
        assert isinstance(result, dict)

    def test_audit_text_has_required_keys(self):
        """Test that audit_text returns all required keys."""
        result = audit_text("The sky is blue.")
        assert "claims" in result
        assert "logical_fallacies" in result
        assert "inconsistencies" in result
        assert "unsupported_jumps" in result

    def test_audit_text_empty_input(self):
        """Test audit_text with empty input."""
        result = audit_text("")
        assert result["claims"] == []
        assert result["logical_fallacies"] == []
        assert result["inconsistencies"] == []
        assert result["unsupported_jumps"] == []

    def test_audit_text_extracts_factual_claims(self):
        """Test that audit_text extracts factual claims."""
        result = audit_text("The Earth is round. Water boils at 100 degrees.")
        assert len(result["claims"]) > 0
        assert any(c["type"] == "factual" for c in result["claims"])

    def test_audit_text_extracts_universal_claims(self):
        """Test that audit_text extracts universal claims."""
        result = audit_text("All humans need oxygen to survive. Everyone knows this.")
        assert len(result["claims"]) > 0
        assert any(c["type"] == "universal" for c in result["claims"])

    def test_audit_text_detects_ad_hominem(self):
        """Test that audit_text detects ad hominem fallacy."""
        result = audit_text("He is stupid, so his argument must be wrong.")
        fallacy_types = [f["type"] for f in result["logical_fallacies"]]
        assert "Ad Hominem" in fallacy_types

    def test_audit_text_detects_strawman(self):
        """Test that audit_text detects strawman fallacy."""
        result = audit_text("So you're saying we should just give up entirely?")
        fallacy_types = [f["type"] for f in result["logical_fallacies"]]
        assert "Straw Man" in fallacy_types

    def test_audit_text_detects_hasty_generalization(self):
        """Test that audit_text detects hasty generalization."""
        result = audit_text("All politicians are corrupt. Everyone knows this.")
        fallacy_types = [f["type"] for f in result["logical_fallacies"]]
        assert "Hasty Generalization" in fallacy_types

    def test_audit_text_detects_certainty_jumps(self):
        """Test that audit_text detects unjustified certainty."""
        result = audit_text("Obviously this is correct. Clearly the best option.")
        assert len(result["unsupported_jumps"]) > 0
        assert any(j["type"] == "unjustified_certainty" for j in result["unsupported_jumps"])

    def test_audit_text_deterministic(self):
        """Test that audit_text produces deterministic results."""
        text = "All dogs are mammals. Therefore, my pet is a mammal."
        result1 = audit_text(text)
        result2 = audit_text(text)
        assert result1 == result2


class TestLogicAuditor:
    """Tests for the LogicAuditor class."""

    def test_auditor_initialization(self):
        """Test that LogicAuditor can be initialized."""
        auditor = LogicAuditor()
        assert auditor is not None
        assert auditor.config == {}

    def test_auditor_initialization_with_config(self):
        """Test that LogicAuditor accepts configuration."""
        config = {"custom_setting": "value"}
        auditor = LogicAuditor(config=config)
        assert auditor.config == config

    def test_auditor_analyze(self):
        """Test that analyze method returns results with scores."""
        auditor = LogicAuditor()
        result = auditor.analyze("This is a test with obvious claims. Clearly correct.")
        assert "claims" in result
        assert "logical_fallacies" in result
        assert "consistency_score" in result
        assert "recommendations" in result

    def test_auditor_consistency_score_range(self):
        """Test that consistency score is between 0 and 1."""
        auditor = LogicAuditor()
        result = auditor.analyze("Test text with some content.")
        assert 0.0 <= result["consistency_score"] <= 1.0

    def test_auditor_identify_fallacies(self):
        """Test identify_fallacies method."""
        auditor = LogicAuditor()
        result = auditor.identify_fallacies("You are stupid, therefore wrong.")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_auditor_extract_claims(self):
        """Test extract_claims method."""
        auditor = LogicAuditor()
        result = auditor.extract_claims("The sky is blue. Water is wet.")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_auditor_check_consistency(self):
        """Test check_consistency method."""
        auditor = LogicAuditor()
        result = auditor.check_consistency([
            "The cat is black.",
            "The cat is not black."
        ])
        assert "is_consistent" in result
        assert "conflicts" in result
        assert "confidence" in result

    def test_auditor_recommendations_generated(self):
        """Test that recommendations are generated for issues."""
        auditor = LogicAuditor()
        result = auditor.analyze("You are stupid. Obviously this is true.")
        # Should have recommendations due to fallacy and certainty markers
        if result["logical_fallacies"] or result["unsupported_jumps"]:
            assert len(result["recommendations"]) > 0


class TestFallacyDetection:
    """Detailed tests for fallacy detection patterns."""

    def test_detect_false_dichotomy(self):
        """Test detection of false dichotomy."""
        result = audit_text("You're either with us or against us.")
        fallacy_types = [f["type"] for f in result["logical_fallacies"]]
        assert "False Dichotomy" in fallacy_types

    def test_detect_appeal_to_authority(self):
        """Test detection of appeal to authority."""
        result = audit_text("Experts say this is true, so it must be true.")
        fallacy_types = [f["type"] for f in result["logical_fallacies"]]
        assert "Appeal to Authority" in fallacy_types

    def test_detect_red_herring(self):
        """Test detection of red herring."""
        result = audit_text("But what about the other issue? The real issue is something else.")
        fallacy_types = [f["type"] for f in result["logical_fallacies"]]
        assert "Red Herring" in fallacy_types

    def test_detect_slippery_slope(self):
        """Test detection of slippery slope."""
        result = audit_text("If we allow this, then next we'll have chaos, and then eventually disaster.")
        fallacy_types = [f["type"] for f in result["logical_fallacies"]]
        assert "Slippery Slope" in fallacy_types


class TestClaimExtraction:
    """Tests for claim extraction functionality."""

    def test_extract_causal_claims(self):
        """Test extraction of causal claims."""
        result = audit_text("Smoking causes cancer. Pollution leads to health problems.")
        claim_types = [c["type"] for c in result["claims"]]
        assert "causal" in claim_types

    def test_extract_normative_claims(self):
        """Test extraction of normative claims."""
        result = audit_text("You should exercise daily. People must follow the rules.")
        claim_types = [c["type"] for c in result["claims"]]
        assert "normative" in claim_types

    def test_claims_have_positions(self):
        """Test that extracted claims have position information."""
        result = audit_text("The sky is blue. The grass is green.")
        for claim in result["claims"]:
            assert "position" in claim
            assert isinstance(claim["position"], int)
