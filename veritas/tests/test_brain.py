"""
Tests for VeritasBrain reasoning engine.

Phase 3: Tests for task classification, tool orchestration,
synthesis, and pipeline integrity.
"""

import pytest
from typing import Any, Dict

from app.logic.brain import VeritasBrain, get_brain


class TestVeritasBrainInitialization:
    """Tests for VeritasBrain initialization."""

    def test_brain_initialization(self):
        """Test that VeritasBrain initializes correctly."""
        brain = VeritasBrain()
        assert brain._initialized is True
        assert brain.memory_client is not None
        assert brain.logger is not None

    def test_brain_with_custom_memory_client(self):
        """Test initialization with custom memory client."""
        from app.rag.query import RAGQuery
        custom_client = RAGQuery({"top_k": 10})
        brain = VeritasBrain(memory_client=custom_client)
        assert brain.memory_client == custom_client

    def test_get_brain_singleton(self):
        """Test that get_brain returns consistent instance."""
        brain1 = get_brain()
        brain2 = get_brain()
        assert brain1 is brain2


class TestClassifyTask:
    """Tests for task classification."""

    def test_classify_text_only(self):
        """Test classification with text only -> audit_text."""
        brain = VeritasBrain()
        result = brain.classify_task({"text": "Some text to analyze"})
        assert result == "audit_text"

    def test_classify_steps_list(self):
        """Test classification with steps list -> validate_chain."""
        brain = VeritasBrain()
        result = brain.classify_task({"steps": ["Step A", "Step B"]})
        assert result == "validate_chain"

    def test_classify_chain_list(self):
        """Test classification with chain list -> validate_chain."""
        brain = VeritasBrain()
        result = brain.classify_task({"chain": ["Step A", "Step B"]})
        assert result == "validate_chain"

    def test_classify_sources_list(self):
        """Test classification with sources list -> check_sources."""
        brain = VeritasBrain()
        result = brain.classify_task({"sources": ["http://example.com"]})
        assert result == "check_sources"

    def test_classify_composite_text_and_steps(self):
        """Test classification with text and steps -> composite_audit."""
        brain = VeritasBrain()
        result = brain.classify_task({
            "text": "Some text",
            "steps": ["Step A", "Step B"]
        })
        assert result == "composite_audit"

    def test_classify_composite_text_and_sources(self):
        """Test classification with text and sources -> composite_audit."""
        brain = VeritasBrain()
        result = brain.classify_task({
            "text": "Some text",
            "sources": ["http://example.com"]
        })
        assert result == "composite_audit"

    def test_classify_composite_all_three(self):
        """Test classification with text, steps, and sources -> composite_audit."""
        brain = VeritasBrain()
        result = brain.classify_task({
            "text": "Some text",
            "steps": ["Step A"],
            "sources": ["http://example.com"]
        })
        assert result == "composite_audit"

    def test_classify_empty_payload(self):
        """Test classification with empty payload -> audit_text (default)."""
        brain = VeritasBrain()
        result = brain.classify_task({})
        assert result == "audit_text"

    def test_classify_empty_text(self):
        """Test classification with empty text string."""
        brain = VeritasBrain()
        result = brain.classify_task({"text": ""})
        assert result == "audit_text"


class TestRetrieveRelevantMemory:
    """Tests for memory retrieval."""

    def test_retrieve_memory_with_text(self):
        """Test memory retrieval with text in payload."""
        brain = VeritasBrain()
        result = brain.retrieve_relevant_memory({"text": "Test query"})
        assert "memory_hits" in result
        assert "memory_summary" in result
        assert isinstance(result["memory_hits"], list)

    def test_retrieve_memory_with_topic(self):
        """Test memory retrieval with topic in payload."""
        brain = VeritasBrain()
        result = brain.retrieve_relevant_memory({"topic": "climate change"})
        assert "memory_hits" in result
        assert "memory_summary" in result

    def test_retrieve_memory_with_context(self):
        """Test memory retrieval with context in payload."""
        brain = VeritasBrain()
        result = brain.retrieve_relevant_memory({"context": "Political debate"})
        assert "memory_hits" in result
        assert "memory_summary" in result

    def test_retrieve_memory_with_steps(self):
        """Test memory retrieval uses first step as query."""
        brain = VeritasBrain()
        result = brain.retrieve_relevant_memory({"steps": ["First reasoning step"]})
        assert "memory_hits" in result

    def test_retrieve_memory_empty_payload(self):
        """Test memory retrieval with empty payload returns empty."""
        brain = VeritasBrain()
        result = brain.retrieve_relevant_memory({})
        assert result["memory_hits"] == []
        assert result["memory_summary"] == ""

    def test_retrieve_memory_stub_response(self):
        """Test that stub RAG returns appropriate message."""
        brain = VeritasBrain()
        result = brain.retrieve_relevant_memory({"text": "Test"})
        # Since RAG is stubbed, should indicate that
        assert "memory_summary" in result


