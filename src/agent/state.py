from typing import TypedDict, Annotated, Optional
import operator
from src.schemas import ActionItem

class MeetingState(TypedDict):
    # Inputs
    transcript: str
    roster_names: Optional[list[str]]
    max_retries: int

    # Outputs
    action_items: list[ActionItem]
    unassigned_observations: list[str]

    # Historical (Optional)
    historical_context: str

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