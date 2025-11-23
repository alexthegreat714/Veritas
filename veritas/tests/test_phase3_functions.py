"""
Tests for Veritas Phase 3 Convenience Functions

Tests for audit_with_sources() and validate_sources() functions
that provide the API expected by the Phase 3 spec.
"""

import pytest

from app.logic.brain import audit_with_sources, validate_sources


class TestAuditWithSources:
    """Tests for audit_with_sources convenience function."""

    def test_audit_with_sources_basic(self):
        """Test basic combined audit."""
        text = "This is a test statement that needs to be verified."
        sources = ["https://example.edu/research", "https://reuters.com/article"]

        result = audit_with_sources(text, sources)

        assert "text_audit" in result
        assert "bias_analysis" in result
        assert "source_validation" in result
        assert "combined_assessment" in result

    def test_audit_with_sources_text_only(self):
        """Test audit with text but no sources."""
        text = "Some claim that needs checking."
        sources = []

        result = audit_with_sources(text, sources)

        assert result["text_audit"] is not None
        assert result["source_validation"] is None

    def test_audit_with_sources_sources_only(self):
        """Test audit with sources but no text."""
        text = ""
        sources = ["https://nature.com/article", "https://bbc.com/news"]

        result = audit_with_sources(text, sources)

        assert result["text_audit"] is None
        assert result["source_validation"] is not None

    def test_audit_with_sources_without_bias(self):
        """Test audit without bias detection."""
        text = "Test text for analysis."
        sources = ["https://example.gov/data"]

        result = audit_with_sources(text, sources, include_bias=False)

        assert result["text_audit"] is not None
        assert result["bias_analysis"] is None

    def test_audit_with_sources_detects_issues(self):
        """Test that audit detects issues in problematic content."""
        text = """
        OBVIOUSLY everyone KNOWS this is absolutely TRUE!
        This HORRIBLE policy will DESTROY everything!
        """
        sources = ["http://sketchy-site.xyz/fake-news"]

        result = audit_with_sources(text, sources)

        assessment = result["combined_assessment"]
        assert "has_issues" in assessment
        assert "issue_types" in assessment
        assert "confidence" in assessment
        assert "recommendation" in assessment

    def test_audit_with_sources_combined_assessment_structure(self):
        """Test that combined_assessment has expected structure."""
        text = "A factual statement supported by evidence."
        sources = ["https://arxiv.org/abs/1234.5678"]

        result = audit_with_sources(text, sources)

        assessment = result["combined_assessment"]
        assert isinstance(assessment["has_issues"], bool)
        assert isinstance(assessment["issue_types"], list)
        assert 0.0 <= assessment["confidence"] <= 1.0
        assert isinstance(assessment["recommendation"], str)

    def test_audit_with_sources_credible_sources(self):
        """Test audit with highly credible sources."""
        text = "Research shows that this effect is measurable."
        sources = [
            "https://nature.com/articles/research",
            "https://pubmed.ncbi.nlm.nih.gov/12345",
            "https://arxiv.org/abs/2301.00001"
        ]

        result = audit_with_sources(text, sources)

        # High credibility sources should result in higher confidence
        assert result["source_validation"] is not None
        ranked = result["source_validation"].get("ranked_confidence", [])
        assert len(ranked) > 0
        # At least some sources should have confidence > 0.7
        high_cred = [r for r in ranked if r["confidence"] > 0.7]
        assert len(high_cred) > 0


class TestValidateSources:
    """Tests for validate_sources convenience function."""

    def test_validate_sources_basic(self):
        """Test basic source validation."""
        sources = [
            "https://example.edu/paper",
            "https://reuters.com/article"
        ]

        result = validate_sources(sources)

        assert "valid" in result
        assert "sources_checked" in result
        assert "verified_count" in result
        assert "unverified_count" in result
        assert "credibility_scores" in result

    def test_validate_sources_empty_list(self):
        """Test validation of empty source list."""
        result = validate_sources([])

        assert result["sources_checked"] == 0
        assert result["valid"] is False

    def test_validate_sources_high_credibility(self):
        """Test validation of high credibility sources."""
        sources = [
            "https://nature.com/research",
            "https://science.org/article",
            "https://pubmed.ncbi.nlm.nih.gov/123456"
        ]

        result = validate_sources(sources)

        assert result["sources_checked"] == 3
        assert result["valid"] is True
        assert result["verified_count"] > 0

    def test_validate_sources_low_credibility(self):
        """Test validation of low credibility sources."""
        sources = [
            "https://random-blog.blogspot.com/post",
            "https://twitter.com/user/status/123",
            "http://sketchy.xyz/fake"
        ]

        result = validate_sources(sources)

        assert result["sources_checked"] == 3
        # Low credibility sources should have fewer verified
        assert result["unverified_count"] >= result["verified_count"]

    def test_validate_sources_mixed_credibility(self):
        """Test validation of mixed credibility sources."""
        sources = [
            "https://arxiv.org/abs/1234.5678",  # High
            "https://medium.com/article",  # Medium
            "random text not a url"  # Invalid
        ]

        result = validate_sources(sources)

        assert result["sources_checked"] == 3
        assert len(result["unverified_sources"]) > 0

    def test_validate_sources_warnings(self):
        """Test that warnings are generated for issues."""
        sources = [
            "",  # Empty
            "https://example.com/valid",
            "not-a-valid-source"  # Invalid format
        ]

        result = validate_sources(sources)

        # Should have warnings about empty or invalid sources
        assert "warnings" in result

    def test_validate_sources_credibility_scores(self):
        """Test that credibility scores are provided."""
        sources = [
            "https://nature.com/article",
            "https://wikipedia.org/wiki/Topic"
        ]

        result = validate_sources(sources)

        assert len(result["credibility_scores"]) > 0
        for source, score in result["credibility_scores"].items():
            assert 0.0 <= score <= 1.0

    def test_validate_sources_with_claims(self):
        """Test validation with claims parameter."""
        sources = ["https://example.edu/research"]
        claims = ["The sky is blue."]

        result = validate_sources(sources, claims=claims)

        # Should still work with claims parameter
        assert result["sources_checked"] == 1


class TestIntegration:
    """Integration tests for Phase 3 convenience functions."""

    def test_audit_and_validate_consistency(self):
        """Test that audit_with_sources and validate_sources give consistent results."""
        sources = [
            "https://nature.com/research",
            "https://bbc.com/news"
        ]

        audit_result = audit_with_sources("Test text", sources)
        validate_result = validate_sources(sources)

        # Both should have source validation
        assert audit_result["source_validation"] is not None
        assert validate_result["sources_checked"] == len(sources)

    def test_full_audit_workflow(self):
        """Test complete audit workflow."""
        text = """
        According to recent research, climate change is accelerating.
        Multiple studies have confirmed this trend over the past decade.
        """
        sources = [
            "https://nature.com/climate-study",
            "https://science.org/ipcc-report",
            "https://arxiv.org/abs/2301.12345"
        ]

        # Run full audit
        result = audit_with_sources(text, sources, include_bias=True)

        # Verify all components present
        assert result["text_audit"] is not None
        assert result["bias_analysis"] is not None
        assert result["source_validation"] is not None
        assert result["combined_assessment"] is not None

        # Verify assessment quality
        assessment = result["combined_assessment"]
        assert isinstance(assessment["has_issues"], bool)
        assert isinstance(assessment["recommendation"], str)
        assert len(assessment["recommendation"]) > 0
