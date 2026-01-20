# DocuMind Pipeline Components Implementation Plan

## Executive Summary

This implementation plan details the development of DocuMind's 5-component document processing pipeline using Goal-Oriented Action Planning (GOAP) methodology. The pipeline transforms uploaded documents into searchable, vector-embedded knowledge base entries through a hierarchical multi-agent architecture.

**Planning Date:** 2025-12-16
**Target Completion:** 5 development sprints (estimated 2-3 weeks)
**Methodology:** GOAP with SPARC (Specification, Pseudocode, Architecture, Refinement, Completion)

---

## GOAP State Analysis

### Current State (What is true now)
- Supabase database configured with `documents` table
- Environment variables set (OPENAI_API_KEY, SUPABASE_URL, SUPABASE_ANON_KEY)
- Project structure established with `/src/agents/pipeline/` directory
- Demo documents available in `/demo-docs/` for testing
- DocuMind PRD defines requirements and success metrics

### Goal State (What should be true)
- 5 pipeline components operational: Extractor, Chunker, Embedder, Writer, Orchestrator
- End-to-end document processing: Upload → Extract → Chunk → Embed → Store
- Parallel processing capability (10+ documents simultaneously)
- Error handling and recovery mechanisms implemented
- Performance metrics: 100+ docs/hour, < 3s average processing time
- All components tested and verified in Supabase

### Gap Analysis (What needs to happen)
1. Create `document_chunks` table with pgvector support
2. Implement 5 specialized agent scripts with JSON I/O interfaces
3. Build asyncio coordination for parallel execution
4. Add error handling, retry logic, and circuit breakers
5. Integrate OpenAI embeddings API (text-embedding-3-small)
6. Establish validation and testing framework

---

## Pipeline Components Overview

### Component Topology (Hierarchical Pipeline)

```
User Upload Request
        ↓
   Orchestrator (coordinates workflow)
        ↓
   Extractor (parallel: multiple files)
        ↓
   Chunker (parallel: multiple documents)
        ↓
   Embedder (parallel: batch embeddings)
        ↓
   Writer (parallel: database writes)
        ↓
   Orchestrator (completion report)
```

### Communication Pattern
- **Data Flow:** Sequential stages with parallel execution within each stage
- **Interface:** JSON input/output for all components
- **State Management:** Shared memory keys for cross-agent coordination
- **Error Handling:** Stage-level isolation prevents cascade failures

---

## Component 1: Extractor Agent

### Overview
Reads files in multiple formats and extracts raw text with metadata. Expertise in file format handling (PDF, DOCX, XLSX, TXT, MD).

### GOAP Definition

**Goal:** Extract text and metadata from uploaded documents
**Preconditions:**
- File path provided and file exists
- File format is supported (.pdf, .docx, .xlsx, .txt, .md)
- File is readable (permissions, not corrupted)

**Actions:**
1. Detect file format from extension
2. Route to format-specific parser
3. Extract text content
4. Extract metadata (title, author, created_date, page_count)
5. Return structured JSON output

**Effects:**
- Raw text available for chunking
- Metadata stored for context
- Shared memory key `extraction/raw_text/{document_id}` populated

**Success Criteria:**
- Handles all 5 formats correctly
- Preserves document structure (headings, paragraphs)
- Extracts metadata when available
- Returns error details for unsupported formats
- Processing time < 200ms per document (excluding large PDFs)

### Technical Requirements

**Dependencies:**
```python
# File parsing libraries
PyPDF2==3.0.1           # Simple PDF extraction
pdfplumber==0.10.3      # Complex PDF (tables, layouts)
python-docx==1.1.0      # Word documents
openpyxl==3.1.2         # Excel files
pandas==2.1.4           # Spreadsheet processing
```

**Input Format:**
```json
{
  "file_path": "/path/to/document.pdf",
  "document_id": "uuid-string",
  "options": {
    "extract_images": false,
    "preserve_formatting": true
  }
}
```

**Output Format:**
```json
{
  "success": true,
  "document_id": "uuid-string",
  "text": "Extracted content...",
  "metadata": {
    "title": "Document Title",
    "file_type": "pdf",
    "page_count": 42,
    "word_count": 5234,
    "created_at": "2024-01-15T10:30:00Z",
    "author": "John Doe"
  },
  "extraction_time_ms": 145
}
```

