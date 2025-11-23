"""
Tests for Veritas RAG (Retrieval-Augmented Generation) system.

Phase 4: Tests for document ingestion, embedding, and similarity search.
"""

import pytest
from typing import Any, Dict, List

from app.rag.ingest import (
    ingest_documents,
    clear_corpus,
    get_corpus_stats,
    load_corpus,
)
from app.rag.query import (
    embed_text,
    cosine_similarity,
    query_relevant_documents,
    RAGQuery,
)
from app.logic.brain import VeritasBrain


class TestIngestDocuments:
    """Tests for document ingestion."""

    def test_ingest_single_document(self):
        """Test ingesting a single document."""
        clear_corpus()
        docs = [{"id": "doc1", "text": "The sky is blue.", "tags": ["science"]}]
        result = ingest_documents(docs)

        assert result["ingested_count"] == 1
        assert result["errors"] == []

    def test_ingest_multiple_documents(self):
        """Test ingesting multiple documents."""
        clear_corpus()
        docs = [
            {"id": "doc1", "text": "The sky is blue."},
            {"id": "doc2", "text": "Water is composed of hydrogen and oxygen."},
            {"id": "doc3", "text": "The Earth orbits the Sun."},
        ]
        result = ingest_documents(docs)

        assert result["ingested_count"] == 3
        assert result["errors"] == []

    def test_ingest_missing_id_fails(self):
        """Test that missing id field causes error."""
        clear_corpus()
        docs = [{"text": "No ID here"}]
        result = ingest_documents(docs)

        assert result["ingested_count"] == 0
        assert len(result["errors"]) == 1
        assert "Missing 'id' field" in result["errors"][0]["error"]

    def test_ingest_missing_text_fails(self):
        """Test that missing text field causes error."""
        clear_corpus()
        docs = [{"id": "doc1"}]
        result = ingest_documents(docs)

        assert result["ingested_count"] == 0
        assert len(result["errors"]) == 1
        assert "Missing 'text' field" in result["errors"][0]["error"]

    def test_ingest_with_tags(self):
        """Test ingesting documents with tags."""
        clear_corpus()
        docs = [
            {"id": "doc1", "text": "Science fact", "tags": ["science", "fact"]},
        ]
        result = ingest_documents(docs)

        assert result["ingested_count"] == 1
        corpus = load_corpus()
        assert corpus[0]["tags"] == ["science", "fact"]

    def test_ingest_appends_to_corpus(self):
        """Test that ingestion appends to existing corpus."""
        clear_corpus()

        # First ingest
        docs1 = [{"id": "doc1", "text": "First document"}]
        ingest_documents(docs1)

        # Second ingest
        docs2 = [{"id": "doc2", "text": "Second document"}]
        ingest_documents(docs2)

        stats = get_corpus_stats()
        assert stats["document_count"] == 2


class TestClearCorpus:
    """Tests for corpus clearing."""

    def test_clear_corpus(self):
        """Test clearing the corpus."""
        # Add some documents first
        docs = [{"id": "doc1", "text": "Test"}]
        ingest_documents(docs)

        result = clear_corpus()
        assert result["cleared"] is True

        stats = get_corpus_stats()
        assert stats["document_count"] == 0

    def test_clear_empty_corpus(self):
        """Test clearing an already empty corpus."""
        clear_corpus()
        result = clear_corpus()

        assert result["cleared"] is True


class TestCorpusStats:
    """Tests for corpus statistics."""

    def test_stats_empty_corpus(self):
        """Test stats on empty corpus."""
        clear_corpus()
        stats = get_corpus_stats()

        assert stats["document_count"] == 0
        assert stats["exists"] is False

    def test_stats_with_documents(self):
        """Test stats with documents."""
        clear_corpus()
        docs = [
            {"id": "doc1", "text": "First document"},
            {"id": "doc2", "text": "Second document"},
        ]
        ingest_documents(docs)

        stats = get_corpus_stats()

        assert stats["document_count"] == 2
        assert stats["exists"] is True
        assert stats["file_size_bytes"] > 0


