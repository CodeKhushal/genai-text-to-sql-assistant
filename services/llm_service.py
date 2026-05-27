from google import genai
from dotenv import load_dotenv
import os
import time


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# GENERATE SQL USING GEMINI
def generate_sql_query(prompt):

    max_retries = 3

    for attempt in range(max_retries):

        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash",
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