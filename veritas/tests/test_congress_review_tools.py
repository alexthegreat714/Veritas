"""
Tests for Veritas Phase 4 Congress Review Tools

Tests for tool_review_bill and tool_review_statement functions
that provide Congress-facing audit capabilities.
"""

import pytest

from app.tools import (
    tool_review_bill,
    tool_review_statement,
    audit_text_structured,
    audit_with_sources_structured,
    registry,
    TOOLS,
)
from app.schemas import (
    AuditResult,
    AuditWithSourcesResult,
    CongressReviewResult,
)


class TestAuditTextStructured:
    """Tests for audit_text_structured function."""

    def test_returns_audit_result_model(self):
        """Test that structured audit returns AuditResult."""
        text = "This is a simple statement that needs verification."
        result = audit_text_structured(text)

        assert isinstance(result, AuditResult)
        assert result.original_text == text
        assert result.confidence in ["low", "medium", "high"]

    def test_audit_result_has_normalized_dict(self):
        """Test that normalized field contains expected keys."""
        text = "The sky is blue. Water is wet."
        result = audit_text_structured(text)

        assert "claims" in result.normalized
        assert "word_count" in result.normalized
        assert "sentence_count" in result.normalized

    def test_audit_result_is_json_serializable(self):
        """Test that result can be serialized to JSON."""
        text = "Testing JSON serialization."
        result = audit_text_structured(text)

        # model_dump should work
        data = result.model_dump()
        assert isinstance(data, dict)
        assert "original_text" in data
        assert "logical_issues" in data
        assert "bias_flags" in data

    def test_detects_bias_in_loaded_text(self):
        """Test that biased text triggers bias flags."""
        text = """
        OBVIOUSLY everyone KNOWS this is absolutely TRUE!
        This HORRIBLE policy will DESTROY everything!
        We MUST act NOW or face DISASTER!
        """
        result = audit_text_structured(text)

        # Should have some bias flags
        assert len(result.bias_flags) > 0

    def test_clean_text_has_high_confidence(self):
        """Test that clean text gets high confidence."""
        text = "Research indicates that regular exercise improves health."
        result = audit_text_structured(text)

        assert result.confidence == "high"


class TestAuditWithSourcesStructured:
    """Tests for audit_with_sources_structured function."""

    def test_returns_audit_with_sources_result(self):
        """Test that structured audit with sources returns correct model."""
        text = "Climate change is accelerating according to recent studies."
        sources = ["https://nature.com/climate", "https://science.org/report"]

        result = audit_with_sources_structured(text, sources)

        assert isinstance(result, AuditWithSourcesResult)
        assert isinstance(result.audit, AuditResult)

    def test_includes_retrieved_docs(self):
        """Test that retrieved_docs field exists."""
        text = "Some claim that needs verification."
        result = audit_with_sources_structured(text)

        assert "retrieved_docs" in result.model_dump()
        assert isinstance(result.retrieved_docs, list)

    def test_source_validation_populated(self):
        """Test that source validation is populated when sources provided."""
        text = "The study shows significant results."
        sources = ["https://arxiv.org/abs/1234.5678"]

        result = audit_with_sources_structured(text, sources)

        # Should have source validation items
        assert isinstance(result.source_validation, list)


class TestToolReviewBill:
    """Tests for tool_review_bill function."""

    def test_basic_bill_review(self):
        """Test basic bill review functionality."""
        payload = {
            "bill_id": "BILL-001",
            "text": "This bill proposes to establish guidelines for data privacy."
        }

        result = tool_review_bill(payload)

        assert "item_type" in result
        assert result["item_type"] == "bill"
        assert result["id"] == "BILL-001"

    def test_bill_review_returns_congress_review_structure(self):
        """Test that bill review returns CongressReviewResult structure."""
        payload = {
            "bill_id": "BILL-002",
            "text": "A clear and well-structured policy document."
        }

        result = tool_review_bill(payload)

        # Should have all CongressReviewResult fields
        assert "item_type" in result
        assert "id" in result
        assert "audit" in result
        assert "recommendation" in result
        assert "notes" in result

    def test_bill_review_recommendation_values(self):
        """Test that recommendation is one of valid values."""
        payload = {
            "bill_id": "BILL-003",
            "text": "This is a test bill with some content."
        }

        result = tool_review_bill(payload)

        assert result["recommendation"] in ["approve", "reject", "revise"]

    def test_bill_review_with_issues_gets_reject_or_revise(self):
        """Test that problematic text gets reject or revise recommendation."""
        payload = {
            "bill_id": "BILL-004",
            "text": """
            This TERRIBLE bill will DESTROY our economy!
            Everyone KNOWS this is absolutely WRONG!
            We MUST reject this IMMEDIATELY!
            Obviously, the authors are completely incompetent.
            """
        }

        result = tool_review_bill(payload)

        # Should recommend reject or revise due to bias
        assert result["recommendation"] in ["reject", "revise"]

    def test_bill_review_without_text_returns_error(self):
        """Test that missing text returns error."""
        payload = {
            "bill_id": "BILL-005",
            "text": ""
        }

        result = tool_review_bill(payload)

        assert "error" in result

    def test_bill_review_is_json_serializable(self):
        """Test that result is JSON serializable."""
        import json

        payload = {
            "bill_id": "BILL-006",
            "text": "A simple bill for testing serialization."
        }

        result = tool_review_bill(payload)

        # Should not raise
        json_str = json.dumps(result)
        assert isinstance(json_str, str)

    def test_bill_review_with_sources(self):
        """Test bill review with supporting sources."""
        payload = {
            "bill_id": "BILL-007",
            "text": "This policy is based on scientific research.",
            "sources": [
                "https://nature.com/article",
                "https://science.org/study"
            ]
        }

        result = tool_review_bill(payload)

        assert result["item_type"] == "bill"
        # Should complete without error
        assert "audit" in result


