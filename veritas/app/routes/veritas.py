"""
Veritas API Routes

This module defines the API endpoints for the Veritas truth auditing service.
All endpoints return JSON responses.

Phase 2: Integrated with logic modules for actual analysis.
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


logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["veritas"])


# Request Models

class TaskRequest(BaseModel):
    """Request model for running a task."""
    task_type: str = Field(..., description="Type of task to execute")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Task payload data")


class EventRequest(BaseModel):
    """Request model for submitting an event."""
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


# Endpoints

@router.post("/run_task", response_class=JSONResponse)
async def run_task(request: TaskRequest) -> Dict[str, Any]:
    """
    Execute a specified task.

    Supported task types:
    - audit_text: Analyze text for logical issues
    - detect_bias: Detect bias in text
    - validate_chain: Validate reasoning chain
    - check_sources: Check source credibility
    """
    logger.info(f"Running task: {request.task_type}")

    try:
        if request.task_type == "audit_text":
            text = request.payload.get("text", "")
            result = audit_text(text)
        elif request.task_type == "detect_bias":
            text = request.payload.get("text", "")
            result = detect_bias(text)
        elif request.task_type == "validate_chain":
            chain = request.payload.get("chain", [])
            result = validate_chain(chain)
        elif request.task_type == "check_sources":
            sources = request.payload.get("sources", [])
            result = check_sources(sources)
        else:
            result = {"error": f"Unknown task type: {request.task_type}"}

        return {
            "ok": True,
            "task_type": request.task_type,
            "result": result,
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
    - Logic auditor
    - Bias detector
    - Chain validator
    - Source checker
    - RAG system
    """
    return {
        "ok": True,
        "status": "operational",
        "version": "0.2.0",
        "phase": 2,
        "components": {
            "auditor": "active",
            "bias_detector": "active",
            "chain_validator": "active",
            "source_checker": "active",
            "rag": "stub",
        },
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


@router.post("/event", response_class=JSONResponse)
async def submit_event(request: EventRequest) -> Dict[str, Any]:
    """
    Submit an event to the Veritas event processing system.

    Events can include external triggers, notifications,
    or data updates that Veritas should process.
    """
    logger.info(f"Event received: {request.event_type}")
    return {
        "ok": True,
        "event_type": request.event_type,
        "processed": False,
        "message": "Event processing not implemented in Phase 2",
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
