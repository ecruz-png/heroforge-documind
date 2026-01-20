"""
RAG vs CAG Comparison Tool for DocuMind.

This module provides tools to compare Retrieval-Augmented Generation (RAG)
and Context-Augmented Generation (CAG) approaches for question answering.

Key differences:
- RAG: Retrieves relevant documents using semantic search, then generates
- CAG: Loads entire knowledge base into context, then generates
"""

import time
from typing import Dict, Any

from documind.rag.qa_pipeline import generate_answer as rag_answer
from documind.rag.cag_pipeline import generate_answer_cag as cag_answer


def compare_approaches(query: str) -> Dict[str, Any]:
    """
    Compare RAG and CAG approaches for answering a query.

    Runs both RAG and CAG pipelines on the same query, measuring execution
    time and comparing the results. Useful for understanding trade-offs
    between retrieval-based and full-context approaches.

    Args:
        query: The question to answer using both approaches.

    Returns:
        A dictionary containing:
            - query: The original query
            - rag: RAG results with answer, latency, sources
            - cag: CAG results with answer, latency, context_size
            - comparison: Analysis of differences

    Example:
        >>> results = compare_approaches("What is the vacation policy?")
        >>> print(f"RAG: {results['rag']['latency']:.2f}s")
        >>> print(f"CAG: {results['cag']['latency']:.2f}s")
    """
    print("=" * 70)
    print("RAG vs CAG Comparison")
    print("=" * 70)
    print(f"\nQuery: {query}")
    print("-" * 70)

    results = {"query": query}

    # Test RAG approach
    print("\n[1/2] Testing RAG (Retrieval-Augmented Generation)...")
    print("      → Retrieving relevant documents via semantic search")

    rag_start = time.time()
    try:
        rag_result = rag_answer(query)
        rag_latency = time.time() - rag_start
        rag_success = True
        print(f"      ✓ Completed in {rag_latency:.2f}s")
    except Exception as e:
        rag_latency = time.time() - rag_start
        rag_result = {"answer": f"Error: {str(e)}", "sources": []}
        rag_success = False
        print(f"      ✗ Failed: {e}")

    results["rag"] = {
        "answer": rag_result.get("answer", ""),
        "latency": rag_latency,
        "sources": rag_result.get("sources", []),
        "context_chunks": rag_result.get("context_chunks", 0),
        "success": rag_success
    }

    # Test CAG approach
    print("\n[2/2] Testing CAG (Context-Augmented Generation)...")
    print("      → Loading entire knowledge base into context")

    cag_start = time.time()
    try:
        cag_result = cag_answer(query)
        cag_latency = time.time() - cag_start
        cag_success = True
        print(f"      ✓ Completed in {cag_latency:.2f}s")
    except Exception as e:
        cag_latency = time.time() - cag_start
        cag_result = {"answer": f"Error: {str(e)}", "context_size": 0}
        cag_success = False
        print(f"      ✗ Failed: {e}")

    results["cag"] = {
        "answer": cag_result.get("answer", ""),
        "latency": cag_latency,
        "context_size": cag_result.get("context_size", 0),
        "success": cag_success
    }

    # Display results side-by-side
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    # RAG Answer
    print("\n┌" + "─" * 68 + "┐")
    print("│ RAG ANSWER" + " " * 57 + "│")
    print("├" + "─" * 68 + "┤")

    rag_answer_text = results["rag"]["answer"]
    for line in _wrap_text(rag_answer_text, 66):
        print(f"│ {line:<66} │")

    print("├" + "─" * 68 + "┤")
    sources_info = f"Sources: {results['rag']['context_chunks']} chunks retrieved"
    print(f"│ {sources_info:<66} │")

    if results["rag"]["sources"]:
        for src in results["rag"]["sources"][:3]:
            src_line = f"  • {src['document']} (chunk {src['chunk']}, sim: {src['similarity']:.3f})"
            if len(src_line) > 66:
                src_line = src_line[:63] + "..."
            print(f"│ {src_line:<66} │")

    print("└" + "─" * 68 + "┘")

    # CAG Answer
    print("\n┌" + "─" * 68 + "┐")
    print("│ CAG ANSWER" + " " * 57 + "│")
    print("├" + "─" * 68 + "┤")

    cag_answer_text = results["cag"]["answer"]
    for line in _wrap_text(cag_answer_text, 66):
        print(f"│ {line:<66} │")

    print("├" + "─" * 68 + "┤")
    context_info = f"Context: {results['cag']['context_size']:,} characters loaded"
    print(f"│ {context_info:<66} │")
    print("└" + "─" * 68 + "┘")

    # Performance metrics
    print("\n" + "=" * 70)
    print("PERFORMANCE METRICS")
    print("=" * 70)

    print(f"\n{'Metric':<25} {'RAG':>20} {'CAG':>20}")
    print("-" * 70)
    print(f"{'Latency':<25} {results['rag']['latency']:>19.2f}s {results['cag']['latency']:>19.2f}s")
    print(f"{'Status':<25} {'✓ Success' if results['rag']['success'] else '✗ Failed':>20} {'✓ Success' if results['cag']['success'] else '✗ Failed':>20}")

    if results["rag"]["success"] and results["cag"]["success"]:
        faster = "RAG" if rag_latency < cag_latency else "CAG"
        diff = abs(rag_latency - cag_latency)
        print(f"{'Winner':<25} {faster + f' (by {diff:.2f}s)':>41}")

    # Method comparison
    print("\n" + "=" * 70)
    print("APPROACH COMPARISON")
    print("=" * 70)

    print("""
┌─────────────────────────────┬─────────────────────────────────────┐
│ RAG (Retrieval-Augmented)   │ CAG (Context-Augmented)             │
├─────────────────────────────┼─────────────────────────────────────┤
│ ✓ Scalable to large KBs     │ ✗ Limited by context window         │
│ ✓ Lower token usage         │ ✗ Higher token usage                │
│ ✓ Faster for large KBs      │ ✓ No retrieval latency              │
│ ✗ May miss relevant docs    │ ✓ Full context available            │
│ ✗ Depends on embedding      │ ✓ LLM finds relevance               │
│   quality                   │                                     │
├─────────────────────────────┼─────────────────────────────────────┤
│ Best for: Large knowledge   │ Best for: Small knowledge bases     │
│ bases, production systems   │ (<20 docs), comprehensive answers   │
└─────────────────────────────┴─────────────────────────────────────┘
""")

    # Answer similarity analysis
    results["comparison"] = {
        "faster_method": "RAG" if rag_latency < cag_latency else "CAG",
        "latency_diff": abs(rag_latency - cag_latency),
        "rag_context_chunks": results["rag"]["context_chunks"],
        "cag_context_chars": results["cag"]["context_size"]
    }

    return results


