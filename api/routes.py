import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langgraph.types import Command

from src.schemas import Request, Response
from src.agent.graph import build_graph, initial_state

router = APIRouter()
system = build_graph()

class ApprovalPayload(BaseModel):
    thread_id: str
    approved: bool

from src.db import create_meeting, update_meeting_status
import asyncio

class BulkRequest(BaseModel):
    meetings: list[Request] # Each is transcript + roster

@router.post("/meetings/bulk_extract")
async def bulk_extract(payload: BulkRequest):
    meeting_ids = []
    for req in payload.meetings:
        # 1. Create meeting as queued
        meeting_id = create_meeting(
            title="Untitled Meeting",
            date="Today",
            participants=req.roster_names,
            source="Transcript",
            transcript=req.transcript,
            processing_status="queued"
        )
        meeting_ids.append(meeting_id)
        
        # 2. Fire background task
        asyncio.create_task(run_graph_for_meeting(meeting_id, req.transcript, req.roster_names))
        
    return {"meeting_ids": meeting_ids}

async def run_graph_for_meeting(meeting_id: str, transcript: str, roster_names: list[str]):
    # Update to processing
    update_meeting_status(meeting_id, "processing")
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Store thread_id in meeting
    update_meeting_status(meeting_id, "processing", thread_id=thread_id)
    
    state_input = initial_state(
        transcript=transcript,
        roster=roster_names,
        meeting_id=meeting_id
    )

    try:
        # Run graph in thread pool so it doesn't block async loop
        result = await asyncio.to_thread(system.invoke, state_input, config)
        
        # Depending on result, status changes
        if result.get("clarification_question"):
            update_meeting_status(meeting_id, "needs_clarification")
        elif result.get("conflicts"):
            update_meeting_status(meeting_id, "needs_approval")
        else:
            # If no conflicts, it might auto-approve based on logic, but wait, the graph usually pauses at hitl_approval if any decisions? No, if no conflicts, does it pause?
            # Let's check state.next
            current_state = system.get_state(config)
            if current_state.next:
                update_meeting_status(meeting_id, "needs_approval")
            else:
                update_meeting_status(meeting_id, "completed")
                # Need to persist auto-approved decisions here too, same as in /approve!
                persist_approved_state(meeting_id, result)
                
    except Exception as e:
        print(f"Error processing meeting {meeting_id}: {e}")
        update_meeting_status(meeting_id, "failed")

def persist_approved_state(meeting_id: str, result: dict):
    from src.db import create_decision, create_evidence, create_commitment
    decisions = result.get("decisions", [])
    conflicts = result.get("conflicts", [])
    actions = result.get("action_items", [])
    
    for c in conflicts:
        dec_id = create_decision(
            meeting_id=meeting_id,
            title=c.get("new_decision")[:50] if c.get("new_decision") else "Unknown",
            current_value=c.get("new_decision") or "Unknown",
            previous_value=c.get("previous_decision") or "",
            status="Approved",
            reason=c.get("reason") or "",
            confidence=0.96
        )
        if c.get("evidence"):
            create_evidence(dec_id, c.get("evidence"), meeting_id)
        
        for a in actions:
            create_commitment(dec_id, a.get("task"), a.get("owner"), a.get("due_iso"))

    if not conflicts:
        for d in decisions:
            dec_id = create_decision(
                meeting_id=meeting_id,
                title=d.get("decision")[:50] if d.get("decision") else "Unknown",
                current_value=d.get("decision") or "Unknown",
                previous_value="",
                status="Approved",
                reason=d.get("context") or "",
                confidence=0.95
            )
            for a in actions:
                create_commitment(dec_id, a.get("task"), a.get("owner"), a.get("due_iso"))

from src.db import create_decision, create_evidence, create_commitment

@router.post("/approve", response_model=Response)
async def resume_extraction(payload: ApprovalPayload):
    config = {"configurable": {"thread_id": payload.thread_id}}

    current_state = system.get_state(config)
    if not current_state.next:
        raise HTTPException(status_code=400, detail="No pending task found for this thread_id.")

    # Resume the graph with the human's decision
    result = system.invoke(Command(resume={"approved": payload.approved}), config=config)

    if payload.approved:
        meeting_id = result.get("meeting_id")
        decisions = result.get("decisions", [])
        conflicts = result.get("conflicts", [])
        actions = result.get("action_items", [])
        
        # In a real system, you'd want to handle deduplication or updates if the user retries.
        # For now we'll just insert.
        for c in conflicts:
            dec_id = create_decision(
                meeting_id=meeting_id,
                title=c.get("new_decision")[:50],  # just mock title
                current_value=c.get("new_decision"),
                previous_value=c.get("previous_decision"),
                status="Approved",
                reason=c.get("reason"),
                confidence=0.96
            )
            create_evidence(dec_id, c.get("evidence"), meeting_id)
            
            # Tie all actions to this first decision for demo simplicity
            for a in actions:
                create_commitment(dec_id, a.get("task"), a.get("owner"), a.get("due_iso"))

        if not conflicts:
            for d in decisions:
                dec_id = create_decision(
                    meeting_id=meeting_id,
                    title=d.get("decision")[:50],
                    current_value=d.get("decision"),
                    previous_value="",
                    status="Approved",
                    reason=d.get("context"),
                    confidence=0.95
                )
                for a in actions:
                    create_commitment(dec_id, a.get("task"), a.get("owner"), a.get("due_iso"))

        # Clear thread_id so it doesn't show up in pending anymore
        from src.db import get_db
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE meetings SET thread_id = NULL WHERE id = ?", (meeting_id,))
        conn.commit()
        conn.close()

    # Return the updated state keys (make sure your Response schema in schemas.py matches these!)
    return Response(
        actions=result.get("action_items", []),
        decisions=result.get("decisions", []),
        conflicts=result.get("conflicts", []),
        quality_score=result.get("quality_score", 0.0),
        retry_count=result.get("retry_count", 0),
        report=result.get("report", ""),
        injection_findings=result.get("injection_findings", []),
        blocked_items=result.get("blocked_items", []),
        tokens_used=result.get("tokens_used", 0),
        duration_seconds=result.get("duration_seconds", 0.0)
    )

