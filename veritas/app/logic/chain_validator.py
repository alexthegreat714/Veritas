"""
Veritas Chain-of-Thought Validator Module

This module contains functionality for validating chains of reasoning
to ensure logical coherence and proper argumentation flow.

Phase 2: Deterministic heuristic-based implementation.
All analysis is rule-based with no ML models.
"""

import logging
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from logging.handlers import RotatingFileHandler


# Configure module logger
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = RotatingFileHandler(
        LOG_DIR / "chain_validator.log",
        maxBytes=5_000_000,
        backupCount=3
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)


# Transition/connection indicators
TRANSITION_INDICATORS = [
    r"\b(therefore|thus|hence|consequently|so|accordingly)\b",
    r"\b(because|since|as|given that|due to)\b",
    r"\b(then|next|finally|subsequently)\b",
    r"\b(this (means|implies|shows|proves))\b",
    r"\b(it follows that|we can conclude)\b",
    r"\b(first|second|third|furthermore|moreover|additionally)\b",
]

# Flawed premise indicators
FLAWED_PREMISE_INDICATORS = [
    r"\b(assume|assuming|suppose|supposing)\b",
    r"\b(let's say|say that|imagine)\b",
    r"\b(if we accept|granted that)\b",
    r"\b(for the sake of argument)\b",
    r"\b(arguably|presumably|probably)\b",
    r"\b(might|may|could|possibly)\b",
]

# Contradiction indicators within steps
CONTRADICTION_PATTERNS = [
    (r"\b(is|are)\b", r"\b(is not|isn't|are not|aren't)\b"),
    (r"\b(will)\b", r"\b(will not|won't)\b"),
    (r"\b(can)\b", r"\b(cannot|can't)\b"),
    (r"\b(true)\b", r"\b(false|not true|untrue)\b"),
    (r"\b(always)\b", r"\b(never)\b"),
    (r"\b(all)\b", r"\b(none|no)\b"),
    (r"\b(increase)\b", r"\b(decrease)\b"),
    (r"\b(positive)\b", r"\b(negative)\b"),
    (r"\b(more)\b", r"\b(less|fewer)\b"),
]

# Circular reasoning indicators
CIRCULAR_INDICATORS = [
    r"\b(as (we|i) (said|stated|mentioned))\b",
    r"\b(as (noted|established) (earlier|above|before))\b",
    r"\b(going back to)\b",
    r"\b(this proves? (my|our|the) (original|initial))\b",
]


def validate_chain(steps: List[str]) -> Dict[str, Any]:
    """
    Validate a chain of reasoning steps for logical coherence.

    Args:
        steps: List of reasoning steps to validate.

    Returns:
        Dictionary containing:
        - gaps: List of missing steps between reasoning points
        - contradictions: List of incompatible steps
        - circular_logic: List of steps that reference themselves
        - flawed_premises: List of steps with weak premises
    """
    logger.info(f"Validating chain with {len(steps)} steps")
    logger.debug(f"Input steps: {steps}")

    if not steps:
        result = {
            "gaps": [],
            "contradictions": [],
            "circular_logic": [],
            "flawed_premises": [],
        }
        logger.info(f"Output: {result}")
        return result

    gaps = _detect_gaps(steps)
    contradictions = _detect_contradictions(steps)
    circular_logic = _detect_circular_logic(steps)
    flawed_premises = _detect_flawed_premises(steps)

    result = {
        "gaps": gaps,
        "contradictions": contradictions,
        "circular_logic": circular_logic,
        "flawed_premises": flawed_premises,
    }

    logger.info(f"Validation complete: {len(gaps)} gaps, {len(contradictions)} contradictions, "
                f"{len(circular_logic)} circular, {len(flawed_premises)} flawed premises")
    logger.debug(f"Output: {result}")

    return result


def _normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    # Remove punctuation and extra whitespace, lowercase
    text = re.sub(r'[^\w\s]', '', text.lower())
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _extract_key_terms(text: str) -> Set[str]:
    """Extract significant terms from text (words with 4+ characters)."""
    text_lower = text.lower()
    # Extract words with 4+ characters, excluding common stop words
    stop_words = {
        'that', 'this', 'with', 'from', 'have', 'been', 'were', 'they',
        'their', 'what', 'when', 'where', 'which', 'while', 'would', 'could',
        'should', 'about', 'after', 'before', 'being', 'because', 'between',
    }
    words = set(re.findall(r'\b\w{4,}\b', text_lower))
    return words - stop_words


