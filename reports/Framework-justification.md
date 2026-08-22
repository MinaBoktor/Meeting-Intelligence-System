# Framework-Justification Write-Up & Comparison Matrix

This document provides a running comparison matrix of the architectural choices our team made across the program's mandatory layers. For each component of the Meeting Intelligence System, we evaluated multiple frameworks before committing to the final stack.

## Architecture Comparison Matrix

| Program Layer | Chosen Framework | Rejected Alternative | Primary Justification for Choice |
| :--- | :--- | :--- | :--- |
| **Structured Outputs** | **Pydantic** | Raw JSON parsing / Regex | Guaranteed schema validation for action items. Pre-validation hooks (`field_validator`) allowed us to intercept and correct relative dates to ISO 8601 without triggering API crashes. |
| **Knowledge / Retrieval** | **LlamaIndex** | Full-context payload dumping | Dumping raw historical transcripts into the prompt caused severe "Lost in the Middle" degradation and high latency. LlamaIndex provided measured semantic chunking, restoring our extraction recall to 94.44%. |
| **Agent Workflow** | **LangGraph** | Sequential LangChain / AutoGen | We required a stateful, cyclic execution graph to implement the multi-agent `critic` repair loop and the native `interrupt()` API for our Human-in-the-Loop (HITL) approval step. |
| **Interface** | **Streamlit** | React / Custom Next.js | Allowed the team to build a multi-page interactive UI strictly in Python within the 1-week time constraint, easily surfacing the agent's retrieved context and reasoning alongside the final table. |
| **API Backend** | **FastAPI** | Flask / Django | Native asynchronous request handling and seamless integration with our Pydantic validation schemas. It provided a robust `/extract` endpoint capable of managing concurrent LLM network calls. |
| **Automation** | **n8n** | Python Cron Jobs / Airflow | Visual workflow mapping made it highly efficient to link our FastAPI endpoints to post-meeting triggers, automatically emailing the generated Markdown minutes and action items once approved. |

## Deep-Dive Rationale

### 1. LangGraph vs. Sequential Pipelines (Workflow Layer)
A standard sequential chain could not handle the complexity of the Meeting Intelligence System. The core requirement was a completeness-critic cycle. LangGraph was selected because it natively supports cyclic routing: if the `critic` node scores an extraction below 8.0, the graph routes state back to the `extractor` for a repair loop. Furthermore, LangGraph's built-in checkpointer enabled the crucial `interrupt()` function to pause the backend until the human user approved the tasks in the UI.

### 2. LlamaIndex vs. Brute-Force Prompting (Retrieval Layer)
During initial testing, we attempted to pass the entire 20-file knowledge base directly into the prompt payload. This was rejected because it broke the LLM's attention mechanism (dropping recall to 85%) and triggered 429 rate limits. LlamaIndex was chosen to embed the past decisions and roster. By retrieving only the Top-K relevant historical chunks per query, we minimized token expenditure, avoided hallucinating owners, and maintained sub-4-second inference times.

### 3. FastAPI + Pydantic vs. Flask (API & Validation Layers)
Flask was rejected due to its synchronous nature and reliance on manual JSON validation. FastAPI was chosen because it is built entirely around Pydantic. This allowed us to define our `ActionItem` constraint (task, owner, due_iso, priority) once, and automatically enforce it at the API boundary. The async nature of FastAPI also ensured that the Streamlit UI did not hang while waiting for the LLM to finish processing the transcript.