from langgraph.graph import StateGraph, START, END
from agent.nodes import planner, research, critic, reporter
from agent.router import decision, route
from agent.state import ResearchState

def build_graph():
    builder = StateGraph(ResearchState)
    for name, fn in [("planner", planner), ("research", research),
                     ("critic", critic), ("decision", decision), ("reporter", reporter)]:
        builder.add_node(name, fn)

    builder.add_edge(START, "planner")
    builder.add_edge("planner", "research")
    builder.add_edge("research", "critic")
    builder.add_edge("critic", "decision")
    builder.add_conditional_edges("decision", route, {"retry": "planner", "approve": "reporter"})
    builder.add_edge("reporter", END)

    return builder.compile()

system = build_graph()
print("Graph compiled \u2713")