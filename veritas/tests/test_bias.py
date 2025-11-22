"""
Veritas Bias Detector Tests

This module tests the bias detection functionality.
"""

import pytest

from app.logic.bias_detector import BiasDetector, detect_bias_stub


class TestBiasDetector:
    """Tests for the BiasDetector class."""

    def test_detector_initialization(self):
        """Test that BiasDetector can be initialized."""
        detector = BiasDetector()
        assert detector is not None
        assert detector.config == {}
        assert detector.threshold == 0.7

    def test_detector_initialization_with_config(self):
        """Test that BiasDetector accepts configuration."""
        config = {"threshold": 0.8}
        detector = BiasDetector(config=config)
        assert detector.threshold == 0.8

    def test_detect_returns_stub(self):
        """Test that detect method returns stub response."""
        detector = BiasDetector()
        result = detector.detect("Test text for bias detection")
        assert result["status"] == "stub"
        assert "overall_bias_score" in result
        assert "bias_types" in result
        assert "loaded_language" in result

    def test_detect_political_bias_returns_stub(self):
        """Test that detect_political_bias returns stub response."""
        detector = BiasDetector()
        result = detector.detect_political_bias("Political text")
        assert result["status"] == "stub"
        assert "leaning" in result
        assert "confidence" in result
        assert "indicators" in result

    def test_detect_emotional_bias_returns_stub(self):
        """Test that detect_emotional_bias returns stub response."""
        detector = BiasDetector()
        result = detector.detect_emotional_bias("Emotional text")
        assert result["status"] == "stub"
        assert "emotional_score" in result
        assert "sentiment" in result
        assert "loaded_terms" in result

    def test_detect_selection_bias_returns_stub(self):
        """Test that detect_selection_bias returns stub response."""
        detector = BiasDetector()
        result = detector.detect_selection_bias("Text with potential selection bias")
        assert result["status"] == "stub"
        assert "has_selection_bias" in result
        assert "missing_perspectives" in result

    def test_get_bias_report_returns_stub(self):
        """Test that get_bias_report returns stub response."""
        detector = BiasDetector()
        result = detector.get_bias_report("Text for bias report")
        assert result["status"] == "stub"
        assert "report" in result


class TestDetectBiasStub:
    """Tests for the detect_bias_stub function."""

    def test_detect_bias_stub_returns_dict(self):
        """Test that detect_bias_stub returns a dictionary."""
        result = detect_bias_stub("Test text")
        assert isinstance(result, dict)

    def test_detect_bias_stub_returns_status(self):
        """Test that detect_bias_stub returns status key."""
        result = detect_bias_stub("Test text")
        assert "status" in result
        assert result["status"] == "stub"
