from typing import TypedDict
from pydantic import BaseModel, Field


TopicLevel = Literal["Beginner", "Intermediate", "Advanced"]

class Action(BaseModel):
    task: str
    owner: str
    due_iso: str
    priority: 


class MeetingState(TypedDict):
    tasks: list[str]     # produced by the Planner
    findings: list[str]  # produced by the Researcher
    sources: list[str]
    critique: str        # the Critic's written feedback/ gaps
    quality_score: float # 0.0-1.0, produced by the Critic
    retry_count: int     # incremented on every loop back
    report: str          # final structured output