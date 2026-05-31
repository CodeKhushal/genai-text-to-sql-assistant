import streamlit as st
import google.genai as genai
import json


def analyse_activity(activity_text, client, model_name):
    prompt = f"""
Context:
You are analyzing e-commerce user activity logs.

Role:
Act as a senior data analyst.

Task:
1. Summarize the user activity
2. Extract structured insights

Constraints:
- Return ONLY valid JSON
- Do not include markdown formatting
- Do not add extra explanations

Format:
{{
  "summary": "...",
  "total_users": 0,
  "purchasing_users": 0,
  "total_revenue": 0,
  "insights": [
    "...",
    "..."
  ]
}}

Input Data:
{activity_text}
"""
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        text = response.text.strip()
        text = text.replace("```json","").replace("```","").strip()
        return json.loads(text), None
    except Exception as e:
        return None, str(e)


def show(client, model_name):
    st.title("📊 Activity Analysis")
    st.write("Paste user activity logs and extract structured AI insights.")
    st.markdown("---")

    default_activity = """User activity:
- User A logged in and purchased a laptop worth $1200
- User B logged in but did not make any purchase
- User C purchased a phone worth $800"""

    activity_input = st.text_area(
        "Enter user activity logs:",
        value=default_activity,
        height=200
    )

    if st.button("Analyse Activity"):
        if not activity_input.strip():
            st.warning("Please enter some activity data.")
        else:
            with st.spinner("Analysing with AI..."):
                result, error = analyse_activity(activity_input ,client, model_name)

            if error:
                st.error(f"Error: {error}")
            elif result:
                st.markdown("---")

                # KPI Cards
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Users", result.get("total_users", 0))
                with col2:
                    st.metric("Purchasing Users", result.get("purchasing_users", 0))
                with col3:
                    st.metric("Total Revenue", f"${result.get('total_revenue', 0):,}")

                st.subheader("Summary")
                st.info(result.get("summary", ""))

                st.subheader("Insights")
                for insight in result.get("insights", []):
                    st.write(f"• {insight}")

                st.subheader("Raw JSON Output")
                st.json(result)