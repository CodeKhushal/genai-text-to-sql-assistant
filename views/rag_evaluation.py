import streamlit as st
from pypdf import PdfReader
from docx import Document
import numpy as np
import json

# ── REUSE RAG FUNCTIONS ───────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading embedding model...")
def load_embedding_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


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


def chunk_text(text, chunk_size=200, overlap=30):
    words = text.split()
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i: i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def embed_texts(texts):
    model = load_embedding_model()
    return model.encode(texts, normalize_embeddings=True)


def retrieve_chunks(question, chunk_embeddings, chunks, top_k=3):
    query_vec = embed_texts([question])[0]
    scores = np.dot(chunk_embeddings, query_vec)
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [{"chunk": chunks[i], "score": float(scores[i])} for i in top_indices]


def get_rag_answer(question, chunks, chunk_embeddings, top_k, client, model_name):
    results = retrieve_chunks(question, chunk_embeddings, chunks, top_k)
    context = "\n\n".join([f"[Chunk {i+1}]: {r['chunk']}" for i, r in enumerate(results)])

    prompt = f"""
Context: You are a document Q&A assistant.
Role: Expert document analyst.
Task: Answer the question using ONLY the chunks below.
Constraints:
- Only use provided chunks
- If not found, say "The answer is not available in the document."
- Be concise

Chunks:
{context}

Question: {question}
"""
    try:
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"


# ── LLM JUDGE ─────────────────────────────────────────────────────────────────

def evaluate_answer(question, expected, actual, q_type, client, model_name):
    prompt = f"""
Context:
You are an AI evaluation expert assessing RAG system answers.

Role:
Act as a strict but fair answer quality judge.

Task:
Compare the actual answer to the expected answer and score it.

Question: {question}
Question Type: {q_type}
Expected Answer: {expected}
Actual Answer: {actual}

Constraints:
- Return ONLY valid JSON
- No markdown, no explanation outside JSON
- Score must be integer 0-10
- Verdict must be exactly one of: CORRECT, PARTIAL, WRONG, HALLUCINATED
- CORRECT = answer is accurate and complete (score 8-10)
- PARTIAL = answer is partially correct or incomplete (score 4-7)
- WRONG = answer is incorrect (score 0-3)
- HALLUCINATED = answer contains information not in the question context (score 0)

Format:
{{
  "score": 9,
  "verdict": "CORRECT",
  "reason": "one sentence explanation"
}}
"""
    try:
        response = client.models.generate_content(model=model_name, contents=prompt)
        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end != 0:
            text = text[start:end]
        return json.loads(text)
    except Exception as e:
        return {"score": 0, "verdict": "WRONG", "reason": f"Evaluation error: {str(e)}"}


# ── VERDICT STYLING ───────────────────────────────────────────────────────────

VERDICT_ICONS = {
    "CORRECT":      "🟢",
    "PARTIAL":      "🟡",
    "WRONG":        "❌",
    "HALLUCINATED": "🚨"
}

VERDICT_COLORS = {
    "CORRECT":      "#4CAF50",
    "PARTIAL":      "#FFC107",
    "WRONG":        "#F44336",
    "HALLUCINATED": "#9C27B0"
}


# ── DEFAULT EVAL QUESTIONS ────────────────────────────────────────────────────

DEFAULT_QUESTIONS = [
    {"question": "What was the total revenue in 2024?",            "expected": "48.5 million",        "type": "factual"},
    {"question": "Which region had the highest revenue?",          "expected": "North America",       "type": "factual"},
    {"question": "What was the profit margin in Q3 2024?",         "expected": "22%",                 "type": "factual"},
    {"question": "What is the revenue target for 2025?",           "expected": "58 million",          "type": "factual"},
    {"question": "What was the customer churn rate increase in SMB?","expected": "8% to 11%",         "type": "factual"},
    {"question": "Who is the CEO of Acme Corp?",                   "expected": "not in document",     "type": "out-of-scope"},
    {"question": "How many employees does the company have?",      "expected": "not in document",     "type": "out-of-scope"},
    {"question": "What was the revenue in 2022?",                  "expected": "not in document",     "type": "out-of-scope"},
]


# ── PAGE ──────────────────────────────────────────────────────────────────────

