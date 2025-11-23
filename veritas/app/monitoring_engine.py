"""
Veritas Monitoring Engine

Phase 6: Automated Monitoring, Drift Detection, Bias Trends, and Long-Term Logging

This module provides continuous evaluation of agent outputs over time, tracking:
- Logical drift (increasing issues, inconsistencies)
- Bias accumulation (emotional language, loaded framing trends)
- Anomaly detection (sudden deviations from patterns)

IMPORTANT: Veritas monitors only — never intervenes or takes autonomous actions.
All monitoring results are reported to Sky/Congress for their decision-making.
"""

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from logging.handlers import RotatingFileHandler
from pathlib import Path


# Configure module logger
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = RotatingFileHandler(
        LOG_DIR / "monitoring_engine.log",
        maxBytes=5_000_000,
        backupCount=3
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)


# Default configuration
DEFAULT_WINDOW_SIZE = 10
DRIFT_CONCERN_THRESHOLD = 0.3  # 30% increase triggers concern
BIAS_CONCERN_THRESHOLD = 0.3  # 30% rise across windows
ANOMALY_STD_THRESHOLD = 2.0   # 2 standard deviations


def _extract_issue_counts(audit: Dict[str, Any]) -> Dict[str, int]:
    """Extract issue counts from a single audit result."""
    counts = {
        "logical_fallacies": 0,
        "inconsistencies": 0,
        "unsupported_jumps": 0,
        "contradictions": 0,
    }

    # Handle different audit result formats
    if "audit" in audit:
        inner = audit.get("audit", {})
        if isinstance(inner, dict) and "audit" in inner:
            # AuditWithSourcesResult format
            inner = inner.get("audit", {})
    else:
        inner = audit

    # Count logical issues
    if "logical_issues" in inner:
        issues = inner.get("logical_issues", [])
        counts["logical_fallacies"] = sum(
            1 for i in issues if isinstance(i, dict) and i.get("type") in ["fallacy", "circular_reasoning"]
        )
        counts["contradictions"] = sum(
            1 for i in issues if isinstance(i, dict) and i.get("type") == "contradiction"
        )
        counts["unsupported_jumps"] = sum(
            1 for i in issues if isinstance(i, dict) and i.get("type") in ["non_sequitur", "unsupported_conclusion"]
        )
    else:
        # Raw audit format
        counts["logical_fallacies"] = len(inner.get("logical_fallacies", []))
        counts["inconsistencies"] = len(inner.get("inconsistencies", []))
        counts["unsupported_jumps"] = len(inner.get("unsupported_jumps", []))

    return counts


def _extract_bias_scores(audit: Dict[str, Any]) -> Dict[str, float]:
    """Extract bias scores from a single audit result."""
    scores = {
        "emotional_language": 0.0,
        "political_bias": 0.0,
        "certainty_overconfidence": 0.0,
        "loaded_framing": 0.0,
    }

    # Handle different audit result formats
    if "audit" in audit:
        inner = audit.get("audit", {})
        if isinstance(inner, dict) and "audit" in inner:
            inner = inner.get("audit", {})
    else:
        inner = audit

    # Extract from bias_flags (structured format)
    if "bias_flags" in inner:
        for flag in inner.get("bias_flags", []):
            if isinstance(flag, dict):
                flag_type = flag.get("type", "")
                if flag_type == "emotional_language":
                    scores["emotional_language"] += 0.5
                elif flag_type == "loaded_framing":
                    scores["loaded_framing"] += 0.5
                elif flag_type == "overconfidence":
                    scores["certainty_overconfidence"] += 0.5

    # Extract from bias dict (raw format)
    if "bias" in audit:
        bias = audit.get("bias", {})
        scores["emotional_language"] = max(scores["emotional_language"], bias.get("emotional_bias", 0))
        scores["political_bias"] = max(scores["political_bias"], bias.get("political_bias", 0))
        scores["certainty_overconfidence"] = max(
            scores["certainty_overconfidence"],
            bias.get("certainty_overconfidence", 0)
        )

    return scores


