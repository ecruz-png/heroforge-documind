"""
Integration Test Suite for RAG Q&A Pipeline

Tests the complete RAG pipeline flow including:
- Question answering with relevant context
- Document retrieval and relevance
- Citation extraction and validation
- Out-of-scope question handling
- End-to-end pipeline integrity

Run with: pytest tests/test_rag_integration.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List
import sys
import os
from pathlib import Path

# Set test environment
os.environ.setdefault("TESTING", "1")

# Mock optional dependencies before any documind imports
# This prevents ImportError for optional packages
_mock_modules = [
    'pdfplumber',
    'docx',
    'docx.Document',
    'openpyxl',
    'pandas',
    'PIL',
    'PIL.Image',
]
for mod in _mock_modules:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from documind.rag.production_qa import (
    ProductionQA,
    rerank_results,
    assemble_context,
    add_citations,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def rag_qa_system():
    """
    Create a ProductionQA instance for integration testing.

    This fixture provides a fresh RAG Q&A system instance for each test,
    ensuring test isolation.
    """
    return ProductionQA(default_model='claude')


@pytest.fixture
def mock_document_chunks():
    """
    Sample document chunks simulating a knowledge base about company policies.

    These chunks represent real-world document content with varying
    relevance scores for testing retrieval quality.
    """
    return [
        {
            "id": "chunk-001",
            "content": "Our company offers 20 days of paid vacation per year for full-time employees. "
                       "Vacation days accrue monthly at a rate of 1.67 days per month. "
                       "New employees can use vacation after their first 90 days.",
            "metadata": {"document_name": "employee_handbook.pdf"},
            "similarity": 0.95,
            "document_name": "employee_handbook.pdf",
            "chunk_index": 12,
        },
        {
            "id": "chunk-002",
            "content": "Remote work policy: Employees may work from home up to 3 days per week "
                       "with manager approval. All remote workers must be available during core hours "
                       "(10 AM - 3 PM local time) and attend mandatory team meetings.",
            "metadata": {"document_name": "remote_work_policy.pdf"},
            "similarity": 0.72,
            "document_name": "remote_work_policy.pdf",
            "chunk_index": 5,
        },
        {
            "id": "chunk-003",
            "content": "Health insurance coverage begins on the first day of employment. "
                       "The company covers 80% of premium costs for employees and 50% for dependents. "
                       "Dental and vision plans are also available.",
            "metadata": {"document_name": "benefits_guide.pdf"},
            "similarity": 0.68,
            "document_name": "benefits_guide.pdf",
            "chunk_index": 3,
        },
        {
            "id": "chunk-004",
            "content": "Performance reviews are conducted annually in December. "
                       "Mid-year check-ins occur in June. Employees receive feedback on goals, "
                       "achievements, and areas for improvement.",
            "metadata": {"document_name": "hr_processes.pdf"},
            "similarity": 0.55,
            "document_name": "hr_processes.pdf",
            "chunk_index": 8,
        },
        {
            "id": "chunk-005",
            "content": "The company kitchen is stocked with coffee, tea, and snacks. "
                       "Please clean up after yourself and report any maintenance issues to facilities.",
            "metadata": {"document_name": "office_guidelines.pdf"},
            "similarity": 0.25,
            "document_name": "office_guidelines.pdf",
            "chunk_index": 15,
        },
    ]


@pytest.fixture
def mock_llm_response_with_citations():
    """Mock LLM response that properly cites sources."""
    mock = Mock()
    mock.choices = [
        Mock(
            message=Mock(
                content="According to [Source 1], full-time employees receive 20 days of paid "
                        "vacation per year. The vacation days accrue at a rate of 1.67 days per month "
                        "[Source 1]. New employees must wait 90 days before using vacation time."
            )
        )
    ]
    mock.usage = Mock(prompt_tokens=800, completion_tokens=150, total_tokens=950)
    return mock


@pytest.fixture
def mock_llm_response_no_context():
    """Mock LLM response when context doesn't contain relevant information."""
    mock = Mock()
    mock.choices = [
        Mock(
            message=Mock(
                content="I don't have enough information to answer that question. "
                        "The provided context does not contain information about "
                        "the company's stock option program."
            )
        )
    ]
    mock.usage = Mock(prompt_tokens=600, completion_tokens=50, total_tokens=650)
    return mock


