import streamlit as st
from datetime import datetime
import pandas as pd
import altair as alt

from prompts.sql_prompt import generate_sql_prompt
from services.llm_service import generate_sql_query, get_sql_confidence
from services.sql_validator import validate_sql_query
from services.sql_executor import execute_sql_query
from services.answer_formatter import format_answer_naturally

# ── Session state init ──
if "query_history" not in st.session_state:
    st.session_state.query_history = []
if "last_sql" not in st.session_state:
    st.session_state.last_sql = None
if "last_results" not in st.session_state:
    st.session_state.last_results = None
if "last_question" not in st.session_state:
    st.session_state.last_question = None
if "explanation" not in st.session_state:
    st.session_state.explanation = None

# ── Sidebar history ──
with st.sidebar:
    st.subheader("Query History")
    if st.session_state.query_history:
        for item in reversed(st.session_state.query_history[-5:]):
            st.caption(f"{item['timestamp']} — {item['question'][:40]}...")
            st.code(item['sql'], language="sql")
            st.write(f"Rows returned: {item['row_count']}")
            st.divider()
    else:
        st.info("No queries yet.")

def is_safe_request(user_question):
    blocked_words = ["insert","delete","update","drop","create","alter","truncate"]
    for word in blocked_words:
        if word in user_question.lower():
            return False
    return True

# ── Page ──
st.title("AI Text-to-SQL Assistant")
st.write("Ask business questions in natural language.")

user_question = st.text_input("Enter your business question:")

# ── MAIN BUTTON ──
if st.button("Generate SQL Query"):

    if not user_question:
        st.warning("Please enter a question.")

    elif not is_safe_request(user_question):
        st.error("Only read-only analytical questions are allowed.")

    else:
        prompt = generate_sql_prompt(user_question)
        generated_sql = generate_sql_query(prompt)

        if not generated_sql:
            st.error("Failed to generate SQL query.")

        else:
            is_valid, validation_message = validate_sql_query(generated_sql)

            if not is_valid:
                st.error("Unsafe SQL query blocked.")

            else:
                execution_result = execute_sql_query(generated_sql)

                # Generate explanation immediately alongside SQL generation
                explain_prompt = f"""
Context:
You are explaining a SQL query to a non-technical business user.

Role:
Act as a patient SQL teacher.

Task:
Explain what this SQL query does in plain English.

SQL Query:
{generated_sql}

Constraints:
- No technical jargon
- Maximum 3 bullet points
- Focus on what business question it answers

Format:
Bullet points only
"""
                explanation = generate_sql_query(explain_prompt)

                # Save everything to session state
                st.session_state.last_sql = generated_sql
                st.session_state.last_question = user_question
                st.session_state.last_results = execution_result
                st.session_state.explanation = explanation
                st.session_state.query_history.append({
                    "question": user_question,
                    "sql": generated_sql,
                    "row_count": len(execution_result["data"]),
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })

# ── DISPLAY AREA ──
if st.session_state.last_sql:

    # Generated SQL
    st.subheader("Generated SQL")
    st.code(st.session_state.last_sql, language="sql")

    # SQL Query Explained — automatic, no button
    st.subheader("SQL Query Explained")
    st.info(st.session_state.explanation)

    # Confidence score
    confidence = get_sql_confidence(
        st.session_state.last_sql,
        st.session_state.last_question
    )
    score = confidence["confidence"]
    if score >= 80:
        st.success(f"Confidence: {score}% — {confidence['reason']}")
    elif score >= 50:
        st.warning(f"Confidence: {score}% — {confidence['reason']}")
    else:
        st.error(f"Low Confidence: {score}% — {confidence['reason']}")

    # Results
    execution_result = st.session_state.last_results

    if execution_result["success"]:
        if execution_result["data"]:

            st.subheader("Query Results")
            st.json(execution_result["data"])

            # Natural language answer
            natural_answer = format_answer_naturally(
                st.session_state.last_question,
                execution_result["data"]
            )
            st.subheader("Answer")
            st.success(natural_answer)

            # Auto chart
            df = pd.DataFrame(execution_result["data"])
            numeric_cols = df.select_dtypes(include='number').columns.tolist()
            text_cols = df.select_dtypes(include='object').columns.tolist()

            if len(numeric_cols) >= 1 and len(text_cols) >= 1:
                st.subheader("Auto Chart")
                chart = alt.Chart(df).mark_bar().encode(
                    x=alt.X(text_cols[0], sort='-y'),
                    y=alt.Y(numeric_cols[0]),
                    color=alt.value("#4CAF50")
                ).properties(width=600, height=300)
                st.altair_chart(chart, use_container_width=True)

        else:
            st.info("No results found.")
    else:
        st.error(execution_result["message"])