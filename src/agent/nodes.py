import os
import time
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from src.schemas import Response, CriticEvaluation
from src.agent.state import MeetingState
from src.retrieval.retriever import retrieve_context

HAS_KEY = bool(os.environ.get("GROQ_API_KEY"))
PASSING_THRESHOLD = 8.0

llm = None
if HAS_KEY:
    from langchain_groq import ChatGroq
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
else:
    raise ValueError("API KEY IS MISSING")


def ingestor(state: MeetingState) -> dict:
    return {
        "current_retries": 0,
        "is_complete": False,
        "human_approved": False,
        "retrieved_context": "",
        "tokens_used": 0,
        "duration_seconds": 0.0
    }


def extract(state: MeetingState) -> dict:
    start_time = time.time()

    transcript = state.get("transcript", "")
    roster = state.get("roster_names", [])
    feedback = state.get("critic_feedback", [])
    past_decisions = state.get("past_decisions", "")

    structured_llm = llm.with_structured_output(Response, include_raw=True)

    prompt = f"Extract action items from this transcript:\n{transcript}\n\n"
    if roster:
        prompt += f"Strict Rule: Valid owners MUST be exactly one of these names: {roster}. Use null/omit if unknown.\n"
    if past_decisions:
        prompt += f"Strict Rule: Adhere to these past decisions: {past_decisions}\n"
    if feedback:
        prompt += f"CRITICAL - Fix this issue from the previous attempt: {feedback[-1]}\n"

    result = structured_llm.invoke([HumanMessage(content=prompt)])

    parsed_response = result["parsed"]
    raw_response = result["raw"]

    metadata = raw_response.response_metadata or {}
    token_usage = metadata.get("token_usage", {})
    actual_tokens = token_usage.get("total_tokens", 0)

    elapsed = time.time() - start_time

    return {
        "action_items": parsed_response.actions,
        "unassigned_observations": parsed_response.unassigned_observations,
        "tokens_used": state.get("tokens_used", 0) + actual_tokens,
        "duration_seconds": state.get("duration_seconds", 0.0) + elapsed,
        "current_retries": state.get("current_retries", 0) + 1
    }


def enricher(state: MeetingState) -> dict:
    actions = state.get("action_items", [])

    if not actions:
        return {"retrieved_context": "No action items extracted."}

    query_str = " ".join([a.task for a in actions])

    ctx, srcs = retrieve_context(query_str, top_k=3)

    return {"retrieved_context": ctx}


def critic_node(state: MeetingState) -> dict:
    actions = state.get("action_items", [])
    retrieved_context = state.get("retrieved_context", "")
    current_retries = state.get("current_retries", 0)
    max_retries = state.get("max_retries", 2)

    if current_retries >= max_retries:
        return {"is_complete": True}

    if not actions:
        return {
            "is_complete": False,
            "critic_feedback": ["Score: 0.0 - No action items were extracted. Please reread the transcript."],
            "quality_score": 0.0
        }

    critic_llm = llm.with_structured_output(CriticEvaluation)

    prompt = "You are a strict quality assurance critic. Review these extracted action items:\n"
    for item in actions:
        prompt += f"- Task: {item.task} | Owner: {item.owner} | Due: {item.due_iso} | Priority: {item.priority}\n"

    prompt += f"\nHistorical Context Retrieved:\n{retrieved_context}\n\n"
    prompt += (
        "Evaluate the extraction and assign a quality_score from 0.0 to 10.0. "
        "Deduct points if high-priority tasks lack dates, or if assignments contradict the historical context. "
        "If the score is strictly below 8.0, you MUST provide specific feedback on what needs to be fixed."
    )

    eval_result = critic_llm.invoke([HumanMessage(content=prompt)])

    if eval_result.quality_score >= PASSING_THRESHOLD:
        return {
            "is_complete": True,
            "quality_score": eval_result.quality_score
        }
    else:
        return {
            "is_complete": False,
            "critic_feedback": [f"(Score: {eval_result.quality_score}/10) {eval_result.feedback}"],
            "quality_score": eval_result.quality_score
        }

def decision(state: MeetingState) -> dict:
    if not state.get("human_approved"):
        raise ValueError("Graph resumed but items were not human-approved.")
    return {}


def reporter(state: MeetingState) -> dict:
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