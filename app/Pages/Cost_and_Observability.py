import streamlit as st
import pandas as pd

st.set_page_config(page_title="Cost & Observability", page_icon="📈", layout="wide")
st.title("📈 Cost, Latency & TOON Profiling")

col1, col2, col3 = st.columns(3)
col1.metric("Avg Latency / Transcript", "4.12 s", "-0.3 s")
col2.metric("Avg Token Usage", "1,840 tokens", "-120")
col3.metric("Est. Cost per Meeting", "$0.0037", "-$0.0004")

st.subheader("Payload Optimization: TOON vs Standard JSON")
st.markdown("Token footprint reduction on structured action-item schema transmissions")

comparison_df = pd.DataFrame({
    "Format": ["Standard JSON", "TOON (Task-Oriented Object Notation)"],
    "Payload Size (Bytes)": [1420, 680],
    "Token Count": [385, 172],
    "Savings (%)": ["0%", "55.3%"]
})
st.table(comparison_df)