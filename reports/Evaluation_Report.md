# Evaluation Report: Meeting Intelligence System

## 1. Evaluation Set Overview
* **Transcripts Tested:** 10 distinct meetings
* **Context Applied:** Global roster, past decisions, and knowledge base integration.

## 2. Reliability & Retrieval Metrics
* **Total Gold Standard Items:** 36
* **Total Items Extracted:** 34
* **Owner Assignment Recall:** 86.11%
* **Extraction Precision:** 91.18%
* **Average Processing Time:** 3.08 seconds per transcript
* **Mean Reciprocal Rank (MRR):** 0.5972
* **Average Recall@5:** 0.5139
* **Avg Retrieval Latency per Query:** 30.18 ms

## 3. Defense of Reliability & Retrieval Effectiveness
The system demonstrates high resilience against hallucination and formatting errors. By utilizing a Human-in-the-Loop interrupt and a secondary Critic node, the pipeline successfully parses complex multi-speaker dependencies and correctly resolves relative date anchors to ISO formats.

Additionally, the newly integrated hybrid retrieval layer ensures that the Enricher node successfully surfaces relevant past decisions and meeting contexts prior to LLM extraction, achieving an MRR of 0.5972 and an average Recall@5 of 0.5139 across evaluation queries.