"""
Veritas Tools Package

This package contains tool definitions and integrations for the Veritas system.
Tools provide specialized capabilities that can be invoked by the truth auditing
system to perform specific tasks.

Phase 5: Dispute resolution tools added.
"""

import logging
from typing import Any, Dict, List, Optional

from app.logic.auditor import audit_text
from app.logic.bias_detector import detect_bias
from app.logic.source_checker import check_sources
from app.rag.query import query_relevant_documents
from app.schemas import (
    LogicalIssue,
    BiasFlag,
    SourceValidationItem,
    AuditResult,
    AuditWithSourcesResult,
    CongressReviewResult,
)
from app.dispute_engine import parse_dispute, get_dispute_engine
from app.memory_utils import store_dispute_analysis


logger = logging.getLogger(__name__)


# ============================================================================
# Structured Output Functions
# ============================================================================
# These functions convert raw tool outputs to schema-compliant models.


def _map_logical_issues(audit_result: Dict[str, Any]) -> List[LogicalIssue]:
    """Map raw audit results to LogicalIssue models."""
    issues = []

    # Map logical fallacies
    for fallacy in audit_result.get("logical_fallacies", []):
        if isinstance(fallacy, dict):
            issues.append(LogicalIssue(
                type=fallacy.get("type", "unknown"),
                description=fallacy.get("description", str(fallacy))
            ))
        else:
            issues.append(LogicalIssue(
                type="fallacy",
                description=str(fallacy)
            ))

    # Map inconsistencies as contradictions
    for inconsistency in audit_result.get("inconsistencies", []):
        if isinstance(inconsistency, dict):
            issues.append(LogicalIssue(
                type="contradiction",
                description=inconsistency.get("description", str(inconsistency))
            ))
        else:
            issues.append(LogicalIssue(
                type="contradiction",
                description=str(inconsistency)
            ))

    # Map unsupported jumps as non-sequitur
    for jump in audit_result.get("unsupported_jumps", []):
        if isinstance(jump, dict):
            issues.append(LogicalIssue(
                type="non_sequitur",
                description=jump.get("description", str(jump))
            ))
        else:
            issues.append(LogicalIssue(
                type="unsupported_conclusion",
                description=str(jump)
            ))

    return issues


def _map_bias_flags(bias_result: Dict[str, Any]) -> List[BiasFlag]:
    """Map raw bias detection results to BiasFlag models."""
    flags = []

    # Check political bias
    political = bias_result.get("political_bias", 0)
    if political > 0.3:
        flags.append(BiasFlag(
            type="loaded_framing",
            snippet=f"Political bias score: {political:.2f}",
            explanation="Text contains partisan or politically charged language"
        ))

    # Check emotional bias
    emotional = bias_result.get("emotional_bias", 0)
    if emotional > 0.3:
        flags.append(BiasFlag(
            type="emotional_language",
            snippet=f"Emotional bias score: {emotional:.2f}",
            explanation="Text contains emotionally charged or loaded language"
        ))

    # Check certainty overconfidence
    certainty = bias_result.get("certainty_overconfidence", 0)
    if certainty > 0.3:
        flags.append(BiasFlag(
            type="overconfidence",
            snippet=f"Certainty overconfidence score: {certainty:.2f}",
            explanation="Text makes claims with unwarranted certainty"
        ))

    # Check motivational bias
    motivational = bias_result.get("motivational_bias", 0)
    if motivational > 0.3:
        flags.append(BiasFlag(
            type="appeal_to_authority",
            snippet=f"Motivational bias score: {motivational:.2f}",
            explanation="Text uses persuasive or manipulative patterns"
        ))

    return flags


