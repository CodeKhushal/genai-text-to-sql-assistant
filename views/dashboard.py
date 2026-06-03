import streamlit as st

def show():
    st.title("🏠 Dashboard")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("✨ Prompt Optimisation")
        st.write(
            "Build structured prompts using 6 key components (Context, Role, Task, Constraints, "
            "Format, Examples). AI optimises your prompt, scores quality before and after, "
            "explains every change, and lets you compare original vs optimised responses side by side."
        )

        st.subheader("📊 Activity Analysis")
        st.write("Analyse user activity logs and extract structured business insights using AI.")

        st.subheader("🔄 Data Augmentation")
        st.write("Upload a CSV and generate synthetic data using AI to expand your dataset for testing.")

        st.subheader("🔍 RAG System")
        st.write(
            "Upload a PDF or Word document — auto-chunked, embedded using sentence-transformers, "
            "and queried via cosine similarity. Gemini generates answers from retrieved chunks only. "
            "Sidebar controls: Top-K, Chunk Size, Overlap."
        )

    with col2:
        st.subheader("📄 Document Analysis")
        st.write("Upload a PDF or Word document and ask questions. AI answers based only on the document.")

        st.subheader("🗄️ Text to SQL")
        st.write("Ask business questions in natural language. AI generates and executes SQL queries on your database.")

        st.subheader("📊 RAG Evaluation")
        st.write(
            "Automatically evaluate RAG answer quality. 8 pre-loaded questions — all editable. "
            "LLM judge scores each answer: CORRECT / PARTIAL / WRONG / HALLUCINATED. "
            "Summary dashboard + downloadable CSV report."
        )

    st.markdown("---")
    st.info("Use the sidebar to navigate between services.")