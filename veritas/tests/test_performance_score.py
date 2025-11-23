"""
Tests for Veritas Phase 7 Performance Score

Tests for compute_performance_score function.
"""

import pytest

from app.trend_engine import compute_performance_score


class TestPerformanceScoreBasic:
    """Basic tests for performance score computation."""

    def test_perfect_score_with_no_issues(self):
        """Test that no issues results in perfect score."""
        trends = {
            "bias_trends": {"slopes": {}},
            "logic_trends": {"slopes": {}},
            "source_trends": {"slopes": {}},
        }
        result = compute_performance_score(trends)
        assert result["score"] == 100.0

    def test_score_has_correct_structure(self):
        """Test result structure."""
        trends = {
            "bias_trends": {"slopes": {}},
            "logic_trends": {"slopes": {}},
            "source_trends": {"slopes": {}},
        }
        result = compute_performance_score(trends)
        assert "score" in result
        assert "grades" in result
        assert "stability_index" in result
        assert "summary" in result
        assert "penalties" in result

    def test_grades_structure(self):
        """Test grades structure."""
        trends = {
            "bias_trends": {"slopes": {}},
            "logic_trends": {"slopes": {}},
            "source_trends": {"slopes": {}},
        }
        result = compute_performance_score(trends)
        grades = result["grades"]
        assert "bias_analysis" in grades
        assert "logic_analysis" in grades
        assert "source_validation" in grades
        assert "monitoring_stability" in grades


class TestPerformanceScorePenalties:
    """Tests for performance score penalties."""

    def test_strong_bias_trend_penalty(self):
        """Test strong upward bias trend penalty (-15)."""
        trends = {
            "bias_trends": {"slopes": {"emotional_language": 0.15}},
            "logic_trends": {"slopes": {}},
            "source_trends": {"slopes": {}},
        }
        result = compute_performance_score(trends)
        assert result["score"] == 85.0
        assert any("-15" in p for p in result["penalties"])

    def test_moderate_bias_trend_penalty(self):
        """Test moderate upward bias trend penalty (-7)."""
        trends = {
            "bias_trends": {"slopes": {"emotional_language": 0.07}},
            "logic_trends": {"slopes": {}},
            "source_trends": {"slopes": {}},
        }
        result = compute_performance_score(trends)
        assert result["score"] == 93.0
        assert any("-7" in p for p in result["penalties"])

    def test_strong_contradiction_trend_penalty(self):
        """Test strong contradiction trend penalty (-20)."""
        trends = {
            "bias_trends": {"slopes": {}},
            "logic_trends": {"slopes": {"contradiction": 0.15}},
            "source_trends": {"slopes": {}},
        }
        result = compute_performance_score(trends)
        assert result["score"] == 80.0
        assert any("-20" in p for p in result["penalties"])

    def test_moderate_contradiction_trend_penalty(self):
        """Test moderate contradiction trend penalty (-10)."""
        trends = {
            "bias_trends": {"slopes": {}},
            "logic_trends": {"slopes": {"contradiction": 0.07}},
            "source_trends": {"slopes": {}},
        }
        result = compute_performance_score(trends)
        assert result["score"] == 90.0
        assert any("-10" in p for p in result["penalties"])

    def test_fallacy_trend_penalty(self):
        """Test fallacy trend penalty (-10)."""
        trends = {
            "bias_trends": {"slopes": {}},
            "logic_trends": {"slopes": {"fallacy": 0.15}},
            "source_trends": {"slopes": {}},
        }
        result = compute_performance_score(trends)
        assert result["score"] == 90.0
        assert any("-10" in p for p in result["penalties"])

    def test_declining_source_agreement_penalty(self):
        """Test declining source agreement penalty (-10)."""
        trends = {
            "bias_trends": {"slopes": {}},
            "logic_trends": {"slopes": {}},
            "source_trends": {"slopes": {"support_rate": -0.1}},
        }
        result = compute_performance_score(trends)
        assert result["score"] == 90.0
        assert any("-10" in p for p in result["penalties"])

    def test_increasing_source_contradiction_penalty(self):
        """Test increasing source contradiction penalty (-5)."""
        trends = {
            "bias_trends": {"slopes": {}},
            "logic_trends": {"slopes": {}},
            "source_trends": {"slopes": {"contradiction_rate": 0.1}},
        }
        result = compute_performance_score(trends)
        assert result["score"] == 95.0
        assert any("-5" in p for p in result["penalties"])


