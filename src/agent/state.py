from typing import TypedDict, Annotated, Optional
import operator
from src.schemas import ActionItem

class MeetingState(TypedDict):
    # Inputs
    transcript: str
    roster_names: Optional[list[str]]
    max_retries: int

    # Context (Optional)
    past_transcripts: Optional[list[str]]
    past_decisions: Optional[str]
    general_context: Optional[str]

    # Outputs
    action_items: list[ActionItem]
    unassigned_observations: Optional[list[str]]
    retrieved_context: Optional[str]

    # Critic
    critic_feedback: Annotated[list[str], operator.add]
    is_complete: bool
    current_retries: int

    # Human-in-the-Loop
    human_approved: bool
    human_edits: Optional[str]

    # Report
    final_minutes_markdown: str

    # Usage and time consumption
    tokens_used: int
    duration_seconds: float