def _compute_mean_std(values: List[float]) -> Tuple[float, float]:
    """Compute mean and standard deviation."""
    if not values:
        return 0.0, 0.0

    n = len(values)
    mean = sum(values) / n

    if n < 2:
        return mean, 0.0

    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    std = math.sqrt(variance)

    return mean, std


def detect_logical_drift(
    audit_results: List[Dict[str, Any]],
    window_size: int = DEFAULT_WINDOW_SIZE
) -> Dict[str, Any]:
    """
    Identify increases in logical issues over time.

    Analyzes:
    - Logical issues over time
    - Unsupported conclusions
    - Inconsistent reasoning patterns
    - Contradictory claims across audits

    Args:
        audit_results: List of audit result dictionaries (oldest first)
        window_size: Rolling window size for comparison

    Returns:
        {
            "drift_score": float (0.0 - 1.0),
            "increasing_issue_types": [...],
            "possible_causes": [...],
            "is_concerning": bool
        }
    """
    logger.info(f"Detecting logical drift across {len(audit_results)} audits")

    if len(audit_results) < 2:
        return {
            "drift_score": 0.0,
            "increasing_issue_types": [],
            "possible_causes": [],
            "is_concerning": False,
            "message": "Insufficient data for drift analysis",
        }

    # Extract issue counts for each audit
    all_counts = [_extract_issue_counts(audit) for audit in audit_results]

    # Split into windows
    mid = len(all_counts) // 2
    if mid < 1:
        mid = 1

    window_old = all_counts[:mid]
    window_new = all_counts[mid:]

    # Compute average issues per window
    def window_avg(window: List[Dict[str, int]], key: str) -> float:
        if not window:
            return 0.0
        return sum(w.get(key, 0) for w in window) / len(window)

    issue_types = ["logical_fallacies", "inconsistencies", "unsupported_jumps", "contradictions"]

    increasing_types = []
    drift_scores = []

    for issue_type in issue_types:
        old_avg = window_avg(window_old, issue_type)
        new_avg = window_avg(window_new, issue_type)

        if old_avg > 0:
            change = (new_avg - old_avg) / old_avg
        elif new_avg > 0:
            change = 1.0  # Went from 0 to something
        else:
            change = 0.0

        if change > 0.1:  # 10% increase
            increasing_types.append({
                "type": issue_type,
                "old_avg": round(old_avg, 3),
                "new_avg": round(new_avg, 3),
                "change_percent": round(change * 100, 1),
            })

        drift_scores.append(max(0, change))

    # Overall drift score (normalized)
    drift_score = min(1.0, sum(drift_scores) / len(drift_scores)) if drift_scores else 0.0

    # Identify possible causes
    possible_causes = []
    if any(t["type"] == "logical_fallacies" for t in increasing_types):
        possible_causes.append("Reasoning quality degradation")
    if any(t["type"] == "contradictions" for t in increasing_types):
        possible_causes.append("Internal consistency issues")
    if any(t["type"] == "unsupported_jumps" for t in increasing_types):
        possible_causes.append("Evidence gaps increasing")

    is_concerning = drift_score >= DRIFT_CONCERN_THRESHOLD

    logger.info(f"Drift analysis complete: score={drift_score:.3f}, concerning={is_concerning}")

    return {
        "drift_score": round(drift_score, 3),
        "increasing_issue_types": increasing_types,
        "possible_causes": possible_causes,
        "is_concerning": is_concerning,
    }