def _calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two texts."""
    return SequenceMatcher(None, _normalize_text(text1), _normalize_text(text2)).ratio()


def _has_logical_connection(step1: str, step2: str) -> Tuple[bool, float]:
    """
    Check if two steps have a logical connection.
    Returns (has_connection, confidence).
    """
    step1_lower = step1.lower()
    step2_lower = step2.lower()

    # Check for explicit transition words in step2
    has_transition = any(
        re.search(pattern, step2_lower)
        for pattern in TRANSITION_INDICATORS
    )

    # Check for shared key terms
    terms1 = _extract_key_terms(step1)
    terms2 = _extract_key_terms(step2)
    common_terms = terms1 & terms2
    term_overlap = len(common_terms) / max(len(terms1 | terms2), 1)

    # Calculate overall connection score
    # Transition words alone are not sufficient - need semantic overlap too
    connection_score = 0.0
    if has_transition and term_overlap > 0:
        # Transition with some term overlap = good connection
        connection_score += 0.4
    elif has_transition:
        # Transition without term overlap = suspicious (claimed connection but no semantic link)
        connection_score += 0.1  # Small boost but not enough to validate
    connection_score += term_overlap * 0.6

    # Connection requires either good term overlap OR transition with some overlap
    has_connection = connection_score > 0.2 and (term_overlap > 0.05 or (has_transition and term_overlap > 0))

    return has_connection, connection_score


def _detect_gaps(steps: List[str]) -> List[Dict[str, Any]]:
    """Detect gaps in reasoning where steps don't follow logically."""
    gaps = []

    if len(steps) < 2:
        return gaps

    for i in range(len(steps) - 1):
        current_step = steps[i]
        next_step = steps[i + 1]

        has_connection, connection_score = _has_logical_connection(current_step, next_step)

        if not has_connection:
            # Determine severity based on connection score
            if connection_score < 0.1:
                severity = "major"
            elif connection_score < 0.2:
                severity = "moderate"
            else:
                severity = "minor"

            gaps.append({
                "position": i + 1,
                "before_step": current_step,
                "after_step": next_step,
                "severity": severity,
                "connection_score": round(connection_score, 3),
                "suggestion": "Consider adding an intermediate step to connect these ideas",
            })

    return gaps


def _detect_contradictions(steps: List[str]) -> List[Dict[str, Any]]:
    """Detect contradictions between steps in the chain."""
    contradictions = []

    for i, step1 in enumerate(steps):
        step1_lower = step1.lower()
        terms1 = _extract_key_terms(step1)

        for j, step2 in enumerate(steps[i + 1:], start=i + 1):
            step2_lower = step2.lower()
            terms2 = _extract_key_terms(step2)

            # Check if steps share significant content
            common_terms = terms1 & terms2
            if len(common_terms) < 2:
                continue

            # Check for contradiction patterns
            for pos_pattern, neg_pattern in CONTRADICTION_PATTERNS:
                has_pos1 = re.search(pos_pattern, step1_lower)
                has_neg1 = re.search(neg_pattern, step1_lower)
                has_pos2 = re.search(pos_pattern, step2_lower)
                has_neg2 = re.search(neg_pattern, step2_lower)

                # One step has positive, other has negative form
                if (has_pos1 and has_neg2) or (has_neg1 and has_pos2):
                    contradictions.append({
                        "step_1_index": i,
                        "step_1": step1,
                        "step_2_index": j,
                        "step_2": step2,
                        "common_terms": list(common_terms)[:5],
                        "type": "logical_negation",
                    })
                    break

    return contradictions


def _detect_circular_logic(steps: List[str]) -> List[Dict[str, Any]]:
    """Detect circular reasoning where later steps reference earlier conclusions."""
    circular = []

    if len(steps) < 2:
        return circular

    first_step = steps[0]
    first_terms = _extract_key_terms(first_step)
    first_normalized = _normalize_text(first_step)

    for i, step in enumerate(steps[1:], start=1):
        step_lower = step.lower()
        step_terms = _extract_key_terms(step)

        # Check for explicit back-references
        has_back_reference = any(
            re.search(pattern, step_lower)
            for pattern in CIRCULAR_INDICATORS
        )

        # Check for high similarity to first step (potential rephrasing)
        similarity = _calculate_similarity(first_step, step)

        # Check if later step essentially restates first step
        term_overlap = len(first_terms & step_terms) / max(len(first_terms), 1)

        if has_back_reference:
            circular.append({
                "step_index": i,
                "step": step,
                "type": "explicit_back_reference",
                "references_step": 0,
                "explanation": "Step explicitly references earlier reasoning",
            })
        elif similarity > 0.6 and i > 1:
            circular.append({
                "step_index": i,
                "step": step,
                "type": "rephrased_premise",
                "references_step": 0,
                "similarity_score": round(similarity, 3),
                "explanation": "Step appears to rephrase the initial premise as a conclusion",
            })
        elif term_overlap > 0.7 and i > 1:
            circular.append({
                "step_index": i,
                "step": step,
                "type": "term_repetition",
                "references_step": 0,
                "term_overlap": round(term_overlap, 3),
                "explanation": "Step uses same key terms as premise without new information",
            })

    return circular


