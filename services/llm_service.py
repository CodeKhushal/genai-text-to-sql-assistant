from google import genai
from dotenv import load_dotenv
import os
import time


load_dotenv()
model_name=os.getenv("MODEL")

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
)


# GENERATE SQL USING GEMINI
def generate_sql_query(prompt):

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

    return None


def get_sql_confidence(sql_query, user_question):
    
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

Format:
{{"confidence": 85, "reason": "one sentence reason"}}
"""
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        import json
        text = response.text.strip().replace("```json","").replace("```","")
        return json.loads(text)
    
    except:
        return {"confidence": 0, "reason": "Could not assess confidence"}