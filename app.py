import streamlit as st
from google import genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

model_name = os.getenv("MODEL")

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# Page Config
st.set_page_config(
    page_title="AI Data Assistant",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for navigation-style buttons
st.markdown("""
<style>
/* Only sidebar buttons */
[data-testid="stSidebar"] .stButton {
    width: 100%;
}

[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;

    display: flex !important;
    justify-content: flex-start !important;
    align-items: center !important;

    padding: 8px 12px !important;
    margin: 0 !important;
}

[data-testid="stSidebar"] .stButton > button div {
    width: 100% !important;
    display: flex !important;
    justify-content: flex-start !important;
    text-align: left !important;
}

[data-testid="stSidebar"] .stButton > button p {
    margin: 0 !important;
    text-align: left !important;
    width: 100% !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.08) !important;
    border-radius: 6px;
}
</style>
""", unsafe_allow_html=True)

# Initialize page state
if "page" not in st.session_state:
    st.session_state.page = "🏠 Dashboard"

# Sidebar Navigation
with st.sidebar:
    st.title("🤖 AI Data Assistant")
    st.markdown("---")

    if st.button("Dashboard", use_container_width=True):
        st.session_state.page = "🏠 Dashboard"

    if st.button("Prompt Optimisation", use_container_width=True):
        st.session_state.page = "✨ Prompt Optimisation"

    if st.button("Activity Analysis", use_container_width=True):
        st.session_state.page = "📊 Activity Analysis"

    if st.button("Data Augmentation", use_container_width=True):
        st.session_state.page = "🔄 Data Augmentation"

    if st.button("Document Analysis", use_container_width=True):
        st.session_state.page = "📄 Document Analysis"

    if st.button("Text to SQL", use_container_width=True):
        st.session_state.page = "🗄️ Text to SQL"

    if st.button("RAG System", use_container_width=True):
        st.session_state.page = "🔍 RAG System"

    if st.button("RAG Evaluation", use_container_width=True):
        st.session_state.page = "📊 RAG Evaluation"

# Current Page
page = st.session_state.page

# Page Routing
if page == "🏠 Dashboard":
    from views.dashboard import show
    show()

elif page == "✨ Prompt Optimisation":
    from views.prompt_optimization import show
    show(client, model_name)

elif page == "📊 Activity Analysis":
    from views.activity_analysis import show
    show(client, model_name)

elif page == "🔄 Data Augmentation":
    from views.data_augmentation import show
    show(client, model_name)

elif page == "📄 Document Analysis":
    from views.document_analysis import show
    show(client, model_name)

elif page == "🗄️ Text to SQL":
    from views.text_to_sql import show
    show(client, model_name)

# Add to routing
elif page == "🔍 RAG System":
    from views.rag_system import show
    show(client, model_name)

elif page == "📊 RAG Evaluation":
    from views.rag_evaluation import show
    show(client, model_name)