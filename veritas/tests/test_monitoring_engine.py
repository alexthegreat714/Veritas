"""
Tests for Veritas Phase 6 Monitoring Engine

Tests for drift detection, bias trends, and anomaly detection.
"""

import pytest
from datetime import datetime, timezone

from app.monitoring_engine import (
    detect_logical_drift,
    analyze_bias_trends,
    detect_anomalies,
    run_monitoring_cycle,
    get_monitoring_engine,
    MonitoringEngine,
    _extract_issue_counts,
    _extract_bias_scores,
    _compute_mean_std,
)


class TestExtractIssueCounts:
    """Tests for _extract_issue_counts helper."""

    def test_extract_from_raw_audit(self):
        """Test extraction from raw audit format."""
        audit = {
            "logical_fallacies": ["fallacy1", "fallacy2"],
            "inconsistencies": ["inc1"],
            "unsupported_jumps": ["jump1", "jump2", "jump3"],
        }

        counts = _extract_issue_counts(audit)

        assert counts["logical_fallacies"] == 2
        assert counts["inconsistencies"] == 1
        assert counts["unsupported_jumps"] == 3

    def test_extract_from_structured_audit(self):
        """Test extraction from structured audit format."""
        audit = {
            "audit": {
                "audit": {
                    "logical_issues": [
                        {"type": "fallacy", "description": "test"},
                        {"type": "contradiction", "description": "test"},
                        {"type": "non_sequitur", "description": "test"},
                    ]
                }
            }
        }

        counts = _extract_issue_counts(audit)

        assert counts["logical_fallacies"] == 1
        assert counts["contradictions"] == 1
        assert counts["unsupported_jumps"] == 1

    def test_extract_empty_audit(self):
        """Test extraction from empty audit."""
        counts = _extract_issue_counts({})

        assert counts["logical_fallacies"] == 0
        assert counts["inconsistencies"] == 0
        assert counts["unsupported_jumps"] == 0
        assert counts["contradictions"] == 0


class TestExtractBiasScores:
    """Tests for _extract_bias_scores helper."""

    def test_extract_from_bias_flags(self):
        """Test extraction from structured bias flags."""
        audit = {
            "audit": {
                "audit": {
                    "bias_flags": [
                        {"type": "emotional_language", "snippet": "test"},
                        {"type": "loaded_framing", "snippet": "test"},
                    ]
                }
            }
        }

        scores = _extract_bias_scores(audit)

        assert scores["emotional_language"] == 0.5
        assert scores["loaded_framing"] == 0.5

    def test_extract_from_raw_bias(self):
        """Test extraction from raw bias format."""
        audit = {
            "bias": {
                "emotional_bias": 0.7,
                "political_bias": 0.4,
                "certainty_overconfidence": 0.3,
            }
        }

        scores = _extract_bias_scores(audit)

        assert scores["emotional_language"] == 0.7
        assert scores["political_bias"] == 0.4
        assert scores["certainty_overconfidence"] == 0.3

    def test_extract_empty_audit(self):
        """Test extraction from empty audit."""
        scores = _extract_bias_scores({})

        assert scores["emotional_language"] == 0.0
        assert scores["political_bias"] == 0.0
        assert scores["certainty_overconfidence"] == 0.0
        assert scores["loaded_framing"] == 0.0


class TestComputeMeanStd:
    """Tests for _compute_mean_std helper."""

    def test_mean_std_normal(self):
        """Test mean and std for normal data."""
        values = [1, 2, 3, 4, 5]
        mean, std = _compute_mean_std(values)

        assert mean == 3.0
        assert abs(std - 1.58) < 0.1  # Approx sqrt(2.5)

    def test_mean_std_empty(self):
        """Test mean and std for empty data."""
        mean, std = _compute_mean_std([])

        assert mean == 0.0
        assert std == 0.0

    def test_mean_std_single(self):
        """Test mean and std for single value."""
        mean, std = _compute_mean_std([5])

        assert mean == 5.0
        assert std == 0.0


