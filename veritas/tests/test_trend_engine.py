"""
Tests for Veritas Phase 7 Trend Engine

Tests for long-term trend analysis: bias trends, logic issue trends, source reliability.
"""

import pytest
from datetime import datetime, timezone, timedelta

from app.trend_engine import (
    load_all_audits,
    compute_bias_over_time,
    compute_logic_issue_trends,
    compute_source_reliability_trends,
    _get_iso_week,
    _compute_linear_slope,
    _extract_bias_flags,
    _extract_logic_issues,
    _extract_source_validation,
    get_trend_engine,
    TrendEngine,
)


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_iso_week_valid_timestamp(self):
        """Test ISO week extraction from valid timestamp."""
        # Known date: 2024-01-15 is week 3
        week = _get_iso_week("2024-01-15T12:00:00+00:00")
        assert week == "2024-W03"

    def test_get_iso_week_date_only(self):
        """Test ISO week extraction from date only."""
        week = _get_iso_week("2024-01-15")
        assert week == "2024-W03"

    def test_get_iso_week_invalid(self):
        """Test ISO week extraction from invalid timestamp."""
        week = _get_iso_week("invalid")
        assert week == "unknown"

    def test_compute_linear_slope_increasing(self):
        """Test slope computation for increasing values."""
        values = [1, 2, 3, 4, 5]
        slope = _compute_linear_slope(values)
        assert slope == 1.0

    def test_compute_linear_slope_decreasing(self):
        """Test slope computation for decreasing values."""
        values = [5, 4, 3, 2, 1]
        slope = _compute_linear_slope(values)
        assert slope == -1.0

    def test_compute_linear_slope_flat(self):
        """Test slope computation for flat values."""
        values = [3, 3, 3, 3]
        slope = _compute_linear_slope(values)
        assert slope == 0.0

    def test_compute_linear_slope_empty(self):
        """Test slope computation for empty list."""
        slope = _compute_linear_slope([])
        assert slope == 0.0

    def test_compute_linear_slope_single(self):
        """Test slope computation for single value."""
        slope = _compute_linear_slope([5])
        assert slope == 0.0


class TestExtractBiasFlags:
    """Tests for bias flag extraction."""

    def test_extract_from_structured_format(self):
        """Test extraction from structured bias_flags."""
        audit = {
            "audit": {
                "audit": {
                    "bias_flags": [
                        {"type": "emotional_language"},
                        {"type": "loaded_framing"},
                    ]
                }
            }
        }
        flags = _extract_bias_flags(audit)
        assert "emotional_language" in flags
        assert "loaded_framing" in flags

    def test_extract_from_raw_bias(self):
        """Test extraction from raw bias scores."""
        audit = {
            "bias": {
                "emotional_bias": 0.5,
                "political_bias": 0.4,
                "certainty_overconfidence": 0.1,
            }
        }
        flags = _extract_bias_flags(audit)
        assert "emotional_language" in flags
        assert "political_bias" in flags
        assert "certainty_overconfidence" not in flags  # Below threshold

    def test_extract_empty_audit(self):
        """Test extraction from empty audit."""
        flags = _extract_bias_flags({})
        assert flags == []


class TestExtractLogicIssues:
    """Tests for logic issue extraction."""

    def test_extract_from_structured_format(self):
        """Test extraction from structured logical_issues."""
        audit = {
            "audit": {
                "audit": {
                    "logical_issues": [
                        {"type": "contradiction"},
                        {"type": "non_sequitur"},
                    ]
                }
            }
        }
        issues = _extract_logic_issues(audit)
        assert "contradiction" in issues
        assert "non_sequitur" in issues

    def test_extract_from_raw_format(self):
        """Test extraction from raw format."""
        audit = {
            "logical_fallacies": [{"type": "ad_hominem"}],
            "inconsistencies": ["inc1"],
            "unsupported_jumps": ["jump1"],
        }
        issues = _extract_logic_issues(audit)
        assert "ad_hominem" in issues
        assert "inconsistency" in issues
        assert "unsupported_conclusion" in issues

    def test_extract_empty_audit(self):
        """Test extraction from empty audit."""
        issues = _extract_logic_issues({})
        assert issues == []


class TestExtractSourceValidation:
    """Tests for source validation extraction."""

    def test_extract_source_stats(self):
        """Test extraction of source validation stats."""
        audit = {
            "audit": {
                "source_validation": [
                    {"claim": "c1", "supporting": ["s1"], "contradicting": [], "missing_context": False},
                    {"claim": "c2", "supporting": [], "contradicting": ["c1"], "missing_context": True},
                ]
            }
        }
        stats = _extract_source_validation(audit)
        assert stats["total_claims"] == 2
        assert stats["supporting"] == 1
        assert stats["contradicting"] == 1
        assert stats["missing_context"] == 1

    def test_extract_empty_audit(self):
        """Test extraction from empty audit."""
        stats = _extract_source_validation({})
        assert stats["total_claims"] == 0


