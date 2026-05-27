from prompts.sql_prompt import generate_sql_prompt
from services.llm_service import generate_sql_query
from services.sql_validator import validate_sql_query
from services.sql_executor import execute_sql_query


# GET USER QUESTION
user_question = input("\nEnter your business question:\n")


# GENERATE PROMPT
prompt = generate_sql_prompt(user_question)

print("\n==============================")
print("GENERATED PROMPT")
print("==============================\n")

print(prompt)


# GENERATE SQL USING GEMINI
generated_sql = generate_sql_query(prompt)

# Handle LLM failure
if not generated_sql:

    print("\nFailed to generate SQL query.")
    exit()


print("\n==============================")
print("GENERATED SQL")
print("==============================\n")

print(generated_sql)


# VALIDATE SQL
is_valid, validation_message = validate_sql_query(generated_sql)

print("\n==============================")
print("VALIDATION RESULT")
print("==============================\n")

print(validation_message)

# Stop if invalid
if not is_valid:

    print("\nUnsafe SQL query blocked.")
    exit()


# EXECUTE SQL
execution_result = execute_sql_query(generated_sql)


# DISPLAY RESULTS
print("\n==============================")
print("QUERY RESULTS")
print("==============================\n")

if execution_result["success"]:

    print(execution_result["message"])

    if execution_result["data"]:

        for row in execution_result["data"]:
            print(row)

else:

    print("Execution Error:")
    print(execution_result["message"])