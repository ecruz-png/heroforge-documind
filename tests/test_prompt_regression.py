# tests/test_prompt_regression.py
"""
Prompt Regression Tests for DocuMind RAG Pipeline

Validates that the RAG system produces consistent, high-quality answers
by checking for expected keywords, forbidden content, correct sources,
and reasonable answer lengths.

Usage:
    pytest tests/test_prompt_regression.py -v
    pytest tests/test_prompt_regression.py -v --tb=short
    pytest tests/test_prompt_regression.py::test_expected_keywords -v
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from documind.rag.production_qa import ProductionQA


# =============================================================================
# CONFIGURATION
# =============================================================================

TEST_DATA_PATH = Path(__file__).parent / "prompt_regression_tests.json"
MIN_ANSWER_LENGTH = 50
MAX_ANSWER_LENGTH = 500
DEFAULT_MODEL = "google/gemini-2.5-flash-lite"


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture(scope="module")
def qa_pipeline():
    """Initialize RAG pipeline once for all tests."""
    return ProductionQA(
        default_model=DEFAULT_MODEL,
        enable_logging=False,  # Disable logging during tests
    )


@pytest.fixture(scope="module")
def test_cases() -> List[Dict[str, Any]]:
    """Load test cases from JSON file."""
    if not TEST_DATA_PATH.exists():
        pytest.skip(f"Test data file not found: {TEST_DATA_PATH}")

    with open(TEST_DATA_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)

    if not cases:
        pytest.skip("No test cases found in JSON file")

    return cases


def load_test_cases() -> List[Dict[str, Any]]:
    """Load test cases for parametrize decorator."""
    if not TEST_DATA_PATH.exists():
        return []

    with open(TEST_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_test_ids() -> List[str]:
    """Generate readable test IDs from questions."""
    cases = load_test_cases()
    return [
        case.get("question", "unknown")[:50].replace(" ", "_")
        for case in cases
    ]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def run_query(qa_pipeline: ProductionQA, question: str) -> Dict[str, Any]:
    """Execute RAG query and return result with error handling."""
    try:
        result = qa_pipeline.query(
            question=question,
            enable_fallback=True,
            log_query=False,
        )
        return result
    except Exception as e:
        pytest.fail(f"RAG query failed for question '{question}': {e}")


def format_keywords_error(
    question: str,
    answer: str,
    expected: List[str],
    found: List[str],
    missing: List[str],
) -> str:
    """Format detailed error message for keyword assertion."""
    return (
        f"\n{'=' * 70}\n"
        f"KEYWORD CHECK FAILED\n"
        f"{'=' * 70}\n"
        f"Question: {question}\n"
        f"{'-' * 70}\n"
        f"Answer (truncated):\n{answer[:300]}{'...' if len(answer) > 300 else ''}\n"
        f"{'-' * 70}\n"
        f"Expected keywords (any): {expected}\n"
        f"Found keywords: {found}\n"
        f"Missing ALL of: {missing}\n"
        f"{'=' * 70}"
    )


def format_forbidden_error(
    question: str,
    answer: str,
    forbidden: List[str],
    found: List[str],
) -> str:
    """Format detailed error message for forbidden content assertion."""
    return (
        f"\n{'=' * 70}\n"
        f"FORBIDDEN CONTENT CHECK FAILED\n"
        f"{'=' * 70}\n"
        f"Question: {question}\n"
        f"{'-' * 70}\n"
        f"Answer (truncated):\n{answer[:300]}{'...' if len(answer) > 300 else ''}\n"
        f"{'-' * 70}\n"
        f"Should NOT contain: {forbidden}\n"
        f"But found: {found}\n"
        f"{'=' * 70}"
    )


def format_sources_error(
    question: str,
    expected_sources: List[str],
    actual_sources: List[str],
    missing: List[str],
) -> str:
    """Format detailed error message for source citation assertion."""
    return (
        f"\n{'=' * 70}\n"
        f"SOURCE CITATION CHECK FAILED\n"
        f"{'=' * 70}\n"
        f"Question: {question}\n"
        f"{'-' * 70}\n"
        f"Expected sources: {expected_sources}\n"
        f"Actual sources: {actual_sources}\n"
        f"Missing sources: {missing}\n"
        f"{'=' * 70}"
    )


def format_length_error(
    question: str,
    answer: str,
    actual_length: int,
    min_len: int,
    max_len: int,
) -> str:
    """Format detailed error message for answer length assertion."""
    return (
        f"\n{'=' * 70}\n"
        f"ANSWER LENGTH CHECK FAILED\n"
        f"{'=' * 70}\n"
        f"Question: {question}\n"
        f"{'-' * 70}\n"
        f"Answer:\n{answer}\n"
        f"{'-' * 70}\n"
        f"Actual length: {actual_length} characters\n"
        f"Expected range: {min_len}-{max_len} characters\n"
        f"{'=' * 70}"
    )


def check_keywords(answer: str, keywords: List[str]) -> tuple[List[str], List[str]]:
    """Check which keywords are present/missing in answer."""
    answer_lower = answer.lower()
    found = [kw for kw in keywords if kw.lower() in answer_lower]
    missing = [kw for kw in keywords if kw.lower() not in answer_lower]
    return found, missing


def check_sources(
    result: Dict[str, Any],
    expected_sources: List[str],
) -> tuple[List[str], List[str]]:
    """Check which expected sources are cited."""
    sources = result.get("sources", [])
    actual_source_names = [
        src.get("document", "").lower() for src in sources
    ]

    found = []
    missing = []

    for expected in expected_sources:
        expected_lower = expected.lower()
        # Check if expected source name is contained in any actual source
        if any(expected_lower in actual for actual in actual_source_names):
            found.append(expected)
        else:
            missing.append(expected)

    return found, missing


# =============================================================================
# PARAMETRIZED TESTS
# =============================================================================


@pytest.mark.parametrize(
    "test_case",
    load_test_cases(),
    ids=get_test_ids(),
)
class TestPromptRegression:
    """Regression tests for RAG prompt responses."""

    def test_expected_keywords(
        self,
        qa_pipeline: ProductionQA,
        test_case: Dict[str, Any],
    ):
        """Verify expected keywords are present in the answer."""
        question = test_case["question"]
        expected_keywords = test_case.get("expected_keywords", [])

        if not expected_keywords:
            pytest.skip("No expected keywords defined for this test case")

        result = run_query(qa_pipeline, question)
        answer = result.get("answer", "")

        found, missing = check_keywords(answer, expected_keywords)

        # At least one expected keyword should be present
        assert found, format_keywords_error(
            question=question,
            answer=answer,
            expected=expected_keywords,
            found=found,
            missing=missing,
        )

    def test_forbidden_content(
        self,
        qa_pipeline: ProductionQA,
        test_case: Dict[str, Any],
    ):
        """Verify forbidden content is NOT present in the answer."""
        question = test_case["question"]
        should_not_contain = test_case.get("should_not_contain", [])

        if not should_not_contain:
            pytest.skip("No forbidden content defined for this test case")

        result = run_query(qa_pipeline, question)
        answer = result.get("answer", "")

        answer_lower = answer.lower()
        found_forbidden = [
            phrase for phrase in should_not_contain
            if phrase.lower() in answer_lower
        ]

        assert not found_forbidden, format_forbidden_error(
            question=question,
            answer=answer,
            forbidden=should_not_contain,
            found=found_forbidden,
        )

    def test_source_citations(
        self,
        qa_pipeline: ProductionQA,
        test_case: Dict[str, Any],
    ):
        """Verify correct sources are cited in the response."""
        question = test_case["question"]
        expected_sources = test_case.get("expected_sources", [])

        if not expected_sources:
            pytest.skip("No expected sources defined for this test case")

        result = run_query(qa_pipeline, question)
        sources = result.get("sources", [])
        actual_source_names = [src.get("document", "") for src in sources]

        found, missing = check_sources(result, expected_sources)

        assert not missing, format_sources_error(
            question=question,
            expected_sources=expected_sources,
            actual_sources=actual_source_names,
            missing=missing,
        )

    def test_answer_length(
        self,
        qa_pipeline: ProductionQA,
        test_case: Dict[str, Any],
    ):
        """Verify answer length is within reasonable bounds."""
        question = test_case["question"]

        # Allow custom length bounds per test case
        min_len = test_case.get("min_answer_length", MIN_ANSWER_LENGTH)
        max_len = test_case.get("max_answer_length", MAX_ANSWER_LENGTH)

        result = run_query(qa_pipeline, question)
        answer = result.get("answer", "")
        actual_length = len(answer)

        assert min_len <= actual_length <= max_len, format_length_error(
            question=question,
            answer=answer,
            actual_length=actual_length,
            min_len=min_len,
            max_len=max_len,
        )


# =============================================================================
# STANDALONE TESTS
# =============================================================================


def test_all_test_cases_have_questions(test_cases: List[Dict[str, Any]]):
    """Validate that all test cases have required fields."""
    for i, case in enumerate(test_cases):
        assert "question" in case, f"Test case {i} missing 'question' field"
        assert case["question"].strip(), f"Test case {i} has empty question"


def test_json_file_exists():
    """Verify the test data file exists."""
    assert TEST_DATA_PATH.exists(), (
        f"Test data file not found: {TEST_DATA_PATH}\n"
        f"Create the file with test cases in the following format:\n"
        f'[{{"question": "...", "expected_keywords": [...], '
        f'"expected_sources": [...], "should_not_contain": [...]}}]'
    )


def test_json_file_valid():
    """Verify the test data file contains valid JSON."""
    with open(TEST_DATA_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            assert isinstance(data, list), "Test data must be a JSON array"
            assert len(data) > 0, "Test data array is empty"
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in test data file: {e}")


# =============================================================================
# COMPREHENSIVE TEST RUNNER
# =============================================================================


@pytest.mark.slow
def test_full_regression_suite(
    qa_pipeline: ProductionQA,
    test_cases: List[Dict[str, Any]],
):
    """
    Run comprehensive regression test on all cases.

    This test runs all checks for all test cases and collects
    all failures before reporting.
    """
    failures = []

    for i, test_case in enumerate(test_cases):
        question = test_case["question"]
        case_failures = []

        try:
            result = run_query(qa_pipeline, question)
            answer = result.get("answer", "")

            # Check keywords
            expected_keywords = test_case.get("expected_keywords", [])
            if expected_keywords:
                found, missing = check_keywords(answer, expected_keywords)
                if not found:
                    case_failures.append(
                        f"  - Keywords: None of {expected_keywords} found"
                    )

            # Check forbidden content
            should_not_contain = test_case.get("should_not_contain", [])
            if should_not_contain:
                answer_lower = answer.lower()
                found_forbidden = [
                    p for p in should_not_contain if p.lower() in answer_lower
                ]
                if found_forbidden:
                    case_failures.append(
                        f"  - Forbidden: Found {found_forbidden}"
                    )

            # Check sources
            expected_sources = test_case.get("expected_sources", [])
            if expected_sources:
                _, missing_sources = check_sources(result, expected_sources)
                if missing_sources:
                    case_failures.append(
                        f"  - Sources: Missing {missing_sources}"
                    )

            # Check length
            min_len = test_case.get("min_answer_length", MIN_ANSWER_LENGTH)
            max_len = test_case.get("max_answer_length", MAX_ANSWER_LENGTH)
            actual_len = len(answer)
            if not (min_len <= actual_len <= max_len):
                case_failures.append(
                    f"  - Length: {actual_len} chars (expected {min_len}-{max_len})"
                )

        except Exception as e:
            case_failures.append(f"  - Error: {e}")

        if case_failures:
            failures.append(
                f"\nCase {i + 1}: {question[:50]}...\n" +
                "\n".join(case_failures)
            )

    if failures:
        failure_report = (
            f"\n{'=' * 70}\n"
            f"REGRESSION TEST FAILURES: {len(failures)}/{len(test_cases)} cases\n"
            f"{'=' * 70}"
            + "".join(failures) +
            f"\n{'=' * 70}"
        )
        pytest.fail(failure_report)


# =============================================================================
# MAIN
# =============================================================================


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v", "--tb=short"])
