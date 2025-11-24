# Veritas - AI Senate Truth Auditor

Veritas is the AI Senate member responsible for truth auditing, logic checking, bias detection, and chain-of-thought validation. It serves as the analytical backbone for verifying claims, detecting logical fallacies, and ensuring the integrity of reasoning processes.

## Current Status: Phase 11

**Phase 11 implements Production Hardening with error boundaries, rate limiting, and security controls.**

Veritas now:
- Provides centralized error handling with structured JSON responses
- Enforces rate limiting (20 events/min, 30 tools/min)
- Validates payload sizes (max 64KB)
- Implements feature flags for RAG, monitoring, and reporting
- Includes RAG safety layer to reject malicious queries
- Hardened tools and endpoints for production stability

Previous Phase 10 added:
- Long-term bias trends over weeks/months with regression slopes
- Logic issue trends with slope analysis
- Veritas Performance Score (0-100) with subsystem grades
- Governance-grade reports with chart-ready data

**Important:** Veritas monitors only — never intervenes or takes autonomous actions.
All monitoring results are reported to Sky/Congress for their decision-making.

Veritas does NOT:
- Rule on ethics or law (that's Sophia's domain)
- Rule on security or danger (that's Aegis's domain)
- Override Congress, Sky, or any agent
- Actually escalate or forward events
- Intervene based on monitoring results

Previous phases include: automated monitoring, drift detection, bias trends, dispute resolution, structured schema audits, Congress review tools, legislative functions, Event API, and RAG memory.

All analysis is rule-based with no ML models. Results are deterministic and interpretable.
Veritas adjudicates **logic, not policy**. It does not evaluate morality, cost, or political alignment.

## Core Tools

### 1. Logic Auditor (`/audit_text`)

Analyzes text for logical consistency, claims, fallacies, and reasoning issues.

**Input:**
```json
{
  "text": "You are stupid, so your argument is wrong. Obviously this is true."
}
```

**Output:**
```json
{
  "ok": true,
  "claims": [
    {"text": "...", "type": "factual|universal|causal|normative", "position": 0}
  ],
  "logical_fallacies": [
    {"type": "Ad Hominem", "description": "...", "matched_text": "...", "position": 0}
  ],
  "inconsistencies": [],
  "unsupported_jumps": [
    {"text": "...", "type": "unjustified_certainty", "reason": "...", "position": 0}
  ]
}
```

**Detected Fallacies:**
- Ad Hominem
- Straw Man
- Circular Reasoning
- False Dichotomy
- Appeal to Authority
- Appeal to Emotion
- Slippery Slope
- Red Herring
- Hasty Generalization
- False Cause

### 2. Bias Detector (`/detect_bias`)

Detects various forms of bias using heuristic word lists and pattern matching.

**Input:**
```json
{
  "text": "This is absolutely terrible! Obviously everyone knows this is wrong."
}
```

**Output:**
```json
{
  "ok": true,
  "political_bias": 0.0,
  "emotional_bias": 0.45,
  "motivational_bias": 0.0,
  "certainty_overconfidence": 0.38
}
```

**Bias Types (0.0-1.0 normalized scores):**
- `political_bias`: Partisan language intensity
- `emotional_bias`: Loaded/emotional language
- `motivational_bias`: Persuasive/self-serving patterns
- `certainty_overconfidence`: Unjustified certainty markers

### 3. Chain Validator (`/validate_chain`)

Validates chains of reasoning for logical coherence.

**Input:**
```json
{
  "chain": [
    "Assume that all birds can fly",
    "Penguins are birds",
    "Therefore penguins can fly"
  ]
}
```

**Output:**
```json
{
  "ok": true,
  "gaps": [],
  "contradictions": [],
  "circular_logic": [],
  "flawed_premises": [
    {"step_index": 0, "step": "...", "issues": [{"type": "unverified_assumption"}]}
  ]
}
```

**Detection Capabilities:**
- Gaps in reasoning (missing intermediate steps)
- Contradictions between steps
- Circular logic patterns
- Flawed/weak premises

### 4. Source Checker (`/check_sources`)

Validates and scores source credibility without external requests.

**Input:**
```json
{
  "sources": [
    "https://www.nature.com/articles/test",
    "https://random-blog.blogspot.com/post",
    "not a valid url"
  ]
}
```

**Output:**
```json
{
  "ok": true,
  "missing_sources": [],
  "unverifiable": [{"index": 2, "source": "not a valid url", "issues": ["invalid_format"]}],
  "conflicting": [],
  "ranked_confidence": [
    {"index": 0, "source": "...", "type": "url", "confidence": 0.85},
    {"index": 1, "source": "...", "type": "url", "confidence": 0.35}
  ]
}
```

**Credibility Scoring:**
- `.edu`, `.gov`, academic journals: 0.80-0.85
- Major news (Reuters, AP, BBC): 0.70-0.75
- Reference sites (Wikipedia, Britannica): 0.60-0.75
- Social media, blogs: 0.20-0.45

## VeritasBrain - Internal Reasoning Engine

The VeritasBrain is the central orchestration system that coordinates all analysis tools into a unified pipeline.

### Pipeline Overview

1. **Task Classification** - Automatically determines analysis type based on payload
2. **Memory Retrieval** - Queries RAG system for relevant context (stub in Phase 3)
3. **Tool Orchestration** - Executes appropriate analysis tools
4. **Result Synthesis** - Combines findings into structured summary
5. **Contribution Logging** - Records analysis for auditing

### Task Types

