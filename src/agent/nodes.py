import os
import re
import time
from typing import Optional
from dateutil import parser as dateparser

from langchain_core.messages import HumanMessage
from langgraph.types import interrupt

from src.schemas import Response, CriticEvaluation
from src.agent.state import MeetingState
from src.retrieval.retriever import retrieve_context

HAS_KEY = bool(os.environ.get("GROQ_API_KEY"))
PASSING_THRESHOLD = 8.0

llm = None
if HAS_KEY:
    from langchain_groq import ChatGroq
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.2)

# Fallback Utilities
_DATE_HEADER = re.compile(r"^\s*Date:\s*(.+?)\s*$", re.I | re.M)
_MONTHS = ("January|February|March|April|May|June|July|August|September|October|November|December")
_DATE_PATTERN = re.compile(rf"\b(?:\d{{4}}-\d{{2}}-\d{{2}}|(?:{_MONTHS})\s+\d{{1,2}}(?:st|nd|rd|th)?)\b", re.I)
_COMMITMENT = re.compile(r"\b(?:i['’]?ll|i will|i can|we['’]?ll|we will|will|going to|need to|needs to|must|should)\b", re.I)
_URGENT = re.compile(r"\b(?:urgent|asap|blocker|blocking|critical|immediately)\b", re.I)

def _header_date(transcript: str) -> Optional[str]:
    """Extracts the 'Date:' header to anchor relative deadlines."""
    match = _DATE_HEADER.search(transcript)
    if not match:
        return None
    try:
        return dateparser.parse(match.group(1)).date().isoformat()
    except (ValueError, OverflowError, TypeError):
        return None

def _heuristic_items(transcript: str, roster: list[str]) -> list[dict]:
    """Regex fallback used when no API key is configured."""
    items = []
    # Simplified offline logic to catch obvious tasks
    for line in transcript.splitlines():
        if _COMMITMENT.search(line):
            date_match = _DATE_PATTERN.search(line)
            items.append({
                "task": line.strip(),
                "owner": "Unknown (Offline Fallback)",
                "due_iso": date_match.group(0) if date_match else None,
                "priority": "high" if _URGENT.search(line) else "medium",
                "dependencies": [],
                "confidence": 0.5
            })
    return items


def ingestor(state: MeetingState) -> dict:
    """Normalizes the transcript and sets up initial tracking metrics."""
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in state.get("transcript", "").splitlines()]
    transcript = "\n".join([line for line in lines if line]).strip()

    meeting_date = state.get("meeting_date") or _header_date(transcript)

    return {
        "transcript": transcript,
        "meeting_date": meeting_date,
        "current_retries": 0,
        "is_complete": False,
        "human_approved": False,
        "retrieved_context": "",
        "tokens_used": 0,
        "duration_seconds": 0.0
    }


def enricher(state: MeetingState) -> dict:
    """Queries the local RAG layer using the transcript to find relevant history."""
    transcript = state.get("transcript", "")

    if not transcript:
        return {"retrieved_context": "No transcript available."}

    # Query the vector DB using the transcript text to pull the top 4 most relevant chunks
    ctx, _ = retrieve_context(transcript, top_k=4)

    return {"retrieved_context": ctx}


def extractor(state: MeetingState) -> dict:
    """Extracts tasks using structured LLM output augmented by RAG context."""
    start_time = time.time()
    transcript = state.get("transcript", "")
    roster = state.get("roster_names", [])
    meeting_date = state.get("meeting_date")
    feedback = state.get("critic_feedback", [])
    retrieved_context = state.get("retrieved_context", "") # Add this line!

    if not HAS_KEY:
        print("[extractor] No API key. Falling back to heuristic extraction.")
        return {
            "action_items": _heuristic_items(transcript, roster),
            "duration_seconds": state.get("duration_seconds", 0.0) + (time.time() - start_time)
        }

    structured_llm = llm.with_structured_output(Response, include_raw=True)

    prompt = (
        f"Extract action items from this transcript:\n{transcript}\n\n"
        "RULES:\n"
        "1. Merge near-duplicates. Never emit two items for the exact same work.\n"
        "2. Only capture actual commitments. Do NOT capture decisions not to do something.\n"
    )
    if roster:
        prompt += f"3. Valid owners MUST be exactly one of: {roster}. Use null if unknown.\n"
    if meeting_date:
        prompt += f"4. The meeting date is {meeting_date}. Resolve relative deadlines (e.g. 'next Friday' or 'August 7') against this date and output them STRICTLY in ISO 8601 format (YYYY-MM-DD).\n"

    if retrieved_context:
        prompt += f"\nHISTORICAL CONTEXT\n{retrieved_context}\nUse this history to resolve ambiguous tasks or owners.\n"

    if feedback:
        prompt += f"\nCRITICAL - Fix this from previous run: {feedback[-1]}\n"

    result = structured_llm.invoke([HumanMessage(content=prompt)])

    parsed_response = result.get("parsed")
    raw_response = result.get("raw")

    actual_tokens = 0
    if raw_response and hasattr(raw_response, "response_metadata"):
        actual_tokens = raw_response.response_metadata.get("token_usage", {}).get("total_tokens", 0)

    elapsed = time.time() - start_time

    if not parsed_response:
        print(f"[extractor] LLM failed to parse structured output. Falling back to heuristic.")
        return {
            "action_items": _heuristic_items(transcript, roster),
            "unassigned_observations": [],
            "tokens_used": state.get("tokens_used", 0) + actual_tokens,
            "duration_seconds": state.get("duration_seconds", 0.0) + elapsed,
            "current_retries": state.get("current_retries", 0) + 1
        }

    return {
        "action_items": parsed_response.actions,
        "unassigned_observations": parsed_response.unassigned_observations,
        "tokens_used": state.get("tokens_used", 0) + actual_tokens,
        "duration_seconds": state.get("duration_seconds", 0.0) + elapsed,
        "current_retries": state.get("current_retries", 0) + 1
    }


