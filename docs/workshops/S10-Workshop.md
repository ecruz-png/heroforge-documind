# HeroForge.AI Course: AI-Powered Software Development
## Lesson 10 Workshop: Evaluation & Optimization Tools

**Workshop Duration:** 60 minutes\
**Structure:** 4 modules × 15 minutes each\
**Goal:** Build complete evaluation system for DocuMind

---

## Before You Begin: Plan Your Work!

> **📋 Reminder:** In Session 3, we learned about **Issue-Driven Development** - the practice of creating GitHub Issues *before* starting work. This ensures clear requirements, enables collaboration, and creates traceability between your code and original requirements.
>
> **Before diving into this workshop:**
> 1. Create a GitHub Issue for the features you'll build today
> 2. Reference that issue in your branch name (`issue-XX-feature-name`)
> 3. Include `Closes #XX` or `Relates to #XX` in your commit messages
>
> 👉 See [S3-Workshop: Planning Your Work with GitHub Issues](./S3-Workshop.md#planning-your-work-with-github-issues-5-minutes) for the full workflow.

---

## Workshop Overview

By the end of this workshop, you will have:
- ✅ Implemented RAGAS evaluation pipeline
- ✅ Integrated TruLens monitoring
- ✅ Created A/B testing framework
- ✅ Set up quality gates in CI/CD
- ✅ Built evaluation dashboard
- ✅ Deployed production monitoring

---

## Prerequisites Check (Before Starting)

**🖥️ Run in Terminal:**
```bash
# Verify installations
python --version  # Should be 3.10+
pip list | grep -i ragas  # Should show ragas installed (install with: pip install ragas)
pip list | grep -i trulens  # Should show trulens-eval installed (install with: pip install trulens-eval)

# Verify DocuMind modules from prior sessions are working
cd /workspaces/heroforge-documind
python -c "from src.documind.hybrid_search import HybridSearcher; print('✅ Ready')"
```

---

### ⚠️ Important: Search Response Format

Before implementing evaluation, understand how DocuMind search returns data:

**Search Response Structure:**
```python
# DocuMind search returns a wrapper object
search_result = search_service.search(query)

# Response structure:
{
    "success": True,
    "documents": [
        {"id": "...", "content": "...", "score": 0.92},
        {"id": "...", "content": "...", "score": 0.88}
    ],
    "count": 2
}
```

**Common Error:** Passing the full response to evaluators expecting a list:
```python
# ❌ WRONG - RAGAS expects a list, not a dict
contexts = search_result  # This will fail!

# ✅ CORRECT - Unwrap the documents
contexts = search_result['documents']
```

**Helper Function Pattern:**
```python
def unwrap_search_response(response):
    """Extract documents list from search response wrapper."""
    if isinstance(response, dict) and 'documents' in response:
        return response['documents']
    # Fallback if already a list
    return response if isinstance(response, list) else []
```

Use this pattern whenever passing search results to RAGAS or other evaluators.

---

## Module 1: RAGAS Evaluation Implementation (15 minutes)

### Learning Objectives
- Understand RAGAS metrics
- Create evaluation dataset
- Implement RAGASEvaluator class
- Run first evaluation

### Exercise 1.1: Create Test Dataset (5 minutes)

**Task:** Create a comprehensive test dataset with 10 queries covering different types.

**🖥️ Run in Terminal:**
```bash
# Create directories for this workshop
mkdir -p data results scripts src/evaluation

# Create test dataset
cat > data/evaluation_dataset.json << 'EOF'
[
  {
    "question": "What is DocuMind and what is it used for?",
    "ground_truth": "DocuMind is a RAG-based document question-answering system that uses PostgreSQL with pgvector for semantic search and Claude API for answer generation. It's used for querying knowledge bases and extracting information from documents."
  },
  {
    "question": "How do I configure the chunk size for document processing?",
    "ground_truth": "Configure chunk size by setting CHUNK_SIZE in config/settings.py. The default is 512 tokens. You can also adjust CHUNK_OVERLAP to control how much adjacent chunks overlap."
  },
  {
    "question": "What embedding model does DocuMind use by default?",
    "ground_truth": "DocuMind uses OpenAI's text-embedding-3-large model by default for generating vector embeddings of text chunks and queries."
  },
  {
    "question": "Explain how the RAG pipeline works step by step.",
    "ground_truth": "The RAG pipeline works in three steps: 1) Embed the user query using the embedding model, 2) Retrieve semantically similar document chunks using pgvector cosine similarity search, 3) Generate an answer using Claude API with the retrieved chunks as context."
  },
  {
    "question": "What database technology powers DocuMind's vector search?",
    "ground_truth": "DocuMind uses PostgreSQL with the pgvector extension for storing document chunks and performing vector similarity search."
  },
  {
    "question": "How many chunks are retrieved for each query by default?",
    "ground_truth": "By default, DocuMind retrieves the top 3 most semantically similar chunks for each query, though this can be configured in the settings."
  },
  {
    "question": "What API does DocuMind use for answer generation?",
    "ground_truth": "DocuMind uses the Anthropic Claude API (Claude 3.5 Sonnet model) for generating answers based on retrieved context."
  },
  {
    "question": "Can DocuMind process PDF files?",
    "ground_truth": "Yes, DocuMind can process PDF files along with other formats like DOCX, TXT, and Markdown. It extracts text and chunks it for vector storage."
  },
  {
    "question": "How does DocuMind handle conversation history?",
    "ground_truth": "DocuMind stores conversation history in the conversations and messages tables, allowing it to maintain context across multiple turns in a conversation."
  },
  {
    "question": "What is the capital of Mars?",
    "ground_truth": "This question cannot be answered from the DocuMind documentation as it is outside the scope of the system's knowledge base."
  }
]
EOF

echo "✅ Test dataset created with 10 queries"
```

**Expected Output:**
```
✅ Test dataset created with 10 queries
```

### Exercise 1.2: Implement RAGASEvaluator (5 minutes)

**Task:** Create production-ready evaluation class.

**📝 Create file `src/evaluation/ragas_evaluator.py` using Claude Code or your editor:**
```python
# src/evaluation/ragas_evaluator.py
from typing import List, Dict
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from datasets import Dataset
import json
from datetime import datetime

class RAGASEvaluator:
    """Production RAGAS evaluator for DocuMind"""
    
    def __init__(self, rag_pipeline):
        self.rag_pipeline = rag_pipeline
        self.metrics = [
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall
        ]
    
    def evaluate(self, test_dataset: List[Dict]) -> Dict:
        """Run RAGAS evaluation on test dataset"""
        print(f"\n{'='*60}")
        print(f"RAGAS EVALUATION STARTED: {datetime.now()}")
        print(f"{'='*60}")
        print(f"Test cases: {len(test_dataset)}")
        
        # TODO: Generate answers for each test case
        # For each test_case in test_dataset:
        #   1. Call self.rag_pipeline.answer(test_case['question'])
        #   2. Extract contexts from result['retrieved_chunks']
        #   3. Add to test_case as 'contexts' and 'answer'
        
        # TODO: Convert to Dataset and run evaluate()
        # dataset = Dataset.from_list(test_dataset)
        # results = evaluate(dataset=dataset, metrics=self.metrics)
        
        # TODO: Format and return results
        pass
    
    def format_results(self, results: Dict) -> Dict:
        """Format RAGAS results with pass/fail indicators"""
        # TODO: Extract metrics and calculate average
        # TODO: Add pass/fail flags based on thresholds
        pass
```

**Your Task:** Complete the TODOs in the code above.

**Solution:**

```python
def evaluate(self, test_dataset: List[Dict]) -> Dict:
    """Run RAGAS evaluation on test dataset"""
    print(f"\n{'='*60}")
    print(f"RAGAS EVALUATION STARTED: {datetime.now()}")
    print(f"{'='*60}")
    print(f"Test cases: {len(test_dataset)}")
    
    # Generate answers for each test case
    for i, test_case in enumerate(test_dataset, 1):
        print(f"[{i}/{len(test_dataset)}] {test_case['question'][:60]}...")
        
        result = self.rag_pipeline.answer(test_case['question'])
        
        test_case['contexts'] = [
            chunk['chunk_text'] 
            for chunk in result.get('retrieved_chunks', [])
        ]
        test_case['answer'] = result['answer']
    
    # Run RAGAS evaluation
    print("\nRunning RAGAS metrics...")
    dataset = Dataset.from_list(test_dataset)
    results = evaluate(dataset=dataset, metrics=self.metrics)
    
    return self.format_results(results)

def format_results(self, results: Dict) -> Dict:
    """Format RAGAS results with pass/fail indicators"""
    formatted = {
        'faithfulness': float(results['faithfulness']),
        'answer_relevancy': float(results['answer_relevancy']),
        'context_precision': float(results['context_precision']),
        'context_recall': float(results['context_recall'])
    }
    
    # Calculate average
    formatted['average_score'] = sum(formatted.values()) / len(formatted)
    
    # Add pass/fail
    thresholds = {
        'faithfulness': 0.90,
        'answer_relevancy': 0.85,
        'context_precision': 0.80,
        'context_recall': 0.85
    }
    
    formatted['passed'] = all(
        formatted[metric] >= threshold 
        for metric, threshold in thresholds.items()
    )
    
    return formatted
```

### Exercise 1.3: Run Evaluation (5 minutes)

**Task:** Run complete evaluation and analyze results.

**🖥️ Run in Terminal:**
```bash
# Create evaluation runner
cat > scripts/run_evaluation.py << 'EOF'
import json
import sys
sys.path.append('src')

from evaluation.ragas_evaluator import RAGASEvaluator
from rag.pipeline import DocuMindRAGPipeline

# Load test dataset
with open('data/evaluation_dataset.json', 'r') as f:
    test_dataset = json.load(f)

# Initialize
rag = DocuMindRAGPipeline()
evaluator = RAGASEvaluator(rag)

# Run evaluation
results = evaluator.evaluate(test_dataset)

# Display results
print("\n" + "="*60)
print("EVALUATION RESULTS")
print("="*60)

for metric in ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']:
    score = results[metric]
    status = "✅" if score >= {'faithfulness': 0.90, 'answer_relevancy': 0.85, 
                               'context_precision': 0.80, 'context_recall': 0.85}[metric] else "❌"
    print(f"{metric:.<25} {score:.3f} {status}")

print(f"\nAverage Score: {results['average_score']:.3f}")
print(f"Overall Status: {'✅ PASSED' if results['passed'] else '❌ FAILED'}")

# Save results
with open('results/evaluation_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\n📁 Results saved to results/evaluation_results.json")
EOF

# Run it
python scripts/run_evaluation.py
```

**Expected Output:**
```
============================================================
RAGAS EVALUATION STARTED: 2025-01-15 10:30:45
============================================================
Test cases: 10
[1/10] What is DocuMind and what is it used for?...
[2/10] How do I configure the chunk size for document processing?...
...
[10/10] What is the capital of Mars?...

Running RAGAS metrics...

============================================================
EVALUATION RESULTS
============================================================
faithfulness............. 0.918 ✅
answer_relevancy......... 0.893 ✅
context_precision........ 0.847 ✅
context_recall........... 0.901 ✅

Average Score: 0.890
Overall Status: ✅ PASSED

📁 Results saved to results/evaluation_results.json
```

### Module 1 Quiz

**Question 1:** What does RAGAS faithfulness metric measure?\
- A) How fast the RAG system responds\
- B) Whether the answer is grounded in retrieved context\
- C) The quality of the question\
- D) The size of the knowledge base

