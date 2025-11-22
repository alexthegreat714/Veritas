"""
Veritas Configuration Module

This module contains configuration settings for the Veritas truth auditing system.
Phase 1: Placeholder configuration settings.
"""

from typing import Optional


class VeritasConfig:
    """
    Configuration class for Veritas system settings.

    Attributes:
        app_name: Name of the application
        version: Current version of Veritas
        debug: Enable debug mode
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        rag_enabled: Whether RAG functionality is enabled
        max_text_length: Maximum text length for audit operations
        bias_threshold: Threshold for bias detection sensitivity
        source_timeout: Timeout in seconds for source checking operations
    """

    app_name: str = "Veritas"
    version: str = "0.1.0"
    debug: bool = True
    log_level: str = "INFO"

    # RAG Configuration
    rag_enabled: bool = False
    embedding_model: Optional[str] = None
    vector_store_path: str = "app/memory/long"

    # Auditor Configuration
    max_text_length: int = 100000
    bias_threshold: float = 0.7

    # Source Checker Configuration
    source_timeout: int = 30
    max_sources_per_check: int = 10

    # Chain Validator Configuration
    max_chain_depth: int = 50

    # Memory Configuration
    short_term_memory_path: str = "app/memory/short"
    long_term_memory_path: str = "app/memory/long"

    # Logging Configuration
    log_path: str = "app/logs"


# Global configuration instance
config = VeritasConfig()
