"""
CAG (Context-Augmented Generation) Pipeline Module for DocuMind.

This module provides a Context-Augmented Generation approach where the entire
knowledge base is loaded into the LLM context, rather than using retrieval.
This approach is only practical for small knowledge bases (<20 documents).

CAG vs RAG:
- RAG: Retrieves relevant documents based on query similarity
- CAG: Loads ALL documents into context, letting the LLM find relevant info
"""

import os
from typing import Dict, Any, List
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables must be set"
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize OpenRouter client
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable must be set")

openrouter_client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)


def load_all_documents(max_docs: int = 20) -> str:
    """
    Load all document chunks from the knowledge base into a single context string.

    Fetches document chunks from Supabase and formats them into a concatenated
    string suitable for inclusion in an LLM prompt. This is the core of the CAG
    approach - loading the entire knowledge base rather than retrieving selectively.

    Args:
        max_docs: Maximum number of document chunks to load. Defaults to 20.
            Keep this low to avoid exceeding context limits.

    Returns:
        A formatted string containing all documents, each prefixed with
        "[Document: {name}]" and separated by "---" dividers.

    Raises:
        Exception: If the database query fails.

    Example:
        >>> context = load_all_documents(max_docs=10)
        >>> print(context[:200])
        [Document: HR Policy Manual]
        Our vacation policy allows employees...
        ---
        [Document: Employee Handbook]
        ...
    """
    # Fetch document chunks with their parent document titles
    response = supabase.from_("document_chunks") \
        .select("chunk_text, chunk_index, document_id, documents!inner(title)") \
        .order("document_id") \
        .order("chunk_index") \
        .limit(max_docs) \
        .execute()

    if not response.data:
        return ""

    # Format each document chunk
    formatted_docs = []
    for row in response.data:
        document_name = row.get("documents", {}).get("title", "Unknown Document")
        content = row.get("chunk_text", "")

        formatted_doc = f"[Document: {document_name}]\n{content}"
        formatted_docs.append(formatted_doc)

    return "\n---\n".join(formatted_docs)


def generate_answer_cag(
    query: str,
    model: str = "anthropic/claude-3.5-sonnet",
    temperature: float = 0.1,
    max_tokens: int = 500
) -> Dict[str, Any]:
    """
    Generate an answer using Context-Augmented Generation (CAG).

    Unlike RAG which retrieves relevant documents, CAG loads the entire
    knowledge base into the context and lets the LLM find relevant information.
    This approach works well for small knowledge bases where:
    - The entire corpus fits in the context window
    - You want the LLM to have full context for nuanced answers
    - Query relevance is hard to determine automatically

    Args:
        query: The user's question to answer.
        model: OpenRouter model identifier. Defaults to "anthropic/claude-3.5-sonnet".
        temperature: Sampling temperature for response generation. Lower values
            produce more deterministic responses. Defaults to 0.1.
        max_tokens: Maximum tokens in the generated response. Defaults to 500.

    Returns:
        A dictionary containing:
            - answer: The generated answer text
            - method: "CAG" to indicate the generation method
            - query: The original query
            - model: The model used for generation
            - context_size: Number of characters in the full context
            - timestamp: ISO format timestamp of the response

    Raises:
        ValueError: If the query is empty.
        Exception: If document loading or LLM generation fails.

    Example:
        >>> result = generate_answer_cag("What is the vacation policy?")
        >>> print(result["answer"])
        Based on the HR Policy Manual, employees are entitled to...
        >>> print(result["method"])
        CAG
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    # Load ALL documents into context
    full_context = load_all_documents()

    if not full_context:
        return {
            "answer": "No documents found in the knowledge base.",
            "method": "CAG",
            "query": query,
            "model": model,
            "context_size": 0,
            "timestamp": datetime.utcnow().isoformat()
        }

    # Build prompt with full context
    prompt = f"""You are a helpful assistant with access to a complete knowledge base.

INSTRUCTIONS:
1. Answer the question using the information from the documents provided below.
2. Be concise but comprehensive in your response.
3. Reference specific documents when citing information (e.g., "According to the HR Policy Manual...").
4. If the answer cannot be found in the documents, say "I don't have enough information to answer that question."
5. Do not make up information that is not in the documents.

KNOWLEDGE BASE:
{full_context}

QUESTION:
{query}

ANSWER:"""

    # Generate answer using OpenRouter
    response = openrouter_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
        max_tokens=max_tokens
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "method": "CAG",
        "query": query,
        "model": model,
        "context_size": len(full_context),
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="DocuMind CAG Pipeline - Full context Q&A"
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
        "--max-docs",
        type=int,
        default=20,
        help="Maximum documents to load (default: 20)"
    )
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.1,
        help="Temperature for generation (default: 0.1)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output raw JSON response"
    )
    parser.add_argument(
        "--show-context",
        action="store_true",
        help="Show the loaded context"
    )

    args = parser.parse_args()

    # Interactive mode if no query provided
    if not args.query:
        print("=" * 60)
        print("DocuMind CAG (Context-Augmented Generation) Pipeline")
        print("=" * 60)
        print("\nLoading knowledge base...")

        context = load_all_documents(max_docs=args.max_docs)
        print(f"Loaded {len(context)} characters of context")

        if args.show_context:
            print("\n" + "-" * 60)
            print("CONTEXT:")
            print("-" * 60)
            print(context[:2000] + "..." if len(context) > 2000 else context)

        print("\nEnter your questions (type 'quit' to exit):\n")

        while True:
            try:
                query = input("Question: ").strip()
                if query.lower() in ["quit", "exit", "q"]:
                    print("\nGoodbye!")
                    break

                if not query:
                    continue

                print("\nGenerating answer (CAG method)...\n")

                result = generate_answer_cag(
                    query,
                    model=args.model,
                    temperature=args.temperature
                )

                if args.json:
                    print(json.dumps(result, indent=2))
                else:
                    print("-" * 60)
                    print("ANSWER (CAG):")
                    print("-" * 60)
                    print(result["answer"])
                    print(f"\n[Context size: {result['context_size']} chars]")

                print()

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}\n")

    else:
        # Single query mode
        try:
            if args.show_context:
                print("Loading context...")
                context = load_all_documents(max_docs=args.max_docs)
                print(f"\n{'-'*60}")
                print("CONTEXT:")
                print("-" * 60)
                print(context[:2000] + "..." if len(context) > 2000 else context)
                print()

            result = generate_answer_cag(
                args.query,
                model=args.model,
                temperature=args.temperature
            )

            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print("=" * 60)
                print("DocuMind CAG Response")
                print("=" * 60)
                print(f"\nQuery: {result['query']}")
                print(f"Model: {result['model']}")
                print(f"Method: {result['method']}")
                print("-" * 60)
                print("\nANSWER:")
                print(result["answer"])
                print(f"\n[Context size: {result['context_size']} chars]")
                print()

        except Exception as e:
            print(f"Error: {e}")
            exit(1)