### Implementation Steps

**Milestone 1.1: Basic Text Extraction (Priority: High)**
1. Create `src/agents/pipeline/extractor.py`
2. Implement TXT and MD parsers (simplest formats)
3. Add JSON input/output interface
4. Test with demo documents

**Milestone 1.2: PDF Support (Priority: High)**
1. Integrate PyPDF2 for simple PDFs
2. Add pdfplumber for complex layouts
3. Extract page numbers and structure
4. Test with multi-page PDFs

**Milestone 1.3: Office Formats (Priority: Medium)**
1. Add python-docx for DOCX files
2. Implement openpyxl for XLSX files
3. Handle embedded objects and formatting
4. Test with real-world documents

**Milestone 1.4: Metadata Enrichment (Priority: Low)**
1. Extract document properties
2. Calculate word/sentence counts
3. Identify language (if detectable)
4. Add content summary (first 200 chars)

### Testing Approach

**Unit Tests:**
```python
def test_extractor_txt():
    result = extract_text("demo-docs/sample.txt")
    assert result["success"] == True
    assert "text" in result
    assert result["metadata"]["file_type"] == "txt"

def test_extractor_pdf():
    result = extract_text("demo-docs/policy.pdf")
    assert result["metadata"]["page_count"] > 0

def test_extractor_unsupported_format():
    result = extract_text("demo-docs/image.png")
    assert result["success"] == False
    assert "Unsupported format" in result["error"]
```

**Integration Tests:**
- Process all files in `demo-docs/` directory
- Verify no crashes on corrupted files
- Check metadata extraction accuracy

---

## Component 2: Chunker Agent

### Overview
Splits extracted text into semantic chunks of approximately 500 words with 50-word overlap. Expertise in text segmentation and semantic boundaries.

### GOAP Definition

**Goal:** Create optimally-sized chunks for embedding and retrieval
**Preconditions:**
- Raw text available from Extractor
- Text length > 0 characters
- Target chunk size configured (default: 500 words)

**Actions:**
1. Receive extracted text from Extractor
2. Identify semantic boundaries (paragraphs, sentences)
3. Split text into chunks with overlap
4. Assign chunk indices and positions
5. Calculate chunk metadata (word count, character count)

**Effects:**
- Text divided into retrievable units
- Chunk overlap enables context preservation
- Shared memory key `chunking/chunks/{document_id}` populated

**Success Criteria:**
- Chunks average 450-550 words (target: 500)
- 50-word overlap between adjacent chunks
- Semantic boundaries preserved (no mid-sentence cuts)
- Maintains document structure in metadata
- Processing time < 100ms per document

### Technical Requirements

**Dependencies:**
```python
# Text processing
nltk==3.8.1             # Sentence tokenization
spacy==3.7.2            # Advanced NLP (optional)
tiktoken==0.5.2         # Token counting for embeddings
```

**Input Format:**
```json
{
  "document_id": "uuid-string",
  "text": "Full extracted text...",
  "metadata": {
    "title": "Document Title",
    "file_type": "pdf"
  },
  "options": {
    "chunk_size": 500,
    "chunk_overlap": 50,
    "strategy": "semantic"
  }
}
```

**Output Format:**
```json
{
  "success": true,
  "document_id": "uuid-string",
  "chunks": [
    {
      "chunk_index": 0,
      "content": "First chunk text...",
      "word_count": 487,
      "char_count": 3245,
      "start_position": 0,
      "end_position": 3245,
      "metadata": {
        "section": "Introduction",
        "page": 1
      }
    },
    {
      "chunk_index": 1,
      "content": "Second chunk with overlap...",
      "word_count": 512,
      "char_count": 3401,
      "start_position": 2845,
      "end_position": 6246,
      "metadata": {
        "section": "Introduction",
        "page": 1
      }
    }
  ],
  "total_chunks": 2,
  "chunking_time_ms": 78
}
```

### Implementation Steps

**Milestone 2.1: Fixed-Size Chunking (Priority: High)**
1. Create `src/agents/pipeline/chunker.py`
2. Implement basic word-count splitting
3. Add overlap logic
4. Test chunk size distribution

