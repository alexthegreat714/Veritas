"""
Veritas Trend Engine

Phase 7: Long-Term Trend Analytics, Performance Metrics, and Professional Reporting

This module performs long-term analysis across all saved audits to identify:
- Bias trends over time (weekly buckets)
- Logic issue trends
- Source reliability trends
- Performance scoring

IMPORTANT: Veritas monitors only — never intervenes or takes autonomous actions.
All trend analysis is informational and reported for review.
"""

import json
import logging
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from logging.handlers import RotatingFileHandler


# Configure module logger
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = RotatingFileHandler(
        LOG_DIR / "trend_engine.log",
        maxBytes=5_000_000,
        backupCount=3
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)


# Paths
MEMORY_BASE = Path(__file__).parent / "memory" / "long_term"
AUDITS_DIR = MEMORY_BASE / "audits"


def _get_iso_week(timestamp_str: str) -> str:
    """Extract ISO week from timestamp string (YYYY-WXX format)."""
    try:
        # Handle various timestamp formats
        if "T" in timestamp_str:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        else:
            dt = datetime.strptime(timestamp_str[:10], "%Y-%m-%d")
        iso_cal = dt.isocalendar()
        return f"{iso_cal.year}-W{iso_cal.week:02d}"
    except Exception:
        return "unknown"


def _compute_linear_slope(values: List[float]) -> float:
    """
    Compute simple linear regression slope.

    Uses least squares method without external libraries.
    Returns slope (change per unit time).
    """
    if len(values) < 2:
        return 0.0

    n = len(values)
    x = list(range(n))

    x_mean = sum(x) / n
    y_mean = sum(values) / n

    numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return 0.0

    return numerator / denominator


def load_all_audits() -> List[Dict[str, Any]]:
    """
    Load ALL audits in long_term/audits/.

    Returns:
        List of audit dicts sorted by timestamp (oldest first).
    """
    logger.info("Loading all audits from storage")

    if not AUDITS_DIR.exists():
        logger.warning(f"Audits directory does not exist: {AUDITS_DIR}")
        return []

    audits = []

    for file_path in AUDITS_DIR.glob("*.json"):
        try:
            with open(file_path, "r") as f:
                audit = json.load(f)
                # Ensure timestamp exists
                if "timestamp" not in audit:
                    # Try to extract from filename
                    audit["timestamp"] = file_path.stem.split("_")[-1] if "_" in file_path.stem else datetime.now(timezone.utc).isoformat()
                audits.append(audit)
        except Exception as e:
            logger.error(f"Error loading audit {file_path}: {e}")

    # Sort by timestamp
    audits.sort(key=lambda a: a.get("timestamp", ""))

    logger.info(f"Loaded {len(audits)} audits")
    return audits


def _extract_bias_flags(audit: Dict[str, Any]) -> List[str]:
    """Extract bias flag types from an audit."""
    flags = []

    # Navigate audit structure
    inner = audit
    if "audit" in audit:
        inner = audit.get("audit", {})
        if isinstance(inner, dict) and "audit" in inner:
            inner = inner.get("audit", {})

    # Extract from bias_flags (structured format)
    for flag in inner.get("bias_flags", []):
        if isinstance(flag, dict):
            flags.append(flag.get("type", "unknown"))
        elif isinstance(flag, str):
            flags.append(flag)

    # Extract from bias dict (raw format)
    if "bias" in audit:
        bias = audit.get("bias", {})
        if bias.get("emotional_bias", 0) > 0.3:
            flags.append("emotional_language")
        if bias.get("political_bias", 0) > 0.3:
            flags.append("political_bias")
        if bias.get("certainty_overconfidence", 0) > 0.3:
            flags.append("certainty_overconfidence")

    return flags


def _extract_logic_issues(audit: Dict[str, Any]) -> List[str]:
    """Extract logic issue types from an audit."""
    issues = []

    # Navigate audit structure
    inner = audit
    if "audit" in audit:
        inner = audit.get("audit", {})
        if isinstance(inner, dict) and "audit" in inner:
            inner = inner.get("audit", {})

    # Extract from logical_issues (structured format)
    for issue in inner.get("logical_issues", []):
        if isinstance(issue, dict):
            issues.append(issue.get("type", "unknown"))
        elif isinstance(issue, str):
            issues.append(issue)

    # Extract from raw format
    for fallacy in inner.get("logical_fallacies", []):
        if isinstance(fallacy, dict):
            issues.append(fallacy.get("type", "fallacy"))
        else:
            issues.append("fallacy")

    for _ in inner.get("inconsistencies", []):
        issues.append("inconsistency")

    for _ in inner.get("unsupported_jumps", []):
        issues.append("unsupported_conclusion")

    return issues