def critic(state: MeetingState) -> dict:
    """Evaluates the extraction quality, bridging math constraints and LLM analysis."""
    actions = state.get("action_items", [])
    retrieved_context = state.get("retrieved_context", "")
    current_retries = state.get("current_retries", 0)
    max_retries = state.get("max_retries", 2)

    if current_retries >= max_retries:
        return {"is_complete": True}

    if not actions:
        return {
            "is_complete": False,
            "critic_feedback": ["Score: 0.0 - No action items extracted. Reread transcript."],
            "quality_score": 0.0
        }

    critic_llm = llm.with_structured_output(CriticEvaluation)

    prompt = "Review these extracted action items:\n"
    for item in actions:
        task = item.get("task") if isinstance(item, dict) else item.task
        owner = item.get("owner") if isinstance(item, dict) else item.owner
        due = item.get("due_iso") if isinstance(item, dict) else item.due_iso
        prompt += f"- Task: {task} | Owner: {owner} | Due: {due}\n"

    prompt += f"\nHistorical Context:\n{retrieved_context}\n\n"
    prompt += (
        f"Assign a quality_score from 0.0 to 10.0. "
        f"Deduct points heavily if tasks lack owners/dates, or contradict the history. "
        f"If below {PASSING_THRESHOLD}, write specific instructions for the extractor to fix it.\n\n"
        f"CRITICAL INSTRUCTION: You MUST respond by calling the provided tool to output structured JSON. "
        f"Do NOT output any raw text, markdown, or conversational filler."
    )

    eval_result = critic_llm.invoke([HumanMessage(content=prompt)])

    if eval_result.quality_score >= PASSING_THRESHOLD:
        return {"is_complete": True, "quality_score": eval_result.quality_score}
    else:
        return {
            "is_complete": False,
            "critic_feedback": [f"(Score: {eval_result.quality_score}/10) {eval_result.feedback}"],
            "quality_score": eval_result.quality_score
        }

def decision(state: MeetingState) -> dict:
    """Suspends graph execution using LangGraph's native interrupt API."""
    user_decision = interrupt({
        "action_items": state.get("action_items"),
        "quality_score": state.get("quality_score"),
        "message": "Approve these action items before proceeding?"
    })

    approved = bool(user_decision.get("approved")) if isinstance(user_decision, dict) else bool(user_decision)
    return {"human_approved": approved}

def reporter(state: MeetingState) -> dict:
    """Compiles the final markdown artifacts and performance metrics."""
    actions = state.get("action_items", [])

    md = [
        f"**Quality score:** {state.get('quality_score', 0):.2f}",
        f"**Execution Time:** {state.get('duration_seconds', 0):.2f}s",
        f"**Tokens Used:** {state.get('tokens_used', 0)}",
        "\n## Action Items",
        "| Task | Owner | Due Date | Priority |",
        "|---|---|---|---|"
    ]

    for item in actions:
        task = item.get("task") if isinstance(item, dict) else item.task
        owner = item.get("owner") if isinstance(item, dict) else item.owner
        due = item.get("due_iso") if isinstance(item, dict) else item.due_iso
        priority = item.get("priority", "medium") if isinstance(item, dict) else item.priority

        md.append(f"| {task} | {owner or 'TBD'} | {due or 'TBD'} | {priority} |")

    unassigned = state.get("unassigned_observations", [])
    if unassigned:
        md.append("\n## Unassigned Observations")
        for obs in unassigned:
            md.append(f"* {obs}")

    return {"final_minutes_markdown": "\n".join(md)}