from agent.state import ResearchState

THRESHOLD, MAX_RETRIES = 0.8, 2


def decision(state: ResearchState):
    print(f"\u2696\uFE0F  Decision -> score {round(state['quality_score'],2)} at retry_count {state['retry_count']}")
    return {}

def route(state: ResearchState) -> str:
    if state["quality_score"] >= THRESHOLD:
        return "approve"
    if state["retry_count"] >= MAX_RETRIES:
        print("   \u26A0\uFE0F  Max retry_counts hit -> approving best-effort (quality below threshold).")
        return "approve"
    return "retry"
