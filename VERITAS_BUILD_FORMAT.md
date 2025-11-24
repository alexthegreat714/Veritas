# Veritas Agent Build Format & Phase Breakdown

## Overview

This document details the structured format and methodology used to build **Veritas**, the AI Senate Truth Auditor. The build follows a phased, incremental approach where each phase adds specific capabilities while maintaining backwards compatibility and comprehensive test coverage.

---

## Build Format & Philosophy

### Core Principles

1. **Phased Implementation**: Each phase is a complete, testable unit
2. **Deterministic Logic**: All analysis is rule-based, no ML models
3. **Test-Driven Development**: Every phase includes comprehensive tests (typically 40-100+ tests per phase)
4. **Backwards Compatibility**: New phases never break existing functionality
5. **Structured Output**: All APIs return consistent JSON schemas using Pydantic models
6. **Audit Trail**: All operations are logged for transparency
7. **Advisory Only**: Veritas never takes autonomous actions - it only analyzes and reports

### Standard Phase Structure

Each phase follows this pattern:

```
Phase N: [Name]
├── Core Files
│   ├── Logic/Engine Implementation (e.g., brain.py, dispute_engine.py)
│   ├── API Routes (added to routes/veritas.py)
│   ├── Tool Registry Functions (added to tools/__init__.py)
│   └── Pydantic Schemas (added to schemas.py)
├── Tests
│   ├── Unit tests (e.g., test_brain.py)
│   ├── Integration tests (e.g., test_events.py)
│   └── Endpoint tests (e.g., test_endpoints.py)
├── Documentation
│   └── README updates with usage examples
└── Validation
    └── All tests pass (100% of existing + new tests)
```

### File Organization

```
veritas/
├── app/
│   ├── main.py              # FastAPI entry point + global handlers
│   ├── config.py            # Configuration + feature flags
│   ├── schemas.py           # Pydantic models
│   ├── routes/veritas.py    # All API endpoints
│   ├── logic/               # Core analysis engines
│   │   ├── brain.py         # Main orchestration
│   │   ├── auditor.py       # Logic auditing
│   │   ├── bias_detector.py # Bias detection
│   │   ├── chain_validator.py # Chain validation
│   │   ├── source_checker.py  # Source verification
│   │   └── legislative.py   # Legislative functions
│   ├── rag/                 # Memory/RAG system
│   │   ├── ingest.py
│   │   └── query.py
│   ├── tools/               # Tool registry
│   │   └── __init__.py
│   ├── monitoring_engine.py # Monitoring/drift detection
│   ├── trend_engine.py      # Long-term analytics
│   ├── reporting.py         # Report generation
│   ├── dispute_engine.py    # Dispute resolution
│   ├── error_handler.py     # Exception handling
│   ├── utils.py             # Utilities (validation, rate limiting)
│   └── memory/
│       └── long_term/       # Persistent storage
│           ├── audits/
│           ├── disputes/
│           └── monitoring/
│               └── reports/
└── tests/
    ├── test_[feature].py    # One test file per major feature
    └── conftest.py          # Shared fixtures
```

---

## Phase Breakdown

### Phase 1-2: Core Analysis Tools

**Purpose**: Foundation - Individual analysis tools without orchestration

**Components Added**:
- Logic Auditor (`auditor.py`) - Detects 10 fallacy types
- Bias Detector (`bias_detector.py`) - 4 bias types (political, emotional, motivational, certainty)
- Chain Validator (`chain_validator.py`) - Reasoning chain validation
- Source Checker (`source_checker.py`) - URL credibility scoring

**API Endpoints**:
- `POST /audit_text`
- `POST /detect_bias`
- `POST /validate_chain`
- `POST /check_sources`

**Key Features**:
- Regex-based pattern matching
- Heuristic word lists (e.g., political keywords, emotional intensifiers)
- Deterministic scoring (0.0-1.0 normalized)
- No external API calls

**Tests**: ~40 tests covering each tool independently

**Philosophy**: Build individual tools that are completely self-contained and testable before orchestration.

---

