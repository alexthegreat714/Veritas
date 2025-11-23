"""
Veritas Dispute Engine

Phase 5: Dispute Resolution Hooks (Non-Judicial)

This module processes disagreements between agents, classifies dispute types,
and returns structured data for potential escalation routing.

IMPORTANT: Veritas DOES NOT:
- Rule on ethics or law (that's Sophia's domain)
- Rule on security or danger (that's Aegis's domain)
- Override Congress, Sky, or any agent
- Actually escalate or forward events

Veritas only:
- Classifies what kind of disagreement it is
- Provides fact-logic analysis
- Identifies whether external escalation is required
"""

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from app.logic.auditor import audit_text
from app.logic.bias_detector import detect_bias
from app.logic.source_checker import check_sources


logger = logging.getLogger(__name__)


# Keywords that suggest ethical/legal domain (escalate to Sophia)
ETHICAL_LEGAL_KEYWORDS = {
    "ethics", "ethical", "moral", "morality", "law", "legal", "illegal",
    "rights", "justice", "fair", "fairness", "discrimination", "privacy",
    "consent", "harm", "wrong", "right", "duty", "obligation", "principle",
    "values", "virtue", "unethical", "immoral", "unlawful", "constitutional",
}

# Keywords that suggest security/safety domain (escalate to Aegis)
SECURITY_SAFETY_KEYWORDS = {
    "security", "safety", "danger", "dangerous", "threat", "attack",
    "vulnerability", "breach", "compromise", "malicious", "exploit",
    "risk", "hazard", "emergency", "critical", "protect", "defense",
    "intrusion", "unauthorized", "damage", "harm", "crash", "failure",
}

# Keywords that suggest political/governance domain (escalate to Congress)
POLITICAL_GOVERNANCE_KEYWORDS = {
    "policy", "political", "vote", "election", "government", "legislation",
    "congress", "senate", "budget", "tax", "regulation", "public",
    "citizen", "democracy", "authority", "jurisdiction", "mandate",
    "allocation", "resources", "priority", "governance", "constituency",
}


def _extract_claims(audit_result: Dict[str, Any]) -> List[str]:
    """Extract claim texts from audit result."""
    claims = []
    for claim in audit_result.get("claims", []):
        if isinstance(claim, dict):
            claims.append(claim.get("text", claim.get("claim", str(claim))))
        else:
            claims.append(str(claim))
    return claims


def _normalize_claim(claim: str) -> str:
    """Normalize a claim for comparison."""
    # Lowercase and remove extra whitespace
    normalized = claim.lower().strip()
    normalized = re.sub(r'\s+', ' ', normalized)
    # Remove punctuation
    normalized = re.sub(r'[^\w\s]', '', normalized)
    return normalized


def _find_contradictions(claims_a: List[str], claims_b: List[str]) -> List[Dict[str, Any]]:
    """
    Find potential contradictions between two sets of claims.

    Uses simple heuristic matching for negation patterns and
    opposite sentiment indicators.
    """
    contradictions = []

    # Negation patterns
    negation_pairs = [
        (r'\bis\b', r'\bis not\b'),
        (r'\bare\b', r'\bare not\b'),
        (r'\bwill\b', r'\bwill not\b'),
        (r'\bcan\b', r'\bcannot\b'),
        (r'\bshould\b', r'\bshould not\b'),
        (r'\btrue\b', r'\bfalse\b'),
        (r'\bcorrect\b', r'\bincorrect\b'),
        (r'\byes\b', r'\bno\b'),
        (r'\bsupports?\b', r'\bopposes?\b'),
        (r'\baccepts?\b', r'\brejects?\b'),
    ]

    for claim_a in claims_a:
        norm_a = _normalize_claim(claim_a)

        for claim_b in claims_b:
            norm_b = _normalize_claim(claim_b)

            # Check for direct negation patterns
            for pos, neg in negation_pairs:
                if re.search(pos, norm_a) and re.search(neg, norm_b):
                    # Check if claims share significant terms
                    words_a = set(norm_a.split())
                    words_b = set(norm_b.split())
                    overlap = words_a & words_b

                    if len(overlap) >= 2:  # Significant overlap
                        contradictions.append({
                            "claim_a": claim_a,
                            "claim_b": claim_b,
                            "type": "negation",
                            "shared_terms": list(overlap),
                        })
                        break

                elif re.search(neg, norm_a) and re.search(pos, norm_b):
                    words_a = set(norm_a.split())
                    words_b = set(norm_b.split())
                    overlap = words_a & words_b

                    if len(overlap) >= 2:
                        contradictions.append({
                            "claim_a": claim_a,
                            "claim_b": claim_b,
                            "type": "negation",
                            "shared_terms": list(overlap),
                        })
                        break

    return contradictions


