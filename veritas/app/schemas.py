"""
Veritas Output Schemas

Standardized Pydantic models for structured audit output.
Phase 4: All Veritas public tool responses conform to these models.

These schemas ensure consistent, validated output for:
- Internal audits
- Congress-facing reviews
- Inter-agent communication
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LogicalIssue(BaseModel):
    """A detected logical issue in the analyzed text."""

    type: str = Field(
        ...,
        description="Type of logical issue: 'contradiction' | 'non_sequitur' | "
                    "'unsupported_conclusion' | 'circular_reasoning'"
    )
    description: str = Field(
        ...,
        description="Human-readable description of the logical issue"
    )


class BiasFlag(BaseModel):
    """A detected bias indicator in the analyzed text."""

    type: str = Field(
        ...,
        description="Type of bias: 'emotional_language' | 'cherry_picking' | "
                    "'loaded_framing' | 'appeal_to_authority' | 'overconfidence'"
    )
    snippet: str = Field(
        ...,
        description="The text snippet that triggered this flag"
    )
    explanation: str = Field(
        ...,
        description="Explanation of why this was flagged as bias"
    )


class SourceValidationItem(BaseModel):
    """Validation result for a single claim against sources."""

    claim: str = Field(
        ...,
        description="The claim being validated"
    )
    supporting: List[str] = Field(
        default_factory=list,
        description="List of sources that support this claim"
    )
    contradicting: List[str] = Field(
        default_factory=list,
        description="List of sources that contradict this claim"
    )
    missing_context: bool = Field(
        default=False,
        description="Whether the claim is missing important context"
    )


class AuditResult(BaseModel):
    """
    Core audit result for text analysis.

    Contains logical issues, bias flags, and confidence assessment.
    """

    original_text: str = Field(
        ...,
        description="The original text that was audited"
    )
    normalized: Dict[str, Any] = Field(
        default_factory=dict,
        description="Normalized/parsed representation of the text"
    )
    logical_issues: List[LogicalIssue] = Field(
        default_factory=list,
        description="List of detected logical issues"
    )
    bias_flags: List[BiasFlag] = Field(
        default_factory=list,
        description="List of detected bias indicators"
    )
    confidence: str = Field(
        default="medium",
        description="Confidence level: 'low' | 'medium' | 'high'"
    )


class AuditWithSourcesResult(BaseModel):
    """
    Extended audit result including source validation.

    Combines core audit with RAG-retrieved documents and source checks.
    """

    audit: AuditResult = Field(
        ...,
        description="Core audit result"
    )
    retrieved_docs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Documents retrieved from RAG system"
    )
    source_validation: List[SourceValidationItem] = Field(
        default_factory=list,
        description="Validation results for claims against sources"
    )


class CongressReviewResult(BaseModel):
    """
    Result of a Congress-facing review (bill or statement).

    NOTE: Veritas is an auditor. This recommendation is advisory only.
    It does not constitute a vote, law change, or override of any other agent.
    """

    item_type: str = Field(
        ...,
        description="Type of item reviewed: 'bill' | 'statement'"
    )
    id: str = Field(
        ...,
        description="Identifier for the reviewed item"
    )
    audit: AuditWithSourcesResult = Field(
        ...,
        description="Full audit results with source validation"
    )
    recommendation: str = Field(
        ...,
        description="Advisory recommendation: 'approve' | 'reject' | 'revise'"
    )
    notes: str = Field(
        ...,
        description="Explanation of the recommendation"
    )


# ============================================================================
# Response wrapper models for API endpoints
# ============================================================================


class EventResponse(BaseModel):
    """Standard response for /event endpoint."""

    ok: bool = Field(
        ...,
        description="Whether the event was processed successfully"
    )
    event_type: str = Field(
        ...,
        description="The event type that was processed"
    )
    result: Dict[str, Any] = Field(
        ...,
        description="The processing result"
    )


class ErrorResponse(BaseModel):
    """Standard error response."""

    ok: bool = Field(
        default=False,
        description="Always False for errors"
    )
    error: str = Field(
        ...,
        description="Error message"
    )
    supported_types: Optional[List[str]] = Field(
        default=None,
        description="List of supported event types (for unknown type errors)"
    )