def _calculate_confidence(
    audit_result: Dict[str, Any],
    bias_result: Optional[Dict[str, Any]] = None
) -> str:
    """Calculate confidence level from results."""
    score = 1.0

    # Deduct for logical issues
    fallacies = len(audit_result.get("logical_fallacies", []))
    inconsistencies = len(audit_result.get("inconsistencies", []))
    jumps = len(audit_result.get("unsupported_jumps", []))

    score -= fallacies * 0.15
    score -= inconsistencies * 0.2
    score -= jumps * 0.1

    # Deduct for bias
    if bias_result:
        for key in ["political_bias", "emotional_bias", "certainty_overconfidence"]:
            score -= bias_result.get(key, 0) * 0.1

    if score >= 0.7:
        return "high"
    elif score >= 0.4:
        return "medium"
    else:
        return "low"


def audit_text_structured(text: str) -> AuditResult:
    """
    Perform text audit and return structured AuditResult.

    Args:
        text: The text to audit.

    Returns:
        AuditResult model with standardized structure.
    """
    logger.info(f"Structured audit for text of length {len(text)}")

    # Run raw audit
    audit_raw = audit_text(text)
    bias_raw = detect_bias(text)

    # Map to structured format
    logical_issues = _map_logical_issues(audit_raw)
    bias_flags = _map_bias_flags(bias_raw)
    confidence = _calculate_confidence(audit_raw, bias_raw)

    return AuditResult(
        original_text=text,
        normalized={
            "claims": audit_raw.get("claims", []),
            "word_count": len(text.split()),
            "sentence_count": text.count(".") + text.count("!") + text.count("?"),
        },
        logical_issues=logical_issues,
        bias_flags=bias_flags,
        confidence=confidence,
    )


def audit_with_sources_structured(text: str, sources: Optional[List[str]] = None) -> AuditWithSourcesResult:
    """
    Perform audit with source validation and return structured result.

    Args:
        text: The text to audit.
        sources: Optional list of source URLs or references.

    Returns:
        AuditWithSourcesResult model with full audit and source validation.
    """
    logger.info(f"Structured audit with sources for text of length {len(text)}")

    # Get core audit
    audit = audit_text_structured(text)

    # Retrieve relevant documents from RAG
    rag_result = query_relevant_documents(text[:500], top_k=5)
    retrieved_docs = rag_result.get("hits", [])

    # Validate sources if provided
    source_validation = []
    if sources:
        source_check = check_sources(sources)

        # Extract claims from audit
        claims = audit.normalized.get("claims", [])

        # Create validation items for each claim
        for i, claim in enumerate(claims[:5]):  # Limit to first 5 claims
            claim_text = claim.get("claim", str(claim)) if isinstance(claim, dict) else str(claim)

            # Categorize sources based on credibility
            supporting = []
            contradicting = []

            for ranked in source_check.get("ranked_confidence", []):
                if ranked.get("confidence", 0) >= 0.5:
                    supporting.append(ranked.get("source", ""))
                else:
                    contradicting.append(ranked.get("source", ""))

            source_validation.append(SourceValidationItem(
                claim=claim_text,
                supporting=supporting,
                contradicting=contradicting,
                missing_context=len(supporting) == 0 and len(contradicting) == 0,
            ))

    return AuditWithSourcesResult(
        audit=audit,
        retrieved_docs=retrieved_docs,
        source_validation=source_validation,
    )


# ============================================================================
# Congress-facing Review Tools
# ============================================================================
# NOTE: Veritas is an auditor. These recommendations are advisory only.
# They do not constitute a vote, law change, or override of any other agent.


