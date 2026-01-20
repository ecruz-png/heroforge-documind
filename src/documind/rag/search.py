"""
Semantic Search Module for DocuMind RAG System.

This module provides semantic and hybrid search capabilities for document retrieval
using OpenAI embeddings and Supabase vector search with pgvector.
"""

import os
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

# Initialize clients using environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Validate environment variables
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "SUPABASE_URL and SUPABASE_KEY environment variables must be set")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable must be set")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)


def get_query_embedding(query: str) -> List[float]:
    """
    Generate embedding vector for a search query using OpenAI.

    Uses the text-embedding-3-small model to convert text into a 1536-dimensional
    vector representation suitable for semantic similarity search.

    Args:
        query: The search query text to embed.

    Returns:
        A list of floats representing the 1536-dimensional embedding vector.

    Raises:
        openai.APIError: If the OpenAI API request fails.
        ValueError: If the query is empty.

    Example:
        >>> embedding = get_query_embedding("What is our vacation policy?")
        >>> len(embedding)
        1536
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query.strip()
    )

    return response.data[0].embedding


def search_documents(
    query: str,
    top_k: int = 5,
    similarity_threshold: float = 0.35
) -> List[Dict[str, Any]]:
    """
    Perform semantic search on document chunks using vector similarity.

    Generates an embedding for the query and searches the document_chunks table
    using the Supabase RPC function 'match_documents' which performs cosine
    similarity matching against stored document embeddings.

    Args:
        query: The search query text.
        top_k: Maximum number of results to return. Defaults to 5.
        similarity_threshold: Minimum similarity score (0-1) for results.
            Defaults to 0.35.

    Returns:
        A list of dictionaries containing matched documents with keys:
            - id: UUID of the document chunk
            - content: The chunk text content
            - metadata: Additional metadata from the chunk
            - similarity: Cosine similarity score (0-1)
            - document_name: Title of the parent document
            - chunk_index: Position of chunk within the document

    Raises:
        ValueError: If query is empty or parameters are invalid.
        Exception: If the database query fails.

    Example:
        >>> results = search_documents("vacation policy", top_k=3)
        >>> for doc in results:
        ...     print(f"{doc['document_name']}: {doc['similarity']:.2f}")
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    if not 0 <= similarity_threshold <= 1:
        raise ValueError("similarity_threshold must be between 0 and 1")

    # Generate embedding for the query
    query_embedding = get_query_embedding(query)

    # Call Supabase RPC function for vector similarity search
    response = supabase.rpc(
        "match_documents",
        {
            "query_embedding": query_embedding,
            "match_count": top_k,
            "similarity_threshold": similarity_threshold
        }
    ).execute()

    # Format results
    results = []
    for row in response.data:
        results.append({
            "id": row.get("chunk_id"),
            "content": row.get("chunk_text"),
            "metadata": row.get("metadata", {}),
            "similarity": row.get("similarity"),
            "document_name": row.get("document_title"),
            "chunk_index": row.get("chunk_index")
        })

    return results