| Task Type | Triggered By | Tools Run |
|-----------|--------------|-----------|
| `audit_text` | `text` field only | Logic Auditor, Bias Detector |
| `validate_chain` | `steps` or `chain` field | Chain Validator |
| `check_sources` | `sources` field | Source Checker |
| `composite_audit` | Multiple fields | All relevant tools |

### Sample `/run_task` Request

**Input:**
```json
{
  "task_type": "audit",
  "payload": {
    "text": "You are wrong because you are stupid. Obviously everyone agrees."
  }
}
```

**Output:**
```json
{
  "ok": true,
  "task_type": "audit_text",
  "summary": {
    "has_major_issues": true,
    "issue_types": ["logical_fallacies", "overconfident_claims"],
    "confidence_estimate": 0.85
  },
  "details": {
    "audit": {
      "claims": [...],
      "logical_fallacies": [{"type": "Ad Hominem", ...}],
      "inconsistencies": [],
      "unsupported_jumps": [...]
    },
    "bias": {
      "political_bias": 0.0,
      "emotional_bias": 0.35,
      "motivational_bias": 0.0,
      "certainty_overconfidence": 0.42
    },
    "chain": null,
    "sources": null,
    "memory_context": {
      "memory_hits": [],
      "memory_summary": "RAG system not yet implemented"
    }
  }
}
```

### Composite Analysis Example

**Input:**
```json
{
  "task_type": "composite",
  "payload": {
    "text": "Climate change is real.",
    "steps": ["CO2 levels are rising", "Temperatures are increasing", "Therefore climate is changing"],
    "sources": ["https://www.nature.com/article", "https://random-blog.com"]
  }
}
```

**Output:**
```json
{
  "ok": true,
  "task_type": "composite_audit",
  "summary": {
    "has_major_issues": false,
    "issue_types": ["low_credibility_sources"],
    "confidence_estimate": 0.89
  },
  "details": {
    "audit": {...},
    "bias": {...},
    "chain": {...},
    "sources": {...},
    "memory_context": {...}
  }
}
```

### Issue Detection

The summary flags major issues when:
- 2+ logical fallacies detected
- Any bias score > 0.6
- Flawed premises or contradictions in chain
- Sources with credibility < 0.4

### Event Processing

The `/event` endpoint now processes certain event types through VeritasBrain:

| Event Type | Behavior |
|------------|----------|
| `analyze` | Full analysis through brain |
| `audit` | Audit analysis |
| `validate` | Chain validation |
| `check` | Source checking |
| Other | Logged only, not processed |

## RAG & Memory System (Phase 4)

The RAG (Retrieval-Augmented Generation) system provides Veritas with memory capabilities, allowing it to store and retrieve relevant context during analysis.

### Storage

Documents are stored in a local JSONL file at:
```
memory/long/veritas_corpus.jsonl
```

Each document is stored as a JSON line with:
- `id`: Unique identifier (required)
- `text`: Document content (required)
- `tags`: Optional categorization tags
- `embedding`: Pre-computed embedding vector (128 dimensions)

### Document Ingestion

**Via Python:**
```python
from app.rag.ingest import ingest_documents, clear_corpus

# Ingest documents
docs = [
    {"id": "fact1", "text": "The speed of light is 299,792,458 m/s.", "tags": ["physics"]},
    {"id": "fact2", "text": "Water freezes at 0 degrees Celsius.", "tags": ["chemistry"]},
]
result = ingest_documents(docs)
# {"ingested_count": 2, "errors": []}

# Clear all documents
clear_corpus()
```

**Via API:**
```bash
# Ingest documents
curl -X POST http://localhost:8000/ingest_docs \
  -H "Content-Type: application/json" \
  -d '{"docs": [{"id": "doc1", "text": "Document content", "tags": ["tag1"]}]}'

# Clear corpus
curl -X POST http://localhost:8000/clear_corpus

# Get statistics
curl http://localhost:8000/corpus_stats
```

### Memory Retrieval in VeritasBrain

When processing a task, VeritasBrain automatically retrieves relevant memory context:

1. **Query Construction** - Extracts search text from payload (topic > text > context > steps)
2. **Embedding** - Creates deterministic embedding using hashed bag-of-words
3. **Similarity Search** - Computes cosine similarity against all corpus documents
4. **Context Assembly** - Returns top-k most relevant documents

The memory context is included in all analysis results:
```json
{
  "details": {
    "memory_context": {
      "memory_hits": [
        {"id": "fact1", "text": "...", "score": 0.85, "tags": ["physics"]}
      ],
      "memory_summary": "Found 1 relevant entries in memory"
    }
  }
}
```

### Embedding System

The embedding system is entirely deterministic and rule-based:

- **Tokenization**: Lowercase, split on non-alphanumeric characters
- **Hashing**: Polynomial rolling hash maps tokens to 128-dimension vector
- **Weighting**: TF-like log-scaled token counts
- **Normalization**: L2 normalized for cosine similarity

```python
from app.rag.query import embed_text, cosine_similarity

# Create embeddings
emb1 = embed_text("machine learning algorithms")
emb2 = embed_text("artificial intelligence systems")

# Compute similarity
similarity = cosine_similarity(emb1, emb2)
```

### RAGQuery Class

For advanced querying:

```python
from app.rag.query import RAGQuery

rag = RAGQuery({"top_k": 10, "similarity_threshold": 0.3})

# Basic query
result = rag.query("climate change effects")

# Query with tag filters
result = rag.query_with_filter("physics", filters={"tags": ["science"]})

# Hybrid keyword + semantic search
result = rag.hybrid_search("quantum mechanics", keyword_weight=0.5)

# Get context optimized for token limits
result = rag.get_context("summarize findings", max_tokens=4000)
```

