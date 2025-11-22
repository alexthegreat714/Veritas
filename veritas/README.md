# Veritas - AI Senate Truth Auditor

Veritas is the AI Senate member responsible for truth auditing, logic checking, bias detection, and chain-of-thought validation. It serves as the analytical backbone for verifying claims, detecting logical fallacies, and ensuring the integrity of reasoning processes.

## Purpose

Veritas provides the following core capabilities:

- **Truth Auditing**: Analyze text for factual accuracy and logical consistency
- **Logic Checking**: Identify logical fallacies, contradictions, and unsupported claims
- **Bias Detection**: Detect political, emotional, and selection biases in content
- **Chain-of-Thought Validation**: Verify the logical flow and coherence of reasoning chains
- **Source Verification**: Assess source credibility and cross-reference claims

## Phase 1 Status

**This is Phase 1 of Veritas development.**

Phase 1 contains only scaffolding and stub implementations. All endpoints and logic modules return placeholder responses. No actual truth auditing, bias detection, or validation logic is implemented yet.

### What's Included in Phase 1

- Complete project structure and module organization
- FastAPI application with all planned endpoints
- Stub implementations for all logic modules
- RAG system scaffolding (no embeddings or retrieval)
- Test scaffolding with passing tests for stub responses
- Configuration management structure

### What's NOT Included in Phase 1

- Actual logic auditing algorithms
- Real bias detection models
- Chain validation logic
- Source verification functionality
- RAG embeddings and retrieval
- External API integrations

## Installation

### Requirements

- Python 3.10+
- pip

### Setup

1. Clone the repository and navigate to the veritas directory:

```bash
cd veritas
```

2. Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Server

Start the FastAPI server with:

```bash
uvicorn app.main:app --reload
```

The server will start at `http://localhost:8000`.

### API Documentation

Once running, access the interactive API documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service information |
| `/health` | GET | Health check |
| `/status` | GET | Component status |
| `/run_task` | POST | Execute a task |
| `/shutdown` | POST | Initiate shutdown |
| `/event` | POST | Submit an event |
| `/audit_text` | POST | Audit text for truth/logic |
| `/validate_chain` | POST | Validate reasoning chain |
| `/check_sources` | POST | Verify source credibility |

## Project Structure

```
veritas/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings
│   ├── routes/
│   │   └── veritas.py       # API route handlers
│   ├── tools/
│   │   └── __init__.py      # Tool registry (future)
│   ├── logic/
│   │   ├── auditor.py       # Logic auditing
│   │   ├── bias_detector.py # Bias detection
│   │   ├── chain_validator.py # Chain validation
│   │   └── source_checker.py  # Source verification
│   ├── rag/
│   │   ├── ingest.py        # Document ingestion
│   │   └── query.py         # Semantic search
│   ├── memory/
│   │   ├── short/           # Short-term memory storage
│   │   └── long/            # Long-term memory storage
│   └── logs/                # Application logs
├── tests/
│   ├── conftest.py          # Test fixtures
│   ├── test_endpoints.py    # API endpoint tests
│   ├── test_auditor.py      # Auditor tests
│   ├── test_bias.py         # Bias detector tests
│   └── test_chain_validator.py # Chain validator tests
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Running Tests

Execute the test suite with pytest:

```bash
pytest tests/ -v
```

## Roadmap

### Phase 2 (Planned)

- Implement logic auditing algorithms
- Add fallacy detection patterns
- Develop claim extraction
- Integrate consistency checking

### Phase 3 (Planned)

- Implement bias detection models
- Add political bias analysis
- Develop emotional bias detection
- Create selection bias identification

### Phase 4 (Planned)

- Implement chain validation logic
- Add gap detection algorithms
- Develop circular reasoning detection
- Integrate hidden assumption extraction

### Phase 5 (Planned)

- Implement source verification
- Add credibility scoring
- Develop cross-reference checking
- Integrate citation validation

### Phase 6 (Planned)

- RAG system implementation
- Embedding generation
- Vector store integration
- Semantic search functionality

## Design Philosophy

Veritas is designed to be:

- **Analytical**: Focused on factual accuracy and logical rigor
- **Objective**: No emotional or narrative behavior
- **Systematic**: Structured approach to truth verification
- **Transparent**: Clear reasoning and source attribution

## License

[License information to be added]

## Contributing

[Contributing guidelines to be added]
