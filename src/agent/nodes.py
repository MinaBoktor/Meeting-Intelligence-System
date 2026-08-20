import os
import json
import re
from src.schemas import ActionItem, Response
from langchain_core.messages import HumanMessage
from agent.state import MeetingState
from retrieval.retriever import retrieve_context
import textwrap


HAS_KEY = bool(os.environ.get("GROQ_API_KEY"))

llm = None
if HAS_KEY:
    from langchain_groq import ChatGroq
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
else:
    raise ValueError("API KEY IS MISSING")


def ingestor_node(state: dict) -> dict:
    return {
        "current_retries": 0,
        "is_complete": False,
        "human_approved": False,
        "retrieved_context": ""
    }


def extract(state: dict) -> dict:
    transcript = state.get("transcript", "")
    roster = state.get("roster_names", [])
    feedback = state.get("critic_feedback", [])

    structured_llm = llm.with_structured_output(Response, include_raw=True)

    prompt = f"Extract action items from this transcript: {transcript}\n"
    if roster:
        prompt += f"Valid owners: {roster}\n"
    if feedback:
        prompt += f"Previous feedback to fix: {feedback[-1]}\n"

    result = structured_llm.invoke([HumanMessage(content=prompt)])

    parsed_response = result["parsed"]
    raw_response = result["raw"]

    actual_tokens = raw_response.response_metadata.get("token_usage", {}).get("total_tokens", 0)

    return {
        "action_items": parsed_response.actions,
        "unassigned_observations": parsed_response.unassigned_observations,
        "tokens_used": actual_tokens,
        "current_retries": state.get("current_retries", 0) + 1
    }


def enricher_node(state: dict) -> dict:
    # 1. Check for user-provided context first
    past_decisions = state.get("past_decisions")
    if past_decisions:
        return {"retrieved_context": f"Provided Rules: {past_decisions}"}
    
    # 2. Otherwise, query LlamaIndex (pseudo-code for your LlamaIndex engine)
    actions = state.get("action_items", [])
    query_str = f"Find past decisions related to: {[a.task for a in actions]}"
    
    # retrieved_nodes = query_engine.query(query_str)
    # formatted_context = format_nodes(retrieved_nodes)
    
    formatted_context = "Historical data retrieved from LlamaIndex..." 
    
    return {"retrieved_context": formatted_context}


def decision_node(state: dict) -> dict:
    # The graph pauses BEFORE executing this. 
    # When it resumes, we check if the UI updated the state.
    if not state.get("human_approved"):
        raise ValueError("Graph resumed but items were not human-approved.")
    
    # Apply any manual human edits to the action items if they exist
    return {} # No further state changes needed; proceed to Reporter


def reporter_node(state: dict) -> dict:
    actions = state.get("action_items", [])
    
    markdown = "# Meeting Minutes\n\n## Action Items\n"
    markdown += "| Task | Owner | Due Date | Priority |\n"
    markdown += "|---|---|---|---|\n"
    
    for item in actions:
        due = item.due_iso if item.due_iso else "TBD"
        markdown += f"| {item.task} | {item.owner} | {due} | {item.priority} |\n"
        
    unassigned = state.get("unassigned_observations", [])
    if unassigned:
        markdown += "\n## Unassigned Observations\n"
        for obs in unassigned:
            markdown += f"* {obs}\n"
            
    return {"final_minutes_markdown": markdown}
