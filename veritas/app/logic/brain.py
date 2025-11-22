"""
Veritas Brain - Central Reasoning Engine

This module contains the VeritasBrain class that coordinates:
- Task classification
- Memory retrieval (RAG)
- Analytical tool orchestration
- Structured output synthesis
- Contribution logging

Phase 3: Core reasoning pipeline implementation.
All processing is deterministic with no ML models.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from logging.handlers import RotatingFileHandler

from app.logic.auditor import audit_text
from app.logic.bias_detector import detect_bias
from app.logic.chain_validator import validate_chain
from app.logic.source_checker import check_sources
from app.rag.query import RAGQuery


# Configure module logger
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = RotatingFileHandler(
        LOG_DIR / "veritas_brain.log",
        maxBytes=5_000_000,
        backupCount=3
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)


# Thresholds for issue detection
BIAS_HIGH_THRESHOLD = 0.6
FALLACY_COUNT_THRESHOLD = 2
CREDIBILITY_LOW_THRESHOLD = 0.4


class VeritasBrain:
    """
    Central reasoning engine for Veritas.

    Coordinates task classification, memory retrieval,
    analytical tools, and structured outputs.

    This class implements the core pipeline:
    1. classify_task - Determine what type of analysis is needed
    2. retrieve_relevant_memory - Query RAG for context
    3. run_audit_tools - Execute appropriate analysis tools
    4. synthesize_findings - Combine results into structured output
    5. log_contribution - Record the analysis for auditing

    All processing is deterministic and rule-based.
    """

    def __init__(
        self,
        memory_client: Optional[RAGQuery] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the VeritasBrain.

        Args:
            memory_client: Optional RAGQuery instance for memory retrieval.
            logger: Optional logger instance. If not provided, creates default.
        """
        self.memory_client = memory_client or RAGQuery()
        self.logger = logger or self._build_default_logger()
        self._contribution_logger = self._build_contribution_logger()
        self._initialized = True

        self.logger.info("VeritasBrain initialized")

    def _build_default_logger(self) -> logging.Logger:
        """Create a default logger for the brain module."""
        brain_logger = logging.getLogger("veritas.brain")
        brain_logger.setLevel(logging.DEBUG)

        if not brain_logger.handlers:
            handler = RotatingFileHandler(
                LOG_DIR / "veritas_brain.log",
                maxBytes=5_000_000,
                backupCount=3
            )
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            brain_logger.addHandler(handler)

        return brain_logger

    def _build_contribution_logger(self) -> logging.Logger:
        """Create a dedicated logger for contribution tracking."""
        contrib_logger = logging.getLogger("veritas.contributions")
        contrib_logger.setLevel(logging.INFO)

        if not contrib_logger.handlers:
            handler = RotatingFileHandler(
                LOG_DIR / "veritas_contributions.log",
                maxBytes=10_000_000,
                backupCount=5
            )
            # JSON format for contribution logs
            handler.setFormatter(logging.Formatter('%(message)s'))
            contrib_logger.addHandler(handler)

        return contrib_logger

    def classify_task(self, payload: Dict[str, Any]) -> str:
        """
        Classify the task type based on the payload structure.

        Uses simple heuristic rules based on keys present:
        - If text and no steps/sources -> "audit_text"
        - If steps list present -> "validate_chain"
        - If sources list present -> "check_sources"
        - If combination -> "composite_audit"

        Args:
            payload: Arbitrary JSON payload from /run_task or /event.

        Returns:
            String task type: "audit_text", "validate_chain",
            "check_sources", or "composite_audit".
        """
        self.logger.debug(f"Classifying task with keys: {list(payload.keys())}")

        has_text = "text" in payload and bool(payload["text"])
        has_steps = "steps" in payload and isinstance(payload.get("steps"), list) and len(payload["steps"]) > 0
        has_chain = "chain" in payload and isinstance(payload.get("chain"), list) and len(payload["chain"]) > 0
        has_sources = "sources" in payload and isinstance(payload.get("sources"), list) and len(payload["sources"]) > 0

        # Count how many major data types are present
        data_types_present = sum([
            1 if has_text else 0,
            1 if (has_steps or has_chain) else 0,
            1 if has_sources else 0
        ])

        # Composite if multiple types present
        if data_types_present > 1:
            task_type = "composite_audit"
        elif has_steps or has_chain:
            task_type = "validate_chain"
        elif has_sources:
            task_type = "check_sources"
        elif has_text:
            task_type = "audit_text"
        else:
            # Default to audit_text for unknown payloads
            task_type = "audit_text"

        self.logger.info(f"Task classified as: {task_type}")
        return task_type

    def retrieve_relevant_memory(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve relevant memory/context from the RAG system.

        Uses key fields such as topic, context, or text to query
        the memory system for relevant information.

        Args:
            payload: The task payload containing query context.

        Returns:
            Dictionary containing:
            - memory_hits: List of relevant snippets or IDs
            - memory_summary: Short summary or empty string
        """
        self.logger.debug("Retrieving relevant memory")

        # Extract query text from payload
        query_text = ""
        if "text" in payload:
            query_text = payload["text"][:500]  # Limit query length
        elif "topic" in payload:
            query_text = payload["topic"]
        elif "context" in payload:
            query_text = payload["context"]
        elif "steps" in payload and payload["steps"]:
            # Use first step as query
            query_text = payload["steps"][0][:200]
        elif "chain" in payload and payload["chain"]:
            query_text = payload["chain"][0][:200]

        if not query_text:
            self.logger.info("No query text found for memory retrieval")
            return {
                "memory_hits": [],
                "memory_summary": "",
            }

        try:
            # Query the RAG system
            rag_result = self.memory_client.query(query_text)

            # Check if RAG is stubbed
            if rag_result.get("status") == "stub":
                self.logger.info("RAG system is stubbed, returning empty memory")
                return {
                    "memory_hits": [],
                    "memory_summary": "RAG system not yet implemented",
                }

            # Extract and format results
            memory_hits = rag_result.get("results", [])
            total_matches = rag_result.get("total_matches", 0)

            # Generate summary
            if memory_hits:
                memory_summary = f"Found {total_matches} relevant memory entries"
            else:
                memory_summary = ""

            self.logger.info(f"Memory retrieval complete: {len(memory_hits)} hits")

            return {
                "memory_hits": memory_hits,
                "memory_summary": memory_summary,
            }

        except Exception as e:
            self.logger.error(f"Memory retrieval error: {e}")
            return {
                "memory_hits": [],
                "memory_summary": f"Memory retrieval failed: {str(e)}",
            }

    def run_audit_tools(
        self,
        task_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the appropriate analysis tools based on task type.

        Dispatches to the Phase 2 analysis functions:
        - audit_text(text)
        - detect_bias(text)
        - validate_chain(steps)
        - check_sources(sources)

        Args:
            task_type: The classified task type.
            payload: The task payload containing data to analyze.

        Returns:
            Dictionary containing results from each tool:
            - audit: Audit results or None
            - bias: Bias detection results or None
            - chain: Chain validation results or None
            - sources: Source check results or None
        """
        self.logger.info(f"Running audit tools for task type: {task_type}")

        results = {
            "audit": None,
            "bias": None,
            "chain": None,
            "sources": None,
        }

        try:
            if task_type == "audit_text":
                text = payload.get("text", "")
                results["audit"] = audit_text(text)
                results["bias"] = detect_bias(text)

            elif task_type == "validate_chain":
                # Support both "steps" and "chain" keys
                steps = payload.get("steps") or payload.get("chain", [])
                results["chain"] = validate_chain(steps)

            elif task_type == "check_sources":
                sources = payload.get("sources", [])
                results["sources"] = check_sources(sources)

            elif task_type == "composite_audit":
                # Run all relevant tools based on keys present
                if "text" in payload:
                    text = payload["text"]
                    results["audit"] = audit_text(text)
                    results["bias"] = detect_bias(text)

                if "steps" in payload or "chain" in payload:
                    steps = payload.get("steps") or payload.get("chain", [])
                    results["chain"] = validate_chain(steps)

                if "sources" in payload:
                    sources = payload["sources"]
                    results["sources"] = check_sources(sources)

            self.logger.debug(f"Tool results keys populated: {[k for k, v in results.items() if v]}")

        except Exception as e:
            self.logger.error(f"Error running audit tools: {e}")
            raise

        return results

    def synthesize_findings(
        self,
        task_type: str,
        memory_data: Dict[str, Any],
        tool_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesize all findings into a structured summary.

        Compresses tool results and memory context into a single,
        structured response with issue detection and confidence estimation.

        Args:
            task_type: The classified task type.
            memory_data: Results from memory retrieval.
            tool_results: Results from audit tools.

        Returns:
            Structured dictionary containing:
            - task_type: The task type processed
            - summary: Overview with has_major_issues, issue_types, confidence
            - details: Full results from all tools and memory
        """
        self.logger.debug("Synthesizing findings")

        # Analyze results for major issues
        has_major_issues = False
        issue_types: List[str] = []

        # Check audit results
        if tool_results.get("audit"):
            audit = tool_results["audit"]
            if len(audit.get("logical_fallacies", [])) >= FALLACY_COUNT_THRESHOLD:
                has_major_issues = True
                issue_types.append("logical_fallacies")
            if audit.get("inconsistencies"):
                has_major_issues = True
                issue_types.append("inconsistencies")
            if audit.get("unsupported_jumps"):
                issue_types.append("unsupported_claims")

        # Check bias results
        if tool_results.get("bias"):
            bias = tool_results["bias"]
            if bias.get("political_bias", 0) > BIAS_HIGH_THRESHOLD:
                has_major_issues = True
                issue_types.append("high_political_bias")
            if bias.get("emotional_bias", 0) > BIAS_HIGH_THRESHOLD:
                has_major_issues = True
                issue_types.append("high_emotional_bias")
            if bias.get("certainty_overconfidence", 0) > BIAS_HIGH_THRESHOLD:
                issue_types.append("overconfident_claims")

        # Check chain validation results
        if tool_results.get("chain"):
            chain = tool_results["chain"]
            if chain.get("flawed_premises"):
                has_major_issues = True
                issue_types.append("flawed_premises")
            if chain.get("contradictions"):
                has_major_issues = True
                issue_types.append("contradictions")
            if chain.get("gaps"):
                issue_types.append("reasoning_gaps")
            if chain.get("circular_logic"):
                issue_types.append("circular_reasoning")

        # Check source results
        if tool_results.get("sources"):
            sources = tool_results["sources"]
            if sources.get("unverifiable"):
                issue_types.append("unverifiable_sources")

            # Check for low credibility sources
            ranked = sources.get("ranked_confidence", [])
            low_cred_count = sum(
                1 for r in ranked
                if r.get("confidence", 1.0) < CREDIBILITY_LOW_THRESHOLD
            )
            if low_cred_count > 0:
                has_major_issues = True
                issue_types.append("low_credibility_sources")

        # Calculate confidence estimate
        confidence_estimate = self._calculate_confidence(
            tool_results, memory_data, issue_types
        )

        # Remove duplicates from issue_types while preserving order
        seen = set()
        unique_issues = []
        for issue in issue_types:
            if issue not in seen:
                seen.add(issue)
                unique_issues.append(issue)

        result = {
            "task_type": task_type,
            "summary": {
                "has_major_issues": has_major_issues,
                "issue_types": unique_issues,
                "confidence_estimate": round(confidence_estimate, 3),
            },
            "details": {
                "audit": tool_results.get("audit"),
                "bias": tool_results.get("bias"),
                "chain": tool_results.get("chain"),
                "sources": tool_results.get("sources"),
                "memory_context": memory_data,
            },
        }

        self.logger.info(
            f"Synthesis complete: major_issues={has_major_issues}, "
            f"issue_count={len(unique_issues)}, confidence={confidence_estimate:.3f}"
        )

        return result

    def _calculate_confidence(
        self,
        tool_results: Dict[str, Any],
        memory_data: Dict[str, Any],
        issue_types: List[str]
    ) -> float:
        """
        Calculate confidence estimate for the analysis.

        Heuristic based on:
        - Amount of data analyzed
        - Presence/absence of contradictions
        - Clarity of tool outputs

        Args:
            tool_results: Results from audit tools.
            memory_data: Results from memory retrieval.
            issue_types: List of detected issue types.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        confidence = 0.8  # Start with reasonable base confidence

        # Boost for having more data
        tools_used = sum(1 for v in tool_results.values() if v is not None)
        confidence += tools_used * 0.03

        # Boost for memory context
        if memory_data.get("memory_hits"):
            confidence += 0.05

        # Penalty for contradictions (makes analysis less certain)
        if "contradictions" in issue_types:
            confidence -= 0.15

        # Penalty for circular reasoning
        if "circular_reasoning" in issue_types:
            confidence -= 0.10

        # Penalty for many issues (complex situation = less certainty)
        if len(issue_types) > 5:
            confidence -= 0.10
        elif len(issue_types) > 3:
            confidence -= 0.05

        # Ensure bounds
        return max(0.1, min(1.0, confidence))

    def log_contribution(
        self,
        task_type: str,
        payload: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """
        Log the contribution for auditing and tracking.

        Writes to logs/veritas_contributions.log with:
        - timestamp
        - task_type
        - minimal payload metadata (never full text if sensitive)
        - summary section from result

        Args:
            task_type: The task type processed.
            payload: The original payload (metadata only logged).
            result: The synthesis result.
        """
        try:
            # Extract minimal metadata from payload (never log full text)
            payload_meta = {
                "keys": list(payload.keys()),
            }

            if "text" in payload:
                payload_meta["text_length"] = len(payload["text"])
            if "steps" in payload:
                payload_meta["steps_count"] = len(payload["steps"])
            if "chain" in payload:
                payload_meta["chain_length"] = len(payload["chain"])
            if "sources" in payload:
                payload_meta["sources_count"] = len(payload["sources"])

            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "task_type": task_type,
                "payload_metadata": payload_meta,
                "summary": result.get("summary", {}),
            }

            self._contribution_logger.info(json.dumps(log_entry))
            self.logger.debug(f"Contribution logged for task: {task_type}")

        except Exception as e:
            self.logger.error(f"Failed to log contribution: {e}")

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the complete reasoning pipeline.

        This is the main entry point that orchestrates:
        1. Task classification
        2. Memory retrieval
        3. Tool execution
        4. Result synthesis
        5. Contribution logging

        Args:
            payload: The task payload to process.

        Returns:
            Structured analysis results.
        """
        self.logger.info("Starting VeritasBrain processing pipeline")

        # Step 1: Classify the task
        task_type = self.classify_task(payload)

        # Step 2: Retrieve relevant memory
        memory_data = self.retrieve_relevant_memory(payload)

        # Step 3: Run audit tools
        tool_results = self.run_audit_tools(task_type, payload)

        # Step 4: Synthesize findings
        result = self.synthesize_findings(task_type, memory_data, tool_results)

        # Step 5: Log contribution
        self.log_contribution(task_type, payload, result)

        self.logger.info("VeritasBrain processing complete")

        return result


# Module-level instance for convenience
_brain_instance: Optional[VeritasBrain] = None


def get_brain() -> VeritasBrain:
    """Get or create the global VeritasBrain instance."""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = VeritasBrain()
    return _brain_instance