class TestComputeBiasOverTime:
    """Tests for compute_bias_over_time function."""

    def test_empty_audits(self):
        """Test with empty audits list."""
        result = compute_bias_over_time([])
        assert result["bias_types"] == {}
        assert result["slopes"] == {}
        assert "message" in result

    def test_with_audits(self):
        """Test with audit data."""
        audits = [
            {
                "timestamp": "2024-01-08T12:00:00+00:00",
                "bias": {"emotional_bias": 0.5},
            },
            {
                "timestamp": "2024-01-15T12:00:00+00:00",
                "bias": {"emotional_bias": 0.6},
            },
        ]
        result = compute_bias_over_time(audits)
        assert "bias_types" in result
        assert "slopes" in result
        assert "top_increasing" in result
        assert "top_decreasing" in result

    def test_result_structure(self):
        """Test result structure."""
        audits = [
            {
                "timestamp": "2024-01-08T12:00:00+00:00",
                "bias": {"emotional_bias": 0.5},
            },
        ]
        result = compute_bias_over_time(audits)
        assert isinstance(result["bias_types"], dict)
        assert isinstance(result["slopes"], dict)
        assert isinstance(result["top_increasing"], list)
        assert isinstance(result["top_decreasing"], list)


class TestComputeLogicIssueTrends:
    """Tests for compute_logic_issue_trends function."""

    def test_empty_audits(self):
        """Test with empty audits list."""
        result = compute_logic_issue_trends([])
        assert result["issue_types"] == {}
        assert result["slopes"] == {}
        assert "message" in result

    def test_with_audits(self):
        """Test with audit data."""
        audits = [
            {
                "timestamp": "2024-01-08T12:00:00+00:00",
                "logical_fallacies": [{"type": "ad_hominem"}],
                "inconsistencies": [],
                "unsupported_jumps": [],
            },
            {
                "timestamp": "2024-01-15T12:00:00+00:00",
                "logical_fallacies": [{"type": "ad_hominem"}, {"type": "strawman"}],
                "inconsistencies": ["inc1"],
                "unsupported_jumps": [],
            },
        ]
        result = compute_logic_issue_trends(audits)
        assert "issue_types" in result
        assert "slopes" in result
        assert "notable_trends" in result

    def test_notable_trends_generated(self):
        """Test that notable trends are generated for significant slopes."""
        audits = [
            {
                "timestamp": "2024-01-08T12:00:00+00:00",
                "logical_fallacies": [],
                "inconsistencies": [],
                "unsupported_jumps": [],
            },
            {
                "timestamp": "2024-01-15T12:00:00+00:00",
                "logical_fallacies": [{"type": "contradiction"}, {"type": "contradiction"}],
                "inconsistencies": [],
                "unsupported_jumps": [],
            },
        ]
        result = compute_logic_issue_trends(audits)
        assert isinstance(result["notable_trends"], list)


class TestComputeSourceReliabilityTrends:
    """Tests for compute_source_reliability_trends function."""

    def test_empty_audits(self):
        """Test with empty audits list."""
        result = compute_source_reliability_trends([])
        assert result["support_rate"] == []
        assert result["contradiction_rate"] == []
        assert result["missing_context_rate"] == []

    def test_with_audits(self):
        """Test with audit data."""
        audits = [
            {
                "timestamp": "2024-01-08T12:00:00+00:00",
                "audit": {
                    "source_validation": [
                        {"claim": "c1", "supporting": ["s1"], "contradicting": [], "missing_context": False},
                    ]
                },
            },
            {
                "timestamp": "2024-01-15T12:00:00+00:00",
                "audit": {
                    "source_validation": [
                        {"claim": "c1", "supporting": [], "contradicting": ["c1"], "missing_context": True},
                    ]
                },
            },
        ]
        result = compute_source_reliability_trends(audits)
        assert "support_rate" in result
        assert "contradiction_rate" in result
        assert "missing_context_rate" in result
        assert "slopes" in result
        assert "summary" in result

    def test_summary_generated(self):
        """Test that summary is generated."""
        audits = [
            {"timestamp": "2024-01-08T12:00:00+00:00", "audit": {"source_validation": []}},
        ]
        result = compute_source_reliability_trends(audits)
        assert isinstance(result["summary"], str)


class TestTrendEngine:
    """Tests for TrendEngine class."""

    def test_initialization(self):
        """Test engine initialization."""
        engine = TrendEngine()
        assert engine._audits is None
        assert engine._last_analysis is None

    def test_load_audits(self):
        """Test loading audits."""
        engine = TrendEngine()
        audits = engine.load_audits()
        assert isinstance(audits, list)

    def test_analyze_all(self):
        """Test full analysis."""
        engine = TrendEngine()
        result = engine.analyze_all()
        assert "trends" in result
        assert "performance" in result
        assert "audits_analyzed" in result
        assert "timestamp" in result

    def test_get_last_analysis(self):
        """Test getting last analysis."""
        engine = TrendEngine()
        assert engine.get_last_analysis() is None

        engine.analyze_all()
        assert engine.get_last_analysis() is not None


class TestGetTrendEngine:
    """Tests for get_trend_engine function."""

    def test_returns_engine(self):
        """Test that function returns an engine."""
        engine = get_trend_engine()
        assert engine is not None
        assert isinstance(engine, TrendEngine)

    def test_returns_singleton(self):
        """Test that function returns same instance."""
        engine1 = get_trend_engine()
        engine2 = get_trend_engine()
        assert engine1 is engine2
