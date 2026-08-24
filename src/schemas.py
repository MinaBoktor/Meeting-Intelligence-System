from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from typing import Literal, Optional, List, Dict, Any, Optional
from dateutil import parser as dateparser



level = Literal["low", "medium", "high"]

class ActionItem(BaseModel):
    task: str
    owner: Optional[str] = Field(default=None, description="The assigned owner, or null if unassigned")
    due_iso: Optional[str] = Field(default=None, description="The ISO due date, or null if unspecified")
    priority: str
    dependencies: List[str] = Field(default_factory=list)
    confidence: float

    @field_validator("due_iso", mode="before")
    @classmethod
    def enforce_iso_date(cls, value):
        if not value or value.lower() in ["null", "none", "n/a"]:
            return None

        try:
            parsed_date = dateparser.parse(str(value)).date()
            return parsed_date.isoformat()
        except (ValueError, TypeError, OverflowError):
            return None

    @field_validator('owner')
    @classmethod
    def validate_owner(cls, v: str, info: ValidationInfo) -> str:

        valid_names = info.context.get('valid_names') if info.context else None

        if not valid_names:
            return v

        if v not in valid_names:
            raise ValueError(f"'{v}' is invalid. Owners must be exact roster names. Valid options are: {valid_names}. If there is no clear owner, omit this task entirely.")
        return v

    @field_validator('due_iso')
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("Must be a valid ISO 8601 date string or null.")
        return v

class Request(BaseModel):
    transcript: str
    roster_names: List[str] = Field(default_factory=list)
    history: Optional[str] = None
    context: Optional[str] = None
    past_decisions: Optional[str] = None

    @field_validator('roster_names')
    @classmethod
    def check_for_garbage(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if not v:
            return v

        clean_names = []
        for item in v:
            item = item.strip()
            if 1 < len(item) < 60 and not item.isnumeric():
                clean_names.append(item)

        if not clean_names:
            raise ValueError("The provided roster is invalid. It must contain human-readable names, not paragraphs, numbers, or empty values.")
        return clean_names

class Response(BaseModel):
    actions: list[ActionItem]
    decisions: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted decisions.")
    conflicts: List[Dict[str, Any]] = Field(default_factory=list, description="Detected conflicts with past decisions.")
    unassigned_observations: list[str] = Field(default=[], description="List any tasks or decisions that lack a clear, valid owner from the roster.")
    quality_score: float
    retry_count: int
    tokens_used: int
    duration_seconds: float
    report: str = ""
    injection_findings: List[Dict[str, Any]] = []
    blocked_items: List[Dict[str, Any]] = []


class CriticEvaluation(BaseModel):
    quality_score: float = Field(description="A mathematical score from 0.0 to 10.0 evaluating the extraction. Deduct points for missing due dates, invalid owners, or contradicting historical context.")
    feedback: str = Field(description="Strict, actionable instructions for the extractor on what to fix if the score is below 8.0. Leave empty if 8.0 or higher.")