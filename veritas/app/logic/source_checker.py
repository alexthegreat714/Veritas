"""
Veritas Source Checker Module

This module contains functionality for verifying and assessing
the credibility of information sources.

Phase 2: Deterministic heuristic-based implementation.
Uses URL validation and pattern matching only.
No external web requests or content fetching.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from logging.handlers import RotatingFileHandler


# Configure module logger
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = RotatingFileHandler(
        LOG_DIR / "source_checker.log",
        maxBytes=5_000_000,
        backupCount=3
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)


# Trusted domain patterns (high credibility)
TRUSTED_DOMAINS = {
    # Academic/Research
    r"\.edu$": 0.85,
    r"\.gov$": 0.80,
    r"\.ac\.[a-z]{2}$": 0.85,  # Academic domains (e.g., .ac.uk)
    r"arxiv\.org$": 0.80,
    r"pubmed\.": 0.85,
    r"nature\.com$": 0.85,
    r"science\.org$": 0.85,
    r"sciencedirect\.com$": 0.80,
    r"jstor\.org$": 0.85,
    r"springer\.com$": 0.80,
    r"wiley\.com$": 0.80,
    # Major news
    r"reuters\.com$": 0.75,
    r"apnews\.com$": 0.75,
    r"bbc\.(com|co\.uk)$": 0.70,
    r"npr\.org$": 0.70,
    # Reference
    r"wikipedia\.org$": 0.60,
    r"britannica\.com$": 0.75,
}

# Lower credibility domain patterns
LOWER_CREDIBILITY_DOMAINS = {
    r"\.blogspot\.": 0.35,
    r"\.wordpress\.com$": 0.40,
    r"medium\.com$": 0.45,
    r"reddit\.com$": 0.30,
    r"twitter\.com$": 0.30,
    r"x\.com$": 0.30,
    r"facebook\.com$": 0.25,
    r"tiktok\.com$": 0.20,
    r"youtube\.com$": 0.40,
}

# Citation patterns
CITATION_PATTERNS = [
    # APA style
    r"^[A-Z][a-z]+,\s+[A-Z]\.\s*(\([0-9]{4}\)|\d{4})\.",
    # MLA style
    r"^[A-Z][a-z]+,\s+[A-Z][a-z]+\.\s+\"",
    # Chicago style
    r"^[A-Z][a-z]+,\s+[A-Z][a-z]+\.\s+[0-9]{4}\.",
    # IEEE style
    r"^\[[0-9]+\]\s+[A-Z]\.\s+[A-Z][a-z]+",
    # DOI
    r"doi:\s*10\.\d{4,}",
    r"https?://doi\.org/10\.\d{4,}",
    # ISBN
    r"ISBN[:\s-]*[0-9-]{10,17}",
    # arXiv
    r"arXiv:\d{4}\.\d{4,5}",
]


def check_sources(sources: List[str]) -> Dict[str, Any]:
    """
    Check a list of sources for validity and credibility.

    Args:
        sources: List of URLs or references to check.

    Returns:
        Dictionary containing:
        - missing_sources: List of empty or None entries
        - unverifiable: List of invalid URLs or nonsense strings
        - conflicting: List of potential conflicts (placeholder)
        - ranked_confidence: List of sources with confidence scores (0-1)
    """
    logger.info(f"Checking {len(sources)} sources")
    logger.debug(f"Input sources: {sources}")

    if not sources:
        result = {
            "missing_sources": [],
            "unverifiable": [],
            "conflicting": [],
            "ranked_confidence": [],
        }
        logger.info(f"Output: {result}")
        return result

    missing_sources = []
    unverifiable = []
    ranked_confidence = []

    for i, source in enumerate(sources):
        # Check for missing/empty sources
        if source is None or (isinstance(source, str) and not source.strip()):
            missing_sources.append({
                "index": i,
                "reason": "empty_or_null",
            })
            continue

        source_str = str(source).strip()

        # Classify and score the source
        source_type, confidence, issues = _analyze_source(source_str)

        if source_type == "unverifiable":
            unverifiable.append({
                "index": i,
                "source": source_str,
                "issues": issues,
            })
        else:
            ranked_confidence.append({
                "index": i,
                "source": source_str,
                "type": source_type,
                "confidence": round(confidence, 3),
                "issues": issues,
            })

    # Sort by confidence (highest first)
    ranked_confidence.sort(key=lambda x: x["confidence"], reverse=True)

    # Detect potential conflicts (sources that might contradict)
    conflicting = _detect_conflicting_sources(ranked_confidence)

    result = {
        "missing_sources": missing_sources,
        "unverifiable": unverifiable,
        "conflicting": conflicting,
        "ranked_confidence": ranked_confidence,
    }

    logger.info(f"Check complete: {len(missing_sources)} missing, "
                f"{len(unverifiable)} unverifiable, {len(conflicting)} conflicting")
    logger.debug(f"Output: {result}")

    return result


def _analyze_source(source: str) -> tuple:
    """
    Analyze a source and return (type, confidence, issues).
    """
    issues = []

    # Check if it's a URL
    if _is_valid_url(source):
        source_type = "url"
        confidence, url_issues = _score_url(source)
        issues.extend(url_issues)
        return source_type, confidence, issues

    # Check if it's a citation
    if _is_citation(source):
        source_type = "citation"
        confidence = _score_citation(source)
        if confidence < 0.5:
            issues.append("incomplete_citation")
        return source_type, confidence, issues

    # Check if it's a DOI or arXiv reference
    if _is_doi_or_arxiv(source):
        source_type = "academic_reference"
        confidence = 0.80
        return source_type, confidence, issues

    # Check for book reference patterns
    if _is_book_reference(source):
        source_type = "book_reference"
        confidence = 0.65
        return source_type, confidence, issues

    # If it's a reasonably formatted text reference
    if _is_text_reference(source):
        source_type = "text_reference"
        confidence = 0.40
        issues.append("unstructured_reference")
        return source_type, confidence, issues

    # Otherwise unverifiable
    source_type = "unverifiable"
    confidence = 0.0
    issues.append("invalid_format")

    return source_type, confidence, issues


def _is_valid_url(source: str) -> bool:
    """Check if source is a valid URL format."""
    try:
        result = urlparse(source)
        return all([
            result.scheme in ('http', 'https', 'ftp'),
            result.netloc,
            len(result.netloc) > 3,
            '.' in result.netloc,
        ])
    except Exception:
        return False


def _score_url(url: str) -> tuple:
    """Score a URL based on domain credibility. Returns (score, issues)."""
    issues = []

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]

        # Check trusted domains
        for pattern, score in TRUSTED_DOMAINS.items():
            if re.search(pattern, domain):
                return score, issues

        # Check lower credibility domains
        for pattern, score in LOWER_CREDIBILITY_DOMAINS.items():
            if re.search(pattern, domain):
                issues.append("lower_credibility_platform")
                return score, issues

        # Default scoring based on URL structure
        score = 0.50  # Base score for unknown domains

        # Boost for HTTPS
        if parsed.scheme == 'https':
            score += 0.05

        # Check for suspicious patterns
        if re.search(r'\d{5,}', domain):
            issues.append("suspicious_numeric_domain")
            score -= 0.15

        if len(domain) > 50:
            issues.append("unusually_long_domain")
            score -= 0.10

        if domain.count('.') > 4:
            issues.append("excessive_subdomains")
            score -= 0.10

        # Check path for credibility indicators
        path = parsed.path.lower()
        if any(x in path for x in ['/research', '/publications', '/journal', '/paper']):
            score += 0.10

        if any(x in path for x in ['/blog', '/opinion', '/editorial']):
            issues.append("opinion_content")
            score -= 0.05

        return max(0.1, min(0.9, score)), issues

    except Exception:
        issues.append("url_parse_error")
        return 0.2, issues


def _is_citation(source: str) -> bool:
    """Check if source matches citation patterns."""
    for pattern in CITATION_PATTERNS:
        if re.search(pattern, source, re.IGNORECASE):
            return True
    return False


def _score_citation(source: str) -> float:
    """Score a citation based on completeness."""
    score = 0.50  # Base score

    # Check for author name
    if re.search(r'^[A-Z][a-z]+', source):
        score += 0.10

    # Check for year
    if re.search(r'\b(19|20)\d{2}\b', source):
        score += 0.10

    # Check for title (quoted or italicized pattern)
    if re.search(r'\"[^\"]+\"', source) or re.search(r'_[^_]+_', source):
        score += 0.10

    # Check for publication info
    if re.search(r'\b(journal|proceedings|conference|press|publisher)\b', source, re.IGNORECASE):
        score += 0.10

    # Check for page numbers
    if re.search(r'pp?\.\s*\d+', source):
        score += 0.05

    # Check for DOI
    if re.search(r'doi', source, re.IGNORECASE):
        score += 0.10

    return min(1.0, score)


def _is_doi_or_arxiv(source: str) -> bool:
    """Check if source is a DOI or arXiv reference."""
    doi_pattern = r'(doi:\s*)?10\.\d{4,}/[^\s]+'
    arxiv_pattern = r'arXiv:\d{4}\.\d{4,5}'

    return bool(re.search(doi_pattern, source, re.IGNORECASE) or
                re.search(arxiv_pattern, source, re.IGNORECASE))


def _is_book_reference(source: str) -> bool:
    """Check if source appears to be a book reference."""
    # Check for ISBN
    if re.search(r'ISBN', source, re.IGNORECASE):
        return True

    # Check for publisher patterns
    if re.search(r'\b(press|publishers?|publishing|books?)\b', source, re.IGNORECASE):
        # Also should have author and title patterns
        if re.search(r'^[A-Z][a-z]+', source) and len(source) > 30:
            return True

    return False


def _is_text_reference(source: str) -> bool:
    """Check if source is a reasonably formatted text reference."""
    # Must be reasonable length
    if len(source) < 10 or len(source) > 1000:
        return False

    # Should start with capital letter
    if not source[0].isupper():
        return False

    # Should have multiple words
    words = source.split()
    if len(words) < 3:
        return False

    # Should not be random characters
    alpha_ratio = sum(c.isalpha() for c in source) / len(source)
    if alpha_ratio < 0.5:
        return False

    return True


def _detect_conflicting_sources(ranked_sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect potential conflicts between sources.
    Without content fetching, we can only detect structural conflicts.
    """
    conflicts = []

    # Check for duplicate URLs with different scores (shouldn't happen, but check)
    seen_domains = {}
    for source in ranked_sources:
        if source["type"] == "url":
            try:
                parsed = urlparse(source["source"])
                domain = parsed.netloc.lower()
                if domain in seen_domains:
                    # Same domain appears multiple times
                    conflicts.append({
                        "source_1_index": seen_domains[domain]["index"],
                        "source_2_index": source["index"],
                        "type": "duplicate_domain",
                        "domain": domain,
                    })
                else:
                    seen_domains[domain] = source
            except Exception:
                pass

    return conflicts


