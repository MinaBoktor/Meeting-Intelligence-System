import streamlit as st
import pandas as pd

st.set_page_config(page_title="Evaluation Metrics", page_icon="📊", layout="wide")
st.title("📊 Evaluation Benchmark")
st.markdown("Metrics benchmarked on `data/eval/` labeled gold standard transcripts")

col1, col2, col3 = st.columns(3)
col1.metric("Owner Assignment Recall", "86.11%")
col2.metric("Extraction Precision", "91.18%")
col3.metric("Avg Latency / Transcript", "2.97 s")

st.subheader("Dataset Overview")
st.markdown("""
* **Transcripts Tested:** 10 distinct meetings
* **Total Gold Standard Items:** 36
* **Total Items Extracted:** 34
""")