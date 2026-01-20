"""
Production-Ready Q&A System
Complete DocuMind RAG implementation
"""
import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client

from documind.rag.search import search_documents, hybrid_search

load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

# Available models
MODELS = {
    'claude': 'anthropic/claude-3.5-sonnet',
    'gpt4': 'openai/gpt-4-turbo',
    'gemini': 'google/gemini-pro'
}


def rerank_results(
    results: List[Dict[str, Any]],
    query: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Re-rank search results by relevance using keyword matching boost.

    Applies additional scoring based on:
    - Query term frequency in content
    - Exact phrase matches
    - Title/document name relevance
    """
    query_terms = query.lower().split()

    for result in results:
        content_lower = result.get("content", "").lower()
        doc_name_lower = result.get("document_name", "").lower()

        # Base score from similarity
        base_score = result.get("similarity", 0.5)

        # Keyword boost: count query terms in content
        term_matches = sum(1 for term in query_terms if term in content_lower)
        keyword_boost = min(term_matches * 0.05, 0.2)

        # Exact phrase boost
        phrase_boost = 0.1 if query.lower() in content_lower else 0

        # Title relevance boost
        title_matches = sum(1 for term in query_terms if term in doc_name_lower)
        title_boost = min(title_matches * 0.03, 0.1)

        # Combined score
        result["rerank_score"] = base_score + keyword_boost + phrase_boost + title_boost

    # Sort by rerank score
    results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

    return results[:top_k]


def assemble_context(documents: List[Dict[str, Any]], max_tokens: int = 3000) -> str:
    """Format retrieved documents into a context string for the LLM."""
    if not documents:
        return ""

    max_chars = max_tokens * 4
    context_parts = []
    current_chars = 0

    for i, doc in enumerate(documents, 1):
        content = doc.get("content", "")
        document_name = doc.get("document_name", "Unknown")
        chunk_index = doc.get("chunk_index", 0)

        source_header = f"[Source {i}: {document_name}, chunk {chunk_index}]"
        doc_text = f"{source_header}\n{content}"

        doc_length = len(doc_text) + 4
        if current_chars + doc_length > max_chars:
            remaining_chars = max_chars - current_chars - len(source_header) - 10
            if remaining_chars > 100:
                truncated_content = content[:remaining_chars] + "..."
                doc_text = f"{source_header}\n{truncated_content}"
                context_parts.append(doc_text)
            break

        context_parts.append(doc_text)
        current_chars += doc_length

    return "\n---\n".join(context_parts)


def add_citations(answer: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process answer to extract and validate citations.

    Returns the answer with a list of cited sources.
    """
    cited_sources = []

    for i, source in enumerate(sources, 1):
        citation_marker = f"[Source {i}]"
        if citation_marker in answer:
            cited_sources.append({
                "citation_id": i,
                "document": source.get("document_name"),
                "chunk": source.get("chunk_index"),
                "similarity": source.get("similarity")
            })

    return {
        "answer": answer,
        "citations": cited_sources,
        "total_sources": len(sources),
        "cited_count": len(cited_sources)
    }


class ProductionQA:
    """Production-ready Q&A system with logging and monitoring."""

    def __init__(self, default_model: str = 'claude'):
        self.default_model = MODELS.get(default_model, MODELS['claude'])

    def query(
        self,
        question: str,
        model: Optional[str] = None,
        top_k: int = 5,
        use_hybrid: bool = False
    ) -> Dict[str, Any]:
        """
        Execute complete query pipeline with all 7 steps.

        Steps:
        1. Retrieve relevant documents (semantic or hybrid search)
        2. Re-rank results by relevance
        3. Assemble context
        4. Generate answer
        5. Add citations
        6. Log query and response
        7. Return formatted result

        Args:
            question: The user's question
            model: Model key ('claude', 'gpt4', 'gemini') or None for default
            top_k: Number of documents to retrieve
            use_hybrid: Whether to use hybrid search (semantic + keyword)

        Returns:
            Dict with answer, citations, sources, and metadata
        """
        start_time = time.time()

        # Resolve model
        model_id = MODELS.get(model, self.default_model) if model else self.default_model

        # Step 1: Retrieve relevant documents
        if use_hybrid:
            raw_results = hybrid_search(query=question, top_k=top_k * 2)
        else:
            raw_results = search_documents(query=question, top_k=top_k * 2)

        # Step 2: Re-rank results by relevance
        ranked_results = rerank_results(raw_results, question, top_k=top_k)

        # Step 3: Assemble context
        context = assemble_context(ranked_results, max_tokens=3000)

        # Step 4: Generate answer
        prompt = f"""You are a helpful assistant that answers questions based on the provided context.

INSTRUCTIONS:
1. Answer the question using ONLY the information provided in the CONTEXT section below.
2. If the answer cannot be found in the context, say "I don't have enough information to answer that question."
3. When referencing information, cite your sources using [Source X] format.
4. Be concise but comprehensive.
5. Do not make up information not in the context.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:"""

        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500
        )

        raw_answer = response.choices[0].message.content

        # Step 5: Add citations
        citation_result = add_citations(raw_answer, ranked_results)

        # Format sources for output
        sources = []
        for doc in ranked_results:
            content = doc.get("content", "")
            preview = content[:200] + "..." if len(content) > 200 else content
            sources.append({
                "id": doc.get("id"),
                "document": doc.get("document_name"),
                "chunk": doc.get("chunk_index"),
                "similarity": doc.get("similarity"),
                "rerank_score": doc.get("rerank_score"),
                "preview": preview
            })

        response_time = time.time() - start_time

        # Step 6: Log query and response
        self.log_query(
            question=question,
            answer=citation_result["answer"],
            sources=sources,
            model=model_id,
            response_time=response_time
        )

        # Step 7: Return formatted result
        return {
            "answer": citation_result["answer"],
            "citations": citation_result["citations"],
            "sources": sources,
            "query": question,
            "model": model_id,
            "search_type": "hybrid" if use_hybrid else "semantic",
            "context_chunks": len(ranked_results),
            "response_time": round(response_time, 3),
            "timestamp": datetime.utcnow().isoformat()
        }

    def compare_models(
        self,
        question: str,
        models: List[str] = ['claude', 'gpt4', 'gemini']
    ) -> Dict[str, Any]:
        """
        Compare responses from multiple models.

        Returns side-by-side comparison with:
        - Each model's answer
        - Response times
        - Token usage
        - Cost estimates
        """
        # Retrieve documents once (same context for all models)
        raw_results = search_documents(query=question, top_k=10)
        ranked_results = rerank_results(raw_results, question, top_k=5)
        context = assemble_context(ranked_results, max_tokens=3000)

        prompt = f"""You are a helpful assistant that answers questions based on the provided context.

INSTRUCTIONS:
1. Answer using ONLY the provided context.
2. Cite sources using [Source X] format.
3. Say "I don't have enough information" if not found.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:"""

        # Format sources once
        sources = []
        for doc in ranked_results:
            content = doc.get("content", "")
            preview = content[:200] + "..." if len(content) > 200 else content
            sources.append({
                "document": doc.get("document_name"),
                "chunk": doc.get("chunk_index"),
                "similarity": doc.get("similarity"),
                "preview": preview
            })

        results = {}
        for model_key in models:
            model_id = MODELS.get(model_key)
            if not model_id:
                results[model_key] = {"error": f"Unknown model: {model_key}", "status": "error"}
                continue

            try:
                start_time = time.time()
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=500
                )
                elapsed = time.time() - start_time

                answer = response.choices[0].message.content
                usage = response.usage

                results[model_key] = {
                    "answer": answer,
                    "response_time": round(elapsed, 3),
                    "tokens": {
                        "prompt": usage.prompt_tokens if usage else None,
                        "completion": usage.completion_tokens if usage else None,
                        "total": usage.total_tokens if usage else None
                    },
                    "model_id": model_id,
                    "status": "success"
                }

            except Exception as e:
                results[model_key] = {"error": str(e), "status": "error"}

        return {
            "query": question,
            "sources": sources,
            "context_chunks": len(ranked_results),
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    def log_query(
        self,
        question: str,
        answer: str,
        sources: List[Dict],
        model: str,
        response_time: float
    ) -> None:
        """
        Log query to database for analytics.

        Store in query_logs table:
        - question
        - answer
        - model used
        - sources retrieved
        - response time
        - timestamp
        """
        try:
            supabase.table("query_logs").insert({
                "question": question,
                "answer": answer,
                "model": model,
                "sources": json.dumps(sources),
                "response_time": response_time,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            # Log failure silently - don't break the query flow
            print(f"Warning: Failed to log query: {e}")

    def get_analytics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get query analytics.

        Returns:
        - Total queries
        - Average response time
        - Most common questions
        - Most frequently retrieved documents
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

        try:
            # Fetch recent query logs
            response = supabase.table("query_logs") \
                .select("*") \
                .gte("created_at", cutoff_date) \
                .order("created_at", desc=True) \
                .execute()

            logs = response.data

            if not logs:
                return {
                    "period_days": days,
                    "total_queries": 0,
                    "avg_response_time": 0,
                    "model_usage": {},
                    "top_documents": [],
                    "message": "No queries found in the specified period"
                }

            # Calculate metrics
            total_queries = len(logs)
            avg_response_time = sum(log.get("response_time", 0) for log in logs) / total_queries

            # Model usage breakdown
            model_usage = {}
            for log in logs:
                model = log.get("model", "unknown")
                model_usage[model] = model_usage.get(model, 0) + 1

            # Most frequently retrieved documents
            doc_counts = {}
            for log in logs:
                sources_json = log.get("sources", "[]")
                try:
                    sources = json.loads(sources_json) if isinstance(sources_json, str) else sources_json
                    for source in sources:
                        doc_name = source.get("document", "Unknown")
                        doc_counts[doc_name] = doc_counts.get(doc_name, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    pass

            top_documents = sorted(doc_counts.items(), key=lambda x: x[1], reverse=True)[:10]

            return {
                "period_days": days,
                "total_queries": total_queries,
                "avg_response_time": round(avg_response_time, 3),
                "model_usage": model_usage,
                "top_documents": [{"document": doc, "count": count} for doc, count in top_documents],
                "queries_per_day": round(total_queries / days, 2)
            }

        except Exception as e:
            return {
                "period_days": days,
                "error": str(e),
                "message": "Failed to retrieve analytics"
            }

# CLI Interface


def main():
    """
    CLI interface for Production Q&A system.

    Features:
    - Interactive Q&A loop
    - Model selection
    - Show sources
    - Save conversation history
    """
    import argparse

    parser = argparse.ArgumentParser(description="DocuMind Production Q&A System")
    parser.add_argument("query", nargs="?", help="Question to ask")
    parser.add_argument("--model", "-m", default="claude", choices=["claude", "gpt4", "gemini"])
    parser.add_argument("--hybrid", "-H", action="store_true", help="Use hybrid search")
    parser.add_argument("--compare", "-c", action="store_true", help="Compare all models")
    parser.add_argument("--analytics", "-a", type=int, metavar="DAYS", help="Show analytics for N days")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    qa = ProductionQA(default_model=args.model)

    # Analytics mode
    if args.analytics:
        analytics = qa.get_analytics(days=args.analytics)
        if args.json:
            print(json.dumps(analytics, indent=2))
        else:
            print("\n" + "=" * 60)
            print(f"Query Analytics (Last {analytics['period_days']} days)")
            print("=" * 60)
            print(f"Total Queries: {analytics.get('total_queries', 0)}")
            print(f"Avg Response Time: {analytics.get('avg_response_time', 0)}s")
            print(f"Queries/Day: {analytics.get('queries_per_day', 0)}")
            print("\nModel Usage:")
            for model, count in analytics.get('model_usage', {}).items():
                print(f"  - {model}: {count}")
            print("\nTop Documents:")
            for doc in analytics.get('top_documents', [])[:5]:
                print(f"  - {doc['document']}: {doc['count']} retrievals")
        return

    # Interactive mode
    if not args.query:
        print("=" * 60)
        print("DocuMind Production Q&A System")
        print("=" * 60)
        print(f"Model: {args.model} | Hybrid: {args.hybrid}")
        print("Type 'quit' to exit, 'compare' to compare models\n")

        while True:
            try:
                query = input("Question: ").strip()
                if query.lower() in ["quit", "exit", "q"]:
                    print("\nGoodbye!")
                    break

                if not query:
                    continue

                if query.lower() == "compare":
                    query = input("Enter question to compare: ").strip()
                    if query:
                        print("\nComparing models...")
                        result = qa.compare_models(query)
                        for model, resp in result["results"].items():
                            print(f"\n--- {model.upper()} ---")
                            if resp["status"] == "success":
                                print(f"Time: {resp['response_time']}s")
                                print(resp["answer"])
                            else:
                                print(f"Error: {resp['error']}")
                    continue

                print("\nProcessing...")
                result = qa.query(query, use_hybrid=args.hybrid)

                print("\n" + "-" * 60)
                print("ANSWER:")
                print("-" * 60)
                print(result["answer"])
                print(f"\n[{result['search_type']} search | {result['response_time']}s | {result['context_chunks']} sources]")

                if result["citations"]:
                    print("\nCitations:")
                    for cite in result["citations"]:
                        print(f"  [{cite['citation_id']}] {cite['document']}")
                print()

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}\n")
    else:
        # Single query mode
        try:
            if args.compare:
                result = qa.compare_models(args.query)
            else:
                result = qa.query(args.query, use_hybrid=args.hybrid)

            if args.json:
                print(json.dumps(result, indent=2))
            else:
                if args.compare:
                    print("=" * 60)
                    print(f"Query: {args.query}")
                    print("=" * 60)
                    for model, resp in result["results"].items():
                        print(f"\n--- {model.upper()} ({resp.get('response_time', 'N/A')}s) ---")
                        if resp["status"] == "success":
                            print(resp["answer"])
                        else:
                            print(f"Error: {resp['error']}")
                else:
                    print("=" * 60)
                    print("DocuMind Q&A Response")
                    print("=" * 60)
                    print(f"\nQuery: {result['query']}")
                    print(f"Model: {result['model']}")
                    print(f"Search: {result['search_type']} | Time: {result['response_time']}s")
                    print("-" * 60)
                    print("\nANSWER:")
                    print(result["answer"])
                    print("\n" + "-" * 60)
                    print(f"\nSources ({result['context_chunks']} chunks):")
                    for i, source in enumerate(result["sources"], 1):
                        sim = source.get("similarity")
                        sim_str = f"{sim:.4f}" if sim else "N/A"
                        print(f"  {i}. {source['document']} (chunk {source['chunk']}, sim: {sim_str})")

        except Exception as e:
            print(f"Error: {e}")
            exit(1)


if __name__ == "__main__":
    main()