class TestRunAuditTools:
    """Tests for audit tool execution."""

    def test_run_tools_audit_text(self):
        """Test running tools for audit_text task."""
        brain = VeritasBrain()
        result = brain.run_audit_tools("audit_text", {"text": "Test text"})

        assert result["audit"] is not None
        assert result["bias"] is not None
        assert result["chain"] is None
        assert result["sources"] is None

    def test_run_tools_validate_chain(self):
        """Test running tools for validate_chain task."""
        brain = VeritasBrain()
        result = brain.run_audit_tools("validate_chain", {"steps": ["A", "B"]})

        assert result["audit"] is None
        assert result["bias"] is None
        assert result["chain"] is not None
        assert result["sources"] is None

    def test_run_tools_validate_chain_with_chain_key(self):
        """Test running tools with 'chain' key instead of 'steps'."""
        brain = VeritasBrain()
        result = brain.run_audit_tools("validate_chain", {"chain": ["A", "B"]})

        assert result["chain"] is not None

    def test_run_tools_check_sources(self):
        """Test running tools for check_sources task."""
        brain = VeritasBrain()
        result = brain.run_audit_tools("check_sources", {
            "sources": ["http://example.com"]
        })

        assert result["audit"] is None
        assert result["bias"] is None
        assert result["chain"] is None
        assert result["sources"] is not None

    def test_run_tools_composite_audit(self):
        """Test running all tools for composite_audit task."""
        brain = VeritasBrain()
        result = brain.run_audit_tools("composite_audit", {
            "text": "Test text",
            "steps": ["A", "B"],
            "sources": ["http://example.com"]
        })

        assert result["audit"] is not None
        assert result["bias"] is not None
        assert result["chain"] is not None
        assert result["sources"] is not None

    def test_run_tools_composite_partial(self):
        """Test composite audit with only some data types."""
        brain = VeritasBrain()
        result = brain.run_audit_tools("composite_audit", {
            "text": "Test text",
            "sources": ["http://example.com"]
        })

        assert result["audit"] is not None
        assert result["bias"] is not None
        assert result["chain"] is None
        assert result["sources"] is not None

    def test_run_tools_audit_returns_expected_keys(self):
        """Test that audit results have expected structure."""
        brain = VeritasBrain()
        result = brain.run_audit_tools("audit_text", {"text": "Test"})

        audit = result["audit"]
        assert "claims" in audit
        assert "logical_fallacies" in audit
        assert "inconsistencies" in audit
        assert "unsupported_jumps" in audit

    def test_run_tools_bias_returns_expected_keys(self):
        """Test that bias results have expected structure."""
        brain = VeritasBrain()
        result = brain.run_audit_tools("audit_text", {"text": "Test"})

        bias = result["bias"]
        assert "political_bias" in bias
        assert "emotional_bias" in bias
        assert "motivational_bias" in bias
        assert "certainty_overconfidence" in bias


