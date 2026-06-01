import streamlit as st

def show():
    st.title("🏠 Dashboard")
    # st.write("Welcome to your AI-powered data platform. Select a service from the sidebar.")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Activity Analysis")
        st.write("Analyse user activity logs and extract structured business insights using AI.")

        st.subheader("🔄 Data Augmentation")
        st.write("Upload a CSV and generate synthetic data using AI to expand your dataset for testing.")

        st.subheader("🔍 RAG System")
        st.write("Upload PDF or Word auto-chunked into word-based overlapping chunks. Each chunk embedded using sentence-transformers (all-MiniLM-L6-v2). Question embedded → cosine similarity → top-K chunks retrieved. Shows each retrieved chunk with similarity score exactly like your screenshot. Gemini generates answer from retrieved chunks only, not the whole document Sidebar controls: Top-K, Chunk Size, Overlap")

    with col2:
        st.subheader("📄 Document Analysis")
        st.write("Upload a PDF or Word document and ask questions. AI answers based only on the document.")

        st.subheader("🗄️ Text to SQL")
        st.write("Ask business questions in natural language. AI generates and executes SQL queries on your database.")

        st.subheader("📊 RAG Evaluation")
        st.write("Same document upload → same RAG pipeline runs automatically. 8 pre-loaded evaluation questions (factual + out-of-scope) — all editable. For each question: RAG answers it, then a second Gemini call acts as judge. Judge returns score 0-10, verdict (CORRECT / PARTIAL / WRONG / HALLUCINATED), and reason. Summary dashboard shows Avg Score, Correct, Partial, Wrong, Hallucinated counts. Expandable detailed results per question exactly like your screenshot. Download full evaluation report as CSV")

    st.markdown("---")
    st.info("Use the sidebar to navigate between services.")