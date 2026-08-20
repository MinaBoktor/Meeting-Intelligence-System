from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from typing import Literal, Optional



level = Literal["low", "medium", "high"]

class ActionItem(BaseModel):
    task: str
    owner: str = Field(description="The person responsible for the task.")
    due_iso: Optional[str] = Field(description="ISO 8601 date string. Use null if vague.")
    priority: level = Field(description="High means explicit urgency; otherwise Medium/Low.")
    dependencies: list[str]
    confidence: float

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
    max_retries: int = 2
    roster_names: Optional[list[str]] = Field(default=None, description="A normalized list of valid names extracted from the user's roster.")

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
    unassigned_observations: list[str] = Field(default=[], description="List any tasks or decisions that lack a clear, valid owner from the roster.")
    quality_score: float
    retry_count: int
    tokens_used: int
    duration_seconds: float


class CriticEvaluation(BaseModel):
    quality_score: float = Field(description="A mathematical score from 0.0 to 10.0 evaluating the extraction. Deduct points for missing due dates, invalid owners, or contradicting historical context.")
    feedback: str = Field(description="Strict, actionable instructions for the extractor on what to fix if the score is below 8.0. Leave empty if 8.0 or higher.")