def hybrid_search(
    query: str,
    top_k: int = 5,
    semantic_weight: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search combining semantic and keyword-based retrieval.

    This function merges results from vector similarity search with full-text
    keyword search to improve recall while maintaining semantic relevance.
    Results are weighted and deduplicated before returning.

    Args:
        query: The search query text.
        top_k: Maximum number of results to return. Defaults to 5.
        semantic_weight: Weight for semantic results (0-1). Keyword weight
            will be (1 - semantic_weight). Defaults to 0.7.

    Returns:
        A list of dictionaries containing matched documents with keys:
            - id: UUID of the document chunk
            - content: The chunk text content
            - metadata: Additional metadata from the chunk
            - similarity: Combined relevance score
            - document_name: Title of the parent document
            - chunk_index: Position of chunk within the document
            - search_type: 'semantic', 'keyword', or 'both'

    Raises:
        ValueError: If query is empty or parameters are invalid.
        Exception: If the database query fails.

    Example:
        >>> results = hybrid_search("remote work policy", top_k=5)
        >>> for doc in results:
        ...     print(f"[{doc['search_type']}] {doc['document_name']}")
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    if not 0 <= semantic_weight <= 1:
        raise ValueError("semantic_weight must be between 0 and 1")

    keyword_weight = 1 - semantic_weight

    # Get semantic search results
    semantic_results = search_documents(
        query=query,
        top_k=top_k,
        similarity_threshold=0.5  # Lower threshold for hybrid search
    )

    # Add search type and apply semantic weight
    for result in semantic_results:
        result["search_type"] = "semantic"
        result["weighted_score"] = result["similarity"] * semantic_weight

    # Get keyword search results using Supabase full-text search
    # Search in document_chunks table using ilike for keyword matching
    search_terms = query.strip().split()
    keyword_query = " & ".join(search_terms)

    try:
        # Use textSearch for full-text search on chunk_text
        keyword_response = supabase.from_("document_chunks") \
            .select(
                "id, chunk_text, chunk_index, metadata, "
                "document_id, documents!inner(title)"
        ) \
            .text_search("chunk_text", keyword_query, config="english") \
            .limit(top_k) \
            .execute()

        keyword_results = []
        for row in keyword_response.data:
            keyword_results.append({
                "id": row.get("id"),
                "content": row.get("chunk_text"),
                "metadata": row.get("metadata", {}),
                "similarity": 0.8,  # Default score for keyword matches
                "document_name": row.get("documents", {}).get("title"),
                "chunk_index": row.get("chunk_index"),
                "search_type": "keyword",
                "weighted_score": 0.8 * keyword_weight
            })
    except Exception:
        # Fallback to ilike search if full-text search fails
        keyword_response = supabase.from_("document_chunks") \
            .select(
                "id, chunk_text, chunk_index, metadata, "
                "document_id, documents!inner(title)"
        ) \
            .ilike("chunk_text", f"%{query}%") \
            .limit(top_k) \
            .execute()

        keyword_results = []
        for row in keyword_response.data:
            keyword_results.append({
                "id": row.get("id"),
                "content": row.get("chunk_text"),
                "metadata": row.get("metadata", {}),
                "similarity": 0.6,  # Lower score for ilike matches
                "document_name": row.get("documents", {}).get("title"),
                "chunk_index": row.get("chunk_index"),
                "search_type": "keyword",
                "weighted_score": 0.6 * keyword_weight
            })

    # Merge results, avoiding duplicates
    seen_ids = set()
    merged_results = []

    # Process semantic results first (higher priority)
    for result in semantic_results:
        result_id = result["id"]
        if result_id not in seen_ids:
            seen_ids.add(result_id)
            merged_results.append(result)

    # Add keyword results that aren't duplicates
    for result in keyword_results:
        result_id = result["id"]
        if result_id not in seen_ids:
            seen_ids.add(result_id)
            merged_results.append(result)
        else:
            # Update existing result to indicate it matched both
            for merged in merged_results:
                if merged["id"] == result_id:
                    merged["search_type"] = "both"
                    merged["weighted_score"] += result["weighted_score"]
                    break

    # Sort by weighted score and return top_k
    merged_results.sort(key=lambda x: x.get("weighted_score", 0), reverse=True)

    # Clean up and format final results
    final_results = []
    for result in merged_results[:top_k]:
        final_results.append({
            "id": result["id"],
            "content": result["content"],
            "metadata": result["metadata"],
            "similarity": result.get("weighted_score", result["similarity"]),
            "document_name": result["document_name"],
            "chunk_index": result["chunk_index"],
            "search_type": result["search_type"]
        })

    return final_results


def populate_embeddings() -> int:
    """
    Generate and store embeddings for all document chunks that don't have them.

    Fetches chunks with NULL embeddings, generates embeddings using OpenAI,
    and updates the database with the vectors.

    Returns:
        Number of chunks that were updated with embeddings.
    """
    # Fetch chunks without embeddings
    response = supabase.from_("document_chunks") \
        .select("id, chunk_text") \
        .is_("embedding", "null") \
        .execute()

    chunks = response.data
    if not chunks:
        print("All chunks already have embeddings.")
        return 0

    print(f"Found {len(chunks)} chunks without embeddings. Generating...")

    updated_count = 0
    for chunk in chunks:
        chunk_id = chunk["id"]
        chunk_text = chunk["chunk_text"]

        # Generate embedding
        embedding = get_query_embedding(chunk_text)

        # Update the chunk with the embedding
        supabase.from_("document_chunks") \
            .update({"embedding": embedding}) \
            .eq("id", chunk_id) \
            .execute()

        updated_count += 1
        print(f"  Updated chunk {updated_count}/{len(chunks)}")

    print(f"Successfully populated {updated_count} embeddings.")
    return updated_count


if __name__ == "__main__":
    # Test the search functionality
    print("=" * 60)
    print("DocuMind Semantic Search Test")
    print("=" * 60)

    test_query = "What is our vacation policy?"
    print(f"\nSearch Query: '{test_query}'")
    print("-" * 60)

    try:
        # Test semantic search
        print("\n[Semantic Search Results]")
        results = search_documents(
            test_query, top_k=5, similarity_threshold=0.5)

        if results:
            for i, doc in enumerate(results, 1):
                print(f"\n{i}. {doc['document_name']}")
                print(f"   Similarity: {doc['similarity']:.4f}")
                print(f"   Chunk Index: {doc['chunk_index']}")
                print(f"   Content: {doc['content'][:150]}...")
        else:
            print("   No results found.")

        # Test hybrid search
        print("\n" + "-" * 60)
        print("\n[Hybrid Search Results]")
        hybrid_results = hybrid_search(test_query, top_k=5)

        if hybrid_results:
            for i, doc in enumerate(hybrid_results, 1):
                print(
                    f"\n{i}. [{doc['search_type'].upper()}] {doc['document_name']}")
                print(f"   Score: {doc['similarity']:.4f}")
                print(f"   Chunk Index: {doc['chunk_index']}")
                print(f"   Content: {doc['content'][:150]}...")
        else:
            print("   No results found.")

    except ValueError as e:
        print(f"Validation Error: {e}")
    except Exception as e:
        print(f"Error during search: {e}")

    print("\n" + "=" * 60)
