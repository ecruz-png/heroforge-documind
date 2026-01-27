"""
Intelligent DocuMind Q&A System
With memory, learning, and personalization
"""
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

from documind.memory.conversation import ConversationMemory, list_user_conversations
from documind.memory.feedback import FeedbackCollector
from documind.memory.learning import LearningSystem
from documind.rag.search import search_documents

# Load environment variables from .env
load_dotenv()

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)


class IntelligentQA:
    """
    Intelligent Q&A system with memory and learning.
    """

    def __init__(self, user_id: str = "anonymous"):
        self.user_id = user_id
        self.conversation: Optional[ConversationMemory] = None
        self.feedback_collector = FeedbackCollector(user_id=user_id)
        self.learning_system = LearningSystem()
        self.user_preferences = None

    def start_conversation(self, conversation_id: Optional[str] = None) -> str:
        """
        Start a new conversation or restore existing one.

        Args:
            conversation_id: Optional ID to restore existing conversation

        Returns:
            Conversation ID
        """
        self.conversation = ConversationMemory(
            conversation_id=conversation_id,
            user_id=self.user_id
        )
        # Load user preferences for personalization
        self.user_preferences = self.learning_system.learn_user_preferences(
            self.user_id, days=30
        )
        return self.conversation.conversation_id

    def ask(
        self,
        question: str,
        model: str = 'openai/gpt-4o'
    ) -> Dict[str, Any]:
        """
        Ask a question with conversation context.

        Steps:
        1. Add user message to conversation
        2. Get conversation context
        3. Retrieve documents (with personalization)
        4. Generate answer with context
        5. Add assistant message
        6. Return response
        """
        import time
        start_time = time.time()

        # Ensure conversation is started
        if not self.conversation:
            self.start_conversation()

        # 1. Add user message to conversation
        user_message = self.conversation.add_message("user", question)

        # 2. Get conversation context
        context_messages = self.conversation.get_context()

        # 3. Retrieve documents with personalization
        sources = self.personalize_search(question, top_k=5)

        # Build context from retrieved documents
        doc_context = "\n\n".join([
            f"[Source: {doc['document_name']} (relevance: {doc['similarity']:.2f})]\n{doc['content']}"
            for doc in sources
        ])

        # 4. Generate answer with context
        system_prompt = """You are an intelligent Q&A assistant with access to a knowledge base.
Use the provided context to answer questions accurately and helpfully.
Always cite your sources when referencing specific information.
If the context doesn't contain enough information, say so honestly.

Previous conversation context is provided to maintain continuity."""

        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history for context
        for msg in context_messages[:-1]:  # Exclude the current question
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current question with document context
        messages.append({
            "role": "user",
            "content": f"""Based on the following context, answer the question.

Context:
{doc_context}

Question: {question}

Provide a helpful, accurate answer based on the context. Cite sources when appropriate."""
        })

        # Call LLM
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )

        answer = response.choices[0].message.content
        response_time = time.time() - start_time

        # 5. Add assistant message with sources and metadata
        source_refs = [
            {"document": s["document_name"], "similarity": s["similarity"]}
            for s in sources
        ]
        metadata = {
            "model": model,
            "response_time": round(response_time, 2),
            "sources_count": len(sources)
        }

        assistant_message = self.conversation.add_message(
            "assistant",
            answer,
            sources=source_refs,
            metadata=metadata
        )

        # 6. Return response
        return {
            "answer": answer,
            "sources": source_refs,
            "message_id": assistant_message["id"],
            "conversation_id": self.conversation.conversation_id,
            "response_time": response_time,
            "model": model
        }

    def submit_feedback(
        self,
        message_id: int,
        rating: int,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit feedback for an answer.

        Args:
            message_id: Message being rated
            rating: 1-5 stars
            comment: Optional comment

        Returns:
            Created feedback record
        """
        if not self.conversation:
            raise ValueError("No active conversation. Start a conversation first.")

        return self.feedback_collector.submit_feedback(
            conversation_id=self.conversation.conversation_id,
            message_id=message_id,
            rating=rating,
            comment=comment,
            feedback_type="answer_quality"
        )

    def personalize_search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Personalized document retrieval.

        Steps:
        1. Get user preferences
        2. Retrieve documents
        3. Boost preferred documents
        4. Re-rank results
        """
        # 1 & 2. Retrieve documents using standard search
        results = search_documents(query, top_k=top_k * 2, similarity_threshold=0.3)

        if not results:
            return []

        # 3. Boost preferred documents based on user preferences
        if self.user_preferences and 'top_documents' in self.user_preferences:
            preferred_docs = {
                d['document']: d['count']
                for d in self.user_preferences.get('top_documents', [])
            }

            for result in results:
                doc_name = result.get('document_name', '')
                # Check if this document is in user's preferred list
                for pref_doc, pref_count in preferred_docs.items():
                    if pref_doc in doc_name or doc_name in pref_doc:
                        # Boost by preference score (max 20% boost)
                        boost = min(0.2, pref_count * 0.02)
                        result['similarity'] = min(1.0, result['similarity'] + boost)
                        result['personalized'] = True
                        break
                else:
                    result['personalized'] = False

        # 4. Re-rank results by adjusted similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)

        return results[:top_k]

    def apply_learning(self) -> Dict[str, Any]:
        """
        Apply learning from feedback.

        Returns:
            Learning results with changes applied and suggestions
        """
        # Apply system-wide learning
        learning_results = self.learning_system.apply_learning()

        # Refresh user preferences
        self.user_preferences = self.learning_system.learn_user_preferences(
            self.user_id, days=30
        )

        return {
            "learning_applied": True,
            "changes": learning_results.get('changes_applied', []),
            "suggestions": learning_results.get('suggestions', {}),
            "user_preferences_updated": self.user_preferences is not None
        }

    def get_conversation_list(self) -> List[Dict[str, Any]]:
        """
        List user's conversations.

        Returns:
            List of conversations with metadata
        """
        return list_user_conversations(self.user_id, limit=20)

    def get_insights(self) -> Dict[str, Any]:
        """
        Get user insights and analytics.

        Returns:
            User statistics and preferences
        """
        # Get user preferences
        preferences = self.learning_system.learn_user_preferences(
            self.user_id, days=30
        )

        # Get feedback analysis
        feedback_analysis = self.feedback_collector.analyze_feedback(days=30)

        # Get conversation statistics
        conversations = self.get_conversation_list()

        return {
            "user_id": self.user_id,
            "total_conversations": len(conversations),
            "preferences": preferences,
            "feedback_summary": feedback_analysis,
            "top_topics": preferences.get('top_topics', []),
            "preferred_documents": preferences.get('top_documents', []),
            "satisfaction_rate": feedback_analysis.get('satisfaction_rate', 0),
            "average_rating": feedback_analysis.get('average_rating', 0)
        }


def main():
    """
    Interactive CLI with all features:

    Commands:
    - /new - Start new conversation
    - /list - List conversations
    - /load <id> - Load conversation
    - /feedback - Rate last answer
    - /insights - Show user insights
    - /learn - Apply learning
    - /quit - Exit
    """
    print("=" * 60)
    print("DocuMind Intelligent Q&A System")
    print("=" * 60)

    # Get user ID
    user_id = input("Enter your user ID (or press Enter for 'anonymous'): ").strip()
    if not user_id:
        user_id = "anonymous"

    qa = IntelligentQA(user_id=user_id)
    last_message_id = None

    print(f"\nWelcome, {user_id}!")
    print("\nCommands:")
    print("  /new      - Start new conversation")
    print("  /list     - List your conversations")
    print("  /load <id> - Load a conversation")
    print("  /feedback - Rate the last answer (1-5)")
    print("  /insights - View your insights")
    print("  /learn    - Apply learning optimizations")
    print("  /quit     - Exit")
    print("\nOr just type your question to get started.\n")

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                parts = user_input.split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                if command == "/quit":
                    print("\nGoodbye!")
                    break

                elif command == "/new":
                    conv_id = qa.start_conversation()
                    print(f"\nStarted new conversation: {conv_id}\n")

                elif command == "/list":
                    conversations = qa.get_conversation_list()
                    print("\nYour Conversations:")
                    print("-" * 40)
                    if not conversations:
                        print("  No conversations found.")
                    else:
                        for conv in conversations:
                            print(f"  ID: {conv['id']}")
                            print(f"  Title: {conv.get('title', 'Untitled')}")
                            print(f"  Last Activity: {conv.get('last_message_at', 'N/A')}")
                            print("-" * 40)
                    print()

                elif command == "/load":
                    if not args:
                        print("\nUsage: /load <conversation_id>\n")
                    else:
                        try:
                            qa.start_conversation(conversation_id=args)
                            print(f"\nLoaded conversation: {args}")
                            stats = qa.conversation.get_conversation_stats()
                            print(f"Messages: {stats.get('message_count', 0)}\n")
                        except Exception as e:
                            print(f"\nError loading conversation: {e}\n")

                elif command == "/feedback":
                    if last_message_id is None:
                        print("\nNo answer to rate yet. Ask a question first.\n")
                    else:
                        try:
                            rating = input("Rating (1-5 stars): ").strip()
                            rating = int(rating)
                            comment = input("Comment (optional, press Enter to skip): ").strip()
                            comment = comment if comment else None

                            qa.submit_feedback(last_message_id, rating, comment)
                            print("\nThank you for your feedback!\n")
                        except ValueError:
                            print("\nInvalid rating. Please enter a number 1-5.\n")
                        except Exception as e:
                            print(f"\nError submitting feedback: {e}\n")

                elif command == "/insights":
                    print("\nLoading insights...")
                    insights = qa.get_insights()
                    print("\nYour Insights:")
                    print("-" * 40)
                    print(f"  Total Conversations: {insights['total_conversations']}")
                    print(f"  Average Rating: {insights['average_rating']}")
                    print(f"  Satisfaction Rate: {insights['satisfaction_rate']:.1%}")

                    if insights['top_topics']:
                        print("\n  Top Topics:")
                        for topic in insights['top_topics'][:5]:
                            print(f"    - {topic['topic']} ({topic['count']} queries)")

                    if insights['preferred_documents']:
                        print("\n  Preferred Documents:")
                        for doc in insights['preferred_documents'][:3]:
                            print(f"    - {doc['document']} ({doc['count']} uses)")
                    print()

                elif command == "/learn":
                    print("\nApplying learning from feedback...")
                    results = qa.apply_learning()
                    print("\nLearning Results:")
                    print("-" * 40)
                    if results['changes']:
                        print("  Changes Applied:")
                        for change in results['changes']:
                            print(f"    - {change['change']}: {change['rationale']}")
                    else:
                        print("  No immediate changes needed.")

                    if any(results['suggestions'].values()):
                        print("\n  Suggestions:")
                        for category, items in results['suggestions'].items():
                            if items:
                                print(f"    {category.upper()}:")
                                for item in items:
                                    print(f"      - {item}")
                    print()

                else:
                    print(f"\nUnknown command: {command}")
                    print("Type /quit to exit or ask a question.\n")

            else:
                # Regular question
                print("\nSearching and generating answer...")
                try:
                    response = qa.ask(user_input)
                    last_message_id = response['message_id']

                    print(f"\nAssistant: {response['answer']}")
                    print(f"\n[Sources: {len(response['sources'])} documents | "
                          f"Time: {response['response_time']:.2f}s]")

                    if response['sources']:
                        print("  Referenced:")
                        for src in response['sources'][:3]:
                            print(f"    - {src['document']} ({src['similarity']:.2f})")
                    print()

                except Exception as e:
                    print(f"\nError: {e}\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            print("\n\nGoodbye!")
            break


if __name__ == "__main__":
    main()
