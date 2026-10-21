# StartupPulse

Forecasts industry-level startup trends (by founding cohort), estimates an individual
startup's probability of being profitable, and explains both in plain English.
**The models predict; the commentary only explains** (see DECISIONS.md, Decision 6).

## Headline results (details and caveats in DECISIONS.md)
- Forecasting (leave-last-cohort-out): Prophet best, MAE 10.28 vs 14.26 naive; LSTM fails (MAE 40.29); all models have negative R^2.
- Classification (5-fold CV x3): ROC-AUC 0.55-0.58, barely above chance; majority-class accuracy is 0.568.
- The industry-cohort context feature gave no measurable gain (mean AUC change -0.002 to -0.007).

## Architecture
```
CSV -> src/ingest.py -> PostgreSQL -> src/classify.py, src/forecast.py   (modelling)
                                   -> src/service.py  (final model, forecasts, commentary)
                                   -> src/api.py      (FastAPI, X-API-Key auth)
                                   -> app.py          (Streamlit, calls the API over HTTP)
```

## Run it (two terminals, from the project root)
1. Postgres container from Module 1 must be running.
2. `pip3 install -r requirements-app.txt` (plus the Module 2/3 requirements you already have).
3. Terminal A: `STARTUPPULSE_API_KEY=dev-key uvicorn src.api:app --port 8000`
   (first start takes a few seconds: it trains the model and fits 8 Prophet models lazily).
4. Terminal B: `streamlit run app.py` -> opens http://localhost:8501
5. API docs: http://localhost:8000/docs (all endpoints except /health need header `X-API-Key`).

## Tests you can run
- `curl localhost:8000/health` -> `{"status":"ok"}`
- `curl -H "X-API-Key: dev-key" localhost:8000/startups/Startup_1`
- Wrong key -> HTTP 401.

## Docker (untested)
`docker compose up --build` after making `DB_URL` in `src/classify.py` read
`os.environ.get("DATABASE_URL", "<your current localhost URL>")`. The compose file points the
containers at the host's Postgres via `host.docker.internal`.

## Limits
500 startups, likely simplified data; `Profitable` is a static snapshot; cohort forecasts use 7 points per industry;
a single shared API key is demo-grade auth, not production security. Not investment advice.
