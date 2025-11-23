"""
Veritas Memory Utilities

Phase 5: Memory storage for dispute analyses and other long-term data.

This module provides utilities for persisting analysis results
to the file system for audit trails and future reference.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from logging.handlers import RotatingFileHandler


# Configure module logger
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = RotatingFileHandler(
        LOG_DIR / "memory_utils.log",
        maxBytes=5_000_000,
        backupCount=3
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)


# Memory storage paths
MEMORY_BASE = Path(__file__).parent / "memory"
DISPUTES_DIR = MEMORY_BASE / "long_term" / "disputes"


def _ensure_dirs() -> None:
    """Ensure all required directories exist."""
    MEMORY_BASE.mkdir(parents=True, exist_ok=True)
    DISPUTES_DIR.mkdir(parents=True, exist_ok=True)


def store_dispute_analysis(dispute: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save a parsed dispute into long_term/disputes/ with timestamp and agent names.

    Args:
        dispute: The dispute analysis result from parse_dispute()

    Returns:
        Dictionary containing:
        - stored: bool - Whether storage succeeded
        - file_path: str - Path to stored file
        - dispute_id: str - Unique identifier for this dispute
    """
    logger.info("Storing dispute analysis")
    _ensure_dirs()

    try:
        # Generate unique ID from timestamp and agents
        timestamp = dispute.get("timestamp") or datetime.now(timezone.utc).isoformat()
        agents = dispute.get("agents", ["unknown", "unknown"])
        agent_str = "_".join(a.replace(" ", "-") for a in agents)

        # Create filename
        ts_str = timestamp.replace(":", "-").replace(".", "-")
        dispute_id = f"dispute_{agent_str}_{ts_str}"
        filename = f"{dispute_id}.json"
        file_path = DISPUTES_DIR / filename

        # Add storage metadata
        dispute_record = {
            **dispute,
            "dispute_id": dispute_id,
            "stored_at": datetime.now(timezone.utc).isoformat(),
        }

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(dispute_record, f, indent=2, ensure_ascii=False)

        logger.info(f"Dispute stored: {filename}")

        return {
            "stored": True,
            "file_path": str(file_path),
            "dispute_id": dispute_id,
        }

    except Exception as e:
        logger.error(f"Failed to store dispute: {e}")
        return {
            "stored": False,
            "file_path": None,
            "dispute_id": None,
            "error": str(e),
        }


def load_dispute_analysis(dispute_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a previously stored dispute analysis.

    Args:
        dispute_id: The unique identifier for the dispute

    Returns:
        The dispute record if found, None otherwise
    """
    _ensure_dirs()

    filename = f"{dispute_id}.json"
    file_path = DISPUTES_DIR / filename

    if not file_path.exists():
        logger.warning(f"Dispute not found: {dispute_id}")
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load dispute {dispute_id}: {e}")
        return None


def list_disputes(limit: int = 100) -> Dict[str, Any]:
    """
    List stored dispute analyses.

    Args:
        limit: Maximum number of disputes to return

    Returns:
        Dictionary containing:
        - disputes: List of dispute summaries
        - total_count: Total number of stored disputes
    """
    _ensure_dirs()

    disputes = []
    try:
        files = sorted(DISPUTES_DIR.glob("*.json"), reverse=True)[:limit]

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    disputes.append({
                        "dispute_id": data.get("dispute_id"),
                        "agents": data.get("agents"),
                        "needs_escalation": data.get("needs_escalation"),
                        "recommendation": data.get("recommendation"),
                        "timestamp": data.get("timestamp"),
                    })
            except Exception:
                continue

        total_count = len(list(DISPUTES_DIR.glob("*.json")))

        return {
            "disputes": disputes,
            "total_count": total_count,
        }

    except Exception as e:
        logger.error(f"Failed to list disputes: {e}")
        return {
            "disputes": [],
            "total_count": 0,
            "error": str(e),
        }


def get_dispute_stats() -> Dict[str, Any]:
    """
    Get statistics about stored disputes.

    Returns:
        Dictionary containing:
        - total_disputes: Total number of stored disputes
        - escalation_counts: Counts by escalation type
        - recommendation_counts: Counts by recommendation type
    """
    _ensure_dirs()

    escalation_counts = {"none": 0, "sophia": 0, "aegis": 0, "congress": 0}
    recommendation_counts = {}

    try:
        for file_path in DISPUTES_DIR.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    escalation = data.get("needs_escalation", "none")
                    recommendation = data.get("recommendation", "unknown")

                    escalation_counts[escalation] = escalation_counts.get(escalation, 0) + 1
                    recommendation_counts[recommendation] = recommendation_counts.get(recommendation, 0) + 1
            except Exception:
                continue

        return {
            "total_disputes": sum(escalation_counts.values()),
            "escalation_counts": escalation_counts,
            "recommendation_counts": recommendation_counts,
        }

    except Exception as e:
        logger.error(f"Failed to get dispute stats: {e}")
        return {
            "total_disputes": 0,
            "escalation_counts": escalation_counts,
            "recommendation_counts": {},
            "error": str(e),
        }


def clear_disputes() -> Dict[str, Any]:
    """
    Clear all stored disputes.

    WARNING: This is destructive and irreversible.

    Returns:
        Dictionary containing:
        - cleared: bool - Whether clearing succeeded
        - count: int - Number of files removed
    """
    _ensure_dirs()

    try:
        count = 0
        for file_path in DISPUTES_DIR.glob("*.json"):
            os.remove(file_path)
            count += 1

        logger.info(f"Cleared {count} disputes")
        return {
            "cleared": True,
            "count": count,
        }

    except Exception as e:
        logger.error(f"Failed to clear disputes: {e}")
        return {
            "cleared": False,
            "count": 0,
            "error": str(e),
        }
