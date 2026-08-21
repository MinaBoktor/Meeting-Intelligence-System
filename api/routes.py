import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langgraph.types import Command

from src.schemas import Request, Response
from src.agent.graph import system, initial_state
from src.agent.state import MAX_RETRIES

router = APIRouter()

class ApprovalPayload(BaseModel):
    thread_id: str
    approved: bool

@router.post("/extract")
async def start_extraction(request: Request):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    state_input = initial_state(
        transcript=request.transcript,
        roster=request.roster_names
    )
    state_input["max_retries"] = MAX_RETRIES

    result = system.invoke(state_input, config=config)

    current_state = system.get_state(config)
    if not current_state.next:
        raise HTTPException(status_code=500, detail="Graph completed without pausing for HITL.")

    return {
        "status": "pending_approval",
        "thread_id": thread_id,
        "quality_score": result.get("quality_score", 0.0),
        "action_items": result.get("action_items", []),
        "message": "Graph paused. Awaiting human review."
    }

@router.post("/approve", response_model=Response)
async def resume_extraction(payload: ApprovalPayload):
    config = {"configurable": {"thread_id": payload.thread_id}}

    current_state = system.get_state(config)
    if not current_state.next:
        raise HTTPException(status_code=400, detail="No pending task found for this thread_id.")

    result = system.invoke(Command(resume={"approved": payload.approved}), config=config)

    return Response(
        actions=result.get("action_items", []),
        unassigned_observations=result.get("unassigned_observations", []),
        quality_score=result.get("quality_score", 0.0),
        retry_count=result.get("current_retries", 0),
        tokens_used=result.get("tokens_used", 0),
        duration_seconds=result.get("duration_seconds", 0.0)
    )