**Answer:** B - Faithfulness measures whether the answer is supported by the retrieved context, detecting hallucinations.

**Question 2:** What is the target threshold for answer relevancy?\
- A) ≥0.75\
- B) ≥0.80\
- C) ≥0.85\
- D) ≥0.90

**Answer:** C - Answer relevancy should be ≥0.85 to ensure responses properly address the question.

**Question 3:** Which metric would detect if your retrieval system is missing critical information?\
- A) Faithfulness\
- B) Answer Relevancy\
- C) Context Precision\
- D) Context Recall

**Answer:** D - Context Recall measures whether all necessary context was retrieved.

---

## Module 2: TruLens Monitoring Integration (15 minutes)

### Learning Objectives
- Integrate TruLens with DocuMind
- Define custom feedback functions
- Launch monitoring dashboard
- Analyze real-time metrics

### Exercise 2.1: TruLens Wrapper (7 minutes)

**Task:** Create TruLens wrapper with feedback functions.

**📝 Create file `src/evaluation/trulens_monitor.py` using Claude Code or your editor:**
```python
# src/evaluation/trulens_monitor.py
from trulens_eval import TruCustomApp, Feedback, Tru
from trulens_eval.feedback.provider import OpenAI
import numpy as np

class DocuMindTruLens:
    """TruLens monitoring for DocuMind RAG"""
    
    def __init__(self, rag_pipeline):
        self.rag = rag_pipeline
        self.provider = OpenAI()
        self.tru = Tru()
        
        # TODO: Define feedback functions
        # 1. Groundedness feedback
        # 2. Answer relevance feedback  
        # 3. Context relevance feedback
        
        # TODO: Create TruCustomApp recorder
        
    def query(self, question: str):
        """Run monitored query"""
        # TODO: Wrap query with TruLens recording
        pass
    
    def launch_dashboard(self):
        """Launch TruLens Streamlit dashboard"""
        self.tru.run_dashboard()
```

