"""
Veritas Logic Package

This package contains the core logic modules for truth auditing operations:
- auditor: Logical consistency and claim analysis
- bias_detector: Bias identification and analysis
- chain_validator: Chain-of-thought validation
- source_checker: Source verification and credibility assessment
"""

from app.logic.auditor import LogicAuditor, audit_text_stub
from app.logic.bias_detector import BiasDetector, detect_bias_stub
from app.logic.chain_validator import ChainValidator, validate_chain_stub
from app.logic.source_checker import SourceChecker, check_sources_stub

__all__ = [
    "LogicAuditor",
    "audit_text_stub",
    "BiasDetector",
    "detect_bias_stub",
    "ChainValidator",
    "validate_chain_stub",
    "SourceChecker",
    "check_sources_stub",
]
