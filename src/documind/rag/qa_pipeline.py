"""
Q&A Pipeline Module for DocuMind RAG System.

This module provides a complete question-answering pipeline using OpenRouter
for LLM inference, combining document retrieval with generative AI responses.
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

from documind.rag.search import search_documents, get_query_embedding

# Load environment variables
load_dotenv()

# Initialize OpenRouter client using OpenAI-compatible API
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable must be set")

openrouter_client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)


def assemble_context(
    documents: List[Dict[str, Any]],
    max_tokens: int = 3000
) -> str:
    """
    Format retrieved documents into a context string for the LLM.

    Assembles document chunks into a formatted context string with source
    citations, respecting the maximum token limit to avoid context overflow.

    Args:
        documents: List of document dictionaries from search results, each
            containing 'content', 'document_name', 'chunk_index', and 'similarity'.
        max_tokens: Maximum number of tokens for the context. Uses ~4 chars
            per token estimate. Defaults to 3000.

    Returns:
        A formatted string containing document content with source citations,
        separated by "---" dividers.

    Example:
        >>> docs = [{"content": "Policy text...", "document_name": "HR Policy", "chunk_index": 0}]
        >>> context = assemble_context(docs, max_tokens=1000)
        >>> print(context)
        [Source 1: HR Policy, chunk 0]
        Policy text...
        ---
    """
    if not documents:
        return ""

    # Estimate max characters (~4 chars per token)
    max_chars = max_tokens * 4

    context_parts = []
    current_chars = 0

    for i, doc in enumerate(documents, 1):
        content = doc.get("content", "")
        document_name = doc.get("document_name", "Unknown")
        chunk_index = doc.get("chunk_index", 0)

        # Format source citation
        source_header = f"[Source {i}: {document_name}, chunk {chunk_index}]"
        doc_text = f"{source_header}\n{content}"

        # Check if adding this document would exceed the limit
        doc_length = len(doc_text) + 4  # +4 for "---\n" separator
        if current_chars + doc_length > max_chars:
            # Try to fit a truncated version
            remaining_chars = max_chars - \
                current_chars - len(source_header) - 10
            if remaining_chars > 100:  # Only include if we can fit meaningful content
                truncated_content = content[:remaining_chars] + "..."
                doc_text = f"{source_header}\n{truncated_content}"
                context_parts.append(doc_text)
            break

        context_parts.append(doc_text)
        current_chars += doc_length

    return "\n---\n".join(context_parts)


def build_qa_prompt(query: str, context: str) -> str:
    """
    Create a prompt for the Q&A model with instructions and context.

    Builds a structured prompt that instructs the model to answer questions
    using only the provided context, cite sources properly, and acknowledge
    when information is not available.

    Args:
        query: The user's question.
        context: The assembled context string from retrieved documents.

    Returns:
        A formatted prompt string ready for the LLM.

    Example:
        >>> prompt = build_qa_prompt("What is the vacation policy?", context_str)
        >>> print(prompt[:100])
        You are a helpful assistant that answers questions based on the provided context.
    """
    prompt = f"""You are a helpful assistant that answers questions based on the provided context.

INSTRUCTIONS:
1. Answer the question using ONLY the information provided in the CONTEXT section below.
2. If the answer cannot be found in the context, respond with "I don't have enough information to answer that question based on the available documents."
3. When referencing information, cite your sources using the [Source X] format (e.g., "According to [Source 1]...").
4. Be concise but comprehensive in your response.
5. Do not make up or infer information that is not explicitly stated in the context.

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:"""

    return prompt


def generate_answer(
    query: str,
    model: str = "anthropic/claude-3.5-sonnet",
    temperature: float = 0.1,
    max_tokens: int = 500
) -> Dict[str, Any]:
    """
    Generate an answer to a question using RAG (Retrieval-Augmented Generation).

    This function orchestrates the complete Q&A pipeline:
    1. Retrieves relevant documents using semantic search
    2. Assembles context from retrieved documents
    3. Builds a prompt with instructions and context
    4. Generates an answer using OpenRouter LLM
    5. Formats the response with source information

    Args:
        query: The user's question to answer.
        model: OpenRouter model identifier. Defaults to "anthropic/claude-3.5-sonnet".
        temperature: Sampling temperature for response generation. Lower values
            produce more deterministic responses. Defaults to 0.1.
        max_tokens: Maximum tokens in the generated response. Defaults to 500.

    Returns:
        A dictionary containing:
            - answer: The generated answer text
            - sources: List of source documents with id, document, chunk, similarity, preview
            - query: The original query
            - model: The model used for generation
            - context_chunks: Number of context chunks used
            - timestamp: ISO format timestamp of the response

    Raises:
        ValueError: If the query is empty.
        Exception: If document retrieval or LLM generation fails.

    Example:
        >>> result = generate_answer("What is the vacation policy?")
        >>> print(result["answer"])
        According to [Source 1], employees are entitled to...
        >>> print(result["sources"][0]["document"])
        HR Policy Manual
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    # Step 1: Retrieve relevant documents
    documents = search_documents(query, top_k=5)

    # Step 2: Assemble context from documents
    context = assemble_context(documents, max_tokens=3000)

    # Step 3: Build the prompt
    prompt = build_qa_prompt(query, context)

    # Step 4: Generate answer using OpenRouter
    response = openrouter_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
        max_tokens=max_tokens
    )

    answer = response.choices[0].message.content

    # Step 5: Format sources
    sources = []
    for doc in documents:
        content = doc.get("content", "")
        preview = content[:200] + "..." if len(content) > 200 else content

        sources.append({
            "id": doc.get("id"),
            "document": doc.get("document_name"),
            "chunk": doc.get("chunk_index"),
            "similarity": doc.get("similarity"),
            "preview": preview
        })

    return {
        "answer": answer,
        "sources": sources,
        "query": query,
        "model": model,
        "context_chunks": len(documents),
        "timestamp": datetime.utcnow().isoformat()
    }