**Your Task:** Complete the implementation.

**Solution:**

```python
class DocuMindTruLens:
    def __init__(self, rag_pipeline):
        self.rag = rag_pipeline
        self.provider = OpenAI()
        self.tru = Tru()
        
        # Define feedback functions
        self.feedbacks = [
            Feedback(
                self.provider.groundedness_measure_with_cot_reasons
            ).on_output().on(
                lambda x: [c['chunk_text'] for c in x.get('retrieved_chunks', [])]
            ).aggregate(np.mean),
            
            Feedback(
                self.provider.relevance
            ).on_input().on_output(),
            
            Feedback(
                self.provider.context_relevance_with_cot_reasons
            ).on_input().on(
                lambda x: [c['chunk_text'] for c in x.get('retrieved_chunks', [])]
            ).aggregate(np.mean)
        ]
        
        # Create recorder
        self.tru_recorder = TruCustomApp(
            self.rag,
            app_id="DocuMind_RAG_Production",
            feedbacks=self.feedbacks
        )
        
        print("✅ TruLens monitoring initialized")
        print(f"📊 Dashboard: http://localhost:8501")
    
    def query(self, question: str):
        """Run monitored query"""
        with self.tru_recorder as recording:
            return self.rag.answer(question)
```

### Exercise 2.2: Run Monitored Queries (5 minutes)

**Task:** Run queries with TruLens monitoring.

**🖥️ Run in Terminal:**
```bash
# Create monitoring demo
cat > scripts/monitor_queries.py << 'EOF'
import sys
sys.path.append('src')

from evaluation.trulens_monitor import DocuMindTruLens
from rag.pipeline import DocuMindRAGPipeline

# Initialize
rag = DocuMindRAGPipeline()
monitor = DocuMindTruLens(rag)

# Sample queries
queries = [
    "What is DocuMind?",
    "How does vector search work?",
    "Explain the chunking process",
    "What models are used?",
    "How do I configure the system?"
]

print("\n" + "="*60)
print("RUNNING MONITORED QUERIES")
print("="*60)

for i, query in enumerate(queries, 1):
    print(f"\n[{i}/{len(queries)}] {query}")
    result = monitor.query(query)
    print(f"✓ Answer length: {len(result['answer'])} chars")
    print(f"✓ Retrieved: {len(result.get('retrieved_chunks', []))} chunks")

print("\n" + "="*60)
print("✅ All queries monitored and logged")
print("📊 View dashboard: python -c \"from trulens_eval import Tru; Tru().run_dashboard()\"")
print("="*60)
EOF

python scripts/monitor_queries.py
```

**Expected Output:**
```
✅ TruLens monitoring initialized
📊 Dashboard: http://localhost:8501

============================================================
RUNNING MONITORED QUERIES
============================================================

[1/5] What is DocuMind?
✓ Answer length: 243 chars
✓ Retrieved: 3 chunks

[2/5] How does vector search work?
✓ Answer length: 312 chars
✓ Retrieved: 4 chunks

[3/5] Explain the chunking process
✓ Answer length: 278 chars
✓ Retrieved: 3 chunks

[4/5] What models are used?
✓ Answer length: 198 chars
✓ Retrieved: 2 chunks

[5/5] How do I configure the system?
✓ Answer length: 356 chars
✓ Retrieved: 4 chunks

============================================================
✅ All queries monitored and logged
📊 View dashboard: python -c "from trulens_eval import Tru; Tru().run_dashboard()"
============================================================
```

### Exercise 2.3: Explore Dashboard (3 minutes)

**Task:** Launch TruLens dashboard and explore features.

**🖥️ Run in Terminal:**
```bash
# Launch dashboard
python -c "from trulens_eval import Tru; Tru().run_dashboard()"
```

**Dashboard Exploration Checklist:**
- [ ] View app leaderboard
- [ ] Check average groundedness score
- [ ] Explore individual query traces
- [ ] Review feedback function outputs
- [ ] Compare metrics across queries

### Module 2 Quiz

**Question 1:** What runs TruLens feedback functions?\
- A) Synchronously during the query\
- B) Asynchronously after the response\
- C) Only when requested manually\
- D) In a separate database

