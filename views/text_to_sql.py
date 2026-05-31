import streamlit as st
from datetime import datetime
import pandas as pd
import altair as alt

from prompts.sql_prompt import generate_sql_prompt
from services.llm_service import generate_sql_query, get_sql_confidence
from services.sql_validator import validate_sql_query
from services.sql_executor import execute_sql_query
from services.answer_formatter import format_answer_naturally

def show(client, model_name):
    # Session state
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
    if "followups" not in st.session_state:
        st.session_state.followups = []

    # History in sidebar
    with st.sidebar:
        st.markdown("---")
        st.subheader("Query History")
        if st.session_state.query_history:
            for item in reversed(st.session_state.query_history[-5:]):
                st.caption(f"{item['timestamp']} — {item['question'][:40]}...")
                st.code(item['sql'], language="sql")
                st.write(f"Rows returned: {item['row_count']}")
                st.divider()
        else:
            st.info("No queries yet.")

    def is_safe_request(q):
        blocked = ["insert","delete","update","drop","create","alter","truncate"]
        return not any(w in q.lower() for w in blocked)

    st.title("🗄️ Text to SQL")
    st.write("Ask business questions in natural language.")
    with st.expander("Available Tables & Example Questions"):
        st.markdown("""
### Customer
- customer_id
- name
- email
- join_date

### Sales
- sale_id
- customer_id
- product
- amount
- sale_date

### Example Questions
- Show all customers
- Total sales by product
- Top customers by revenue
- Average sale amount
- Sales in the last month
- Highest selling product
""")
    st.markdown("---")

    user_question = st.text_input("Enter your business question:")

    if st.button("Generate SQL Query"):
        if not user_question:
            st.warning("Please enter a question.")
        elif not is_safe_request(user_question):
            st.error("Only read-only analytical questions are allowed.")
        else:
            prompt = generate_sql_prompt(user_question)
            generated_sql = generate_sql_query(prompt, client, model_name)

            if not generated_sql:
                st.error("Failed to generate SQL query.")
            else:
                is_valid, _ = validate_sql_query(generated_sql)
                if not is_valid:
                    st.error("Unsafe SQL query blocked.")
                else:
                    execution_result = execute_sql_query(generated_sql)

                    explain_prompt = f"""
Context: You are explaining a SQL query to a non-technical business user.
Role: Act as a patient SQL teacher.
Task: Explain what this SQL query does in plain English.
SQL Query: {generated_sql}
Constraints:
- No technical jargon
- Maximum 3 bullet points
- Focus on what business question it answers
Format: Bullet points only
"""
                    explanation = generate_sql_query(explain_prompt, client, model_name)

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

    # Display area
    if st.session_state.last_sql:

        st.subheader("Generated SQL")
        st.code(st.session_state.last_sql, language="sql")

        st.subheader("SQL Query Explained")
        st.info(st.session_state.explanation)

        confidence = get_sql_confidence(
            st.session_state.last_sql,
            st.session_state.last_question, client, model_name
        )
        score = confidence["confidence"]
        if score >= 80:
            st.success(f"Confidence: {score}% — {confidence['reason']}")
        elif score >= 50:
            st.warning(f"Confidence: {score}% — {confidence['reason']}")
        else:
            st.error(f"Low Confidence: {score}% — {confidence['reason']}")

        execution_result = st.session_state.last_results

        if execution_result["success"]:
            if execution_result["data"]:
                st.subheader("Query Results")
                st.json(execution_result["data"])

                natural_answer = format_answer_naturally(
                    st.session_state.last_question,
                    execution_result["data"], client, model_name
                )
                st.subheader("Query Result Explained")
                st.success(natural_answer)

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

                # Download results
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download Results as CSV",
                    data=csv,
                    file_name="query_results.csv",
                    mime="text/csv"
                )

            else:
                st.info("No results found.")
        else:
            st.error(execution_result["message"])