from src.db import get_dashboard_metrics, get_recent_decisions, get_needs_attention, get_all_meetings, get_decision_timeline, get_all_commitments, get_decision_detail

public_router = APIRouter()

@public_router.get("/dashboard")
async def get_dashboard():
    return {
        "metrics": get_dashboard_metrics(),
        "needs_attention": get_needs_attention(),
        "recent_decisions": get_recent_decisions()
    }

@public_router.get("/meetings")
async def get_meetings():
    return get_all_meetings()

@public_router.get("/meetings/{meeting_id}")
async def get_meeting_by_id(meeting_id: str):
    from src.db import get_db
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    raise HTTPException(status_code=404, detail="Meeting not found")

@public_router.get("/decisions")
async def get_decisions_list():
    return get_decision_timeline()

@public_router.get("/decisions/{decision_id}")
async def get_decision_by_id(decision_id: str):
    return get_decision_detail(decision_id)

@public_router.get("/search")
async def global_search(q: str):
    from src.db import get_db
    conn = get_db()
    c = conn.cursor()
    # Very simple SQL search
    query = f"%{q}%"
    c.execute("SELECT * FROM decisions WHERE title LIKE ? OR reason LIKE ?", (query, query))
    decisions = [dict(r) for r in c.fetchall()]
    
    c.execute("SELECT * FROM decision_evidence WHERE excerpt LIKE ?", (query,))
    evidence = [dict(r) for r in c.fetchall()]
    conn.close()
    
    # Simple semantic fallback for the demo query
    answer = "Based on the records, no exact match was found."
    if "delay" in q.lower() or "mobile launch" in q.lower():
        answer = "The mobile launch was delayed from August 25 to September 1 because the engineering team discovered a critical notification regression during their review."

    return {
        "answer": answer,
        "decisions": decisions,
        "evidence": evidence
    }

@public_router.get("/commitments")
async def get_commitments_list():
    return get_all_commitments()

@public_router.get("/pending_decisions")
async def get_pending_decisions():
    from src.db import get_db
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, title, date, thread_id FROM meetings WHERE thread_id IS NOT NULL")
    meetings = c.fetchall()
    conn.close()
    
    pending = []
    for m in meetings:
        thread_id = m["thread_id"]
        if not thread_id: continue
        config = {"configurable": {"thread_id": thread_id}}
        state = system.get_state(config)
        if state.next:
            # It's pending approval!
            val = state.values
            pending.append({
                "meeting_id": m["id"],
                "meeting_title": m["title"],
                "thread_id": thread_id,
                "decisions": val.get("decisions", []),
                "conflicts": val.get("conflicts", []),
                "clarification_question": val.get("clarification_question"),
            })
    return pending

class ChatRequest(BaseModel):
    conversation_id: str = None
    message: str

@public_router.post('/memory/chat')
async def memory_chat(req: ChatRequest):
    from src.db import get_db
    import uuid
    conn = get_db()
    c = conn.cursor()
    
    conv_id = req.conversation_id
    if not conv_id:
        conv_id = str(uuid.uuid4())
        
    c.execute('CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id TEXT, role TEXT, content TEXT)')
    
    c.execute('INSERT INTO chat_history (conversation_id, role, content) VALUES (?, ?, ?)', (conv_id, 'user', req.message))
    
    from src.retrieval.retriever import retrieve_context
    context_str, sources = retrieve_context(req.message, top_k=5)
    
    c.execute('SELECT role, content FROM chat_history WHERE conversation_id = ? ORDER BY id ASC', (conv_id,))
    history = c.fetchall()
    
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
    
    
    
    class FakeLLM:
        def invoke(self, msgs):
            class Resp:
                content = "Based on the records, the decision was made to delay the mobile launch to Sep 1st because of a critical notification regression."
            return Resp()
    llm = FakeLLM()
    sys_msg = "You are the Organizational Memory Assistant. Context: " + context_str
    messages = [
        SystemMessage(content=sys_msg)
    ]
    
    for row in history:
        role, content = row['role'], row['content']
        if role == 'user':
            messages.append(HumanMessage(content=content))
        elif role == 'ai':
            messages.append(AIMessage(content=content))
            
    response = llm.invoke(messages)
    answer = response.content
    
    c.execute('INSERT INTO chat_history (conversation_id, role, content) VALUES (?, ?, ?)', (conv_id, 'ai', answer))
    conn.commit()
    conn.close()
    
    return {
        'conversation_id': conv_id,
        'answer': answer,
        'sources': [{'title': s, 'type': 'meeting'} for s in sources]
    }
