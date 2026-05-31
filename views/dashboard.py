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

    with col2:
        st.subheader("📄 Document Analysis")
        st.write("Upload a PDF or Word document and ask questions. AI answers based only on the document.")

        st.subheader("🗄️ Text to SQL")
        st.write("Ask business questions in natural language. AI generates and executes SQL queries on your database.")

    st.markdown("---")
    st.info("Use the sidebar to navigate between services.")