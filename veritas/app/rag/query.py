"""
Veritas RAG Query Module

This module handles semantic search and knowledge retrieval
from the RAG system using deterministic embeddings.

Phase 4: Local file-based querying with simple similarity search.
No external services, no network calls, no ML models.
"""

import logging
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

from logging.handlers import RotatingFileHandler

from app.rag.ingest import load_corpus


# Configure module logger
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = RotatingFileHandler(
        LOG_DIR / "rag_query.log",
        maxBytes=5_000_000,
        backupCount=3
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)


# Embedding configuration
EMBEDDING_DIM = 128  # Fixed dimension for our simple embeddings
VOCAB_HASH_SIZE = 1000  # Size of vocabulary hash space


def _tokenize(text: str) -> List[str]:
    """
    Simple tokenizer: lowercase, split on non-alphanumeric.

    Args:
        text: Input text to tokenize.

    Returns:
        List of tokens.
    """
    text = text.lower()
    tokens = re.findall(r'\b[a-z0-9]+\b', text)
    return tokens


def _hash_token(token: str) -> int:
    """
    Hash a token to a vocabulary index.

    Uses a simple deterministic hash for reproducibility.

    Args:
        token: Token to hash.

    Returns:
        Integer hash value in range [0, VOCAB_HASH_SIZE).
    """
    # Simple polynomial rolling hash
    h = 0
    for char in token:
        h = (h * 31 + ord(char)) % VOCAB_HASH_SIZE
    return h


def embed_text(text: str) -> List[float]:
    """
    Create a deterministic embedding for text.

    Uses a simple bag-of-words approach with hashed vocabulary
    to create a fixed-dimension vector representation.

    This is a deterministic, rule-based embedding:
    - Tokenize text
    - Hash each token to a position
    - Count occurrences
    - Normalize to unit vector

    Args:
        text: The text to embed.

    Returns:
        List of floats representing the embedding vector.
    """
    if not text or not text.strip():
        return [0.0] * EMBEDDING_DIM

    tokens = _tokenize(text)
    if not tokens:
        return [0.0] * EMBEDDING_DIM

    # Create embedding vector using token hashing
    embedding = [0.0] * EMBEDDING_DIM
    token_counts = Counter(tokens)

    for token, count in token_counts.items():
        # Hash token to embedding dimension
        idx = _hash_token(token) % EMBEDDING_DIM
        # Add log-scaled count (TF-like weighting)
        embedding[idx] += 1 + math.log(count) if count > 0 else 0

    # L2 normalize
    magnitude = math.sqrt(sum(x * x for x in embedding))
    if magnitude > 0:
        embedding = [x / magnitude for x in embedding]

    return embedding


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    Args:
        vec1: First vector.
        vec2: Second vector.

    Returns:
        Cosine similarity score between -1 and 1.
    """
    if len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))

    if mag1 == 0 or mag2 == 0:
        return 0.0

    return dot_product / (mag1 * mag2)


def query_relevant_documents(query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Query the corpus for relevant documents.

    Embeds the query and all documents, computes similarity,
    and returns the top-k most relevant documents.

    Args:
        query: The query text.
        top_k: Number of top results to return.

    Returns:
        Dictionary containing:
        - hits: List of matching documents with scores
    """
    logger.info(f"Querying corpus with: '{query[:50]}...' (top_k={top_k})")

    # Load corpus
    corpus = load_corpus()
    if not corpus:
        logger.info("Corpus is empty, returning no hits")
        return {"hits": []}

    # Embed query
    query_embedding = embed_text(query)

    # Score all documents
    scored_docs = []
    for doc in corpus:
        doc_text = doc.get("text", "")
        doc_embedding = embed_text(doc_text)
        score = cosine_similarity(query_embedding, doc_embedding)

        scored_docs.append({
            "id": doc.get("id", ""),
            "text": doc_text,
            "tags": doc.get("tags", []),
            "score": round(score, 4),
        })

    # Sort by score descending
    scored_docs.sort(key=lambda x: x["score"], reverse=True)

    # Return top-k
    hits = scored_docs[:top_k]

    logger.info(f"Found {len(hits)} hits (max score: {hits[0]['score'] if hits else 0})")
    logger.debug(f"Top hit IDs: {[h['id'] for h in hits]}")

    return {"hits": hits}


