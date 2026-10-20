"""Streamlit UI: chat with the analytics agent + standalone A/B test evaluator."""
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from agent import db
from agent.ab_test import evaluate_ab_test
from data.generate_sample_data import generate

load_dotenv()
st.set_page_config(page_title="AI Analytics Agent", page_icon="📊", layout="wide")

if not db.DB_PATH.exists():
    with st.spinner("Generating sample database..."):
        generate()

SAMPLES = [
    "What is monthly completed revenue, and how is it trending?",
    "Which acquisition channel has the highest average order value?",
    "Top 5 countries by total revenue — show a bar chart.",
    "Did the checkout_redesign experiment win? Is it significant?",
    "Compare the pricing_banner experiment results.",
]


def render(result):
    st.markdown(result.answer)
    for r in result.ab_results:
        c = st.columns(4)
        c[0].metric("Control", f"{r.rate_control:.2%}")
        c[1].metric("Treatment", f"{r.rate_treatment:.2%}", f"{r.lift:+.1%} lift")
        c[2].metric("p-value", f"{r.p_value:.4f}")
        c[3].metric(f"{r.confidence:.0%} CI (abs)", f"{r.ci_low:+.2%} to {r.ci_high:+.2%}")
    for fig in result.figures:
        st.plotly_chart(fig, use_container_width=True)
    with st.expander("SQL & data"):
        for q, df in zip(result.queries, result.dataframes):
            st.code(q, language="sql")
            st.dataframe(df, use_container_width=True)


chat_tab, ab_tab = st.tabs(["💬 Ask your data", "🧪 A/B test evaluator"])

with st.sidebar:
    st.header("Database schema")
    st.code(db.get_schema(), language="text")

with chat_tab:
    st.title("AI Analytics Agent")
    if not os.getenv("ANTHROPIC_API_KEY"):
        st.warning("Set ANTHROPIC_API_KEY in `.env` to enable the agent. The A/B tab works without it.")
    else:
        from agent.agent import AnalyticsAgent

        if "agent" not in st.session_state:
            st.session_state.agent, st.session_state.log = AnalyticsAgent(), []
        cols = st.columns(len(SAMPLES))
        clicked = next((s for s, c in zip(SAMPLES, cols) if c.button(s, use_container_width=True)), None)
        for q, res in st.session_state.log:
            with st.chat_message("user"):
                st.write(q)
            with st.chat_message("assistant"):
                render(res)
        question = st.chat_input("Ask a question about orders, users or experiments...") or clicked
        if question:
            with st.chat_message("user"):
                st.write(question)
            with st.chat_message("assistant"), st.spinner("Analyzing..."):
                res = st.session_state.agent.ask(question)
                render(res)
            st.session_state.log.append((question, res))

with ab_tab:
    st.subheader("Two-proportion z-test")
    a, b = st.columns(2)
    n_c = a.number_input("Control users", 1, value=10000)
    x_c = a.number_input("Control conversions", 0, value=1000)
    n_t = b.number_input("Treatment users", 1, value=10000)
    x_t = b.number_input("Treatment conversions", 0, value=1100)
    conf = st.select_slider("Confidence level", [0.90, 0.95, 0.99], value=0.95)
    if st.button("Evaluate", type="primary"):
        try:
            r = evaluate_ab_test(int(x_c), int(n_c), int(x_t), int(n_t), conf)
            (st.success if r.significant else st.info)(r.summary())
            st.dataframe(pd.DataFrame([r.to_dict()]).T.rename(columns={0: "value"}))
        except ValueError as e:
            st.error(str(e))