class TestDetectLogicalDrift:
    """Tests for detect_logical_drift function."""

    def test_insufficient_data(self):
        """Test with insufficient data."""
        result = detect_logical_drift([])

        assert result["drift_score"] == 0.0
        assert result["is_concerning"] is False
        assert "message" in result

    def test_single_audit(self):
        """Test with single audit."""
        result = detect_logical_drift([{"logical_fallacies": ["test"]}])

        assert result["drift_score"] == 0.0
        assert result["is_concerning"] is False

    def test_stable_audits(self):
        """Test with stable audit series."""
        audits = [
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
        ]

        result = detect_logical_drift(audits)

        assert result["drift_score"] <= 0.1
        assert result["is_concerning"] is False

    def test_increasing_issues_detected(self):
        """Test drift detection with increasing issues."""
        audits = [
            {"logical_fallacies": [], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1", "f2"], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1", "f2", "f3"], "inconsistencies": [], "unsupported_jumps": []},
        ]

        result = detect_logical_drift(audits)

        assert result["drift_score"] > 0.0
        assert len(result["increasing_issue_types"]) > 0

    def test_concerning_drift(self):
        """Test concerning drift threshold."""
        audits = [
            {"logical_fallacies": [], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": [], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1", "f2", "f3"], "inconsistencies": ["i1", "i2"], "unsupported_jumps": ["j1"]},
            {"logical_fallacies": ["f1", "f2", "f3", "f4"], "inconsistencies": ["i1", "i2", "i3"], "unsupported_jumps": ["j1", "j2"]},
        ]

        result = detect_logical_drift(audits)

        assert result["is_concerning"] is True
        assert len(result["possible_causes"]) > 0


class TestAnalyzeBiasTrends:
    """Tests for analyze_bias_trends function."""

    def test_insufficient_data(self):
        """Test with insufficient data."""
        result = analyze_bias_trends([])

        assert result["bias_trend_score"] == 0.0
        assert result["is_concerning"] is False
        assert "summary" in result

    def test_stable_bias(self):
        """Test with stable bias levels."""
        audits = [
            {"bias": {"emotional_bias": 0.1, "political_bias": 0.1}},
            {"bias": {"emotional_bias": 0.1, "political_bias": 0.1}},
            {"bias": {"emotional_bias": 0.1, "political_bias": 0.1}},
            {"bias": {"emotional_bias": 0.1, "political_bias": 0.1}},
        ]

        result = analyze_bias_trends(audits)

        assert result["bias_trend_score"] <= 0.1
        assert result["is_concerning"] is False

    def test_increasing_bias_detected(self):
        """Test bias trend detection with increasing bias."""
        audits = [
            {"bias": {"emotional_bias": 0.1}},
            {"bias": {"emotional_bias": 0.15}},
            {"bias": {"emotional_bias": 0.3}},
            {"bias": {"emotional_bias": 0.5}},
        ]

        result = analyze_bias_trends(audits)

        assert result["bias_trend_score"] > 0.0
        assert len(result["bias_types_increasing"]) > 0

    def test_summary_generation(self):
        """Test summary generation."""
        audits = [
            {"bias": {"emotional_bias": 0.1, "political_bias": 0.1}},
            {"bias": {"emotional_bias": 0.1, "political_bias": 0.1}},
            {"bias": {"emotional_bias": 0.5, "political_bias": 0.5}},
            {"bias": {"emotional_bias": 0.7, "political_bias": 0.7}},
        ]

        result = analyze_bias_trends(audits)

        assert "summary" in result
        assert len(result["summary"]) > 0


class TestDetectAnomalies:
    """Tests for detect_anomalies function."""

    def test_insufficient_data(self):
        """Test with insufficient data."""
        result = detect_anomalies([])

        assert result["anomaly_detected"] is False
        assert "message" in result

    def test_no_anomalies(self):
        """Test with normal data."""
        audits = [
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1", "f2"], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
        ]

        result = detect_anomalies(audits)

        assert result["anomaly_detected"] is False
        assert "statistics" in result

    def test_high_anomaly_detected(self):
        """Test detection of high anomaly."""
        # Create data with consistent low values and one extreme outlier at the end
        # With more consistent data points (1 issue each), the std will be low enough
        # that the outlier (16 issues) exceeds 2 standard deviations
        audits = [
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10"], "inconsistencies": ["i1", "i2", "i3"], "unsupported_jumps": ["j1", "j2", "j3"]},
        ]

        result = detect_anomalies(audits)

        assert result["anomaly_detected"] is True
        assert result["anomaly_reason"] is not None
        assert "high" in result["anomaly_reason"].lower()

    def test_statistics_returned(self):
        """Test that statistics are returned."""
        audits = [
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1", "f2"], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1"], "inconsistencies": ["i1"], "unsupported_jumps": []},
        ]

        result = detect_anomalies(audits)

        assert "statistics" in result
        assert "mean_issues" in result["statistics"]
        assert "std_issues" in result["statistics"]
        assert "sample_size" in result["statistics"]


