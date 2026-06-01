# PDF Multi-Agent Extraction System

A near production-ready, fully local PDF extraction pipeline using multi-agent orchestration. No API keys, no cloud dependencies — runs entirely on your machine with open-source tools.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PDF Extraction Pipeline                   │
├─────────────────────────────────────────────────────────────┤
│  Supervisor → Extractor → Validator → [Synthesizer/Retry]   │
│                                                             │
│  • Docling/PyPDF2  → PDF parsing                            │
│  • Ollama (local)  → LLM inference & embeddings             │
│  • ChromaDB        → Vector storage                         │
│  • LangGraph       → Agent orchestration                    │
│  • React + FastAPI → Web UI & API                           │
└─────────────────────────────────────────────────────────────┘
```

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Multi-Agent Pipeline** | Supervisor, Extractor, Validator, Synthesizer agents with LangGraph |
| **Local LLM** | Uses Ollama (llama3.2:1b, nomic-embed-text) — no API keys |
| **Memory-Safe Extraction** | Auto-fallback from Docling to PyPDF2 on low memory |
| **Quality Validation** | Automatic validation with retry on low confidence |
| **Semantic Search** | Search across all extracted documents with natural language |
| **Real-Time UI** | Live workflow visualization, agent logs, confidence metrics |
| **CPU-Optimized** | Runs on CPU-only systems with limited RAM |

## 📁 Project Structure

```
pdf_multiagent/
├── src/
│   ├── api/
│   │   └── main.py              # FastAPI application
│   ├── agents/
│   │   ├── supervisor.py        # Workflow orchestrator
│   │   ├── extractor.py         # PDF extraction agent
│   │   ├── validator.py         # Quality validation agent
│   │   └── synthesizer.py       # Final output agent
│   ├── graph/
│   │   └── workflow.py          # LangGraph state machine
│   ├── tools/
│   │   ├── pdf_tools.py         # Docling/PyPDF2 extraction
│   │   ├── llm_tools.py         # Ollama client
│   │   └── vector_tools.py      # ChromaDB operations
│   ├── config.py                # Pydantic settings
│   ├── models.py                # Data schemas
│   └── state.py                 # LangGraph state definitions
├── ui/                          # React frontend
│   ├── src/
│   │   ├── components/          # UI components
│   │   ├── pages/               # Page views
│   │   ├── api.ts               # API client
│   │   └── types.ts             # TypeScript types
│   └── package.json
├── test/
│   └── test_integration.py      # Integration tests
├── .env.example                 # Environment template
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Docker orchestration
└── Dockerfile                   # API container
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for UI)
- [Ollama](https://ollama.com/) installed

### 1. Clone & Setup

```bash
git clone https://github.com/starkjiang/agentic_local_document_extraction.git
cd pdf_multiagent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings (or leave defaults)
```

### 3. Start Ollama & Pull Models

```bash
# Start Ollama server
ollama serve

# In another terminal, pull models
ollama pull llama3.2:1b
ollama pull nomic-embed-text
```

### 4. Start the API

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

API will be available at `http://localhost:8000`

### 5. Start the UI (New Terminal)

```bash
cd ui
npm install
npm start
```

UI will open at `http://localhost:3000`

---

## 🐳 Docker Setup

No test yet.

```bash
# Start everything (API + Ollama + ChromaDB)
docker-compose up

# Pull models into Ollama container
docker exec -it pdf_agent_ollama ollama pull llama3.2:1b
docker exec -it pdf_agent_ollama ollama pull nomic-embed-text
```

---

## 🧪 Testing

```bash
# Run integration tests
pytest test/test_integration.py -v

# Run with output visible
pytest test/test_integration.py -v -s
```

---

## 🔧 Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `llama3.2:1b` | Main LLM for synthesis |
| `OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model for search |
| `DOCLING_DEVICE` | `cpu` | `cpu` or `cuda` |
| `CHUNK_SIZE` | `512` | Text chunk size for vectors |
| `MAX_FILE_SIZE_MB` | `50` | Max upload size |
| `MAX_RETRIES` | `3` | Extraction retry attempts |

See `.env.example` for all options.

---

## 🖥️ API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | System health check |
| `POST` | `/extract` | Upload & extract PDF |
| `GET` | `/status/{job_id}` | Check job status |
| `GET` | `/result/{job_id}/markdown` | Get markdown output |
| `GET` | `/result/{job_id}/json` | Get structured JSON |
| `POST` | `/query` | Semantic search |
| `GET` | `/jobs` | List all jobs |
| `DELETE` | `/jobs/{job_id}` | Delete job |

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| `std::bad_alloc` / Out of memory | Docling auto-falls back to PyPDF2; reduce `CHUNK_SIZE` |
| `ollama` not found | Add Ollama to PATH or use full path |
| `None is not a valid ExtractionStrategy` | Fixed — strategy defaults to `auto` |
| API silently crashes | Check available RAM; fallback extractor handles low memory |
| CORS errors | API allows all origins in development |

---

## 📄 License

MIT License — open source, free to use and modify.

## 🤝 Contributing

Pull requests welcome. Please run tests before submitting:

```bash
pytest
```

## 🙏 Acknowledgments

- [Docling](https://github.com/DS4SD/docling) — IBM's document parser
- [LangGraph](https://github.com/langchain-ai/langgraph) — Agent orchestration
- [Ollama](https://ollama.com/) — Local LLM inference
- [ChromaDB](https://www.trychroma.com/) — Vector database