def show(client, model_name):

    # ── Sidebar config ──
    with st.sidebar:
        st.markdown("---")
        st.markdown("**RAG Configuration**")
        st.caption(f"Model: `{model_name}`")
        top_k = st.slider("Top-K", 1, 8, 3, key="eval_topk")
        chunk_size = st.slider("Chunk Size", 50, 500, 200, step=50, key="eval_chunk")
        overlap = st.slider("Overlap", 0, 100, 30, step=10, key="eval_overlap")

    # ── Session state ──
    if "eval_chunks" not in st.session_state:
        st.session_state.eval_chunks = []
    if "eval_embeddings" not in st.session_state:
        st.session_state.eval_embeddings = None
    if "eval_doc_name" not in st.session_state:
        st.session_state.eval_doc_name = None
    if "eval_results" not in st.session_state:
        st.session_state.eval_results = []

    st.title("RAG Evaluation")
    st.write("Automatically evaluate RAG answer quality against expected answers.")
    st.markdown("---")

    # ── Document upload ──
    uploaded_file = st.file_uploader(
        "Upload the document to evaluate against",
        type=["pdf", "docx"]
    )

    if uploaded_file:
        if uploaded_file.name != st.session_state.eval_doc_name:
            with st.spinner("Indexing document..."):
                if uploaded_file.name.endswith(".pdf"):
                    text = read_pdf(uploaded_file)
                else:
                    text = read_docx(uploaded_file)
                chunks = chunk_text(text, chunk_size, overlap)
                embeddings = embed_texts(chunks)
            st.session_state.eval_chunks = chunks
            st.session_state.eval_embeddings = embeddings
            st.session_state.eval_doc_name = uploaded_file.name
            st.session_state.eval_results = []
            st.info(f"Document indexed: {len(chunks)} chunks")

    # ── Evaluation questions editor ──
    st.subheader("Evaluation Questions")
    st.caption("Edit the expected answers to match your document, then run evaluation.")

    questions = []
    for i, q in enumerate(DEFAULT_QUESTIONS):
        with st.expander(f"Q{i+1}: {q['question']}", expanded=False):
            col1, col2 = st.columns([3, 1])
            with col1:
                expected = st.text_input(
                    "Expected answer",
                    value=q["expected"],
                    key=f"expected_{i}"
                )
            with col2:
                q_type = st.selectbox(
                    "Type",
                    ["factual", "inferential", "out-of-scope"],
                    index=["factual", "inferential", "out-of-scope"].index(q["type"]),
                    key=f"type_{i}"
                )
            questions.append({
                "question": q["question"],
                "expected": expected,
                "type": q_type
            })

    st.markdown("---")

    # ── Run evaluation ──
    if st.session_state.eval_chunks:
        if st.button("▶ Run Full Evaluation", type="primary"):
            results = []
            progress = st.progress(0, text="Running evaluation...")

            for i, q in enumerate(questions):
                progress.progress(
                    (i + 1) / len(questions),
                    text=f"Evaluating question {i+1}/{len(questions)}..."
                )

                # Get RAG answer
                actual = get_rag_answer(
                    q["question"],
                    st.session_state.eval_chunks,
                    st.session_state.eval_embeddings,
                    top_k, client, model_name
                )

                # Judge the answer
                evaluation = evaluate_answer(
                    q["question"],
                    q["expected"],
                    actual,
                    q["type"], client, model_name
                )

                results.append({
                    "question": q["question"],
                    "expected": q["expected"],
                    "actual": actual,
                    "type": q["type"],
                    "score": evaluation.get("score", 0),
                    "verdict": evaluation.get("verdict", "WRONG"),
                    "reason": evaluation.get("reason", "")
                })

            progress.empty()
            st.session_state.eval_results = results

    # ── Display results ──
    if st.session_state.eval_results:
        results = st.session_state.eval_results

        # ── Summary banner ──
        st.subheader("Summary")

        avg_score = sum(r["score"] for r in results) / len(results)
        correct     = sum(1 for r in results if r["verdict"] == "CORRECT")
        partial     = sum(1 for r in results if r["verdict"] == "PARTIAL")
        wrong       = sum(1 for r in results if r["verdict"] == "WRONG")
        hallucinated= sum(1 for r in results if r["verdict"] == "HALLUCINATED")

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Avg Score", f"{avg_score:.1f}/10")
        with col2:
            st.metric("🟢 Correct", correct)
        with col3:
            st.metric("🟡 Partial", partial)
        with col4:
            st.metric("❌ Wrong", wrong)
        with col5:
            st.metric("🚨 Hallucinated", hallucinated)

        # Score bar
        score_pct = avg_score / 10
        if score_pct >= 0.8:
            bar_color = "normal"
        elif score_pct >= 0.5:
            bar_color = "off"
        else:
            bar_color = "inverse"

        st.progress(score_pct)
        st.markdown("---")

        # ── Detailed results ──
        st.subheader("Detailed Results")

        for i, r in enumerate(results):
            icon = VERDICT_ICONS.get(r["verdict"], "❓")
            color = VERDICT_COLORS.get(r["verdict"], "#888888")

            with st.expander(
                f"{icon}  Q: {r['question']} — Score: {r['score']}/10"
            ):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Type:** `{r['type']}`")
                    st.markdown(f"**Expected:** {r['expected']}")

                with col2:
                    st.markdown(
                        f"**Verdict:** "
                        f"<span style='color:{color};font-weight:bold'>"
                        f"{r['verdict']}</span>",
                        unsafe_allow_html=True
                    )
                    st.markdown(f"**Score:** {r['score']}/10")

                st.markdown(f"**Actual:** {r['actual']}")
                st.markdown(f"**Reason:** _{r['reason']}_")

        # ── Download results ──
        import pandas as pd
        df = pd.DataFrame(results)[["question","type","expected","actual","verdict","score","reason"]]
        st.download_button(
            "Download Evaluation Report (CSV)",
            data=df.to_csv(index=False),
            file_name="rag_evaluation.csv",
            mime="text/csv"
        )

    elif st.session_state.eval_chunks:
        st.info("Click 'Run Full Evaluation' to start.")
    else:
        st.info("Upload a document above to enable evaluation.")