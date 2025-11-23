# Veritas - AI Senate Truth Auditor

Veritas is the AI Senate member responsible for truth auditing, logic checking, bias detection, and chain-of-thought validation. It serves as the analytical backbone for verifying claims, detecting logical fallacies, and ensuring the integrity of reasoning processes.

## Current Status: Phase 4

**Phase 4 implements the RAG (Retrieval-Augmented Generation) memory system for context-aware analysis.**

All analysis is rule-based with no ML models. Results are deterministic and interpretable.

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

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service information |
| `/health` | GET | Health check |
| `/status` | GET | Component status |
| `/run_task` | POST | Execute a task by type |
| `/audit_text` | POST | Audit text for logic issues |
| `/detect_bias` | POST | Detect bias in text |
| `/validate_chain` | POST | Validate reasoning chain |
| `/check_sources` | POST | Check source credibility |
| `/ingest_docs` | POST | Ingest documents into corpus |
| `/clear_corpus` | POST | Clear all documents from corpus |
| `/corpus_stats` | GET | Get corpus statistics |

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
│   ├── routes/veritas.py    # API endpoints (Phase 4: RAG integration)
│   ├── logic/
│   │   ├── brain.py         # VeritasBrain reasoning engine (Phase 3)
│   │   ├── auditor.py       # Logic auditing (Phase 2)
│   │   ├── bias_detector.py # Bias detection (Phase 2)
│   │   ├── chain_validator.py # Chain validation (Phase 2)
│   │   └── source_checker.py  # Source verification (Phase 2)
│   ├── rag/
│   │   ├── ingest.py        # Document ingestion (Phase 4)
│   │   └── query.py         # Embedding & similarity search (Phase 4)
│   ├── tools/               # Tool registry (stub)
│   └── logs/
│       ├── veritas_brain.log        # Brain operations
│       ├── veritas_contributions.log # Analysis audit trail
│       └── rag_query.log            # RAG query logs
├── memory/
│   └── long/
│       └── veritas_corpus.jsonl  # Document corpus storage
├── tests/
│   ├── test_brain.py        # Brain unit tests (Phase 3)
│   ├── test_rag.py          # RAG system tests (Phase 4)
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

### Phase 5 (Planned)

- External API integration (optional)
- Real-time source verification
- Content fetching and analysis
- Fact-checking capabilities

### Phase 6 (Planned)

- Enhanced pattern libraries
- Confidence calibration
- Cross-document analysis
- Performance optimization

## Disclaimer

Phase 4 analysis is heuristic-based and deterministic. Results should be interpreted as indicators, not definitive assessments. The tool does not make external requests or fetch content - it analyzes text structure and patterns only. The RAG system uses simple embeddings and should not be considered production-grade semantic search.
