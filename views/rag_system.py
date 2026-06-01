import streamlit as st
from pypdf import PdfReader
from docx import Document
import numpy as np

# ── TEXT EXTRACTION ───────────────────────────────────────────────────────────

def read_pdf(file):
    text = ""
    reader = PdfReader(file)
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text


def read_docx(file):
    text = ""
    doc = Document(file)
    for para in doc.paragraphs:
        if para.text.strip():
            text += para.text + "\n"
    return text


# ── CHUNKING ──────────────────────────────────────────────────────────────────

def chunk_text(text, chunk_size=200, overlap=30):
    """
    Split document into overlapping word-based chunks.
    chunk_size: number of words per chunk
    overlap: number of words shared between adjacent chunks
    """
    words = text.split()
    chunks = []
    step = chunk_size - overlap

    for i in range(0, len(words), step):
        chunk = " ".join(words[i: i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    return chunks


# ── EMBEDDINGS ────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading embedding model...")
def load_embedding_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


def embed_texts(texts):
    model = load_embedding_model()
    return model.encode(texts, normalize_embeddings=True)


def cosine_similarity(query_vec, doc_vecs):
    """Compute cosine similarity — vectors are already normalised."""
    return np.dot(doc_vecs, query_vec)


# ── RETRIEVAL ─────────────────────────────────────────────────────────────────

def retrieve_chunks(question, chunk_embeddings, chunks, top_k=3):
    query_vec = embed_texts([question])[0]
    scores = cosine_similarity(query_vec, chunk_embeddings)
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        results.append({
            "chunk": chunks[idx],
            "score": float(scores[idx]),
            "index": int(idx)
        })
    return results


# ── ANSWER GENERATION ─────────────────────────────────────────────────────────

def generate_rag_answer(question, retrieved_chunks, client, model_name):
    context = "\n\n".join(
        [f"[Chunk {i+1}]: {r['chunk']}" for i, r in enumerate(retrieved_chunks)]
    )

    prompt = f"""
Context:
You are a document Q&A assistant using Retrieval Augmented Generation.

Role:
Act as an expert document analyst.

Task:
Answer the user's question using ONLY the retrieved document chunks provided below.

Constraints:
- Answer ONLY from the provided chunks
- Do not hallucinate or add external knowledge
- If the answer is not present in the chunks, say exactly:
  "The answer is not available in the retrieved document sections."
- Keep the answer concise and factual

Retrieved Document Chunks:
{context}

User Question:
{question}
"""

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text.strip(), None
    except Exception as e:
        return None, str(e)


# ── PAGE ──────────────────────────────────────────────────────────────────────

def show(client, model_name):

    # ── Sidebar config ──
    with st.sidebar:
        st.markdown("---")
        st.markdown("**RAG Configuration**")
        st.caption(f"Model: `{model_name}`")
        top_k = st.slider("Top-K", 1, 8, 3)
        chunk_size = st.slider("Chunk Size", 50, 500, 200, step=50)
        overlap = st.slider("Overlap", 0, 100, 30, step=10)

    # ── Session state ──
    if "rag_chunks" not in st.session_state:
        st.session_state.rag_chunks = []
    if "rag_embeddings" not in st.session_state:
        st.session_state.rag_embeddings = None
    if "rag_doc_name" not in st.session_state:
        st.session_state.rag_doc_name = None
    if "rag_qa_history" not in st.session_state:
        st.session_state.rag_qa_history = []

    st.title("RAG System")
    st.write("Retrieval Augmented Generation - answers from document chunks only.")
    st.markdown("---")

    # ── File upload ──
    uploaded_file = st.file_uploader(
        "Upload PDF or Word document",
        type=["pdf", "docx"]
    )

    if uploaded_file:
        if uploaded_file.name != st.session_state.rag_doc_name:

            with st.spinner("Reading and chunking document..."):
                if uploaded_file.name.endswith(".pdf"):
                    text = read_pdf(uploaded_file)
                else:
                    text = read_docx(uploaded_file)

            if not text.strip():
                st.error("Could not extract text. Try a different document.")
                st.stop()

            with st.spinner("Creating embeddings..."):
                chunks = chunk_text(text, chunk_size, overlap)
                embeddings = embed_texts(chunks)

            st.session_state.rag_chunks = chunks
            st.session_state.rag_embeddings = embeddings
            st.session_state.rag_doc_name = uploaded_file.name
            st.session_state.rag_qa_history = []

    # ── Index status ──
    if st.session_state.rag_chunks:
        n_chunks = len(st.session_state.rag_chunks)
        st.info(
            f"Document indexed: **{n_chunks} chunks** | "
            f"Top-K: **{top_k}** | "
            f"Chunk size: **{chunk_size} words**"
        )

        # ── Question input ──
        question = st.text_input("❓ Ask a question:")

        if st.button("▶ Search & Answer"):
            if not question.strip():
                st.warning("Please enter a question.")
            else:
                with st.spinner("Retrieving relevant chunks..."):
                    results = retrieve_chunks(
                        question,
                        st.session_state.rag_embeddings,
                        st.session_state.rag_chunks,
                        top_k=top_k
                    )

                with st.spinner("Generating answer..."):
                    answer, error = generate_rag_answer(question, results, client, model_name)

                if error:
                    st.error(f"Error: {error}")
                else:
                    # Show retrieved chunks
                    with st.expander("📋 Retrieved Chunks", expanded=True):
                        for i, r in enumerate(results):
                            st.markdown(
                                f"**Chunk {i+1}** "
                                f"(similarity: "
                                f"<span style='color:#4CAF50;font-weight:bold'>"
                                f"{r['score']:.4f}</span>)",
                                unsafe_allow_html=True
                            )
                            st.write(r["chunk"])
                            if i < len(results) - 1:
                                st.divider()

                    # Show answer
                    st.success(answer)

                    # Save to history
                    st.session_state.rag_qa_history.append({
                        "question": question,
                        "answer": answer,
                        "chunks": results,
                        "top_k": top_k
                    })

        # ── Q&A History ──
        if len(st.session_state.rag_qa_history) > 1:
            st.markdown("---")
            st.subheader("Previous Questions")
            for item in reversed(st.session_state.rag_qa_history[:-1]):
                with st.expander(f"Q: {item['question']}"):
                    st.success(item["answer"])

    else:
        st.info("Upload a document above to begin.")