**Answer:** B - Feedback functions run asynchronously so they don't add latency to user responses.

**Question 2:** What does TruLens groundedness measure?\
- A) Whether the system is grounded to earth\
- B) Whether the answer is supported by context\
- C) The speed of response\
- D) The database connection

**Answer:** B - Groundedness checks if the answer is supported by the retrieved context.

**Question 3:** How do you launch the TruLens dashboard?\
- A) `streamlit run trulens`\
- B) `trulens dashboard`\
- C) `Tru().run_dashboard()`\
- D) `python dashboard.py`

**Answer:** C - Use `Tru().run_dashboard()` to launch the Streamlit dashboard.

---

## Module 3: A/B Testing & Quality Gates (15 minutes)

### Learning Objectives
- Implement model comparison framework
- Create quality gate checker
- Integrate with CI/CD
- Interpret A/B test results

### Exercise 3.1: A/B Testing Framework (7 minutes)

**Task:** Build model comparison system.

**📝 Create file `src/evaluation/ab_testing.py` using Claude Code or your editor:**
```python
# src/evaluation/ab_testing.py
from typing import List, Dict
from evaluation.ragas_evaluator import RAGASEvaluator
import json
import time

class ABTester:
    """A/B testing framework for model comparison"""
    
    def __init__(self):
        self.models = {}
        self.results = {}
    
    def add_model(self, name: str, rag_pipeline):
        """Add model to comparison"""
        self.models[name] = rag_pipeline
        print(f"➕ Added model: {name}")
    
    def run_comparison(self, test_dataset: List[Dict]) -> List[Dict]:
        """Compare all models on same dataset"""
        # TODO: For each model:
        #   1. Create RAGASEvaluator
        #   2. Run evaluation
        #   3. Track timing
        #   4. Store results
        
        # TODO: Return sorted comparison report
        pass
    
    def print_comparison(self, results: List[Dict]):
        """Print formatted comparison table"""
        # TODO: Print table with metrics for each model
        pass
```

**Complete the implementation and test:**

**🖥️ Run in Terminal:**
```bash
# Test A/B comparison
cat > scripts/ab_test.py << 'EOF'
import json
import sys
sys.path.append('src')

from evaluation.ab_testing import ABTester
from rag.pipeline import DocuMindRAGPipeline

# Load dataset
with open('data/evaluation_dataset.json', 'r') as f:
    test_dataset = json.load(f)[:5]  # Use 5 queries for speed

# Setup comparison
tester = ABTester()

# Add models
claude_rag = DocuMindRAGPipeline(model="claude-3-5-sonnet-20241022")
tester.add_model("Claude 3.5 Sonnet", claude_rag)

# You would add other models here:
# gpt4_rag = DocuMindRAGPipeline(model="gpt-4-turbo")
# tester.add_model("GPT-4 Turbo", gpt4_rag)

# Run comparison
results = tester.run_comparison(test_dataset)
tester.print_comparison(results)

# Save results
with open('results/ab_test_results.json', 'w') as f:
    json.dump(results, f, indent=2)
EOF

python scripts/ab_test.py
```

### Exercise 3.2: Quality Gates (5 minutes)

**Task:** Implement automated quality gates.

**📝 Create file `src/evaluation/quality_gate.py` using Claude Code or your editor:**
```python
# src/evaluation/quality_gate.py
from typing import Dict
import sys

class QualityGate:
    """Quality gate checker for CI/CD"""
    
    THRESHOLDS = {
        'faithfulness': 0.90,
        'answer_relevancy': 0.85,
        'context_precision': 0.80,
        'context_recall': 0.85
    }
    
    def check(self, results: Dict) -> bool:
        """Check if results pass quality gates"""
        print("\n" + "="*60)
        print("🚦 QUALITY GATE CHECK")
        print("="*60)
        
        all_passed = True
        
        for metric, threshold in self.THRESHOLDS.items():
            actual = results.get(metric, 0)
            passed = actual >= threshold
            status = "✅ PASS" if passed else "❌ FAIL"
            
            print(f"{metric:.<25} {actual:.3f} (≥{threshold:.2f}) {status}")
            
            if not passed:
                all_passed = False
                gap = threshold - actual
                print(f"  ⚠️ Below threshold by {gap:.3f}")
        
        print("="*60)
        
        if all_passed:
            print("✅ QUALITY GATE PASSED - Deployment allowed")
        else:
            print("❌ QUALITY GATE FAILED - Deployment blocked")
        
        return all_passed

# CLI usage
if __name__ == "__main__":
    import json
    
    with open('results/evaluation_results.json', 'r') as f:
        results = json.load(f)
    
    gate = QualityGate()
    passed = gate.check(results)
    
    sys.exit(0 if passed else 1)
```

**Test quality gate:**

**🖥️ Run in Terminal:**
```bash
# Test with current results
python src/evaluation/quality_gate.py
echo "Exit code: $?"

# Test with failing results
cat > results/bad_results.json << 'EOF'
{
  "faithfulness": 0.76,
  "answer_relevancy": 0.81,
  "context_precision": 0.73,
  "context_recall": 0.78
}
EOF

python -c "
import json
import sys
sys.path.append('src')
from evaluation.quality_gate import QualityGate

with open('results/bad_results.json', 'r') as f:
    results = json.load(f)

gate = QualityGate()
passed = gate.check(results)
sys.exit(0 if passed else 1)
"

echo "Exit code: $?"
```

### Exercise 3.3: CI/CD Integration (3 minutes)

**Task:** Create GitHub Actions workflow.

**📝 Create file `.github/workflows/evaluate.yml` using Claude Code or your editor:**
```yaml
# .github/workflows/evaluate.yml
name: RAG Quality Evaluation

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # Daily

jobs:
  evaluate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install ragas trulens-eval
      
      - name: Run evaluation
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python scripts/run_evaluation.py
      
      - name: Check quality gates
        run: python src/evaluation/quality_gate.py
      
      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: evaluation-results
          path: results/
```

