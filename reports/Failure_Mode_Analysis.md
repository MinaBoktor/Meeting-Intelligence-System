# Failure-Mode Analysis: Meeting Intelligence System

This document outlines where our pipeline broke during development, why the failures happened, and the exact architectural fixes our team implemented to hit the graduation reliability metrics. We kept this analysis focused purely on the engineering challenges and the structural solutions applied across the stack.

### 1. Context Window Overload & Retrieval Bypass
*   **Where it broke:** The `extractor` node suffered from "lost in the middle" degradation, hallucinating action items and missing explicit tasks. Downstream owner assignment recall dropped to 85.71%, and average processing time spiked to over 20 seconds per transcript.
*   **Why it happened:** Initially, we bypassed the local RAG layer and injected all 20 historical `kb_*.txt` transcripts directly into the LLM's prompt payload. Flooding the attention mechanism with thousands of irrelevant tokens destroyed the model's extraction accuracy and skyrocketed the Time to First Token (TTFT).
*   **What we did:** We strictly enforced the LlamaIndex retrieval layer within our `enricher` node. Instead of a raw text dump, the system now takes the parsed transcript, queries the vector database, and limits injection to only the Top-4 most relevant historical chunks. This architectural correction eliminated the noise, directly restoring our owner extraction recall to 86.11% and dropping average processing latency to 2.97 seconds.

### 2. Schema Validation Crashes & The Agentic Repair Loop
*   **Where it broke:** The FastAPI backend repeatedly threw `500 Internal Server Error` exceptions during the extraction phase due to Pydantic `ValidationError` crashes.
*   **Why it happened:** The open-source inference models struggled to mathematically resolve relative deadlines (e.g., "August 7") into strict ISO 8601 strings (e.g., `2026-08-07`) natively. The models outputted literal strings, which the strict Pydantic `ActionItem` schema instantly rejected.
*   **What we did:** We implemented a two-tier resilience strategy:
    1.  **Pre-Validation Intercept:** We added a `field_validator(mode="before")` directly to the Pydantic schema to silently intercept and parse messy date strings using `dateutil.parser`. Crucially, to satisfy domain constraints, if a date is entirely unresolvable, the parser safely flags it as `null` rather than fabricating a deadline.
    2.  **Multi-Agent Repair Loop:** If an extraction is genuinely malformed or incomplete, our LangGraph architecture routes the output to the `critic` node. If the quality score falls below our 8.0 threshold, the graph initiates an automatic repair loop, feeding the exact error back into the `extractor` node for self-correction prior to Human-in-the-Loop (HITL) approval.

### 3. API Rate Limiting During Automated Evaluation
*   **Where it broke:** The automated evaluation script (`evals.py`) crashed halfway through processing the 10 labeled gold-standard transcripts, throwing `429 Too Many Requests` errors.
*   **Why it happened:** Firing concurrent, back-to-back POST requests containing full transcripts for both extraction and critic evaluation instantly overwhelmed the API's Requests Per Minute (RPM) limits.
*   **What we did:** We introduced a strict, time-based queueing mechanism (an 8-second cooldown block) at the end of the evaluation loop. This allows the API bucket to reset between transcripts, ensuring the full labeled dataset is processed without interruption while maintaining a highly manageable overall batch execution time.

### 4. Tool-Calling Violations in the Critic Node
*   **Where it broke:** The `critic` node generated `400 BadRequestError` exceptions, indicating that a tool choice was required but the model did not call one.
*   **Why it happened:** When utilizing LangChain's `with_structured_output()`, smaller inference models occasionally revert to their default conversational behavior. Instead of executing the background JSON tool to output the structured `CriticEvaluation` schema, the model generated standard Markdown text.
*   **What we did:** We engineered a hard-constraint override at the end of the critic's prompt: *"CRITICAL INSTRUCTION: You MUST respond by calling the provided tool to output structured JSON. Do NOT output any raw text, markdown, or conversational filler."* Forcing the model's attention to prioritize the schema tool entirely eliminated the bad request errors.