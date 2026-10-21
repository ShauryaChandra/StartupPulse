# StartupPulse - Roadmap

## V1 (this submission)
- Data pipeline: CSV -> PostgreSQL, verified (500 rows, 8 industries, 5 regions).
- Forecasting: 5 models on industry x 5-year-cohort mean revenue (Prophet best).
- Classification: 4 models x 2 feature sets, repeated CV, ablation of the industry-cohort feature.
- Commentary layer: template-based, explains model outputs, never changes them.
- FastAPI backend with API-key auth; Streamlit frontend (lookup, forecast, custom startup).
- Docker files provided (untested).

## V2 (not built)
- Swap the template commentary for a real LLM call (same function signature).
- React frontend, interactive Plotly charts (deferred, Decision 1).
- Recompute the trend feature inside each CV fold (removes feature-level information sharing).
- Longitudinal funding data (true per-year forecasting instead of cohort bins).
- Per-user accounts instead of one shared API key; model/version tracking.
- Secondary task: Exit Status (Private / Acquired / IPO) classification.