**Milestone 2.2: Semantic Boundary Detection (Priority: High)**
1. Integrate NLTK sentence tokenizer
2. Split on paragraph boundaries first
3. Ensure no mid-sentence cuts
4. Test with complex documents

**Milestone 2.3: Structure Preservation (Priority: Medium)**
1. Track headings and sections
2. Include page numbers in metadata
3. Preserve list and table markers
4. Test structure retention

**Milestone 2.4: Adaptive Chunking (Priority: Low)**
1. Adjust chunk size based on content type
2. Optimize for embedding model limits (8192 tokens)
3. Add chunk quality scoring
4. Test with varied document types

### Testing Approach

**Unit Tests:**
```python
def test_chunker_size():
    chunks = chunk_text("Long text...", chunk_size=500)
    assert all(450 <= c["word_count"] <= 550 for c in chunks)

def test_chunker_overlap():
    chunks = chunk_text("Text with overlap...")
    # Verify last 50 words of chunk[0] match first 50 of chunk[1]
    assert has_overlap(chunks[0], chunks[1], overlap=50)

def test_chunker_semantic_boundaries():
    chunks = chunk_text("Sentence one. Sentence two.")
    # No chunk should end mid-sentence
    assert all(c["content"].strip()[-1] in ".!?" for c in chunks)
```

**Integration Tests:**
- Process extracted text from all demo documents
- Verify total word count preservation (overlap accounted for)
- Check chunk distribution (histogram)

---

## Component 3: Embedder Agent

### Overview
Generates vector embeddings for text chunks using OpenAI's text-embedding-3-small model (1536 dimensions). Expertise in embedding generation and batch optimization.

### GOAP Definition

**Goal:** Convert text chunks to vector embeddings for semantic search
**Preconditions:**
- Chunks available from Chunker
- OpenAI API key configured
- API rate limits not exceeded
- Chunk text < 8192 tokens

**Actions:**
1. Receive chunks from Chunker
2. Batch chunks for API efficiency (max 100 per request)
3. Call OpenAI embeddings API
4. Validate embedding dimensions (1536)
5. Return embeddings with chunk metadata

**Effects:**
- Each chunk has corresponding 1536-dim vector
- Embeddings stored for similarity search
- Shared memory key `embeddings/vectors/{document_id}` populated

**Success Criteria:**
- All chunks successfully embedded
- Embedding dimension = 1536
- API calls batched (100 chunks max per call)
- Error handling for API failures
- Processing time < 500ms per batch (100 chunks)

### Technical Requirements

**Dependencies:**
```python
# OpenAI API
openai==1.7.2           # Official OpenAI client
tenacity==8.2.3         # Retry logic
```

**API Configuration:**
```python
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
BATCH_SIZE = 100
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds
```

**Input Format:**
```json
{
  "document_id": "uuid-string",
  "chunks": [
    {
      "chunk_index": 0,
      "content": "Text to embed...",
      "metadata": {}
    }
  ],
  "options": {
    "model": "text-embedding-3-small",
    "batch_size": 100
  }
}
```

**Output Format:**
```json
{
  "success": true,
  "document_id": "uuid-string",
  "embeddings": [
    {
      "chunk_index": 0,
      "embedding": [0.023, -0.145, 0.678, ...],  // 1536 floats
      "model": "text-embedding-3-small",
      "tokens_used": 487
    }
  ],
  "total_embeddings": 1,
  "total_tokens": 487,
  "api_calls": 1,
  "embedding_time_ms": 234
}
```

### Implementation Steps

**Milestone 3.1: Basic Embedding (Priority: High)**
1. Create `src/agents/pipeline/embedder.py`
2. Integrate OpenAI SDK
3. Implement single-chunk embedding
4. Test with sample text

**Milestone 3.2: Batch Processing (Priority: High)**
1. Add batch logic (100 chunks per API call)
2. Implement error handling
3. Test with large document sets
4. Verify token counting

**Milestone 3.3: Retry and Resilience (Priority: High)**
1. Add exponential backoff (1s, 2s, 4s)
2. Implement retry logic (max 3 attempts)
3. Handle rate limiting
4. Test failure scenarios

