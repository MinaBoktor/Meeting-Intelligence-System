from typing import TypedDict
from pydantic import BaseModel, Field
from typing import Literal


level = Literal["low", "medium", "high"]

class Action(BaseModel):
    task: str
    owner: str
    due_iso: str
    priority: level = Field(description="Decide the priority level of the task")
    dependencies: list[str]
    confidence: float


class MeetingState(TypedDict):
    tasks: list[Action]
    findings: list[str]
    sources: list[str]
    critique: str
    quality_score: float
    retry_count: int
    report: str