# =============================================================================
# TEST: RAG PIPELINE ANSWERS QUESTIONS CORRECTLY
# =============================================================================


class TestRAGPipelineAnswersCorrectly:
    """Integration tests verifying the RAG pipeline produces correct answers."""

    @patch("documind.rag.production_qa.client")
    @patch("documind.rag.production_qa.search_documents")
    @patch("documind.rag.production_qa.supabase")
    def test_query_returns_relevant_answer_with_context(
        self,
        mock_supabase,
        mock_search,
        mock_client,
        rag_qa_system,
        mock_document_chunks,
        mock_llm_response_with_citations,
    ):
        """
        Test that a question about vacation policy returns a relevant answer
        that includes information from the retrieved documents.
        """
        # Arrange
        mock_search.return_value = mock_document_chunks[:3]
        mock_client.chat.completions.create.return_value = mock_llm_response_with_citations
        mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock()

        # Act
        result = rag_qa_system.query("How many vacation days do employees get?")

        # Assert - Answer quality checks
        assert "answer" in result
        assert len(result["answer"]) > 50, "Answer should be substantive"
        assert "20" in result["answer"] or "vacation" in result["answer"].lower()

        # Assert - Response structure
        assert "sources" in result
        assert "model" in result
        assert "response_time" in result
        assert result["response_time"] >= 0  # May be 0 with mocked responses

    @patch("documind.rag.production_qa.client")
    @patch("documind.rag.production_qa.search_documents")
    @patch("documind.rag.production_qa.supabase")
    def test_query_uses_hybrid_search_when_specified(
        self,
        mock_supabase,
        mock_search,
        mock_client,
        rag_qa_system,
        mock_document_chunks,
        mock_llm_response_with_citations,
    ):
        """
        Test that hybrid search mode is properly invoked when requested,
        potentially improving retrieval for keyword-heavy queries.
        """
        # Arrange
        with patch("documind.rag.production_qa.hybrid_search") as mock_hybrid:
            mock_hybrid.return_value = mock_document_chunks[:4]
            mock_client.chat.completions.create.return_value = mock_llm_response_with_citations
            mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock()

            # Act
            result = rag_qa_system.query(
                "What is the remote work policy?",
                use_hybrid=True
            )

            # Assert
            mock_hybrid.assert_called_once()
            assert result["search_type"] == "hybrid"
            assert "answer" in result


# =============================================================================
# TEST: RETRIEVAL FINDS RELEVANT DOCUMENTS
# =============================================================================


class TestRetrievalFindsRelevantDocuments:
    """Integration tests verifying document retrieval quality."""

    @patch("documind.rag.production_qa.client")
    @patch("documind.rag.production_qa.search_documents")
    @patch("documind.rag.production_qa.supabase")
    def test_retrieval_returns_documents_sorted_by_relevance(
        self,
        mock_supabase,
        mock_search,
        mock_client,
        rag_qa_system,
        mock_document_chunks,
        mock_llm_response_with_citations,
    ):
        """
        Test that retrieved documents are returned in order of relevance,
        with the most relevant documents appearing first in sources.
        """
        # Arrange
        mock_search.return_value = mock_document_chunks
        mock_client.chat.completions.create.return_value = mock_llm_response_with_citations
        mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock()

        # Act
        result = rag_qa_system.query("vacation policy", top_k=3)

        # Assert - Sources should be present and ordered
        assert len(result["sources"]) > 0
        assert len(result["sources"]) <= 3, "Should respect top_k limit"

        # Assert - Rerank scores should be in descending order
        rerank_scores = [s.get("rerank_score", 0) for s in result["sources"]]
        assert rerank_scores == sorted(rerank_scores, reverse=True), \
            "Sources should be sorted by relevance score"

    def test_rerank_results_boosts_keyword_matches(self, mock_document_chunks):
        """
        Test that the reranking algorithm properly boosts documents
        containing exact query keywords.
        """
        # Arrange
        query = "vacation days employees"

        # Act
        reranked = rerank_results(mock_document_chunks.copy(), query, top_k=5)

        # Assert - Document about vacation should rank highest
        top_result = reranked[0]
        assert "vacation" in top_result["content"].lower()
        assert "rerank_score" in top_result
        assert top_result["rerank_score"] > top_result["similarity"], \
            "Rerank score should be boosted above raw similarity"

    def test_assemble_context_includes_source_markers(self, mock_document_chunks):
        """
        Test that assembled context properly formats documents with
        source markers for citation tracking.
        """
        # Act
        context = assemble_context(mock_document_chunks[:3])

        # Assert
        assert "[Source 1:" in context
        assert "[Source 2:" in context
        assert "[Source 3:" in context
        assert "employee_handbook.pdf" in context