### Phase 3: VeritasBrain - Central Orchestration

**Purpose**: Intelligent task routing and result synthesis

**Components Added**:
- `VeritasBrain` class (`logic/brain.py`)
- Task classification system
- Memory retrieval integration (stub)
- Result synthesis with issue detection
- Contribution logging

**API Endpoints**:
- `POST /run_task` - Main brain endpoint

**Key Features**:
- Automatic task type detection (audit_text, validate_chain, check_sources, composite_audit)
- Multi-tool orchestration (runs multiple tools in one request)
- Summary generation with `has_major_issues` flag
- Issue thresholds (e.g., bias > 0.6, 2+ fallacies)

**Task Types**:
| Type | Triggered By | Tools Run |
|------|--------------|-----------|
| `audit_text` | `text` field only | Auditor + Bias Detector |
| `validate_chain` | `steps` or `chain` | Chain Validator |
| `check_sources` | `sources` field | Source Checker |
| `composite_audit` | Multiple fields | All relevant tools |

**Tests**: ~60 tests including task classification, orchestration, and edge cases

**Philosophy**: Create a central brain that intelligently routes requests to the right tools and synthesizes results.

---

### Phase 4: RAG & Memory System

**Purpose**: Give Veritas memory capabilities for context-aware analysis

**Components Added**:
- Document ingestion (`rag/ingest.py`)
- Embedding system (`rag/query.py`)
- JSONL corpus storage (`memory/long/veritas_corpus.jsonl`)
- Cosine similarity search
- `RAGQuery` class

**API Endpoints**:
- `POST /ingest_docs`
- `POST /clear_corpus`
- `GET /corpus_stats`

**Key Features**:
- Deterministic embeddings (hashed bag-of-words, 128 dimensions)
- Polynomial rolling hash for token→vector mapping
- TF-like weighting with L2 normalization
- Top-k retrieval with similarity threshold
- Hybrid keyword + semantic search

**VeritasBrain Integration**:
- Automatic memory retrieval during analysis
- Context injection into results (`memory_context` field)
- Query construction from payload (topic > text > context > steps)

**Tests**: ~80 tests covering ingestion, embeddings, similarity, and brain integration

**Philosophy**: Enable context-aware analysis without ML models - use deterministic, rule-based embeddings.

---

### Phase 5: Event API for Inter-Agent Communication

**Purpose**: Standardized interface for other agents to request analysis

**Components Added**:
- `VeritasEvent` Pydantic schema
- `VeritasResponse` Pydantic schema
- `handle_event()` method in VeritasBrain
- Event type routing

**API Endpoints**:
- `POST /event` - Main event API

**Supported Event Types**:
| Event Type | Payload Fields | Used By |
|------------|----------------|---------|
| `audit-request` | `text` | Sky |
| `bill-logic-check` | `bill_text` or `text` | Congress, Bill Engine |
| `argument-integrity-check` | `steps` or `chain` | Apollo, Mercury, Aero |
| `source-integrity-check` | `sources` | Any agent |
| `composite-audit` | Any combination | Sky (complex cases) |

**Key Features**:
- Correlation ID support for tracing
- Consistent response format
- Source agent tracking
- Unknown event type handling

**Tests**: ~50 tests covering all event types and error handling

**Philosophy**: Create a standardized contract for inter-agent communication with clear schemas.

---

### Phase 6: Legislative Functions

**Purpose**: Enable Veritas to participate in Senate legislative processes

**Components Added**:
- `vote_on_bill()` function (`logic/legislative.py`)
- `adversarial_contribution()` function (`logic/legislative.py`)
- `LegislativeHandler` class
- Legislative contribution logging

**API Endpoints**:
- `POST /vote_on_bill`
- `POST /adversarial_contribution`

**Event Types Added**:
- `bill-vote-request`
- `bill-adversarial-request`

**Key Features**:
- Vote values: `yes`, `no`, `abstain`
- Vote based strictly on logic, not policy
- Devil's advocate analysis for groupthink prevention
- Confidence scoring (0.0-1.0)
- Risk flags and hidden assumption detection

