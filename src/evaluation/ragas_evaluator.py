# src/evaluation/ragas_evaluator.py
import os
from typing import List, Dict
from statistics import mean
from datetime import datetime

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    answer_correctness
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from datasets import Dataset
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()


class RAGASEvaluator:
    """Production RAGAS evaluator for DocuMind (compatible with RAGAS 0.4.x)"""

    def __init__(self, rag_pipeline):
        """
        Initialize evaluator with a RAG pipeline.

        Args:
            rag_pipeline: ProductionQA instance with query() method
        """
        self.rag_pipeline = rag_pipeline

        # Configure LLM for RAGAS evaluation (judges answer quality)
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.llm = LangchainLLMWrapper(llm)

        # Configure embeddings for RAGAS (measures semantic similarity)
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.embeddings = LangchainEmbeddingsWrapper(embeddings)

        # Metrics to evaluate
        # - faithfulness: Is the answer grounded in the retrieved context?
        # - answer_relevancy: Is the answer relevant to the question?
        # - answer_correctness: Is the answer factually correct vs ground_truth?
        self.metrics = [
            faithfulness,
            answer_relevancy,
            answer_correctness
        ]

    def evaluate(self, test_dataset: List[Dict]) -> Dict:
        """Run RAGAS evaluation on test dataset"""
        print(f"\n{'='*60}")
        print(f"RAGAS EVALUATION STARTED: {datetime.now()}")
        print(f"{'='*60}")
        print(f"Test cases: {len(test_dataset)}")

        # Generate answers for each test case
        eval_data = []
        for i, test_case in enumerate(test_dataset, 1):
            print(f"[{i}/{len(test_dataset)}] {test_case['question'][:50]}...")

            # ProductionQA.query() returns dict with 'answer' and 'sources'
            result = self.rag_pipeline.query(test_case['question'])

            # Extract contexts from sources (ProductionQA uses 'preview' field)
            contexts = [
                source.get('preview', '')
                for source in result.get('sources', [])
                if source.get('preview')  # Filter out empty previews
            ]

            # Build evaluation record (RAGAS 0.4.x format)
            eval_data.append({
                'question': test_case['question'],
                'answer': result['answer'],
                'contexts': contexts,
                'ground_truth': test_case.get('ground_truth', '')
            })

        # Run RAGAS evaluation with configured LLM and embeddings
        print("\nRunning RAGAS metrics...")
        dataset = Dataset.from_list(eval_data)
        results = evaluate(
            dataset=dataset,
            metrics=self.metrics,
            llm=self.llm,
            embeddings=self.embeddings
        )

        return self.format_results(results)

    def format_results(self, results) -> Dict:
        """Format RAGAS results with pass/fail indicators"""
        # RAGAS 0.4.x returns a Dataset - convert to pandas and get means
        df = results.to_pandas()

        formatted = {}
        metric_names = ['faithfulness',
                        'answer_relevancy', 'answer_correctness']

        for metric in metric_names:
            if metric in df.columns:
                # Get mean, filtering out NaN values
                values = df[metric].dropna().tolist()
                formatted[metric] = mean(values) if values else 0.0
            else:
                formatted[metric] = 0.0

        # Calculate average of available metrics
        valid_scores = [v for v in formatted.values() if v > 0]
        formatted['average_score'] = mean(
            valid_scores) if valid_scores else 0.0

        # Add pass/fail based on thresholds
        thresholds = {
            'faithfulness': 0.70,
            'answer_relevancy': 0.80,
            'answer_correctness': 0.70
        }

        formatted['passed'] = all(
            formatted.get(metric, 0) >= threshold
            for metric, threshold in thresholds.items()
        )

        # Include per-question scores for detailed analysis
        formatted['per_question'] = df.to_dict('records')

        return formatted
