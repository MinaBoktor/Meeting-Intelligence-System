from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.agent.state import MeetingState
from src.agent.nodes import (
    ingestor,
    extract,
    enricher,
    critic,
    decision,
    reporter
)

def route_critic(state: MeetingState):
    if state.get("is_complete"):
        return "approve"
    return "retry"

def route_human_decision(state: MeetingState):
    if state.get("human_approved"):
        return "reporter"

    if state.get("critic_feedback"):
        return "extractor"

    return END

def build_graph():
    builder = StateGraph(MeetingState)

    builder.add_node("ingestor", ingestor)
    builder.add_node("extractor", extract)
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
            "retry": "extractor",
            "approve": "decision"
        }
    )

    builder.add_conditional_edges(
        "decision",
        route_human_decision,
        {
            "reporter": "reporter",
            "extractor": "extractor",
            END: END
        }
    )
    builder.add_edge("reporter", END)

    memory = MemorySaver()

    return builder.compile(checkpointer=memory, interrupt_before=["decision"])

system = build_graph()
print("Meeting Intelligence Graph compiled")