**Vote Thresholds**:
| Vote | Condition |
|------|-----------|
| `yes` | Minimal or no logical issues |
| `no` | Contradictions, high bias, multiple fallacies |
| `abstain` | Text too short, unclear, insufficient evidence |

**Tests**: ~45 tests covering voting logic, adversarial analysis, and edge cases

**Philosophy**: Participate in governance by adjudicating logic, not policy - no moral/cost/political evaluation.

---

### Phase 7: Congress Integration & Structured Schema

**Purpose**: Dedicated Congress API with standardized output schemas

**Components Added**:
- `AuditResult` Pydantic model
- `AuditWithSourcesResult` Pydantic model
- `CongressReviewResult` Pydantic model
- `tool_review_bill()` function
- `tool_review_statement()` function
- Tool registry system

**API Endpoints**:
- `POST /event/congress` - Dedicated Congress endpoint

**Event Types**:
| Event Type | Description | Response Schema |
|------------|-------------|-----------------|
| `bill_for_review` | Review a bill | `CongressReviewResult` |
| `statement_for_audit` | Audit a statement | `CongressReviewResult` |

**Key Features**:
- Structured schemas with consistent fields
- Recommendation values: `approve`, `revise`, `reject`
- Constitutional boundary checks (advisory disclaimers)
- Source validation integration
- RAG context retrieval

**Tool Registry**:
```python
from app.tools import registry

# List tools
registry.list_tools()  # ['review_bill', 'review_statement', ...]

# Invoke tool
registry.invoke("review_bill", {"bill_id": "...", "text": "..."})
```

**Tests**: ~70 tests covering schemas, tools, and Congress endpoint

**Philosophy**: Provide Congress with structured, consistent responses that are clearly marked as advisory only.

---

### Phase 8: Dispute Resolution (Non-Judicial)

**Purpose**: Classify and analyze disputes between agents

**Components Added**:
- `parse_dispute()` function (`dispute_engine.py`)
- `DisputeEngine` class
- Escalation classification logic
- Dispute storage system (`app/memory/long_term/disputes/`)

**API Endpoints**:
- `POST /event/congress` with `dispute_for_analysis` event type

**Event Types Added**:
- `dispute_for_analysis`

**Key Features**:
- Factual vs. interpretation disagreement detection
- Contradiction detection with negation patterns
- Escalation targets: `sophia` (ethics), `aegis` (security), `congress` (governance)
- Recommendation values: `forward_to_sophia`, `forward_to_aegis`, `mediation_by_congress`, etc.

**Escalation Detection**:
| Target | Keywords |
|--------|----------|
| `sophia` | ethics, rights, justice, law, discrimination, privacy |
| `aegis` | security, threat, vulnerability, danger, attack, risk |
| `congress` | policy, budget, legislation, authority, regulation |

**Important**: Veritas does NOT escalate events - it only classifies and reports.

**Tests**: ~55 tests covering dispute parsing, escalation, and storage

**Philosophy**: Classify disputes by domain expertise needed, but never actually escalate or intervene.

---

### Phase 9: Automated Monitoring & Drift Detection

**Purpose**: Continuous evaluation of agent outputs to detect quality degradation

**Components Added**:
- `detect_logical_drift()` function (`monitoring_engine.py`)
- `analyze_bias_trends()` function
- `detect_anomalies()` function
- `run_monitoring_cycle()` orchestration
- `MonitoringEngine` class
- Audit storage system (`app/memory/long_term/audits/`)
- Monitoring snapshot storage

**API Endpoints**:
- `POST /event/congress` with `monitoring_cycle` event type

**Event Types Added**:
- `monitoring_cycle`

**Key Features**:
- Logical drift detection (30% increase threshold)
- Bias trend analysis (30% rise threshold)
- Statistical anomaly detection (>2 std dev)
- Overall status: `stable`, `warning`, `critical`
- Historical snapshot storage

