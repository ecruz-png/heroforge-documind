# Test script: test_search_queries.py
from documind.rag.search import search_documents, hybrid_search, populate_embeddings

test_cases = [
    # (query, minimum_expected_results)
    ("remote", 1),                                    # Keyword - should work
    # Natural language - MUST work
    ("What is our remote work policy?", 1),
    # Question format - MUST work
    ("How many PTO days do employees get?", 1),
    ("vacation benefits", 1),                         # Two keywords
    ("Can I work from home on Fridays?", 1),          # Conversational
]

print("Search Query Testing")
print("=" * 60)

all_passed = True
for query, min_results in test_cases:
    results = search_documents(query, top_k=5)
    count = len(results)
    passed = count >= min_results
    status = "✅ PASS" if passed else "❌ FAIL"
    print(
        f"{status}: '{query[:40]}...' returned {count} results (need {min_results}+)")
    if not passed:
        all_passed = False

print("=" * 60)
if all_passed:
    print("✅ All search tests passed!")
else:
    print("❌ Some tests failed - check your search implementation")
