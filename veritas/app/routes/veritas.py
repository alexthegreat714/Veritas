"""
Veritas API Routes

This module defines the API endpoints for the Veritas truth auditing service.
All endpoints return JSON responses.

Phase 6: Legislative functions for Congress interaction.
Integrated with VeritasBrain reasoning engine, RAG memory, and Event API.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.logic.auditor import audit_text
from app.logic.bias_detector import detect_bias
from app.logic.chain_validator import validate_chain
from app.logic.source_checker import check_sources
from app.logic.brain import VeritasBrain, get_brain
from app.logic.legislative import (
    vote_on_bill,
    adversarial_contribution,
    contribution_log,
    get_legislative_handler,
)
from app.rag.ingest import ingest_documents, clear_corpus, get_corpus_stats
from app.tools import (
    tool_review_bill,
    tool_review_statement,
    tool_parse_dispute,
    tool_run_monitoring,
    registry as tool_registry,
)
from app.schemas import EventResponse, ErrorResponse


logger = logging.getLogger(__name__)

# Initialize the VeritasBrain instance at module scope
brain = get_brain()

router = APIRouter(prefix="", tags=["veritas"])


# ============================================================================
# Event Models (Phase 5) - For inter-agent communication
# ============================================================================

class VeritasEvent(BaseModel):
    """
    Standardized event model for inter-agent communication.

    Used by Sky, Congress, and other agents to request analysis from Veritas.

    Supported event_type values:
    - "audit-request": General text audit (logic + bias)
    - "bill-logic-check": Audit a proposed bill or policy
    - "argument-integrity-check": Validate chain-of-thought reasoning
    - "source-integrity-check": Validate supporting sources
    - "composite-audit": Combined analysis of multiple data types
    """
    event_type: str = Field(..., description="Event type (e.g., 'audit-request', 'bill-logic-check')")
    source: str = Field(..., description="Sender agent ID (e.g., 'sky', 'apollo', 'congress')")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Task-specific content")
    correlation_id: Optional[str] = Field(default=None, description="Tracing ID across systems")


class VeritasResponse(BaseModel):
    """
    Standardized response model for event-based requests.

    Returns structured analysis results with tracing support.
    """
    ok: bool = Field(..., description="Whether the request succeeded")
    event_type: str = Field(..., description="The event type that was processed")
    correlation_id: Optional[str] = Field(default=None, description="Echo of request correlation_id")
    result: Dict[str, Any] = Field(default_factory=dict, description="Analysis results or error details")


# ============================================================================
# Legacy Request Models
# ============================================================================

class TaskRequest(BaseModel):
    """Request model for running a task."""
    task_type: str = Field(..., description="Type of task to execute")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Task payload data")


class EventRequest(BaseModel):
    """Legacy request model for submitting an event (deprecated, use VeritasEvent)."""
    event_type: str = Field(..., description="Type of event")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data")


class AuditTextRequest(BaseModel):
    """Request model for text auditing."""
    text: str = Field(..., description="Text to audit for truth and logical consistency")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Audit options")


class DetectBiasRequest(BaseModel):
    """Request model for bias detection."""
    text: str = Field(..., description="Text to analyze for bias")


class ValidateChainRequest(BaseModel):
    """Request model for chain-of-thought validation."""
    chain: List[str] = Field(..., description="List of reasoning steps to validate")
    context: Optional[str] = Field(default=None, description="Optional context for validation")


class CheckSourcesRequest(BaseModel):
    """Request model for source checking."""
    sources: List[str] = Field(..., description="List of source URLs or references to check")
    claims: Optional[List[str]] = Field(default=None, description="Claims to verify against sources")


class DocumentModel(BaseModel):
    """Model for a single document to ingest."""
    id: str = Field(..., description="Unique document identifier")
    text: str = Field(..., description="Document text content")
    tags: Optional[List[str]] = Field(default=None, description="Optional tags for categorization")


class IngestDocsRequest(BaseModel):
    """Request model for document ingestion."""
    docs: List[DocumentModel] = Field(..., description="List of documents to ingest")


# ============================================================================
# Legislative Request Models (Phase 6)
# ============================================================================

class VoteOnBillRequest(BaseModel):
    """Request model for bill voting."""
    bill_text: str = Field(..., description="Full text of the bill to vote on")
    bill_id: Optional[str] = Field(default=None, description="Optional bill identifier")


class AdversarialContributionRequest(BaseModel):
    """Request model for adversarial contribution."""
    bill_text: str = Field(..., description="Full text of the bill to analyze")
    bill_id: Optional[str] = Field(default=None, description="Optional bill identifier")


# Endpoints

@router.post("/run_task", response_class=JSONResponse)
async def run_task(request: TaskRequest) -> Dict[str, Any]:
    """
    Execute a specified task through the VeritasBrain reasoning engine.

    The brain automatically classifies tasks and runs appropriate tools.
    For explicit task_type requests, the payload is enriched accordingly.

    Supported task types:
    - audit_text: Analyze text for logical issues and bias
    - validate_chain: Validate reasoning chain
    - check_sources: Check source credibility
    - composite_audit: Run multiple analyses

    Returns structured results with summary and detailed findings.
    """
    logger.info(f"Running task: {request.task_type}")

    try:
        # Build payload for brain processing
        payload = dict(request.payload)

        # If task_type is explicitly specified, ensure payload has right structure
        if request.task_type == "audit_text" and "text" not in payload:
            # Allow backward compatibility with old API
            payload["text"] = payload.get("text", "")
        elif request.task_type == "validate_chain" and "steps" not in payload:
            # Support both "chain" and "steps" keys
            if "chain" in payload:
                payload["steps"] = payload["chain"]
        elif request.task_type == "check_sources" and "sources" not in payload:
            payload["sources"] = payload.get("sources", [])

        # Process through VeritasBrain
        result = brain.process(payload)

        return {
            "ok": True,
            "task_type": result["task_type"],
            "summary": result["summary"],
            "details": result["details"],
        }
    except Exception as e:
        logger.error(f"Task execution error: {e}")
        return {
            "ok": False,
            "task_type": request.task_type,
            "error": str(e),
        }


@router.get("/status", response_class=JSONResponse)
async def get_status() -> Dict[str, Any]:
    """
    Get the current status of the Veritas service.

    Returns operational status of all components including:
    - VeritasBrain reasoning engine
    - Logic auditor
    - Bias detector
    - Chain validator
    - Source checker
    - RAG system
    """
    return {
        "ok": True,
        "status": "operational",
        "version": "0.9.0",
        "phase": 9,
        "components": {
            "brain": "active",
            "auditor": "active",
            "bias_detector": "active",
            "chain_validator": "active",
            "source_checker": "active",
            "rag": "active",
            "event_api": "active",
            "legislative": "active",
            "congress_integration": "active",
            "structured_output": "active",
            "dispute_engine": "active",
            "monitoring_engine": "active",
        },
        "tools": tool_registry.list_tools(),
    }


@router.post("/shutdown", response_class=JSONResponse)
async def shutdown() -> Dict[str, Any]:
    """
    Initiate graceful shutdown of the Veritas service.

    This endpoint will trigger cleanup operations and prepare
    the service for shutdown.
    """
    logger.info("Shutdown requested")
    return {
        "ok": True,
        "shutdown_initiated": False,
        "message": "Shutdown not implemented in Phase 2",
    }


@router.post("/event", response_model=VeritasResponse)
async def handle_event(event: VeritasEvent) -> VeritasResponse:
    """
    Handle standardized events from other agents (Phase 5).

    This is the primary entry point for inter-agent communication.
    Sky, Congress, and other agents use this endpoint to request
    analysis from Veritas.

    Supported event_type values:
    - "audit-request": General text audit (uses payload.text)
    - "bill-logic-check": Audit bill/policy (uses payload.bill_text or text)
    - "argument-integrity-check": Validate reasoning (uses payload.steps)
    - "source-integrity-check": Check sources (uses payload.sources)
    - "composite-audit": Combined analysis

    Agent conventions:
    - Sky: Uses "audit-request" for general text, "composite-audit" for complex cases
    - Congress/Bill Engine: Uses "bill-logic-check" with payload.bill_text
    - Aero/Mercury/Apollo: Uses "argument-integrity-check" for reasoning chains
    """
    logger.info(f"Event received: type={event.event_type}, source={event.source}, "
                f"correlation_id={event.correlation_id}")

    try:
        # Use VeritasBrain's handle_event method for processing
        result = brain.handle_event(event.event_type, event.payload, event.source)

        return VeritasResponse(
            ok=result.get("ok", True),
            event_type=event.event_type,
            correlation_id=event.correlation_id,
            result=result,
        )
    except ValueError as e:
        # Unknown event type or validation error
        logger.warning(f"Event handling error: {e}")
        return VeritasResponse(
            ok=False,
            event_type=event.event_type,
            correlation_id=event.correlation_id,
            result={
                "error": str(e),
                "error_type": "validation_error",
            },
        )
    except Exception as e:
        logger.error(f"Event processing error: {e}")
        return VeritasResponse(
            ok=False,
            event_type=event.event_type,
            correlation_id=event.correlation_id,
            result={
                "error": str(e),
                "error_type": "processing_error",
            },
        )


# ============================================================================
# Congress Event Types (Phase 5)
# ============================================================================

# Supported Congress event types
CONGRESS_EVENT_TYPES = {
    "bill_for_review": tool_review_bill,
    "statement_for_audit": tool_review_statement,
    "dispute_for_analysis": tool_parse_dispute,  # Phase 5 implementation
    "monitoring_cycle": tool_run_monitoring,  # Phase 6 implementation
}


class CongressEventRequest(BaseModel):
    """Request model for Congress events."""
    event_type: str = Field(..., description="Type of event: bill_for_review | statement_for_audit | dispute_for_analysis | monitoring_cycle")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event payload")


@router.post("/event/congress", response_class=JSONResponse)
async def handle_congress_event(request: CongressEventRequest) -> Dict[str, Any]:
    """
    Handle structured events from Congress (Phase 5/6).

    Supported event_type values:
    - "bill_for_review": Review a bill for logical consistency
    - "statement_for_audit": Audit a statement for truth/bias
    - "dispute_for_analysis": Analyze a dispute between agents (Phase 5)
    - "monitoring_cycle": Run drift/bias/anomaly monitoring (Phase 6)

    Expected payload patterns:
    - bill_for_review: {"bill_id": str, "text": str}
    - statement_for_audit: {"statement_id": str, "text": str}
    - dispute_for_analysis: {"agent_A": {...}, "agent_B": {...}}
    - monitoring_cycle: {"limit": int} (optional, default 10)

    Returns CongressReviewResult for bill/statement reviews.
    Returns dispute analysis result for disputes.
    Returns monitoring snapshot for monitoring cycles.

    NOTE: Veritas does NOT escalate or forward events.
    It only classifies disputes and reports findings.
    Actual escalation is handled by Sky/n8n.
    """
    logger.info(f"Congress event received: {request.event_type}")

    # Validate event type
    if request.event_type not in CONGRESS_EVENT_TYPES:
        return JSONResponse(
            status_code=400,
            content={
                "ok": False,
                "error": f"Unknown event_type '{request.event_type}'",
                "supported_types": list(CONGRESS_EVENT_TYPES.keys()),
            }
        )

    # Get the appropriate tool
    tool = CONGRESS_EVENT_TYPES[request.event_type]

    try:
        result = tool(request.payload)
        return {
            "ok": True,
            "event_type": request.event_type,
            "result": result,
        }
    except Exception as e:
        logger.error(f"Congress event error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "event_type": request.event_type,
                "error": str(e),
            }
        )


@router.post("/event/legacy", response_class=JSONResponse)
async def submit_event_legacy(request: EventRequest) -> Dict[str, Any]:
    """
    Legacy event endpoint (deprecated, use /event with VeritasEvent model).

    Maintained for backward compatibility with Phase 4 event format.
    """
    logger.info(f"Legacy event received: {request.event_type}")

    # Event types that trigger brain processing
    processable_events = {"analyze", "audit", "validate", "check"}

    if request.event_type in processable_events:
        try:
            # Process through VeritasBrain
            result = brain.process(request.data)

            return {
                "ok": True,
                "event_type": request.event_type,
                "processed": True,
                "task_type": result["task_type"],
                "summary": result["summary"],
                "details": result["details"],
            }
        except Exception as e:
            logger.error(f"Event processing error: {e}")
            return {
                "ok": False,
                "event_type": request.event_type,
                "processed": False,
                "error": str(e),
            }

    # Non-processable events are logged only
    return {
        "ok": True,
        "event_type": request.event_type,
        "processed": False,
        "message": f"Event type '{request.event_type}' logged but not processed",
    }


@router.post("/audit_text", response_class=JSONResponse)
async def audit_text_endpoint(request: AuditTextRequest) -> Dict[str, Any]:
    """
    Audit text for truth, logical consistency, and factual accuracy.

    Analyzes the provided text for:
    - Logical fallacies (ad hominem, strawman, false dichotomy, etc.)
    - Factual claims extraction
    - Internal inconsistencies and contradictions
    - Unsupported logical jumps

    Returns deterministic, heuristic-based analysis results.
    """
    logger.info(f"Auditing text of length {len(request.text)}")

    try:
        result = audit_text(request.text)

        return {
            "ok": True,
            "text_length": len(request.text),
            "claims": result["claims"],
            "logical_fallacies": result["logical_fallacies"],
            "inconsistencies": result["inconsistencies"],
            "unsupported_jumps": result["unsupported_jumps"],
        }
    except Exception as e:
        logger.error(f"Audit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect_bias", response_class=JSONResponse)
async def detect_bias_endpoint(request: DetectBiasRequest) -> Dict[str, Any]:
    """
    Detect various forms of bias in text.

    Analyzes the provided text for:
    - Political bias (partisan language intensity)
    - Emotional bias (loaded language)
    - Motivational bias (persuasive patterns)
    - Certainty overconfidence (unjustified certainty markers)

    Returns normalized scores between 0.0-1.0 for each bias type.
    """
    logger.info(f"Detecting bias in text of length {len(request.text)}")

    try:
        result = detect_bias(request.text)

        return {
            "ok": True,
            "text_length": len(request.text),
            "political_bias": result["political_bias"],
            "emotional_bias": result["emotional_bias"],
            "motivational_bias": result["motivational_bias"],
            "certainty_overconfidence": result["certainty_overconfidence"],
        }
    except Exception as e:
        logger.error(f"Bias detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate_chain", response_class=JSONResponse)
async def validate_chain_endpoint(request: ValidateChainRequest) -> Dict[str, Any]:
    """
    Validate a chain of reasoning steps.

    Examines the logical flow of reasoning to identify:
    - Gaps in reasoning (missing intermediate steps)
    - Contradictions between steps
    - Circular logic patterns
    - Flawed or weak premises

    Returns validation results with specific issues identified.
    """
    logger.info(f"Validating chain with {len(request.chain)} steps")

    try:
        result = validate_chain(request.chain)

        return {
            "ok": True,
            "chain_length": len(request.chain),
            "gaps": result["gaps"],
            "contradictions": result["contradictions"],
            "circular_logic": result["circular_logic"],
            "flawed_premises": result["flawed_premises"],
        }
    except Exception as e:
        logger.error(f"Chain validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check_sources", response_class=JSONResponse)
async def check_sources_endpoint(request: CheckSourcesRequest) -> Dict[str, Any]:
    """
    Check and verify sources for credibility and accuracy.

    Analyzes provided sources to determine:
    - Missing or empty sources
    - Invalid/unverifiable sources
    - Source credibility scores (0-1)
    - Potential conflicts between sources

    Uses URL validation and pattern matching (no external requests).
    """
    logger.info(f"Checking {len(request.sources)} sources")

    try:
        result = check_sources(request.sources)

        return {
            "ok": True,
            "sources_count": len(request.sources),
            "missing_sources": result["missing_sources"],
            "unverifiable": result["unverifiable"],
            "conflicting": result["conflicting"],
            "ranked_confidence": result["ranked_confidence"],
        }
    except Exception as e:
        logger.error(f"Source check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# RAG Memory Endpoints

@router.post("/ingest_docs", response_class=JSONResponse)
async def ingest_docs_endpoint(request: IngestDocsRequest) -> Dict[str, Any]:
    """
    Ingest documents into Veritas' fact corpus.

    Accepts a list of documents, each with:
    - id: Unique identifier (required)
    - text: Document content (required)
    - tags: Optional list of tags

    Documents are stored in memory/long/veritas_corpus.jsonl.
    """
    logger.info(f"Ingesting {len(request.docs)} documents")

    try:
        # Convert Pydantic models to dicts
        docs = [
            {
                "id": doc.id,
                "text": doc.text,
                "tags": doc.tags or [],
            }
            for doc in request.docs
        ]

        result = ingest_documents(docs)

        return {
            "ok": True,
            "ingested_count": result["ingested_count"],
            "errors": result["errors"],
        }
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear_corpus", response_class=JSONResponse)
async def clear_corpus_endpoint() -> Dict[str, Any]:
    """
    Clear the fact corpus.

    Removes all documents from memory/long/veritas_corpus.jsonl.
    Use with caution - this is irreversible.
    """
    logger.info("Clearing corpus")

    try:
        result = clear_corpus()
        return {
            "ok": result["cleared"],
            "message": result["message"],
        }
    except Exception as e:
        logger.error(f"Clear corpus error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/corpus_stats", response_class=JSONResponse)
async def corpus_stats_endpoint() -> Dict[str, Any]:
    """
    Get statistics about the fact corpus.

    Returns:
    - document_count: Number of documents in corpus
    - file_size_bytes: Size of corpus file
    - exists: Whether corpus file exists
    """
    try:
        stats = get_corpus_stats()
        return {
            "ok": True,
            **stats,
        }
    except Exception as e:
        logger.error(f"Corpus stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Legislative Endpoints (Phase 6)
# ============================================================================

@router.post("/vote_on_bill", response_class=JSONResponse)
async def vote_on_bill_endpoint(request: VoteOnBillRequest) -> Dict[str, Any]:
    """
    Vote on a bill based on logic integrity analysis (Phase 6).

    Veritas votes based STRICTLY on:
    - Logical consistency
    - Presence of contradictions
    - Fallacy detection
    - Bias levels
    - Clarity and structure

    Veritas does NOT evaluate:
    - Policy merit
    - Cost or budget implications
    - Moral considerations
    - Political alignment

    Returns vote ("yes", "no", or "abstain") with confidence and reasons.
    Automatically logs the contribution.
    """
    logger.info(f"Vote request for bill: {request.bill_id or 'unknown'}")

    try:
        handler = get_legislative_handler()
        result = handler.vote(
            bill_text=request.bill_text,
            bill_id=request.bill_id,
            log_contribution=True
        )

        return {
            "ok": True,
            "bill_id": request.bill_id,
            "vote": result["vote"],
            "confidence": result["confidence"],
            "reasons": result["reasons"],
            "analysis_summary": result["analysis_summary"],
        }
    except Exception as e:
        logger.error(f"Vote error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adversarial_contribution", response_class=JSONResponse)
async def adversarial_contribution_endpoint(
    request: AdversarialContributionRequest
) -> Dict[str, Any]:
    """
    Generate adversarial (devil's advocate) contribution for a bill (Phase 6).

    Purpose: Surface potential issues that may be missed during groupthink.
    This is NOT a vote - it's a structured critique to ensure thorough review.

    Identifies:
    - Edge-case flaws
    - Hidden assumptions
    - Potential fallacies
    - Alternate interpretations
    - Structural weaknesses

    Returns counterpoints, risk flags, and whether review is required.
    Automatically logs the contribution.
    """
    logger.info(f"Adversarial contribution request for bill: {request.bill_id or 'unknown'}")

    try:
        handler = get_legislative_handler()
        result = handler.adversarial(
            bill_text=request.bill_text,
            bill_id=request.bill_id,
            log_contribution=True
        )

        return {
            "ok": True,
            "bill_id": request.bill_id,
            "counterpoints": result["counterpoints"],
            "risk_flags": result["risk_flags"],
            "requires_review": result["requires_review"],
            "hidden_assumptions": result["hidden_assumptions"],
        }
    except Exception as e:
        logger.error(f"Adversarial contribution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