**Monitoring Components**:
| Component | Metrics | Threshold |
|-----------|---------|-----------|
| Logical Drift | Fallacies, inconsistencies, contradictions | 30% increase |
| Bias Trends | Emotional, political, certainty, motivational | 30% rise |
| Anomaly Detection | Issue count deviations | 2σ |

**Important**: Veritas monitors only - never intervenes or takes autonomous actions.

**Tests**: ~85 tests covering drift, trends, anomalies, and storage

**Philosophy**: Detect quality degradation early through statistical analysis, but report only - never intervene.

---

### Phase 10: Long-Term Trend Analytics & Reporting

**Purpose**: Governance-grade reports with performance metrics and trend analysis

**Components Added**:
- `load_all_audits()` function (`trend_engine.py`)
- `compute_bias_over_time()` function
- `compute_logic_issue_trends()` function
- `compute_source_reliability_trends()` function
- `compute_performance_score()` function
- `TrendEngine` class
- `generate_full_veritas_report()` function (`reporting.py`)
- `ReportingEngine` class
- `VeritasReport` Pydantic schema
- Report storage system

**API Endpoints**:
- `POST /event/congress` with `generate_veritas_report` event type

**Event Types Added**:
- `generate_veritas_report`

**Key Features**:
- Weekly time buckets for trend analysis
- Linear regression slopes for trend detection
- Performance score (0-100) with letter grades (A/B/C/D)
- Subsystem grades: bias_analysis, logic_analysis, source_validation, monitoring_stability
- Chart-ready data structures for visualization
- Advisory recommendations based on trends

**Performance Score Penalties**:
| Condition | Penalty |
|-----------|---------|
| Strong upward bias trend (slope > 0.1) | -15 |
| Strong contradiction trend (slope > 0.1) | -20 |
| Fallacy trend increase (slope > 0.1) | -10 |
| Declining source support (slope < -0.05) | -10 |
| Critical monitoring status | -25 |

**Report Sections**:
1. `meta`: Agent info, version, timestamp
2. `trends`: Bias trends, logic trends, source trends
3. `monitoring`: Current monitoring status
4. `performance`: Score, grades, stability index, penalties
5. `chart_data`: Arrays for visualization
6. `summary`: Executive summary
7. `recommendations`: Advisory recommendations
8. `storage`: Storage metadata

**Important**: All reports are informational - no autonomous actions triggered.

**Tests**: ~95 tests covering trends, performance scoring, reporting, and storage

**Philosophy**: Provide comprehensive, governance-grade insights for decision-making without triggering any autonomous actions.

---

### Phase 11: Production Hardening

**Purpose**: Add error boundaries, rate limiting, and security controls for production stability

**Components Added**:
- Custom exception hierarchy (`error_handler.py`)
  - `VeritasError` (base class)
  - `InvalidPayloadError`, `ToolExecutionError`, `MemoryAccessError`
  - `RAGSafetyError`, `RateLimitError`, `PayloadSizeError`, `FeatureDisabledError`
- Feature flags system (`config.py`)
  - `VERITAS_FEATURE_FLAGS` dictionary
  - `is_feature_enabled()`, `get_rate_limit()`, `get_max_payload_size_kb()`
- Payload validation and rate limiting (`utils.py`)
  - `enforce_payload_size()` (max 64KB)
  - `enforce_rate_limit()` (20 events/min, 30 tools/min)
  - Rolling window rate limiting with 60-second window
- RAG safety layer (`rag/query.py`)
  - `risky_query_detected()` - Pattern-based detection
  - `sanitize_rag_query()` - Query sanitization
  - Blocks: file paths, code execution, SQL injection, script tags
- Global exception handlers (`main.py`)
  - Structured JSON error responses
  - No stack traces exposed

**Key Changes**:
- All tools check feature flags before execution
- All endpoints enforce rate limits and payload size
- RAG queries checked for malicious patterns
- `/status` endpoint expanded with feature flags and rate limits

**Feature Flags**:
```python
VERITAS_FEATURE_FLAGS = {
    "enable_rag": True,
    "enable_monitoring": True,
    "enable_reporting": True,
    "strict_mode": False,
    "max_payload_size_kb": 64,
    "rate_limits": {
        "events_per_minute": 20,
        "tools_per_minute": 30
    }
}
```