### Module 3 Quiz

**Question 1:** What is the purpose of quality gates?\
- A) To make CI/CD slower\
- B) To automatically block deployments that don't meet quality standards\
- C) To generate reports\
- D) To test network latency

**Answer:** B - Quality gates automatically prevent deploying code that doesn't meet minimum quality thresholds.

**Question 2:** In A/B testing, what should you keep constant?\
- A) The model being tested\
- B) The test dataset\
- C) The time of day\
- D) The developer running the test

**Answer:** B - Use the exact same test dataset for fair comparison between models.

**Question 3:** What exit code should quality gate return on failure?\
- A) 0\
- B) 1\
- C) -1\
- D) 404

**Answer:** B - Exit code 1 indicates failure in CI/CD systems, blocking deployment.

---

## Module 4: Production Deployment (15 minutes)

### Learning Objectives
- Set up evaluation database
- Create monitoring dashboard
- Implement alerting system
- Deploy complete evaluation system

### Exercise 4.1: Database Setup (5 minutes)

**Task:** Create evaluation tracking schema.

**🗄️ Run in SQL Editor (Supabase SQL Editor, pgAdmin, or psql):**
```sql
-- Create schema for evaluation tracking
CREATE TABLE IF NOT EXISTS evaluation_runs (
    id SERIAL PRIMARY KEY,
    run_name VARCHAR(255),
    model_name VARCHAR(100),
    faithfulness DECIMAL(5,4),
    answer_relevancy DECIMAL(5,4),
    context_precision DECIMAL(5,4),
    context_recall DECIMAL(5,4),
    average_score DECIMAL(5,4),
    test_dataset_size INT,
    passed BOOLEAN,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS query_evaluations (
    id SERIAL PRIMARY KEY,
    evaluation_run_id INT REFERENCES evaluation_runs(id),
    question TEXT,
    answer TEXT,
    retrieved_contexts JSONB,
    faithfulness_score DECIMAL(5,4),
    answer_relevancy_score DECIMAL(5,4),
    latency_ms INT,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_evaluation_timestamp 
ON evaluation_runs(timestamp DESC);

CREATE INDEX idx_evaluation_passed 
ON evaluation_runs(passed);

-- View for trend analysis
CREATE OR REPLACE VIEW evaluation_trends AS
SELECT 
    DATE(timestamp) as eval_date,
    model_name,
    AVG(faithfulness) as avg_faithfulness,
    AVG(answer_relevancy) as avg_answer_relevancy,
    AVG(average_score) as avg_score,
    COUNT(*) as num_runs
FROM evaluation_runs
GROUP BY DATE(timestamp), model_name
ORDER BY eval_date DESC;
```

**Create storage class:**

**📝 Create file `src/evaluation/storage.py` using Claude Code or your editor:**
```python
# src/evaluation/storage.py
import psycopg2
import json
from typing import Dict, List
from datetime import datetime

class EvaluationStorage:
    """Store evaluation results in PostgreSQL"""
    
    def __init__(self, db_connection_string: str):
        self.conn = psycopg2.connect(db_connection_string)
    
    def save_run(self, run_name: str, model_name: str, 
                 results: Dict, test_dataset: List[Dict]) -> int:
        """Save evaluation run to database"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO evaluation_runs
                (run_name, model_name, faithfulness, answer_relevancy,
                 context_precision, context_recall, average_score,
                 test_dataset_size, passed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                run_name,
                model_name,
                results['faithfulness'],
                results['answer_relevancy'],
                results['context_precision'],
                results['context_recall'],
                results['average_score'],
                len(test_dataset),
                results['passed']
            ))
            
            run_id = cur.fetchone()[0]
            
            # Save individual queries
            for item in test_dataset:
                cur.execute("""
                    INSERT INTO query_evaluations
                    (evaluation_run_id, question, answer, 
                     retrieved_contexts, faithfulness_score,
                     answer_relevancy_score)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    run_id,
                    item['question'],
                    item.get('answer', ''),
                    json.dumps(item.get('contexts', [])),
                    item.get('faithfulness_score', 0),
                    item.get('answer_relevancy_score', 0)
                ))
        
        self.conn.commit()
        return run_id
    
    def get_recent_runs(self, limit: int = 10):
        """Get recent evaluation runs"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM evaluation_runs
                ORDER BY timestamp DESC
                LIMIT %s
            """, (limit,))
            return cur.fetchall()
```

### Exercise 4.2: Monitoring Dashboard (5 minutes)

**Task:** Create Streamlit evaluation dashboard.

**📝 Create file `src/dashboard/evaluation_dashboard.py` using Claude Code or your editor:**
```python
# src/dashboard/evaluation_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from evaluation.storage import EvaluationStorage
import os

st.set_page_config(
    page_title="DocuMind Evaluation Dashboard",
    page_icon="📊",
    layout="wide"
)

# Initialize storage
storage = EvaluationStorage(os.getenv('DATABASE_URL'))

st.title("📊 DocuMind Evaluation Dashboard")

# Recent runs
recent_runs = storage.get_recent_runs(limit=50)
df = pd.DataFrame(recent_runs, columns=[
    'id', 'run_name', 'model_name', 'faithfulness',
    'answer_relevancy', 'context_precision', 'context_recall',
    'average_score', 'test_dataset_size', 'passed', 'timestamp'
])

# Metrics overview
st.header("Latest Results")
latest = df.iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Faithfulness", f"{latest['faithfulness']:.3f}",
            delta="Target: 0.90")
col2.metric("Answer Relevancy", f"{latest['answer_relevancy']:.3f}",
            delta="Target: 0.85")
col3.metric("Context Precision", f"{latest['context_precision']:.3f}",
            delta="Target: 0.80")
col4.metric("Context Recall", f"{latest['context_recall']:.3f}",
            delta="Target: 0.85")

# Status indicator
if latest['passed']:
    st.success("✅ Quality Gates: PASSING")
else:
    st.error("❌ Quality Gates: FAILING")

# Trend over time
st.header("Quality Trends")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df['timestamp'], y=df['faithfulness'],
    name='Faithfulness', mode='lines+markers'
))
fig.add_trace(go.Scatter(
    x=df['timestamp'], y=df['answer_relevancy'],
    name='Answer Relevancy', mode='lines+markers'
))
fig.add_hline(y=0.90, line_dash="dash", 
              annotation_text="Faithfulness Target")
fig.add_hline(y=0.85, line_dash="dash",
              annotation_text="Answer Relevancy Target")

st.plotly_chart(fig, use_container_width=True)

# Recent runs table
st.header("Recent Evaluation Runs")
st.dataframe(df[[
    'run_name', 'model_name', 'average_score', 
    'passed', 'timestamp'
]], use_container_width=True)
```

