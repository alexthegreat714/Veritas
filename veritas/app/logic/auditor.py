"""
Veritas Logic Auditor Module

This module contains the logic auditing functionality for analyzing
text for logical consistency, identifying claims, and detecting fallacies.

Phase 2: Deterministic heuristic-based implementation.
All analysis is rule-based with no ML models.
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
        LOG_DIR / "auditor.log",
        maxBytes=5_000_000,
        backupCount=3
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)


# Static fallacy dictionary with detection patterns
FALLACY_PATTERNS: Dict[str, Dict[str, Any]] = {
    "ad_hominem": {
        "name": "Ad Hominem",
        "patterns": [
            r"\b(you|he|she|they)\s+(are|is)\s+(stupid|idiot|fool|ignorant|dumb)",
            r"\bof course\s+\w+\s+would say that",
            r"\bwhat do you expect from\b",
            r"\btypical\s+(of|for)\s+\w+",
            r"\bcan't trust\s+\w+\s+because\b",
        ],
        "description": "Attacking the person rather than the argument"
    },
    "strawman": {
        "name": "Straw Man",
        "patterns": [
            r"\bso you('re| are) saying\b",
            r"\bwhat you('re| are) really saying\b",
            r"\bin other words,?\s+you\b",
            r"\bthat's like saying\b",
        ],
        "description": "Misrepresenting someone's argument to make it easier to attack"
    },
    "circular_reasoning": {
        "name": "Circular Reasoning",
        "patterns": [
            r"\bbecause\s+it\s+(is|just is)\b",
            r"\bit's true because\s+.{0,30}\s+true\b",
            r"\bthe reason is because\b",
            r"\bby definition\b.*\btherefore\b",
        ],
        "description": "Using the conclusion as a premise"
    },
    "false_dichotomy": {
        "name": "False Dichotomy",
        "patterns": [
            r"\beither\s+.{5,50}\s+or\s+.{5,50}(?!or)\b",
            r"\byou('re| are) either with us or against us\b",
            r"\bthere('s| is) (only\s+)?(two|2)\s+(choices?|options?|ways?)\b",
            r"\bit's (either|one) or the other\b",
        ],
        "description": "Presenting only two options when more exist"
    },
    "appeal_to_authority": {
        "name": "Appeal to Authority",
        "patterns": [
            r"\bexperts?\s+(say|agree|believe|think)\b",
            r"\bscientists?\s+(say|agree|believe|think)\b",
            r"\baccording to\s+\w+,?\s+(it's|this is)\s+(true|fact|proven)\b",
            r"\b(doctor|professor|expert)\s+\w+\s+(says?|said)\b",
        ],
        "description": "Using authority as evidence without proper justification"
    },
    "appeal_to_emotion": {
        "name": "Appeal to Emotion",
        "patterns": [
            r"\bthink of the children\b",
            r"\bhow would you feel if\b",
            r"\bimagine\s+(if|how)\b.*\bfeel\b",
            r"\bwon't somebody think of\b",
        ],
        "description": "Using emotional manipulation instead of logical argument"
    },
    "slippery_slope": {
        "name": "Slippery Slope",
        "patterns": [
            r"\bif we (allow|let|permit)\s+.{5,50},?\s+(then\s+)?(next|soon|eventually)\b",
            r"\bwhere does it end\b",
            r"\bfirst\s+.{5,30},?\s+then\s+.{5,30},?\s+(and\s+)?then\b",
            r"\bwhat's next\b",
        ],
        "description": "Assuming one event will lead to extreme consequences without justification"
    },
    "red_herring": {
        "name": "Red Herring",
        "patterns": [
            r"\bbut what about\b",
            r"\bthe real issue is\b",
            r"\blet's not forget\b.*\binstead\b",
            r"\bmore importantly\b.*(?<!relevant)\b",
        ],
        "description": "Introducing irrelevant information to distract from the main issue"
    },
    "hasty_generalization": {
        "name": "Hasty Generalization",
        "patterns": [
            r"\ball\s+\w+\s+(are|is|do|does|have|has)\b",
            r"\beveryone\s+(knows?|thinks?|believes?|says?)\b",
            r"\bnobody\s+(ever|really)?\s*(knows?|thinks?|believes?)\b",
            r"\balways\b.*\bnever\b|\bnever\b.*\balways\b",
        ],
        "description": "Drawing broad conclusions from limited examples"
    },
    "false_cause": {
        "name": "False Cause",
        "patterns": [
            r"\bafter\s+.{5,30},?\s+(therefore|so|thus|hence)\b",
            r"\bbecause\s+.{5,30}\s+happened\s+(before|first)\b",
            r"\bever since\s+.{5,30},?\s+.{5,30}\s+happened\b",
            r"\bcaused by\b.*\bbefore\b",
        ],
        "description": "Assuming causation from correlation or sequence"
    },
}

# Patterns for detecting claims
CLAIM_INDICATORS = [
    r"(?:^|[.!?]\s+)([A-Z][^.!?]*(?:is|are|was|were|will be|has been|have been)[^.!?]*[.!?])",
    r"(?:^|[.!?]\s+)([A-Z][^.!?]*(?:shows?|proves?|demonstrates?|indicates?)[^.!?]*[.!?])",
    r"(?:^|[.!?]\s+)([A-Z][^.!?]*(?:always|never|every|all|none|no one)[^.!?]*[.!?])",
    r"(?:^|[.!?]\s+)([A-Z][^.!?]*(?:must|should|ought to|need to)[^.!?]*[.!?])",
    r"(?:^|[.!?]\s+)([A-Z][^.!?]*(?:fact|truth|reality|evidence)[^.!?]*[.!?])",
]

# Patterns for causal/conclusion markers (potential unsupported jumps)
CAUSAL_MARKERS = [
    r"\b(therefore|thus|hence|consequently|so|accordingly)\b",
    r"\b(because|since|as a result|due to|owing to)\b",
    r"\b(proves?|shows?|demonstrates?|implies?|means?)\b",
    r"\b(clearly|obviously|evidently|certainly|undoubtedly)\b",
]

# Contradiction detection patterns
NEGATION_PAIRS = [
    (r"\bis\b", r"\bis not\b|\bisn't\b"),
    (r"\bare\b", r"\bare not\b|\baren't\b"),
    (r"\bwill\b", r"\bwill not\b|\bwon't\b"),
    (r"\bcan\b", r"\bcannot\b|\bcan't\b"),
    (r"\bdoes\b", r"\bdoes not\b|\bdoesn't\b"),
    (r"\bhas\b", r"\bhas not\b|\bhasn't\b"),
    (r"\btrue\b", r"\bfalse\b|\bnot true\b|\buntrue\b"),
    (r"\balways\b", r"\bnever\b"),
    (r"\beveryone\b", r"\bno one\b|\bnobody\b"),
    (r"\ball\b", r"\bnone\b|\bno\b"),
]

# Overgeneralization indicators
OVERGENERALIZATION_PATTERNS = [
    r"\balways\b",
    r"\bnever\b",
    r"\beveryone\b",
    r"\bnobody\b",
    r"\bno one\b",
    r"\ball\s+\w+\b",
    r"\bnothing\b",
    r"\beverything\b",
    r"\bcompletely\b",
    r"\btotally\b",
    r"\babsolutely\b",
    r"\bentirely\b",
]


def audit_text(text: str) -> Dict[str, Any]:
    """
    Audit text for logical consistency, claims, fallacies, and reasoning issues.

    Args:
        text: The text to audit.

    Returns:
        Dictionary containing:
        - claims: List of extracted factual or assertive statements
        - logical_fallacies: List of detected fallacies by name
        - inconsistencies: List of contradictions within the text
        - unsupported_jumps: List of leaps in reasoning or missing links
    """
    logger.info(f"Auditing text of length {len(text)}")
    logger.debug(f"Input text: {text[:500]}...")

    if not text or not text.strip():
        result = {
            "claims": [],
            "logical_fallacies": [],
            "inconsistencies": [],
            "unsupported_jumps": [],
        }
        logger.info(f"Output: {result}")
        return result

    text_lower = text.lower()
    sentences = _split_sentences(text)

    claims = _extract_claims(text, sentences)
    fallacies = _detect_fallacies(text, text_lower)
    inconsistencies = _detect_inconsistencies(sentences)
    unsupported_jumps = _detect_unsupported_jumps(text, text_lower, sentences)

    result = {
        "claims": claims,
        "logical_fallacies": fallacies,
        "inconsistencies": inconsistencies,
        "unsupported_jumps": unsupported_jumps,
    }

    logger.info(f"Audit complete: {len(claims)} claims, {len(fallacies)} fallacies, "
                f"{len(inconsistencies)} inconsistencies, {len(unsupported_jumps)} jumps")
    logger.debug(f"Output: {result}")

    return result


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def _extract_claims(text: str, sentences: List[str]) -> List[Dict[str, Any]]:
    """Extract factual or assertive claims from text."""
    claims = []
    seen_claims = set()

    for sentence in sentences:
        sentence_stripped = sentence.strip()
        if len(sentence_stripped) < 10:
            continue

        # Check for claim indicators
        is_claim = False
        claim_type = "assertion"

        # Check for factual claim patterns
        if re.search(r'\b(is|are|was|were)\s+\w+', sentence, re.IGNORECASE):
            is_claim = True
            claim_type = "factual"

        # Check for universal claims
        if re.search(r'\b(all|every|always|never|none|no one)\b', sentence, re.IGNORECASE):
            is_claim = True
            claim_type = "universal"

        # Check for causal claims
        if re.search(r'\b(causes?|leads? to|results? in|because)\b', sentence, re.IGNORECASE):
            is_claim = True
            claim_type = "causal"

        # Check for normative claims
        if re.search(r'\b(should|must|ought|need to|have to)\b', sentence, re.IGNORECASE):
            is_claim = True
            claim_type = "normative"

        if is_claim and sentence_stripped not in seen_claims:
            seen_claims.add(sentence_stripped)
            claims.append({
                "text": sentence_stripped,
                "type": claim_type,
                "position": text.find(sentence_stripped),
            })

    return claims


def _detect_fallacies(text: str, text_lower: str) -> List[Dict[str, Any]]:
    """Detect logical fallacies using pattern matching."""
    fallacies = []

    for fallacy_key, fallacy_info in FALLACY_PATTERNS.items():
        for pattern in fallacy_info["patterns"]:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                fallacies.append({
                    "type": fallacy_info["name"],
                    "description": fallacy_info["description"],
                    "matched_text": text[match.start():match.end()],
                    "position": match.start(),
                })

    # Deduplicate by position (keep first match at each position)
    seen_positions = set()
    unique_fallacies = []
    for f in fallacies:
        if f["position"] not in seen_positions:
            seen_positions.add(f["position"])
            unique_fallacies.append(f)

    return unique_fallacies


def _detect_inconsistencies(sentences: List[str]) -> List[Dict[str, Any]]:
    """Detect contradictions and inconsistencies between sentences."""
    inconsistencies = []

    for i, sent1 in enumerate(sentences):
        sent1_lower = sent1.lower()
        for j, sent2 in enumerate(sentences[i + 1:], start=i + 1):
            sent2_lower = sent2.lower()

            # Check for direct negation patterns
            for pos_pattern, neg_pattern in NEGATION_PAIRS:
                # Find shared subjects/objects
                words1 = set(re.findall(r'\b\w{4,}\b', sent1_lower))
                words2 = set(re.findall(r'\b\w{4,}\b', sent2_lower))
                common_words = words1 & words2

                if len(common_words) >= 2:  # At least 2 significant words in common
                    has_pos1 = re.search(pos_pattern, sent1_lower)
                    has_neg1 = re.search(neg_pattern, sent1_lower)
                    has_pos2 = re.search(pos_pattern, sent2_lower)
                    has_neg2 = re.search(neg_pattern, sent2_lower)

                    # One positive, one negative with common content
                    if (has_pos1 and has_neg2) or (has_neg1 and has_pos2):
                        inconsistencies.append({
                            "sentence_1": sent1,
                            "sentence_2": sent2,
                            "type": "potential_contradiction",
                            "common_terms": list(common_words)[:5],
                        })
                        break

    return inconsistencies


def _detect_unsupported_jumps(text: str, text_lower: str, sentences: List[str]) -> List[Dict[str, Any]]:
    """Detect unsupported logical jumps and leaps in reasoning."""
    jumps = []

    for i, sentence in enumerate(sentences):
        sentence_lower = sentence.lower()

        # Check for causal markers without preceding justification
        for pattern in CAUSAL_MARKERS:
            if re.search(pattern, sentence_lower):
                # Check if it's at the beginning (no prior justification)
                if i == 0:
                    jumps.append({
                        "text": sentence,
                        "type": "unsupported_conclusion",
                        "reason": "Conclusion marker without preceding premises",
                        "position": i,
                    })
                # Check for overgeneralization with causal claim
                elif re.search(r'|'.join(OVERGENERALIZATION_PATTERNS), sentence_lower):
                    jumps.append({
                        "text": sentence,
                        "type": "overgeneralized_conclusion",
                        "reason": "Conclusion uses absolute terms without sufficient support",
                        "position": i,
                    })
                break

        # Check for assertion markers that suggest unjustified certainty
        certainty_markers = re.findall(
            r'\b(obviously|clearly|certainly|undoubtedly|definitely|without doubt)\b',
            sentence_lower
        )
        if certainty_markers:
            jumps.append({
                "text": sentence,
                "type": "unjustified_certainty",
                "reason": f"Uses certainty markers ({', '.join(certainty_markers)}) without evidence",
                "position": i,
            })

    return jumps


class LogicAuditor:
    """
    Logic Auditor for analyzing text for logical consistency and fallacies.

    This class provides comprehensive logic auditing capabilities including:
    - Identification of logical fallacies (ad hominem, straw man, false dichotomy, etc.)
    - Detection of unsupported claims
    - Analysis of argument structure
    - Assessment of logical consistency
    - Identification of contradictions

    Phase 2: Deterministic heuristic-based implementation.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LogicAuditor.

        Args:
            config: Optional configuration dictionary for auditor settings.
        """
        self.config = config or {}
        self._initialized = True
        logger.info("LogicAuditor initialized")

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze text for logical consistency and identify issues.

        Args:
            text: The text to analyze for logical issues.

        Returns:
            Dictionary containing analysis results.
        """
        result = audit_text(text)
        # Add additional metadata
        result["consistency_score"] = self._calculate_consistency_score(result)
        result["recommendations"] = self._generate_recommendations(result)
        return result

    def _calculate_consistency_score(self, audit_result: Dict[str, Any]) -> float:
        """Calculate a consistency score based on audit findings."""
        score = 1.0

        # Deduct for fallacies
        score -= len(audit_result.get("logical_fallacies", [])) * 0.1

        # Deduct for inconsistencies
        score -= len(audit_result.get("inconsistencies", [])) * 0.15

        # Deduct for unsupported jumps
        score -= len(audit_result.get("unsupported_jumps", [])) * 0.08

        return max(0.0, min(1.0, score))

    def _generate_recommendations(self, audit_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on audit findings."""
        recommendations = []

        if audit_result.get("logical_fallacies"):
            fallacy_types = set(f["type"] for f in audit_result["logical_fallacies"])
            recommendations.append(
                f"Review and address logical fallacies: {', '.join(fallacy_types)}"
            )

        if audit_result.get("inconsistencies"):
            recommendations.append(
                "Resolve contradictory statements to improve logical consistency"
            )

        if audit_result.get("unsupported_jumps"):
            recommendations.append(
                "Provide supporting evidence for conclusions and causal claims"
            )

        return recommendations

    def identify_fallacies(self, text: str) -> List[Dict[str, Any]]:
        """
        Identify logical fallacies in the provided text.

        Args:
            text: The text to scan for logical fallacies.

        Returns:
            List of detected fallacies with details.
        """
        text_lower = text.lower()
        return _detect_fallacies(text, text_lower)

    def extract_claims(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract factual claims from the provided text.

        Args:
            text: The text to extract claims from.

        Returns:
            List of extracted claims with metadata.
        """
        sentences = _split_sentences(text)
        return _extract_claims(text, sentences)

    def check_consistency(self, statements: List[str]) -> Dict[str, Any]:
        """
        Check a list of statements for internal consistency.

        Args:
            statements: List of statements to check for consistency.

        Returns:
            Dictionary containing consistency analysis results.
        """
        inconsistencies = _detect_inconsistencies(statements)
        is_consistent = len(inconsistencies) == 0
        confidence = 1.0 - (len(inconsistencies) * 0.2)

        return {
            "is_consistent": is_consistent,
            "conflicts": inconsistencies,
            "confidence": max(0.0, min(1.0, confidence)),
        }


def audit_text_stub(text: str) -> Dict[str, Any]:
    """
    Backward-compatible stub that calls the real implementation.

    Args:
        text: The text to audit.

    Returns:
        Dictionary containing audit results.
    """
    return audit_text(text)