**Milestone 3.4: Cost Optimization (Priority: Medium)**
1. Track token usage per document
2. Add cost estimation
3. Implement caching for duplicate text
4. Log API usage metrics

### Testing Approach

**Unit Tests:**
```python
def test_embedder_single_chunk():
    result = generate_embeddings([{"content": "Test text"}])
    assert result["success"] == True
    assert len(result["embeddings"][0]["embedding"]) == 1536

def test_embedder_batch():
    chunks = [{"content": f"Text {i}"} for i in range(150)]
    result = generate_embeddings(chunks)
    assert result["api_calls"] == 2  # 100 + 50

def test_embedder_retry_on_failure():
    # Mock API failure
    with patch("openai.embeddings.create", side_effect=APIError):
        result = generate_embeddings([{"content": "test"}])
        assert result["success"] == False
        assert "retries" in result["error"]
```

**Integration Tests:**
- Process chunks from real documents
- Verify embedding quality (spot check similarity)
- Test API rate limit handling

---

## Component 4: Writer Agent

### Overview
Stores document records and embedded chunks in Supabase with transactional safety. Expertise in database operations and data integrity.

### GOAP Definition

**Goal:** Persist documents and chunks to database for retrieval
**Preconditions:**
- Supabase connection established
- `documents` table exists
- `document_chunks` table with pgvector extension exists
- Embeddings available from Embedder
- Document ID is unique

**Actions:**
1. Receive document metadata and chunks with embeddings
2. Begin database transaction
3. Insert/update `documents` table
4. Batch insert `document_chunks` table
5. Commit transaction
6. Return database record IDs

**Effects:**
- Document record created in `documents` table
- Chunks with embeddings stored in `document_chunks` table
- Data queryable via Supabase API
- Shared memory key `database/write_status/{document_id}` confirmed

**Success Criteria:**
- Transactional integrity (all-or-nothing writes)
- Batch insert for performance (50+ chunks per transaction)
- Duplicate document handling (update vs insert)
- Error rollback on failure
- Processing time < 200ms per document

### Technical Requirements

**Dependencies:**
```python
# Supabase client
supabase==2.3.2         # Official Python client
postgrest==0.13.1       # PostgreSQL REST API
```

**Database Schema:**
```sql
-- Ensure this schema exists before Writer operations
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  file_path TEXT,
  file_type TEXT,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS document_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL,
  content TEXT NOT NULL,
  embedding vector(1536),
  word_count INTEGER,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Vector index for semantic search
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
ON document_chunks
USING hnsw (embedding vector_cosine_ops);
```

**Input Format:**
```json
{
  "document": {
    "id": "uuid-string",
    "title": "Document Title",
    "content": "Full text...",
    "file_path": "/path/to/doc.pdf",
    "file_type": "pdf",
    "metadata": {
      "author": "John Doe",
      "page_count": 42
    }
  },
  "chunks": [
    {
      "chunk_index": 0,
      "content": "Chunk text...",
      "embedding": [0.023, -0.145, ...],
      "word_count": 487,
      "metadata": {
        "section": "Introduction"
      }
    }
  ]
}
```

**Output Format:**
```json
{
  "success": true,
  "document_id": "uuid-string",
  "chunks_written": 42,
  "database_ids": {
    "document": "uuid-doc-id",
    "chunks": ["uuid-1", "uuid-2", ...]
  },
  "write_time_ms": 156
}
```

### Implementation Steps

**Milestone 4.1: Basic Document Write (Priority: High)**
1. Create `src/agents/pipeline/writer.py`
2. Initialize Supabase client
3. Implement document insert
4. Test with sample data

**Milestone 4.2: Chunk Batch Writing (Priority: High)**
1. Add chunk insertion logic
2. Implement batch writes (50 chunks per batch)
3. Test with large chunk sets
4. Verify vector data integrity

**Milestone 4.3: Transaction Safety (Priority: High)**
1. Wrap operations in transactions
2. Add rollback on error
3. Handle duplicate documents (upsert)
4. Test failure scenarios

**Milestone 4.4: Performance Optimization (Priority: Medium)**
1. Optimize batch sizes
2. Add connection pooling
3. Implement write caching
4. Test concurrent writes

### Testing Approach

