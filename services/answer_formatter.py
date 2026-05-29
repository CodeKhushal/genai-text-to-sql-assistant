# services/answer_formatter.py

from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
model_name=os.getenv("MODEL")

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
)

def format_answer_naturally(user_question, sql_results):
    
    if not sql_results:
        return "No results found for your question."
    
    prompt = f"""
Context:
You are a business intelligence assistant presenting data results to a non-technical user.

Role:
Act as a friendly data analyst explaining query results in plain English.

Task:
Convert the SQL query results into a clear, natural language answer to the user's question.

User Question: {user_question}

Query Results: {sql_results}

Constraints:
- Answer in 1-3 sentences only
- Use actual numbers from the results
- Do not mention SQL or databases
- Be conversational and clear

Format:
Plain text answer only. No bullet points.
"""
    
    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )
    
    return response.text.strip()