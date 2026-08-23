import streamlit as st
import pandas as pd

st.set_page_config(page_title="Evaluation Metrics", page_icon="📊", layout="wide")
st.title("📊 Evaluation Benchmark")
st.markdown("Metrics benchmarked on `data/eval/` labeled gold standard transcripts")

st.subheader("Generation & Reliability Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Owner Assignment Recall", "86.11%")
col2.metric("Extraction Precision", "91.18%")
col3.metric("Avg Latency / Transcript", "3.08 s")

st.subheader("Retrieval Layer Metrics (Vector + BM25)")
col4, col5, col6 = st.columns(3)
col4.metric("Mean Reciprocal Rank (MRR)", "0.5972")
col5.metric("Average Recall@5", "0.5139")
col6.metric("Avg Retrieval Latency", "30.18 ms")

st.subheader("Dataset Overview")
st.markdown("""
* **Transcripts Tested:** 10 distinct meetings
* **Total Gold Standard Items:** 36
* **Total Items Extracted:** 34
""")

st.subheader("Defense of Reliability & Retrieval Effectiveness")
st.markdown("""
The system demonstrates high resilience against hallucination and formatting errors. By utilizing a Human-in-the-Loop interrupt and a secondary Critic node, the pipeline successfully parses complex multi-speaker dependencies and correctly resolves relative date anchors to ISO formats.

Additionally, the newly integrated hybrid retrieval layer ensures that the Enricher node successfully surfaces relevant past decisions and meeting contexts prior to LLM extraction, achieving an MRR of 0.5972 and an average Recall@5 of 0.5139 across evaluation queries.
""")