**Launch dashboard:**

**🖥️ Run in Terminal:**
```bash
streamlit run src/dashboard/evaluation_dashboard.py
```

### Exercise 4.3: Alerting System (5 minutes)

**Task:** Implement quality alerting.

**📝 Create file `src/evaluation/alerting.py` using Claude Code or your editor:**
```python
# src/evaluation/alerting.py
from typing import List, Dict
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

class QualityAlerter:
    """Alert on quality issues"""
    
    def __init__(self, recipients: List[str], smtp_config: Dict = None):
        self.recipients = recipients
        self.smtp_config = smtp_config or {}
        self.alert_history = []
    
    def check_and_alert(self, results: Dict, run_name: str):
        """Check results and send alerts if needed"""
        issues = []
        
        # Check each metric
        thresholds = {
            'faithfulness': 0.90,
            'answer_relevancy': 0.85,
            'context_precision': 0.80,
            'context_recall': 0.85
        }
        
        for metric, threshold in thresholds.items():
            actual = results.get(metric, 0)
            if actual < threshold:
                gap = threshold - actual
                issues.append(f"{metric}: {actual:.3f} (need {threshold:.2f}, gap: {gap:.3f})")
        
        if issues:
            self.send_alert(
                severity="HIGH",
                run_name=run_name,
                issues=issues,
                results=results
            )
    
    def send_alert(self, severity: str, run_name: str, 
                   issues: List[str], results: Dict):
        """Send alert email"""
        subject = f"[{severity}] DocuMind Quality Alert - {run_name}"
        
        body = f"""
DocuMind Evaluation Alert
========================

Run: {run_name}
Time: {datetime.now().isoformat()}
Severity: {severity}

Quality Issues Detected:
{chr(10).join('- ' + issue for issue in issues)}

Full Results:
- Faithfulness: {results.get('faithfulness', 0):.3f}
- Answer Relevancy: {results.get('answer_relevancy', 0):.3f}
- Context Precision: {results.get('context_precision', 0):.3f}
- Context Recall: {results.get('context_recall', 0):.3f}

Action Required:
1. Review evaluation dashboard
2. Check recent code changes
3. Analyze failing test cases
4. Update prompts or configuration

Dashboard: http://localhost:8501
        """
        
        print(f"\n🚨 ALERT SENT")
        print(f"Subject: {subject}")
        print(f"Recipients: {', '.join(self.recipients)}")
        print(body)
        
        # In production, send actual email:
        # msg = MIMEText(body)
        # msg['Subject'] = subject
        # msg['From'] = self.smtp_config['from']
        # msg['To'] = ', '.join(self.recipients)
        # 
        # with smtplib.SMTP(self.smtp_config['server']) as server:
        #     server.send_message(msg)
```

**Test alerting:**

**🖥️ Run in Terminal:**
```bash
# Test with bad results
python -c "
import sys
sys.path.append('src')
from evaluation.alerting import QualityAlerter

bad_results = {
    'faithfulness': 0.76,
    'answer_relevancy': 0.81,
    'context_precision': 0.73,
    'context_recall': 0.78
}

alerter = QualityAlerter(recipients=['team@company.com'])
alerter.check_and_alert(bad_results, 'test_run_20250115')
"
```

### Module 4 Quiz

**Question 1:** Why store evaluation results in a database?\
- A) To waste storage space\
- B) To track trends and regression over time\
- C) To slow down evaluation\
- D) To make it harder to access

**Answer:** B - Database storage enables tracking quality trends, detecting regressions, and historical analysis.

**Question 2:** What should trigger a quality alert?\
- A) Every evaluation run\
- B) Only when all metrics are perfect\
- C) When metrics fall below thresholds\
- D) Never, alerts are annoying

**Answer:** C - Alerts should trigger when quality metrics drop below defined thresholds.

**Question 3:** What's the benefit of a dashboard?\
- A) Makes the project look professional\
- B) Real-time visibility into system quality\
- C) Required by management\
- D) Replaces testing

**Answer:** B - Dashboards provide real-time visibility and make quality metrics accessible to the whole team.

---

---

## Module 5: The Unified Interface (15 minutes)

### Concept Review
We have built:
- Ingestion Agents (S5/S7)
- Vector Search (S8)
- Memory & Feedback (S9)
- Evaluation (S10)

Currently, these are separate scripts. Let's combine them into a single "DocuMind" application using Streamlit.

### Exercise 5.1: Create the App Entry Point

**Task:** Create `src/app.py` that imports your modules and provides a UI.

**Step 1: Create the App File**