### Current Limitations

- **Simple embeddings**: Uses hashed bag-of-words, not semantic ML embeddings
- **No external knowledge**: Only searches ingested corpus, no web access
- **File-based storage**: JSONL file, not a vector database
- **In-memory processing**: Entire corpus loaded for each query
- **No persistence across restarts**: Corpus file must be re-ingested if deleted

## Event API for Other Agents (Phase 5)

The Event API provides a standardized interface for inter-agent communication. Sky, Congress, and other agents can request analysis from Veritas using structured event types.

### VeritasEvent Schema

```json
{
  "event_type": "audit-request",
  "source": "sky",
  "payload": { "text": "Text to analyze..." },
  "correlation_id": "optional-trace-id-123"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_type` | string | Yes | Type of analysis requested |
| `source` | string | Yes | Sender agent ID (e.g., "sky", "congress") |
| `payload` | object | Yes | Task-specific content |
| `correlation_id` | string | No | Tracing ID for request correlation |

### VeritasResponse Schema

```json
{
  "ok": true,
  "event_type": "audit-request",
  "correlation_id": "optional-trace-id-123",
  "result": {
    "task_type": "audit_text",
    "summary": { ... },
    "details": { ... }
  }
}
```

### Supported Event Types

| Event Type | Description | Payload Fields | Used By |
|------------|-------------|----------------|---------|
| `audit-request` | General text audit (logic + bias) | `text` | Sky |
| `bill-logic-check` | Audit bill/policy text | `bill_text` or `text` | Congress, Bill Engine |
| `argument-integrity-check` | Validate reasoning chain | `steps` or `chain` | Aero, Mercury, Apollo |
| `source-integrity-check` | Check source credibility | `sources` | Any agent |
| `composite-audit` | Combined analysis | Any combination | Sky (complex cases) |

### Example: Audit Request from Sky

**Request:**
```bash
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "audit-request",
    "source": "sky",
    "payload": { "text": "You are wrong because you are stupid." },
    "correlation_id": "sky-session-456"
  }'
```

**Response:**
```json
{
  "ok": true,
  "event_type": "audit-request",
  "correlation_id": "sky-session-456",
  "result": {
    "task_type": "audit_text",
    "summary": {
      "has_major_issues": true,
      "issue_types": ["logical_fallacies"],
      "confidence_estimate": 0.85
    },
    "details": {
      "audit": { "logical_fallacies": [{"type": "Ad Hominem", ...}] },
      "bias": { ... },
      "memory_context": { ... }
    }
  }
}
```

### Example: Bill Logic Check from Congress

**Request:**
```bash
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "bill-logic-check",
    "source": "congress",
    "payload": {
      "bill_text": "All citizens shall have equal rights. No citizen shall be discriminated against."
    }
  }'
```

### Example: Argument Integrity Check

**Request:**
```bash
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "argument-integrity-check",
    "source": "apollo",
    "payload": {
      "steps": [
        "Premise: All mammals are warm-blooded",
        "Premise: Whales are mammals",
        "Conclusion: Therefore whales are warm-blooded"
      ]
    }
  }'
```

### Example: Composite Audit

**Request:**
```bash
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "composite-audit",
    "source": "sky",
    "payload": {
      "text": "Climate change is real and urgent.",
      "steps": ["CO2 levels rising", "Temperatures increasing", "Climate changing"],
      "sources": ["https://www.ipcc.ch/report", "https://www.nature.com/climate"]
    }
  }'
```

### Error Handling

Unknown event types return `ok: false`:

```json
{
  "ok": false,
  "event_type": "unknown-type",
  "correlation_id": null,
  "result": {
    "error": "Unknown event_type 'unknown-type'. Valid types: [...]",
    "error_type": "validation_error"
  }
}
```

### Agent Conventions

| Agent | Primary Event Types |
|-------|---------------------|
| **Sky** | `audit-request`, `composite-audit` |
| **Congress** | `bill-logic-check`, `bill-vote-request`, `bill-adversarial-request` |
| **Bill Engine** | `bill-logic-check`, `bill-vote-request` |
| **Apollo** | `argument-integrity-check` |
| **Mercury** | `argument-integrity-check`, `source-integrity-check` |
| **Aero** | `argument-integrity-check` |

## Legislative Functions (Phase 6)

Veritas participates in Senate legislative processes through voting and adversarial contributions.

**Key Principle:** Veritas adjudicates **logic, not policy**. It does not evaluate:
- Moral considerations
- Cost or budget implications
- Political alignment
- Social desirability

### Bill Voting (`/vote_on_bill`)

Veritas votes on bills based strictly on:
- Logical consistency
- Presence of contradictions
- Fallacy detection
- Bias levels
- Clarity and structure

**Request:**
```bash
curl -X POST http://localhost:8000/vote_on_bill \
  -H "Content-Type: application/json" \
  -d '{
    "bill_text": "All citizens shall have equal rights under the law.",
    "bill_id": "EQUALITY-ACT-2024"
  }'
```

**Response:**
```json
{
  "ok": true,
  "bill_id": "EQUALITY-ACT-2024",
  "vote": "yes",
  "confidence": 0.85,
  "reasons": ["No significant logical issues detected", "Structure is coherent"],
  "analysis_summary": "No significant issues found"
}
```

**Vote Values:**
| Vote | Condition |
|------|-----------|
| `yes` | Minimal or no logical issues |
| `no` | Contradictions, high bias, multiple fallacies |
| `abstain` | Text too short, unclear, or insufficient evidence |

