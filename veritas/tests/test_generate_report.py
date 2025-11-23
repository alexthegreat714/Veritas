"""
Tests for Veritas Phase 7 Generate Report Tool

Tests for tool_generate_report function and reporting module.
"""

import json
import os
import shutil
import tempfile
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.tools import tool_generate_report
from app.reporting import (
    generate_full_veritas_report,
    store_report,
    get_recent_reports,
    ReportingEngine,
    get_reporting_engine,
    _build_chart_data,
    _generate_summary,
    _generate_recommendations,
)
from app.schemas import VeritasReport


class TestGenerateFullReport:
    """Tests for generate_full_veritas_report function."""

    def test_report_has_correct_structure(self):
        """Test that report has all required keys."""
        with patch("app.trend_engine.load_all_audits", return_value=[]):
            report = generate_full_veritas_report()

        assert "meta" in report
        assert "trends" in report
        assert "monitoring" in report
        assert "performance" in report
        assert "chart_data" in report
        assert "summary" in report
        assert "recommendations" in report

    def test_meta_structure(self):
        """Test meta section structure."""
        with patch("app.trend_engine.load_all_audits", return_value=[]):
            report = generate_full_veritas_report()

        meta = report["meta"]
        assert meta["agent"] == "veritas"
        assert meta["version"] == "0.10.0"
        assert meta["phase"] == 10
        assert "generated_at" in meta
        assert "audits_analyzed" in meta

    def test_trends_structure(self):
        """Test trends section structure."""
        with patch("app.trend_engine.load_all_audits", return_value=[]):
            report = generate_full_veritas_report()

        trends = report["trends"]
        assert "bias_trends" in trends
        assert "logic_trends" in trends
        assert "source_trends" in trends
        assert "audits_analyzed" in trends

    def test_performance_structure(self):
        """Test performance section structure."""
        with patch("app.trend_engine.load_all_audits", return_value=[]):
            report = generate_full_veritas_report()

        performance = report["performance"]
        assert "score" in performance
        assert "grades" in performance
        assert "stability_index" in performance

    def test_chart_data_structure(self):
        """Test chart_data section structure."""
        with patch("app.trend_engine.load_all_audits", return_value=[]):
            report = generate_full_veritas_report()

        chart_data = report["chart_data"]
        assert "bias_over_time" in chart_data
        assert "logic_issues_over_time" in chart_data
        assert "source_rates" in chart_data

    def test_recommendations_is_list(self):
        """Test that recommendations is a list."""
        with patch("app.trend_engine.load_all_audits", return_value=[]):
            report = generate_full_veritas_report()

        assert isinstance(report["recommendations"], list)
        assert len(report["recommendations"]) > 0


class TestToolGenerateReport:
    """Tests for tool_generate_report function."""

    def test_tool_returns_report(self):
        """Test tool returns a valid report."""
        with patch("app.trend_engine.load_all_audits", return_value=[]):
            with patch("app.reporting.store_report", return_value={"stored": True}):
                result = tool_generate_report({})

        assert "meta" in result
        assert "trends" in result
        assert "performance" in result

    def test_tool_stores_report_by_default(self):
        """Test tool stores report by default."""
        with patch("app.trend_engine.load_all_audits", return_value=[]):
            with tempfile.TemporaryDirectory() as tmpdir:
                with patch("app.reporting.REPORTS_DIR", Path(tmpdir)):
                    result = tool_generate_report({})

        assert result.get("storage", {}).get("stored") == True
        assert "file_path" in result.get("storage", {})

    def test_tool_respects_store_false(self):
        """Test tool respects store=False payload."""
        with patch("app.trend_engine.load_all_audits", return_value=[]):
            result = tool_generate_report({"store": False})

        assert result["storage"]["stored"] == False
        assert "reason" in result["storage"]