# =============================================================================
# TEST: CITATIONS ARE INCLUDED
# =============================================================================


class TestCitationsIncluded:
    """Integration tests verifying citation extraction and validation."""

    @patch("documind.rag.production_qa.client")
    @patch("documind.rag.production_qa.search_documents")
    @patch("documind.rag.production_qa.supabase")
    def test_answer_includes_citation_references(
        self,
        mock_supabase,
        mock_search,
        mock_client,
        rag_qa_system,
        mock_document_chunks,
        mock_llm_response_with_citations,
    ):
        """
        Test that the generated answer includes proper [Source X] citations
        and that these citations are tracked in the response.
        """
        # Arrange
        mock_search.return_value = mock_document_chunks[:3]
        mock_client.chat.completions.create.return_value = mock_llm_response_with_citations
        mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock()

        # Act
        result = rag_qa_system.query("How many vacation days do employees get?")

        # Assert - Answer should contain citation markers
        assert "[Source" in result["answer"], "Answer should contain source citations"

        # Assert - Citations list should be populated
        assert "citations" in result
        assert len(result["citations"]) > 0, "Citations list should not be empty"

        # Assert - Each citation should have required fields
        for citation in result["citations"]:
            assert "citation_id" in citation
            assert "document" in citation
            assert "chunk" in citation

    def test_add_citations_extracts_referenced_sources(self, mock_document_chunks):
        """
        Test that the add_citations function correctly identifies
        which sources were actually referenced in the answer.
        """
        # Arrange
        answer_with_citations = (
            "According to [Source 1], employees receive 20 vacation days. "
            "The remote work policy [Source 2] allows 3 days per week from home."
        )

        # Act
        result = add_citations(answer_with_citations, mock_document_chunks[:3])

        # Assert
        assert result["answer"] == answer_with_citations
        assert result["cited_count"] == 2
        assert result["total_sources"] == 3

        # Verify correct sources were identified
        citation_ids = [c["citation_id"] for c in result["citations"]]
        assert 1 in citation_ids
        assert 2 in citation_ids
        assert 3 not in citation_ids

    def test_add_citations_handles_no_citations_gracefully(self, mock_document_chunks):
        """
        Test that answers without explicit citations are handled correctly.
        """
        # Arrange
        answer_without_citations = "Employees receive vacation days based on tenure."

        # Act
        result = add_citations(answer_without_citations, mock_document_chunks[:2])

        # Assert
        assert result["cited_count"] == 0
        assert result["total_sources"] == 2
        assert len(result["citations"]) == 0


# =============================================================================
# TEST: OUT-OF-SCOPE QUESTIONS HANDLED GRACEFULLY
# =============================================================================


