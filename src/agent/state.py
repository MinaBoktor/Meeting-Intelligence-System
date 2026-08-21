import operator
from typing import Annotated, Optional, TypedDict, Any
from src.schemas import ActionItem

QUALITY_THRESHOLD: float = 8.0
MAX_RETRIES: int = 2
MAX_REPAIR_ATTEMPTS: int = 2

class MeetingState(TypedDict):
    # 1. Core Inputs
    transcript: str
    meeting_date: Optional[str]
    roster_names: Optional[list[str]]
    max_retries: int

    # 2. Context & RAG
    past_transcripts: Optional[list[str]]
    past_decisions: Optional[str]
    general_context: Optional[str]
    retrieved_context: Optional[str]

    # Extracted Data
    action_items: list[dict | ActionItem]
    unassigned_observations: Optional[list[str]]

    # Critic & Repair Loop Variables
    critic_feedback: Annotated[list[str], operator.add]
    quality_score: float
    current_retries: int
    is_complete: bool

    # Defensive flags to detect if the LLM is stubbornly repeating itself
    last_signature: str
    stagnant: bool

    # Human-in-the-Loop (HITL)
    human_approved: bool
    human_edits: Optional[str]

    # Outputs & Metrics
    final_minutes_markdown: str
    tokens_used: int
    duration_seconds: float