class TestEmbedText:
    """Tests for text embedding."""

    def test_embed_returns_list(self):
        """Test that embed returns a list of floats."""
        embedding = embed_text("Hello world")

        assert isinstance(embedding, list)
        assert len(embedding) == 128  # EMBEDDING_DIM
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_empty_text(self):
        """Test embedding empty text."""
        embedding = embed_text("")

        assert len(embedding) == 128
        assert all(x == 0.0 for x in embedding)

    def test_embed_deterministic(self):
        """Test that embedding is deterministic."""
        text = "The quick brown fox"
        embedding1 = embed_text(text)
        embedding2 = embed_text(text)

        assert embedding1 == embedding2

    def test_embed_different_texts_differ(self):
        """Test that different texts have different embeddings."""
        embedding1 = embed_text("cats are fluffy")
        embedding2 = embed_text("quantum physics is complex")

        assert embedding1 != embedding2

    def test_embed_normalized(self):
        """Test that embeddings are L2 normalized."""
        import math
        embedding = embed_text("Some text for testing normalization")

        magnitude = math.sqrt(sum(x * x for x in embedding))
        assert abs(magnitude - 1.0) < 0.001


class TestCosineSimilarity:
    """Tests for cosine similarity computation."""

    def test_identical_vectors(self):
        """Test similarity of identical vectors."""
        vec = [0.5, 0.5, 0.5, 0.5]
        similarity = cosine_similarity(vec, vec)

        assert abs(similarity - 1.0) < 0.001

    def test_orthogonal_vectors(self):
        """Test similarity of orthogonal vectors."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = cosine_similarity(vec1, vec2)

        assert abs(similarity) < 0.001

    def test_different_length_vectors(self):
        """Test handling of different length vectors."""
        vec1 = [1.0, 0.5]
        vec2 = [1.0, 0.5, 0.3]
        similarity = cosine_similarity(vec1, vec2)

        assert similarity == 0.0

    def test_zero_vector(self):
        """Test handling of zero vector."""
        vec1 = [1.0, 0.5]
        vec2 = [0.0, 0.0]
        similarity = cosine_similarity(vec1, vec2)

        assert similarity == 0.0


class TestQueryRelevantDocuments:
    """Tests for document querying."""

    def test_query_empty_corpus(self):
        """Test querying empty corpus returns empty hits."""
        clear_corpus()
        result = query_relevant_documents("test query")

        assert result["hits"] == []

    def test_query_finds_relevant_document(self):
        """Test that query finds relevant document."""
        clear_corpus()
        docs = [
            {"id": "climate", "text": "Climate change is caused by greenhouse gas emissions."},
            {"id": "cooking", "text": "Cooking pasta requires boiling water."},
            {"id": "sports", "text": "Soccer is the most popular sport worldwide."},
        ]
        ingest_documents(docs)

        result = query_relevant_documents("What causes climate change?", top_k=3)

        assert len(result["hits"]) == 3
        # Climate doc should rank highest
        assert result["hits"][0]["id"] == "climate"

    def test_query_top_k(self):
        """Test that top_k limits results."""
        clear_corpus()
        docs = [
            {"id": f"doc{i}", "text": f"Document number {i}"}
            for i in range(10)
        ]
        ingest_documents(docs)

        result = query_relevant_documents("document", top_k=3)

        assert len(result["hits"]) == 3

    def test_query_returns_scores(self):
        """Test that query returns scores."""
        clear_corpus()
        docs = [{"id": "doc1", "text": "Test document content"}]
        ingest_documents(docs)

        result = query_relevant_documents("test document", top_k=1)

        assert len(result["hits"]) == 1
        assert "score" in result["hits"][0]
        assert isinstance(result["hits"][0]["score"], float)

    def test_query_returns_text_and_tags(self):
        """Test that query returns text and tags."""
        clear_corpus()
        docs = [{"id": "doc1", "text": "Test content", "tags": ["test"]}]
        ingest_documents(docs)

        result = query_relevant_documents("test", top_k=1)

        assert result["hits"][0]["text"] == "Test content"
        assert result["hits"][0]["tags"] == ["test"]


class TestRAGQuery:
    """Tests for the RAGQuery class."""

    def test_query_class_initialization(self):
        """Test RAGQuery initialization."""
        rag = RAGQuery()
        assert rag._initialized is True

    def test_query_class_with_config(self):
        """Test RAGQuery with custom config."""
        rag = RAGQuery({"top_k": 10, "similarity_threshold": 0.5})
        assert rag.top_k == 10
        assert rag.similarity_threshold == 0.5

    def test_query_method(self):
        """Test RAGQuery.query method."""
        clear_corpus()
        docs = [{"id": "doc1", "text": "Machine learning algorithms"}]
        ingest_documents(docs)

        rag = RAGQuery()
        result = rag.query("machine learning")

        assert result["status"] == "success"
        assert "results" in result
        assert "total_matches" in result

    def test_explain_match(self):
        """Test explain_match functionality."""
        rag = RAGQuery()
        result = rag.explain_match("cat dog", "the cat and dog are friends")

        assert result["status"] == "success"
        assert "matching_terms" in result
        assert "cat" in result["matching_terms"]
        assert "dog" in result["matching_terms"]
        assert "similarity_score" in result


class TestBrainRAGIntegration:
    """Tests for VeritasBrain RAG integration."""

    def test_brain_retrieve_empty_corpus(self):
        """Test brain retrieval with empty corpus."""
        clear_corpus()
        brain = VeritasBrain()

        result = brain.retrieve_relevant_memory({"text": "test query"})

        assert "memory_hits" in result
        assert "memory_summary" in result
        assert result["memory_hits"] == []

    def test_brain_retrieve_with_corpus(self):
        """Test brain retrieval with populated corpus."""
        clear_corpus()
        docs = [
            {"id": "fact1", "text": "The speed of light is approximately 300,000 km/s."},
            {"id": "fact2", "text": "Water freezes at 0 degrees Celsius."},
        ]
        ingest_documents(docs)

        brain = VeritasBrain()
        result = brain.retrieve_relevant_memory({"text": "speed of light"})

        assert len(result["memory_hits"]) > 0
        # First hit should be about speed of light
        assert result["memory_hits"][0]["id"] == "fact1"

    def test_brain_retrieve_with_topic(self):
        """Test brain retrieval using topic field."""
        clear_corpus()
        docs = [{"id": "doc1", "text": "Python programming language"}]
        ingest_documents(docs)

        brain = VeritasBrain()
        result = brain.retrieve_relevant_memory({"topic": "python"})

        assert len(result["memory_hits"]) > 0

    def test_brain_retrieve_uses_steps(self):
        """Test brain retrieval uses first step when no text."""
        clear_corpus()
        docs = [{"id": "doc1", "text": "Logic and reasoning"}]
        ingest_documents(docs)

        brain = VeritasBrain()
        result = brain.retrieve_relevant_memory({
            "steps": ["Logic is important", "Reasoning follows"]
        })

        assert len(result["memory_hits"]) > 0

    def test_brain_process_includes_memory(self):
        """Test that brain.process includes memory context."""
        clear_corpus()
        docs = [{"id": "fact1", "text": "Veritas checks for truth and accuracy."}]
        ingest_documents(docs)

        brain = VeritasBrain()
        result = brain.process({"text": "checking truth"})

        assert "details" in result
        assert "memory_context" in result["details"]
        assert "memory_hits" in result["details"]["memory_context"]


class TestEndpointIntegration:
    """Tests for RAG endpoint integration."""

    def test_ingest_docs_endpoint(self, client):
        """Test /ingest_docs endpoint."""
        # Clear first
        client.post("/clear_corpus")

        response = client.post(
            "/ingest_docs",
            json={
                "docs": [
                    {"id": "test1", "text": "Test document", "tags": ["test"]},
                    {"id": "test2", "text": "Another document"},
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["ingested_count"] == 2

    def test_clear_corpus_endpoint(self, client):
        """Test /clear_corpus endpoint."""
        response = client.post("/clear_corpus")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_corpus_stats_endpoint(self, client):
        """Test /corpus_stats endpoint."""
        client.post("/clear_corpus")
        client.post(
            "/ingest_docs",
            json={"docs": [{"id": "test1", "text": "Test"}]}
        )

        response = client.get("/corpus_stats")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["document_count"] == 1
        assert data["exists"] is True

    def test_run_task_uses_memory(self, client):
        """Test that /run_task includes memory context."""
        client.post("/clear_corpus")
        client.post(
            "/ingest_docs",
            json={"docs": [{"id": "fact1", "text": "The capital of France is Paris."}]}
        )

        response = client.post(
            "/run_task",
            json={
                "task_type": "audit_text",
                "payload": {"text": "What is the capital of France?"}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "details" in data
        assert "memory_context" in data["details"]

    def test_status_shows_rag_active(self, client):
        """Test that /status shows RAG as active."""
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert data["phase"] == 5
        assert data["components"]["rag"] == "active"