class TestOutOfScopeQuestionsHandled:
    """Integration tests verifying graceful handling of unanswerable questions."""

    @patch("documind.rag.production_qa.client")
    @patch("documind.rag.production_qa.search_documents")
    @patch("documind.rag.production_qa.supabase")
    def test_out_of_scope_question_returns_appropriate_response(
        self,
        mock_supabase,
        mock_search,
        mock_client,
        rag_qa_system,
        mock_document_chunks,
        mock_llm_response_no_context,
    ):
        """
        Test that questions outside the knowledge base scope receive
        an appropriate 'no information' response rather than hallucination.
        """
        # Arrange - Return low-relevance documents
        low_relevance_docs = [
            {**doc, "similarity": 0.2} for doc in mock_document_chunks[-2:]
        ]
        mock_search.return_value = low_relevance_docs
        mock_client.chat.completions.create.return_value = mock_llm_response_no_context
        mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock()

        # Act
        result = rag_qa_system.query("What is the company stock option program?")

        # Assert - Should indicate lack of information
        answer_lower = result["answer"].lower()
        assert any(phrase in answer_lower for phrase in [
            "don't have enough information",
            "not contain information",
            "cannot find",
            "no information"
        ]), "Should indicate inability to answer from context"

    @patch("documind.rag.production_qa.client")
    @patch("documind.rag.production_qa.search_documents")
    @patch("documind.rag.production_qa.supabase")
    def test_empty_search_results_handled_gracefully(
        self,
        mock_supabase,
        mock_search,
        mock_client,
        rag_qa_system,
    ):
        """
        Test that queries returning no documents are handled gracefully
        without crashing the pipeline.
        """
        # Arrange - No documents found
        mock_search.return_value = []
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content="I don't have enough information to answer that question."
                )
            )
        ]
        mock_response.usage = Mock(prompt_tokens=100, completion_tokens=20, total_tokens=120)
        mock_client.chat.completions.create.return_value = mock_response
        mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock()

        # Act
        result = rag_qa_system.query("What is quantum computing?")

        # Assert - Should complete without error
        assert "answer" in result
        assert result["context_chunks"] == 0
        assert result["sources"] == []


# =============================================================================
# TEST: END-TO-END PIPELINE INTEGRITY
# =============================================================================


class TestEndToEndPipelineIntegrity:
    """Integration tests verifying complete pipeline data flow."""

    @patch("documind.rag.production_qa.client")
    @patch("documind.rag.production_qa.search_documents")
    @patch("documind.rag.production_qa.supabase")
    def test_complete_pipeline_returns_all_required_fields(
        self,
        mock_supabase,
        mock_search,
        mock_client,
        rag_qa_system,
        mock_document_chunks,
        mock_llm_response_with_citations,
    ):
        """
        Test that the complete RAG pipeline returns all required fields
        for downstream consumption (UI, logging, analytics).
        """
        # Arrange
        mock_search.return_value = mock_document_chunks[:4]
        mock_client.chat.completions.create.return_value = mock_llm_response_with_citations
        mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock()

        # Act
        result = rag_qa_system.query(
            "What benefits does the company offer?",
            model="claude",
            top_k=4,
            use_hybrid=False
        )

        # Assert - All required fields present
        required_fields = [
            "answer", "citations", "sources", "query",
            "model", "search_type", "context_chunks",
            "response_time", "timestamp"
        ]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

        # Assert - Field types are correct
        assert isinstance(result["answer"], str)
        assert isinstance(result["citations"], list)
        assert isinstance(result["sources"], list)
        assert isinstance(result["response_time"], float)
        assert result["query"] == "What benefits does the company offer?"
        assert "anthropic/claude" in result["model"]

    @patch("documind.rag.production_qa.client")
    @patch("documind.rag.production_qa.search_documents")
    @patch("documind.rag.production_qa.supabase")
    def test_source_metadata_is_preserved_through_pipeline(
        self,
        mock_supabase,
        mock_search,
        mock_client,
        rag_qa_system,
        mock_document_chunks,
        mock_llm_response_with_citations,
    ):
        """
        Test that document metadata (document name, chunk index, similarity)
        is preserved throughout the pipeline and available in the response.
        """
        # Arrange
        mock_search.return_value = mock_document_chunks[:3]
        mock_client.chat.completions.create.return_value = mock_llm_response_with_citations
        mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock()

        # Act
        result = rag_qa_system.query("Tell me about employee benefits")

        # Assert - Source metadata preserved
        for source in result["sources"]:
            assert "id" in source
            assert "document" in source
            assert "chunk" in source
            assert "similarity" in source
            assert "rerank_score" in source
            assert "preview" in source

            # Preview should be truncated appropriately
            assert len(source["preview"]) <= 203  # 200 chars + "..."


# =============================================================================
# MAIN
# =============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
