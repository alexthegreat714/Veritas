"""
Veritas Legislative Functions

This module implements Veritas' legislative capabilities:
- Bill voting based on logic integrity
- Contribution logging for Senate activity
- Adversarial (counter-perspective) contributions

Phase 6: Legislative functions for Congress interaction.

Veritas does NOT decide policy.
Veritas audits and votes based on logic integrity alone.
All processing is deterministic with no ML models.
"""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from logging.handlers import RotatingFileHandler

from app.logic.auditor import audit_text
from app.logic.bias_detector import detect_bias
from app.logic.chain_validator import validate_chain
from app.logic.source_checker import check_sources


# Configure module logger
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = RotatingFileHandler(
        LOG_DIR / "veritas_legislative.log",
        maxBytes=5_000_000,
        backupCount=3
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)


# Thresholds for voting decisions
CONTRADICTION_THRESHOLD = 1  # Any contradiction triggers concern
FALLACY_THRESHOLD = 2  # Multiple fallacies trigger rejection
HIGH_BIAS_THRESHOLD = 0.5  # Emotional/political bias threshold
CERTAINTY_OVERCONFIDENCE_THRESHOLD = 0.6  # Overconfidence threshold
MIN_BILL_LENGTH = 50  # Minimum characters for meaningful analysis
FLAWED_PREMISE_THRESHOLD = 1  # Any flawed premise triggers concern
UNSUPPORTED_JUMP_THRESHOLD = 2  # Multiple unsupported jumps