class TestRunMonitoringCycle:
    """Tests for run_monitoring_cycle function."""

    def test_empty_audits(self):
        """Test monitoring cycle with empty audits."""
        result = run_monitoring_cycle([])

        assert result["overall_status"] == "stable"
        assert result["audits_analyzed"] == 0
        assert "timestamp" in result

    def test_stable_status(self):
        """Test stable overall status."""
        audits = [
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": [], "bias": {"emotional_bias": 0.1}},
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": [], "bias": {"emotional_bias": 0.1}},
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": [], "bias": {"emotional_bias": 0.1}},
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": [], "bias": {"emotional_bias": 0.1}},
        ]

        result = run_monitoring_cycle(audits)

        assert result["overall_status"] == "stable"
        assert "logical_drift" in result
        assert "bias_trends" in result
        assert "anomalies" in result

    def test_warning_status(self):
        """Test warning status when one area is concerning."""
        # Create audits with increasing issues (drift concern)
        audits = [
            {"logical_fallacies": [], "inconsistencies": [], "unsupported_jumps": [], "bias": {"emotional_bias": 0.1}},
            {"logical_fallacies": [], "inconsistencies": [], "unsupported_jumps": [], "bias": {"emotional_bias": 0.1}},
            {"logical_fallacies": ["f1", "f2", "f3"], "inconsistencies": ["i1", "i2"], "unsupported_jumps": ["j1"], "bias": {"emotional_bias": 0.1}},
            {"logical_fallacies": ["f1", "f2", "f3", "f4"], "inconsistencies": ["i1", "i2", "i3"], "unsupported_jumps": ["j1", "j2"], "bias": {"emotional_bias": 0.1}},
        ]

        result = run_monitoring_cycle(audits)

        # Either warning or critical depending on exact scores
        assert result["overall_status"] in ["warning", "critical"]

    def test_result_structure(self):
        """Test that result has correct structure."""
        audits = [
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
        ]

        result = run_monitoring_cycle(audits)

        assert "logical_drift" in result
        assert "bias_trends" in result
        assert "anomalies" in result
        assert "overall_status" in result
        assert "timestamp" in result
        assert "audits_analyzed" in result

        # Check nested structure
        assert "drift_score" in result["logical_drift"]
        assert "bias_trend_score" in result["bias_trends"]
        assert "anomaly_detected" in result["anomalies"]


class TestMonitoringEngine:
    """Tests for MonitoringEngine class."""

    def test_initialization(self):
        """Test engine initialization."""
        engine = MonitoringEngine(window_size=5)

        assert engine.window_size == 5
        assert engine._last_snapshot is None

    def test_run_cycle(self):
        """Test running a monitoring cycle."""
        engine = MonitoringEngine()

        audits = [
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []},
        ]

        result = engine.run_cycle(audits)

        assert result is not None
        assert engine._last_snapshot is not None
        assert engine._last_snapshot == result

    def test_get_last_snapshot(self):
        """Test getting last snapshot."""
        engine = MonitoringEngine()

        assert engine.get_last_snapshot() is None

        engine.run_cycle([{"logical_fallacies": ["f1"], "inconsistencies": [], "unsupported_jumps": []}])

        assert engine.get_last_snapshot() is not None

    def test_get_status(self):
        """Test getting status."""
        engine = MonitoringEngine()

        assert engine.get_status() == "unknown"

        engine.run_cycle([
            {"logical_fallacies": [], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": [], "inconsistencies": [], "unsupported_jumps": []},
        ])

        assert engine.get_status() in ["stable", "warning", "critical"]

    def test_is_concerning(self):
        """Test is_concerning check."""
        engine = MonitoringEngine()

        assert engine.is_concerning() is False  # Unknown status

        # Run with stable data
        engine.run_cycle([
            {"logical_fallacies": [], "inconsistencies": [], "unsupported_jumps": []},
            {"logical_fallacies": [], "inconsistencies": [], "unsupported_jumps": []},
        ])

        # Stable should not be concerning
        if engine.get_status() == "stable":
            assert engine.is_concerning() is False


class TestGetMonitoringEngine:
    """Tests for get_monitoring_engine function."""

    def test_returns_engine(self):
        """Test that function returns an engine."""
        engine = get_monitoring_engine()

        assert engine is not None
        assert isinstance(engine, MonitoringEngine)

    def test_returns_singleton(self):
        """Test that function returns same instance."""
        engine1 = get_monitoring_engine()
        engine2 = get_monitoring_engine()

        assert engine1 is engine2
