"""
Veritas Bias Detector Tests

This module tests the bias detection functionality.
Phase 2: Tests for actual bias detection implementation.
"""

import pytest

from app.logic.bias_detector import BiasDetector, detect_bias


class TestDetectBiasFunction:
    """Tests for the detect_bias function."""

    def test_detect_bias_returns_dict(self):
        """Test that detect_bias returns a dictionary."""
        result = detect_bias("Test text")
        assert isinstance(result, dict)

    def test_detect_bias_has_required_keys(self):
        """Test that detect_bias returns all required keys."""
        result = detect_bias("Neutral statement.")
        assert "political_bias" in result
        assert "emotional_bias" in result
        assert "motivational_bias" in result
        assert "certainty_overconfidence" in result

    def test_detect_bias_returns_floats(self):
        """Test that bias scores are floats."""
        result = detect_bias("Test text")
        assert isinstance(result["political_bias"], float)
        assert isinstance(result["emotional_bias"], float)
        assert isinstance(result["motivational_bias"], float)
        assert isinstance(result["certainty_overconfidence"], float)

    def test_detect_bias_scores_in_range(self):
        """Test that bias scores are between 0 and 1."""
        result = detect_bias("Some text with amazing content and obvious truth.")
        assert 0.0 <= result["political_bias"] <= 1.0
        assert 0.0 <= result["emotional_bias"] <= 1.0
        assert 0.0 <= result["motivational_bias"] <= 1.0
        assert 0.0 <= result["certainty_overconfidence"] <= 1.0

    def test_detect_bias_empty_input(self):
        """Test detect_bias with empty input."""
        result = detect_bias("")
        assert result["political_bias"] == 0.0
        assert result["emotional_bias"] == 0.0
        assert result["motivational_bias"] == 0.0
        assert result["certainty_overconfidence"] == 0.0

    def test_detect_bias_emotional_positive(self):
        """Test detection of positive emotional language."""
        result = detect_bias("This is absolutely amazing and incredible! Fantastic work!")
        assert result["emotional_bias"] > 0.0

    def test_detect_bias_emotional_negative(self):
        """Test detection of negative emotional language."""
        result = detect_bias("This is terrible and disgusting. A complete disaster!")
        assert result["emotional_bias"] > 0.0

    def test_detect_bias_certainty_markers(self):
        """Test detection of certainty/overconfidence markers."""
        result = detect_bias("Obviously this is true. Clearly correct. Undoubtedly the best.")
        assert result["certainty_overconfidence"] > 0.0

    def test_detect_bias_motivational_language(self):
        """Test detection of motivational/persuasive language."""
        result = detect_bias("You must act now! Don't miss this exclusive opportunity!")
        assert result["motivational_bias"] > 0.0

    def test_detect_bias_deterministic(self):
        """Test that detect_bias produces deterministic results."""
        text = "This is obviously amazing and incredible content."
        result1 = detect_bias(text)
        result2 = detect_bias(text)
        assert result1 == result2


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

    def test_detector_detect_method(self):
        """Test the detect method returns comprehensive results."""
        detector = BiasDetector()
        result = detector.detect("This is amazing! Obviously the best ever!")
        assert "overall_bias_score" in result
        assert "bias_types" in result
        assert "loaded_language" in result
        assert "recommendations" in result

    def test_detector_overall_score_in_range(self):
        """Test that overall bias score is between 0 and 1."""
        detector = BiasDetector()
        result = detector.detect("Test text with some bias markers.")
        assert 0.0 <= result["overall_bias_score"] <= 1.0

    def test_detector_bias_types_list(self):
        """Test that bias_types is a list of typed scores."""
        detector = BiasDetector()
        result = detector.detect("Test text")
        assert isinstance(result["bias_types"], list)
        assert len(result["bias_types"]) == 4
        for bias_type in result["bias_types"]:
            assert "type" in bias_type
            assert "score" in bias_type

    def test_detector_loaded_language_extraction(self):
        """Test extraction of loaded language."""
        detector = BiasDetector()
        result = detector.detect("This is terrible and disgusting! Obviously wrong.")
        assert isinstance(result["loaded_language"], list)

    def test_detector_recommendations_generated(self):
        """Test that recommendations are generated for high bias."""
        detector = BiasDetector()
        result = detector.detect(
            "This is absolutely terrible and disgusting! Obviously wrong! "
            "You must believe this is clearly true!"
        )
        # High bias text should generate recommendations
        if result["overall_bias_score"] > 0.3:
            assert len(result["recommendations"]) > 0


class TestPoliticalBiasDetection:
    """Tests for political bias detection."""

    def test_detect_political_bias_neutral(self):
        """Test that neutral text has low political bias."""
        detector = BiasDetector()
        result = detector.detect_political_bias("The weather is sunny today.")
        assert result["leaning"] == "neutral"

    def test_detect_political_bias_indicators(self):
        """Test that political indicators are detected."""
        detector = BiasDetector()
        result = detector.detect_political_bias(
            "We need progressive social justice and equity for marginalized communities."
        )
        assert len(result["indicators"]) > 0
        assert result["left_count"] > 0

    def test_detect_political_bias_has_required_keys(self):
        """Test that political bias result has required keys."""
        detector = BiasDetector()
        result = detector.detect_political_bias("Test text")
        assert "leaning" in result
        assert "confidence" in result
        assert "indicators" in result


class TestEmotionalBiasDetection:
    """Tests for emotional bias detection."""

    def test_detect_emotional_bias_neutral(self):
        """Test that neutral text has neutral sentiment."""
        detector = BiasDetector()
        result = detector.detect_emotional_bias("The report contains data.")
        assert result["sentiment"] == "neutral"

    def test_detect_emotional_bias_positive(self):
        """Test detection of positive emotional bias."""
        detector = BiasDetector()
        result = detector.detect_emotional_bias(
            "This is amazing and wonderful! Incredible achievement!"
        )
        assert result["sentiment"] in ["positive", "mixed"]
        assert result["emotional_score"] > 0.0

    def test_detect_emotional_bias_negative(self):
        """Test detection of negative emotional bias."""
        detector = BiasDetector()
        result = detector.detect_emotional_bias(
            "This is terrible and horrible. A complete disaster!"
        )
        assert result["sentiment"] in ["negative", "mixed"]
        assert result["emotional_score"] > 0.0

    def test_detect_emotional_bias_loaded_terms(self):
        """Test extraction of loaded terms."""
        detector = BiasDetector()
        result = detector.detect_emotional_bias("Shocking and outrageous behavior!")
        assert len(result["loaded_terms"]) > 0


class TestBiasReport:
    """Tests for comprehensive bias reporting."""

    def test_get_bias_report(self):
        """Test the get_bias_report method."""
        detector = BiasDetector()
        result = detector.get_bias_report("This is amazing! Obviously correct.")
        assert "summary" in result
        assert "political_analysis" in result
        assert "emotional_analysis" in result
        assert "word_count" in result

    def test_bias_report_word_count(self):
        """Test that word count is accurate."""
        detector = BiasDetector()
        text = "One two three four five"
        result = detector.get_bias_report(text)
        assert result["word_count"] == 5