**RAG Safety Patterns**:
```python
RISKY_PATTERNS = [
    r'[/\\](?:etc|var|home|root|usr|tmp)',  # File paths
    r'\bexec\s*\(',                          # Code execution
    r'\b(?:SELECT|INSERT|UPDATE|DELETE)\b', # SQL injection
    r'<script[^>]*>',                        # Script tags
]
```

**Important**: Phase 11 adds NO new intelligence - purely stability and security controls.

**Tests**: ~74 new tests covering errors, rate limits, feature flags, payload size, and status

**Philosophy**: Harden for production without changing analysis behavior - add protective boundaries only.

---

## Implementation Methodology

### Step-by-Step Phase Implementation

1. **Plan the Phase**
   - Define clear objectives
   - Identify components to add/modify
   - Design API contracts (Pydantic schemas)
   - Determine test coverage needs

2. **Implement Core Logic**
   - Create new modules (e.g., `dispute_engine.py`)
   - Add functions with clear responsibilities
   - Include logging for all operations
   - Document with docstrings

3. **Add API Endpoints**
   - Update `routes/veritas.py`
   - Define Pydantic request/response models
   - Add to tool registry if applicable
   - Implement error handling

4. **Write Comprehensive Tests**
   - Unit tests for each function
   - Integration tests for workflows
   - Edge case coverage
   - Error handling tests
   - Aim for 40-100+ tests per phase

5. **Update Documentation**
   - Add phase to README roadmap
   - Document API endpoints with examples
   - Explain use cases and agent conventions
   - Include disclaimers (advisory only, no intervention)

6. **Validate**
   - Run full test suite (all existing + new tests)
   - Check backwards compatibility
   - Verify no regressions
   - Confirm 100% pass rate

7. **Commit**
   - Clear commit message describing phase
   - List all components added/modified
   - Reference test pass rate

### Test-Driven Development Pattern

```python
# Step 1: Write the test first
def test_feature():
    result = new_feature(input)
    assert result["ok"] == True
    assert "expected_field" in result

# Step 2: Implement to make test pass
def new_feature(input):
    # Implementation
    return {"ok": True, "expected_field": "value"}

# Step 3: Add more tests for edge cases
def test_feature_edge_case():
    result = new_feature(edge_input)
    assert result["ok"] == False
    assert "error" in result
```

### Backwards Compatibility Guidelines

- Never remove existing fields from responses
- Add new fields as optional
- Maintain existing endpoint behavior
- Add new endpoints rather than modifying existing ones
- Version schemas when breaking changes needed
- Test all existing endpoints after each phase

---

## Key Design Patterns

### 1. Engine Pattern
```python
class EngineClass:
    def __init__(self):
        self.logger = setup_logger()

    def main_method(self, params):
        # Validation
        # Processing
        # Logging
        # Return structured result
```

**Examples**: `VeritasBrain`, `DisputeEngine`, `MonitoringEngine`, `TrendEngine`, `ReportingEngine`

### 2. Tool Registry Pattern
```python
TOOLS = {
    "tool_name": {
        "description": "What it does",
        "params": ["param1", "param2"],
        "handler": tool_function
    }
}

def invoke(tool_name, params):
    return TOOLS[tool_name]["handler"](**params)
```

### 3. Event Handler Pattern
```python
def handle_event(event: VeritasEvent) -> VeritasResponse:
    if event.event_type == "type1":
        result = handle_type1(event.payload)
    elif event.event_type == "type2":
        result = handle_type2(event.payload)
    else:
        result = {"error": "Unknown event type"}

    return VeritasResponse(
        ok=True,
        event_type=event.event_type,
        result=result
    )
```

### 4. Storage Pattern
```python
def store_item(item, category):
    timestamp = datetime.now(timezone.utc)
    file_id = f"{category}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
    file_path = f"app/memory/long_term/{category}/{file_id}.json"

    with open(file_path, "w") as f:
        json.dump(item, f, indent=2)

    return {"stored": True, "file_path": file_path, "id": file_id}
```