### Adversarial Contribution (`/adversarial_contribution`)

When Congress risks groupthink, Veritas surfaces:
- Edge-case flaws
- Hidden assumptions
- Potential fallacies
- Alternate interpretations

This is NOT a vote - it's a devil's advocate contribution.

**Request:**
```bash
curl -X POST http://localhost:8000/adversarial_contribution \
  -H "Content-Type: application/json" \
  -d '{
    "bill_text": "All schools must implement new curriculum standards.",
    "bill_id": "EDU-REFORM-2024"
  }'
```

**Response:**
```json
{
  "ok": true,
  "bill_id": "EDU-REFORM-2024",
  "counterpoints": [
    {
      "type": "structural",
      "issue": "Universal mandate may not account for regional differences",
      "severity": "medium"
    }
  ],
  "risk_flags": [],
  "requires_review": false,
  "hidden_assumptions": ["Assumes uniform educational infrastructure"]
}
```

### Event-Based Legislative Requests

Congress can also use the `/event` endpoint:

**Vote Request:**
```json
{
  "event_type": "bill-vote-request",
  "source": "congress",
  "payload": {"bill_text": "..."},
  "correlation_id": "session-123"
}
```

**Adversarial Request:**
```json
{
  "event_type": "bill-adversarial-request",
  "source": "congress",
  "payload": {"bill_text": "..."}
}
```

## Congress Integration (Phase 7)

The `/event/congress` endpoint provides structured event handling for Congress with schema-based responses.

**Important:** Veritas is an auditor. Recommendations are **advisory only**. They do not constitute a vote, law change, or override of any other agent.

### Supported Congress Event Types

| Event Type | Description | Payload Fields |
|------------|-------------|----------------|
| `bill_for_review` | Review a bill for logical issues | `bill_id`, `text`, `sources` (optional) |
| `statement_for_audit` | Audit a statement for truth/bias | `statement_id`, `text`, `sources` (optional) |
| `dispute_for_analysis` | Analyze a dispute between agents | `agent_A`, `agent_B` |
| `monitoring_cycle` | Run drift/bias/anomaly monitoring | `limit` (optional, default 10) |
| `generate_veritas_report` | Generate comprehensive trend/performance report | `store` (optional, default true) |

### Bill Review Example

**Request:**
```bash
curl -X POST http://localhost:8000/event/congress \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "bill_for_review",
    "payload": {
      "bill_id": "BILL-2024-001",
      "text": "All citizens shall have equal rights under the law."
    }
  }'
```

**Response:**
```json
{
  "ok": true,
  "event_type": "bill_for_review",
  "result": {
    "item_type": "bill",
    "id": "BILL-2024-001",
    "audit": {
      "audit": {
        "original_text": "...",
        "normalized": {"claims": [...], "word_count": 9},
        "logical_issues": [],
        "bias_flags": [],
        "confidence": "high"
      },
      "retrieved_docs": [],
      "source_validation": []
    },
    "recommendation": "approve",
    "notes": "ADVISORY: Analysis found no significant issues. High confidence in analysis"
  }
}
```

### Recommendation Values

| Recommendation | Condition |
|----------------|-----------|
| `approve` | High confidence, no significant issues |
| `revise` | Some issues detected that should be addressed |
| `reject` | Severe logical issues or major contradictions |

### Unknown Event Type Error

**Request:**
```bash
curl -X POST http://localhost:8000/event/congress \
  -H "Content-Type: application/json" \
  -d '{"event_type": "unknown", "payload": {}}'
```

**Response (400):**
```json
{
  "ok": false,
  "error": "Unknown event_type 'unknown'",
  "supported_types": ["bill_for_review", "statement_for_audit", "dispute_for_analysis"]
}
```

### Tool Registry

Veritas tools can be invoked programmatically:

```python
from app.tools import registry, TOOLS

# List available tools
tools = registry.list_tools()
# ['review_bill', 'review_statement', 'audit_text', 'audit_with_sources', 'parse_dispute']

# Invoke a tool
result = registry.invoke("review_bill", {
    "bill_id": "TEST-001",
    "text": "Policy document text..."
})
```

## Dispute Resolution (Phase 8)

The dispute engine processes disagreements between agents and classifies dispute types.