class RAGQuery:
    """
    RAG Query handler for semantic search and knowledge retrieval.

    Phase 4: File-based implementation with deterministic embeddings.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the RAGQuery handler.

        Args:
            config: Optional configuration dictionary for query settings.
        """
        self.config = config or {}
        self.top_k = self.config.get("top_k", 5)
        self.similarity_threshold = self.config.get("similarity_threshold", 0.1)
        self._initialized = True
        logger.info("RAGQuery initialized")

    def query(self, query_text: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        """
        Perform a semantic search query.

        Args:
            query_text: The query text to search for.
            top_k: Optional override for number of results to return.

        Returns:
            Dictionary containing query results.
        """
        k = top_k or self.top_k
        result = query_relevant_documents(query_text, top_k=k)

        hits = result.get("hits", [])

        # Filter by threshold
        filtered_hits = [
            h for h in hits
            if h["score"] >= self.similarity_threshold
        ]

        return {
            "status": "success",
            "results": filtered_hits,
            "scores": [h["score"] for h in filtered_hits],
            "total_matches": len(filtered_hits),
        }

    def query_with_filter(
        self,
        query_text: str,
        filters: Dict[str, Any],
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Perform a semantic search with metadata filters.

        Args:
            query_text: The query text to search for.
            filters: Dictionary of metadata filters (e.g., {"tags": ["science"]}).
            top_k: Optional override for number of results.

        Returns:
            Dictionary containing filtered query results.
        """
        k = top_k or self.top_k
        result = query_relevant_documents(query_text, top_k=k * 3)  # Get more to filter

        hits = result.get("hits", [])

        # Apply tag filter if present
        tag_filter = filters.get("tags", [])
        if tag_filter:
            hits = [
                h for h in hits
                if any(t in h.get("tags", []) for t in tag_filter)
            ]

        # Apply threshold and limit
        filtered_hits = [
            h for h in hits
            if h["score"] >= self.similarity_threshold
        ][:k]

        return {
            "status": "success",
            "results": filtered_hits,
            "scores": [h["score"] for h in filtered_hits],
            "filters_applied": filters,
            "total_matches": len(filtered_hits),
        }

    def hybrid_search(
        self,
        query_text: str,
        keyword_weight: float = 0.5,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Perform a hybrid search combining keyword and semantic search.

        Args:
            query_text: The query text to search for.
            keyword_weight: Weight given to keyword matching (0-1).
            top_k: Optional override for number of results.

        Returns:
            Dictionary containing hybrid search results.
        """
        k = top_k or self.top_k

        # Load corpus
        corpus = load_corpus()
        if not corpus:
            return {
                "status": "success",
                "results": [],
                "keyword_matches": [],
                "semantic_matches": [],
                "total_matches": 0,
            }

        # Get semantic results
        semantic_result = query_relevant_documents(query_text, top_k=k)
        semantic_hits = semantic_result.get("hits", [])

        # Compute keyword matches
        query_tokens = set(_tokenize(query_text))
        keyword_scores = []

        for doc in corpus:
            doc_tokens = set(_tokenize(doc.get("text", "")))
            if query_tokens and doc_tokens:
                overlap = len(query_tokens & doc_tokens)
                jaccard = overlap / len(query_tokens | doc_tokens)
            else:
                jaccard = 0.0

            keyword_scores.append({
                "id": doc.get("id", ""),
                "text": doc.get("text", ""),
                "tags": doc.get("tags", []),
                "score": round(jaccard, 4),
            })

        keyword_scores.sort(key=lambda x: x["score"], reverse=True)
        keyword_hits = keyword_scores[:k]

        # Combine scores
        combined = {}
        semantic_weight = 1.0 - keyword_weight

        for hit in semantic_hits:
            doc_id = hit["id"]
            combined[doc_id] = {
                **hit,
                "combined_score": hit["score"] * semantic_weight,
            }

        for hit in keyword_hits:
            doc_id = hit["id"]
            if doc_id in combined:
                combined[doc_id]["combined_score"] += hit["score"] * keyword_weight
            else:
                combined[doc_id] = {
                    **hit,
                    "combined_score": hit["score"] * keyword_weight,
                }

        # Sort by combined score
        results = sorted(combined.values(), key=lambda x: x["combined_score"], reverse=True)[:k]

        return {
            "status": "success",
            "results": results,
            "keyword_matches": keyword_hits,
            "semantic_matches": semantic_hits,
            "total_matches": len(results),
        }

    def get_context(self, query_text: str, max_tokens: int = 4000) -> Dict[str, Any]:
        """
        Retrieve context for a query optimized for token limits.

        Args:
            query_text: The query to get context for.
            max_tokens: Maximum number of tokens in the context.

        Returns:
            Dictionary containing assembled context.
        """
        result = query_relevant_documents(query_text, top_k=10)
        hits = result.get("hits", [])

        context_parts = []
        sources = []
        estimated_tokens = 0

        for hit in hits:
            text = hit.get("text", "")
            # Rough token estimate: ~4 chars per token
            text_tokens = len(text) // 4

            if estimated_tokens + text_tokens <= max_tokens:
                context_parts.append(text)
                sources.append({"id": hit["id"], "score": hit["score"]})
                estimated_tokens += text_tokens
            else:
                break

        return {
            "status": "success",
            "context": "\n\n".join(context_parts),
            "sources": sources,
            "token_count": estimated_tokens,
        }

    def explain_match(self, query_text: str, document: str) -> Dict[str, Any]:
        """
        Explain why a document matched a query.

        Args:
            query_text: The query that was searched.
            document: The document that matched.

        Returns:
            Dictionary containing match explanation.
        """
        query_embedding = embed_text(query_text)
        doc_embedding = embed_text(document)

        similarity = cosine_similarity(query_embedding, doc_embedding)

        query_tokens = set(_tokenize(query_text))
        doc_tokens = set(_tokenize(document))
        matching_terms = list(query_tokens & doc_tokens)

        return {
            "status": "success",
            "explanation": f"Document matched with similarity {similarity:.4f}",
            "matching_terms": matching_terms[:20],
            "similarity_score": round(similarity, 4),
        }


def query_knowledge_stub(query: str) -> Dict[str, Any]:
    """
    Backward-compatible stub that uses the real implementation.

    Args:
        query: The query to search for.

    Returns:
        Dictionary containing query results.
    """
    return query_relevant_documents(query)
