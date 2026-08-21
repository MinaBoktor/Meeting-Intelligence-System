from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.agent.state import MeetingState
from src.agent.nodes import (
    ingestor,
    extractor,
    enricher,
    critic,
    decision,
    reporter
)


def route_critic(state: MeetingState) -> str:
    """Evaluates the critic's output to determine if we need an autonomous repair loop."""
    if state.get("is_complete"):
        return "decision"
    return "extractor"


def route_human_decision(state: MeetingState) -> str:
    """Routes the graph based on the human's response from the HITL interrupt."""
    if state.get("human_approved"):
        return "reporter"

    # If the human rejected it but provided feedback in the UI, cycle back for a retry
    if state.get("critic_feedback"):
        return "extractor"

    return END


def build_graph():
    builder = StateGraph(MeetingState)

    builder.add_node("ingestor", ingestor)
    builder.add_node("extractor", extractor)
    builder.add_node("enricher", enricher)
    builder.add_node("critic", critic)
    builder.add_node("decision", decision)
    builder.add_node("reporter", reporter)

    builder.add_edge(START, "ingestor")
    builder.add_edge("ingestor", "extractor")
    builder.add_edge("extractor", "enricher")
    builder.add_edge("enricher", "critic")

    builder.add_conditional_edges(
        "critic",
        route_critic,
        {
            "decision": "decision",
            "extractor": "extractor"
        }
    )

    # HITL Gateway
    builder.add_conditional_edges(
        "decision",
        route_human_decision,
        {
            "reporter": "reporter",
            "extractor": "extractor",
            END: END
        }
    )

    # Finalization
    builder.add_edge("reporter", END)

    memory = MemorySaver()
    return builder.compile(checkpointer=memory)


def initial_state(
    transcript: str,
    roster: list[str] | None = None,
    meeting_date: str | None = None,
    past_decisions: str | None = None
) -> dict:
    """
    Helper to cleanly initialize the state dictionary for the API/UI.
    The ingestor will read the meeting_date from the transcript's Date: header if it isn't supplied here.
    """
    return {
        "transcript": transcript,
        "roster_names": roster or [],
        "meeting_date": meeting_date,
        "past_decisions": past_decisions or "",
        "action_items": [],
        "unassigned_observations": [],
        "critic_feedback": [],
        "current_retries": 0,
        "max_retries": 2,
        "is_complete": False,
        "human_approved": False,
        "quality_score": 0.0,
        "tokens_used": 0,
        "duration_seconds": 0.0,
        "retrieved_context": ""
    }


system = build_graph()
print("Meeting Intelligence Graph compiled and ready \u2713")