def _compute_recommendation(audit: AuditWithSourcesResult) -> tuple:
    """
    Compute recommendation and notes from audit results.

    Returns:
        Tuple of (recommendation, notes)
    """
    severe_issues = 0
    moderate_issues = 0
    notes_parts = []

    # Check logical issues
    for issue in audit.audit.logical_issues:
        if issue.type in ["contradiction", "circular_reasoning"]:
            severe_issues += 1
        else:
            moderate_issues += 1

    if audit.audit.logical_issues:
        notes_parts.append(f"{len(audit.audit.logical_issues)} logical issue(s) detected")

    # Check bias flags
    high_bias_count = sum(
        1 for flag in audit.audit.bias_flags
        if flag.type in ["emotional_language", "loaded_framing"]
    )
    if high_bias_count > 0:
        moderate_issues += high_bias_count
        notes_parts.append(f"{high_bias_count} significant bias flag(s)")

    # Check confidence
    if audit.audit.confidence == "low":
        notes_parts.append("Low overall confidence in analysis")
        moderate_issues += 1
    elif audit.audit.confidence == "high":
        notes_parts.append("High confidence in analysis")

    # Check source validation
    missing_context_count = sum(
        1 for sv in audit.source_validation
        if sv.missing_context
    )
    if missing_context_count > 0:
        notes_parts.append(f"{missing_context_count} claim(s) lack source support")
        moderate_issues += 1

    # Compute recommendation
    # NOTE: This is advisory only - Veritas does not have legislative authority
    if severe_issues >= 2 or (severe_issues >= 1 and moderate_issues >= 2):
        recommendation = "reject"
        notes_parts.insert(0, "ADVISORY: Significant logical issues require attention.")
    elif severe_issues >= 1 or moderate_issues >= 2:
        recommendation = "revise"
        notes_parts.insert(0, "ADVISORY: Issues detected that should be addressed.")
    elif audit.audit.confidence == "high" and moderate_issues == 0:
        recommendation = "approve"
        notes_parts.insert(0, "ADVISORY: Analysis found no significant issues.")
    else:
        recommendation = "revise"
        notes_parts.insert(0, "ADVISORY: Minor issues suggest review before approval.")

    notes = " ".join(notes_parts)

    return recommendation, notes


