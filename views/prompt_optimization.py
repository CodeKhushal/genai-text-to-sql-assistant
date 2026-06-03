import streamlit as st
import json

# ── PRESET TEMPLATES ──────────────────────────────────────────────────────────

PRESETS = {
    "Custom (blank)": {
        "context": "",
        "role": "",
        "task": "",
        "constraints": "",
        "format": "",
        "examples": ""
    },
    "SQL Query Optimisation": {
        "context": (
            "I am a data engineer working on a Snowflake data warehouse.\n"
            "The fact table `sales_fact` has 2 billion rows partitioned by `sale_date`.\n"
            "The following query is scanning all partitions and taking too long to run "
            "and causing high warehouse compute costs:\n\n"
            "    SELECT\n"
            "        c.region,\n"
            "        p.category,\n"
            "        SUM(s.revenue)   AS total_revenue,\n"
            "        COUNT(s.sale_id) AS total_orders\n"
            "    FROM sales_fact s\n"
            "    JOIN customers   c ON s.customer_id = c.customer_id\n"
            "    JOIN products    p ON s.product_id  = p.product_id\n"
            "    WHERE s.sale_date BETWEEN '2023-01-01' AND '2023-12-31'\n"
            "    GROUP BY c.region, p.category\n"
            "    ORDER BY total_revenue DESC;"
        ),
        "role": (
            "Act as a senior Snowflake data warehouse performance engineer "
            "with 10+ years of experience in query optimisation and cost reduction."
        ),
        "task": (
            "Analyse the SQL query above and rewrite it so it runs in under 5 minutes. "
            "Explain every change you make and WHY it improves performance."
        ),
        "constraints": (
            "• Improvements must be specific to Snowflake (clustering keys, result cache, "
            "materialized views, warehouse sizing).\n"
            "• Do NOT change the business logic or the output columns/ordering.\n"
            "• Suggest at most 3 alternative approaches ranked by implementation effort."
        ),
        "format": (
            "1. List of identified performance problems (bullet points).\n"
            "2. Optimised SQL query (code block).\n"
            "3. Explanation of each change made.\n"
            "4. Alternative approaches ranked by effort (low → high)."
        ),
        "examples": (
            "Problem  : Full table scan due to missing clustering key on sale_date.\n"
            "Fix      : ALTER TABLE sales_fact CLUSTER BY (sale_date);"
        )
    },
    "ELT Pipeline Design": {
        "context": (
            "I am building an ELT pipeline on Azure Databricks. "
            "Raw CSV files land daily in ADLS Gen2 under /raw/sales/. "
            "I need to load them into Bronze, clean in Silver, and aggregate in Gold (Delta Lake)."
        ),
        "role": (
            "Act as a senior data engineer specialising in Azure Databricks "
            "and medallion architecture with 8+ years of experience."
        ),
        "task": (
            "Design a production-ready ELT pipeline from raw CSV ingestion "
            "to Gold Delta table aggregations including error handling and logging."
        ),
        "constraints": (
            "• Use PySpark and Delta Lake only — no external orchestration tools.\n"
            "• Include data quality checks at the Silver layer.\n"
            "• Pipeline must be idempotent — safe to rerun without duplicates.\n"
            "• Include schema drift handling."
        ),
        "format": (
            "1. Architecture diagram description (text).\n"
            "2. Bronze layer PySpark code.\n"
            "3. Silver layer PySpark code with quality checks.\n"
            "4. Gold layer aggregation code.\n"
            "5. Error handling and logging strategy."
        ),
        "examples": (
            "Bronze: df.write.mode('append').format('delta').saveAsTable('bronze_sales')\n"
            "Silver: df.dropDuplicates(['order_id']).filter(col('amount') > 0)"
        )
    },
    "Data Quality Check Generation": {
        "context": (
            "I have a Silver layer Delta table called `silver_orders` with columns:\n"
            "order_id (INT), customer_id (INT), product (STRING), "
            "amount (DECIMAL), order_date (DATE), status (STRING).\n"
            "I need to define data quality rules before data flows to Gold."
        ),
        "role": (
            "Act as a senior data quality engineer experienced in "
            "Great Expectations and PySpark validation frameworks."
        ),
        "task": (
            "Generate comprehensive data quality checks for the `silver_orders` table "
            "covering all critical columns and business rules."
        ),
        "constraints": (
            "• Use both PySpark native checks and pandas-based assertions.\n"
            "• Cover: nulls, uniqueness, value ranges, referential integrity, date validity.\n"
            "• Each check must include what happens on failure — stop pipeline or log and continue.\n"
            "• Maximum 10 checks total."
        ),
        "format": (
            "1. Check name.\n"
            "2. Column(s) checked.\n"
            "3. Python/PySpark code for the check.\n"
            "4. Failure action (STOP or LOG).\n"
            "5. Business reason for the check."
        ),
        "examples": (
            "Check    : No null order_ids\n"
            "Code     : assert df.filter(col('order_id').isNull()).count() == 0\n"
            "On fail  : STOP — order_id is the primary key"
        )
    }
}