def _check_escalation_domain(text_a: str, text_b: str, metadata_a: Dict, metadata_b: Dict) -> str:
    """
    Determine if escalation is needed and to which domain.

    Returns: "none" | "sophia" | "aegis" | "congress"
    """
    combined_text = (text_a + " " + text_b).lower()

    # Count keyword matches for each domain
    ethical_count = sum(1 for kw in ETHICAL_LEGAL_KEYWORDS if kw in combined_text)
    security_count = sum(1 for kw in SECURITY_SAFETY_KEYWORDS if kw in combined_text)
    political_count = sum(1 for kw in POLITICAL_GOVERNANCE_KEYWORDS if kw in combined_text)

    # Check metadata for explicit domain indicators
    for metadata in [metadata_a, metadata_b]:
        domain = metadata.get("domain", "").lower()
        if domain in ["ethics", "legal", "law"]:
            ethical_count += 5
        elif domain in ["security", "safety"]:
            security_count += 5
        elif domain in ["political", "governance", "policy"]:
            political_count += 5

    # Determine escalation based on thresholds
    # Security takes priority (safety first)
    if security_count >= 3:
        return "aegis"

    # Ethical/legal next
    if ethical_count >= 3:
        return "sophia"

    # Political/governance
    if political_count >= 3:
        return "congress"

    return "none"


def _generate_recommendation(
    has_factual: bool,
    has_interpretation: bool,
    has_missing_data: bool,
    escalation: str,
    issues_a: List,
    issues_b: List
) -> str:
    """Generate recommendation based on dispute analysis."""

    # If escalation is needed, recommend forwarding
    if escalation == "sophia":
        return "forward_to_sophia"
    elif escalation == "aegis":
        return "forward_to_aegis"
    elif escalation == "congress":
        return "mediation_by_congress"

    # Missing data case
    if has_missing_data:
        return "request_more_data"

    # Both have significant issues
    if len(issues_a) >= 2 and len(issues_b) >= 2:
        return "inconclusive"

    # Factual disagreement with clear issues on one side
    if has_factual:
        if len(issues_a) > len(issues_b) + 1:
            return "minimal_issue_detected"  # B seems more sound
        elif len(issues_b) > len(issues_a) + 1:
            return "minimal_issue_detected"  # A seems more sound
        else:
            return "request_more_data"  # Need more info to resolve

    # Interpretation disagreement
    if has_interpretation:
        return "mediation_by_congress"  # Policy-level decision needed

    # Default
    return "minimal_issue_detected"