class TestStoreReport:
    """Tests for store_report function."""

    def test_store_creates_file(self):
        """Test that store_report creates a file."""
        test_report = {
            "meta": {"agent": "veritas", "generated_at": datetime.now(timezone.utc).isoformat()},
            "performance": {"score": 100},
        }

        # Create temp directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.reporting.REPORTS_DIR", Path(tmpdir)):
                result = store_report(test_report)

                assert result["stored"] == True
                assert "file_path" in result
                assert "report_id" in result
                assert os.path.exists(result["file_path"])

    def test_stored_file_contains_report(self):
        """Test that stored file contains valid JSON report."""
        test_report = {
            "meta": {"agent": "veritas", "generated_at": datetime.now(timezone.utc).isoformat()},
            "performance": {"score": 85},
            "summary": "Test summary",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.reporting.REPORTS_DIR", Path(tmpdir)):
                result = store_report(test_report)

                # Read back the stored file
                with open(result["file_path"], "r") as f:
                    loaded = json.load(f)

                assert loaded["meta"]["agent"] == "veritas"
                assert loaded["performance"]["score"] == 85
                assert loaded["summary"] == "Test summary"

    def test_report_id_format(self):
        """Test report_id has correct format."""
        test_report = {"meta": {}, "performance": {}}

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.reporting.REPORTS_DIR", Path(tmpdir)):
                result = store_report(test_report)

                assert result["report_id"].startswith("report_")


class TestGetRecentReports:
    """Tests for get_recent_reports function."""

    def test_returns_empty_list_when_no_reports(self):
        """Test returns empty list when no reports exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.reporting.REPORTS_DIR", Path(tmpdir)):
                reports = get_recent_reports()
                assert reports == []

    def test_returns_stored_reports(self):
        """Test returns stored reports."""
        test_reports = [
            {"meta": {"agent": "veritas"}, "performance": {"score": 90}},
            {"meta": {"agent": "veritas"}, "performance": {"score": 85}},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            reports_dir = Path(tmpdir)
            # Manually create report files with different names to avoid timestamp collision
            for i, report in enumerate(test_reports):
                file_path = reports_dir / f"report_2024-01-01_00-00-0{i}.json"
                with open(file_path, "w") as f:
                    json.dump(report, f)

            with patch("app.reporting.REPORTS_DIR", reports_dir):
                # Get recent reports
                loaded = get_recent_reports(limit=10)

                assert len(loaded) == 2

    def test_respects_limit(self):
        """Test respects limit parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reports_dir = Path(tmpdir)
            # Manually create report files with different names to avoid timestamp collision
            for i in range(5):
                file_path = reports_dir / f"report_2024-01-01_00-00-0{i}.json"
                with open(file_path, "w") as f:
                    json.dump({"meta": {}, "performance": {"score": i * 10}}, f)

            with patch("app.reporting.REPORTS_DIR", reports_dir):
                # Get only 2 recent
                loaded = get_recent_reports(limit=2)

                assert len(loaded) == 2


class TestBuildChartData:
    """Tests for _build_chart_data helper function."""

    def test_empty_trends(self):
        """Test with empty trend data."""
        chart_data = _build_chart_data(
            {"bias_types": {}, "slopes": {}},
            {"issue_types": {}, "slopes": {}},
            {"support_rate": [], "contradiction_rate": [], "missing_context_rate": [], "slopes": {}},
        )

        assert "bias_over_time" in chart_data
        assert "logic_issues_over_time" in chart_data
        assert "source_rates" in chart_data

    def test_with_bias_data(self):
        """Test with bias trend data."""
        bias_trends = {
            "bias_types": {
                "emotional_language": [
                    {"week": "2024-W01", "count": 5},
                    {"week": "2024-W02", "count": 7},
                ]
            },
            "slopes": {"emotional_language": 0.05},
        }

        chart_data = _build_chart_data(
            bias_trends,
            {"issue_types": {}, "slopes": {}},
            {"support_rate": [], "contradiction_rate": [], "missing_context_rate": [], "slopes": {}},
        )

        assert "emotional_language" in chart_data["bias_over_time"]
        assert chart_data["bias_over_time"]["emotional_language"]["weeks"] == ["2024-W01", "2024-W02"]
        assert chart_data["bias_over_time"]["emotional_language"]["counts"] == [5, 7]
        assert chart_data["bias_over_time"]["emotional_language"]["slope"] == 0.05


class TestGenerateSummary:
    """Tests for _generate_summary helper function."""

    def test_excellent_score_summary(self):
        """Test summary for excellent score."""
        summary = _generate_summary(
            {"score": 95},
            {"overall_status": "stable"},
            {"logic_trends": {}, "bias_trends": {}},
        )

        assert "excellent" in summary.lower()

    def test_good_score_summary(self):
        """Test summary for good score."""
        summary = _generate_summary(
            {"score": 75},
            {"overall_status": "stable"},
            {"logic_trends": {}, "bias_trends": {}},
        )

        assert "good" in summary.lower()

    def test_moderate_score_summary(self):
        """Test summary for moderate score."""
        summary = _generate_summary(
            {"score": 50},
            {"overall_status": "stable"},
            {"logic_trends": {}, "bias_trends": {}},
        )

        assert "moderate" in summary.lower()

    def test_low_score_summary(self):
        """Test summary for low score."""
        summary = _generate_summary(
            {"score": 30},
            {"overall_status": "stable"},
            {"logic_trends": {}, "bias_trends": {}},
        )

        assert "attention" in summary.lower()

    def test_critical_monitoring_included(self):
        """Test critical monitoring status is included in summary."""
        summary = _generate_summary(
            {"score": 95},
            {"overall_status": "critical"},
            {"logic_trends": {}, "bias_trends": {}},
        )

        assert "critical" in summary.lower()


class TestGenerateRecommendations:
    """Tests for _generate_recommendations helper function."""

    def test_no_issues_returns_status_ok(self):
        """Test recommendations when no issues."""
        recommendations = _generate_recommendations(
            {"score": 100, "grades": {"bias_analysis": "A", "logic_analysis": "A", "source_validation": "A", "monitoring_stability": "A"}},
            {"logic_trends": {"slopes": {}}, "bias_trends": {"slopes": {}}},
            {"overall_status": "stable"},
        )

        assert any("normal parameters" in r.lower() for r in recommendations)

    def test_includes_advisory_note(self):
        """Test recommendations include advisory note."""
        recommendations = _generate_recommendations(
            {"score": 100, "grades": {}},
            {"logic_trends": {"slopes": {}}, "bias_trends": {"slopes": {}}},
            {"overall_status": "stable"},
        )

        assert any("advisory only" in r.lower() for r in recommendations)

    def test_critical_monitoring_recommendation(self):
        """Test recommendations for critical monitoring."""
        recommendations = _generate_recommendations(
            {"score": 50, "grades": {}},
            {"logic_trends": {"slopes": {}}, "bias_trends": {"slopes": {}}},
            {"overall_status": "critical"},
        )

        assert any("urgent" in r.lower() for r in recommendations)

    def test_bad_grades_recommendations(self):
        """Test recommendations for bad grades."""
        recommendations = _generate_recommendations(
            {"score": 40, "grades": {"bias_analysis": "D", "logic_analysis": "D", "source_validation": "D", "monitoring_stability": "D"}},
            {"logic_trends": {"slopes": {}}, "bias_trends": {"slopes": {}}},
            {"overall_status": "warning"},
        )

        # Should have multiple advisory recommendations
        advisories = [r for r in recommendations if "ADVISORY" in r]
        assert len(advisories) >= 3


class TestReportingEngine:
    """Tests for ReportingEngine class."""

    def test_initialization(self):
        """Test engine initializes correctly."""
        engine = ReportingEngine()
        assert engine._last_report is None

    def test_generate_report(self):
        """Test generate_report method."""
        engine = ReportingEngine()

        with patch("app.trend_engine.load_all_audits", return_value=[]):
            with tempfile.TemporaryDirectory() as tmpdir:
                with patch("app.reporting.REPORTS_DIR", Path(tmpdir)):
                    report = engine.generate_report()

        assert "meta" in report
        assert "storage" in report
        assert engine._last_report is not None

    def test_get_last_report_returns_none_initially(self):
        """Test get_last_report returns None before generating."""
        engine = ReportingEngine()
        assert engine.get_last_report() is None

    def test_get_score_returns_zero_initially(self):
        """Test get_score returns 0 before generating."""
        engine = ReportingEngine()
        assert engine.get_score() == 0.0

    def test_get_score_after_generate(self):
        """Test get_score returns correct value after generating."""
        engine = ReportingEngine()

        with patch("app.trend_engine.load_all_audits", return_value=[]):
            with tempfile.TemporaryDirectory() as tmpdir:
                with patch("app.reporting.REPORTS_DIR", Path(tmpdir)):
                    engine.generate_report()

        assert engine.get_score() == 100.0  # No audits = perfect score


class TestGetReportingEngine:
    """Tests for get_reporting_engine singleton."""

    def test_returns_same_instance(self):
        """Test singleton returns same instance."""
        # Reset singleton for test
        import app.reporting
        app.reporting._engine_instance = None

        engine1 = get_reporting_engine()
        engine2 = get_reporting_engine()

        assert engine1 is engine2


class TestVeritasReportSchema:
    """Tests for VeritasReport schema validation."""

    def test_valid_report_passes_validation(self):
        """Test that a valid report passes schema validation."""
        report_data = {
            "meta": {"agent": "veritas", "version": "0.10.0"},
            "trends": {"bias_trends": {}, "logic_trends": {}},
            "monitoring": {"overall_status": "stable"},
            "performance": {"score": 100, "grades": {}},
            "chart_data": {},
            "summary": "Test summary",
            "recommendations": ["Recommendation 1"],
        }

        # Should not raise
        report = VeritasReport(**report_data)
        assert report.meta["agent"] == "veritas"
        assert report.summary == "Test summary"

    def test_schema_requires_all_fields(self):
        """Test that schema requires all fields."""
        with pytest.raises(Exception):  # ValidationError
            VeritasReport(meta={}, trends={})  # Missing required fields

    def test_generated_report_matches_schema(self):
        """Test that generated report matches schema."""
        with patch("app.trend_engine.load_all_audits", return_value=[]):
            report_dict = generate_full_veritas_report()

        # Should not raise
        report = VeritasReport(**report_dict)
        assert report.meta["agent"] == "veritas"