# ── PROMPT BUILDER ────────────────────────────────────────────────────────────

def build_prompt(context, role, task, constraints, format_str, examples):
    sections = []

    if context.strip():
        sections.append(f"CONTEXT:\n{context.strip()}")
    if role.strip():
        sections.append(f"ROLE:\n{role.strip()}")
    if task.strip():
        sections.append(f"TASK:\n{task.strip()}")
    if constraints.strip():
        sections.append(f"CONSTRAINTS:\n{constraints.strip()}")
    if format_str.strip():
        sections.append(f"FORMAT:\n{format_str.strip()}")
    if examples.strip():
        sections.append(f"EXAMPLES:\n{examples.strip()}")

    return "\n\n".join(sections)


# ── LLM CALLS ─────────────────────────────────────────────────────────────────

def optimise_prompt(raw_prompt, client, model_name):
    """Ask LLM to improve the prompt and explain what was changed."""

    meta_prompt = f"""
Context:
You are a world-class prompt engineering expert specialising in data engineering prompts for LLMs.

Role:
Act as a senior prompt engineer who improves prompts for clarity, specificity, and output quality.

Task:
Analyse the prompt below and return an improved version that will produce better, more accurate,
and more structured LLM responses. Then explain every change you made and why.

Input Prompt:
{raw_prompt}

Constraints:
- Preserve the original intent and all key information
- Do NOT remove any domain-specific details
- Improve clarity, specificity, and structure
- Add any missing elements that would improve output quality
- Return ONLY valid JSON — no markdown, no code blocks

Format:
{{
  "optimised_prompt": "the full improved prompt here",
  "changes": [
    {{"change": "what was changed", "reason": "why this improves the prompt"}},
    {{"change": "what was changed", "reason": "why this improves the prompt"}}
  ],
  "quality_score_before": 6,
  "quality_score_after": 9,
  "summary": "one sentence describing the main improvement"
}}
"""

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=meta_prompt
        )
        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end != 0:
            text = text[start:end]
        return json.loads(text), None
    except Exception as e:
        return None, str(e)


def execute_prompt(prompt, client, model_name):
    """Run the prompt through the LLM and return the response."""
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text.strip(), None
    except Exception as e:
        return None, str(e)


# ── PAGE ──────────────────────────────────────────────────────────────────────