def _detect_flawed_premises(steps: List[str]) -> List[Dict[str, Any]]:
    """Detect steps with weak or flawed premises."""
    flawed = []

    for i, step in enumerate(steps):
        step_lower = step.lower()
        issues = []

        # Check for assumption indicators
        assumption_matches = []
        for pattern in FLAWED_PREMISE_INDICATORS:
            matches = re.findall(pattern, step_lower)
            if matches:
                assumption_matches.extend(matches)

        if assumption_matches:
            issues.append({
                "type": "unverified_assumption",
                "indicators": assumption_matches[:3],
            })

        # First step is especially important - check for weak foundation
        if i == 0:
            # Check if first step lacks factual grounding
            factual_indicators = [
                r"\b(research|study|data|evidence|statistics)\b",
                r"\b(according to|based on|shown by)\b",
                r"\b(fact|proven|demonstrated)\b",
            ]
            has_factual_grounding = any(
                re.search(pattern, step_lower)
                for pattern in factual_indicators
            )

            if not has_factual_grounding and assumption_matches:
                issues.append({
                    "type": "weak_foundation",
                    "explanation": "Initial premise relies on assumptions without factual support",
                })

        if issues:
            flawed.append({
                "step_index": i,
                "step": step,
                "issues": issues,
            })

    return flawed


