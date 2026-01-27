"""
Production Search API for DocuMind

Provides a unified search interface with multiple modes, query expansion,
result diversification, and performance monitoring.
"""
from typing import List, Dict, Any
from enum import Enum
import time
import re
from dataclasses import dataclass, field
from collections import defaultdict
from statistics import mean, stdev

from documind.hybrid_search import HybridSearcher


class SearchMode(Enum):
    """Search mode options"""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    AUTO = "auto"


@dataclass
class SearchResult:
    """Search result with metadata"""
    chunk_id: str
    document_id: str
    chunk_text: str
    score: float
    rank: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchMetrics:
    """Search performance metrics"""
    query: str
    mode: SearchMode
    latency_ms: float
    num_results: int
    avg_score: float
    top_score: float


class SearchAPI:
    """
    Production search API with monitoring and optimization.

    Features:
    - Multiple search modes (semantic, keyword, hybrid, auto)
    - Automatic mode selection based on query characteristics
    - Query expansion with synonyms
    - Result diversification
    - Performance monitoring and reporting
    """

    # Common synonyms for query expansion
    SYNONYMS = {
        "ai": ["artificial intelligence", "machine learning", "ml"],
        "ml": ["machine learning", "ai", "artificial intelligence"],
        "pto": ["paid time off", "vacation", "time off", "leave"],
        "vacation": ["pto", "paid time off", "time off", "holiday"],
        "sick": ["illness", "medical", "health"],
        "401k": ["retirement", "pension", "retirement plan"],
        "health": ["medical", "healthcare", "wellness"],
        "insurance": ["coverage", "benefits", "plan"],
        "salary": ["compensation", "pay", "wages"],
        "remote": ["work from home", "wfh", "telecommute"],
        "wfh": ["work from home", "remote", "telecommute"],
        "hr": ["human resources", "personnel"],
        "employee": ["staff", "worker", "team member"],
        "manager": ["supervisor", "lead", "boss"],
        "review": ["evaluation", "assessment", "appraisal"],
        "bonus": ["incentive", "reward", "commission"],
    }

    # Patterns that indicate keyword search is better
    KEYWORD_PATTERNS = [
        r'[A-Z]{2,}',           # Acronyms like PTO, HR, API
        r'\d+',                  # Numbers like 401k, 2024
        r'"[^"]+"',              # Quoted phrases
        r"'[^']+'",              # Single-quoted phrases
        r'[A-Z][a-z]+[A-Z]',    # CamelCase terms
        r'\b[A-Z][A-Z0-9_]+\b',  # Constants like MAX_VALUE
    ]

    def __init__(self, semantic_weight: float = 0.7):
        """
        Initialize SearchAPI.

        Args:
            semantic_weight: Weight for semantic search in hybrid mode (0-1)
        """
        self.searcher = HybridSearcher(semantic_weight=semantic_weight)
        self.query_history: List[SearchMetrics] = []

    def search(
        self,
        query: str,
        mode: SearchMode = SearchMode.HYBRID,
        top_k: int = 10,
        expand_query: bool = False,
        diversify: bool = True,
        max_per_document: int = 2,
        **kwargs
    ) -> List[SearchResult]:
        """
        Search documents with specified mode.

        Args:
            query: Search query string
            mode: Search mode (SEMANTIC, KEYWORD, HYBRID, AUTO)
            top_k: Maximum number of results to return
            expand_query: Whether to expand query with synonyms
            diversify: Whether to diversify results
            max_per_document: Maximum chunks per document if diversifying

        Returns:
            List of SearchResult objects
        """
        start_time = time.perf_counter()

        # Auto mode selection
        if mode == SearchMode.AUTO:
            mode = self.auto_select_mode(query)

        # Query expansion
        search_query = query
        if expand_query:
            search_query = self.expand_query(query)

        # Execute search based on mode
        if mode == SearchMode.SEMANTIC:
            raw_results = self.searcher.search_semantic(
                search_query, top_k=top_k * 2)
            score_key = "semantic_score"
        elif mode == SearchMode.KEYWORD:
            raw_results = self.searcher.search_keyword(
                search_query, top_k=top_k * 2)
            score_key = "keyword_score"
        else:  # HYBRID
            raw_results = self.searcher.search_hybrid(
                search_query,
                top_k=top_k * 2,
                rerank_method=kwargs.get("rerank_method", "linear")
            )
            score_key = "combined_score" if kwargs.get(
                "rerank_method") != "rrf" else "rrf_score"

        # Convert to SearchResult objects
        results = []
        for rank, item in enumerate(raw_results, 1):
            score = item.get(score_key, item.get("semantic_score", 0))
            results.append(SearchResult(
                chunk_id=str(item.get("id", "")),
                document_id=str(item.get("document_id", "")),
                chunk_text=item.get("content", ""),
                score=float(score) if score else 0.0,
                rank=rank,
                metadata={
                    "document_name": item.get("document_name", "Unknown"),
                    "section_heading": item.get("section_heading"),
                    "search_mode": mode.value,
                    **item.get("metadata", {})
                }
            ))

        # Diversify results
        if diversify and results:
            results = self.diversify_results(results, max_per_document)

        # Limit to top_k
        results = results[:top_k]

        # Update ranks after diversification
        for i, result in enumerate(results, 1):
            result.rank = i

        # Calculate metrics
        latency_ms = (time.perf_counter() - start_time) * 1000
        scores = [r.score for r in results if r.score > 0]

        metrics = SearchMetrics(
            query=query,
            mode=mode,
            latency_ms=latency_ms,
            num_results=len(results),
            avg_score=mean(scores) if scores else 0.0,
            top_score=max(scores) if scores else 0.0
        )
        self.query_history.append(metrics)

        return results

    def auto_select_mode(self, query: str) -> SearchMode:
        """
        Automatically select best search mode based on query characteristics.

        Heuristics:
        - KEYWORD: Query contains rare terms, codes, exact phrases, or acronyms
        - SEMANTIC: Conceptual or paraphrased queries
        - HYBRID: Default for balanced queries

        Args:
            query: Search query string

        Returns:
            Selected SearchMode
        """
        # Check for quoted phrases (exact match needed)
        if '"' in query or "'" in query:
            return SearchMode.KEYWORD

        # Check for keyword patterns (acronyms, numbers, codes)
        keyword_score = 0
        for pattern in self.KEYWORD_PATTERNS:
            matches = re.findall(pattern, query)
            keyword_score += len(matches)

        # Short queries with specific terms favor keyword
        words = query.split()
        if len(words) <= 2 and keyword_score > 0:
            return SearchMode.KEYWORD

        # High keyword pattern density suggests keyword search
        if keyword_score >= 2:
            return SearchMode.KEYWORD

        # Question-like queries favor semantic
        question_words = ["what", "how", "why", "when",
                          "where", "who", "which", "explain", "describe"]
        if any(query.lower().startswith(qw) for qw in question_words):
            return SearchMode.SEMANTIC

        # Long, natural language queries favor semantic
        if len(words) >= 6:
            return SearchMode.SEMANTIC

        # Default to hybrid for balanced approach
        return SearchMode.HYBRID

    def expand_query(self, query: str) -> str:
        """
        Expand query with synonyms and related terms.

        Adds synonyms for known terms to improve recall without
        significantly impacting precision.

        Args:
            query: Original search query

        Returns:
            Expanded query string
        """
        words = query.lower().split()
        expansions = []

        for word in words:
            # Check if word has synonyms
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word in self.SYNONYMS:
                # Add first 2 synonyms to avoid query explosion
                synonyms = self.SYNONYMS[clean_word][:2]
                expansions.extend(synonyms)

        if expansions:
            # Combine original query with expansions
            expansion_str = " ".join(expansions)
            return f"{query} {expansion_str}"

        return query

    def diversify_results(
        self,
        results: List[SearchResult],
        max_per_document: int = 2
    ) -> List[SearchResult]:
        """
        Diversify results to avoid too many chunks from the same document.

        Ensures variety in search results by limiting chunks per document
        while preserving the highest-scoring chunks from each.

        Args:
            results: List of SearchResult objects
            max_per_document: Maximum chunks to include per document

        Returns:
            Diversified list of SearchResult objects
        """
        if not results:
            return results

        # Group by document
        doc_chunks: Dict[str, List[SearchResult]] = defaultdict(list)
        for result in results:
            doc_id = result.document_id or result.chunk_id
            doc_chunks[doc_id].append(result)

        # Sort each document's chunks by score
        for doc_id in doc_chunks:
            doc_chunks[doc_id].sort(key=lambda x: x.score, reverse=True)

        # Build diversified results using round-robin with score priority
        diversified = []
        doc_counts: Dict[str, int] = defaultdict(int)

        # Sort results by score to process highest first
        sorted_results = sorted(results, key=lambda x: x.score, reverse=True)

        for result in sorted_results:
            doc_id = result.document_id or result.chunk_id
            if doc_counts[doc_id] < max_per_document:
                diversified.append(result)
                doc_counts[doc_id] += 1

        # Re-sort by score
        diversified.sort(key=lambda x: x.score, reverse=True)

        return diversified

    def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate performance report from query history.

        Provides aggregated metrics including:
        - Average latency by mode
        - Query volume by mode
        - Score distribution statistics
        - Overall trends

        Returns:
            Dictionary containing performance metrics
        """
        if not self.query_history:
            return {
                "total_queries": 0,
                "message": "No queries recorded yet"
            }

        # Group metrics by mode
        by_mode: Dict[SearchMode, List[SearchMetrics]] = defaultdict(list)
        for metrics in self.query_history:
            by_mode[metrics.mode].append(metrics)

        # Calculate per-mode statistics
        mode_stats = {}
        for mode, metrics_list in by_mode.items():
            latencies = [m.latency_ms for m in metrics_list]
            scores = [m.avg_score for m in metrics_list if m.avg_score > 0]
            result_counts = [m.num_results for m in metrics_list]

            mode_stats[mode.value] = {
                "query_count": len(metrics_list),
                "avg_latency_ms": round(mean(latencies), 2),
                "min_latency_ms": round(min(latencies), 2),
                "max_latency_ms": round(max(latencies), 2),
                "latency_stdev_ms": round(stdev(latencies), 2) if len(latencies) > 1 else 0,
                "avg_score": round(mean(scores), 4) if scores else 0,
                "avg_results": round(mean(result_counts), 1),
            }

        # Overall statistics
        all_latencies = [m.latency_ms for m in self.query_history]
        all_scores = [
            m.avg_score for m in self.query_history if m.avg_score > 0]
        all_top_scores = [
            m.top_score for m in self.query_history if m.top_score > 0]

        # Find slowest queries
        slowest = sorted(self.query_history,
                         key=lambda x: x.latency_ms, reverse=True)[:5]

        return {
            "total_queries": len(self.query_history),
            "by_mode": mode_stats,
            "overall": {
                "avg_latency_ms": round(mean(all_latencies), 2),
                "p95_latency_ms": round(sorted(all_latencies)[int(len(all_latencies) * 0.95)], 2) if all_latencies else 0,
                "avg_score": round(mean(all_scores), 4) if all_scores else 0,
                "avg_top_score": round(mean(all_top_scores), 4) if all_top_scores else 0,
            },
            "slowest_queries": [
                {"query": m.query[:50], "latency_ms": round(
                    m.latency_ms, 2), "mode": m.mode.value}
                for m in slowest
            ],
            "mode_distribution": {
                mode.value: len(metrics_list) / len(self.query_history) * 100
                for mode, metrics_list in by_mode.items()
            }
        }

    def clear_history(self):
        """Clear query history."""
        self.query_history = []


# Test the search API
if __name__ == "__main__":
    import json

    print("=" * 70)
    print("  DocuMind Search API Test")
    print("=" * 70)

    api = SearchAPI()

    # Test queries
    test_cases = [
        # (query, expected_mode_hint)
        ("What is our vacation policy?", "semantic - natural question"),
        ("PTO", "keyword - acronym"),
        ("401k retirement benefits", "hybrid - mixed"),
        ('"exact phrase match"', "keyword - quoted"),
        ("How do I request time off for medical appointments?",
         "semantic - long question"),
        ("HR-2024-001", "keyword - code pattern"),
    ]

    print("\n1. Testing Auto Mode Selection")
    print("-" * 50)
    for query, hint in test_cases:
        selected = api.auto_select_mode(query)
        print(f"  Query: '{query[:40]}...' " if len(
            query) > 40 else f"  Query: '{query}'")
        print(f"    Expected: {hint}")
        print(f"    Selected: {selected.value}")
        print()

    print("\n2. Testing Query Expansion")
    print("-" * 50)
    expansion_tests = ["vacation policy",
                       "AI benefits", "remote work", "401k options"]
    for query in expansion_tests:
        expanded = api.expand_query(query)
        print(f"  Original: '{query}'")
        print(f"  Expanded: '{expanded}'")
        print()

    print("\n3. Testing Search Modes")
    print("-" * 50)

    search_query = "What is the vacation policy?"

    for mode in [SearchMode.SEMANTIC, SearchMode.KEYWORD, SearchMode.HYBRID, SearchMode.AUTO]:
        print(f"\n  Mode: {mode.value.upper()}")
        try:
            results = api.search(search_query, mode=mode, top_k=3)
            print(f"  Results: {len(results)}")
            for r in results:
                print(
                    f"    [{r.rank}] Score: {r.score:.4f} - {r.chunk_text[:50]}...")
        except Exception as e:
            print(f"  Error: {e}")

    print("\n4. Testing Result Diversification")
    print("-" * 50)

    # Create mock results with same document
    mock_results = [
        SearchResult("c1", "doc1", "Chunk 1 from doc 1", 0.95, 1),
        SearchResult("c2", "doc1", "Chunk 2 from doc 1", 0.90, 2),
        SearchResult("c3", "doc1", "Chunk 3 from doc 1", 0.85, 3),
        SearchResult("c4", "doc2", "Chunk 1 from doc 2", 0.80, 4),
        SearchResult("c5", "doc2", "Chunk 2 from doc 2", 0.75, 5),
        SearchResult("c6", "doc3", "Chunk 1 from doc 3", 0.70, 6),
    ]

    print("  Before diversification:")
    for r in mock_results:
        print(f"    Doc: {r.document_id}, Score: {r.score}")

    diversified = api.diversify_results(mock_results, max_per_document=2)

    print("\n  After diversification (max 2 per doc):")
    for r in diversified:
        print(f"    Doc: {r.document_id}, Score: {r.score}")

    print("\n5. Performance Report")
    print("-" * 50)

    # Run a few more searches to populate history
    test_queries = [
        "employee benefits",
        "sick leave",
        "performance review",
    ]

    for q in test_queries:
        try:
            api.search(q, mode=SearchMode.AUTO, top_k=5)
        except Exception:
            pass

    report = api.get_performance_report()
    print(json.dumps(report, indent=2))

    print("\n" + "=" * 70)
    print("  Test Complete")
    print("=" * 70)
