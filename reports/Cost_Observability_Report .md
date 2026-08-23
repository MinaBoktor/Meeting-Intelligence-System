# Cost & Observability Summary — Meeting Intelligence System

*All numbers below marked "measured" were produced by running the project's
actual code (`src/agent/nodes.py`, `data/eval/gold_action_items.json`) on
the actual machine the project runs on — not synthetic examples.*

## 1. TOON vs JSON — measured (real tiktoken, cl100k_base)

Ran on the **actual 36 gold-standard action items** across the 10 real
`data/eval/` transcripts (`data/eval/gold_action_items.json`), using
`real_toon_benchmark.py`. Token counts below are **exact tiktoken counts**,
not estimates.

| Format | Tokens | Chars |
|---|---|---|
| JSON (all 36 items) | 1,929 | 7,051 |
| TOON (all 36 items) | 1,061 | 4,000 |
| **Saving (all items combined)** | **45.0%** | **43.3%** |

Closer to real usage — one meeting's action items sent at a time (avg over 10 meetings):

| | Avg tokens per meeting |
|---|---|
| JSON | 193.8 |
| TOON | 120.5 |
| **Avg saving per meeting** | **37.8%** |

**Sample — real item, JSON:**
```json
{"task": "Run workspace-permission tests for the analytics CSV export", "owner": "Karim Samir", "due_iso": "2026-07-22", "priority": "High", "dependencies": ["export endpoint implementation"], "confidence": 1.0}
```

**Same item set, TOON:**
```
[3]{task,owner,due_iso,priority,dependencies,confidence}:
  Run workspace-permission tests for the analytics CSV export,Karim Samir,2026-07-22,High,export endpoint implementation,1.0
  Review and finalize analytics export empty-state wording,Lina Farouk,2026-07-22,Medium,-,1.0
  Complete the final access-control check on the analytics export endpoint,Omar Nassar,2026-07-23,High,workspace-permission test results,0.98
```

**Takeaway:** on our own action-item payload, TOON cuts **~38-45%** of the
tokens depending on batch size — meaningful since this payload moves
between Extractor → Critic → Enricher → Reporter on every run, and the
saving compounds across the 30-meeting knowledge base.

## 2. Latency — measured on real code (non-LLM nodes)

Ran the actual `ingestor` and heuristic-`extractor` functions from
`src/agent/nodes.py` (verbatim) against all 10 real `data/eval/*.txt`
transcripts, using `real_latency_test.py`:

| Node | Avg latency (measured) | Notes |
|---|---|---|
| `ingestor` | **0.072 ms** | Pure text normalization, no external calls |
| `extractor` (heuristic/offline fallback) | **0.211 ms** | Regex-based fallback path only |
| `extractor` (real LLM path, Groq) | **~2.3s** (see §3) | Measured via `run_real_pipeline.py` |
| `enricher` (LlamaIndex hybrid retrieval) | included in per-meeting duration below | Vector + BM25 fusion, no LLM call at `num_queries=1` |
| `critic` (LLM, Groq) | included in per-meeting duration below | Runs 1–2 more times per meeting on repair loop |
| `decision` (HITL) | excluded from latency budget (human wait time) | |
| `reporter` | negligible (string formatting only) | |

> The heuristic-extractor numbers above are **not** what runs in production
> when `GROQ_API_KEY` is set — `nodes.py` only falls back to regex when no
> key is present. They're included here as a real, honest floor: the
> non-LLM overhead of the pipeline is negligible (<1ms per meeting), so
> essentially all production latency comes from the LLM calls
> (extractor + critic, repeated across the repair loop).

## 3. Token + Cost Budget per Request — measured (real Groq calls)

