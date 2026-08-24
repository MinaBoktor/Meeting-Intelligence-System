from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .nodes import critic, extractor, hitl_approval, ingestor, enricher, reporter
from .router import decision, route, route_after_approval
from .state import MeetingState


def build_graph():
    builder = StateGraph(MeetingState)

    # 1. Register ALL nodes
    builder.add_node("ingestor", ingestor)
    builder.add_node("enricher", enricher)
    builder.add_node("extractor", extractor)
    builder.add_node("critic", critic)
    builder.add_node("decision", decision)
    builder.add_node("hitl_approval", hitl_approval)
    builder.add_node("reporter", reporter)

    builder.add_edge(START, "ingestor")
    builder.add_edge("ingestor", "enricher")
    builder.add_edge("enricher", "extractor")
    builder.add_edge("extractor", "critic")
    builder.add_edge("critic", "decision")

    builder.add_conditional_edges(
        "decision",
        route,
        {"retry": "extractor", "approval": "hitl_approval"},
    )
    builder.add_conditional_edges(
        "hitl_approval",
        route_after_approval,
        {"assign": "reporter", "revise": "extractor"},
    )

    builder.add_edge("reporter", END)

    return builder.compile(checkpointer=MemorySaver())


def initial_state(
    transcript: str,
    roster: list[str] | None = None,
    meeting_date: str | None = None,
    meeting_id: str | None = None,
) -> MeetingState:
    """Builds the starting state. `meeting_date` is optional — the ingestor
    reads it from the transcript's `Date:` header when it isn't supplied."""
    return MeetingState(
        transcript=transcript,
        meeting_date=meeting_date,
        meeting_id=meeting_id,
        roster=roster or [],
        action_items=[],
        decisions=[],
        conflicts=[],
        clarification_question=None,
        critique="",
        quality_score=0.0,
        retry_count=0,
        last_signature="",
        stagnant=False,
        approved=False,
        report="",
        injection_findings=[],
        blocked_items=[],
        tokens_used=0,
        duration_seconds=0.0
    )