def compare_models(
    query: str,
    models: List[str]
) -> Dict[str, Any]:
    """
    Query multiple LLM models and compare their responses.

    Useful for evaluating different models' performance on the same query
    with the same retrieved context. Handles errors gracefully, returning
    error information for models that fail.

    Args:
        query: The question to ask all models.
        models: List of OpenRouter model identifiers to compare.

    Returns:
        A dictionary containing:
            - query: The original query
            - timestamp: ISO format timestamp
            - results: Dict mapping model names to their responses or errors

    Example:
        >>> models = ["anthropic/claude-3.5-sonnet", "openai/gpt-4"]
        >>> comparison = compare_models("What is the vacation policy?", models)
        >>> for model, result in comparison["results"].items():
        ...     print(f"{model}: {result.get('answer', result.get('error'))[:100]}")
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    if not models:
        raise ValueError("At least one model must be specified")

    # Retrieve documents once for all models (same context)
    documents = search_documents(query, top_k=5)
    context = assemble_context(documents, max_tokens=3000)
    prompt = build_qa_prompt(query, context)

    # Format sources once
    sources = []
    for doc in documents:
        content = doc.get("content", "")
        preview = content[:200] + "..." if len(content) > 200 else content

        sources.append({
            "id": doc.get("id"),
            "document": doc.get("document_name"),
            "chunk": doc.get("chunk_index"),
            "similarity": doc.get("similarity"),
            "preview": preview
        })

    results = {}

    for model in models:
        try:
            response = openrouter_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )

            answer = response.choices[0].message.content

            results[model] = {
                "answer": answer,
                "sources": sources,
                "context_chunks": len(documents),
                "status": "success"
            }

        except Exception as e:
            results[model] = {
                "error": str(e),
                "status": "error"
            }

    return {
        "query": query,
        "timestamp": datetime.utcnow().isoformat(),
        "results": results
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="DocuMind Q&A Pipeline - Ask questions about your documents"
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="The question to ask"
    )
    parser.add_argument(
        "--model", "-m",
        default="anthropic/claude-3.5-sonnet",
        help="OpenRouter model to use (default: anthropic/claude-3.5-sonnet)"
    )
    parser.add_argument(
        "--compare", "-c",
        nargs="+",
        help="Compare multiple models (space-separated model names)"
    )
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.1,
        help="Temperature for generation (default: 0.1)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=500,
        help="Maximum tokens in response (default: 500)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output raw JSON response"
    )

    args = parser.parse_args()

    # Interactive mode if no query provided
    if not args.query:
        print("=" * 60)
        print("DocuMind Q&A Pipeline")
        print("=" * 60)
        print("\nEnter your questions (type 'quit' to exit):\n")

        while True:
            try:
                query = input("Question: ").strip()
                if query.lower() in ["quit", "exit", "q"]:
                    print("\nGoodbye!")
                    break

                if not query:
                    continue

                print("\nGenerating answer...\n")

                if args.compare:
                    result = compare_models(query, args.compare)
                    if args.json:
                        print(json.dumps(result, indent=2))
                    else:
                        for model, response in result["results"].items():
                            print(f"\n{'='*60}")
                            print(f"Model: {model}")
                            print("-" * 60)
                            if response["status"] == "success":
                                print(response["answer"])
                            else:
                                print(f"Error: {response['error']}")
                else:
                    result = generate_answer(
                        query,
                        model=args.model,
                        temperature=args.temperature,
                        max_tokens=args.max_tokens
                    )

                    if args.json:
                        print(json.dumps(result, indent=2))
                    else:
                        print("-" * 60)
                        print("ANSWER:")
                        print("-" * 60)
                        print(result["answer"])
                        print("\n" + "-" * 60)
                        print(f"Sources ({result['context_chunks']} chunks):")
                        for i, source in enumerate(result["sources"], 1):
                            sim = source["similarity"]
                            sim_str = f"{sim:.4f}" if sim else "N/A"
                            print(
                                f"  {i}. {source['document']} (chunk {source['chunk']}, similarity: {sim_str})")

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
                result = compare_models(args.query, args.compare)
            else:
                result = generate_answer(
                    args.query,
                    model=args.model,
                    temperature=args.temperature,
                    max_tokens=args.max_tokens
                )

            if args.json:
                print(json.dumps(result, indent=2))
            else:
                if args.compare:
                    print("=" * 60)
                    print(f"Query: {args.query}")
                    print("=" * 60)
                    for model, response in result["results"].items():
                        print(f"\n--- {model} ---")
                        if response["status"] == "success":
                            print(response["answer"])
                        else:
                            print(f"Error: {response['error']}")
                else:
                    print("=" * 60)
                    print("DocuMind Q&A Response")
                    print("=" * 60)
                    print(f"\nQuery: {result['query']}")
                    print(f"Model: {result['model']}")
                    print("-" * 60)
                    print("\nANSWER:")
                    print(result["answer"])
                    print("\n" + "-" * 60)
                    print(
                        f"\nSources ({result['context_chunks']} chunks used):")
                    for i, source in enumerate(result["sources"], 1):
                        sim = source["similarity"]
                        sim_str = f"{sim:.4f}" if sim else "N/A"
                        print(
                            f"  {i}. {source['document']} (chunk {source['chunk']}, similarity: {sim_str})")
                    print()

        except Exception as e:
            print(f"Error: {e}")
            exit(1)
