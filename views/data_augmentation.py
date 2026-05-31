import streamlit as st
from google import genai
import pandas as pd
import json

def generate_synthetic_data(sample_data, num_records, client, model_name):
    prompt = f"""
Context:
You are generating synthetic sales data for testing a retail analytics pipeline.

Role:
Act as a senior data generation specialist.

Task:
Generate {num_records} new realistic sales records similar to the provided dataset.

Constraints:
- Return ONLY valid JSON array
- Do not use markdown
- Do not add explanations
- Maintain the exact same column schema
- Generate realistic values
- customer_id should be unique and not duplicate existing ones

Format:
[
  {{
    "column1": value1,
    "column2": value2
  }}
]

Sample Dataset:
{sample_data}
"""
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        text = response.text.strip()
        text = text.replace("```json","").replace("```","").strip()
        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end != 0:
            text = text[start:end]
        return json.loads(text), None
    except Exception as e:
        return None, str(e)


def show(client, model_name):
    st.title("🔄 Data Augmentation")
    st.write("Upload a CSV file and generate synthetic data using AI.")
    st.markdown("---")

    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

    num_records = st.slider("Number of synthetic records to generate", 1, 100, 5)

    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        st.subheader("Original Dataset")
        st.dataframe(df, use_container_width=True)
        st.write(f"Rows: {len(df)} | Columns: {len(df.columns)}")

        if st.button("Generate Synthetic Data"):
            with st.spinner("Generating with AI..."):
                synthetic, error = generate_synthetic_data(
                    df.to_string(index=False),
                    num_records, client, model_name
                )

            if error:
                st.error(f"Error: {error}")
            elif synthetic:
                synthetic_df = pd.DataFrame(synthetic)

                st.subheader("Generated Synthetic Data")
                st.dataframe(synthetic_df, use_container_width=True)

                augmented_df = pd.concat([df, synthetic_df], ignore_index=True)

                st.subheader("Augmented Dataset")
                st.dataframe(augmented_df, use_container_width=True)
                st.write(f"Original: {len(df)} rows → Augmented: {len(augmented_df)} rows")

                # Download button
                csv = augmented_df.to_csv(index=False)
                st.download_button(
                    label="Download Augmented CSV",
                    data=csv,
                    file_name="augmented_data.csv",
                    mime="text/csv"
                )