**Unit Tests:**
```python
def test_writer_document():
    result = write_document({
        "title": "Test Doc",
        "content": "Content...",
        "file_type": "txt"
    })
    assert result["success"] == True
    assert "document_id" in result

def test_writer_chunks():
    chunks = [{"chunk_index": i, "content": f"Chunk {i}"}
              for i in range(50)]
    result = write_chunks("doc-id", chunks)
    assert result["chunks_written"] == 50

def test_writer_transaction_rollback():
    # Simulate failure mid-transaction
    with pytest.raises(Exception):
        write_document_with_invalid_chunk()
    # Verify no partial data in database
    assert get_document_by_id("invalid-id") is None
```

**Integration Tests:**
- Write complete pipeline output to database
- Verify data retrievable via Supabase API
- Test concurrent write operations
- Validate vector index creation

---

## Component 5: Orchestrator Agent

### Overview
Coordinates the full pipeline workflow with parallel processing, error recovery, and performance monitoring. Expertise in workflow management and system coordination.

### GOAP Definition

**Goal:** Process documents end-to-end with maximum efficiency and reliability
**Preconditions:**
- All 4 pipeline components (Extractor, Chunker, Embedder, Writer) operational
- File paths provided or directory specified
- Environment variables configured
- Database tables exist

**Actions:**
1. Receive upload request (single file or batch)
2. Initialize processing queue
3. Spawn parallel Extractor tasks
4. Coordinate data flow: Extract → Chunk → Embed → Write
5. Handle errors and retries
6. Generate completion report

**Effects:**
- Multiple documents processed concurrently
- End-to-end pipeline execution
- Performance metrics collected
- Errors logged and reported
- Processing status available in real-time