class SourceChecker:
    """
    Source Checker for verifying and assessing information sources.

    This class provides comprehensive source verification capabilities including:
    - Source credibility assessment
    - URL validation and domain reputation
    - Citation format validation
    - Confidence scoring

    Phase 2: Deterministic heuristic-based implementation.
    No external web requests - uses pattern matching only.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the SourceChecker.

        Args:
            config: Optional configuration dictionary for checker settings.
        """
        self.config = config or {}
        self.timeout = self.config.get("timeout", 30)
        self.max_sources = self.config.get("max_sources", 10)
        self._initialized = True
        logger.info("SourceChecker initialized")

    def check(self, sources: List[str], claims: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Check a list of sources for credibility.

        Args:
            sources: List of source URLs or references to check.
            claims: Optional list of claims (not used without content fetching).

        Returns:
            Dictionary containing check results.
        """
        result = check_sources(sources)

        # Add verified/unverified categorization
        verified = [s for s in result["ranked_confidence"] if s["confidence"] >= 0.5]
        unverified = [s for s in result["ranked_confidence"] if s["confidence"] < 0.5]

        # Create credibility scores dict
        credibility_scores = {
            s["source"]: s["confidence"]
            for s in result["ranked_confidence"]
        }

        # Generate warnings
        warnings = self._generate_warnings(result)

        return {
            "verified_sources": [s["source"] for s in verified],
            "unverified_sources": (
                [s["source"] for s in unverified] +
                [u["source"] for u in result["unverifiable"]]
            ),
            "credibility_scores": credibility_scores,
            "claim_verification": [],  # Requires content fetching
            "warnings": warnings,
            "details": result,
        }

    def _generate_warnings(self, result: Dict[str, Any]) -> List[str]:
        """Generate warnings based on source analysis."""
        warnings = []

        if result["missing_sources"]:
            warnings.append(f"{len(result['missing_sources'])} source(s) are empty or missing")

        if result["unverifiable"]:
            warnings.append(f"{len(result['unverifiable'])} source(s) could not be verified")

        if result["conflicting"]:
            warnings.append(f"{len(result['conflicting'])} potential conflict(s) detected")

        # Check for low overall credibility
        if result["ranked_confidence"]:
            avg_confidence = sum(s["confidence"] for s in result["ranked_confidence"]) / len(result["ranked_confidence"])
            if avg_confidence < 0.4:
                warnings.append("Average source credibility is low")

        # Check for sources with issues
        sources_with_issues = [s for s in result["ranked_confidence"] if s["issues"]]
        if sources_with_issues:
            warnings.append(f"{len(sources_with_issues)} source(s) have potential issues")

        return warnings

    def assess_credibility(self, source: str) -> Dict[str, Any]:
        """
        Assess the credibility of a single source.

        Args:
            source: URL or reference to assess.

        Returns:
            Dictionary containing credibility assessment.
        """
        source_type, confidence, issues = _analyze_source(source)

        # Get domain reputation if URL
        domain_reputation = None
        if source_type == "url" and _is_valid_url(source):
            try:
                parsed = urlparse(source)
                domain = parsed.netloc.lower()
                if domain.startswith('www.'):
                    domain = domain[4:]

                # Check against known domains
                for pattern, score in TRUSTED_DOMAINS.items():
                    if re.search(pattern, domain):
                        domain_reputation = "trusted"
                        break
                for pattern, score in LOWER_CREDIBILITY_DOMAINS.items():
                    if re.search(pattern, domain):
                        domain_reputation = "lower_credibility"
                        break
                if domain_reputation is None:
                    domain_reputation = "unknown"
            except Exception:
                domain_reputation = "unknown"

        return {
            "credibility_score": round(confidence, 3),
            "source_type": source_type,
            "factors": issues if issues else ["no_issues_detected"],
            "domain_reputation": domain_reputation,
            "known_issues": issues,
        }

    def verify_claim(self, claim: str, sources: List[str]) -> Dict[str, Any]:
        """
        Verify a claim against provided sources.

        Note: Without content fetching, this only validates source credibility.

        Args:
            claim: The claim to verify.
            sources: List of sources.

        Returns:
            Dictionary containing verification results.
        """
        # Without content fetching, we can only assess source credibility
        result = check_sources(sources)

        credible_sources = [
            s["source"] for s in result["ranked_confidence"]
            if s["confidence"] >= 0.6
        ]

        return {
            "is_verified": None,  # Cannot verify without content
            "supporting_sources": [],  # Would require content analysis
            "contradicting_sources": [],  # Would require content analysis
            "credible_sources_count": len(credible_sources),
            "confidence": None,
            "note": "Content verification requires external API access",
        }

    def cross_reference(self, claim: str) -> Dict[str, Any]:
        """
        Cross-reference a claim (placeholder - requires external access).

        Args:
            claim: The claim to cross-reference.

        Returns:
            Dictionary indicating feature unavailability.
        """
        return {
            "sources_checked": 0,
            "agreement_ratio": None,
            "sources": [],
            "consensus": None,
            "note": "Cross-referencing requires external API access",
        }

    def check_citation(self, citation: str) -> Dict[str, Any]:
        """
        Validate a citation for format accuracy.

        Args:
            citation: The citation to validate.

        Returns:
            Dictionary containing citation validation results.
        """
        is_citation = _is_citation(citation)
        score = _score_citation(citation) if is_citation else 0.0

        # Parse citation components
        parsed_info = {}
        issues = []

        # Extract author
        author_match = re.match(r'^([A-Z][a-z]+(?:,\s*[A-Z]\.?)?)', citation)
        if author_match:
            parsed_info["author"] = author_match.group(1)
        else:
            issues.append("missing_or_unclear_author")

        # Extract year
        year_match = re.search(r'\b(19|20)\d{2}\b', citation)
        if year_match:
            parsed_info["year"] = year_match.group(0)
        else:
            issues.append("missing_year")

        # Extract DOI if present
        doi_match = re.search(r'(10\.\d{4,}/[^\s]+)', citation)
        if doi_match:
            parsed_info["doi"] = doi_match.group(1)

        return {
            "is_valid": is_citation and score >= 0.5,
            "is_accessible": None,  # Would require fetching
            "format_score": round(score, 3),
            "parsed_info": parsed_info,
            "issues": issues,
        }

    def get_source_report(self, source: str) -> Dict[str, Any]:
        """
        Generate a comprehensive report for a single source.

        Args:
            source: The source to generate a report for.

        Returns:
            Dictionary containing source analysis report.
        """
        credibility = self.assess_credibility(source)

        return {
            "source": source,
            "credibility": credibility,
            "recommendation": self._get_source_recommendation(credibility),
        }

    def _get_source_recommendation(self, credibility: Dict[str, Any]) -> str:
        """Generate recommendation based on credibility assessment."""
        score = credibility["credibility_score"]

        if score >= 0.8:
            return "High credibility source - suitable for primary reference"
        elif score >= 0.6:
            return "Moderate credibility - verify with additional sources"
        elif score >= 0.4:
            return "Lower credibility - use with caution, seek corroboration"
        else:
            return "Low credibility - not recommended as primary source"


def check_sources_stub(sources: List[str]) -> Dict[str, Any]:
    """
    Backward-compatible stub that calls the real implementation.

    Args:
        sources: List of sources to check.

    Returns:
        Dictionary containing source check results.
    """
    return check_sources(sources)