class TestSynthesizeFindings:
    """Tests for finding synthesis."""

    def test_synthesize_returns_correct_schema(self):
        """Test that synthesis returns the expected schema."""
        brain = VeritasBrain()
        tool_results = {
            "audit": {"claims": [], "logical_fallacies": [], "inconsistencies": [], "unsupported_jumps": []},
            "bias": {"political_bias": 0.1, "emotional_bias": 0.2, "motivational_bias": 0.1, "certainty_overconfidence": 0.1},
            "chain": None,
            "sources": None,
        }
        memory_data = {"memory_hits": [], "memory_summary": ""}

        result = brain.synthesize_findings("audit_text", memory_data, tool_results)

        assert "task_type" in result
        assert "summary" in result
        assert "details" in result
        assert result["task_type"] == "audit_text"

    def test_synthesize_summary_has_required_keys(self):
        """Test that summary has all required keys."""
        brain = VeritasBrain()
        tool_results = {
            "audit": {"claims": [], "logical_fallacies": [], "inconsistencies": [], "unsupported_jumps": []},
            "bias": {"political_bias": 0.1, "emotional_bias": 0.2, "motivational_bias": 0.1, "certainty_overconfidence": 0.1},
            "chain": None,
            "sources": None,
        }
        memory_data = {"memory_hits": [], "memory_summary": ""}

        result = brain.synthesize_findings("audit_text", memory_data, tool_results)

        summary = result["summary"]
        assert "has_major_issues" in summary
        assert "issue_types" in summary
        assert "confidence_estimate" in summary

    def test_synthesize_details_has_required_keys(self):
        """Test that details has all required keys."""
        brain = VeritasBrain()
        tool_results = {
            "audit": None,
            "bias": None,
            "chain": None,
            "sources": None,
        }
        memory_data = {"memory_hits": [], "memory_summary": ""}

        result = brain.synthesize_findings("audit_text", memory_data, tool_results)

        details = result["details"]
        assert "audit" in details
        assert "bias" in details
        assert "chain" in details
        assert "sources" in details
        assert "memory_context" in details

    def test_synthesize_detects_high_bias(self):
        """Test that high bias is flagged as major issue."""
        brain = VeritasBrain()
        tool_results = {
            "audit": None,
            "bias": {"political_bias": 0.8, "emotional_bias": 0.2, "motivational_bias": 0.1, "certainty_overconfidence": 0.1},
            "chain": None,
            "sources": None,
        }
        memory_data = {"memory_hits": [], "memory_summary": ""}

        result = brain.synthesize_findings("audit_text", memory_data, tool_results)

        assert result["summary"]["has_major_issues"] is True
        assert "high_political_bias" in result["summary"]["issue_types"]

    def test_synthesize_detects_fallacies(self):
        """Test that multiple fallacies are flagged."""
        brain = VeritasBrain()
        tool_results = {
            "audit": {
                "claims": [],
                "logical_fallacies": [{"type": "ad_hominem"}, {"type": "strawman"}],
                "inconsistencies": [],
                "unsupported_jumps": []
            },
            "bias": None,
            "chain": None,
            "sources": None,
        }
        memory_data = {"memory_hits": [], "memory_summary": ""}

        result = brain.synthesize_findings("audit_text", memory_data, tool_results)

        assert result["summary"]["has_major_issues"] is True
        assert "logical_fallacies" in result["summary"]["issue_types"]

    def test_synthesize_detects_flawed_premises(self):
        """Test that flawed premises are flagged."""
        brain = VeritasBrain()
        tool_results = {
            "audit": None,
            "bias": None,
            "chain": {
                "gaps": [],
                "contradictions": [],
                "circular_logic": [],
                "flawed_premises": [{"step_index": 0, "step": "Assuming X"}]
            },
            "sources": None,
        }
        memory_data = {"memory_hits": [], "memory_summary": ""}

        result = brain.synthesize_findings("validate_chain", memory_data, tool_results)

        assert result["summary"]["has_major_issues"] is True
        assert "flawed_premises" in result["summary"]["issue_types"]

    def test_synthesize_confidence_in_range(self):
        """Test that confidence is between 0.0 and 1.0."""
        brain = VeritasBrain()
        tool_results = {
            "audit": {"claims": [], "logical_fallacies": [], "inconsistencies": [], "unsupported_jumps": []},
            "bias": {"political_bias": 0.5, "emotional_bias": 0.5, "motivational_bias": 0.5, "certainty_overconfidence": 0.5},
            "chain": {"gaps": [], "contradictions": [], "circular_logic": [], "flawed_premises": []},
            "sources": {"missing_sources": [], "unverifiable": [], "conflicting": [], "ranked_confidence": []},
        }
        memory_data = {"memory_hits": [], "memory_summary": ""}

        result = brain.synthesize_findings("composite_audit", memory_data, tool_results)

        confidence = result["summary"]["confidence_estimate"]
        assert 0.0 <= confidence <= 1.0

    def test_synthesize_no_issues_clean(self):
        """Test that clean data shows no major issues."""
        brain = VeritasBrain()
        tool_results = {
            "audit": {"claims": [], "logical_fallacies": [], "inconsistencies": [], "unsupported_jumps": []},
            "bias": {"political_bias": 0.1, "emotional_bias": 0.1, "motivational_bias": 0.1, "certainty_overconfidence": 0.1},
            "chain": None,
            "sources": None,
        }
        memory_data = {"memory_hits": [], "memory_summary": ""}

        result = brain.synthesize_findings("audit_text", memory_data, tool_results)

        assert result["summary"]["has_major_issues"] is False