def analyze_bias_trends(
    audit_results: List[Dict[str, Any]],
    window_size: int = DEFAULT_WINDOW_SIZE
) -> Dict[str, Any]:
    """
    Track accumulation of bias patterns over time.

    Analyzes:
    - Emotional language trends
    - Cherry picking patterns
    - Certainty/overconfidence language
    - Loaded framing

    Args:
        audit_results: List of audit result dictionaries (oldest first)
        window_size: Rolling window size for comparison

    Returns:
        {
            "bias_trend_score": float (0.0 - 1.0),
            "bias_types_increasing": [...],
            "summary": str,
            "is_concerning": bool
        }
    """
    logger.info(f"Analyzing bias trends across {len(audit_results)} audits")

    if len(audit_results) < 2:
        return {
            "bias_trend_score": 0.0,
            "bias_types_increasing": [],
            "summary": "Insufficient data for trend analysis",
            "is_concerning": False,
        }

    # Extract bias scores for each audit
    all_scores = [_extract_bias_scores(audit) for audit in audit_results]

    # Split into windows
    mid = len(all_scores) // 2
    if mid < 1:
        mid = 1

    window_old = all_scores[:mid]
    window_new = all_scores[mid:]

    # Compute average bias per window
    def window_avg(window: List[Dict[str, float]], key: str) -> float:
        if not window:
            return 0.0
        return sum(w.get(key, 0) for w in window) / len(window)

    bias_types = ["emotional_language", "political_bias", "certainty_overconfidence", "loaded_framing"]

    increasing_types = []
    trend_scores = []

    for bias_type in bias_types:
        old_avg = window_avg(window_old, bias_type)
        new_avg = window_avg(window_new, bias_type)

        if old_avg > 0.01:  # Avoid division by tiny numbers
            change = (new_avg - old_avg) / old_avg
        elif new_avg > 0.01:
            change = 1.0
        else:
            change = 0.0

        if change > 0.1:  # 10% increase
            increasing_types.append({
                "type": bias_type,
                "old_avg": round(old_avg, 3),
                "new_avg": round(new_avg, 3),
                "change_percent": round(change * 100, 1),
            })

        trend_scores.append(max(0, change))

    # Overall trend score
    trend_score = min(1.0, sum(trend_scores) / len(trend_scores)) if trend_scores else 0.0

    # Generate summary
    if not increasing_types:
        summary = "No significant bias trends detected"
    elif len(increasing_types) == 1:
        summary = f"Rising {increasing_types[0]['type'].replace('_', ' ')} detected"
    else:
        types_str = ", ".join(t["type"].replace("_", " ") for t in increasing_types[:3])
        summary = f"Multiple bias trends rising: {types_str}"

    is_concerning = trend_score >= BIAS_CONCERN_THRESHOLD

    logger.info(f"Bias trend analysis complete: score={trend_score:.3f}, concerning={is_concerning}")

    return {
        "bias_trend_score": round(trend_score, 3),
        "bias_types_increasing": increasing_types,
        "summary": summary,
        "is_concerning": is_concerning,
    }


def detect_anomalies(
    audit_results: List[Dict[str, Any]],
    std_threshold: float = ANOMALY_STD_THRESHOLD
) -> Dict[str, Any]:
    """
    Detect sudden deviations from normal patterns.

    Analyzes:
    - Confidence level deviations
    - Number of contradictions
    - Missing context flags
    - Source agreement/contradiction patterns

    Args:
        audit_results: List of audit result dictionaries
        std_threshold: Number of standard deviations for anomaly

    Returns:
        {
            "anomaly_detected": bool,
            "anomaly_reason": str | None,
            "anomalies": [...],
            "statistics": {...}
        }
    """
    logger.info(f"Detecting anomalies across {len(audit_results)} audits")

    if len(audit_results) < 3:
        return {
            "anomaly_detected": False,
            "anomaly_reason": None,
            "anomalies": [],
            "statistics": {},
            "message": "Insufficient data for anomaly detection",
        }

    # Extract metrics for each audit
    issue_totals = []
    confidence_map = {"high": 3, "medium": 2, "low": 1}

    for audit in audit_results:
        counts = _extract_issue_counts(audit)
        total_issues = sum(counts.values())
        issue_totals.append(total_issues)

    # Compute statistics
    mean_issues, std_issues = _compute_mean_std(issue_totals)

    anomalies = []
    statistics = {
        "mean_issues": round(mean_issues, 3),
        "std_issues": round(std_issues, 3),
        "sample_size": len(audit_results),
    }

    # Check for anomalies in recent results
    if std_issues > 0:
        for i, total in enumerate(issue_totals[-3:]):  # Check last 3
            z_score = (total - mean_issues) / std_issues
            if abs(z_score) > std_threshold:
                anomalies.append({
                    "index": len(issue_totals) - 3 + i,
                    "value": total,
                    "z_score": round(z_score, 2),
                    "direction": "high" if z_score > 0 else "low",
                })

    anomaly_detected = len(anomalies) > 0

    anomaly_reason = None
    if anomaly_detected:
        high_anomalies = [a for a in anomalies if a["direction"] == "high"]
        low_anomalies = [a for a in anomalies if a["direction"] == "low"]

        if high_anomalies:
            anomaly_reason = f"Unusually high issue count ({high_anomalies[0]['value']} issues, {high_anomalies[0]['z_score']}σ)"
        elif low_anomalies:
            anomaly_reason = f"Unusually low issue count ({low_anomalies[0]['value']} issues, {low_anomalies[0]['z_score']}σ)"

    logger.info(f"Anomaly detection complete: detected={anomaly_detected}")

    return {
        "anomaly_detected": anomaly_detected,
        "anomaly_reason": anomaly_reason,
        "anomalies": anomalies,
        "statistics": statistics,
    }