---

## Testing Strategy

### Test Categories

1. **Unit Tests**
   - Individual functions in isolation
   - Mock external dependencies
   - Test all code paths
   - Example: `test_brain.py`, `test_dispute_engine.py`

2. **Integration Tests**
   - Multiple components working together
   - Real database/file operations
   - End-to-end workflows
   - Example: `test_event_handlers.py`

3. **Endpoint Tests**
   - API contract validation
   - Request/response schemas
   - HTTP status codes
   - Example: `test_endpoints.py`

4. **Edge Case Tests**
   - Empty inputs
   - Malformed data
   - Boundary conditions
   - Error scenarios

### Test Coverage Requirements

- **Minimum**: 80% code coverage
- **Target**: 90%+ code coverage
- **Critical paths**: 100% coverage (voting, dispute classification, scoring)

### Test Fixtures (conftest.py)

```python
@pytest.fixture
def sample_audit():
    """Reusable audit result for tests"""
    return {
        "claims": [...],
        "logical_fallacies": [...],
        "inconsistencies": [],
        "unsupported_jumps": [...]
    }

@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Reset rate state before each test"""
    reset_rate_state()
    yield
    reset_rate_state()
```

---

## Logging Strategy

### Log Levels

- **INFO**: Normal operations (e.g., task received, tool invoked)
- **WARNING**: Unusual but handled (e.g., missing data, low confidence)
- **ERROR**: Failures requiring attention (e.g., storage error, invalid input)

### Log Files

```
app/logs/
├── veritas_brain.log                # Brain operations
├── veritas_contributions.log        # Analysis audit trail
├── veritas_legislative.log          # Legislative operations
├── veritas_legislative_contributions.log  # Legislative audit trail
├── rag_query.log                    # RAG operations
├── memory_utils.log                 # Memory storage
├── monitoring_engine.log            # Monitoring
├── trend_engine.log                 # Trend analysis
└── reporting.log                    # Report generation
```

### Logging Pattern

```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler("app/logs/module.log")
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(handler)

# Usage
logger.info(f"Processing task: {task_type}")
logger.warning(f"Low confidence: {confidence}")
logger.error(f"Failed to store: {error}")
```

---

## Configuration Management

### Environment-Based Config

```python
# config.py
import os

# Development vs. Production
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Feature flags
VERITAS_FEATURE_FLAGS = {
    "enable_rag": os.getenv("ENABLE_RAG", "true").lower() == "true",
    "enable_monitoring": os.getenv("ENABLE_MONITORING", "true").lower() == "true",
    "strict_mode": os.getenv("STRICT_MODE", "false").lower() == "true",
    "max_payload_size_kb": int(os.getenv("MAX_PAYLOAD_KB", "64")),
}

# Rate limits
RATE_LIMITS = {
    "events_per_minute": int(os.getenv("EVENTS_PER_MIN", "20")),
    "tools_per_minute": int(os.getenv("TOOLS_PER_MIN", "30")),
}
```

---

## API Design Principles

### 1. Consistent Response Format

```json
{
  "ok": true,
  "event_type": "audit-request",
  "correlation_id": "trace-123",
  "result": {
    "task_type": "audit_text",
    "summary": {...},
    "details": {...}
  }
}
```

### 2. Error Response Format

```json
{
  "ok": false,
  "error": "Rate limit exceeded",
  "error_type": "rate_limit_error",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "details": {
    "limit": 20,
    "window": "1 minute"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 3. Pydantic Schema Usage

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class EventRequest(BaseModel):
    event_type: str = Field(..., description="Type of analysis")
    source: str = Field(..., description="Requesting agent")
    payload: Dict[str, Any] = Field(..., description="Task data")
    correlation_id: Optional[str] = Field(None, description="Trace ID")

class EventResponse(BaseModel):
    ok: bool
    event_type: str
    correlation_id: Optional[str]
    result: Dict[str, Any]
```

