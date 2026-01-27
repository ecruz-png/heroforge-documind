# src/evaluation/trulens_monitor.py
import os
from trulens.core import TruSession, Feedback
from trulens.apps.custom import TruCustomApp, instrument
from trulens.providers.openai import OpenAI as OpenAIProvider
from dotenv import load_dotenv

load_dotenv()


class InstrumentedRAG:
    """Wrapper that instruments RAG pipeline methods for TruLens"""

    def __init__(self, rag_pipeline):
        self._rag = rag_pipeline

    @instrument
    def query(self, question: str) -> dict:
        """Instrumented query method for TruLens recording"""
        return self._rag.query(question)

    @instrument
    def retrieve(self, question: str) -> list:
        """Retrieve relevant documents"""
        result = self._rag.query(question)
        return result.get('sources', [])

    @instrument
    def generate(self, question: str, context: list) -> str:
        """Generate answer from context"""
        result = self._rag.query(question)
        return result.get('answer', '')


class DocuMindTruLens:
    """TruLens monitoring for DocuMind RAG (v2.x compatible)"""

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

        # Define feedback functions
        self.feedbacks = [
            # Answer relevance - Is the answer relevant to the question?
            Feedback(self.provider.relevance_with_cot_reasons,
                     name="answer_relevance")
            .on_input()
            .on_output(),

            # Groundedness - Is answer grounded in context?
            Feedback(self.provider.groundedness_measure_with_cot_reasons,
                     name="groundedness")
            .on_input()
            .on_output()
        ]

        # Create TruCustomApp recorder
        self.tru_app = TruCustomApp(
            self.rag,
            app_name="DocuMind_RAG",
            app_version="production",
            feedbacks=self.feedbacks
        )

        print("✅ TruLens monitoring initialized")
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
