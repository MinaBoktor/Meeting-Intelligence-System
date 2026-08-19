import os
import json
import re
from typing import List
from pydantic import BaseModel, Field
from agent.state import ResearchState
from agent.retriever import retrieve_context
import textwrap


HAS_KEY = bool(os.environ.get("GROQ_API_KEY"))

llm = None
if HAS_KEY:
    from langchain_groq import ChatGroq
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
else:
    raise ValueError("API KEY IS MISSING")


class FinalReport(BaseModel):
    goal: str
    summary: str
    key_findings: List[str] = Field(min_length=1)
    risks: List[str]
    sources: List[str]
    retry_counts: int
    confidence: str = Field(description="high | medium | low")


def planner(state: ResearchState):
    it = state["retry_count"] + 1
    prior = state.get("critique", "")

    prompt = (
        f"You are a planning agent. Goal: {state['goal']}.\n"
        f"Previous critique to address (empty on first pass): {prior or 'none'}.\n"
        "Return 3 short task bullets that specifically address any gaps. "
        "One per line, no numbering."
    )
    text = llm.invoke(prompt).content
    tasks = [t.strip("-* ").strip() for t in text.splitlines() if t.strip()][:3]

    print(f"\U0001F9ED Planner (retry_count {it}) -> {len(tasks)} tasks"
          + (f'  [addressing: "{prior[:40]}..."]' if prior else ""))
    return {"retry_count": it, "tasks": tasks}


def research(state: ResearchState):
    ctx, srcs = retrieve_context(state["goal"])

    prompt = (
        "Answer ONLY from the context. Be concise (3-4 sentences). "
        "If a task from the plan isn't covered, say so.\n"
        f"Plan: {state['tasks']}\n\nContext:\n{ctx}\n\nGoal: {state['goal']}"
    )
    msg = llm.invoke(prompt).content

    print("\U0001F50E Research -> grounded findings gathered", "| sources:", srcs)
    findings_list = [f.strip("-* ") for f in msg.split('\n') if f.strip()]
    return {"findings": findings_list, "sources": srcs}


def _extract_json(text: str):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0)) if m else {}


def critic(state: ResearchState):

    prompt = (
        "You are a strict reviewer. Score the findings for completeness vs the goal.\n"
        'Return ONLY JSON: {"score": <0..1 float>, "gaps": "<one sentence>"}.\n'
        f"Goal: {state['goal']}\nFindings: {state['findings']}"
    )
    try:
        data = _extract_json(llm.invoke(prompt).content)
        score = float(data.get("score", 0.5))
        gaps = str(data.get("gaps", ""))
    except Exception:
        score, gaps = 0.5, "Could not parse critic output; treat as incomplete."

    print(f"\U0001F9D0 Critic -> quality_score = {round(score,2)}" + (f' | gap: {gaps[:50]}' if gaps else ""))
    return {"quality_score": score, "critique": gaps}



def reporter(state: ResearchState):
    findings_text = "\n".join(state["findings"])
    risks = [s.strip() for s in re.split(r"[;\n]", findings_text) if "risk" in s.lower()]
    confidence = "high" if state["quality_score"] >= 0.8 else "medium"
    report = FinalReport(
        goal=state["goal"],
        summary=findings_text[:300],
        key_findings=[s.strip() for s in re.split(r"[.;\n]", findings_text) if s.strip()][:5] or [findings_text],
        risks=risks,
        sources=state.get("sources", []),
        retry_counts=state["retry_count"],
        confidence=confidence,
    )
    print("\U0001F4DD Reporter -> validated FinalReport")


    key_findings_str = "\n".join(f"- {x}" for x in report.key_findings)

    # To avoid printing empty risks section
    risks_section = ""
    if report.risks:
        risks_str = "\n".join(f"- {x}" for x in report.risks)
        risks_section = f"\n## Risks\n{risks_str}\n"
    sources_str = "\n".join(f"- {x}" for x in report.sources)

    report_markdown = f"""# Final Research Report

## Goal
{report.goal}

## Summary
{report.summary}

## Key Findings
{key_findings_str}
{risks_section}
## Sources
{sources_str}

#### Retry Count: {report.retry_counts}
#### Confidence: {report.confidence}
"""

    return {"report": report_markdown}

