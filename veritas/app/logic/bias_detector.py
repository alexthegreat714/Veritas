"""
Veritas Bias Detector Module

This module contains functionality for detecting and analyzing
various forms of bias in text content.

Phase 2: Deterministic heuristic-based implementation.
All analysis is rule-based with no ML models.
Returns normalized floats between 0.0-1.0.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from logging.handlers import RotatingFileHandler


# Configure module logger
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = RotatingFileHandler(
        LOG_DIR / "bias_detector.log",
        maxBytes=5_000_000,
        backupCount=3
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)


# Political bias indicators (simplified heuristic word lists)
POLITICAL_LEFT_INDICATORS = [
    r"\bprogressive\b",
    r"\bsocial justice\b",
    r"\binequality\b",
    r"\bsystemic\b",
    r"\bmarginalized\b",
    r"\boppression\b",
    r"\bprivilege\b",
    r"\binclusiv(e|ity)\b",
    r"\bdiversity\b",
    r"\bequity\b",
    r"\bclimate crisis\b",
    r"\bcorporate greed\b",
    r"\bworking class\b",
    r"\bwealth gap\b",
    r"\buniversal (healthcare|income|basic)\b",
]

POLITICAL_RIGHT_INDICATORS = [
    r"\btraditional values\b",
    r"\bfree market\b",
    r"\bpatrioti(c|sm)\b",
    r"\bfamily values\b",
    r"\blaw and order\b",
    r"\billegal (immigrant|alien)\b",
    r"\bborder security\b",
    r"\bsecond amendment\b",
    r"\bgun rights\b",
    r"\bsmall government\b",
    r"\btax(es)? (cut|relief|burden)\b",
    r"\breligious freedom\b",
    r"\bnational security\b",
    r"\bderegulat(e|ion)\b",
    r"\bfiscal responsib(le|ility)\b",
]

# Emotionally loaded language indicators
EMOTIONAL_POSITIVE_TERMS = [
    r"\bamazing\b",
    r"\bincredible\b",
    r"\bfantastic\b",
    r"\bbrilliant\b",
    r"\bwonderful\b",
    r"\bextraordinary\b",
    r"\bphenomenal\b",
    r"\bspectacular\b",
    r"\boutstanding\b",
    r"\bremarkable\b",
    r"\btriumph(ant)?\b",
    r"\bvictory\b",
    r"\bheroic\b",
    r"\binspir(e|ing|ation)\b",
]

EMOTIONAL_NEGATIVE_TERMS = [
    r"\bterrible\b",
    r"\bhorrible\b",
    r"\bdisgusting\b",
    r"\bappalling\b",
    r"\bshocking\b",
    r"\boutrageous\b",
    r"\bdisaster(ous)?\b",
    r"\bcatastroph(e|ic)\b",
    r"\bdevastating\b",
    r"\btragic\b",
    r"\bshameful\b",
    r"\bdisgrace(ful)?\b",
    r"\bdangerous\b",
    r"\bthreat(en|ening)?\b",
    r"\bcrisis\b",
    r"\bfear\b",
    r"\banger\b",
    r"\bhate\b",
]

EMOTIONAL_INTENSIFIERS = [
    r"\babsolutely\b",
    r"\bcompletely\b",
    r"\btotally\b",
    r"\butterly\b",
    r"\bextremely\b",
    r"\bincredibly\b",
    r"\bunbelievably\b",
    r"\bshockingly\b",
]

# Motivational/persuasive bias indicators
MOTIVATIONAL_INDICATORS = [
    r"\byou (must|should|need to|have to)\b",
    r"\bdon't (miss|wait|hesitate)\b",
    r"\bact now\b",
    r"\blimited time\b",
    r"\bexclusive\b",
    r"\bonly (you|way|option|chance)\b",
    r"\bguarantee[ds]?\b",
    r"\bproven\b",
    r"\bsecret\b",
    r"\bthey don't want you to know\b",
    r"\bwake up\b",
    r"\bopen your eyes\b",
    r"\bthe truth (is|about)\b",
    r"\bjoin (us|now|today)\b",
    r"\btake action\b",
]

SELF_SERVING_INDICATORS = [
    r"\bi('m| am) (right|correct)\b",
    r"\bmy (view|opinion|perspective) is\b",
    r"\bas i (said|mentioned|predicted)\b",
    r"\bi told you\b",
    r"\bproves? (me|my point)\b",
    r"\bvindicate[ds]?\b",
]

# Certainty/overconfidence indicators
CERTAINTY_INDICATORS = [
    r"\bobviously\b",
    r"\bclearly\b",
    r"\bundoubtedly\b",
    r"\bcertainly\b",
    r"\bdefinitely\b",
    r"\bwithout (a )?doubt\b",
    r"\bunquestionabl[ye]\b",
    r"\bindisputabl[ye]\b",
    r"\bof course\b",
    r"\bneedless to say\b",
    r"\bit('s| is) (a )?fact\b",
    r"\beveryone knows\b",
    r"\bno one (can )?(deny|dispute)\b",
    r"\bthe truth is\b",
    r"\bplain (and simple|to see)\b",
]


def detect_bias(text: str) -> Dict[str, float]:
    """
    Detect various forms of bias in text using heuristic analysis.

    Args:
        text: The text to analyze for bias.

    Returns:
        Dictionary containing normalized bias scores (0.0-1.0):
        - political_bias: Detected political leaning intensity
        - emotional_bias: Emotionally loaded language score
        - motivational_bias: Self-serving/persuasive patterns score
        - certainty_overconfidence: Unjustified certainty markers score
    """
    logger.info(f"Detecting bias in text of length {len(text)}")
    logger.debug(f"Input text: {text[:500]}...")

    if not text or not text.strip():
        result = {
            "political_bias": 0.0,
            "emotional_bias": 0.0,
            "motivational_bias": 0.0,
            "certainty_overconfidence": 0.0,
        }
        logger.info(f"Output: {result}")
        return result

    text_lower = text.lower()
    word_count = len(text.split())

    # Prevent division by zero
    if word_count == 0:
        result = {
            "political_bias": 0.0,
            "emotional_bias": 0.0,
            "motivational_bias": 0.0,
            "certainty_overconfidence": 0.0,
        }
        logger.info(f"Output: {result}")
        return result

    political_bias = _calculate_political_bias(text_lower, word_count)
    emotional_bias = _calculate_emotional_bias(text_lower, word_count)
    motivational_bias = _calculate_motivational_bias(text_lower, word_count)
    certainty_overconfidence = _calculate_certainty_bias(text_lower, word_count)

    result = {
        "political_bias": political_bias,
        "emotional_bias": emotional_bias,
        "motivational_bias": motivational_bias,
        "certainty_overconfidence": certainty_overconfidence,
    }

    logger.info(f"Bias detection complete: political={political_bias:.3f}, "
                f"emotional={emotional_bias:.3f}, motivational={motivational_bias:.3f}, "
                f"certainty={certainty_overconfidence:.3f}")
    logger.debug(f"Output: {result}")

    return result


def _count_matches(text: str, patterns: List[str]) -> int:
    """Count total matches for a list of regex patterns."""
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, text, re.IGNORECASE))
    return count


def _normalize_score(raw_count: int, word_count: int, sensitivity: float = 50.0) -> float:
    """
    Normalize a raw count to a 0.0-1.0 score.

    Uses a logarithmic scaling to handle varying text lengths.
    Sensitivity controls how quickly the score approaches 1.0.
    """
    if word_count == 0:
        return 0.0

    # Calculate density (matches per 100 words)
    density = (raw_count / word_count) * 100

    # Apply sigmoid-like normalization
    # This gives a smooth curve that approaches 1.0 as density increases
    score = density / (density + sensitivity / 10)

    return min(1.0, max(0.0, score))


def _calculate_political_bias(text_lower: str, word_count: int) -> float:
    """Calculate political bias score based on partisan language indicators."""
    left_count = _count_matches(text_lower, POLITICAL_LEFT_INDICATORS)
    right_count = _count_matches(text_lower, POLITICAL_RIGHT_INDICATORS)

    total_political = left_count + right_count

    # Political bias is the presence of partisan language regardless of direction
    # Higher score = more politically charged language
    return _normalize_score(total_political, word_count, sensitivity=30.0)


def _calculate_emotional_bias(text_lower: str, word_count: int) -> float:
    """Calculate emotional bias score based on loaded language."""
    positive_count = _count_matches(text_lower, EMOTIONAL_POSITIVE_TERMS)
    negative_count = _count_matches(text_lower, EMOTIONAL_NEGATIVE_TERMS)
    intensifier_count = _count_matches(text_lower, EMOTIONAL_INTENSIFIERS)

    # Emotional bias considers all emotional language
    # Intensifiers amplify the score
    total_emotional = positive_count + negative_count + (intensifier_count * 1.5)

    return _normalize_score(int(total_emotional), word_count, sensitivity=25.0)


def _calculate_motivational_bias(text_lower: str, word_count: int) -> float:
    """Calculate motivational/persuasive bias score."""
    motivational_count = _count_matches(text_lower, MOTIVATIONAL_INDICATORS)
    self_serving_count = _count_matches(text_lower, SELF_SERVING_INDICATORS)

    # Self-serving language is weighted more heavily
    total_motivational = motivational_count + (self_serving_count * 2)

    return _normalize_score(total_motivational, word_count, sensitivity=35.0)


def _calculate_certainty_bias(text_lower: str, word_count: int) -> float:
    """Calculate certainty/overconfidence bias score."""
    certainty_count = _count_matches(text_lower, CERTAINTY_INDICATORS)

    return _normalize_score(certainty_count, word_count, sensitivity=20.0)


class BiasDetector:
    """
    Bias Detector for identifying and analyzing bias in text.

    This class provides comprehensive bias detection capabilities including:
    - Political bias detection (partisanship intensity)
    - Emotional bias and loaded language detection
    - Motivational/persuasive bias detection
    - Certainty overconfidence detection

    Phase 2: Deterministic heuristic-based implementation.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the BiasDetector.

        Args:
            config: Optional configuration dictionary for detector settings.
        """
        self.config = config or {}
        self.threshold = self.config.get("threshold", 0.7)
        self._initialized = True
        logger.info("BiasDetector initialized")

    def detect(self, text: str) -> Dict[str, Any]:
        """
        Detect all forms of bias in the provided text.

        Args:
            text: The text to analyze for bias.

        Returns:
            Dictionary containing detection results.
        """
        bias_scores = detect_bias(text)

        # Calculate overall bias score (weighted average)
        overall_score = (
            bias_scores["political_bias"] * 0.25 +
            bias_scores["emotional_bias"] * 0.30 +
            bias_scores["motivational_bias"] * 0.25 +
            bias_scores["certainty_overconfidence"] * 0.20
        )

        # Extract loaded language examples
        loaded_language = self._extract_loaded_language(text.lower())

        # Generate recommendations
        recommendations = self._generate_recommendations(bias_scores)

        return {
            "overall_bias_score": round(overall_score, 3),
            "bias_types": [
                {"type": "political", "score": round(bias_scores["political_bias"], 3)},
                {"type": "emotional", "score": round(bias_scores["emotional_bias"], 3)},
                {"type": "motivational", "score": round(bias_scores["motivational_bias"], 3)},
                {"type": "certainty", "score": round(bias_scores["certainty_overconfidence"], 3)},
            ],
            "loaded_language": loaded_language,
            "recommendations": recommendations,
        }

    def _extract_loaded_language(self, text_lower: str) -> List[Dict[str, str]]:
        """Extract examples of loaded language from text."""
        loaded = []

        # Check emotional terms
        all_emotional = EMOTIONAL_POSITIVE_TERMS + EMOTIONAL_NEGATIVE_TERMS
        for pattern in all_emotional:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                loaded.append({"term": match, "category": "emotional"})

        # Check certainty terms
        for pattern in CERTAINTY_INDICATORS:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                loaded.append({"term": match, "category": "certainty"})

        # Limit to first 10 examples
        return loaded[:10]

    def _generate_recommendations(self, bias_scores: Dict[str, float]) -> List[str]:
        """Generate recommendations based on bias scores."""
        recommendations = []

        if bias_scores["political_bias"] > 0.3:
            recommendations.append(
                "Consider using more neutral language to reduce political bias"
            )

        if bias_scores["emotional_bias"] > 0.3:
            recommendations.append(
                "Replace emotionally loaded terms with factual descriptions"
            )

        if bias_scores["motivational_bias"] > 0.3:
            recommendations.append(
                "Reduce persuasive language for more objective presentation"
            )

        if bias_scores["certainty_overconfidence"] > 0.3:
            recommendations.append(
                "Qualify absolute statements with appropriate uncertainty markers"
            )

        return recommendations

    def detect_political_bias(self, text: str) -> Dict[str, Any]:
        """
        Detect political bias in the provided text.

        Args:
            text: The text to analyze for political bias.

        Returns:
            Dictionary containing political bias analysis.
        """
        text_lower = text.lower()
        word_count = len(text.split())

        left_count = _count_matches(text_lower, POLITICAL_LEFT_INDICATORS)
        right_count = _count_matches(text_lower, POLITICAL_RIGHT_INDICATORS)

        # Determine leaning
        if left_count == 0 and right_count == 0:
            leaning = "neutral"
        elif left_count > right_count * 1.5:
            leaning = "left"
        elif right_count > left_count * 1.5:
            leaning = "right"
        else:
            leaning = "center"

        # Find indicators
        indicators = []
        for pattern in POLITICAL_LEFT_INDICATORS:
            matches = re.findall(pattern, text_lower)
            indicators.extend([{"term": m, "direction": "left"} for m in matches])
        for pattern in POLITICAL_RIGHT_INDICATORS:
            matches = re.findall(pattern, text_lower)
            indicators.extend([{"term": m, "direction": "right"} for m in matches])

        total = left_count + right_count
        confidence = _normalize_score(total, word_count, sensitivity=30.0) if total > 0 else 0.0

        return {
            "leaning": leaning,
            "confidence": round(confidence, 3),
            "indicators": indicators[:10],
            "left_count": left_count,
            "right_count": right_count,
        }

    def detect_emotional_bias(self, text: str) -> Dict[str, Any]:
        """
        Detect emotional bias and loaded language in text.

        Args:
            text: The text to analyze for emotional bias.

        Returns:
            Dictionary containing emotional bias analysis.
        """
        text_lower = text.lower()
        word_count = len(text.split())

        positive_count = _count_matches(text_lower, EMOTIONAL_POSITIVE_TERMS)
        negative_count = _count_matches(text_lower, EMOTIONAL_NEGATIVE_TERMS)

        # Determine sentiment
        if positive_count == 0 and negative_count == 0:
            sentiment = "neutral"
        elif positive_count > negative_count * 1.5:
            sentiment = "positive"
        elif negative_count > positive_count * 1.5:
            sentiment = "negative"
        else:
            sentiment = "mixed"

        emotional_score = _calculate_emotional_bias(text_lower, word_count)

        # Find loaded terms
        loaded_terms = []
        for pattern in EMOTIONAL_POSITIVE_TERMS:
            loaded_terms.extend(re.findall(pattern, text_lower))
        for pattern in EMOTIONAL_NEGATIVE_TERMS:
            loaded_terms.extend(re.findall(pattern, text_lower))

        return {
            "emotional_score": round(emotional_score, 3),
            "sentiment": sentiment,
            "loaded_terms": list(set(loaded_terms))[:10],
            "neutral_alternatives": [],  # Would require synonym mapping
        }

    def detect_selection_bias(self, text: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Detect selection bias in presented information.

        Args:
            text: The text to analyze for selection bias.
            context: Optional broader context for comparison.

        Returns:
            Dictionary containing selection bias analysis.
        """
        # Selection bias detection requires context comparison
        # For now, we check for one-sidedness indicators
        text_lower = text.lower()

        # Check for one-sided language
        one_sided_indicators = [
            r"\bonly\s+(one|the)\s+(side|view|perspective)\b",
            r"\bignor(e|ing|ed)\b",
            r"\bfail(s|ed)?\s+to\s+mention\b",
            r"\bconveniently\b",
            r"\bcherry.?pick\b",
        ]

        one_sided_count = _count_matches(text_lower, one_sided_indicators)

        has_selection_bias = one_sided_count > 0

        return {
            "has_selection_bias": has_selection_bias,
            "missing_perspectives": [],  # Would require semantic analysis
            "confidence": 0.5 if one_sided_count > 0 else 0.3,
        }

    def get_bias_report(self, text: str) -> Dict[str, Any]:
        """
        Generate a comprehensive bias report for the provided text.

        Args:
            text: The text to generate a bias report for.

        Returns:
            Dictionary containing a comprehensive bias analysis report.
        """
        main_result = self.detect(text)
        political = self.detect_political_bias(text)
        emotional = self.detect_emotional_bias(text)

        return {
            "summary": main_result,
            "political_analysis": political,
            "emotional_analysis": emotional,
            "word_count": len(text.split()),
        }


def detect_bias_stub(text: str) -> Dict[str, Any]:
    """
    Backward-compatible stub that calls the real implementation.

    Args:
        text: The text to analyze for bias.

    Returns:
        Dictionary containing bias detection results.
    """
    return detect_bias(text)