def vote_on_bill(bill_text: str, bill_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Vote on a bill based strictly on logic, coherence, and bias analysis.

    Veritas does NOT evaluate policy merit, cost, or morality.
    Voting is based on:
    - Logical consistency
    - Presence of contradictions
    - Fallacy detection
    - Bias levels
    - Clarity and structure

    Args:
        bill_text: The full text of the bill to analyze.
        bill_id: Optional bill identifier for logging.

    Returns:
        Dictionary containing:
        - vote: "yes" | "no" | "abstain"
        - confidence: float 0.0-1.0
        - reasons: list of short, unemotional reasons
        - analysis_summary: brief summary of findings
    """
    logger.info(f"Voting on bill: {bill_id or 'unknown'} ({len(bill_text)} chars)")

    # Handle edge cases
    if not bill_text or not bill_text.strip():
        logger.warning("Empty bill text received")
        return {
            "vote": "abstain",
            "confidence": 0.0,
            "reasons": ["Bill text is empty or missing"],
            "analysis_summary": "No content to analyze",
        }

    if len(bill_text.strip()) < MIN_BILL_LENGTH:
        logger.warning(f"Bill text too short: {len(bill_text.strip())} chars")
        return {
            "vote": "abstain",
            "confidence": 0.3,
            "reasons": ["Bill text is too brief for meaningful analysis"],
            "analysis_summary": "Insufficient content for comprehensive review",
        }

    # Run analysis tools
    audit_result = audit_text(bill_text)
    bias_result = detect_bias(bill_text)

    # Extract bill into logical steps if possible (split by sentences/periods)
    sentences = [s.strip() for s in re.split(r'[.!?]+', bill_text) if s.strip()]
    chain_result = validate_chain(sentences) if len(sentences) >= 2 else {
        "gaps": [],
        "contradictions": [],
        "circular_logic": [],
        "flawed_premises": [],
    }

    # Collect issues
    issues: List[str] = []
    severe_issues: List[str] = []

    # Check for contradictions
    contradictions = chain_result.get("contradictions", [])
    if len(contradictions) >= CONTRADICTION_THRESHOLD:
        severe_issues.append(f"Contains {len(contradictions)} contradiction(s)")

    # Check for logical fallacies
    fallacies = audit_result.get("logical_fallacies", [])
    if len(fallacies) >= FALLACY_THRESHOLD:
        severe_issues.append(f"Contains {len(fallacies)} logical fallacies")
    elif len(fallacies) > 0:
        issues.append(f"Contains {len(fallacies)} logical fallacy(ies)")

    # Check for flawed premises
    flawed_premises = chain_result.get("flawed_premises", [])
    if len(flawed_premises) >= FLAWED_PREMISE_THRESHOLD:
        issues.append(f"Contains {len(flawed_premises)} flawed or unverified premise(s)")

    # Check for unsupported jumps
    unsupported_jumps = audit_result.get("unsupported_jumps", [])
    if len(unsupported_jumps) >= UNSUPPORTED_JUMP_THRESHOLD:
        issues.append(f"Contains {len(unsupported_jumps)} unsupported logical jumps")

    # Check for circular logic
    circular = chain_result.get("circular_logic", [])
    if circular:
        severe_issues.append("Contains circular reasoning")

    # Check for high emotional bias
    emotional_bias = bias_result.get("emotional_bias", 0)
    if emotional_bias > HIGH_BIAS_THRESHOLD:
        severe_issues.append(f"High emotional bias detected ({emotional_bias:.2f})")

    # Check for high political bias
    political_bias = bias_result.get("political_bias", 0)
    if political_bias > HIGH_BIAS_THRESHOLD:
        issues.append(f"Political bias detected ({political_bias:.2f})")

    # Check for overconfidence
    certainty = bias_result.get("certainty_overconfidence", 0)
    if certainty > CERTAINTY_OVERCONFIDENCE_THRESHOLD:
        issues.append(f"Overconfident language detected ({certainty:.2f})")

    # Check for reasoning gaps
    gaps = chain_result.get("gaps", [])
    if len(gaps) > 2:
        issues.append(f"Contains {len(gaps)} reasoning gaps")

    # Determine vote
    vote = "yes"
    confidence = 0.85

    if severe_issues:
        vote = "no"
        confidence = min(0.95, 0.7 + len(severe_issues) * 0.1)
    elif len(issues) >= 3:
        vote = "no"
        confidence = 0.7
    elif len(issues) >= 1:
        # Issues present but not severe - reduce confidence but still yes
        vote = "yes"
        confidence = max(0.5, 0.85 - len(issues) * 0.15)

    # Build reasons list
    reasons = severe_issues + issues
    if not reasons:
        reasons = ["No significant logical issues detected", "Structure is coherent"]

    # Build analysis summary
    summary_parts = []
    if fallacies:
        summary_parts.append(f"{len(fallacies)} fallacies")
    if contradictions:
        summary_parts.append(f"{len(contradictions)} contradictions")
    if flawed_premises:
        summary_parts.append(f"{len(flawed_premises)} flawed premises")
    if emotional_bias > 0.3:
        summary_parts.append(f"emotional bias {emotional_bias:.2f}")

    analysis_summary = (
        "Issues: " + ", ".join(summary_parts) if summary_parts
        else "No significant issues found"
    )

    result = {
        "vote": vote,
        "confidence": round(confidence, 3),
        "reasons": reasons,
        "analysis_summary": analysis_summary,
    }

    logger.info(f"Vote result: {vote} (confidence: {confidence:.3f})")

    return result


def contribution_log(entry: Dict[str, Any]) -> None:
    """
    Append a structured contribution to the legislative contributions log.

    Logs only metadata and structured summaries, never raw bill text.

    Args:
        entry: Dictionary containing contribution data with keys:
            - bill_id: Identifier for the bill
            - analysis: Structured analysis results
            - summary: Brief summary of contribution
            - contribution_type: Type of contribution (vote, adversarial, etc.)
    """
    contrib_logger = logging.getLogger("veritas.legislative_contributions")
    contrib_logger.setLevel(logging.INFO)

    if not contrib_logger.handlers:
        handler = RotatingFileHandler(
            LOG_DIR / "veritas_legislative_contributions.log",
            maxBytes=10_000_000,
            backupCount=5
        )
        handler.setFormatter(logging.Formatter('%(message)s'))
        contrib_logger.addHandler(handler)

    # Build log entry with timestamp
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "bill_id": entry.get("bill_id", "unknown"),
        "contribution_type": entry.get("contribution_type", "unspecified"),
        "analysis": _sanitize_analysis(entry.get("analysis", {})),
        "summary": entry.get("summary", ""),
    }

    contrib_logger.info(json.dumps(log_entry))
    logger.debug(f"Contribution logged for bill: {log_entry['bill_id']}")


def _sanitize_analysis(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize analysis data for logging, removing raw text content.

    Args:
        analysis: Raw analysis dictionary.

    Returns:
        Sanitized analysis with only metadata.
    """
    sanitized = {}

    # Copy simple fields
    for key in ["vote", "confidence", "requires_review"]:
        if key in analysis:
            sanitized[key] = analysis[key]

    # Convert lists to counts
    for key in ["reasons", "counterpoints", "risk_flags"]:
        if key in analysis and isinstance(analysis[key], list):
            sanitized[f"{key}_count"] = len(analysis[key])

    # Include summary if present
    if "analysis_summary" in analysis:
        sanitized["analysis_summary"] = analysis["analysis_summary"]

    return sanitized


def adversarial_contribution(
    bill_text: str,
    bill_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate adversarial (devil's advocate) contribution for a bill.

    Purpose: Surface potential issues that may be missed during groupthink.
    This is NOT a vote - it's a structured critique to ensure thorough review.

    Identifies:
    - Edge-case flaws
    - Hidden assumptions
    - Potential fallacies
    - Alternate interpretations
    - Structural weaknesses

    Args:
        bill_text: The full text of the bill to analyze.
        bill_id: Optional bill identifier for logging.

    Returns:
        Dictionary containing:
        - counterpoints: list of structured issues
        - risk_flags: list of specific risks detected
        - requires_review: bool indicating if major issues found
        - hidden_assumptions: list of detected assumptions
    """
    logger.info(f"Generating adversarial contribution for bill: {bill_id or 'unknown'}")

    if not bill_text or not bill_text.strip():
        return {
            "counterpoints": ["No bill text provided for analysis"],
            "risk_flags": ["missing_content"],
            "requires_review": True,
            "hidden_assumptions": [],
        }

    # Run analysis tools
    audit_result = audit_text(bill_text)
    bias_result = detect_bias(bill_text)

    # Split into logical steps
    sentences = [s.strip() for s in re.split(r'[.!?]+', bill_text) if s.strip()]
    chain_result = validate_chain(sentences) if len(sentences) >= 2 else {
        "gaps": [],
        "contradictions": [],
        "circular_logic": [],
        "flawed_premises": [],
    }

    counterpoints: List[Dict[str, Any]] = []
    risk_flags: List[str] = []
    hidden_assumptions: List[str] = []

    # Surface logical fallacies as counterpoints
    for fallacy in audit_result.get("logical_fallacies", []):
        counterpoints.append({
            "type": "logical_fallacy",
            "issue": fallacy.get("type", "Unknown fallacy"),
            "description": fallacy.get("description", ""),
            "severity": "medium",
        })

    # Surface unsupported jumps
    for jump in audit_result.get("unsupported_jumps", []):
        counterpoints.append({
            "type": "unsupported_claim",
            "issue": "Claim lacks supporting evidence",
            "description": jump.get("reason", ""),
            "severity": "low",
        })

    # Surface flawed premises
    for premise in chain_result.get("flawed_premises", []):
        counterpoints.append({
            "type": "flawed_premise",
            "issue": "Premise requires verification",
            "step": premise.get("step", ""),
            "severity": "high",
        })
        # Extract hidden assumptions
        for issue in premise.get("issues", []):
            if issue.get("type") == "unverified_assumption":
                hidden_assumptions.append(premise.get("step", ""))

    # Surface contradictions
    for contradiction in chain_result.get("contradictions", []):
        counterpoints.append({
            "type": "contradiction",
            "issue": "Internal contradiction detected",
            "between": contradiction.get("between", []),
            "severity": "critical",
        })
        risk_flags.append("internal_contradiction")

    # Surface circular reasoning
    for circular in chain_result.get("circular_logic", []):
        counterpoints.append({
            "type": "circular_reasoning",
            "issue": "Circular logic pattern detected",
            "description": circular.get("description", ""),
            "severity": "high",
        })
        risk_flags.append("circular_reasoning")

    # Surface reasoning gaps
    for gap in chain_result.get("gaps", []):
        counterpoints.append({
            "type": "reasoning_gap",
            "issue": "Missing logical step",
            "description": gap.get("description", "Unexplained jump in reasoning"),
            "severity": "medium",
        })

    # Check for bias-related risks
    emotional_bias = bias_result.get("emotional_bias", 0)
    if emotional_bias > 0.3:
        counterpoints.append({
            "type": "emotional_language",
            "issue": f"Emotional language detected (score: {emotional_bias:.2f})",
            "description": "May influence interpretation rather than inform",
            "severity": "medium" if emotional_bias < 0.5 else "high",
        })
        if emotional_bias > 0.5:
            risk_flags.append("high_emotional_bias")

    political_bias = bias_result.get("political_bias", 0)
    if political_bias > 0.3:
        counterpoints.append({
            "type": "political_language",
            "issue": f"Political framing detected (score: {political_bias:.2f})",
            "description": "Language may not be neutral",
            "severity": "low" if political_bias < 0.5 else "medium",
        })

    certainty = bias_result.get("certainty_overconfidence", 0)
    if certainty > 0.4:
        counterpoints.append({
            "type": "overconfidence",
            "issue": f"Overconfident assertions detected (score: {certainty:.2f})",
            "description": "Claims may lack adequate evidence",
            "severity": "medium",
        })

    # Extract claims as potential points of contention
    claims = audit_result.get("claims", [])
    universal_claims = [c for c in claims if c.get("type") == "universal"]
    if universal_claims:
        hidden_assumptions.append(
            f"Contains {len(universal_claims)} universal claim(s) that may not hold in all cases"
        )

    # Add structural observation if very short
    if len(bill_text.strip()) < 200:
        counterpoints.append({
            "type": "structural",
            "issue": "Brief bill may lack necessary detail",
            "description": "Implementation details may be missing",
            "severity": "low",
        })

    # Determine if review is required
    requires_review = (
        len(risk_flags) > 0 or
        any(cp.get("severity") == "critical" for cp in counterpoints) or
        len([cp for cp in counterpoints if cp.get("severity") == "high"]) >= 2
    )

    # If no counterpoints found, still provide constructive observation
    if not counterpoints:
        counterpoints.append({
            "type": "general",
            "issue": "No significant logical issues detected",
            "description": "Bill appears logically sound from adversarial perspective",
            "severity": "none",
        })

    result = {
        "counterpoints": counterpoints,
        "risk_flags": list(set(risk_flags)),  # Deduplicate
        "requires_review": requires_review,
        "hidden_assumptions": hidden_assumptions,
    }

    logger.info(
        f"Adversarial contribution complete: {len(counterpoints)} counterpoints, "
        f"{len(risk_flags)} risk flags, requires_review={requires_review}"
    )

    return result


class LegislativeHandler:
    """
    Handler class for legislative operations.

    Provides an object-oriented interface for bill voting
    and adversarial contributions with integrated logging.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the legislative handler.

        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}
        self.logger = logging.getLogger("veritas.legislative.handler")

    def vote(
        self,
        bill_text: str,
        bill_id: Optional[str] = None,
        log_contribution: bool = True
    ) -> Dict[str, Any]:
        """
        Vote on a bill and optionally log the contribution.

        Args:
            bill_text: The bill text to analyze.
            bill_id: Optional bill identifier.
            log_contribution: Whether to log the contribution.

        Returns:
            Vote result dictionary.
        """
        result = vote_on_bill(bill_text, bill_id)

        if log_contribution:
            contribution_log({
                "bill_id": bill_id or "unknown",
                "contribution_type": "vote",
                "analysis": result,
                "summary": f"Vote: {result['vote']} (confidence: {result['confidence']})",
            })

        return result

    def adversarial(
        self,
        bill_text: str,
        bill_id: Optional[str] = None,
        log_contribution: bool = True
    ) -> Dict[str, Any]:
        """
        Generate adversarial contribution and optionally log it.

        Args:
            bill_text: The bill text to analyze.
            bill_id: Optional bill identifier.
            log_contribution: Whether to log the contribution.

        Returns:
            Adversarial contribution dictionary.
        """
        result = adversarial_contribution(bill_text, bill_id)

        if log_contribution:
            contribution_log({
                "bill_id": bill_id or "unknown",
                "contribution_type": "adversarial",
                "analysis": result,
                "summary": f"Counterpoints: {len(result['counterpoints'])}, "
                          f"Risk flags: {len(result['risk_flags'])}",
            })

        return result


# Module-level handler instance
_legislative_handler: Optional[LegislativeHandler] = None


def get_legislative_handler() -> LegislativeHandler:
    """Get or create the global LegislativeHandler instance."""
    global _legislative_handler
    if _legislative_handler is None:
        _legislative_handler = LegislativeHandler()
    return _legislative_handler