def show(client, model_name):

    # ── Session state ──
    if "po_optimised" not in st.session_state:
        st.session_state.po_optimised = None
    if "po_changes" not in st.session_state:
        st.session_state.po_changes = []
    if "po_scores" not in st.session_state:
        st.session_state.po_scores = {}
    if "po_original_prompt" not in st.session_state:
        st.session_state.po_original_prompt = None
    if "po_original_response" not in st.session_state:
        st.session_state.po_original_response = None
    if "po_optimised_response" not in st.session_state:
        st.session_state.po_optimised_response = None
    if "po_preset" not in st.session_state:
        st.session_state.po_preset = "Custom (blank)"

    st.title("✨ Prompt Optimisation")
    st.write(
        "Build a structured prompt using the 6 key components, "
        "then let AI optimise it and compare the results."
    )
    st.markdown("---")

    # ── Preset selector ──
    selected_preset = st.selectbox(
        "Start from a template or build from scratch:",
        options=list(PRESETS.keys()),
        index=list(PRESETS.keys()).index(st.session_state.po_preset)
    )

    if selected_preset != st.session_state.po_preset:
        st.session_state.po_preset = selected_preset
        # Clear previous results when preset changes
        st.session_state.po_optimised = None
        st.session_state.po_changes = []
        st.session_state.po_scores = {}
        st.session_state.po_original_response = None
        st.session_state.po_optimised_response = None
        st.rerun()

    preset = PRESETS[selected_preset]
    st.markdown("---")

    # ── Prompt builder form ──
    st.subheader("🛠️ Build Your Prompt")
    st.caption("Fill in the components below. All fields except Context are optional but improve quality.")

    context = st.text_area(
        "📌 Context — background situation and data description",
        value=preset["context"],
        height=160,
        placeholder="Describe your data environment, table sizes, current problem..."
    )

    col1, col2 = st.columns(2)

    with col1:
        role = st.text_area(
            "👤 Role — expert persona for the LLM",
            value=preset["role"],
            height=100,
            placeholder="Act as a senior data engineer with 10 years experience..."
        )

        constraints = st.text_area(
            "⚠️ Constraints — rules the LLM must follow",
            value=preset["constraints"],
            height=120,
            placeholder="• Do not change business logic\n• Use Snowflake-specific syntax only\n• Limit response to 3 suggestions..."
        )

        examples = st.text_area(
            "💡 Examples — sample input/output pairs (optional)",
            value=preset["examples"],
            height=100,
            placeholder="Input : slow query\nExpected output : optimised query with explanation..."
        )

    with col2:
        task = st.text_area(
            "🎯 Task — specific action the LLM must perform",
            value=preset["task"],
            height=100,
            placeholder="Analyse the query above and rewrite it for performance..."
        )

        format_str = st.text_area(
            "📋 Format — expected output structure",
            value=preset["format"],
            height=120,
            placeholder="1. Problem list\n2. Optimised query (code block)\n3. Explanation of changes..."
        )

    st.markdown("---")

    # ── Preview assembled prompt ──
    assembled = build_prompt(context, role, task, constraints, format_str, examples)

    with st.expander("👁️ Preview assembled prompt", expanded=False):
        st.code(assembled, language="text")
        st.caption(f"Prompt length: {len(assembled)} characters | ~{len(assembled.split())} words")

    # ── Action buttons ──
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        optimise_btn = st.button(
            "✨ Optimise Prompt",
            type="primary",
            use_container_width=True,
            help="Send your prompt to AI for improvement suggestions"
        )

    with col_b:
        run_original_btn = st.button(
            "▶ Run Original",
            use_container_width=True,
            help="Execute your original prompt as-is"
        )

    with col_c:
        run_optimised_btn = st.button(
            "🚀 Run Optimised",
            use_container_width=True,
            disabled=(st.session_state.po_optimised is None),
            help="Execute the AI-optimised version"
        )

    if not assembled.strip():
        st.warning("Please fill in at least the Context field before proceeding.")
        return

    # ── Optimise prompt ──
    if optimise_btn:
        with st.spinner("Analysing and optimising your prompt..."):
            result, error = optimise_prompt(assembled, client, model_name)

        if error:
            st.error(f"Optimisation failed: {error}")
        elif result:
            st.session_state.po_original_prompt = assembled
            st.session_state.po_optimised = result.get("optimised_prompt", "")
            st.session_state.po_changes = result.get("changes", [])
            st.session_state.po_scores = {
                "before": result.get("quality_score_before", 0),
                "after": result.get("quality_score_after", 0),
                "summary": result.get("summary", "")
            }
            st.session_state.po_original_response = None
            st.session_state.po_optimised_response = None

    # ── Run original ──
    if run_original_btn:
        with st.spinner("Running original prompt..."):
            resp, error = execute_prompt(assembled, client, model_name)
        if error:
            st.error(f"Error: {error}")
        else:
            st.session_state.po_original_response = resp

    # ── Run optimised ──
    if run_optimised_btn and st.session_state.po_optimised:
        with st.spinner("Running optimised prompt..."):
            resp, error = execute_prompt(
                st.session_state.po_optimised, client, model_name
            )
        if error:
            st.error(f"Error: {error}")
        else:
            st.session_state.po_optimised_response = resp

    # ── Show optimisation results ──
    if st.session_state.po_optimised:
        st.markdown("---")
        st.subheader("✨ Optimisation Results")

        # Quality score improvement
        scores = st.session_state.po_scores
        if scores:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Quality Before",
                    f"{scores.get('before', 0)}/10"
                )
            with col2:
                delta = scores.get("after", 0) - scores.get("before", 0)
                st.metric(
                    "Quality After",
                    f"{scores.get('after', 0)}/10",
                    delta=f"+{delta}" if delta > 0 else str(delta)
                )
            with col3:
                st.metric(
                    "Improvement",
                    f"+{delta} points" if delta > 0 else "No change"
                )

            if scores.get("summary"):
                st.info(f"**Key improvement:** {scores['summary']}")

        # What changed
        if st.session_state.po_changes:
            st.subheader("📝 Changes Made")
            for i, change in enumerate(st.session_state.po_changes):
                with st.expander(
                    f"Change {i+1}: {change.get('change', '')[:70]}...",
                    expanded=(i == 0)
                ):
                    st.write(f"**What:** {change.get('change', '')}")
                    st.write(f"**Why:** {change.get('reason', '')}")

        # Side by side comparison
        st.subheader("📊 Side by Side Comparison")
        col_orig, col_opt = st.columns(2)

        with col_orig:
            st.markdown("**Original Prompt**")
            st.text_area(
                label="original",
                value=st.session_state.po_original_prompt or assembled,
                height=300,
                disabled=True,
                label_visibility="collapsed"
            )

        with col_opt:
            st.markdown("**Optimised Prompt**")
            optimised_editable = st.text_area(
                label="optimised",
                value=st.session_state.po_optimised,
                height=300,
                label_visibility="collapsed",
                key="optimised_editable"
            )
            # Allow user to edit the optimised prompt before running
            st.session_state.po_optimised = optimised_editable

        # Copy button
        st.download_button(
            "📋 Download Optimised Prompt",
            data=st.session_state.po_optimised,
            file_name="optimised_prompt.txt",
            mime="text/plain"
        )

    # ── Response comparison ──
    if st.session_state.po_original_response or st.session_state.po_optimised_response:
        st.markdown("---")
        st.subheader("🔁 Response Comparison")

        col_r1, col_r2 = st.columns(2)

        with col_r1:
            st.markdown("**Original Prompt Response**")
            if st.session_state.po_original_response:
                st.markdown(
                    f"<div style='background:#1e1e1e;padding:16px;border-radius:8px;"
                    f"border:1px solid #333;font-size:13px;line-height:1.6;max-height:500px;"
                    f"overflow-y:auto'>{st.session_state.po_original_response}</div>",
                    unsafe_allow_html=True
                )
            else:
                st.info("Click 'Run Original' to see response.")

        with col_r2:
            st.markdown("**Optimised Prompt Response**")
            if st.session_state.po_optimised_response:
                st.markdown(
                    f"<div style='background:#1a2e1a;padding:16px;border-radius:8px;"
                    f"border:1px solid #2d5a2d;font-size:13px;line-height:1.6;max-height:500px;"
                    f"overflow-y:auto'>{st.session_state.po_optimised_response}</div>",
                    unsafe_allow_html=True
                )
            else:
                st.info(
                    "Optimise a prompt first, then click 'Run Optimised'."
                    if not st.session_state.po_optimised
                    else "Click 'Run Optimised' to see response."
                )