class ChainValidator:
    """
    Chain-of-Thought Validator for analyzing reasoning chains.

    This class provides comprehensive chain validation capabilities including:
    - Step-by-step logical flow analysis
    - Gap detection in reasoning chains
    - Circular reasoning identification
    - Premise-conclusion validation
    - Inference strength assessment
    - Hidden assumption detection

    Phase 2: Deterministic heuristic-based implementation.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the ChainValidator.

        Args:
            config: Optional configuration dictionary for validator settings.
        """
        self.config = config or {}
        self.max_chain_depth = self.config.get("max_chain_depth", 50)
        self._initialized = True
        logger.info("ChainValidator initialized")

    def validate(self, chain: List[str], context: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate a complete chain of reasoning.

        Args:
            chain: List of reasoning steps to validate.
            context: Optional context for the reasoning chain.

        Returns:
            Dictionary containing validation results.
        """
        result = validate_chain(chain)

        # Calculate overall validity
        total_issues = (
            len(result["gaps"]) +
            len(result["contradictions"]) +
            len(result["circular_logic"]) +
            len(result["flawed_premises"])
        )

        is_valid = total_issues == 0
        confidence = max(0.0, 1.0 - (total_issues * 0.15))

        # Generate step validations
        step_validations = self._generate_step_validations(chain, result)

        return {
            "is_valid": is_valid,
            "step_validations": step_validations,
            "gaps": result["gaps"],
            "circular_references": result["circular_logic"],
            "contradictions": result["contradictions"],
            "flawed_premises": result["flawed_premises"],
            "confidence": round(confidence, 3),
        }

    def _generate_step_validations(
        self, chain: List[str], validation_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate individual validation results for each step."""
        step_validations = []

        # Create lookup sets for problematic steps
        gap_positions = {g["position"] for g in validation_result["gaps"]}
        contradiction_indices = set()
        for c in validation_result["contradictions"]:
            contradiction_indices.add(c["step_1_index"])
            contradiction_indices.add(c["step_2_index"])
        circular_indices = {c["step_index"] for c in validation_result["circular_logic"]}
        flawed_indices = {f["step_index"] for f in validation_result["flawed_premises"]}

        for i, step in enumerate(chain):
            issues = []

            if i in gap_positions:
                issues.append("gap_before_this_step")
            if i in contradiction_indices:
                issues.append("contradicts_another_step")
            if i in circular_indices:
                issues.append("circular_reasoning")
            if i in flawed_indices:
                issues.append("flawed_premise")

            step_validations.append({
                "step_index": i,
                "step": step[:100] + "..." if len(step) > 100 else step,
                "is_valid": len(issues) == 0,
                "issues": issues,
            })

        return step_validations

    def validate_step(self, premise: str, conclusion: str) -> Dict[str, Any]:
        """
        Validate a single reasoning step from premise to conclusion.

        Args:
            premise: The premise or prior reasoning step.
            conclusion: The conclusion drawn from the premise.

        Returns:
            Dictionary containing step validation results.
        """
        has_connection, connection_score = _has_logical_connection(premise, conclusion)

        # Determine inference type based on language patterns
        conclusion_lower = conclusion.lower()
        if re.search(r'\b(must|necessarily|always)\b', conclusion_lower):
            inference_type = "deductive"
        elif re.search(r'\b(probably|likely|suggests|indicates)\b', conclusion_lower):
            inference_type = "inductive"
        elif re.search(r'\b(could|might|possibly|may)\b', conclusion_lower):
            inference_type = "abductive"
        else:
            inference_type = "unknown"

        issues = []
        if not has_connection:
            issues.append("weak_logical_connection")

        # Check for overgeneralization in conclusion
        if re.search(r'\b(all|always|never|everyone|nobody)\b', conclusion_lower):
            issues.append("potential_overgeneralization")

        return {
            "is_valid": has_connection and len(issues) == 0,
            "inference_type": inference_type,
            "strength": round(connection_score, 3),
            "issues": issues,
        }

    def detect_gaps(self, chain: List[str]) -> List[Dict[str, Any]]:
        """
        Detect gaps in a reasoning chain where steps don't follow logically.

        Args:
            chain: List of reasoning steps to analyze.

        Returns:
            List of detected gaps with details.
        """
        return _detect_gaps(chain)

    def detect_circular_reasoning(self, chain: List[str]) -> Dict[str, Any]:
        """
        Detect circular reasoning patterns in a chain.

        Args:
            chain: List of reasoning steps to analyze.

        Returns:
            Dictionary containing circular reasoning analysis.
        """
        circular = _detect_circular_logic(chain)

        return {
            "has_circular_reasoning": len(circular) > 0,
            "cycles": circular,
            "affected_steps": [c["step_index"] for c in circular],
        }

    def extract_hidden_assumptions(self, chain: List[str]) -> List[Dict[str, Any]]:
        """
        Extract hidden or implicit assumptions in a reasoning chain.

        Args:
            chain: List of reasoning steps to analyze.

        Returns:
            List of detected hidden assumptions.
        """
        assumptions = []

        for i, step in enumerate(chain):
            step_lower = step.lower()

            # Check for implicit assumptions through language patterns
            implicit_patterns = [
                (r"\bof course\b", "unexamined common knowledge"),
                (r"\beveryone knows\b", "appeal to common belief"),
                (r"\bnaturally\b", "assumed natural consequence"),
                (r"\bobviously\b", "unexamined obvious claim"),
                (r"\bit follows that\b", "assumed logical connection"),
            ]

            for pattern, assumption_type in implicit_patterns:
                if re.search(pattern, step_lower):
                    assumptions.append({
                        "step_index": i,
                        "step": step,
                        "assumption_type": assumption_type,
                        "importance": "medium",
                        "validity": "unverified",
                    })

        return assumptions

    def get_chain_summary(self, chain: List[str]) -> Dict[str, Any]:
        """
        Generate a summary analysis of a reasoning chain.

        Args:
            chain: List of reasoning steps to summarize.

        Returns:
            Dictionary containing a comprehensive summary.
        """
        validation = self.validate(chain)

        return {
            "total_steps": len(chain),
            "is_valid": validation["is_valid"],
            "confidence": validation["confidence"],
            "issues_summary": {
                "gaps": len(validation["gaps"]),
                "contradictions": len(validation["contradictions"]),
                "circular_logic": len(validation["circular_references"]),
                "flawed_premises": len(validation["flawed_premises"]),
            },
            "recommendation": self._get_summary_recommendation(validation),
        }

    def _get_summary_recommendation(self, validation: Dict[str, Any]) -> str:
        """Generate a summary recommendation based on validation results."""
        if validation["is_valid"]:
            return "Chain appears logically sound"

        issues = []
        if validation["gaps"]:
            issues.append("add intermediate steps to bridge logical gaps")
        if validation["contradictions"]:
            issues.append("resolve contradictory statements")
        if validation["circular_references"]:
            issues.append("remove circular reasoning")
        if validation["flawed_premises"]:
            issues.append("strengthen or support weak premises")

        return "Consider: " + "; ".join(issues)


def validate_chain_stub(chain: List[str]) -> Dict[str, Any]:
    """
    Backward-compatible stub that calls the real implementation.

    Args:
        chain: List of reasoning steps to validate.

    Returns:
        Dictionary containing validation results.
    """
    return validate_chain(chain)
