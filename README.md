# DocuMind - AI-Powered Knowledge Management System

Build an intelligent Q&A system for company documents using Claude, RAG, and agentic engineering.

## What is DocuMind?

DocuMind is an AI chatbot that answers questions from your company's documents.
Ask questions in natural language, get accurate answers with source citations.
DocuMind is the accompany software to the HeroForge Agentic AI Engineering Course.

## What You'll Build (Sessions 3-10)

| Session | Topic | What You'll Create |
|---------|-------|-------------------|
| S3 | Skills, Subagents, Hooks | Document upload pipeline |
| S4 | Database & MCP | Supabase integration |
| S5 | Multi-Agent Systems | Parallel document processing |
| S6 | RAG Implementation | Q&A interface |
| S7 | Advanced Parsing | PDF/DOCX support |
| S8 | Vector Databases | Semantic search |
| S9 | Memory & Learning | Conversation memory |
| S10 | Evaluation | Quality metrics |

## Quick Start

1. **Fork this repository** to your GitHub account
2. **Launch in Codespaces:** Click green `Code` button → `Codespaces` → `Create codespace on main`
3. **Follow setup guide:** See `docs/guides/SETUP.md`
4. **Workshop files will be released by your instructor post lesson (in docs/workshops/)**
5. **Follow the instrucitons in docs/workshops/Student-Workshops-SOP.md**

## Prerequisites

- Basic Python & JavaScript knowledge
- GitHub account (free)
- Anthropic API key (free tier available)
- OpenAI API key (pay-as-you-go)

## Project Structure

```
heroforge-documind/
├── .claude/              # Claude Code configuration
│   ├── agents/          # AI agent definitions
│   ├── skills/          # Custom skills (you'll create these!)
│   ├── subagents/       # Specialized agents (you'll create these!)
│   └── hooks/           # Automation scripts (you'll create these!)
├── src/
│   └── documind/        # Main DocuMind application code
├── tests/               # Test files
├── docs/
│   └── guides/          # Setup and troubleshooting guides
├── .env.example         # Template for environment variables
└── package.json         # Node.js dependencies
```

## Technologies

- **Claude Code** - AI-powered development assistant
- **Supabase** - PostgreSQL database with pgvector for semantic search
- **OpenRouter** - Multi-model LLM access (GPT-4, Gemini, etc.)
- **RAGAS** - Evaluation framework for RAG systems

## RAG Q&A System

### Overview

The RAG (Retrieval-Augmented Generation) Q&A system enables natural language querying of your document knowledge base. It combines semantic search with LLM generation to provide accurate, citation-backed answers from your uploaded documents.

**Key Features:**
- Semantic and hybrid search for relevant document retrieval
- Re-ranking algorithm for improved relevance
- Automatic citation extraction with `[Source X]` references
- Multi-model support (Claude, GPT-4, Gemini)
- Query logging and analytics
- Graceful handling of out-of-scope questions

### Architecture

The RAG pipeline consists of four main components:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Embeddings │ --> │  Retriever  │ --> │ LLM Client  │ --> │  QA System  │
│  (OpenAI)   │     │  (Supabase) │     │ (OpenRouter)│     │ (Production)│
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

| Component | Description | Location |
|-----------|-------------|----------|
| **Embeddings** | Converts text to vectors using OpenAI's `text-embedding-3-small` model | `src/documind/rag/search.py` |
| **Retriever** | Performs semantic/hybrid search against Supabase pgvector | `src/documind/rag/search.py` |
| **LLM Client** | Generates answers via OpenRouter (Claude, GPT-4, Gemini) | `src/documind/rag/production_qa.py` |
| **QA System** | Orchestrates the full pipeline with citations and logging | `src/documind/rag/production_qa.py` |

### Quick Start

Run the RAG Q&A system from the command line:

```bash
# Single question mode
python -m src.documind.rag.production_qa "What is the vacation policy?"

# Interactive mode
python -m src.documind.rag.production_qa

# Compare multiple models
python -m src.documind.rag.production_qa "What benefits do employees get?" --compare

# Use hybrid search (semantic + keyword)
python -m src.documind.rag.production_qa "remote work policy" --hybrid

# View analytics
python -m src.documind.rag.production_qa --analytics 7
```

### Configuration

The RAG system requires the following environment variables in your `.env` file:

```bash
# Required: Vector embeddings
OPENAI_API_KEY=sk-...

# Required: LLM inference
OPENROUTER_API_KEY=sk-or-...

# Required: Vector database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
```

**Available Models:**

| Key | Model ID | Best For |
|-----|----------|----------|
| `claude` | `anthropic/claude-3.5-sonnet` | Accuracy, reasoning |
| `gpt4` | `openai/gpt-4-turbo` | General purpose |
| `gemini` | `google/gemini-pro` | Speed, cost |

### Example Usage

```python
from documind.rag.production_qa import ProductionQA

# Initialize the Q&A system
qa = ProductionQA(default_model='claude')

# Ask a question
result = qa.query(
    question="How many vacation days do employees get?",
    top_k=5,           # Number of documents to retrieve
    use_hybrid=False   # Set True for hybrid search
)

# Access the response
print(result["answer"])
# "According to [Source 1], employees receive 15 days of paid vacation..."

print(result["citations"])
# [{"citation_id": 1, "document": "hr_policy.pdf", "chunk": 3, "similarity": 0.92}]

print(result["sources"])
# List of retrieved document chunks with metadata

# Compare multiple models
comparison = qa.compare_models(
    question="What is the remote work policy?",
    models=['claude', 'gpt4', 'gemini']
)

for model, response in comparison["results"].items():
    print(f"{model}: {response['answer'][:100]}...")
```

**Response Structure:**

```python
{
    "answer": "According to [Source 1], ...",  # Generated answer with citations
    "citations": [...],                         # List of cited sources
    "sources": [...],                           # All retrieved documents
    "query": "original question",               # Input question
    "model": "anthropic/claude-3.5-sonnet",    # Model used
    "search_type": "semantic",                  # semantic or hybrid
    "context_chunks": 5,                        # Documents used
    "response_time": 2.341,                     # Seconds
    "timestamp": "2024-01-20T10:30:00"         # ISO timestamp
}
```

### Testing

Run the RAG integration tests:

```bash
# Run all RAG tests
pytest tests/test_rag_integration.py -v

# Run specific test class
pytest tests/test_rag_integration.py::TestCitationsIncluded -v

# Run with coverage
pytest tests/test_rag_integration.py --cov=src/documind/rag

# Run the full test suite including unit tests
pytest tests/rag/ -v
```

**Test Coverage:**
- Question answering with relevant context
- Document retrieval and relevance ranking
- Citation extraction and validation
- Out-of-scope question handling
- End-to-end pipeline integrity

## Environment Setup

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Add your API keys to .env file

# 3. Install dependencies
npm install

# 4. Run tests
npm test

# 5. Launch Claude Code
dsp
```

## Getting Help

- **Workshop issues:** Raise your hand or ask your instructor
- **Technical bugs:** Create a GitHub Issue in your fork
- **Course questions:** Ask in the course chat/Discord

## License

MIT License - See [LICENSE](LICENSE) file
