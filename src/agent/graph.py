from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .nodes import critic, extractor, hitl_approval, ingestor, reporter
from .router import decision, route, route_after_approval
from .state import MeetingState


def build_graph():
    builder = StateGraph(MeetingState)

    builder.add_node("ingestor", ingestor)
    builder.add_node("extractor", extractor)
    builder.add_node("critic", critic)
    builder.add_node("decision", decision)
    builder.add_node("hitl_approval", hitl_approval)
    builder.add_node("reporter", reporter)

    builder.add_edge(START, "ingestor")
    builder.add_edge("ingestor", "extractor")
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
) -> MeetingState:
    """Builds the starting state. `meeting_date` is optional — the ingestor
    reads it from the transcript's `Date:` header when it isn't supplied."""
    return MeetingState(
        transcript=transcript,
        meeting_date=meeting_date,
        roster=roster or [],
        action_items=[],
        critique="",
        quality_score=0.0,
        retry_count=0,
        last_signature="",
        stagnant=False,
        approved=False,
        report="",
        injection_findings=[],
        blocked_items=[],
    )
