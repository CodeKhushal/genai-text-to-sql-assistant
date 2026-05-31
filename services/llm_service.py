import time

# GENERATE SQL USING GEMINI
def generate_sql_query(prompt, client, model_name):

    max_retries = 3

    for attempt in range(max_retries):

        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )

            generated_sql = response.text.strip()

            generated_sql = generated_sql.replace("```sql", "")
            generated_sql = generated_sql.replace("```", "")
            generated_sql = generated_sql.strip()

            return generated_sql

        except Exception as e:

            print(f"\nAttempt {attempt + 1} failed:")
            print(e)

            time.sleep(5)

    return "Could not generate a response."


def get_sql_confidence(sql_query, user_question, client, model_name):
    
    prompt = f"""
Context:
You are a SQL quality reviewer.

Role:
Act as a senior SQL code reviewer.

Task:
Rate the confidence that this SQL query correctly answers the user's question.

User Question: {user_question}
Generated SQL: {sql_query}

Constraints:
- Return ONLY a JSON object
- No explanation
- No markdown
- No extra text before or after

Format:
{{"confidence": 85, "reason": "one sentence reason"}}
"""
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        import json
        text = response.text.strip().replace("```json","").replace("```","").strip()
        # Find the JSON object within the response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end != 0:
            text = text[start:end]
        return json.loads(text)
    
    except Exception as e:
        print(f"Confidence check failed: {e}")
        return {"confidence": 0, "reason": "Could not assess confidence"}