**📝 Create file `src/app.py` using Claude Code or your editor:**
```python
import streamlit as st
import os
import time
from typing import List

# Import components from previous sessions
# Note: Ensure students have __init__.py files in their directories
try:
    from documind.memory.conversational_qa_with_feedback import ConversationalQAWithFeedback
    from documind.processor import DocumentProcessor
    from documind.rag.retriever import search_documents
except ImportError:
    st.error("Modules not found. Make sure you are running from the project root.")

# Page Config
st.set_page_config(page_title="DocuMind", page_icon="🧠", layout="wide")

st.title("🧠 DocuMind: Enterprise Knowledge Base")

# Sidebar: App Mode Selection
mode = st.sidebar.radio("Select Mode", ["Chat Assistant", "Document Ingestion", "Knowledge Explorer"])

# Initialize Session State for Chat
if "messages" not in st.session_state:
    st.session_state.messages = []
if "qa_system" not in st.session_state:
    # Initialize the S9 Conversational QA System
    st.session_state.qa_system = ConversationalQAWithFeedback(user_id="streamlit_user")

# --- MODE 1: CHAT ASSISTANT (Sessions 6, 8, 9) ---
if mode == "Chat Assistant":
    st.header("Chat with your Documents")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # 1. User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Assistant Response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Call the S9 System
                response = st.session_state.qa_system.ask_with_feedback(prompt)
                
                answer_text = response['answer']
                sources = response.get('sources', [])
                
                # Display Answer
                st.markdown(answer_text)
                
                # Display Sources (S6/S8 feature)
                if sources:
                    with st.expander("📚 View Sources"):
                        for s in sources:
                            st.markdown(f"- **{s.get('title', 'Doc')}**: {s.get('preview', '')}...")

                # Feedback Mechanism (S9 feature)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👍 Helpful", key=f"up_{len(st.session_state.messages)}"):
                        st.session_state.qa_system.rate_last_answer(response, 5, "User clicked Helpful")
                        st.toast("Feedback saved!")
                with col2:
                    if st.button("👎 Not Helpful", key=f"down_{len(st.session_state.messages)}"):
                        st.session_state.qa_system.rate_last_answer(response, 2, "User clicked Not Helpful")
                        st.toast("Feedback saved!")

        # Add to history
        st.session_state.messages.append({"role": "assistant", "content": answer_text})

# --- MODE 2: DOCUMENT INGESTION (Session 5 & 7) ---
elif mode == "Document Ingestion":
    st.header("📥 Ingest New Documents")
    st.info("Upload documents to add them to the Knowledge Base (supports PDF, DOCX, TXT).")

    uploaded_files = st.file_uploader("Choose files", accept_multiple_files=True)

    if st.button("Process Documents") and uploaded_files:
        processor = DocumentProcessor() # From Session 7
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing {uploaded_file.name}...")
            
            # Save temp file
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            try:
                # 1. Extract & Chunk (S7)
                result = processor.process_document(temp_path)
                
                # 2. Upload to DB (S4/S5)
                # Note: In a real app, you'd call the S5 pipeline script here
                upload_status = processor.upload_to_documind(result)
                
                st.success(f"✅ {uploaded_file.name}: {result['metadata']['basic']['page_count']} pages processed.")
            except Exception as e:
                st.error(f"❌ Failed {uploaded_file.name}: {str(e)}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        status_text.text("Ingestion Complete!")

# --- MODE 3: KNOWLEDGE EXPLORER (Session 4 & 8) ---
elif mode == "Knowledge Explorer":
    st.header("🔎 Explore Knowledge Base")
    
    search_term = st.text_input("Search documents by keyword or semantic meaning")
    
    if search_term:
        # Use S8 Hybrid Search directly
        results = search_documents(search_term, top_k=10)
        
        st.subheader(f"Found {len(results)} chunks")
        for r in results:
            with st.container(border=True):
                st.markdown(f"**Document:** {r.get('document_title', 'Unknown')}")
                st.caption(f"Score: {r.get('similarity', 0.0):.4f}")
                st.text(r.get('content', '')[:300] + "...")

# Footer
st.divider()
st.caption("DocuMind v1.0 | Built with HeroForge Agentic Engineering")
```

**Step 2: Run Your Final App**

**🖥️ Run in Terminal:**
```bash
streamlit run src/app.py
```
What you will see:

1. A sidebar to switch between "Ingestion" and "Chat".
2. A Chat Interface that uses your S9 Memory system.
3. A Document Uploader that triggers your S7 Processor.

This is your final Capstone delivery! Congratulations!!!🚀

Now, if you're an over-achiever, keep rolling with the Challenge Project!

---

## Challenge Project: Complete Evaluation System (Bonus)

**Objective:** Integrate all modules into production-ready system.

**Requirements:**
1. ✅ RAGAS evaluation on 20+ test queries
2. ✅ TruLens monitoring on production endpoint
3. ✅ Quality gates blocking bad deployments
4. ✅ A/B test comparing 2+ models
5. ✅ Database storing historical results
6. ✅ Streamlit dashboard with trends
7. ✅ Alerting on quality drops
8. ✅ CI/CD workflow with automated evaluation
9. ✅ Documentation of thresholds and decisions
10. ✅ Regression test detecting >5% quality drop

**Evaluation Criteria:**
- Code quality and organization
- Completeness of implementation
- Quality of test dataset
- Dashboard usability
- Alert configuration
- CI/CD integration
- Documentation clarity

**Submission:**
- GitHub repository with complete code
- Screenshot of TruLens dashboard
- Screenshot of Streamlit dashboard
- README with setup instructions
- Sample evaluation report

---

## Workshop Wrap-Up

### What You Built Today:
1. ✅ Production RAGAS evaluation pipeline
2. ✅ TruLens real-time monitoring
3. ✅ A/B testing framework
4. ✅ Automated quality gates
5. ✅ Evaluation database
6. ✅ Monitoring dashboard
7. ✅ Alerting system
8. ✅ CI/CD integration

### Key Takeaways:
- RAGAS provides quantifiable RAG quality metrics
- TruLens enables production observability
- Quality gates prevent regressions
- A/B testing drives data-driven decisions
- Continuous evaluation maintains quality
- Dashboards make metrics accessible
- Alerts catch issues before users do

