# AI Analytics Agent

Ask business questions in plain English. A Claude-powered LangChain agent writes SQL, runs it
(read-only), builds charts, and evaluates A/B tests — turning hours of EDA and KPI reporting into minutes.

**Stack:** Python · LangChain · Claude · SQLite · Plotly · Streamlit

## Quick start
```bash
pip install -r requirements.txt
cp .env.example .env            # add your ANTHROPIC_API_KEY
python data/generate_sample_data.py   # builds data/analytics.db (auto-built by the app if missing)
streamlit run app.py
pytest                          # unit tests (no API key needed)
```

## How it works
```
question ─► Claude (tool-calling loop) ─┬─► run_sql      read-only, single-statement SELECT, row-capped
                                        ├─► make_chart   Plotly bar/line/scatter/pie/histogram/box
                                        └─► ab_test      two-proportion z-test, CI, lift
         ◄─ answer + SQL + data + charts + A/B metrics ─► Streamlit UI
```
- **Self-correcting SQL:** query errors are returned to the model, which fixes and retries.
- **Safety:** DB opened in `mode=ro`; validator blocks writes, PRAGMA, multi-statement SQL.
- **A/B evaluator** (`agent/ab_test.py`): pooled-SE z-test, unpooled 95% CI on the absolute difference,
  relative lift, p-value. Also available as a no-API-key tab in the UI.

## Sample data
Synthetic e-commerce DB: `users`, `orders`, `experiments`. `checkout_redesign` has a real lift
(10.0% → 11.8%); `pricing_banner` has none — a good test of whether the agent calls significance correctly.

## Try asking
- "What is monthly completed revenue, and how is it trending?"
- "Which acquisition channel has the highest average order value?"
- "Did the checkout_redesign experiment win? Is it significant?"

## Swap in your own data
Point `DB_PATH` in `agent/db.py` at any SQLite file; the schema is introspected automatically.
