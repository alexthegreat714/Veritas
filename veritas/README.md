# Veritas - AI Senate Truth Auditor

Veritas is the AI Senate member responsible for truth auditing, logic checking, bias detection, and chain-of-thought validation. It serves as the analytical backbone for verifying claims, detecting logical fallacies, and ensuring the integrity of reasoning processes.

## Current Status: Phase 2

**Phase 2 implements deterministic, heuristic-based analysis tools.**

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
│   ├── routes/veritas.py    # API endpoints
│   ├── logic/
│   │   ├── auditor.py       # Logic auditing (Phase 2)
│   │   ├── bias_detector.py # Bias detection (Phase 2)
│   │   ├── chain_validator.py # Chain validation (Phase 2)
│   │   └── source_checker.py  # Source verification (Phase 2)
│   ├── rag/                 # RAG system (stub)
│   ├── tools/               # Tool registry (stub)
│   ├── memory/              # Memory storage
│   └── logs/                # Application logs
├── tests/                   # Test suite
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

### Phase 3 (Planned)

- Enhanced pattern libraries
- Confidence calibration
- Cross-tool integration
- Performance optimization

### Phase 4 (Planned)

- RAG system implementation
- Embedding generation
- Vector store integration
- Semantic search functionality

### Phase 5 (Planned)

- External API integration (optional)
- Real-time source verification
- Content fetching and analysis
- Fact-checking capabilities

## Disclaimer

Phase 2 analysis is heuristic-based and deterministic. Results should be interpreted as indicators, not definitive assessments. The tool does not make external requests or fetch content - it analyzes text structure and patterns only.
