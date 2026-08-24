from typing import Optional, TypedDict

QUALITY_THRESHOLD: float = 0.8
MAX_RETRIES: int = 2
MAX_REPAIR_ATTEMPTS: int = 2


class MeetingState(TypedDict):
    transcript: str
    meeting_date: Optional[str]
    meeting_id: Optional[str]
    roster: list[str]
    action_items: list[dict]
    decisions: list[dict]
    conflicts: list[dict]
    clarification_question: Optional[dict]
    critique: str
    quality_score: float
    retry_count: int
    last_signature: str
    stagnant: bool
    approved: bool
    report: str
    injection_findings: list[dict]
    blocked_items: list[dict]
    tokens_used: int
    duration_seconds: float