"""
Veritas Memory Utilities

Phase 6: Memory storage for dispute analyses, audit trails, and monitoring snapshots.

This module provides utilities for persisting analysis results
to the file system for audit trails and future reference.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

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
AUDITS_DIR = MEMORY_BASE / "long_term" / "audits"
MONITORING_DIR = MEMORY_BASE / "long_term" / "monitoring"


def _ensure_dirs() -> None:
    """Ensure all required directories exist."""
    MEMORY_BASE.mkdir(parents=True, exist_ok=True)
    DISPUTES_DIR.mkdir(parents=True, exist_ok=True)
    AUDITS_DIR.mkdir(parents=True, exist_ok=True)
    MONITORING_DIR.mkdir(parents=True, exist_ok=True)


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


# ============================================================================
# Audit Storage (Phase 6)
# ============================================================================


def store_audit(audit: Dict[str, Any], audit_type: str = "general") -> Dict[str, Any]:
    """
    Store an audit result for long-term tracking and monitoring.

    Args:
        audit: The audit result to store
        audit_type: Type of audit (general, bill, statement, etc.)

    Returns:
        Dictionary containing:
        - stored: bool - Whether storage succeeded
        - file_path: str - Path to stored file
        - audit_id: str - Unique identifier for this audit
    """
    logger.info(f"Storing audit of type: {audit_type}")
    _ensure_dirs()

    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        ts_str = timestamp.replace(":", "-").replace(".", "-")
        audit_id = f"audit_{audit_type}_{ts_str}"
        filename = f"{audit_id}.json"
        file_path = AUDITS_DIR / filename

        audit_record = {
            **audit,
            "audit_id": audit_id,
            "audit_type": audit_type,
            "stored_at": timestamp,
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(audit_record, f, indent=2, ensure_ascii=False)

        logger.info(f"Audit stored: {filename}")

        return {
            "stored": True,
            "file_path": str(file_path),
            "audit_id": audit_id,
        }

    except Exception as e:
        logger.error(f"Failed to store audit: {e}")
        return {
            "stored": False,
            "file_path": None,
            "audit_id": None,
            "error": str(e),
        }


def get_recent_audits(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Load last <limit> audit files from long_term/audits.

    Args:
        limit: Maximum number of audits to return

    Returns:
        List of audit dictionaries (oldest first for time-series analysis)
    """
    logger.info(f"Loading recent audits (limit={limit})")
    _ensure_dirs()

    audits = []
    try:
        # Sort by modification time, newest first
        files = sorted(
            AUDITS_DIR.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )[:limit]

        # Load each file
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    audits.append(json.load(f))
            except Exception as e:
                logger.warning(f"Failed to load audit {file_path}: {e}")
                continue

        # Reverse to get oldest first (for time-series analysis)
        audits.reverse()

        logger.info(f"Loaded {len(audits)} audits")
        return audits

    except Exception as e:
        logger.error(f"Failed to get recent audits: {e}")
        return []


def list_audits(limit: int = 100) -> Dict[str, Any]:
    """
    List stored audits with summary information.

    Args:
        limit: Maximum number of audits to return

    Returns:
        Dictionary containing:
        - audits: List of audit summaries
        - total_count: Total number of stored audits
    """
    _ensure_dirs()

    audit_summaries = []
    try:
        files = sorted(
            AUDITS_DIR.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )[:limit]

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    audit_summaries.append({
                        "audit_id": data.get("audit_id"),
                        "audit_type": data.get("audit_type"),
                        "stored_at": data.get("stored_at"),
                    })
            except Exception:
                continue

        total_count = len(list(AUDITS_DIR.glob("*.json")))

        return {
            "audits": audit_summaries,
            "total_count": total_count,
        }

    except Exception as e:
        logger.error(f"Failed to list audits: {e}")
        return {
            "audits": [],
            "total_count": 0,
            "error": str(e),
        }


# ============================================================================
# Monitoring Snapshots (Phase 6)
# ============================================================================


def store_monitoring_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save monitoring snapshot to long_term/monitoring/.

    Args:
        snapshot: The monitoring snapshot from run_monitoring_cycle()

    Returns:
        Dictionary containing:
        - stored: bool - Whether storage succeeded
        - file_path: str - Path to stored file
        - snapshot_id: str - Unique identifier for this snapshot
    """
    logger.info("Storing monitoring snapshot")
    _ensure_dirs()

    try:
        timestamp = snapshot.get("timestamp") or datetime.now(timezone.utc).isoformat()
        # Format: YYYY-MM-DD_HH-MM
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        filename = dt.strftime("%Y-%m-%d_%H-%M") + ".json"
        snapshot_id = f"monitoring_{filename.replace('.json', '')}"
        file_path = MONITORING_DIR / filename

        snapshot_record = {
            **snapshot,
            "snapshot_id": snapshot_id,
            "stored_at": datetime.now(timezone.utc).isoformat(),
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(snapshot_record, f, indent=2, ensure_ascii=False)

        logger.info(f"Monitoring snapshot stored: {filename}")

        return {
            "stored": True,
            "file_path": str(file_path),
            "snapshot_id": snapshot_id,
        }

    except Exception as e:
        logger.error(f"Failed to store monitoring snapshot: {e}")
        return {
            "stored": False,
            "file_path": None,
            "snapshot_id": None,
            "error": str(e),
        }


def get_recent_monitoring_snapshots(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Load recent monitoring snapshots.

    Args:
        limit: Maximum number of snapshots to return

    Returns:
        List of snapshot dictionaries (newest first)
    """
    logger.info(f"Loading recent monitoring snapshots (limit={limit})")
    _ensure_dirs()

    snapshots = []
    try:
        files = sorted(
            MONITORING_DIR.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )[:limit]

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    snapshots.append(json.load(f))
            except Exception as e:
                logger.warning(f"Failed to load snapshot {file_path}: {e}")
                continue

        logger.info(f"Loaded {len(snapshots)} monitoring snapshots")
        return snapshots

    except Exception as e:
        logger.error(f"Failed to get monitoring snapshots: {e}")
        return []


def get_monitoring_stats() -> Dict[str, Any]:
    """
    Get statistics about monitoring snapshots.

    Returns:
        Dictionary containing:
        - total_snapshots: Total number of stored snapshots
        - status_counts: Counts by overall status
        - latest_status: Most recent status
    """
    _ensure_dirs()

    status_counts = {"stable": 0, "warning": 0, "critical": 0}
    latest_status = "unknown"

    try:
        files = sorted(
            MONITORING_DIR.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )

        for i, file_path in enumerate(files):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    status = data.get("overall_status", "unknown")

                    if i == 0:
                        latest_status = status

                    if status in status_counts:
                        status_counts[status] += 1
            except Exception:
                continue

        return {
            "total_snapshots": len(files),
            "status_counts": status_counts,
            "latest_status": latest_status,
        }

    except Exception as e:
        logger.error(f"Failed to get monitoring stats: {e}")
        return {
            "total_snapshots": 0,
            "status_counts": status_counts,
            "latest_status": "unknown",
            "error": str(e),
        }
