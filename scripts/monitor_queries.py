# scripts/monitor_queries.py
from documind.rag.production_qa import ProductionQA
from evaluation.trulens_monitor import DocuMindTruLens
import sys
sys.path.insert(0, 'src')


# Initialize RAG pipeline and TruLens monitor
rag = ProductionQA()
monitor = DocuMindTruLens(rag)

# Sample queries based on actual knowledge base content
queries = [
    "How many vacation days do full-time employees receive?",
    "How do I request time off?",
    "What are the password requirements?",
    "How do I report a security incident?",
    "How many sick leave days do employees get?"
]

print("\n" + "="*60)
print("RUNNING MONITORED QUERIES")
print("="*60)

for i, query in enumerate(queries, 1):
    print(f"\n[{i}/{len(queries)}] {query}")
    result = monitor.query(query)
    print(f"✓ Answer length: {len(result['answer'])} chars")
    print(f"✓ Sources: {len(result.get('sources', []))} chunks")

print("\n" + "="*60)
print("✅ All queries monitored and logged")
print("📊 View dashboard: python -c \"from trulens_eval import Tru; Tru().run_dashboard()\"")
print("="*60)
