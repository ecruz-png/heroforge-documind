import json
import sys
sys.path.append('src')

from evaluation.ragas_evaluator import RAGASEvaluator
from documind.rag.production_qa import ProductionQA

# Load test dataset
with open('data/evaluation_dataset.json', 'r') as f:
    test_dataset = json.load(f)

# Initialize ProductionQA (the actual DocuMind RAG pipeline)
rag = ProductionQA(enable_logging=False)
evaluator = RAGASEvaluator(rag)

# Run evaluation
results = evaluator.evaluate(test_dataset)

# Display results
print("\n" + "="*60)
print("EVALUATION RESULTS")
print("="*60)

for metric in ['faithfulness', 'answer_relevancy', 'answer_correctness']:
    score = results.get(metric, 0.0)
    status = "✅" if score >= {'faithfulness': 0.70, 'answer_relevancy': 0.80,
                               'answer_correctness': 0.70}[metric] else "❌"
    print(f"{metric:.<25} {score:.3f} {status}")

print(f"\nAverage Score: {results['average_score']:.3f}")
print(f"Overall Status: {'✅ PASSED' if results['passed'] else '❌ FAILED'}")

# Save results
with open('results/evaluation_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\n📁 Results saved to results/evaluation_results.json")