---

## Version Management

### Semantic Versioning

- **Major.Minor.Patch** (e.g., 0.11.0)
- **Major**: Breaking changes
- **Minor**: New features (backwards compatible)
- **Patch**: Bug fixes

### Phase-to-Version Mapping

| Phase | Version | Release |
|-------|---------|---------|
| Phase 1-2 | 0.1.0 | Core tools |
| Phase 3 | 0.3.0 | VeritasBrain |
| Phase 4 | 0.4.0 | RAG system |
| Phase 5 | 0.5.0 | Event API |
| Phase 6 | 0.6.0 | Legislative |
| Phase 7 | 0.7.0 | Congress integration |
| Phase 8 | 0.8.0 | Dispute resolution |
| Phase 9 | 0.9.0 | Monitoring |
| Phase 10 | 0.10.0 | Reporting |
| Phase 11 | 0.11.0 | Production hardening |

---

## Performance Considerations

### Optimization Strategies

1. **In-Memory Caching**
   - Cache frequently accessed data (corpus, recent audits)
   - Invalidate on updates

2. **Batch Processing**
   - Process multiple audits in one pass
   - Reduce I/O operations

3. **Lazy Loading**
   - Load corpus only when RAG is enabled
   - Load historical audits only for reporting

4. **Efficient Storage**
   - JSONL for append-only logs
   - Individual JSON files for discrete items
   - Timestamp-based file naming for easy sorting

---

## Security Considerations

### Input Validation

```python
def enforce_payload_size(payload: Dict[str, Any], max_kb: int = 64):
    serialized = json.dumps(payload)
    size_kb = len(serialized.encode('utf-8')) / 1024
    if size_kb > max_kb:
        raise PayloadSizeError(
            message=f"Payload size {size_kb:.2f}KB exceeds limit {max_kb}KB",
            details={"size_kb": size_kb, "limit_kb": max_kb}
        )
```

### Rate Limiting

```python
RATE_STATE = {"events": [], "tools": []}

def enforce_rate_limit(action_type: str, limit: int):
    now = time.time()
    window_start = now - 60  # 60-second rolling window

    # Remove old timestamps
    RATE_STATE[action_type] = [
        ts for ts in RATE_STATE[action_type] if ts > window_start
    ]

    if len(RATE_STATE[action_type]) >= limit:
        raise RateLimitError(
            message=f"Rate limit exceeded: {limit} {action_type}/minute",
            details={"limit": limit, "window": "1 minute"}
        )

    RATE_STATE[action_type].append(now)
```

### RAG Safety

```python
RISKY_PATTERNS = [
    r'[/\\](?:etc|var|home|root)',  # File paths
    r'\bexec\s*\(',                  # Code execution
    r'\b(?:SELECT|INSERT|UPDATE)\b', # SQL injection
    r'<script[^>]*>',                # Script tags
]

def risky_query_detected(query: str) -> bool:
    for pattern in RISKY_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            return True
    return False
```

---

## Future Phases (Planned)

### Phase 12: External API Integration (Optional)
- Real-time source verification
- Content fetching and analysis
- Fact-checking capabilities
- API key management
- Rate limiting for external calls

### Phase 13: Enhanced Pattern Libraries
- Confidence calibration
- Cross-document analysis
- Performance optimization
- Advanced pattern recognition
- Multi-language support

---

## Conclusion

The Veritas agent build format emphasizes:

1. **Incremental Development**: Each phase adds specific, testable capabilities
2. **Comprehensive Testing**: 40-100+ tests per phase ensure reliability
3. **Deterministic Logic**: Rule-based analysis for transparency
4. **Structured Output**: Consistent JSON schemas with Pydantic
5. **Advisory Only**: Never takes autonomous actions - reports only
6. **Backwards Compatibility**: New phases don't break existing functionality
7. **Production Ready**: Phase 11 adds error handling, rate limiting, and security

This format has successfully delivered 11 phases with 621 tests passing, providing a robust foundation for truth auditing in the AI Senate ecosystem.
