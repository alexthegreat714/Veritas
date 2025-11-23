"""
Veritas RAG Ingestion Module

This module handles document ingestion for the RAG system,
including document processing and persistent storage.

Phase 4: Local file-based ingestion with JSONL storage.
No external services, no network calls.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from logging.handlers import RotatingFileHandler


# Configure module logger
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = RotatingFileHandler(
        LOG_DIR / "rag_ingest.log",
        maxBytes=5_000_000,
        backupCount=3
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)


# Corpus storage path
MEMORY_DIR = Path(__file__).parent.parent / "memory" / "long"
CORPUS_FILE = MEMORY_DIR / "veritas_corpus.jsonl"


def _ensure_corpus_dir() -> None:
    """Ensure the corpus directory exists."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def ingest_documents(docs: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Ingests a list of documents into Veritas' local fact corpus.

    Each document should have fields:
    - 'id': Unique identifier (required)
    - 'text': Document text content (required)
    - 'tags': Optional list of tags for categorization

    Documents are appended to memory/long/veritas_corpus.jsonl.

    Args:
        docs: List of document dictionaries.

    Returns:
        Dictionary containing ingestion results:
        - ingested_count: Number of documents successfully ingested
        - errors: List of any errors encountered
    """
    logger.info(f"Ingesting {len(docs)} documents")
    _ensure_corpus_dir()

    ingested_count = 0
    errors = []

    try:
        with open(CORPUS_FILE, "a", encoding="utf-8") as f:
            for doc in docs:
                try:
                    # Validate required fields
                    if "id" not in doc:
                        errors.append({"error": "Missing 'id' field", "doc": str(doc)[:100]})
                        continue
                    if "text" not in doc:
                        errors.append({"error": "Missing 'text' field", "id": doc.get("id")})
                        continue

                    # Build document record
                    record = {
                        "id": str(doc["id"]),
                        "text": str(doc["text"]),
                        "tags": doc.get("tags", []),
                        "ingested_at": datetime.now(timezone.utc).isoformat(),
                    }

                    # Write as JSONL
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    ingested_count += 1
                    logger.debug(f"Ingested document: {record['id']}")

                except Exception as e:
                    errors.append({
                        "error": str(e),
                        "id": doc.get("id", "unknown")
                    })
                    logger.error(f"Error ingesting document: {e}")

    except Exception as e:
        logger.error(f"Failed to open corpus file: {e}")
        errors.append({"error": f"File error: {str(e)}"})

    logger.info(f"Ingestion complete: {ingested_count} documents, {len(errors)} errors")

    return {
        "ingested_count": ingested_count,
        "errors": errors,
    }


def clear_corpus() -> Dict[str, Any]:
    """
    Clears the current fact corpus.

    Used for tests or resets. Removes all documents from the corpus file.

    Returns:
        Dictionary containing clear results:
        - cleared: Boolean indicating success
        - message: Status message
    """
    logger.info("Clearing corpus")

    try:
        if CORPUS_FILE.exists():
            os.remove(CORPUS_FILE)
            logger.info("Corpus file deleted")
            return {
                "cleared": True,
                "message": "Corpus cleared successfully",
            }
        else:
            logger.info("Corpus file does not exist, nothing to clear")
            return {
                "cleared": True,
                "message": "Corpus was already empty",
            }
    except Exception as e:
        logger.error(f"Failed to clear corpus: {e}")
        return {
            "cleared": False,
            "message": f"Error clearing corpus: {str(e)}",
        }


def get_corpus_stats() -> Dict[str, Any]:
    """
    Get statistics about the current corpus.

    Returns:
        Dictionary containing:
        - document_count: Number of documents in corpus
        - file_size_bytes: Size of corpus file in bytes
        - exists: Whether corpus file exists
    """
    if not CORPUS_FILE.exists():
        return {
            "document_count": 0,
            "file_size_bytes": 0,
            "exists": False,
        }

    try:
        doc_count = 0
        with open(CORPUS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    doc_count += 1

        file_size = CORPUS_FILE.stat().st_size

        return {
            "document_count": doc_count,
            "file_size_bytes": file_size,
            "exists": True,
        }
    except Exception as e:
        logger.error(f"Error getting corpus stats: {e}")
        return {
            "document_count": 0,
            "file_size_bytes": 0,
            "exists": True,
            "error": str(e),
        }


def load_corpus() -> List[Dict[str, Any]]:
    """
    Load all documents from the corpus.

    Returns:
        List of document dictionaries.
    """
    if not CORPUS_FILE.exists():
        return []

    documents = []
    try:
        with open(CORPUS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        doc = json.loads(line)
                        documents.append(doc)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping malformed line: {e}")
    except Exception as e:
        logger.error(f"Error loading corpus: {e}")

    return documents


class DocumentIngester:
    """
    Document Ingester for processing and storing documents in the RAG system.

    Phase 4: File-based implementation using JSONL storage.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the DocumentIngester.

        Args:
            config: Optional configuration dictionary for ingestion settings.
        """
        self.config = config or {}
        self.chunk_size = self.config.get("chunk_size", 1000)
        self.chunk_overlap = self.config.get("chunk_overlap", 200)
        self._initialized = True
        logger.info("DocumentIngester initialized")

    def ingest(self, document: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ingest a document into the RAG system.

        Args:
            document: The document content to ingest.
            metadata: Optional metadata to associate with the document.

        Returns:
            Dictionary containing ingestion results.
        """
        metadata = metadata or {}
        doc_id = metadata.get("id", f"doc_{datetime.now(timezone.utc).timestamp()}")

        doc = {
            "id": doc_id,
            "text": document,
            "tags": metadata.get("tags", []),
        }

        result = ingest_documents([doc])

        return {
            "status": "success" if result["ingested_count"] > 0 else "error",
            "document_id": doc_id if result["ingested_count"] > 0 else None,
            "chunks_created": 1 if result["ingested_count"] > 0 else 0,
            "errors": result["errors"],
        }

    def ingest_batch(
        self,
        documents: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Ingest multiple documents in batch.

        Args:
            documents: List of document contents to ingest.
            metadata_list: Optional list of metadata dictionaries.

        Returns:
            Dictionary containing batch ingestion results.
        """
        metadata_list = metadata_list or [{} for _ in documents]

        docs = []
        for i, (doc_text, meta) in enumerate(zip(documents, metadata_list)):
            doc_id = meta.get("id", f"doc_{i}_{datetime.now(timezone.utc).timestamp()}")
            docs.append({
                "id": doc_id,
                "text": doc_text,
                "tags": meta.get("tags", []),
            })

        result = ingest_documents(docs)

        return {
            "status": "success" if result["ingested_count"] > 0 else "error",
            "documents_processed": result["ingested_count"],
            "total_chunks": result["ingested_count"],
            "errors": result["errors"],
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the ingested documents.

        Returns:
            Dictionary containing statistics about the RAG system.
        """
        stats = get_corpus_stats()
        return {
            "status": "active",
            "total_documents": stats["document_count"],
            "total_chunks": stats["document_count"],
            "storage_used": stats["file_size_bytes"],
        }


def ingest_document_stub(document: str) -> Dict[str, Any]:
    """
    Backward-compatible stub that uses the real implementation.

    Args:
        document: The document content to ingest.

    Returns:
        Dictionary containing ingestion results.
    """
    ingester = DocumentIngester()
    return ingester.ingest(document)
