import streamlit as st
import pandas as pd
import requests
import json
import os

st.set_page_config(
    page_title="Meeting Intelligence System",
    page_icon="📋",
    layout="wide"
)

# Your FastAPI endpoints
EXTRACT_URL = "http://127.0.0.1:8000/extract"
APPROVE_URL = "http://127.0.0.1:8000/approve"

# --- Secure Authentication Setup ---
AUTH_KEY = ""


if not AUTH_KEY:
    AUTH_KEY = os.environ.get("AUTH_KEY", "")

if not AUTH_KEY:
    st.warning("⚠️ Warning: AUTH_KEY is not detected. Requests to the backend may return 403 Forbidden.")

# Define secure headers for all API requests
headers = {
    "AUTH": AUTH_KEY,
    "Content-Type": "application/json"
}

st.title(" Meeting Intelligence System")
st.caption("Autonomous extraction, contextual retrieval, roster validation, and HITL review.")

# --- Session State Initialization ---
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "pending_action_items" not in st.session_state:
    st.session_state.pending_action_items = []
if "final_response" not in st.session_state:
    st.session_state.final_response = None
if "is_assigned" not in st.session_state:
    st.session_state.is_assigned = False

def read_files(uploaded_files):
    if not uploaded_files:
        return ""
    if isinstance(uploaded_files, list):
        return "\n\n---\n\n".join([f.read().decode("utf-8") for f in uploaded_files])
    return uploaded_files.read().decode("utf-8")

def parse_roster(roster_text):
    """Converts uploaded roster text into a clean list of names for the API."""
    if not roster_text:
        return []
    raw_names = roster_text.replace(",", "\n").split("\n")
    return [name.strip() for name in raw_names if name.strip()]


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

# --- Step 1: Execute the Graph until HITL Pause ---
if run_extraction:
    if not transcripts:
        st.warning(" Please upload at least one Transcript to proceed.")
    else:
        # Reset state for a new run
        st.session_state.thread_id = None
        st.session_state.final_response = None
        st.session_state.is_assigned = False

        payload = {
            "transcript": read_files(transcripts),
            "history": read_files(history_files),
            "context": read_files(general_context),
            "roster_names": parse_roster(read_files(roster_file)),
            "past_decisions": read_files(past_decisions)
        }

        st.header(" Agent Reasoning Stream")

        with st.status("Agent Workflow in Progress...", expanded=True) as status:
            st.write(" **Ingestor Node:** Parsing current transcripts and sanitizing injections...")
            st.write(" **Enricher Node:** Indexing History transcripts for semantic retrieval...")
            st.write("⏳ **Extractor Node:** Calling LLM for structured output...")

            try:
                # Included secure headers with the AUTH_KEY token
                response = requests.post(EXTRACT_URL, json=payload, headers=headers, timeout=120)
                if response.status_code == 200:
                    data = response.json()
                    
                    st.session_state.thread_id = data.get("thread_id")
                    st.session_state.pending_action_items = data.get("action_items", [])
                    
                    st.write("**Critic Node:** Validating extracted items against Roster and checking dates...")
                    st.write("**Decision Node:** Graph paused. Waiting for HITL (Human-in-the-Loop) Approval.")
                    status.update(label="Workflow Paused! Awaiting Human Approval.", state="complete", expanded=False)
                else:
                    status.update(label="Failed at LLM / Backend extraction", state="error")
                    st.error(f"API Error {response.status_code}: {response.text}")
            except requests.exceptions.ConnectionError:
                status.update(label="Connection Failed", state="error")
                st.error("Could not reach FastAPI backend. Ensure the API is running.")


# --- Step 2: Human-in-the-Loop (HITL) Validation ---
if st.session_state.thread_id and not st.session_state.is_assigned:
    st.divider()
    st.header("2. Human-in-the-Loop (HITL) Validation")
    st.markdown("> **Rule**: Review the agent's work. Owners not matching the Roster are marked as null.")

    raw_items = st.session_state.pending_action_items
    df = pd.DataFrame(raw_items)

    if not df.empty:
        unresolved_mask = df["owner"].isna() | df["due_iso"].isna()
        if unresolved_mask.any():
            st.warning(f"{unresolved_mask.sum()} item(s) have unresolved fields. Review them carefully.")

        edited_df = st.data_editor(
            df,
            column_config={
                "task": st.column_config.TextColumn("Task", required=True),
                "owner": st.column_config.TextColumn("Owner", required=True),
                "due_iso": st.column_config.TextColumn("Due Date (ISO)", required=True),
                "priority": st.column_config.SelectboxColumn("Priority", options=["low", "medium", "high"]),
                "confidence": st.column_config.ProgressColumn("Confidence", min_value=0.0, max_value=1.0, format="%.2f")
            },
            use_container_width=True,
            num_rows="dynamic"
        )

        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button(" Approve & Assign Items", type="primary", use_container_width=True):
                approval_payload = {
                    "thread_id": st.session_state.thread_id,
                    "approved": True
                }
                try:
                    # Included secure headers for the approval step as well
                    res = requests.post(APPROVE_URL, json=approval_payload, headers=headers, timeout=120)
                    if res.status_code == 200:
                        st.session_state.final_response = res.json()
                        st.session_state.is_assigned = True
                        st.rerun()
                    else:
                        st.error(f"Approval failed: {res.text}")
                except Exception as e:
                    st.error(f"Failed to communicate with API: {e}")
    else:
        st.info("No action items detected by the agent.")


# --- Step 3: Final Output & Observability ---
if st.session_state.is_assigned and st.session_state.final_response:
    data = st.session_state.final_response
    
    st.success("Status: **Approved & Graph Completed**")
    st.divider()
    
    findings = data.get("injection_findings", [])
    blocked = data.get("blocked_items", [])
    
    if findings or blocked:
        st.subheader("🛡️ Security & Integrity Interventions")
        if findings:
            st.error(f"**Quarantined {len(findings)} malicious instruction(s)** before processing.")
            with st.expander("View Blocked Injections"):
                st.json(findings)
        if blocked:
            st.warning(f"**Blocked {len(blocked)} record(s)** from reaching the final report.")
            with st.expander("View Blocked Payloads"):
                st.json(blocked)

    st.subheader("📊 Observability Metrics")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Quality Score", f"{data.get('quality_score', 0.0):.2f}")
    m2.metric("Repair Retries", data.get("retry_count", 0))
    m3.metric("Tokens Used", data.get("tokens_used", 0))
    m4.metric("Latency (s)", f"{data.get('duration_seconds', 0.0):.2f}")

    st.divider()
    st.header("3. Minutes Export")
    
    minutes_md = data.get("report", "# Meeting Minutes\n\nNo report generated.")

    col_view, col_export = st.columns([3, 2])
    with col_view:
        st.markdown(minutes_md)

    with col_export:
        final_actions = data.get("actions", [])
        
        st.download_button(
            label=" Download Minutes (.md)", 
            data=minutes_md, 
            file_name="meeting_minutes.md",
            mime="text/markdown", 
            use_container_width=True
        )
        st.download_button(
            label=" Download Structured Actions (.json)", 
            data=json.dumps(final_actions, indent=2),
            file_name="action_items.json", 
            mime="application/json", 
            use_container_width=True
        )