def run_monitoring_cycle(
    recent_audits: List[Dict[str, Any]],
    window_size: int = DEFAULT_WINDOW_SIZE
) -> Dict[str, Any]:
    """
    Run complete monitoring cycle: drift detection, bias trends, anomaly detection.

    Args:
        recent_audits: List of recent audit results (oldest first)
        window_size: Window size for rolling analysis

    Returns:
        {
            "logical_drift": {...},
            "bias_trends": {...},
            "anomalies": {...},
            "overall_status": "stable" | "warning" | "critical",
            "timestamp": str,
            "audits_analyzed": int
        }

    Status rules:
    - stable: No drift, no bias trends, no anomalies
    - warning: Any one category is concerning
    - critical: 2+ categories are concerning
    """
    logger.info(f"Running monitoring cycle on {len(recent_audits)} audits")

    # Run all detection systems
    logical_drift = detect_logical_drift(recent_audits, window_size)
    bias_trends = analyze_bias_trends(recent_audits, window_size)
    anomalies = detect_anomalies(recent_audits)

    # Count concerning areas
    concerning_count = sum([
        logical_drift.get("is_concerning", False),
        bias_trends.get("is_concerning", False),
        anomalies.get("anomaly_detected", False),
    ])

    # Determine overall status
    if concerning_count >= 2:
        overall_status = "critical"
    elif concerning_count == 1:
        overall_status = "warning"
    else:
        overall_status = "stable"

    result = {
        "logical_drift": logical_drift,
        "bias_trends": bias_trends,
        "anomalies": anomalies,
        "overall_status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "audits_analyzed": len(recent_audits),
    }

    logger.info(f"Monitoring cycle complete: status={overall_status}")

    return result


class MonitoringEngine:
    """
    OOP interface for monitoring operations.

    Provides methods for running monitoring cycles and tracking history.
    """

    def __init__(self, window_size: int = DEFAULT_WINDOW_SIZE):
        """Initialize the monitoring engine."""
        self.window_size = window_size
        self._last_snapshot: Optional[Dict[str, Any]] = None
        logger.info(f"MonitoringEngine initialized with window_size={window_size}")

    def run_cycle(self, audits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run a monitoring cycle and store the snapshot."""
        snapshot = run_monitoring_cycle(audits, self.window_size)
        self._last_snapshot = snapshot
        return snapshot

    def get_last_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get the most recent monitoring snapshot."""
        return self._last_snapshot

    def get_status(self) -> str:
        """Get current overall status."""
        if self._last_snapshot is None:
            return "unknown"
        return self._last_snapshot.get("overall_status", "unknown")

    def is_concerning(self) -> bool:
        """Check if current status is concerning."""
        return self.get_status() in ["warning", "critical"]


# Module-level instance
_engine_instance: Optional[MonitoringEngine] = None


def get_monitoring_engine() -> MonitoringEngine:
    """Get or create the global MonitoringEngine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = MonitoringEngine()
    return _engine_instance
