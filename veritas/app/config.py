"""
Veritas Configuration Module

This module contains configuration settings for the Veritas truth auditing system.
Phase 8: Added feature flags, rate limits, and production controls.
"""

from typing import Any, Dict, Optional


# ============================================================================
# Feature Flags (Phase 8)
# ============================================================================

VERITAS_FEATURE_FLAGS: Dict[str, Any] = {
    "enable_rag": True,
    "enable_monitoring": True,
    "enable_reporting": True,
    "strict_mode": False,          # if True, reject ambiguous inputs
    "max_payload_size_kb": 64,
    "rate_limits": {
        "events_per_minute": 20,
        "tools_per_minute": 30
    }
}


def get_feature_flag(flag_name: str) -> Any:
    """
    Get a feature flag value.

    Args:
        flag_name: Name of the feature flag.

    Returns:
        Flag value, or None if not found.
    """
    return VERITAS_FEATURE_FLAGS.get(flag_name)


def is_feature_enabled(feature: str) -> bool:
    """
    Check if a feature is enabled.

    Args:
        feature: Feature name (rag, monitoring, reporting).

    Returns:
        True if enabled, False otherwise.
    """
    flag_name = f"enable_{feature}"
    return VERITAS_FEATURE_FLAGS.get(flag_name, False)


def get_rate_limit(action_type: str) -> int:
    """
    Get rate limit for an action type.

    Args:
        action_type: Type of action (events, tools).

    Returns:
        Rate limit per minute.
    """
    rate_limits = VERITAS_FEATURE_FLAGS.get("rate_limits", {})
    return rate_limits.get(f"{action_type}_per_minute", 100)


def get_max_payload_size_kb() -> int:
    """Get maximum payload size in KB."""
    return VERITAS_FEATURE_FLAGS.get("max_payload_size_kb", 64)


def is_strict_mode() -> bool:
    """Check if strict mode is enabled."""
    return VERITAS_FEATURE_FLAGS.get("strict_mode", False)


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
