import streamlit as st
import os
import time
from typing import List

# Import components from previous sessions
try:
    from documind.rag.production_qa import ProductionQA
    from documind.rag.search import search_documents
    from documind.processor import DocumentProcessor
except ImportError as e:
    st.error(
        f"Modules not found. Make sure you are running from the project root.\nError: {e}")
    st.stop()

# Page Config
st.set_page_config(page_title="DocuMind", page_icon="🧠", layout="wide")

st.title("🧠 DocuMind: Enterprise Knowledge Base")

# Sidebar: App Mode Selection
mode = st.sidebar.radio(
    "Select Mode", ["Chat Assistant", "Document Ingestion", "Knowledge Explorer"])

# Initialize Session State for Chat
if "messages" not in st.session_state:
    st.session_state.messages = []
if "qa_system" not in st.session_state:
    # Initialize the ProductionQA system
    st.session_state.qa_system = ProductionQA(enable_logging=False)

# --- MODE 1: CHAT ASSISTANT ---
if mode == "Chat Assistant":
    st.header("Chat with your Documents")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # 1. User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Assistant Response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Call ProductionQA
                response = st.session_state.qa_system.query(prompt)

                answer_text = response['answer']
                sources = response.get('sources', [])

                # Display Answer
                st.markdown(answer_text)

                # Display Sources
                if sources:
                    with st.expander("📚 View Sources"):
                        for s in sources:
                            st.markdown(
                                f"- **{s.get('title', 'Doc')}**: {s.get('preview', '')}...")

                # Feedback buttons (visual only - extend with your feedback system)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👍 Helpful", key=f"up_{len(st.session_state.messages)}"):
                        st.toast("Thanks for your feedback!")
                with col2:
                    if st.button("👎 Not Helpful", key=f"down_{len(st.session_state.messages)}"):
                        st.toast("Thanks for your feedback!")

        # Add to history
        st.session_state.messages.append(
            {"role": "assistant", "content": answer_text})

# --- MODE 2: DOCUMENT INGESTION ---
elif mode == "Document Ingestion":
    st.header("📥 Ingest New Documents")
    st.info(
        "Upload documents to add them to the Knowledge Base (supports PDF, DOCX, TXT).")

    uploaded_files = st.file_uploader(
        "Choose files", accept_multiple_files=True)

    if st.button("Process Documents") and uploaded_files:
        processor = DocumentProcessor()

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing {uploaded_file.name}...")

            # Save temp file
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            try:
                # Extract & Chunk
                result = processor.process_document(temp_path)

                # Upload to DB
                upload_status = processor.upload_to_documind(result)

                st.success(
                    f"✅ {uploaded_file.name}: {result['metadata']['basic']['page_count']} pages processed.")
            except Exception as e:
                st.error(f"❌ Failed {uploaded_file.name}: {str(e)}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

            progress_bar.progress((i + 1) / len(uploaded_files))

        status_text.text("Ingestion Complete!")

# --- MODE 3: KNOWLEDGE EXPLORER ---
elif mode == "Knowledge Explorer":
    st.header("🔎 Explore Knowledge Base")

    search_term = st.text_input(
        "Search documents by keyword or semantic meaning")

    if search_term:
        # Use semantic search
        results = search_documents(search_term, top_k=10)

        st.subheader(f"Found {len(results)} chunks")
        for r in results:
            with st.container(border=True):
                st.markdown(
                    f"**Document:** {r.get('document_name', 'Unknown')}")
                st.caption(f"Score: {r.get('similarity', 0.0):.4f}")
                st.text(r.get('content', '')[:300] + "...")

# Footer
st.divider()
st.caption("DocuMind v1.0 | Built with HeroForge Agentic Engineering")