def _wrap_text(text: str, width: int) -> list:
    """Wrap text to specified width, preserving words."""
    if not text:
        return ["(No answer)"]

    words = text.replace("\n", " ").split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 <= width:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)

    if current_line:
        lines.append(" ".join(current_line))

    return lines if lines else ["(No answer)"]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Compare RAG vs CAG approaches for question answering"
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Question to test (or use default test questions)"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run all default test questions"
    )

    args = parser.parse_args()

    # Default test questions
    test_questions = [
        "What is the company vacation policy?",
        "How do I request time off?",
        "What are the remote work guidelines?",
    ]

    if args.query:
        # Single query mode
        compare_approaches(args.query)

    elif args.all:
        # Run all test questions
        print("\n" + "█" * 70)
        print("█  RUNNING ALL TEST QUESTIONS")
        print("█" * 70)

        all_results = []
        for i, question in enumerate(test_questions, 1):
            print(f"\n\n{'━' * 70}")
            print(f"TEST {i}/{len(test_questions)}")
            print("━" * 70)
            result = compare_approaches(question)
            all_results.append(result)

        # Summary
        print("\n\n" + "█" * 70)
        print("█  SUMMARY")
        print("█" * 70)

        print(f"\n{'Question':<40} {'RAG':>12} {'CAG':>12} {'Faster':>10}")
        print("-" * 70)

        rag_wins = 0
        cag_wins = 0

        for result in all_results:
            q = result["query"][:37] + "..." if len(result["query"]) > 40 else result["query"]
            rag_time = result["rag"]["latency"]
            cag_time = result["cag"]["latency"]
            faster = result["comparison"]["faster_method"]

            if faster == "RAG":
                rag_wins += 1
            else:
                cag_wins += 1

            print(f"{q:<40} {rag_time:>11.2f}s {cag_time:>11.2f}s {faster:>10}")

        print("-" * 70)
        print(f"{'Total Wins':<40} {rag_wins:>12} {cag_wins:>12}")

    else:
        # Interactive mode
        print("=" * 70)
        print("RAG vs CAG Comparison Tool")
        print("=" * 70)
        print("\nEnter questions to compare both approaches.")
        print("Type 'quit' to exit.\n")

        while True:
            try:
                query = input("Question: ").strip()
                if query.lower() in ["quit", "exit", "q"]:
                    print("\nGoodbye!")
                    break

                if not query:
                    continue

                compare_approaches(query)
                print()

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}\n")
