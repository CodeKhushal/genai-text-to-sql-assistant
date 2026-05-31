import streamlit as st
from google import genai
from pypdf import PdfReader
from docx import Document

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

def ask_document(document_text, question, client, model_name):
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
        return response.text.strip(), None
    except Exception as e:
        return None, str(e)


def show(client, model_name):
    st.title("📄 Document Analysis")
    st.write("Upload a PDF or Word document and ask questions about it.")
    st.markdown("---")

    # Session state for document
    if "doc_text" not in st.session_state:
        st.session_state.doc_text = None
    if "doc_name" not in st.session_state:
        st.session_state.doc_name = None
    if "doc_qa_history" not in st.session_state:
        st.session_state.doc_qa_history = []

    uploaded_file = st.file_uploader(
        "Upload PDF or Word document",
        type=["pdf", "docx"]
    )

    if uploaded_file:
        if uploaded_file.name != st.session_state.doc_name:
            with st.spinner("Reading document..."):
                if uploaded_file.name.endswith(".pdf"):
                    st.session_state.doc_text = read_pdf(uploaded_file)
                elif uploaded_file.name.endswith(".docx"):
                    st.session_state.doc_text = read_docx(uploaded_file)
                st.session_state.doc_name = uploaded_file.name
                st.session_state.doc_qa_history = []

        st.success(f"Document loaded: {uploaded_file.name}")

        with st.expander("Preview document text"):
            st.text(st.session_state.doc_text[:2000] + "..." if len(st.session_state.doc_text) > 2000 else st.session_state.doc_text)

        st.markdown("---")
        question = st.text_input("Ask a question about the document:")

        if st.button("Get Answer"):
            if not question.strip():
                st.warning("Please enter a question.")
            else:
                with st.spinner("Analysing document..."):
                    answer, error = ask_document(
                        st.session_state.doc_text,
                        question, client, model_name
                    )

                if error:
                    st.error(f"Error: {error}")
                else:
                    st.session_state.doc_qa_history.append({
                        "question": question,
                        "answer": answer
                    })

        # Show Q&A history
        if st.session_state.doc_qa_history:
            st.markdown("---")
            st.subheader("Q&A History")
            for item in reversed(st.session_state.doc_qa_history):
                st.write(f"**Q: {item['question']}**")
                st.info(item["answer"])
                st.divider()