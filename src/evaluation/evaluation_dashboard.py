# src/evaluation/evaluation_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

st.set_page_config(
    page_title="DocuMind Evaluation Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 DocuMind Evaluation Dashboard")

# Load results from JSON file
results_file = "results/evaluation_results.json"

if not os.path.exists(results_file):
    st.error(f"❌ No results found. Run `python scripts/run_evaluation.py` first.")
    st.stop()

with open(results_file, 'r') as f:
    results = json.load(f)

# Metrics overview
st.header("Latest Evaluation Results")

col1, col2, col3, col4 = st.columns(4)

faithfulness = results.get('faithfulness', 0)
answer_relevancy = results.get('answer_relevancy', 0)
answer_correctness = results.get('answer_correctness', 0)
average_score = results.get('average_score', 0)
passed = results.get('passed', False)

col1.metric(
    "Faithfulness",
    f"{faithfulness:.3f}",
    delta=f"{'✓' if faithfulness >= 0.70 else '✗'} Target: 0.70"
)
col2.metric(
    "Answer Relevancy",
    f"{answer_relevancy:.3f}",
    delta=f"{'✓' if answer_relevancy >= 0.80 else '✗'} Target: 0.80"
)
col3.metric(
    "Answer Correctness",
    f"{answer_correctness:.3f}",
    delta=f"{'✓' if answer_correctness >= 0.70 else '✗'} Target: 0.70"
)
col4.metric(
    "Average Score",
    f"{average_score:.3f}",
    delta="Overall"
)

# Status indicator
st.divider()
if passed:
    st.success("✅ Quality Gates: PASSING - Deployment allowed")
else:
    st.error("❌ Quality Gates: FAILING - Deployment blocked")

# Gauge chart for overall score
st.header("Overall Quality Score")

fig = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=average_score * 100,
    domain={'x': [0, 1], 'y': [0, 1]},
    title={'text': "Average Score (%)"},
    delta={'reference': 75, 'increasing': {'color': "green"}},
    gauge={
        'axis': {'range': [0, 100]},
        'bar': {'color': "darkblue"},
        'steps': [
            {'range': [0, 50], 'color': "red"},
            {'range': [50, 70], 'color': "orange"},
            {'range': [70, 85], 'color': "yellow"},
            {'range': [85, 100], 'color': "green"}
        ],
        'threshold': {
            'line': {'color': "black", 'width': 4},
            'thickness': 0.75,
            'value': 75
        }
    }
))
fig.update_layout(height=300)
st.plotly_chart(fig, use_container_width=True)

# Bar chart comparing metrics
st.header("Metrics Comparison")

metrics_df = pd.DataFrame({
    'Metric': ['Faithfulness', 'Answer Relevancy', 'Answer Correctness'],
    'Score': [faithfulness, answer_relevancy, answer_correctness],
    'Threshold': [0.70, 0.80, 0.70]
})

fig2 = go.Figure()
fig2.add_trace(go.Bar(
    name='Score',
    x=metrics_df['Metric'],
    y=metrics_df['Score'],
    marker_color=['green' if s >= t else 'red' for s, t in zip(metrics_df['Score'], metrics_df['Threshold'])]
))
fig2.add_trace(go.Scatter(
    name='Threshold',
    x=metrics_df['Metric'],
    y=metrics_df['Threshold'],
    mode='markers',
    marker=dict(size=15, symbol='line-ew', line=dict(width=3, color='black'))
))
fig2.update_layout(
    yaxis_range=[0, 1],
    yaxis_title="Score",
    showlegend=True
)
st.plotly_chart(fig2, use_container_width=True)

# Per-question breakdown if available
if 'per_question' in results and results['per_question']:
    st.header("Per-Question Analysis")

    per_q_df = pd.DataFrame(results['per_question'])

    # Show table
    display_cols = ['question', 'faithfulness', 'answer_relevancy', 'answer_correctness']
    available_cols = [c for c in display_cols if c in per_q_df.columns]

    if available_cols:
        st.dataframe(per_q_df[available_cols], use_container_width=True)

# Footer
st.divider()
st.caption("📁 Results loaded from: " + results_file)
st.caption("Run `python scripts/run_evaluation.py` to generate new results")
