# scripts/ab_test.py
import json
import sys
sys.path.insert(0, 'src')

from evaluation.ab_testing import ABTester
from documind.rag.production_qa import ProductionQA

# Load dataset
with open('data/evaluation_dataset.json', 'r') as f:
    test_dataset = json.load(f)[:5]  # Use 5 queries for speed

# Setup comparison
tester = ABTester()

# Add current production model
rag = ProductionQA()
tester.add_model("GPT-4o-mini (Production)", rag)

# Note: To compare multiple models, you would create different
# ProductionQA instances with different configurations:
# rag_gpt4 = ProductionQA(model="gpt-4-turbo")
# tester.add_model("GPT-4 Turbo", rag_gpt4)

# Run comparison
results = tester.run_comparison(test_dataset)
tester.print_comparison(results)

# Save results
with open('results/ab_test_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n📁 Results saved to results/ab_test_results.json")
