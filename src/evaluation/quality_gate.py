# src/evaluation/quality_gate.py
from typing import Dict
import sys


class QualityGate:
    """Quality gate checker for CI/CD"""

    THRESHOLDS = {
        'faithfulness': 0.70,
        'answer_relevancy': 0.80,
        'answer_correctness': 0.70
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