**Success Criteria:**
- Parallel processing (10+ documents simultaneously)
- Average processing time < 3 seconds per document
- Throughput > 100 documents per hour
- Error isolation (one failure doesn't stop batch)
- Comprehensive reporting (success/fail counts, timing, bottlenecks)

### Technical Requirements

**Dependencies:**
```python
# Async processing
asyncio==3.11           # Built-in async/await
aiohttp==3.9.1          # Async HTTP (for API calls)
aiometer==0.4.0         # Async semaphore management
```

**Input Format:**
```bash
# CLI Interface
python orchestrate.py <file_or_directory> [options]

Options:
  -d, --directory          Process all files in directory
  --max-parallel N         Max concurrent documents (default: 10)
  --continue-on-error      Continue batch on individual failures
  --json-output PATH       Save results to JSON file
  --verbose                Show detailed progress
```

**Output Format:**
```json
{
  "summary": {
    "total_documents": 16,
    "successful": 15,
    "failed": 1,
    "total_time_seconds": 42.5,
    "avg_time_per_document": 2.66
  },
  "performance": {
    "throughput_docs_per_second": 0.38,
    "stage_times": {
      "extraction_avg_ms": 145,
      "chunking_avg_ms": 78,
      "embedding_avg_ms": 1234,
      "writing_avg_ms": 156
    },
    "bottleneck": "embedding"
  },
  "results": [
    {
      "file_path": "demo-docs/doc1.pdf",
      "status": "success",
      "document_id": "uuid-1",
      "chunks_created": 12,
      "processing_time_ms": 2456
    },
    {
      "file_path": "demo-docs/corrupt.pdf",
      "status": "failed",
      "error": "PDF extraction failed: File corrupted"
    }
  ],
  "errors_by_stage": {
    "extraction": 1,
    "chunking": 0,
    "embedding": 0,
    "writing": 0
  }
}
```

### Implementation Steps

**Milestone 5.1: Sequential Pipeline (Priority: High)**
1. Create `src/agents/pipeline/orchestrate.py`
2. Implement sequential workflow: Extract → Chunk → Embed → Write
3. Add CLI argument parsing
4. Test with single document

**Milestone 5.2: Parallel Processing (Priority: High)**
1. Convert to async/await pattern
2. Use asyncio.gather for concurrency
3. Add semaphore for max parallel limit
4. Test with batch of 20+ documents

**Milestone 5.3: Error Handling (Priority: High)**
1. Wrap each stage in try/except
2. Implement continue-on-error mode
3. Add retry logic (max 3 attempts)
4. Test failure scenarios

**Milestone 5.4: Monitoring and Reporting (Priority: Medium)**
1. Track processing times per stage
2. Identify bottlenecks automatically
3. Generate formatted report
4. Add JSON export option

**Milestone 5.5: Production Features (Priority: Low)**
1. Add circuit breaker pattern
2. Implement processing queue persistence
3. Add health check endpoint
4. Create performance dashboard

### Testing Approach

**Unit Tests:**
```python
async def test_orchestrator_single_document():
    result = await process_document("demo-docs/sample.txt")
    assert result["status"] == "success"
    assert result["chunks_created"] > 0

async def test_orchestrator_batch_parallel():
    files = ["demo-docs/doc1.md", "demo-docs/doc2.md"]
    start = time.time()
    results = await process_batch(files, max_parallel=2)
    duration = time.time() - start
    # Should be faster than sequential (2x files)
    assert duration < sum(r["processing_time_ms"] for r in results) / 1000

async def test_orchestrator_error_isolation():
    files = ["demo-docs/good.md", "demo-docs/corrupt.pdf"]
    results = await process_batch(files, continue_on_error=True)
    assert any(r["status"] == "success" for r in results)
    assert any(r["status"] == "failed" for r in results)
```

**Integration Tests:**
- Process entire `demo-docs/` directory (16 files)
- Verify all stages complete successfully
- Check database for stored documents and chunks
- Validate performance metrics (throughput, bottlenecks)

---

## Cross-Component Integration

### Data Flow Validation

**End-to-End Test Scenario:**
```python
async def test_full_pipeline_integration():
    # 1. Start with uploaded file
    file_path = "demo-docs/remote-work-policy.md"

    # 2. Extract
    extracted = extract_text(file_path)
    assert extracted["success"] == True

    # 3. Chunk
    chunked = chunk_text(extracted["text"])
    assert chunked["total_chunks"] > 0

    # 4. Embed
    embedded = await generate_embeddings(chunked["chunks"])
    assert all(len(e["embedding"]) == 1536 for e in embedded["embeddings"])

    # 5. Write
    written = await write_chunks(extracted["document_id"], embedded["embeddings"])
    assert written["chunks_written"] == chunked["total_chunks"]

    # 6. Verify in database
    db_chunks = supabase.table("document_chunks").select("*").eq("document_id", extracted["document_id"]).execute()
    assert len(db_chunks.data) == chunked["total_chunks"]
```

### Shared Memory Coordination

**Memory Keys Schema:**
```python
# Document processing state
pipeline/status/{document_id}       # "extracting" | "chunking" | "embedding" | "writing" | "complete"
pipeline/errors/{document_id}       # Array of error objects

# Stage outputs
extraction/raw_text/{document_id}   # Full extracted text
extraction/metadata/{document_id}   # File metadata
chunking/chunks/{document_id}       # Array of chunks
chunking/strategy/{document_id}     # "semantic" | "fixed-size"
embeddings/vectors/{document_id}    # Array of embeddings
embeddings/model/{document_id}      # "text-embedding-3-small"
database/write_status/{document_id} # "pending" | "success" | "failed"
database/record_ids/{document_id}   # Database UUIDs
```

### Performance Benchmarks

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Extraction Speed | < 200ms/doc | Time from file read to JSON output |
| Chunking Speed | < 100ms/doc | Time from text input to chunks output |
| Embedding Speed | < 500ms/batch | Time for 100 chunks (OpenAI API) |
| Writing Speed | < 200ms/doc | Time to commit to Supabase |
| Total Processing | < 3s/doc | End-to-end orchestrator time |
| Throughput | > 100 docs/hour | Batch processing rate |
| Parallel Capacity | 10+ concurrent | Max documents in flight |

---

## Dependencies and Preconditions

### Environment Setup

**Required Environment Variables:**
```bash
# API Keys
OPENAI_API_KEY=sk-xxxxx           # For embeddings
ANTHROPIC_API_KEY=sk-ant-xxxxx    # For future RAG

# Supabase Configuration
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJxxxxx
SUPABASE_SERVICE_KEY=eyJxxxxx     # For admin operations

# Pipeline Configuration (optional)
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
CHUNK_SIZE=500
CHUNK_OVERLAP=50
MAX_PARALLEL_DOCS=10
```

**Database Preconditions:**
```sql
-- Execute before running pipeline
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('documents', 'document_chunks');

-- Verify vector index
SELECT indexname
FROM pg_indexes
WHERE tablename = 'document_chunks'
AND indexname = 'document_chunks_embedding_idx';
```

### Python Environment

**Create Virtual Environment:**
```bash
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Install Dependencies:**
```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
# Core dependencies
openai==1.7.2
supabase==2.3.2
python-dotenv==1.0.0

# File parsing
PyPDF2==3.0.1
pdfplumber==0.10.3
python-docx==1.1.0
openpyxl==3.1.2
pandas==2.1.4

# Text processing
nltk==3.8.1
tiktoken==0.5.2

# Async and resilience
aiohttp==3.9.1
tenacity==8.2.3

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
```

---

## Implementation Timeline

### Sprint 1: Foundation (Days 1-3)
- Set up project structure
- Create database schema (document_chunks table)
- Implement Extractor (Milestones 1.1-1.2)
- **Deliverable:** Extract text from TXT, MD, PDF files

### Sprint 2: Text Processing (Days 4-6)
- Implement Chunker (Milestones 2.1-2.2)
- Add semantic boundary detection
- Test chunk size distribution
- **Deliverable:** Text chunking with overlap

### Sprint 3: Embeddings (Days 7-9)
- Implement Embedder (Milestones 3.1-3.3)
- Add batch processing and retry logic
- Test with OpenAI API
- **Deliverable:** Vector embeddings generation

### Sprint 4: Database (Days 10-12)
- Implement Writer (Milestones 4.1-4.3)
- Add transactional safety
- Test data integrity
- **Deliverable:** Persistent storage in Supabase

### Sprint 5: Orchestration (Days 13-16)
- Implement Orchestrator (Milestones 5.1-5.4)
- Add parallel processing
- Create monitoring dashboard
- **Deliverable:** End-to-end pipeline with reporting

### Sprint 6: Enhancement (Days 17-20)
- Add production features (circuit breaker, health checks)
- Performance optimization
- Comprehensive testing
- **Deliverable:** Production-ready pipeline

---

## Success Metrics

### Functional Requirements
- [ ] All 5 components implemented and tested
- [ ] Processes 5 file formats: PDF, DOCX, XLSX, TXT, MD
- [ ] Chunks average 500 words with 50-word overlap
- [ ] Embeddings are 1536-dimensional vectors
- [ ] Data persists correctly in Supabase

### Performance Requirements
- [ ] Average processing time < 3 seconds per document
- [ ] Throughput > 100 documents per hour
- [ ] Parallel processing capacity: 10+ concurrent documents
- [ ] Error rate < 5% (excluding corrupted files)

### Quality Requirements
- [ ] Test coverage > 80%
- [ ] All error cases handled gracefully
- [ ] Comprehensive logging and monitoring
- [ ] Documentation complete (README, API docs)

### Validation Tests
```bash
# End-to-end validation
python src/agents/pipeline/orchestrate.py demo-docs/ --json-output results.json

# Verify results
cat results.json | jq '.summary'
# Expected:
# {
#   "total_documents": 16,
#   "successful": 16,
#   "failed": 0,
#   "avg_time_per_document": 2.5
# }

# Check database
npx @supabase/supabase-js exec "SELECT COUNT(*) FROM document_chunks;"
# Expected: 16+ chunks
```

---

## Risk Mitigation

### Risk 1: OpenAI API Rate Limits
**Probability:** Medium
**Impact:** High (blocks embeddings)
**Mitigation:**
- Implement exponential backoff (1s, 2s, 4s)
- Add request queuing with rate limiter
- Monitor API usage and set alerts
- Consider caching embeddings for duplicates

### Risk 2: Large File Processing Failures
**Probability:** Medium
**Impact:** Medium (some documents fail)
**Mitigation:**
- Set max file size limit (100MB)
- Implement timeout for extraction (30s)
- Add memory monitoring
- Process large files in separate queue

### Risk 3: Database Write Failures
**Probability:** Low
**Impact:** High (data loss)
**Mitigation:**
- Use transactions with rollback
- Implement write-ahead logging
- Add database connection pooling
- Test disaster recovery

### Risk 4: Chunk Quality Issues
**Probability:** Medium
**Impact:** Medium (poor retrieval)
**Mitigation:**
- Validate chunk sizes programmatically
- Add quality scoring for chunks
- Test with diverse document types
- Implement adaptive chunking strategies

---

## Appendix A: Agent Interfaces Contract

### Extractor Interface
```python
class ExtractorAgent:
    def extract_text(self, file_path: str) -> dict:
        """Extract text and metadata from file."""
        pass

    def supported_formats(self) -> list[str]:
        """Return list of supported file extensions."""
        return [".pdf", ".docx", ".xlsx", ".txt", ".md"]
```

### Chunker Interface
```python
class ChunkerAgent:
    def chunk_text(self, text: str, strategy: str = "semantic") -> list[dict]:
        """Split text into semantic chunks."""
        pass

    def optimize_chunk_size(self, text: str) -> int:
        """Calculate optimal chunk size for document."""
        pass
```

### Embedder Interface
```python
class EmbedderAgent:
    async def generate_embeddings(self, chunks: list[str]) -> list[list[float]]:
        """Generate embeddings for text chunks."""
        pass

    def batch_optimize(self, chunks: list[str]) -> int:
        """Calculate optimal batch size for API."""
        pass
```

### Writer Interface
```python
class WriterAgent:
    async def write_chunks(self, document_id: str, chunks: list[dict]) -> bool:
        """Write chunks to document_chunks table."""
        pass

    async def transaction_safe_write(self, data: dict) -> bool:
        """Write with automatic rollback on error."""
        pass
```

### Orchestrator Interface
```python
class OrchestratorAgent:
    async def process_document(self, file_path: str) -> dict:
        """Process single document through pipeline."""
        pass

    async def process_batch(self, file_paths: list[str]) -> dict:
        """Process multiple documents in parallel."""
        pass
```

---

## Appendix B: Testing Strategy

### Unit Testing
- Test each component in isolation
- Mock external dependencies (API calls, database)
- Verify edge cases and error handling
- Target: 80%+ code coverage

### Integration Testing
- Test component interactions
- Verify data flow between stages
- Test with real API calls (separate test environment)
- Validate database operations

### Performance Testing
- Benchmark each component individually
- Test parallel processing capacity
- Measure throughput and latency
- Identify bottlenecks

### End-to-End Testing
- Process complete document sets
- Verify data in Supabase
- Test error recovery
- Validate reporting accuracy

---

## Appendix C: Monitoring and Observability

### Metrics to Track
```python
# Processing metrics
documents_processed_total
documents_failed_total
processing_time_seconds (histogram)
chunks_created_total
embeddings_generated_total
api_calls_total

# Performance metrics
stage_duration_seconds{stage="extraction|chunking|embedding|writing"}
parallel_capacity_current
queue_length_current

# Error metrics
errors_by_stage{stage="extraction|chunking|embedding|writing"}
api_errors_total{api="openai|supabase"}
retry_attempts_total
```

### Logging Strategy
```python
import logging

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)

# Log key events
logger.info("Processing document", extra={
    "document_id": doc_id,
    "file_path": path,
    "file_size": size
})

logger.error("Extraction failed", extra={
    "document_id": doc_id,
    "error": str(e),
    "stage": "extraction"
})
```

---

## Document Control

**Version:** 1.0
**Created:** 2025-12-16
**Author:** GOAP Planning Agent (Claude Opus 4.5)
**Reviewed By:** [Pending]
**Approved By:** [Pending]

**Change Log:**
- 2025-12-16 v1.0: Initial plan created with GOAP methodology

**Next Review Date:** After Sprint 3 completion

---

## References

1. DocuMind PRD: `/workspaces/heroforge-documind/docs/spec/documind-prd.md`
2. S5 Workshop: `/workspaces/heroforge-documind/docs/workshops/S5-Workshop.md`
3. OpenAI Embeddings API: https://platform.openai.com/docs/guides/embeddings
4. Supabase pgvector: https://supabase.com/docs/guides/database/extensions/pgvector
5. GOAP Methodology: https://en.wikipedia.org/wiki/Goal-oriented_action_planning

---

**END OF IMPLEMENTATION PLAN**
