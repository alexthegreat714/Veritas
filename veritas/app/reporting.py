"""
Veritas Reporting Engine

Phase 7: Unified reporting for long-term trends, performance metrics, and governance-grade reports.

This module generates comprehensive reports suitable for Sky, Congress, and n8n consumption.

IMPORTANT: Veritas monitors only — never intervenes or takes autonomous actions.
All reports are informational and do not constitute decisions or recommendations for action.
"""

import json
import logging
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
        LOG_DIR / "reporting.log",
        maxBytes=5_000_000,
        backupCount=3
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)


# Paths
MEMORY_BASE = Path(__file__).parent / "memory" / "long_term"
REPORTS_DIR = MEMORY_BASE / "monitoring" / "reports"


def _ensure_reports_dir():
    """Ensure reports directory exists."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _load_recent_monitoring_snapshot() -> Optional[Dict[str, Any]]:
    """Load the most recent monitoring snapshot."""
    from app.memory_utils import get_recent_monitoring_snapshots

    snapshots = get_recent_monitoring_snapshots(limit=1)
    if snapshots:
        return snapshots[0]
    return None


def generate_full_veritas_report() -> Dict[str, Any]:
    """
    Generate a comprehensive Veritas report.

    Steps:
    1. Load all audits
    2. Compute long-term bias trends
    3. Compute long-term logic issue trends
    4. Compute source reliability trends
    5. Load recent monitoring snapshot
    6. Compute performance score
    7. Return a fully structured report

    Returns:
        {
            "meta": {...},
            "trends": {...},
            "monitoring": {...},
            "performance": {...},
            "chart_data": {...},
            "summary": str,
            "recommendations": [...]
        }
    """
    logger.info("Generating full Veritas report")

    from app.trend_engine import (
        load_all_audits,
        compute_bias_over_time,
        compute_logic_issue_trends,
        compute_source_reliability_trends,
        compute_performance_score,
    )

    # Step 1: Load all audits
    audits = load_all_audits()
    logger.info(f"Loaded {len(audits)} audits for report")

    # Step 2-4: Compute trends
    bias_trends = compute_bias_over_time(audits)
    logic_trends = compute_logic_issue_trends(audits)
    source_trends = compute_source_reliability_trends(audits)

    trends = {
        "bias_trends": bias_trends,
        "logic_trends": logic_trends,
        "source_trends": source_trends,
        "audits_analyzed": len(audits),
    }

    # Step 5: Load recent monitoring
    monitoring = _load_recent_monitoring_snapshot()
    if monitoring is None:
        monitoring = {
            "overall_status": "unknown",
            "message": "No recent monitoring snapshot available",
        }

    # Step 6: Compute performance score
    performance = compute_performance_score(trends, monitoring)

    # Build chart-ready data
    chart_data = _build_chart_data(bias_trends, logic_trends, source_trends)

    # Generate summary and recommendations
    summary = _generate_summary(performance, monitoring, trends)
    recommendations = _generate_recommendations(performance, trends, monitoring)

    # Build final report
    report = {
        "meta": {
            "agent": "veritas",
            "version": "0.10.0",
            "phase": 10,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "audits_analyzed": len(audits),
        },
        "trends": trends,
        "monitoring": monitoring,
        "performance": performance,
        "chart_data": chart_data,
        "summary": summary,
        "recommendations": recommendations,
    }

    logger.info(f"Report generated: score={performance.get('score')}")

    return report


def _build_chart_data(
    bias_trends: Dict[str, Any],
    logic_trends: Dict[str, Any],
    source_trends: Dict[str, Any]
) -> Dict[str, Any]:
    """Build chart-ready data arrays from trend data."""

    # Bias over time: consolidate into weekly totals
    bias_over_time = {}
    for bias_type, series in bias_trends.get("bias_types", {}).items():
        bias_over_time[bias_type] = {
            "weeks": [item["week"] for item in series],
            "counts": [item["count"] for item in series],
            "slope": bias_trends.get("slopes", {}).get(bias_type, 0),
        }

    # Logic issues over time
    logic_issues_over_time = {}
    for issue_type, series in logic_trends.get("issue_types", {}).items():
        logic_issues_over_time[issue_type] = {
            "weeks": [item["week"] for item in series],
            "counts": [item["count"] for item in series],
            "slope": logic_trends.get("slopes", {}).get(issue_type, 0),
        }

    # Source rates
    source_rates = {
        "support": {
            "weeks": [item["week"] for item in source_trends.get("support_rate", [])],
            "rates": [item["rate"] for item in source_trends.get("support_rate", [])],
            "slope": source_trends.get("slopes", {}).get("support_rate", 0),
        },
        "contradiction": {
            "weeks": [item["week"] for item in source_trends.get("contradiction_rate", [])],
            "rates": [item["rate"] for item in source_trends.get("contradiction_rate", [])],
            "slope": source_trends.get("slopes", {}).get("contradiction_rate", 0),
        },
        "missing_context": {
            "weeks": [item["week"] for item in source_trends.get("missing_context_rate", [])],
            "rates": [item["rate"] for item in source_trends.get("missing_context_rate", [])],
            "slope": source_trends.get("slopes", {}).get("missing_context_rate", 0),
        },
    }

    return {
        "bias_over_time": bias_over_time,
        "logic_issues_over_time": logic_issues_over_time,
        "source_rates": source_rates,
    }


def _generate_summary(
    performance: Dict[str, Any],
    monitoring: Dict[str, Any],
    trends: Dict[str, Any]
) -> str:
    """Generate a human-readable summary of the report."""
    parts = []

    # Performance summary
    score = performance.get("score", 0)
    if score >= 80:
        parts.append(f"Veritas health is excellent (score: {score}/100)")
    elif score >= 60:
        parts.append(f"Veritas health is good (score: {score}/100)")
    elif score >= 40:
        parts.append(f"Veritas health is moderate (score: {score}/100)")
    else:
        parts.append(f"Veritas health requires attention (score: {score}/100)")

    # Monitoring status
    status = monitoring.get("overall_status", "unknown")
    if status == "critical":
        parts.append("Recent monitoring shows critical issues")
    elif status == "warning":
        parts.append("Recent monitoring shows some concerns")
    elif status == "stable":
        parts.append("Recent monitoring shows stable operation")

    # Notable trends
    notable = trends.get("logic_trends", {}).get("notable_trends", [])
    if notable:
        parts.append(f"Notable logic trends: {'; '.join(notable[:3])}")

    bias_increasing = trends.get("bias_trends", {}).get("top_increasing", [])
    if bias_increasing:
        parts.append(f"Increasing bias types: {', '.join(bias_increasing[:3])}")

    return ". ".join(parts) + "."


def _generate_recommendations(
    performance: Dict[str, Any],
    trends: Dict[str, Any],
    monitoring: Dict[str, Any]
) -> List[str]:
    """Generate actionable recommendations based on analysis."""
    recommendations = []

    # Based on performance grades
    grades = performance.get("grades", {})

    if grades.get("bias_analysis") in ["C", "D"]:
        recommendations.append(
            "ADVISORY: Review bias detection patterns. Increasing bias trends detected."
        )

    if grades.get("logic_analysis") in ["C", "D"]:
        recommendations.append(
            "ADVISORY: Review logic auditing. Contradiction or fallacy trends increasing."
        )

    if grades.get("source_validation") in ["C", "D"]:
        recommendations.append(
            "ADVISORY: Review source validation. Source reliability declining."
        )

    if grades.get("monitoring_stability") in ["C", "D"]:
        recommendations.append(
            "ADVISORY: Immediate attention needed. Monitoring shows unstable patterns."
        )

    # Based on monitoring status
    status = monitoring.get("overall_status", "unknown")
    if status == "critical":
        recommendations.append(
            "URGENT: Multiple monitoring concerns detected. Manual review recommended."
        )
    elif status == "warning":
        recommendations.append(
            "ATTENTION: Monitoring shows warning signs. Consider investigation."
        )

    # Based on specific slopes
    logic_slopes = trends.get("logic_trends", {}).get("slopes", {})
    if logic_slopes.get("contradiction", 0) > 0.15:
        recommendations.append(
            "TREND: Contradiction rate increasing rapidly. May indicate systemic issues."
        )

    bias_slopes = trends.get("bias_trends", {}).get("slopes", {})
    max_bias_slope = max(bias_slopes.values()) if bias_slopes else 0
    if max_bias_slope > 0.15:
        recommendations.append(
            "TREND: Bias detection increasing rapidly. May indicate input quality issues."
        )

    # If everything is fine
    if not recommendations:
        recommendations.append(
            "STATUS: All systems operating within normal parameters. No immediate action required."
        )

    # Note that Veritas is advisory only
    recommendations.append(
        "NOTE: All recommendations are advisory only. Veritas does not take autonomous action."
    )

    return recommendations


def store_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Store a report to the reports folder.

    Args:
        report: The report to store.

    Returns:
        {
            "stored": bool,
            "file_path": str,
            "report_id": str
        }
    """
    _ensure_reports_dir()

    timestamp = datetime.now(timezone.utc)
    report_id = f"report_{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}"
    file_path = REPORTS_DIR / f"{report_id}.json"

    try:
        with open(file_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Report stored: {file_path}")

        return {
            "stored": True,
            "file_path": str(file_path),
            "report_id": report_id,
        }
    except Exception as e:
        logger.error(f"Failed to store report: {e}")
        return {
            "stored": False,
            "error": str(e),
            "report_id": report_id,
        }


def get_recent_reports(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent reports from storage.

    Args:
        limit: Maximum number of reports to return.

    Returns:
        List of report dictionaries, newest first.
    """
    _ensure_reports_dir()

    reports = []
    files = sorted(REPORTS_DIR.glob("*.json"), reverse=True)[:limit]

    for file_path in files:
        try:
            with open(file_path, "r") as f:
                report = json.load(f)
                report["_file_path"] = str(file_path)
                reports.append(report)
        except Exception as e:
            logger.error(f"Error loading report {file_path}: {e}")

    return reports


class ReportingEngine:
    """
    OOP interface for reporting operations.
    """

    def __init__(self):
        """Initialize the reporting engine."""
        self._last_report: Optional[Dict[str, Any]] = None
        logger.info("ReportingEngine initialized")

    def generate_report(self) -> Dict[str, Any]:
        """Generate and store a full report."""
        report = generate_full_veritas_report()
        storage_result = store_report(report)
        report["storage"] = storage_result
        self._last_report = report
        return report

    def get_last_report(self) -> Optional[Dict[str, Any]]:
        """Get the most recently generated report."""
        return self._last_report

    def get_score(self) -> float:
        """Get the performance score from the last report."""
        if self._last_report is None:
            return 0.0
        return self._last_report.get("performance", {}).get("score", 0.0)


# Module-level instance
_engine_instance: Optional[ReportingEngine] = None


def get_reporting_engine() -> ReportingEngine:
    """Get or create the global ReportingEngine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ReportingEngine()
    return _engine_instance