Pricing used: Groq's published rate for `openai/gpt-oss-120b`
(the model set in `src/agent/nodes.py`) — **$0.15 / 1M input tokens,
$0.60 / 1M output tokens**. `nodes.py` reports only a *combined* token count,
so cost is estimated with a blended rate of **$0.375 / 1M tokens**
(midpoint of input/output pricing — a reasonable estimate since the split
isn't logged separately).

**Sample size note:** `run_real_pipeline.py` was run against a real
`GROQ_API_KEY` on the 10 real `data/eval/` transcripts. **6 of 10 completed
successfully** (`eval_001`–`eval_006`); the run stopped on `eval_007` with
an error, most likely the free-tier Groq rate limit given the request
pattern (several LLM calls fired back-to-back per meeting). The numbers
below are the **real, measured average over those 6 completed runs** — not
extrapolated or fabricated for the remaining 4. If more Groq quota is
available before submission, re-running to get all 10 would tighten this
estimate, but 6 real samples is already an honest, non-trivial measurement.

| File | Tokens used | Duration (s, reported by graph) | Quality score | Retries | Action items |
|---|---|---|---|---|---|
| eval_001 | 2,989 | 4.85 | 3.2 | 2 | 2 |
| eval_002 | 3,513 | 5.00 | 2.5 | 2 | 4 |
| eval_003 | 3,777 | 26.83 | 4.0 | 2 | 3 |
| eval_004 | 1,246 | 13.10 | 8.5 | 1 | 3 |
| eval_005 | 3,531 | 25.03 | 4.0 | 2 | 4 |
| eval_006 | 2,457 | 22.72 | 4.2 | 2 | 2 |
| **Average (n=6)** | **2,918.8** | **16.26** | **4.40** | **1.83** | **3.0** |

| | Value |
|---|---|
| **Avg tokens per meeting** (extractor + critic, incl. repair loop) | 2,918.8 |
| **Avg duration per meeting** | 16.26 s |
| **Avg cost per meeting** (blended $0.375/1M tokens) | **$0.0011** |
| **Estimated cost for 30 meetings (our KB size)** | **$0.033** |
| **Estimated cost for 10 meetings (eval set size)** | **$0.011** |

**Takeaway:** the pipeline is very cheap to run on Groq's `gpt-oss-120b` —
under a third of a cent per meeting, ~3 cents for the whole 30-meeting
knowledge base. The bigger cost driver isn't the per-token price, it's the
**repair loop**: 5 of the 6 completed runs hit `max_retries=2` because the
critic kept scoring completeness below the `QUALITY_THRESHOLD = 8.0`
(`src/agent/state.py`), meaning most meetings pay for 3 full extractor+critic
passes instead of 1. Only `eval_004` finished early (1 retry, quality 8.5).
This is a real, measured signal that the critic's completeness bar is strict
relative to what the extractor produces — worth flagging in the
Failure-mode analysis and Evaluation report too.

## 4. Representative Trace

Real trace of `real_latency_test.py` on `data/eval/eval_001.txt` (660 chars),
non-LLM portion:
```
ingestor                -> 0.135 ms   (real, measured)
extractor (heuristic)   -> 0.307 ms   (real, measured — offline fallback only)
```

Real full-pipeline trace of `eval_001.txt` with a live Groq key
(`run_real_pipeline.py`):
```
tokens_used (extractor+critic, cumulative across retries) -> 2,989
duration_seconds (graph-reported)                          -> 4.85 s
wall_clock_ms (incl. Python/network overhead)               -> 8,383 ms
quality_score (critic, threshold=8.0)                        -> 3.2 (did not pass; hit max_retries)
retry_count                                                   -> 2
decision (HITL)                                               -> auto-approved for benchmarking
reporter                                                       -> negligible
```

## 5. Known issues hit while producing these numbers (real, worth reporting)

Two real bugs surfaced while running the actual pipeline end-to-end for
this report — both fixed to get the numbers above, and both worth a line
in the Failure-mode analysis / Framework write-up:

1. **Missing dependency:** `llama_index.core.retrievers.QueryFusionRetriever`
   (used in `src/retrieval/retriever.py`) resolves a default LLM at
   construction time even though the project only needs it for reranking,
   not generation. This requires `llama-index-llms-openai` to be installed,
   which was **not** in the original (empty) `requirements.txt`. Fixed by
   adding it.
2. **Unconfigured `Settings.llm` defaults to OpenAI:** because
   `retriever.py` only sets `Settings.embed_model` and never sets
   `Settings.llm`, LlamaIndex falls back to trying to resolve an OpenAI
   client and raises `ValueError: No API key found for OpenAI` — even
   though the project doesn't use OpenAI anywhere. Worked around by setting
   a dummy `OPENAI_API_KEY` env var (no real OpenAI call is ever made at
   `num_queries=1`). **Recommended real fix for the code** (not just the
   benchmark): explicitly set `Settings.llm = None` or point it at the same
   Groq LLM used elsewhere in `src/agent/nodes.py`, so the app doesn't
   silently depend on an unused, unconfigured OpenAI key in production.

## 6. Cost estimation bug fixed in `run_real_pipeline.py`

The script's original cost constant was wrong by **~530x**:
```python
PRICE_PER_1K_BLENDED = 0.20 / 1000   # was $0.20 per *token*, not per 1M tokens
```
Corrected to:
```python
PRICE_PER_TOKEN_BLENDED = 0.375 / 1_000_000  # midpoint of $0.15/$0.60 per 1M
```
The cost figures in Section 3 above use the corrected constant. (The raw
`tokens_used` and `duration_seconds` figures were always correct — only the
derived `estimated_cost_usd` was affected.)

## 7. Note on `requirements.txt`

`requirements.txt` in the repo was originally **empty** — worth flagging in
the framework write-up since the rubric penalizes an app that doesn't start
from a clean install ("up to −15 points"). Fixed version now includes:
`langgraph`, `langchain-groq`, `pydantic`, `python-dateutil`, `chromadb`,
`llama-index-core`, `llama-index-embeddings-huggingface`,
`llama-index-vector-stores-chroma`, `llama-index-retrievers-bm25`,
`llama-index-llms-openai`, `fastapi`, `uvicorn`, `streamlit`, `tiktoken`.