class TestToolReviewStatement:
    """Tests for tool_review_statement function."""

    def test_basic_statement_review(self):
        """Test basic statement review functionality."""
        payload = {
            "statement_id": "STMT-001",
            "text": "The proposed budget allocation is reasonable."
        }

        result = tool_review_statement(payload)

        assert "item_type" in result
        assert result["item_type"] == "statement"
        assert result["id"] == "STMT-001"

    def test_statement_review_returns_congress_review_structure(self):
        """Test that statement review returns CongressReviewResult structure."""
        payload = {
            "statement_id": "STMT-002",
            "text": "A factual statement about current conditions."
        }

        result = tool_review_statement(payload)

        # Should have all CongressReviewResult fields
        assert "item_type" in result
        assert "id" in result
        assert "audit" in result
        assert "recommendation" in result
        assert "notes" in result

    def test_statement_review_without_text_returns_error(self):
        """Test that missing text returns error."""
        payload = {
            "statement_id": "STMT-003",
            "text": ""
        }

        result = tool_review_statement(payload)

        assert "error" in result

    def test_clean_statement_gets_favorable_review(self):
        """Test that clean statement gets approve or revise."""
        payload = {
            "statement_id": "STMT-004",
            "text": "The committee met on Tuesday and discussed the agenda items."
        }

        result = tool_review_statement(payload)

        # Clean text should get approve or revise (not reject)
        assert result["recommendation"] in ["approve", "revise"]


class TestToolRegistry:
    """Tests for tool registry functionality."""

    def test_registry_has_review_tools(self):
        """Test that registry includes review tools."""
        tools = registry.list_tools()

        assert "review_bill" in tools
        assert "review_statement" in tools

    def test_registry_invoke_review_bill(self):
        """Test invoking review_bill through registry."""
        result = registry.invoke("review_bill", {
            "bill_id": "REG-001",
            "text": "Test bill content."
        })

        assert "item_type" in result or "error" in result

    def test_registry_invoke_unknown_tool(self):
        """Test invoking unknown tool returns error."""
        result = registry.invoke("unknown_tool", {})

        assert "error" in result
        assert "available_tools" in result

    def test_tools_dict_exported(self):
        """Test that TOOLS dict is exported."""
        assert isinstance(TOOLS, dict)
        assert "review_bill" in TOOLS
        assert "review_statement" in TOOLS


class TestCongressReviewResult:
    """Tests for CongressReviewResult schema."""

    def test_schema_validation(self):
        """Test that schema validates correctly."""
        audit = audit_with_sources_structured("Test text")

        result = CongressReviewResult(
            item_type="bill",
            id="TEST-001",
            audit=audit,
            recommendation="approve",
            notes="Test notes"
        )

        assert result.item_type == "bill"
        assert result.id == "TEST-001"
        assert result.recommendation == "approve"

    def test_schema_model_dump(self):
        """Test that model_dump produces valid dict."""
        audit = audit_with_sources_structured("Test text")

        result = CongressReviewResult(
            item_type="statement",
            id="TEST-002",
            audit=audit,
            recommendation="revise",
            notes="Needs revision"
        )

        data = result.model_dump()
        assert isinstance(data, dict)
        assert data["item_type"] == "statement"
        assert data["recommendation"] == "revise"
