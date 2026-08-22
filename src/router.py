from .state import MAX_RETRIES, QUALITY_THRESHOLD, MeetingState


def decision(state: MeetingState) -> dict:
    needs_retry = (
        state["quality_score"] < QUALITY_THRESHOLD
        and state["retry_count"] < MAX_RETRIES
        and not state.get("stagnant")
    )
    new_retry_count = state["retry_count"] + 1 if needs_retry else state["retry_count"]

    if needs_retry:
        outcome = "retry"
    elif state.get("stagnant"):
        outcome = "proceed to approval (extraction stagnant)"
    else:
        outcome = "proceed to approval"

    print(
        f"[decision] quality_score={round(state['quality_score'], 2)} "
        f"threshold={QUALITY_THRESHOLD} retry_count={state['retry_count']} "
        f"-> {outcome}"
    )
    return {"retry_count": new_retry_count}


def route(state: MeetingState) -> str:
    if state["quality_score"] >= QUALITY_THRESHOLD:
        return "approval"
    if state["retry_count"] >= MAX_RETRIES:
        return "approval"
    if state.get("stagnant"):
        return "approval"
    return "retry"


def route_after_approval(state: MeetingState) -> str:
    return "assign" if state.get("approved") else "revise"