def _extract_source_validation(audit: Dict[str, Any]) -> Dict[str, int]:
    """Extract source validation stats from an audit."""
    stats = {
        "supporting": 0,
        "contradicting": 0,
        "missing_context": 0,
        "total_claims": 0,
    }

    # Navigate audit structure
    inner = audit
    if "audit" in audit:
        inner = audit.get("audit", {})

    # Extract from source_validation
    for sv in inner.get("source_validation", []):
        if isinstance(sv, dict):
            stats["total_claims"] += 1
            if sv.get("supporting"):
                stats["supporting"] += 1
            if sv.get("contradicting"):
                stats["contradicting"] += 1
            if sv.get("missing_context"):
                stats["missing_context"] += 1

    return stats


def compute_bias_over_time(audits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    For each bias type, count occurrences per week and generate time series.

    Args:
        audits: List of audit dictionaries sorted by timestamp.

    Returns:
        {
            "bias_types": {
                "emotional_language": [{"week": "2024-W01", "count": 3}, ...],
                ...
            },
            "slopes": {"emotional_language": 0.5, ...},
            "top_increasing": ["emotional_language", ...],
            "top_decreasing": ["political_bias", ...]
        }
    """
    logger.info(f"Computing bias trends over {len(audits)} audits")

    if not audits:
        return {
            "bias_types": {},
            "slopes": {},
            "top_increasing": [],
            "top_decreasing": [],
            "message": "No audits available for trend analysis",
        }

    # Group by week
    weekly_counts: Dict[str, Dict[str, int]] = {}

    for audit in audits:
        week = _get_iso_week(audit.get("timestamp", ""))
        if week == "unknown":
            continue

        if week not in weekly_counts:
            weekly_counts[week] = {}

        for bias_type in _extract_bias_flags(audit):
            weekly_counts[week][bias_type] = weekly_counts[week].get(bias_type, 0) + 1

    # Get all bias types
    all_bias_types = set()
    for week_data in weekly_counts.values():
        all_bias_types.update(week_data.keys())

    # Sort weeks
    sorted_weeks = sorted(weekly_counts.keys())

    # Build time series for each bias type
    bias_types = {}
    slopes = {}

    for bias_type in all_bias_types:
        series = []
        values = []
        for week in sorted_weeks:
            count = weekly_counts[week].get(bias_type, 0)
            series.append({"week": week, "count": count})
            values.append(count)

        bias_types[bias_type] = series
        slopes[bias_type] = round(_compute_linear_slope(values), 4)

    # Find top increasing and decreasing
    sorted_slopes = sorted(slopes.items(), key=lambda x: x[1], reverse=True)
    top_increasing = [k for k, v in sorted_slopes if v > 0.01][:3]
    top_decreasing = [k for k, v in sorted_slopes if v < -0.01][:3]

    return {
        "bias_types": bias_types,
        "slopes": slopes,
        "top_increasing": top_increasing,
        "top_decreasing": top_decreasing,
    }


def compute_logic_issue_trends(audits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Count each logical issue type per week and produce slope/trend summary.

    Args:
        audits: List of audit dictionaries sorted by timestamp.

    Returns:
        {
            "issue_types": {
                "contradiction": [{"week": "2024-W01", "count": 2}, ...],
                ...
            },
            "slopes": {"contradiction": 0.3, ...},
            "notable_trends": ["Contradictions increasing", ...]
        }
    """
    logger.info(f"Computing logic issue trends over {len(audits)} audits")

    if not audits:
        return {
            "issue_types": {},
            "slopes": {},
            "notable_trends": [],
            "message": "No audits available for trend analysis",
        }

    # Group by week
    weekly_counts: Dict[str, Dict[str, int]] = {}

    for audit in audits:
        week = _get_iso_week(audit.get("timestamp", ""))
        if week == "unknown":
            continue

        if week not in weekly_counts:
            weekly_counts[week] = {}

        for issue_type in _extract_logic_issues(audit):
            weekly_counts[week][issue_type] = weekly_counts[week].get(issue_type, 0) + 1

    # Get all issue types
    all_issue_types = set()
    for week_data in weekly_counts.values():
        all_issue_types.update(week_data.keys())

    # Sort weeks
    sorted_weeks = sorted(weekly_counts.keys())

    # Build time series for each issue type
    issue_types = {}
    slopes = {}

    for issue_type in all_issue_types:
        series = []
        values = []
        for week in sorted_weeks:
            count = weekly_counts[week].get(issue_type, 0)
            series.append({"week": week, "count": count})
            values.append(count)

        issue_types[issue_type] = series
        slopes[issue_type] = round(_compute_linear_slope(values), 4)

    # Generate notable trends
    notable_trends = []
    for issue_type, slope in slopes.items():
        if slope > 0.1:
            notable_trends.append(f"{issue_type.replace('_', ' ').title()} increasing significantly")
        elif slope < -0.1:
            notable_trends.append(f"{issue_type.replace('_', ' ').title()} decreasing")

    return {
        "issue_types": issue_types,
        "slopes": slopes,
        "notable_trends": notable_trends,
    }


def compute_source_reliability_trends(audits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Track how often retrieved sources support/contradict claims.

    Args:
        audits: List of audit dictionaries sorted by timestamp.

    Returns:
        {
            "support_rate": [{"week": "2024-W01", "rate": 0.8}, ...],
            "contradiction_rate": [...],
            "missing_context_rate": [...],
            "slopes": {"support_rate": 0.01, ...},
            "summary": str
        }
    """
    logger.info(f"Computing source reliability trends over {len(audits)} audits")

    if not audits:
        return {
            "support_rate": [],
            "contradiction_rate": [],
            "missing_context_rate": [],
            "slopes": {},
            "summary": "No audits available for trend analysis",
        }

    # Group by week
    weekly_stats: Dict[str, Dict[str, int]] = {}

    for audit in audits:
        week = _get_iso_week(audit.get("timestamp", ""))
        if week == "unknown":
            continue

        if week not in weekly_stats:
            weekly_stats[week] = {
                "supporting": 0,
                "contradicting": 0,
                "missing_context": 0,
                "total_claims": 0,
            }

        stats = _extract_source_validation(audit)
        for key in ["supporting", "contradicting", "missing_context", "total_claims"]:
            weekly_stats[week][key] += stats[key]

    # Sort weeks
    sorted_weeks = sorted(weekly_stats.keys())

    # Build rate series
    support_rate = []
    contradiction_rate = []
    missing_context_rate = []

    support_values = []
    contradiction_values = []
    missing_values = []

    for week in sorted_weeks:
        stats = weekly_stats[week]
        total = stats["total_claims"] or 1  # Avoid division by zero

        s_rate = stats["supporting"] / total
        c_rate = stats["contradicting"] / total
        m_rate = stats["missing_context"] / total

        support_rate.append({"week": week, "rate": round(s_rate, 3)})
        contradiction_rate.append({"week": week, "rate": round(c_rate, 3)})
        missing_context_rate.append({"week": week, "rate": round(m_rate, 3)})

        support_values.append(s_rate)
        contradiction_values.append(c_rate)
        missing_values.append(m_rate)

    # Compute slopes
    slopes = {
        "support_rate": round(_compute_linear_slope(support_values), 4),
        "contradiction_rate": round(_compute_linear_slope(contradiction_values), 4),
        "missing_context_rate": round(_compute_linear_slope(missing_values), 4),
    }

    # Generate summary
    summary_parts = []
    if slopes["support_rate"] > 0.01:
        summary_parts.append("Source support improving")
    elif slopes["support_rate"] < -0.01:
        summary_parts.append("Source support declining")

    if slopes["contradiction_rate"] > 0.01:
        summary_parts.append("Source contradictions increasing")
    elif slopes["contradiction_rate"] < -0.01:
        summary_parts.append("Source contradictions decreasing")

    if slopes["missing_context_rate"] > 0.01:
        summary_parts.append("Missing context increasing")
    elif slopes["missing_context_rate"] < -0.01:
        summary_parts.append("Missing context decreasing")

    summary = "; ".join(summary_parts) if summary_parts else "Source reliability stable"

    return {
        "support_rate": support_rate,
        "contradiction_rate": contradiction_rate,
        "missing_context_rate": missing_context_rate,
        "slopes": slopes,
        "summary": summary,
    }


def compute_performance_score(
    trends: Dict[str, Any],
    monitoring: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Combine long-term trends + recent monitoring to generate performance score.

    Args:
        trends: Combined trend data (bias, logic, source trends).
        monitoring: Recent monitoring snapshot (optional).

    Returns:
        {
            "score": float (0-100),
            "grades": {
                "bias_analysis": "A/B/C/D",
                "logic_analysis": "A/B/C/D",
                "source_validation": "A/B/C/D",
                "monitoring_stability": "A/B/C/D"
            },
            "stability_index": float,
            "summary": str
        }

    Scoring rules:
    - Start with 100
    - Strong upward bias trend: -15
    - Strong upward logic contradictions: -20
    - Poor source agreement trends: -10
    - "critical" monitoring snapshot: -25
    - "warning" monitoring snapshot: -10
    - Score floor = 0
    """
    logger.info("Computing Veritas performance score")

    score = 100.0
    penalties = []

    # Check bias trends
    bias_trends = trends.get("bias_trends", {})
    bias_slopes = bias_trends.get("slopes", {})

    # Penalty for strong upward bias trends
    max_bias_slope = max(bias_slopes.values()) if bias_slopes else 0
    if max_bias_slope > 0.1:
        score -= 15
        penalties.append("Strong upward bias trend (-15)")
    elif max_bias_slope > 0.05:
        score -= 7
        penalties.append("Moderate upward bias trend (-7)")

    # Check logic issue trends
    logic_trends = trends.get("logic_trends", {})
    logic_slopes = logic_trends.get("slopes", {})

    # Penalty for upward contradiction trends
    contradiction_slope = logic_slopes.get("contradiction", 0)
    if contradiction_slope > 0.1:
        score -= 20
        penalties.append("Strong upward contradiction trend (-20)")
    elif contradiction_slope > 0.05:
        score -= 10
        penalties.append("Moderate upward contradiction trend (-10)")

    # Check fallacy trends
    fallacy_slope = logic_slopes.get("fallacy", 0)
    if fallacy_slope > 0.1:
        score -= 10
        penalties.append("Upward fallacy trend (-10)")

    # Check source reliability trends
    source_trends = trends.get("source_trends", {})
    source_slopes = source_trends.get("slopes", {})

    support_slope = source_slopes.get("support_rate", 0)
    if support_slope < -0.05:
        score -= 10
        penalties.append("Declining source agreement (-10)")

    contradiction_rate_slope = source_slopes.get("contradiction_rate", 0)
    if contradiction_rate_slope > 0.05:
        score -= 5
        penalties.append("Increasing source contradictions (-5)")

    # Check monitoring status
    stability_index = 1.0
    if monitoring:
        status = monitoring.get("overall_status", "stable")
        if status == "critical":
            score -= 25
            penalties.append("Critical monitoring status (-25)")
            stability_index = 0.3
        elif status == "warning":
            score -= 10
            penalties.append("Warning monitoring status (-10)")
            stability_index = 0.6
        else:
            stability_index = 1.0

    # Floor at 0
    score = max(0, score)

    # Compute grades based on subsystem performance
    def compute_grade(subsystem_score: float) -> str:
        if subsystem_score >= 80:
            return "A"
        elif subsystem_score >= 60:
            return "B"
        elif subsystem_score >= 40:
            return "C"
        else:
            return "D"

    # Bias analysis grade
    bias_score = 100 - (max_bias_slope * 100) if max_bias_slope > 0 else 100
    bias_grade = compute_grade(max(0, min(100, bias_score)))

    # Logic analysis grade
    logic_score = 100 - (max(logic_slopes.values()) * 100 if logic_slopes else 0)
    logic_grade = compute_grade(max(0, min(100, logic_score)))

    # Source validation grade
    source_score = 100 + (support_slope * 100) - (contradiction_rate_slope * 50)
    source_grade = compute_grade(max(0, min(100, source_score)))

    # Monitoring stability grade
    stability_grade = compute_grade(stability_index * 100)

    # Generate summary
    if score >= 80:
        summary = "Veritas is performing excellently with stable analysis quality"
    elif score >= 60:
        summary = "Veritas is performing well with minor areas for attention"
    elif score >= 40:
        summary = "Veritas performance is moderate with several concerns requiring attention"
    else:
        summary = "Veritas performance requires immediate attention"

    if penalties:
        summary += f". Issues: {', '.join(penalties)}"

    return {
        "score": round(score, 1),
        "grades": {
            "bias_analysis": bias_grade,
            "logic_analysis": logic_grade,
            "source_validation": source_grade,
            "monitoring_stability": stability_grade,
        },
        "stability_index": round(stability_index, 2),
        "summary": summary,
        "penalties": penalties,
    }


class TrendEngine:
    """
    OOP interface for trend analysis operations.
    """

    def __init__(self):
        """Initialize the trend engine."""
        self._audits: Optional[List[Dict[str, Any]]] = None
        self._last_analysis: Optional[Dict[str, Any]] = None
        logger.info("TrendEngine initialized")

    def load_audits(self, force_reload: bool = False) -> List[Dict[str, Any]]:
        """Load audits (cached unless force_reload)."""
        if self._audits is None or force_reload:
            self._audits = load_all_audits()
        return self._audits

    def analyze_all(self, monitoring: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run full trend analysis and return combined results."""
        audits = self.load_audits()

        bias_trends = compute_bias_over_time(audits)
        logic_trends = compute_logic_issue_trends(audits)
        source_trends = compute_source_reliability_trends(audits)

        trends = {
            "bias_trends": bias_trends,
            "logic_trends": logic_trends,
            "source_trends": source_trends,
        }

        performance = compute_performance_score(trends, monitoring)

        self._last_analysis = {
            "trends": trends,
            "performance": performance,
            "audits_analyzed": len(audits),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return self._last_analysis

    def get_last_analysis(self) -> Optional[Dict[str, Any]]:
        """Get the most recent analysis."""
        return self._last_analysis


# Module-level instance
_engine_instance: Optional[TrendEngine] = None


def get_trend_engine() -> TrendEngine:
    """Get or create the global TrendEngine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = TrendEngine()
    return _engine_instance