class TestPerformanceScoreMonitoring:
    """Tests for monitoring status impact on score."""

    def test_critical_monitoring_penalty(self):
        """Test critical monitoring status penalty (-25)."""
        trends = {
            "bias_trends": {"slopes": {}},
            "logic_trends": {"slopes": {}},
            "source_trends": {"slopes": {}},
        }
        monitoring = {"overall_status": "critical"}
        result = compute_performance_score(trends, monitoring)
        assert result["score"] == 75.0
        assert result["stability_index"] == 0.3
        assert any("-25" in p for p in result["penalties"])

    def test_warning_monitoring_penalty(self):
        """Test warning monitoring status penalty (-10)."""
        trends = {
            "bias_trends": {"slopes": {}},
            "logic_trends": {"slopes": {}},
            "source_trends": {"slopes": {}},
        }
        monitoring = {"overall_status": "warning"}
        result = compute_performance_score(trends, monitoring)
        assert result["score"] == 90.0
        assert result["stability_index"] == 0.6
        assert any("-10" in p for p in result["penalties"])

    def test_stable_monitoring_no_penalty(self):
        """Test stable monitoring status has no penalty."""
        trends = {
            "bias_trends": {"slopes": {}},
            "logic_trends": {"slopes": {}},
            "source_trends": {"slopes": {}},
        }
        monitoring = {"overall_status": "stable"}
        result = compute_performance_score(trends, monitoring)
        assert result["score"] == 100.0
        assert result["stability_index"] == 1.0


class TestPerformanceScoreCombined:
    """Tests for combined penalties."""

    def test_multiple_penalties(self):
        """Test that multiple penalties are applied."""
        trends = {
            "bias_trends": {"slopes": {"emotional_language": 0.15}},  # -15
            "logic_trends": {"slopes": {"contradiction": 0.15}},  # -20
            "source_trends": {"slopes": {}},
        }
        result = compute_performance_score(trends)
        assert result["score"] == 65.0
        assert len(result["penalties"]) >= 2

    def test_score_floor_at_zero(self):
        """Test that score doesn't go below 0."""
        trends = {
            "bias_trends": {"slopes": {"emotional_language": 0.15}},  # -15
            "logic_trends": {"slopes": {"contradiction": 0.15, "fallacy": 0.15}},  # -20, -10
            "source_trends": {"slopes": {"support_rate": -0.1, "contradiction_rate": 0.1}},  # -10, -5
        }
        monitoring = {"overall_status": "critical"}  # -25
        result = compute_performance_score(trends, monitoring)
        assert result["score"] >= 0
        # Total penalties: 15+20+10+10+5+25 = 85, so score should be 15


class TestPerformanceScoreGrades:
    """Tests for grade computation."""

    def test_grade_a_for_excellent(self):
        """Test A grade for excellent scores."""
        trends = {
            "bias_trends": {"slopes": {}},
            "logic_trends": {"slopes": {}},
            "source_trends": {"slopes": {}},
        }
        result = compute_performance_score(trends)
        # With no issues, all grades should be A
        for grade in result["grades"].values():
            assert grade == "A"

    def test_valid_grade_values(self):
        """Test that grades are valid values."""
        trends = {
            "bias_trends": {"slopes": {"emotional_language": 0.5}},
            "logic_trends": {"slopes": {"contradiction": 0.5}},
            "source_trends": {"slopes": {}},
        }
        result = compute_performance_score(trends)
        for grade in result["grades"].values():
            assert grade in ["A", "B", "C", "D"]


class TestPerformanceScoreSummary:
    """Tests for summary generation."""

    def test_excellent_summary(self):
        """Test excellent summary for high scores."""
        trends = {
            "bias_trends": {"slopes": {}},
            "logic_trends": {"slopes": {}},
            "source_trends": {"slopes": {}},
        }
        result = compute_performance_score(trends)
        assert "excellent" in result["summary"].lower()

    def test_good_summary(self):
        """Test good summary for decent scores."""
        trends = {
            "bias_trends": {"slopes": {"emotional_language": 0.15}},  # -15
            "logic_trends": {"slopes": {}},
            "source_trends": {"slopes": {}},
        }
        monitoring = {"overall_status": "warning"}  # -10
        result = compute_performance_score(trends, monitoring)
        # Score: 75, should be "well" or "good"
        assert "well" in result["summary"].lower() or "good" in result["summary"].lower()

    def test_moderate_summary(self):
        """Test moderate summary for medium scores."""
        trends = {
            "bias_trends": {"slopes": {"emotional_language": 0.15}},  # -15
            "logic_trends": {"slopes": {"contradiction": 0.15}},  # -20
            "source_trends": {"slopes": {"support_rate": -0.1}},  # -10
        }
        monitoring = {"overall_status": "warning"}  # -10
        result = compute_performance_score(trends, monitoring)
        # Score: 45, should be "moderate"
        assert "moderate" in result["summary"].lower()

    def test_summary_includes_issues(self):
        """Test that summary includes issues when present."""
        trends = {
            "bias_trends": {"slopes": {"emotional_language": 0.15}},
            "logic_trends": {"slopes": {}},
            "source_trends": {"slopes": {}},
        }
        result = compute_performance_score(trends)
        assert "Issues:" in result["summary"]
