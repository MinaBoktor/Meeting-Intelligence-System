

import glob
import json
import time
import os

from src.agent.graph import system, initial_state
from src.agent.state import MAX_RETRIES
from src.retrieval.retriever import read_documents
from langgraph.types import Command

# Groq pricing for openai/gpt-oss-120b (the model used in src/agent/nodes.py)
# Source: Groq's published rate — $0.15 / 1M input tokens, $0.60 / 1M output tokens.
# nodes.py only reports *total* tokens (not split input/output), so we estimate
# cost using a blended rate; edit PRICE_PER_1K_BLENDED if you split them later.
PRICE_PER_1K_BLENDED = 0.375 / 1_000_000  # متوسط (0.15 input + 0.60 output)/2 لكل مليون توكن # conservative blended $/token estimate


def load_roster():
    roster = json.load(open("data/knowledge_base/roster.json"))
    return [p["name"] for p in roster["people"]]


def load_kb_for_retrieval():
    """Index the knowledge base once, exactly like the app does on startup."""
    files = {}
    for path in glob.glob("data/knowledge_base/transcripts/*.txt"):
        files[os.path.basename(path)] = open(path).read()
    files["past_decisions.md"] = open("data/knowledge_base/past_decisions.md").read()
    files["context.md"] = open("data/knowledge_base/context.md").read()
    read_documents(files)


def run_one(transcript: str, roster: list[str], thread_id: str) -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    state_input = initial_state(transcript=transcript, roster=roster)
    state_input["max_retries"] = MAX_RETRIES

    t0 = time.perf_counter()
    result = system.invoke(state_input, config=config)
    # Auto-approve the HITL interrupt for benchmarking purposes
    result = system.invoke(Command(resume={"approved": True}), config=config)
    wall_ms = (time.perf_counter() - t0) * 1000

    tokens = result.get("tokens_used", 0)
    return {
        "thread_id": thread_id,
        "quality_score": result.get("quality_score", 0.0),
        "retry_count": result.get("current_retries", 0),
        "tokens_used": tokens,
        "duration_seconds_reported": result.get("duration_seconds", 0.0),
        "wall_clock_ms": round(wall_ms, 1),
        "estimated_cost_usd": round(tokens * PRICE_PER_1K_BLENDED / 1000 * 1000, 6),
        "n_action_items": len(result.get("action_items", [])),
    }


if __name__ == "__main__":
    if not os.environ.get("GROQ_API_KEY"):
        raise SystemExit("Set GROQ_API_KEY first: export GROQ_API_KEY=your_key")

    roster = load_roster()
    print("Indexing knowledge base for retrieval...")
    load_kb_for_retrieval()

    runs = []
    for path in sorted(glob.glob("data/eval/eval_*.txt")):
        transcript = open(path).read()
        print(f"Running pipeline on {path} ...")
        r = run_one(transcript, roster, thread_id=path)
        r["file"] = path
        runs.append(r)
        print(r)

    avg_tokens = sum(r["tokens_used"] for r in runs) / len(runs)
    avg_latency = sum(r["duration_seconds_reported"] for r in runs) / len(runs)
    avg_cost = sum(r["estimated_cost_usd"] for r in runs) / len(runs)
    total_cost_30_meetings = avg_cost * 30

    print("\n=== SUMMARY (paste into Cost_Observability_Report.md) ===")
    print(f"Avg tokens per meeting (extractor+critic): {avg_tokens:.1f}")
    print(f"Avg reported duration_seconds per meeting: {avg_latency:.2f}s")
    print(f"Avg estimated cost per meeting: ${avg_cost:.6f}")
    print(f"Estimated cost for 30 meetings: ${total_cost_30_meetings:.4f}")

    json.dump(
        {"runs": runs, "avg_tokens": avg_tokens, "avg_duration_seconds": avg_latency,
         "avg_cost_usd": avg_cost, "cost_30_meetings_usd": total_cost_30_meetings},
        open("real_pipeline_trace.json", "w"), indent=2
    )
    print("\nSaved: real_pipeline_trace.json")