def tool_review_bill(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Review a bill for logical consistency and truth.

    NOTE: Veritas is an auditor. This recommendation is advisory only.
    It does not constitute a vote, law change, or override of any other agent.

    Expects payload:
    {
        "bill_id": str,
        "text": str,
        "sources": Optional[List[str]]  # Optional supporting sources
    }

    Returns:
        CongressReviewResult as dict.
    """
    logger.info(f"Reviewing bill: {payload.get('bill_id', 'unknown')}")

    bill_id = payload.get("bill_id", "unknown")
    text = payload.get("text", "")
    sources = payload.get("sources", [])

    if not text:
        return {
            "error": "No bill text provided",
            "item_type": "bill",
            "id": bill_id,
        }

    # Run structured audit with sources
    audit = audit_with_sources_structured(text, sources)

    # Compute recommendation
    recommendation, notes = _compute_recommendation(audit)

    # Build result
    result = CongressReviewResult(
        item_type="bill",
        id=bill_id,
        audit=audit,
        recommendation=recommendation,
        notes=notes,
    )

    return result.model_dump()


def tool_review_statement(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Review a statement for logical consistency and truth.

    NOTE: Veritas is an auditor. This recommendation is advisory only.
    It does not constitute a vote, law change, or override of any other agent.

    Expects payload:
    {
        "statement_id": str,
        "text": str,
        "sources": Optional[List[str]]  # Optional supporting sources
    }

    Returns:
        CongressReviewResult as dict.
    """
    logger.info(f"Reviewing statement: {payload.get('statement_id', 'unknown')}")

    statement_id = payload.get("statement_id", "unknown")
    text = payload.get("text", "")
    sources = payload.get("sources", [])

    if not text:
        return {
            "error": "No statement text provided",
            "item_type": "statement",
            "id": statement_id,
        }

    # Run structured audit with sources
    audit = audit_with_sources_structured(text, sources)

    # Compute recommendation
    recommendation, notes = _compute_recommendation(audit)

    # Build result
    result = CongressReviewResult(
        item_type="statement",
        id=statement_id,
        audit=audit,
        recommendation=recommendation,
        notes=notes,
    )

    return result.model_dump()


# ============================================================================
# Dispute Resolution Tools (Phase 5)
# ============================================================================
# NOTE: Veritas DOES NOT escalate or forward events.
# It only classifies disputes and reports findings.
# Actual escalation is handled by Sky/n8n.


def tool_parse_dispute(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and analyze a dispute between two agents.

    NOTE: Veritas does NOT:
    - Rule on ethics or law (Sophia's domain)
    - Rule on security or danger (Aegis's domain)
    - Override Congress, Sky, or any agent
    - Actually escalate or forward events

    Veritas only classifies what kind of disagreement it is,
    provides fact-logic analysis, and identifies whether
    external escalation is required.

    Expects payload:
    {
        "agent_A": {
            "agent": str,      # Agent name (e.g., "Sky", "Aegis")
            "text": str,       # The agent's position/statement
            "metadata": dict   # Optional additional context
        },
        "agent_B": {
            "agent": str,
            "text": str,
            "metadata": dict
        }
    }

    Returns:
        Dispute analysis result including:
        - agents: [str, str] - Names of disputing agents
        - issues: dict - Factual/interpretation disagreements, logical issues
        - needs_escalation: "none" | "sophia" | "aegis" | "congress"
        - recommendation: str - Suggested action
        - analysis: dict - Detailed audit results
        - storage: dict - Storage confirmation
    """
    logger.info("tool_parse_dispute invoked")

    agent_a = payload.get("agent_A", {})
    agent_b = payload.get("agent_B", {})

    if not agent_a or not agent_b:
        return {
            "error": "Both agent_A and agent_B are required",
            "agents": [],
            "issues": {},
            "needs_escalation": "none",
            "recommendation": "request_more_data",
        }

    if not agent_a.get("text") or not agent_b.get("text"):
        return {
            "error": "Both agents must have non-empty text",
            "agents": [agent_a.get("agent", "A"), agent_b.get("agent", "B")],
            "issues": {"missing_data": True},
            "needs_escalation": "none",
            "recommendation": "request_more_data",
        }

    # Parse the dispute
    result = parse_dispute(agent_a, agent_b)

    # Store the analysis
    storage_result = store_dispute_analysis(result)
    result["storage"] = storage_result

    return result


# ============================================================================
# Tool Registry
# ============================================================================


class ToolRegistry:
    """
    Registry for managing available tools in the Veritas system.

    This class manages tool registration, discovery, and invocation.
    """

    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, Any] = {}
        self._initialized = False
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register default tools."""
        self._tools = {
            "review_bill": tool_review_bill,
            "review_statement": tool_review_statement,
            "audit_text": lambda p: audit_text_structured(p.get("text", "")).model_dump(),
            "audit_with_sources": lambda p: audit_with_sources_structured(
                p.get("text", ""),
                p.get("sources", [])
            ).model_dump(),
            "parse_dispute": tool_parse_dispute,
        }
        self._initialized = True

    def register(self, name: str, tool: Any) -> None:
        """
        Register a tool with the registry.

        Args:
            name: Unique name for the tool.
            tool: The tool callable to register.
        """
        self._tools[name] = tool
        logger.info(f"Tool registered: {name}")

    def get(self, name: str) -> Any:
        """
        Get a tool by name.

        Args:
            name: The name of the tool to retrieve.

        Returns:
            The tool callable, or None if not found.
        """
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """
        List all registered tool names.

        Returns:
            List of registered tool names.
        """
        return list(self._tools.keys())

    def invoke(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke a tool by name with provided payload.

        Args:
            name: The name of the tool to invoke.
            payload: Arguments to pass to the tool.

        Returns:
            Dictionary containing tool execution results.
        """
        tool = self._tools.get(name)
        if tool is None:
            return {
                "error": f"Tool '{name}' not found",
                "available_tools": self.list_tools(),
            }

        try:
            return tool(payload)
        except Exception as e:
            logger.error(f"Tool invocation error for {name}: {e}")
            return {
                "error": str(e),
                "tool": name,
            }


# Global tool registry instance
registry = ToolRegistry()

# Export tools dict for backward compatibility
TOOLS = registry._tools