def parse_dispute(agent_a: Dict[str, Any], agent_b: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and analyze a dispute between two agents.

    Args:
        agent_a: Dictionary with keys:
            - agent: str - Agent name (e.g., "Sky", "Aegis", "Aero")
            - text: str - The agent's position/statement
            - metadata: dict - Optional additional context
        agent_b: Same structure as agent_a

    Returns:
        Dictionary containing:
        - agents: [str, str] - Names of disputing agents
        - issues: dict containing:
            - factual_disagreement: bool
            - interpretation_disagreement: bool
            - missing_data: bool
            - logical_issues_A: list
            - logical_issues_B: list
            - contradictions: list
        - needs_escalation: "none" | "sophia" | "aegis" | "congress"
        - recommendation: str
        - analysis: dict - Detailed audit results

    NOTE: Veritas does NOT escalate or forward events.
    It only classifies and reports. Escalation is handled by Sky/n8n.
    """
    logger.info(f"Parsing dispute between {agent_a.get('agent', 'A')} and {agent_b.get('agent', 'B')}")

    # Extract data
    agent_name_a = agent_a.get("agent", "Agent_A")
    agent_name_b = agent_b.get("agent", "Agent_B")
    text_a = agent_a.get("text", "")
    text_b = agent_b.get("text", "")
    metadata_a = agent_a.get("metadata", {})
    metadata_b = agent_b.get("metadata", {})

    # Run audits on both texts
    audit_a = audit_text(text_a) if text_a else {"claims": [], "logical_fallacies": [], "inconsistencies": [], "unsupported_jumps": []}
    audit_b = audit_text(text_b) if text_b else {"claims": [], "logical_fallacies": [], "inconsistencies": [], "unsupported_jumps": []}

    # Run bias detection
    bias_a = detect_bias(text_a) if text_a else {}
    bias_b = detect_bias(text_b) if text_b else {}

    # Extract claims
    claims_a = _extract_claims(audit_a)
    claims_b = _extract_claims(audit_b)

    # Find contradictions
    contradictions = _find_contradictions(claims_a, claims_b)

    # Collect logical issues for each side
    logical_issues_a = []
    logical_issues_b = []

    for fallacy in audit_a.get("logical_fallacies", []):
        if isinstance(fallacy, dict):
            logical_issues_a.append({
                "type": "fallacy",
                "detail": fallacy.get("type", "unknown"),
                "description": fallacy.get("description", str(fallacy)),
            })
        else:
            logical_issues_a.append({"type": "fallacy", "detail": str(fallacy)})

    for jump in audit_a.get("unsupported_jumps", []):
        if isinstance(jump, dict):
            logical_issues_a.append({
                "type": "unsupported_claim",
                "detail": jump.get("type", "unknown"),
                "description": jump.get("reason", str(jump)),
            })

    for fallacy in audit_b.get("logical_fallacies", []):
        if isinstance(fallacy, dict):
            logical_issues_b.append({
                "type": "fallacy",
                "detail": fallacy.get("type", "unknown"),
                "description": fallacy.get("description", str(fallacy)),
            })
        else:
            logical_issues_b.append({"type": "fallacy", "detail": str(fallacy)})

    for jump in audit_b.get("unsupported_jumps", []):
        if isinstance(jump, dict):
            logical_issues_b.append({
                "type": "unsupported_claim",
                "detail": jump.get("type", "unknown"),
                "description": jump.get("reason", str(jump)),
            })

    # Determine disagreement types
    has_factual_disagreement = len(contradictions) > 0

    # Interpretation disagreement: facts align but conclusions differ
    # Heuristic: similar claims but different bias patterns
    has_interpretation_disagreement = False
    if not has_factual_disagreement and claims_a and claims_b:
        # Check if bias patterns differ significantly
        bias_diff = abs(bias_a.get("political_bias", 0) - bias_b.get("political_bias", 0))
        if bias_diff > 0.3:
            has_interpretation_disagreement = True

    # Missing data check
    has_missing_data = (
        len(claims_a) == 0 or
        len(claims_b) == 0 or
        metadata_a.get("missing_context", False) or
        metadata_b.get("missing_context", False)
    )

    # Determine escalation
    needs_escalation = _check_escalation_domain(text_a, text_b, metadata_a, metadata_b)

    # Generate recommendation
    recommendation = _generate_recommendation(
        has_factual_disagreement,
        has_interpretation_disagreement,
        has_missing_data,
        needs_escalation,
        logical_issues_a,
        logical_issues_b
    )

    result = {
        "agents": [agent_name_a, agent_name_b],
        "issues": {
            "factual_disagreement": has_factual_disagreement,
            "interpretation_disagreement": has_interpretation_disagreement,
            "missing_data": has_missing_data,
            "logical_issues_A": logical_issues_a,
            "logical_issues_B": logical_issues_b,
            "contradictions": contradictions,
        },
        "needs_escalation": needs_escalation,
        "recommendation": recommendation,
        "analysis": {
            "audit_A": {
                "claims_count": len(claims_a),
                "fallacies_count": len(audit_a.get("logical_fallacies", [])),
                "unsupported_count": len(audit_a.get("unsupported_jumps", [])),
                "bias_summary": {
                    "political": round(bias_a.get("political_bias", 0), 3),
                    "emotional": round(bias_a.get("emotional_bias", 0), 3),
                },
            },
            "audit_B": {
                "claims_count": len(claims_b),
                "fallacies_count": len(audit_b.get("logical_fallacies", [])),
                "unsupported_count": len(audit_b.get("unsupported_jumps", [])),
                "bias_summary": {
                    "political": round(bias_b.get("political_bias", 0), 3),
                    "emotional": round(bias_b.get("emotional_bias", 0), 3),
                },
            },
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(f"Dispute analysis complete: escalation={needs_escalation}, recommendation={recommendation}")

    return result


class DisputeEngine:
    """
    OOP interface for dispute analysis.

    Provides methods for parsing disputes and accessing analysis results.
    """

    def __init__(self):
        """Initialize the dispute engine."""
        self._last_analysis: Optional[Dict[str, Any]] = None
        logger.info("DisputeEngine initialized")

    def analyze(
        self,
        agent_a: Dict[str, Any],
        agent_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a dispute between two agents.

        Args:
            agent_a: First agent's position
            agent_b: Second agent's position

        Returns:
            Dispute analysis result
        """
        result = parse_dispute(agent_a, agent_b)
        self._last_analysis = result
        return result

    def get_last_analysis(self) -> Optional[Dict[str, Any]]:
        """Get the most recent analysis result."""
        return self._last_analysis

    def needs_escalation(self) -> bool:
        """Check if the last analysis requires escalation."""
        if self._last_analysis is None:
            return False
        return self._last_analysis.get("needs_escalation", "none") != "none"

    def get_escalation_target(self) -> Optional[str]:
        """Get the escalation target from the last analysis."""
        if self._last_analysis is None:
            return None
        escalation = self._last_analysis.get("needs_escalation", "none")
        return escalation if escalation != "none" else None


# Module-level instance
_engine_instance: Optional[DisputeEngine] = None


def get_dispute_engine() -> DisputeEngine:
    """Get or create the global DisputeEngine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = DisputeEngine()
    return _engine_instance