### Next Steps:
- Run daily evaluation on your RAG system
- Build comprehensive test datasets
- Set up monitoring dashboards
- Integrate quality gates in CI/CD
- A/B test different models and prompts
- Track quality trends over time
- Optimize based on evaluation insights

**Congratulations on completing Session 10 and the entire course! You now have production-grade RAG evaluation skills!**

---

## Regression Testing for Prompts (10 minutes)

### Concept: Preventing Prompt Regressions

**The Problem:**

You optimize a prompt for one use case... and break three others:

```python
# Before (worked for 10 questions):
prompt = "Answer based on context: {context}\n\nQuestion: {question}"

# After "optimization" (works for 1 question, breaks 9):
prompt = "You are an expert. Use this context: {context}. Now answer: {question}"
# Oops! Now it hallucinates, ignores sources, and adds fluff.
```

**The Solution: Regression Test Suite**

Build a test dataset of known good examples. Run it after every prompt change.

### Exercise: Build Prompt Regression Suite

**Step 1: Create Golden Dataset (5 mins)**

**📝 Create file `tests/prompt_regression_tests.json` using Claude Code or your editor:**
```json
[
  {
    "question": "How many vacation days do employees get?",
    "expected_keywords": ["15", "20", "25", "tenure", "years"],
    "expected_sources": ["Company Vacation Policy"],
    "should_not_contain": ["I don't know", "I cannot", "unclear"]
  },
  {
    "question": "What is the remote work policy?",
    "expected_keywords": ["days", "manager", "approval"],
    "expected_sources": ["Remote Work Guidelines"],
    "should_not_contain": []
  },
  {
    "question": "What is the company's stance on quantum computing?",
    "expected_keywords": ["don't have", "no information", "not found"],
    "expected_sources": [],
    "should_not_contain": ["quantum", "computing"]
  }
]
```

**Step 2: Create Regression Test Runner (5 mins)**

**🤖 Ask Claude Code to create `tests/test_prompt_regression.py`:**
```
Create tests/test_prompt_regression.py with:

- Load tests/prompt_regression_tests.json
- For each test case:
  - Run RAG pipeline
  - Check expected_keywords are present
  - Check should_not_contain are absent
  - Verify correct sources cited (if specified)
  - Assert answer length is reasonable (50-500 chars)
- Use pytest with parametrize for each test case
- Print detailed failure messages

Make it production-ready with clear error messages.
```

**Step 3: Run Baseline (establish current behavior):**

**🖥️ Run in Terminal:**
```bash
pytest tests/test_prompt_regression.py -v

# Save output as baseline
pytest tests/test_prompt_regression.py -v > tests/baseline_results.txt
```

**All tests should pass (GREEN).** This is your baseline.

### Exercise: Catch a Prompt Regression

**Step 1: Break the prompt (intentionally):**

**📝 Edit `src/rag/qa_system.py` using Claude Code or your editor:**
```python
# In src/rag/qa_system.py, change the prompt:
def _build_rag_prompt(self, question: str, context: str) -> str:
    # OLD (good):
    # "Answer based ONLY on the context provided."

    # NEW (bad - encourages hallucination):
    prompt = f"""You are a helpful AI assistant. Use your knowledge and this context.

Context: {context}

Question: {question}

Provide a comprehensive answer using both your knowledge and the context."""
    return prompt
```

**Step 2: Run regression tests:**

**🖥️ Run in Terminal:**
```bash
pytest tests/test_prompt_regression.py -v
```

**Expected: Some tests FAIL (RED):**

```
tests/test_prompt_regression.py::test_question_3 FAILED

AssertionError: Regression detected!
Question: "What is the company's stance on quantum computing?"
Expected: ["don't have", "no information"]
Actual answer contained: "quantum computing is an emerging technology..."

❌ FAIL: AI hallucinated information not in context!
```

**Step 3: Revert the prompt:**

**🖥️ Run in Terminal:**
```bash
git checkout src/rag/qa_system.py
pytest tests/test_prompt_regression.py -v
# ✅ All tests pass again (GREEN)
```

### Workflow: Prompt Engineering with Safety

```
1. Establish baseline → Run regression tests (should pass)
2. Make prompt change → Modify _build_rag_prompt()
3. Run regression tests → pytest tests/test_prompt_regression.py
4. Check results:
   ✅ All pass → Accept change
   ❌ Some fail → Investigate:
      - Is failure expected? (Update test)
      - Is failure a regression? (Revert prompt)
      - Is tradeoff worth it? (Document decision)
5. Commit with test results:
   git commit -m "prompt: improve answer conciseness

   Changed prompt to encourage shorter answers.
   Regression tests: 15/15 passing ✅

   Closes #42"
```

### Adding to CI/CD

**📝 Update `.github/workflows/evaluate-rag.yml` using Claude Code or your editor:**
```yaml
- name: Run Prompt Regression Tests
  run: |
    echo "🧪 Running prompt regression tests..."
    pytest tests/test_prompt_regression.py -v
    # Fails workflow if any regression detected
```

**Now every PR checks for prompt regressions automatically!**

### Key Insights

1. **Prompts are code** - Version control them, test them, review them
2. **Regressions happen easily** - Small prompt changes have big impacts
3. **Golden datasets are valuable** - Invest time building good test cases
4. **CI/CD catches regressions** - Automate testing, don't rely on memory
5. **Document tradeoffs** - Sometimes regressions are acceptable

**This is how Anthropic and OpenAI manage prompts at scale.** 🎯

---

## Resources

**Documentation:**
- RAGAS: https://docs.ragas.io/
- TruLens: https://www.trulens.org/
- Claude API: https://docs.anthropic.com/

**Code Examples:**
- https://github.com/your-repo/documind-evaluation
- https://github.com/explodinggradients/ragas/tree/main/examples

**Community:**
- Discord: [Course Discord]
- Office Hours: [Schedule]

**Certification:**
Submit your challenge project to earn your course completion certificate!
