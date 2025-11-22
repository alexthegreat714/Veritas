"""
Veritas Chain Validator Tests

This module tests the chain-of-thought validation functionality.
"""

import pytest

from app.logic.chain_validator import ChainValidator, validate_chain_stub


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

    def test_validate_returns_stub(self):
        """Test that validate method returns stub response."""
        validator = ChainValidator()
        chain = ["Premise", "Intermediate step", "Conclusion"]
        result = validator.validate(chain)
        assert result["status"] == "stub"
        assert "is_valid" in result
        assert "step_validations" in result
        assert "gaps" in result
        assert "circular_references" in result

    def test_validate_step_returns_stub(self):
        """Test that validate_step returns stub response."""
        validator = ChainValidator()
        result = validator.validate_step("Premise", "Conclusion")
        assert result["status"] == "stub"
        assert "is_valid" in result
        assert "inference_type" in result
        assert "strength" in result

    def test_detect_gaps_returns_empty_list(self):
        """Test that detect_gaps returns empty list in stub."""
        validator = ChainValidator()
        result = validator.detect_gaps(["Step 1", "Step 2", "Step 3"])
        assert isinstance(result, list)
        assert len(result) == 0

    def test_detect_circular_reasoning_returns_stub(self):
        """Test that detect_circular_reasoning returns stub response."""
        validator = ChainValidator()
        result = validator.detect_circular_reasoning(["A", "B", "A"])
        assert result["status"] == "stub"
        assert "has_circular_reasoning" in result
        assert "cycles" in result
        assert "affected_steps" in result

    def test_extract_hidden_assumptions_returns_empty_list(self):
        """Test that extract_hidden_assumptions returns empty list in stub."""
        validator = ChainValidator()
        result = validator.extract_hidden_assumptions(["Step 1", "Step 2"])
        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_chain_summary_returns_stub(self):
        """Test that get_chain_summary returns stub response."""
        validator = ChainValidator()
        result = validator.get_chain_summary(["Step 1", "Step 2"])
        assert result["status"] == "stub"
        assert "summary" in result


class TestValidateChainStub:
    """Tests for the validate_chain_stub function."""

    def test_validate_chain_stub_returns_dict(self):
        """Test that validate_chain_stub returns a dictionary."""
        result = validate_chain_stub(["Step 1", "Step 2"])
        assert isinstance(result, dict)

    def test_validate_chain_stub_returns_status(self):
        """Test that validate_chain_stub returns status key."""
        result = validate_chain_stub(["Step 1", "Step 2"])
        assert "status" in result
        assert result["status"] == "stub"
