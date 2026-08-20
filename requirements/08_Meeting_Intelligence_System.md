# Project 08 — Meeting Intelligence System

**Team:** 5 · **Duration:** 1 week · **Primary UI:** Streamlit (calls FastAPI) · **Max size:** 50 MB
**Full graduation project — must apply the ENTIRE program stack. See `00_Overview_and_Rules.md`.**

## 1. Title
Meeting Intelligence System — an autonomous agent that turns transcripts into validated, assignable action items and minutes.

## 2. Simple Description
Upload a meeting transcript; a multi-agent system extracts **validated action items** (task, owner, due date, priority), enriches them with context retrieved from past meetings, a critic checks completeness, a human approves before "assigning", and clean Markdown minutes are exported — served behind an API, automated after a meeting file arrives, evaluated against labels, hardened against transcript injection, and cost-profiled.

## 3. Context — Data / Knowledge Base
- **20–40 meeting transcripts** (synthetic/public-style), varied messiness. TXT/Markdown.
- A **roster** (valid owners/teams) + a **past-decisions/context document** for retrieval.
- A **labeled subset** (~10 transcripts) with correct action items, in `data/eval/`.
- **1–2 poisoned transcripts** (injected instructions) for the security thread.

## 4. Required Actions — the full program stack applied to meeting intelligence
Implement **all** layers. Suggested roles: **Ingestor → Extractor → Enricher (retrieval) → Critic → Decision (HITL approval) → Reporter.**

| Program layer (session) | What YOUR project must do |
| --- | --- |
| Structured Outputs — Pydantic (S1) | `ActionItem{task, owner, due_iso, priority, dependencies[], confidence}`; owner validated vs roster; dates normalized; **repair loop**. |
| Knowledge / Retrieval — LlamaIndex (S2) | Index prior meetings/context; retrieve related decisions to enrich items; measure retrieval. |
| Agent Workflow — LangGraph (S3) | Multi-agent graph with a **completeness-critic cycle**, persistent state, and a **HITL** approval before assigning. |
| Interface — Streamlit (S4) | Transcript → action-item table + context → approval; eval/security/cost pages. |
| API Backend — FastAPI (S5) | Async `/extract` endpoint, validated request, called by the UI. |
| Automation — n8n (S6) | On a new transcript file → extract → email the minutes + action items. (Or defend dropping it.) |
| Evaluation thread | Extraction precision/recall + owner-assignment accuracy on the labeled subset. |
| Security thread | Poisoned transcript must not inject fake tasks/owners; content-as-data; before/after. |
| Cost & Observability + TOON | Token/latency budget; **TOON-vs-JSON** on the action-item records. |

Markdown minutes + action-item table export required.

## 5. The Problem
Meetings produce decisions that get lost in walls of text; ad-hoc summaries hallucinate owners and mangle dates. A useful tool must produce **structured, validated, verifiable** action items with owners checked against a real roster and normalized dates — approved by a human, resistant to injected transcripts, and **measured** for completeness.

## 6. Evaluation Criteria (100 points — shared graduation rubric)

| # | Criterion (domain focus) | Points |
| --- | --- | --- |
| 1 | Streamlit app: action items + context + approval | 10 |
| 2 | README: Mermaid of all layers + KB inventory (marks poisoned transcripts) | 8 |
| 3 | Code quality + recommended structure | 6 |
| 4 | `ActionItem` schema (owner/date validation) + repair loop | 8 |
| 5 | LlamaIndex context retrieval measured | 10 |
| 6 | LangGraph completeness-critic + persistence + HITL | 12 |
| 7 | FastAPI `/extract` backend | 8 |
| 8 | n8n post-meeting automation (or defended cut) | 4 |
| 9 | Evaluation: precision/recall + owner accuracy | 8 |
| 10 | Security: transcript injection resistance, before/after | 8 |
| 11 | Cost/observability + TOON on action-item records | 6 |
| 12 | Framework-justification write-up | 4 |
| 13 | Failure-mode analysis | 2 |
| 14 | Live demo & Q&A | 6 |

## 7. Recommended Project Structure
Shared skeleton + domain specifics:
```
data/knowledge_base/   # transcripts (some poisoned), roster, context docs
data/eval/             # 10 labeled transcripts
src/agent/             # ingestor, extractor, enricher, critic, decision, reporter
reports/               # eval, failure-modes, security, cost+TOON, framework matrix
```

## 8. Deliverables & Constraints
- Streamlit (calls FastAPI) · ≤ 50 MB · no secrets.
- Five graduation deliverables in `reports/`; README Mermaid (all layers) + KB inventory (mark poisoned transcripts).
- Unresolved owners/dates must be **flagged**, never fabricated.