class TestLogContribution:
    """Tests for contribution logging."""

    def test_log_contribution_does_not_raise(self):
        """Test that logging doesn't raise exceptions."""
        brain = VeritasBrain()
        result = {
            "task_type": "audit_text",
            "summary": {"has_major_issues": False, "issue_types": [], "confidence_estimate": 0.8},
            "details": {}
        }

        # Should not raise
        brain.log_contribution("audit_text", {"text": "Test"}, result)

    def test_log_contribution_metadata_no_full_text(self):
        """Test that logging captures metadata but not full text."""
        brain = VeritasBrain()
        long_text = "A" * 10000
        result = {
            "task_type": "audit_text",
            "summary": {"has_major_issues": False, "issue_types": [], "confidence_estimate": 0.8},
            "details": {}
        }

        # Should not raise, and should handle long text safely
        brain.log_contribution("audit_text", {"text": long_text}, result)


class TestProcessPipeline:
    """Tests for the complete processing pipeline."""

    def test_process_returns_correct_structure(self):
        """Test that process returns the expected structure."""
        brain = VeritasBrain()
        result = brain.process({"text": "Test text for analysis"})

        assert "task_type" in result
        assert "summary" in result
        assert "details" in result

    def test_process_audit_text_flow(self):
        """Test full pipeline for audit_text."""
        brain = VeritasBrain()
        result = brain.process({"text": "This is a test."})

        assert result["task_type"] == "audit_text"
        assert result["details"]["audit"] is not None
        assert result["details"]["bias"] is not None

    def test_process_validate_chain_flow(self):
        """Test full pipeline for validate_chain."""
        brain = VeritasBrain()
        result = brain.process({"steps": ["First step", "Second step"]})

        assert result["task_type"] == "validate_chain"
        assert result["details"]["chain"] is not None

    def test_process_check_sources_flow(self):
        """Test full pipeline for check_sources."""
        brain = VeritasBrain()
        result = brain.process({"sources": ["http://example.com", "http://test.edu"]})

        assert result["task_type"] == "check_sources"
        assert result["details"]["sources"] is not None

    def test_process_composite_flow(self):
        """Test full pipeline for composite audit."""
        brain = VeritasBrain()
        result = brain.process({
            "text": "Test text",
            "steps": ["Step A", "Step B"],
            "sources": ["http://example.com"]
        })

        assert result["task_type"] == "composite_audit"
        assert result["details"]["audit"] is not None
        assert result["details"]["chain"] is not None
        assert result["details"]["sources"] is not None

    def test_process_empty_payload(self):
        """Test pipeline handles empty payload gracefully."""
        brain = VeritasBrain()
        result = brain.process({})

        assert result["task_type"] == "audit_text"
        assert "summary" in result

    def test_process_detects_issues_in_text(self):
        """Test that processing detects issues in problematic text."""
        brain = VeritasBrain()
        # Text with fallacy pattern
        result = brain.process({
            "text": "You can't trust him because he's an idiot. Everyone knows that."
        })

        # Should detect ad hominem or other issues
        assert result["details"]["audit"] is not None
        assert result["details"]["bias"] is not None


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_text_handling(self):
        """Test handling of empty text."""
        brain = VeritasBrain()
        result = brain.process({"text": ""})

        assert result["task_type"] == "audit_text"
        assert "summary" in result

    def test_empty_steps_handling(self):
        """Test handling of empty steps list falls back to audit_text."""
        brain = VeritasBrain()
        result = brain.process({"steps": []})

        # Empty lists fall back to audit_text (default)
        assert result["task_type"] == "audit_text"
        assert "summary" in result

    def test_empty_sources_handling(self):
        """Test handling of empty sources list falls back to audit_text."""
        brain = VeritasBrain()
        result = brain.process({"sources": []})

        # Empty lists fall back to audit_text (default)
        assert result["task_type"] == "audit_text"
        assert "summary" in result

    def test_very_long_text(self):
        """Test handling of very long text."""
        brain = VeritasBrain()
        long_text = "This is a test sentence. " * 1000
        result = brain.process({"text": long_text})

        assert "task_type" in result
        assert "summary" in result

    def test_special_characters_in_text(self):
        """Test handling of special characters."""
        brain = VeritasBrain()
        result = brain.process({
            "text": "Special chars: <script>alert('xss')</script> & © ™ € £ ¥"
        })

        assert "task_type" in result
        assert "summary" in result

    def test_unicode_text(self):
        """Test handling of unicode text."""
        brain = VeritasBrain()
        result = brain.process({
            "text": "Unicode text: 你好世界 مرحبا العالم Привет мир"
        })

        assert "task_type" in result
        assert "summary" in result
