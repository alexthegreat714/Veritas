"""
Veritas RAG (Retrieval-Augmented Generation) Package

This package contains modules for RAG-based knowledge retrieval:
- ingest: Document ingestion and embedding generation
- query: Semantic search and knowledge retrieval
"""

from app.rag.ingest import DocumentIngester, ingest_document_stub
from app.rag.query import RAGQuery, query_knowledge_stub

__all__ = [
    "DocumentIngester",
    "ingest_document_stub",
    "RAGQuery",
    "query_knowledge_stub",
]
