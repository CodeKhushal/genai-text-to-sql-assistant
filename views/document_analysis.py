import streamlit as st
from pypdf import PdfReader
from docx import Document
import tempfile
import os

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
        text += para.text + "\n"
    return text

def ask_via_text(document_text, question, client, model_name):

    MAX_CHARS = 30000
    truncated = False

    if len(document_text) > MAX_CHARS:
        document_text = document_text[:MAX_CHARS]
        truncated = True

    prompt = f"""
Context:
You are a document analysis assistant.

Role:
Act as an expert document analyst.

Task:
Answer the user's question ONLY using the provided document content.

Constraints:
- Do not hallucinate
- If the answer is not present in the document, say exactly:
  "The answer is not available in the document."
- Keep response concise and accurate

Document Content:
{document_text}

User Question:
{question}
"""

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text.strip(), None, truncated
    except Exception as e:
        return None, str(e), truncated

# ── DIRECT FILE UPLOAD APPROACH ───────────────────────────────────────────────

def ask_via_file_upload(uploaded_file, question, client, model_name):
    """
    Saves the uploaded file to a temp location,
    uploads it directly to Gemini File API,
    and asks the question with the file as context.
    Best for: scanned PDFs, image-heavy docs, large documents.
    """

    try:
        # Save uploaded file to a temporary file on disk
        # Gemini File API needs a real file path — not a buffer
        suffix = ".pdf" if uploaded_file.name.endswith(".pdf") else ".docx"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        # Upload file to Gemini
        gemini_file = client.files.upload(file=tmp_path)

        # Clean up temp file
        os.unlink(tmp_path)

        prompt = f"""
Context:
You are a document analysis assistant.

Role:
Act as an expert document analyst.

Task:
Answer the user's question ONLY using the provided document content.

Constraints:
- Do not hallucinate
- If the answer is not present in the document, say exactly:
  "The answer is not available in the document."
- Keep response concise and accurate

User Question:
{question}
"""

        # Pass file object + prompt together
        response = client.models.generate_content(
            model=model_name,
            contents=[gemini_file, prompt]
        )

        # Reset file pointer for potential re-use
        uploaded_file.seek(0)

        return response.text.strip(), None

    except Exception as e:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return None, str(e)

def show(client, model_name):
    st.title("📄 Document Analysis")
    st.write("Upload a PDF or Word document and ask questions about it.")
    st.markdown("---")

    # Session state
    if "doc_text" not in st.session_state:
        st.session_state.doc_text = None
    if "doc_name" not in st.session_state:
        st.session_state.doc_name = None
    if "doc_qa_history" not in st.session_state:
        st.session_state.doc_qa_history = []
    if "doc_truncated" not in st.session_state:
        st.session_state.doc_truncated = False

    # ── Approach selector ──
    st.subheader("Analysis Mode")
    approach = st.radio(
        "Choose how the document is sent to AI:",
        options=[
            "Text Extraction  -  Fast, works for most documents",
            "Direct File Upload  -  Better for scanned or image-heavy PDFs"
        ]
    )

    use_file_upload = "Direct File Upload" in approach

    if use_file_upload:
        st.info("Direct File Upload mode: The file is sent directly to Gemini. Works better for scanned PDFs and documents with images or tables.")
    else:
        st.info("Text Extraction mode: Text is extracted locally and passed to Gemini. Fast and efficient for standard text-based documents.")

    st.markdown("---")

    # ── File uploader ──
    uploaded_file = st.file_uploader(
        "Upload PDF or Word document",
        type=["pdf", "docx"]
    )

    if uploaded_file:

        # Reset session if a new file is uploaded
        if uploaded_file.name != st.session_state.doc_name:
            st.session_state.doc_name = uploaded_file.name
            st.session_state.doc_qa_history = []
            st.session_state.doc_truncated = False

            # Only extract text if using text extraction mode
            if not use_file_upload:
                with st.spinner("Reading document..."):
                    if uploaded_file.name.endswith(".pdf"):
                        st.session_state.doc_text = read_pdf(uploaded_file)
                        uploaded_file.seek(0)
                    elif uploaded_file.name.endswith(".docx"):
                        st.session_state.doc_text = read_docx(uploaded_file)
                        uploaded_file.seek(0)

                # Check if text extraction returned anything
                if not st.session_state.doc_text or not st.session_state.doc_text.strip():
                    st.error(
                        "Could not extract text from this document. "
                        "It may be a scanned PDF. Try switching to Direct File Upload mode."
                    )
                    st.session_state.doc_text = None
                    st.stop()
            else:
                st.session_state.doc_text = None

        st.success(f"Document loaded: {uploaded_file.name}")

        # Preview — only available in text extraction mode
        if not use_file_upload and st.session_state.doc_text:
            with st.expander("Preview extracted text"):
                preview = st.session_state.doc_text
                if len(preview) > 2000:
                    st.text(preview[:2000] + "\n\n... (truncated for preview)")
                else:
                    st.text(preview)

                if st.session_state.doc_truncated:
                    st.warning(
                        "Document exceeds 30,000 characters. "
                        "Only the first 30,000 characters will be analysed."
                    )

        st.markdown("---")

        # ── Question input ──
        question = st.text_input("Ask a question about the document:")

        if st.button("Get Answer"):
            if not question.strip():
                st.warning("Please enter a question.")

            else:
                with st.spinner("Analysing document..."):

                    if use_file_upload:
                        # Direct file upload approach
                        uploaded_file.seek(0)
                        answer, error = ask_via_file_upload(
                            uploaded_file,
                            question, client, model_name
                        )
                        truncated = False

                    else:
                        # Text extraction approach
                        answer, error, truncated = ask_via_text(
                            st.session_state.doc_text,
                            question, client, model_name
                        )
                        st.session_state.doc_truncated = truncated

                if error:
                    st.error(f"Error: {error}")
                else:
                    st.session_state.doc_qa_history.append({
                        "question": question,
                        "answer": answer,
                        "mode": "File Upload" if use_file_upload else "Text Extraction"
                    })

        # ── Q&A History ──
        if st.session_state.doc_qa_history:
            st.markdown("---")
            st.subheader("Q&A History")
            for item in reversed(st.session_state.doc_qa_history):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"**Q: {item['question']}**")
                with col2:
                    st.caption(f"via {item['mode']}")
                st.info(item["answer"])
                st.divider()

        # ── Clear history button ──
        if st.session_state.doc_qa_history:
            if st.button("Clear Q&A History"):
                st.session_state.doc_qa_history = []
                st.rerun()