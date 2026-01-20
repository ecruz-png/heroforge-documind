"""
DocuMind RAG (Retrieval-Augmented Generation) Module.

This module provides semantic search and document retrieval capabilities
for the DocuMind knowledge management system.
"""

from .search import (
    get_query_embedding,
    search_documents,
    hybrid_search,
)

__all__ = [
    "get_query_embedding",
    "search_documents",
    "hybrid_search",
]
