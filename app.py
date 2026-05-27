import streamlit as st

from prompts.sql_prompt import generate_sql_prompt
from services.llm_service import generate_sql_query
from services.sql_validator import validate_sql_query
from services.sql_executor import execute_sql_query

def is_safe_request(user_question):
 
    blocked_words = [
        "insert",
        "delete",
        "update",
        "drop",
        "create",
        "alter",
        "truncate"
    ]
 
    lower_question = user_question.lower()
 
    for word in blocked_words:
 
        if word in lower_question:
            return False
 
    return True

# PAGE TITLE
st.title("AI Text-to-SQL Assistant")

st.write("Ask business questions in natural language.")


# USER INPUT
user_question = st.text_input(
    "Enter your business question:"
)


# BUTTON
if st.button("Generate SQL Query"):

    if not user_question:
        st.warning("Please enter a question.")

    else:
        if not is_safe_request(user_question):
            st.error(
                "Only read-only analytical questions are allowed."
            )
            st.stop()
        # GENERATE PROMPT
        prompt = generate_sql_prompt(user_question)

    
        # GENERATE SQL
        generated_sql = generate_sql_query(prompt)

        if not generated_sql:
            st.error("Failed to generate SQL query.")

        else:
            # Display generated SQL
            st.subheader("Generated SQL")

            st.code(generated_sql, language="sql")

        
            # VALIDATE SQL
            is_valid, validation_message = validate_sql_query(
                generated_sql
            )

            st.subheader("Validation Result")

            st.write(validation_message)

            # Stop if invalid 
            if not is_valid:
                st.error("Unsafe SQL query blocked.")
            else:
                # EXECUTE SQL
                execution_result = execute_sql_query(
                    generated_sql
                )
            
                # DISPLAY RESULTS
                st.subheader("Query Results")

                if execution_result["success"]:
                    if execution_result["data"]:
                        st.json(execution_result["data"])
                    else:
                        st.info("No results found.")
                else:
                    st.error(execution_result["message"])