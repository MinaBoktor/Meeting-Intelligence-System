import streamlit as st
import pandas as pd
import requests
import json

st.set_page_config(
    page_title="Meeting Intelligence System",
    page_icon="📋",
    layout="wide"
)

API_URL = "http://localhost:8000/extract"

st.title(" Meeting Intelligence System")
st.caption("Autonomous extraction, contextual retrieval, roster validation, and HITL review.")

# --- Session State Initialization ---
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None
if "approved_items" not in st.session_state:
    st.session_state.approved_items = None
if "is_assigned" not in st.session_state:
    st.session_state.is_assigned = False


def read_files(uploaded_files):
    if not uploaded_files:
        return ""
    if isinstance(uploaded_files, list):
        return "\n\n---\n\n".join([f.read().decode("utf-8") for f in uploaded_files])
    return uploaded_files.read().decode("utf-8")


with st.sidebar:
    st.header("1. Ingest Data & Context")

    st.subheader("Required")
    transcripts = st.file_uploader("1. Transcript(s) (TXT/MD) *", type=["txt", "md"], accept_multiple_files=True)

    st.subheader("Optional Knowledge Base")
    history_files = st.file_uploader("2. History Transcripts", type=["txt", "md"], accept_multiple_files=True,
                                     help="Past meetings to give the agent context.")
    general_context = st.file_uploader("3. General Context", type=["txt", "md"], help="Info about teams or roles.")
    roster_file = st.file_uploader("4. Roster (Valid Owners)", type=["txt", "md", "csv"],
                                   help="List of valid employees to validate owners.")
    past_decisions = st.file_uploader("5. Past Decisions", type=["txt", "md"],
                                      help="Previous decisions that might affect current action items.")

    run_extraction = st.button(" Run Intelligence Agent", use_container_width=True, type="primary")

if run_extraction:
    if not transcripts:
        st.warning(" Please upload at least one Transcript to proceed.")
    else:
        payload = {
            "transcript": read_files(transcripts),
            "history": read_files(history_files),
            "context": read_files(general_context),
            "roster": read_files(roster_file),
            "past_decisions": read_files(past_decisions)
        }

        st.header(" Agent Reasoning Stream")

        with st.status("Agent Workflow in Progress...", expanded=True) as status:
            st.write(" **Ingestor Node:** Parsing current transcripts...")
            if payload["roster"]: st.write(" **Context Node:** Loading Roster for owner validation...")
            if payload["history"]: st.write(
                " **Enricher Node:** Indexing History transcripts for semantic retrieval...")

            st.write("⏳ **Extractor Node:** Calling LLM for structured output...")

            try:
                response = requests.post(API_URL, json=payload, timeout=120)
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.extracted_data = data
                    st.session_state.is_assigned = False

                    st.write("**Critic Node:** Validating extracted items against Roster and checking dates...")
                    st.write("**Decision Node:** Waiting for HITL (Human-in-the-Loop) Approval.")
                    status.update(label="Workflow Complete! Awaiting Human Approval.", state="complete", expanded=False)
                else:
                    status.update(label="Failed at LLM / Backend extraction", state="error")
                    st.error(f"API Error {response.status_code}: {response.text}")
            except requests.exceptions.ConnectionError:
                status.update(label="Connection Failed", state="error")
                st.error("Could not reach FastAPI backend. Ensure the API is running.")

if st.session_state.extracted_data:
    data = st.session_state.extracted_data

    st.divider()
    st.header("2. Human-in-the-Loop (HITL) Validation")
    st.markdown("> **Rule**: Review the agent's work. Owners not matching the Roster are marked UNRESOLVED.")

    raw_items = data.get("action_items", [])
    df = pd.DataFrame(raw_items)

    if not df.empty:
        unresolved_mask = (df["owner"] == "UNRESOLVED") | (df["due_iso"] == "UNRESOLVED")
        if unresolved_mask.any():
            st.warning(f"{unresolved_mask.sum()} item(s) have unresolved fields. Fix them before approval.")

        edited_df = st.data_editor(
            df,
            column_config={
                "task": st.column_config.TextColumn("Task", required=True),
                "owner": st.column_config.TextColumn("Owner", required=True),
                "due_iso": st.column_config.TextColumn("Due Date (ISO)", required=True),
                "priority": st.column_config.SelectboxColumn("Priority", options=["Low", "Medium", "High", "Critical"]),
                "confidence": st.column_config.ProgressColumn("Confidence", min_value=0.0, max_value=1.0, format="%.2f")
            },
            use_container_width=True,
            num_rows="dynamic"
        )

        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button(" Approve & Assign Items", type="primary", use_container_width=True):
                st.session_state.approved_items = edited_df.to_dict(orient="records")
                st.session_state.is_assigned = True
                st.toast("Validated and assigned!", icon="🎉")

        if st.session_state.is_assigned:
            st.success("Status: **Approved & Assigned**")
    else:
        st.info("No action items detected.")

    st.divider()
    st.header("3. Minutes Export")
    minutes_md = data.get("minutes_markdown", "# Meeting Minutes\n\nNo minutes generated.")

    col_view, col_export = st.columns([3, 2])
    with col_view:
        st.markdown(minutes_md)

    with col_export:
        final_records = st.session_state.approved_items if st.session_state.approved_items else raw_items
        action_table_md = pd.DataFrame(final_records).to_markdown(index=False) if final_records else "None"
        full_export = f"{minutes_md}\n\n## Action Items\n\n{action_table_md}"

        st.download_button(label=" Download Minutes & Actions (.md)", data=full_export, file_name="meeting_minutes.md",
                           mime="text/markdown", use_container_width=True)
        st.download_button(label=" Download Structured Actions (.json)", data=json.dumps(final_records, indent=2),
                           file_name="action_items.json", mime="application/json", use_container_width=True)