**Important:** Veritas does NOT:
- Rule on ethics or law (Sophia's domain)
- Rule on security or danger (Aegis's domain)
- Override Congress, Sky, or any agent
- Actually escalate or forward events

Veritas only classifies and reports. Actual escalation is handled by Sky/n8n.

### `parse_dispute` Tool

**Request:**
```bash
curl -X POST http://localhost:8000/event/congress \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "dispute_for_analysis",
    "payload": {
      "agent_A": {
        "agent": "Sky",
        "text": "The proposal is valid and should be approved.",
        "metadata": {}
      },
      "agent_B": {
        "agent": "Aegis",
        "text": "The proposal has security concerns that need addressing.",
        "metadata": {}
      }
    }
  }'
```

**Response:**
```json
{
  "ok": true,
  "event_type": "dispute_for_analysis",
  "result": {
    "agents": ["Sky", "Aegis"],
    "issues": {
      "factual_disagreement": false,
      "interpretation_disagreement": true,
      "missing_data": false,
      "logical_issues_A": [],
      "logical_issues_B": [],
      "contradictions": []
    },
    "needs_escalation": "aegis",
    "recommendation": "forward_to_aegis",
    "analysis": {...},
    "storage": {"stored": true, "dispute_id": "..."}
  }
}
```

### Escalation Categories

| Target | Triggered By | Example Keywords |
|--------|--------------|------------------|
| `sophia` | Ethical/legal ambiguity | ethics, rights, justice, law, discrimination |
| `aegis` | Security/safety implications | security, threat, vulnerability, danger |
| `congress` | Political/governance impact | policy, budget, legislation, authority |
| `none` | No special domain detected | General factual disputes |

### Recommendation Values

| Recommendation | Condition |
|----------------|-----------|
| `forward_to_sophia` | Escalation to Sophia needed |
| `forward_to_aegis` | Escalation to Aegis needed |
| `mediation_by_congress` | Escalation to Congress needed |
| `request_more_data` | Missing data or context |
| `minimal_issue_detected` | Clear logical winner |
| `inconclusive` | Both sides have significant issues |

### Dispute Storage

Disputes are stored in `app/memory/long_term/disputes/` for audit trails:
- One JSON file per dispute
- Includes timestamp, agent names, analysis, recommendation
- Can be queried for historical analysis

## Automated Monitoring (Phase 9)

The monitoring engine provides continuous evaluation of agent outputs over time, detecting drift, bias trends, and anomalies.

**Important:** Veritas monitors only — never intervenes or takes autonomous actions.
All monitoring results are reported for review.

### Monitoring Cycle

**Request:**
```bash
curl -X POST http://localhost:8000/event/congress \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "monitoring_cycle",
    "payload": {"limit": 10}
  }'
```

**Response:**
```json
{
  "ok": true,
  "event_type": "monitoring_cycle",
  "result": {
    "logical_drift": {
      "drift_score": 0.15,
      "increasing_issue_types": [],
      "possible_causes": [],
      "is_concerning": false
    },
    "bias_trends": {
      "bias_trend_score": 0.08,
      "bias_types_increasing": [],
      "summary": "No significant bias trends detected",
      "is_concerning": false
    },
    "anomalies": {
      "anomaly_detected": false,
      "anomaly_reason": null,
      "anomalies": [],
      "statistics": {"mean_issues": 1.5, "std_issues": 0.8, "sample_size": 10}
    },
    "overall_status": "stable",
    "timestamp": "2024-01-15T10:30:00.000000+00:00",
    "audits_analyzed": 10,
    "storage": {"stored": true, "file_path": "...", "snapshot_id": "..."}
  }
}
```

### Monitoring Components

| Component | Description | Concern Threshold |
|-----------|-------------|-------------------|
| **Logical Drift** | Tracks increasing logical issues over time | 30% increase |
| **Bias Trends** | Tracks accumulation of bias patterns | 30% rise |
| **Anomaly Detection** | Detects sudden deviations (>2 std dev) | 2σ threshold |

### Overall Status Values

| Status | Condition |
|--------|-----------|
| `stable` | No drift, no bias trends, no anomalies |
| `warning` | Any one category is concerning |
| `critical` | 2+ categories are concerning |

### Logical Drift Detection

Identifies increases in:
- Logical fallacies
- Inconsistencies
- Unsupported conclusions
- Contradictions

Returns `possible_causes` such as:
- "Reasoning quality degradation"
- "Internal consistency issues"
- "Evidence gaps increasing"

### Bias Trend Analysis

Tracks accumulation of:
- Emotional language
- Political bias
- Certainty overconfidence
- Loaded framing

### Anomaly Detection

Detects sudden deviations using statistical analysis:
- Computes mean and standard deviation of issue counts
- Flags results that exceed 2 standard deviations
- Reports `anomaly_reason` with specific deviation details

### Monitoring Storage

Snapshots are stored in `app/memory/long_term/monitoring/`:
- JSON files named by timestamp (YYYY-MM-DD_HH-MM.json)
- Includes full drift, bias, and anomaly analysis
- Enables historical trend analysis

### Tool Registry

```python
from app.tools import registry

# Run monitoring cycle
result = registry.invoke("run_monitoring", {"limit": 10})
print(result["overall_status"])  # "stable", "warning", or "critical"
```

## Long-Term Trend Analytics & Reporting (Phase 10)

The trend analytics and reporting system provides governance-grade reports for long-term pattern analysis.

**Important:** Veritas monitors only — never intervenes or takes autonomous actions.
All reports are informational and do not constitute decisions or recommendations for action.

### Trend Engine

The trend engine analyzes all historical audits to compute long-term trends:

- **Bias Trends**: Weekly buckets with linear regression slopes for each bias type
- **Logic Issue Trends**: Count issue types per week with trend analysis
- **Source Reliability Trends**: Track support/contradiction/missing context rates

```python
from app.trend_engine import (
    load_all_audits,
    compute_bias_over_time,
    compute_logic_issue_trends,
    compute_source_reliability_trends,
    compute_performance_score,
)

# Load all historical audits
audits = load_all_audits()

# Compute trends
bias_trends = compute_bias_over_time(audits)
logic_trends = compute_logic_issue_trends(audits)
source_trends = compute_source_reliability_trends(audits)

# Compute performance score
trends = {
    "bias_trends": bias_trends,
    "logic_trends": logic_trends,
    "source_trends": source_trends,
}
performance = compute_performance_score(trends)
print(f"Score: {performance['score']}/100")  # e.g., "Score: 85.0/100"
```

### Veritas Performance Score

The performance score (0-100) provides a single metric for Veritas health:

**Penalty System:**

| Condition | Penalty |
|-----------|---------|
| Strong upward bias trend (slope > 0.1) | -15 |
| Moderate upward bias trend (slope 0.05-0.1) | -7 |
| Strong contradiction trend (slope > 0.1) | -20 |
| Moderate contradiction trend (slope 0.05-0.1) | -10 |
| Fallacy trend increase (slope > 0.1) | -10 |
| Declining source support (slope < -0.05) | -10 |
| Increasing source contradictions (slope > 0.05) | -5 |
| Critical monitoring status | -25 |
| Warning monitoring status | -10 |

**Grade System:**

| Grade | Score Range |
|-------|-------------|
| A | ≥ 80 |
| B | ≥ 60 |
| C | ≥ 40 |
| D | < 40 |

**Subsystem Grades:**
- `bias_analysis`: Grade based on bias trend penalties
- `logic_analysis`: Grade based on logic issue penalties
- `source_validation`: Grade based on source reliability penalties
- `monitoring_stability`: Grade based on monitoring status

### Report Generation

Generate comprehensive reports via the Congress endpoint:

**Request:**
```bash
curl -X POST http://localhost:8000/event/congress \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "generate_veritas_report",
    "payload": {}
  }'
```

**Response:**
```json
{
  "ok": true,
  "event_type": "generate_veritas_report",
  "result": {
    "meta": {
      "agent": "veritas",
      "version": "0.10.0",
      "phase": 10,
      "generated_at": "2024-01-15T10:30:00.000000+00:00",
      "audits_analyzed": 50
    },
    "trends": {
      "bias_trends": {"slopes": {...}, "top_increasing": [...], ...},
      "logic_trends": {"slopes": {...}, "notable_trends": [...], ...},
      "source_trends": {"slopes": {...}, "summary": "...", ...}
    },
    "monitoring": {
      "overall_status": "stable",
      ...
    },
    "performance": {
      "score": 85.0,
      "grades": {
        "bias_analysis": "A",
        "logic_analysis": "B",
        "source_validation": "A",
        "monitoring_stability": "A"
      },
      "stability_index": 1.0,
      "summary": "...",
      "penalties": [...]
    },
    "chart_data": {
      "bias_over_time": {...},
      "logic_issues_over_time": {...},
      "source_rates": {...}
    },
    "summary": "Veritas health is excellent (score: 85/100)...",
    "recommendations": [
      "STATUS: All systems operating within normal parameters.",
      "NOTE: All recommendations are advisory only."
    ],
    "storage": {"stored": true, "file_path": "...", "report_id": "..."}
  }
}
```

### Chart-Ready Data

The `chart_data` section provides arrays suitable for visualization:

```json
{
  "bias_over_time": {
    "emotional_language": {
      "weeks": ["2024-W01", "2024-W02", "2024-W03"],
      "counts": [5, 7, 6],
      "slope": 0.05
    }
  },
  "logic_issues_over_time": {
    "contradiction": {
      "weeks": ["2024-W01", "2024-W02"],
      "counts": [2, 3],
      "slope": 0.1
    }
  },
  "source_rates": {
    "support": {"weeks": [...], "rates": [...], "slope": 0.02},
    "contradiction": {"weeks": [...], "rates": [...], "slope": -0.01}
  }
}
```

### Recommendations

Reports include advisory recommendations based on analysis:

| Type | Example |
|------|---------|
| ADVISORY | Review bias detection patterns. Increasing bias trends detected. |
| TREND | Contradiction rate increasing rapidly. May indicate systemic issues. |
| URGENT | Multiple monitoring concerns detected. Manual review recommended. |
| STATUS | All systems operating within normal parameters. |
| NOTE | All recommendations are advisory only. Veritas does not take autonomous action. |

### Report Storage

Reports are stored in `app/memory/long_term/monitoring/reports/`:
- JSON files named by timestamp (report_YYYY-MM-DD_HH-MM-SS.json)
- Can be retrieved using `get_recent_reports(limit=10)`
- Enables historical trend analysis

### Tool Registry

```python
from app.tools import registry

# Generate comprehensive report
result = registry.invoke("generate_report", {"store": True})
print(f"Score: {result['performance']['score']}")
print(f"Summary: {result['summary']}")
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service information |
| `/health` | GET | Health check |
| `/status` | GET | Component status |
| `/event` | POST | **Event API** - Inter-agent communication |
| `/event/congress` | POST | **Congress API** - Bill/statement/dispute handling (Phase 8) |
| `/run_task` | POST | Execute a task by type |
| `/audit_text` | POST | Audit text for logic issues |
| `/detect_bias` | POST | Detect bias in text |
| `/validate_chain` | POST | Validate reasoning chain |
| `/check_sources` | POST | Check source credibility |
| `/vote_on_bill` | POST | **Legislative** - Vote on a bill (Phase 6) |
| `/adversarial_contribution` | POST | **Legislative** - Devil's advocate analysis (Phase 6) |
| `/ingest_docs` | POST | Ingest documents into corpus |
| `/clear_corpus` | POST | Clear all documents from corpus |
| `/corpus_stats` | GET | Get corpus statistics |
| `/event/legacy` | POST | Legacy event format (deprecated) |

## Installation

### Requirements

- Python 3.10+
- pip

### Setup

```bash
cd veritas
pip install -r requirements.txt
```

## Running the Server

```bash
uvicorn app.main:app --reload
```

The server starts at `http://localhost:8000`.

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Running Tests

```bash
PYTHONPATH=. pytest tests/ -v
```

## Project Structure

```
veritas/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Configuration
│   ├── schemas.py           # Pydantic models for structured output (Phase 7/10)
│   ├── dispute_engine.py    # Dispute parsing and classification (Phase 8)
│   ├── monitoring_engine.py # Drift detection and monitoring (Phase 9)
│   ├── trend_engine.py      # Long-term trend analytics (Phase 10)
│   ├── reporting.py         # Governance-grade reporting (Phase 10)
│   ├── memory_utils.py      # Memory storage utilities (Phase 8/9)
│   ├── routes/veritas.py    # API endpoints (Phase 10: Reporting)
│   ├── logic/
│   │   ├── brain.py         # VeritasBrain + handle_event + convenience functions
│   │   ├── legislative.py   # Legislative functions (Phase 6)
│   │   ├── auditor.py       # Logic auditing (Phase 2)
│   │   ├── bias_detector.py # Bias detection (Phase 2)
│   │   ├── chain_validator.py # Chain validation (Phase 2)
│   │   └── source_checker.py  # Source verification (Phase 2)
│   ├── rag/
│   │   ├── ingest.py        # Document ingestion (Phase 4)
│   │   └── query.py         # Embedding & similarity search (Phase 4)
│   ├── tools/
│   │   └── __init__.py      # Tool registry + Reporting tools (Phase 10)
│   ├── memory/
│   │   └── long_term/
│   │       ├── disputes/    # Dispute analysis storage (Phase 8)
│   │       ├── audits/      # Audit storage (Phase 9)
│   │       └── monitoring/
│   │           └── reports/ # Generated reports (Phase 10)
│   └── logs/
│       ├── veritas_brain.log        # Brain operations
│       ├── veritas_contributions.log # Analysis audit trail
│       ├── veritas_legislative.log  # Legislative operations
│       ├── veritas_legislative_contributions.log # Legislative audit trail
│       ├── rag_query.log            # RAG query logs
│       ├── memory_utils.log         # Memory operations
│       ├── monitoring_engine.log    # Monitoring operations (Phase 9)
│       ├── trend_engine.log         # Trend analysis operations (Phase 10)
│       └── reporting.log            # Report generation operations (Phase 10)
├── memory/
│   └── long/
│       └── veritas_corpus.jsonl  # Document corpus storage
├── tests/
│   ├── test_brain.py        # Brain unit tests (Phase 3)
│   ├── test_phase3_functions.py # Phase 3 convenience function tests
│   ├── test_rag.py          # RAG system tests (Phase 4)
│   ├── test_events.py       # Event API tests (Phase 5)
│   ├── test_legislative.py  # Legislative tests (Phase 6)
│   ├── test_congress_review_tools.py # Congress tool tests (Phase 7)
│   ├── test_event_handlers.py # Congress event handler tests (Phase 7)
│   ├── test_dispute_engine.py # Dispute engine tests (Phase 8)
│   ├── test_dispute_event.py  # Dispute event tests (Phase 8)
│   ├── test_monitoring_engine.py # Monitoring engine tests (Phase 9)
│   ├── test_monitoring_tool.py   # Monitoring tool tests (Phase 9)
│   ├── test_monitoring_event.py  # Monitoring event tests (Phase 9)
│   ├── test_trend_engine.py      # Trend engine tests (Phase 10)
│   ├── test_performance_score.py # Performance score tests (Phase 10)
│   ├── test_generate_report.py   # Report generation tests (Phase 10)
│   ├── test_generate_report_event.py # Report event tests (Phase 10)
│   ├── test_endpoints.py    # API endpoint tests
│   ├── test_auditor.py      # Logic auditor tests
│   ├── test_bias.py         # Bias detector tests
│   └── test_chain_validator.py # Chain validator tests
├── requirements.txt
└── README.md
```

## Design Philosophy

Veritas is:

- **Deterministic**: Same input always produces same output
- **Heuristic-based**: Uses pattern matching, not ML models
- **Analytical**: Focused on factual accuracy and logical rigor
- **Objective**: No emotional or narrative behavior
- **Transparent**: All analysis is interpretable

## Implementation Notes

- All logic is deterministic and rule-based
- No external API calls or web requests
- No ML models - only regex patterns and word lists
- All outputs are structured JSON
- Logging enabled for all operations

## Roadmap

### Phase 3 (Complete)

- VeritasBrain reasoning engine
- Task classification system
- Tool orchestration pipeline
- Result synthesis with issue detection
- Contribution logging and audit trail
- Event processing integration

### Phase 4 (Complete)

- RAG system implementation
- Deterministic embedding generation (hashed bag-of-words)
- JSONL-based document corpus storage
- Cosine similarity search functionality
- Memory-augmented analysis in VeritasBrain
- Document ingestion API endpoints

### Phase 5 (Complete)

- Standardized Event API for inter-agent communication
- VeritasEvent and VeritasResponse Pydantic models
- Support for audit-request, bill-logic-check, argument-integrity-check, source-integrity-check, composite-audit
- VeritasBrain.handle_event() for event processing
- Agent conventions for Sky, Congress, Apollo, Mercury, Aero
- Correlation ID support for request tracing

### Phase 6 (Complete)

- Legislative functions for Congress interaction
- `vote_on_bill()` for deterministic bill voting
- `adversarial_contribution()` for devil's advocate analysis
- `/vote_on_bill` and `/adversarial_contribution` endpoints
- `bill-vote-request` and `bill-adversarial-request` event types
- Contribution logging for legislative audit trail
- LegislativeHandler class for OOP interface

### Phase 7 (Complete)

- Standardized Output Schema (Pydantic models)
  - `AuditResult`: Core audit with logical issues, bias flags, confidence
  - `AuditWithSourcesResult`: Extended audit with RAG and source validation
  - `CongressReviewResult`: Full review result with recommendation
- Congress-facing review tools
  - `tool_review_bill()`: Bill review with advisory recommendation
  - `tool_review_statement()`: Statement review with advisory recommendation
- `/event/congress` endpoint for Congress event handling
  - `bill_for_review`: Review a bill
  - `statement_for_audit`: Audit a statement
- Constitutional boundary checks (advisory only disclaimers)
- Tool registry with `review_bill`, `review_statement`, `audit_text`, `audit_with_sources`

### Phase 8 (Complete)

- Dispute Resolution Hooks (Non-Judicial)
  - `parse_dispute()`: Parse and classify disputes between agents
  - `DisputeEngine` class for OOP interface
  - Factual vs. interpretation disagreement detection
  - Contradiction detection with negation patterns
- Escalation classification
  - `sophia`: Ethical/legal ambiguity
  - `aegis`: Security/safety implications
  - `congress`: Political/governance impact
- Memory storage for disputes (`app/memory/long_term/disputes/`)
- `dispute_for_analysis` event type fully implemented
- `tool_parse_dispute()` added to tool registry

**Important:** Veritas does NOT escalate events. It only classifies and reports.

### Phase 9 (Complete)

- Automated Monitoring, Drift Detection, Bias Trends, and Long-Term Logging
  - `detect_logical_drift()`: Identify increasing logical issues over time
  - `analyze_bias_trends()`: Track accumulation of bias patterns
  - `detect_anomalies()`: Detect sudden deviations (>2 std dev)
  - `run_monitoring_cycle()`: Orchestrate all detection systems
  - `MonitoringEngine` class for OOP interface
- Overall status classification (stable/warning/critical)
- Long-term storage for audits and monitoring snapshots
  - `app/memory/long_term/audits/`: Audit result storage
  - `app/memory/long_term/monitoring/`: Monitoring snapshot storage
- `monitoring_cycle` event type for Congress
- `tool_run_monitoring()` added to tool registry

**Important:** Veritas monitors only — never intervenes or takes autonomous actions.

### Phase 10 (Complete)

- Long-Term Trend Analytics, Performance Metrics, and Professional Reporting
  - `load_all_audits()`: Load all historical audits from storage
  - `compute_bias_over_time()`: Weekly bias trends with linear regression slopes
  - `compute_logic_issue_trends()`: Weekly logic issue trends with slope analysis
  - `compute_source_reliability_trends()`: Track source support/contradiction rates
  - `compute_performance_score()`: Generate 0-100 performance score with grades
  - `TrendEngine` class for OOP interface
- Unified Reporting Engine
  - `generate_full_veritas_report()`: Comprehensive governance-grade reports
  - `store_report()`: Store reports to long-term storage
  - `get_recent_reports()`: Retrieve historical reports
  - `ReportingEngine` class for OOP interface
- Chart-ready data structures for visualization
- `VeritasReport` Pydantic schema
- `generate_veritas_report` event type for Congress
- `tool_generate_report()` in tool registry
- Report storage in `app/memory/long_term/monitoring/reports/`

**Important:** Veritas monitors only — never intervenes or takes autonomous actions.
All reports are informational and do not constitute decisions or recommendations for action.

### Phase 11 (Complete)

- Production Hardening, Error Boundaries, Rate Limits, Config Enforcement
  - `app/error_handler.py`: Centralized exception handling
    - `VeritasError`, `InvalidPayloadError`, `ToolExecutionError`, `MemoryAccessError`
    - `RAGSafetyError`, `RateLimitError`, `PayloadSizeError`, `FeatureDisabledError`
    - Structured JSON error responses (no stack traces exposed)
  - `app/config.py`: Feature flags and rate limits
    - `VERITAS_FEATURE_FLAGS`: Enable/disable RAG, monitoring, reporting
    - Rate limits: 20 events/min, 30 tools/min
    - Max payload size: 64KB
  - `app/utils.py`: Payload validation and rate limiting
    - `enforce_payload_size()`: Reject oversized payloads
    - `enforce_rate_limit()`: Rolling window rate limiting
    - Input validation utilities
  - RAG safety layer in `rag/query.py`
    - Reject queries with file paths, code execution patterns
    - Sanitize and truncate queries
  - Hardened tools with feature flag checks
  - Hardened endpoints with rate limiting
  - Expanded `/status` endpoint with feature flags and rate limits

**Important:** Phase 11 is optional production hardening. It adds no new intelligence or decision-making.

### Phase 12 (Planned)

- External API integration (optional)
- Real-time source verification
- Content fetching and analysis
- Fact-checking capabilities

### Phase 13 (Planned)

- Enhanced pattern libraries
- Confidence calibration
- Cross-document analysis
- Performance optimization

## Disclaimer

Phase 11 analysis is heuristic-based and deterministic. Results should be interpreted as indicators, not definitive assessments. The tool does not make external requests or fetch content - it analyzes text structure and patterns only. The RAG system uses simple embeddings and should not be considered production-grade semantic search. **Veritas votes on logic integrity, not policy merit** - moral, economic, and political considerations are outside its scope. **Congress review recommendations are advisory only** - they do not constitute a vote, law change, or override of any other agent. **Dispute escalation targets are advisory** - Veritas does not actually escalate or forward events. **Monitoring results and reports are informational** - Veritas monitors only and never intervenes or takes autonomous actions. **Performance scores and recommendations are advisory** - they provide insights for decision-making but do not trigger any autonomous action. **Rate limits and error responses are for stability** - they do not affect the accuracy of analysis.
