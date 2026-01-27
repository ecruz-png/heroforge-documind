# src/evaluation/trulens_monitor.py
import os
from trulens.core import TruSession, Feedback, Select
from trulens.apps.custom import TruCustomApp
from trulens.apps.app import instrument
from trulens.providers.openai import OpenAI as OpenAIProvider
from dotenv import load_dotenv

load_dotenv()


class InstrumentedRAG:
    """Wrapper that instruments RAG pipeline methods for TruLens

    Properly separates retrieve and generate steps to enable
    accurate faithfulness/groundedness measurement.
    """

    def __init__(self, rag_pipeline):
        self._rag = rag_pipeline
        self._last_context = []  # Store context for faithfulness tracking

    @instrument
    def retrieve(self, question: str) -> list:
        """Retrieve relevant documents - instrumented for context relevance"""
        # Use enhanced_search if available, otherwise fall back to query
        if hasattr(self._rag, 'enhanced_search'):
            docs = self._rag.enhanced_search(question, top_k=5)
        else:
            result = self._rag.query(question)
            docs = result.get('sources', [])

        # Extract text content for TruLens evaluation
        self._last_context = [
            doc.get('content', '') if isinstance(doc, dict) else str(doc)
            for doc in docs
        ]
        return self._last_context

    @instrument
    def generate(self, question: str, context: list) -> str:
        """Generate answer from context - instrumented for faithfulness"""
        # Build context string for the LLM
        context_str = "\n\n".join(context) if context else ""

        # Use the RAG pipeline's query method
        result = self._rag.query(question)
        return result.get('answer', '')

    @instrument
    def query(self, question: str) -> dict:
        """Full RAG pipeline: retrieve then generate"""
        # Step 1: Retrieve context (instrumented)
        context = self.retrieve(question)

        # Step 2: Generate answer (instrumented)
        answer = self.generate(question, context)

        return {
            'answer': answer,
            'context': context,
            'sources': self._last_context
        }


class DocuMindTruLens:
    """TruLens monitoring for DocuMind RAG (v2.x compatible)

    Implements the RAG Triad for comprehensive evaluation:
    - Answer Relevance: Is the answer relevant to the question?
    - Context Relevance: Is the retrieved context relevant to the question?
    - Faithfulness/Groundedness: Is the answer grounded in the context?
    """

    def __init__(self, rag_pipeline):
        # Wrap RAG pipeline with instrumented methods
        self.rag = InstrumentedRAG(rag_pipeline)

        # Initialize TruLens session
        self.session = TruSession()

        # Initialize OpenAI provider for feedback functions
        self.provider = OpenAIProvider(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_engine="gpt-4o-mini"
        )

        # Define comprehensive feedback functions for RAG Triad
        self.feedbacks = [
            # 1. Answer Relevance - Is the answer relevant to the question?
            Feedback(
                self.provider.relevance_with_cot_reasons,
                name="answer_relevance"
            )
            .on_input()
            .on_output(),

            # 2. Context Relevance - Is retrieved context relevant to question?
            Feedback(
                self.provider.relevance_with_cot_reasons,
                name="context_relevance"
            )
            .on_input()
            .on(Select.RecordCalls.retrieve.rets[:]),

            # 3. Faithfulness/Groundedness - Is answer grounded in context?
            # This is the KEY metric for preventing hallucinations
            Feedback(
                self.provider.groundedness_measure_with_cot_reasons,
                name="faithfulness"
            )
            .on(Select.RecordCalls.retrieve.rets[:].collect())  # context
            .on_output(),  # answer

            # 4. Additional groundedness check with answerability consideration
            Feedback(
                self.provider.groundedness_measure_with_cot_reasons_consider_answerability,
                name="groundedness_with_answerability"
            )
            .on(Select.RecordCalls.retrieve.rets[:].collect())
            .on_output()
        ]

        # Create TruCustomApp recorder
        self.tru_app = TruCustomApp(
            self.rag,
            app_name="DocuMind_RAG",
            app_version="production_v2",
            feedbacks=self.feedbacks
        )

        print("✅ TruLens monitoring initialized (RAG Triad enabled)")
        print("📊 Tracking: answer_relevance, context_relevance, faithfulness")
        print("📊 Dashboard: run `trulens-eval leaderboard` or use launch_dashboard()")

    def query(self, question: str):
        """Run monitored query with TruLens recording"""
        with self.tru_app as recording:
            result = self.rag.query(question)
        return result

    def get_records(self):
        """Get all recorded sessions"""
        records, feedback = self.session.get_records_and_feedback()
        return records

    def launch_dashboard(self, port=8501):
        """Launch TruLens Streamlit dashboard"""
        from trulens.dashboard import run_dashboard
        run_dashboard(self.session, port=port)
