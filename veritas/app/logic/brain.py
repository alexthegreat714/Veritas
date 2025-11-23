"""
Veritas Brain - Central Reasoning Engine

This module contains the VeritasBrain class that coordinates:
- Task classification
- Memory retrieval (RAG)
- Analytical tool orchestration
- Structured output synthesis
- Contribution logging
- Event handling (Phase 5)
- Legislative functions (Phase 6)

Phase 6: Legislative functions for Congress interaction.
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
from app.rag.query import RAGQuery, query_relevant_documents


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
        - If mode="vote" with bill_text -> "vote_on_bill"
        - If mode="adversarial" with bill_text -> "adversarial_contribution"
        - If text and no steps/sources -> "audit_text"
        - If steps list present -> "validate_chain"
        - If sources list present -> "check_sources"
        - If combination -> "composite_audit"

        Args:
            payload: Arbitrary JSON payload from /run_task or /event.

        Returns:
            String task type: "audit_text", "validate_chain",
            "check_sources", "composite_audit", "vote_on_bill",
            or "adversarial_contribution".
        """
        self.logger.debug(f"Classifying task with keys: {list(payload.keys())}")

        # Check for legislative modes (Phase 6)
        mode = payload.get("mode", "")
        has_bill_text = "bill_text" in payload and bool(payload["bill_text"])

        if has_bill_text:
            if mode == "vote":
                task_type = "vote_on_bill"
                self.logger.info(f"Task classified as: {task_type}")
                return task_type
            elif mode == "adversarial":
                task_type = "adversarial_contribution"
                self.logger.info(f"Task classified as: {task_type}")
                return task_type

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
        the local memory corpus for relevant information.

        Priority for query text extraction:
        1. payload.get("topic")
        2. payload.get("text")
        3. payload.get("context")
        4. First step from payload.get("steps") or payload.get("chain")
        5. Fallback to "general"

        Args:
            payload: The task payload containing query context.

        Returns:
            Dictionary containing:
            - memory_hits: List of relevant documents with scores
            - memory_summary: Short summary or empty string
        """
        self.logger.debug("Retrieving relevant memory from RAG system")

        # Extract query text from payload (priority order per spec)
        query_text = ""
        if "topic" in payload and payload["topic"]:
            query_text = str(payload["topic"])[:500]
        elif "text" in payload and payload["text"]:
            query_text = str(payload["text"])[:500]
        elif "context" in payload and payload["context"]:
            query_text = str(payload["context"])[:500]
        elif "steps" in payload and payload["steps"]:
            query_text = str(payload["steps"][0])[:200]
        elif "chain" in payload and payload["chain"]:
            query_text = str(payload["chain"][0])[:200]
        else:
            query_text = "general"

        if not query_text.strip():
            query_text = "general"

        self.logger.debug(f"Memory query: '{query_text[:50]}...'")

        try:
            # Query the RAG system directly
            rag_result = query_relevant_documents(query_text, top_k=5)

            # Extract hits
            memory_hits = rag_result.get("hits", [])

            # Generate summary based on results
            if memory_hits:
                top_score = memory_hits[0].get("score", 0) if memory_hits else 0
                memory_summary = f"Found {len(memory_hits)} relevant entries (top score: {top_score:.2f})"
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
                "memory_summary": "",
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
            "legislative": None,  # Phase 6: Legislative results
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

            elif task_type == "vote_on_bill":
                # Phase 6: Legislative voting
                from app.logic.legislative import vote_on_bill
                bill_text = payload.get("bill_text", "")
                bill_id = payload.get("bill_id")
                results["legislative"] = vote_on_bill(bill_text, bill_id)

            elif task_type == "adversarial_contribution":
                # Phase 6: Adversarial contribution
                from app.logic.legislative import adversarial_contribution
                bill_text = payload.get("bill_text", "")
                bill_id = payload.get("bill_id")
                results["legislative"] = adversarial_contribution(bill_text, bill_id)

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
                "legislative": tool_results.get("legislative"),  # Phase 6
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

    # ========================================================================
    # Event Handling (Phase 5/6) - Inter-agent communication
    # ========================================================================

    # Mapping from event_type to internal task_type
    EVENT_TYPE_MAPPING = {
        "audit-request": "audit_text",
        "bill-logic-check": "audit_text",
        "argument-integrity-check": "validate_chain",
        "source-integrity-check": "check_sources",
        "composite-audit": "composite_audit",
        # Phase 6: Legislative event types
        "bill-vote-request": "vote_on_bill",
        "bill-adversarial-request": "adversarial_contribution",
    }

    # Valid event types
    VALID_EVENT_TYPES = set(EVENT_TYPE_MAPPING.keys())

    def handle_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        source: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        High-level handler for event-based calls from other agents.

        Maps event types into internal task types and runs the full
        analysis pipeline. Used by the /event endpoint.

        Supported event_type values:
        - "audit-request": General text audit (logic + bias)
            - Uses payload.text
            - Sky uses this for general text analysis
        - "bill-logic-check": Audit a proposed bill or policy
            - Uses payload.bill_text or payload.text
            - Congress/Bill Engine uses this
        - "argument-integrity-check": Validate chain-of-thought reasoning
            - Uses payload.steps
            - Aero/Mercury/Apollo use this for reasoning chains
        - "source-integrity-check": Validate supporting sources
            - Uses payload.sources
            - Used for reference list validation
        - "composite-audit": Combined analysis of multiple data types
            - Uses any combination of text, steps, sources
            - Sky uses this for complex cases
        - "bill-vote-request": Vote on a bill (Phase 6)
            - Uses payload.bill_text
            - Congress uses this for legislative votes
        - "bill-adversarial-request": Adversarial contribution (Phase 6)
            - Uses payload.bill_text
            - Congress uses this for devil's advocate analysis

        Args:
            event_type: The event type string from VeritasEvent.
            payload: The task-specific content from VeritasEvent.
            source: The sender agent ID (for logging purposes only).

        Returns:
            Dictionary containing:
            - ok: Whether processing succeeded
            - task_type: The internal task type used
            - summary: Analysis summary
            - details: Full analysis details

        Raises:
            ValueError: If event_type is not recognized.
        """
        self.logger.info(f"Handling event: type={event_type}, source={source}")

        # Validate event type
        if event_type not in self.VALID_EVENT_TYPES:
            self.logger.warning(f"Unknown event type: {event_type}")
            raise ValueError(
                f"Unknown event_type '{event_type}'. "
                f"Valid types: {sorted(self.VALID_EVENT_TYPES)}"
            )

        # Normalize payload based on event type
        normalized_payload = self._normalize_event_payload(event_type, payload)

        # Get the mapped internal task type
        mapped_task_type = self.EVENT_TYPE_MAPPING[event_type]

        # Run the pipeline
        task_type = self.classify_task(normalized_payload)
        memory_data = self.retrieve_relevant_memory(normalized_payload)
        tool_results = self.run_audit_tools(task_type, normalized_payload)
        result = self.synthesize_findings(task_type, memory_data, tool_results)

        # Log with event metadata
        self._log_event_contribution(
            event_type, source, normalized_payload, result
        )

        self.logger.info(f"Event handling complete: {event_type}")

        return {
            "ok": True,
            "task_type": result["task_type"],
            "summary": result["summary"],
            "details": result["details"],
        }

    def _normalize_event_payload(
        self,
        event_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize event payload to match internal expectations.

        Handles event-specific field mappings:
        - bill-logic-check: Maps bill_text -> text
        - argument-integrity-check: Ensures steps is a list
        - source-integrity-check: Ensures sources is a list
        - bill-vote-request: Sets mode to "vote" (Phase 6)
        - bill-adversarial-request: Sets mode to "adversarial" (Phase 6)

        Args:
            event_type: The event type.
            payload: The raw payload from the event.

        Returns:
            Normalized payload dict.
        """
        normalized = dict(payload)

        if event_type == "bill-logic-check":
            # Map bill_text to text for processing
            if "bill_text" in normalized and "text" not in normalized:
                normalized["text"] = normalized["bill_text"]

        elif event_type == "argument-integrity-check":
            # Ensure steps is present
            if "steps" not in normalized and "chain" in normalized:
                normalized["steps"] = normalized["chain"]

        elif event_type == "source-integrity-check":
            # Ensure sources is a list
            if "sources" not in normalized:
                normalized["sources"] = []

        elif event_type == "bill-vote-request":
            # Phase 6: Set mode for legislative voting
            normalized["mode"] = "vote"

        elif event_type == "bill-adversarial-request":
            # Phase 6: Set mode for adversarial contribution
            normalized["mode"] = "adversarial"

        return normalized

    def _log_event_contribution(
        self,
        event_type: str,
        source: Optional[str],
        payload: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """
        Log event contribution with event-specific metadata.

        Similar to log_contribution but includes event type and source.

        Args:
            event_type: The event type processed.
            source: The sender agent ID.
            payload: The normalized payload.
            result: The synthesis result.
        """
        try:
            # Extract minimal metadata from payload
            payload_meta = {
                "keys": list(payload.keys()),
            }

            if "text" in payload:
                payload_meta["text_length"] = len(payload["text"])
            if "bill_text" in payload:
                payload_meta["bill_text_length"] = len(payload["bill_text"])
            if "steps" in payload:
                payload_meta["steps_count"] = len(payload["steps"])
            if "chain" in payload:
                payload_meta["chain_length"] = len(payload["chain"])
            if "sources" in payload:
                payload_meta["sources_count"] = len(payload["sources"])

            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "source": source,
                "task_type": result.get("task_type"),
                "payload_metadata": payload_meta,
                "summary": result.get("summary", {}),
            }

            self._contribution_logger.info(json.dumps(log_entry))
            self.logger.debug(f"Event contribution logged: {event_type} from {source}")

        except Exception as e:
            self.logger.error(f"Failed to log event contribution: {e}")


# Module-level instance for convenience
_brain_instance: Optional[VeritasBrain] = None


def get_brain() -> VeritasBrain:
    """Get or create the global VeritasBrain instance."""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = VeritasBrain()
    return _brain_instance
