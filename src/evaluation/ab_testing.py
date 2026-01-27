# src/evaluation/ab_testing.py
from typing import List, Dict
from datetime import datetime
import time


class ABTester:
    """A/B testing framework for RAG model comparison"""

    def __init__(self):
        self.models = {}
        self.results = {}

    def add_model(self, name: str, rag_pipeline):
        """Add model to comparison"""
        self.models[name] = rag_pipeline
        print(f"➕ Added model: {name}")

    def run_comparison(self, test_dataset: List[Dict]) -> List[Dict]:
        """Compare all models on same dataset"""
        from evaluation.ragas_evaluator import RAGASEvaluator

        print(f"\n{'='*60}")
        print(f"A/B TESTING STARTED: {datetime.now()}")
        print(f"{'='*60}")
        print(f"Models: {len(self.models)}")
        print(f"Test queries: {len(test_dataset)}")

        results = []

        for model_name, rag_pipeline in self.models.items():
            print(f"\n{'─'*60}")
            print(f"Testing: {model_name}")
            print(f"{'─'*60}")

            # Track timing
            start_time = time.time()

            # Create evaluator and run
            evaluator = RAGASEvaluator(rag_pipeline)
            eval_results = evaluator.evaluate(test_dataset)

            elapsed_time = time.time() - start_time

            # Store results
            result = {
                "model": model_name,
                "faithfulness": eval_results.get("faithfulness", 0),
                "answer_relevancy": eval_results.get("answer_relevancy", 0),
                "answer_correctness": eval_results.get("answer_correctness", 0),
                "average_score": eval_results.get("average_score", 0),
                "passed": eval_results.get("passed", False),
                "time_seconds": round(elapsed_time, 2),
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)

        # Sort by average score (descending)
        results.sort(key=lambda x: x["average_score"], reverse=True)

        return results

    def print_comparison(self, results: List[Dict]):
        """Print formatted comparison table"""
        print(f"\n{'='*80}")
        print("A/B TEST RESULTS - MODEL COMPARISON")
        print(f"{'='*80}")

        # Header
        print(f"{'Model':<25} {'Faith':>8} {'Relev':>8} {'Correct':>8} {'Avg':>8} {'Time':>8} {'Status':>8}")
        print(f"{'-'*80}")

        # Results rows
        for r in results:
            status = "✅ PASS" if r["passed"] else "❌ FAIL"
            print(
                f"{r['model']:<25} "
                f"{r['faithfulness']:>8.3f} "
                f"{r['answer_relevancy']:>8.3f} "
                f"{r['answer_correctness']:>8.3f} "
                f"{r['average_score']:>8.3f} "
                f"{r['time_seconds']:>7.1f}s "
                f"{status:>8}"
            )

        print(f"{'='*80}")

        # Winner announcement
        if results:
            winner = results[0]
            print(
                f"\n🏆 WINNER: {winner['model']} (avg score: {winner['average_score']:.3f})")
