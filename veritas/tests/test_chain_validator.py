"""
Veritas Chain Validator Tests

This module tests the chain-of-thought validation functionality.
Phase 2: Tests for actual chain validation implementation.
"""

import pytest

from app.logic.chain_validator import ChainValidator, validate_chain


class TestValidateChainFunction:
    """Tests for the validate_chain function."""

    def test_validate_chain_returns_dict(self):
        """Test that validate_chain returns a dictionary."""
        result = validate_chain(["Step 1", "Step 2"])
        assert isinstance(result, dict)

    def test_validate_chain_has_required_keys(self):
        """Test that validate_chain returns all required keys."""
        result = validate_chain(["Premise", "Conclusion"])
        assert "gaps" in result
        assert "contradictions" in result
        assert "circular_logic" in result
        assert "flawed_premises" in result

    def test_validate_chain_empty_input(self):
        """Test validate_chain with empty input."""
        result = validate_chain([])
        assert result["gaps"] == []
        assert result["contradictions"] == []
        assert result["circular_logic"] == []
        assert result["flawed_premises"] == []

    def test_validate_chain_single_step(self):
        """Test validate_chain with single step."""
        result = validate_chain(["Single premise"])
        assert result["gaps"] == []
        assert result["contradictions"] == []

    def test_validate_chain_detects_flawed_premise(self):
        """Test detection of flawed premises with assumptions."""
        result = validate_chain([
            "Assume that all swans are white",
            "This bird is a swan",
            "Therefore this bird is white"
        ])
        assert len(result["flawed_premises"]) > 0

    def test_validate_chain_deterministic(self):
        """Test that validate_chain produces deterministic results."""
        chain = ["Premise A", "Therefore B", "Finally C"]
        result1 = validate_chain(chain)
        result2 = validate_chain(chain)
        assert result1 == result2


class TestChainValidator:
    """Tests for the ChainValidator class."""

    def test_validator_initialization(self):
        """Test that ChainValidator can be initialized."""
        validator = ChainValidator()
        assert validator is not None
        assert validator.config == {}
        assert validator.max_chain_depth == 50

    def test_validator_initialization_with_config(self):
        """Test that ChainValidator accepts configuration."""
        config = {"max_chain_depth": 100}
        validator = ChainValidator(config=config)
        assert validator.max_chain_depth == 100

    def test_validator_validate_method(self):
        """Test the validate method returns comprehensive results."""
        validator = ChainValidator()
        result = validator.validate(["Step 1", "Step 2", "Step 3"])
        assert "is_valid" in result
        assert "step_validations" in result
        assert "gaps" in result
        assert "confidence" in result

    def test_validator_confidence_in_range(self):
        """Test that confidence is between 0 and 1."""
        validator = ChainValidator()
        result = validator.validate(["Step 1", "Therefore Step 2"])
        assert 0.0 <= result["confidence"] <= 1.0

    def test_validator_step_validations(self):
        """Test that step validations are generated for each step."""
        validator = ChainValidator()
        chain = ["Step 1", "Step 2", "Step 3"]
        result = validator.validate(chain)
        assert len(result["step_validations"]) == len(chain)

    def test_validator_validate_step(self):
        """Test validate_step method."""
        validator = ChainValidator()
        result = validator.validate_step(
            "All humans are mortal",
            "Therefore Socrates is mortal"
        )
        assert "is_valid" in result
        assert "inference_type" in result
        assert "strength" in result
        assert "issues" in result

    def test_validator_detect_gaps(self):
        """Test detect_gaps method."""
        validator = ChainValidator()
        result = validator.detect_gaps([
            "Economics is complex",
            "Therefore quantum physics is easy"
        ])
        assert isinstance(result, list)

    def test_validator_detect_circular_reasoning(self):
        """Test detect_circular_reasoning method."""
        validator = ChainValidator()
        result = validator.detect_circular_reasoning([
            "The book is good",
            "Good books are popular",
            "As we said, the book is good"
        ])
        assert "has_circular_reasoning" in result
        assert "cycles" in result
        assert "affected_steps" in result


class TestGapDetection:
    """Tests for gap detection in reasoning chains."""

    def test_detect_gap_unrelated_topics(self):
        """Test detection of gaps between unrelated topics."""
        result = validate_chain([
            "The weather is nice today",
            "Therefore stocks will rise"
        ])
        assert len(result["gaps"]) > 0

    def test_no_gap_connected_steps(self):
        """Test no gap for logically connected steps."""
        result = validate_chain([
            "All mammals are warm-blooded",
            "Dogs are mammals",
            "Therefore dogs are warm-blooded"
        ])
        major_gaps = [g for g in result["gaps"] if g["severity"] == "major"]
        assert len(major_gaps) == 0

    def test_gap_severity_levels(self):
        """Test that gaps have severity levels."""
        result = validate_chain([
            "Topic A is interesting",
            "Completely unrelated topic B"
        ])
        if result["gaps"]:
            gap = result["gaps"][0]
            assert "severity" in gap
            assert gap["severity"] in ["minor", "moderate", "major"]


class TestCircularLogicDetection:
    """Tests for circular logic detection."""

    def test_detect_explicit_back_reference(self):
        """Test detection of explicit back-references."""
        result = validate_chain([
            "The argument is valid",
            "Because it follows logic",
            "As we stated earlier, the argument is valid"
        ])
        assert len(result["circular_logic"]) > 0


class TestFlawedPremiseDetection:
    """Tests for flawed premise detection."""

    def test_detect_assumption_premise(self):
        """Test detection of assumption-based premises."""
        result = validate_chain([
            "Suppose that money grows on trees",
            "Then everyone would be rich"
        ])
        assert len(result["flawed_premises"]) > 0

    def test_detect_weak_foundation(self):
        """Test detection of weak foundational premises."""
        result = validate_chain([
            "Assuming the hypothesis is correct",
            "We can derive conclusion X"
        ])
        if result["flawed_premises"]:
            assert any(f["step_index"] == 0 for f in result["flawed_premises"])


class TestChainSummary:
    """Tests for chain summary functionality."""

    def test_get_chain_summary(self):
        """Test the get_chain_summary method."""
        validator = ChainValidator()
        result = validator.get_chain_summary([
            "Step 1",
            "Therefore Step 2",
            "Finally Step 3"
        ])
        assert "total_steps" in result
        assert "is_valid" in result
        assert "confidence" in result
        assert "issues_summary" in result
        assert "recommendation" in result

    def test_chain_summary_step_count(self):
        """Test that step count is accurate."""
        validator = ChainValidator()
        chain = ["A", "B", "C", "D"]
        result = validator.get_chain_summary(chain)
        assert result["total_steps"] == 4


class TestHiddenAssumptions:
    """Tests for hidden assumption extraction."""

    def test_extract_hidden_assumptions(self):
        """Test extraction of hidden assumptions."""
        validator = ChainValidator()
        result = validator.extract_hidden_assumptions([
            "Of course this is correct",
            "Everyone knows the answer",
            "Obviously the conclusion follows"
        ])
        assert isinstance(result, list)
        assert len(result) > 0
