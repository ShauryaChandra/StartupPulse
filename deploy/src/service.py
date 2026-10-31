"""
StartupPulse - shared service layer.

Reuses the real functions from classify.py (data loading, trend feature,
pipeline, models) and adds: out-of-fold profitability probabilities, a
cohort-level Prophet forecast, and the commentary text. Both the FastAPI
backend (api.py) and any script call these functions, so the logic lives once.

The commentary layer only EXPLAINS model outputs (Decision 6); nothing here
feeds text back into a prediction.
"""
import functools
import logging

import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from classify import (FEATURE_SETS, SEED, add_trend_feature, build_pipeline,
                      load_data, make_models)
import commentary

logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
logging.getLogger("prophet").setLevel(logging.WARNING)

# Decision 14: the context feature gave no gain, so the served model uses the
# firm-level (baseline) features. Logistic Regression: tied-best AUC (0.580),
# and its probabilities are the simplest to explain.
FEATURES = FEATURE_SETS["baseline (firm-level only)"]
MODEL_NAME = "LogisticRegression"
COHORT_STEP = 5

# Headline numbers from Decision 14, exposed through the API so the UI can
# show the model's real strength next to every prediction.
MODEL_INFO = {
    "model": MODEL_NAME,
    "features": FEATURES,
    "cv_roc_auc": 0.580,
    "cv_accuracy": 0.574,
    "majority_baseline_accuracy": 0.568,
    "note": ("Weak signal: ROC-AUC 0.50 is a coin flip. Context feature "
             "(revenue_vs_trend) gave no measurable gain (Decision 14)."),
}


@functools.lru_cache(maxsize=1)
def get_data() -> pd.DataFrame:
    return add_trend_feature(load_data())


def _new_pipeline():
    return build_pipeline(make_models()[MODEL_NAME], FEATURES)


@functools.lru_cache(maxsize=1)
def get_model():
    """Final model trained on all 500 rows (used for startups not in the data)."""
    df = get_data()
    pipe = _new_pipeline()
    pipe.fit(df[FEATURES], df["profitable"].astype(int))
    return pipe


@functools.lru_cache(maxsize=1)
def get_oof_probs() -> pd.Series:
    """Out-of-fold P(profitable) for every known startup. A model scoring rows
    it was trained on would look better than it is, so known startups get the
    probability from a fold that did NOT see them."""
    df = get_data()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    probs = cross_val_predict(_new_pipeline(), df[FEATURES],
                              df["profitable"].astype(int), cv=cv,
                              method="predict_proba")[:, 1]
    return pd.Series(probs, index=df.index)


def industries() -> list:
    return sorted(get_data()["industry"].unique().tolist())


def list_startups(industry: str = None, limit: int = 50) -> list:
    df = get_data()
    if industry:
        df = df[df["industry"].str.lower() == industry.lower()]
    return df["name"].head(limit).tolist()


def cohort_series(industry: str) -> pd.Series:
    df = get_data()
    d = df[df["industry"].str.lower() == industry.lower()]
    if d.empty:
        raise KeyError(industry)
    return d.groupby("cohort_bin")["revenue_musd"].mean().sort_index()


@functools.lru_cache(maxsize=None)
def _forecast_cached(industry_key: str) -> dict:
    from prophet import Prophet
    s = cohort_series(industry_key)
    train = pd.DataFrame({
        "ds": pd.to_datetime([f"{int(c)}-01-01" for c in s.index]),
        "y": s.values,
    })
    m = Prophet(yearly_seasonality=False, weekly_seasonality=False,
                daily_seasonality=False)
    m.fit(train)
    nxt = int(s.index.max()) + COHORT_STEP
    pred = m.predict(pd.DataFrame({"ds": [pd.Timestamp(f"{nxt}-01-01")]})).iloc[0]
    canonical = get_data().loc[
        get_data()["industry"].str.lower() == industry_key, "industry"].iloc[0]
    return {
        "industry": canonical,
        "model": "Prophet",
        "history": [{"cohort": int(c), "revenue_musd": round(float(v), 2)}
                    for c, v in s.items()],
        "forecast": {"cohort": nxt,
                     "revenue_musd": round(float(pred["yhat"]), 2),
                     "lower": round(float(pred["yhat_lower"]), 2),
                     "upper": round(float(pred["yhat_upper"]), 2)},
    }


def forecast_industry(industry: str) -> dict:
    cohort_series(industry)  # raises KeyError for unknown industries
    return _forecast_cached(industry.lower())


def _commentary(name, industry, cohort, prob, rvt) -> str:
    f = forecast_industry(industry)
    last = f["history"][-1]
    return commentary.build_commentary(
        name=name, industry=f["industry"], cohort=cohort, prob=prob,
        revenue_vs_trend=rvt,
        last_cohort=last["cohort"], last_value=last["revenue_musd"],
        forecast_cohort=f["forecast"]["cohort"],
        forecast_value=f["forecast"]["revenue_musd"],
        forecast_model=f["model"])


def analyze_known(name: str) -> dict:
    df = get_data()
    row = df[df["name"].str.lower() == name.lower()]
    if row.empty:
        raise KeyError(name)
    idx = row.index[0]
    r = row.iloc[0]
    prob = float(get_oof_probs().loc[idx])
    return {
        "name": r["name"], "industry": r["industry"], "region": r["region"],
        "year_founded": int(r["year_founded"]), "cohort": int(r["cohort_bin"]),
        "revenue_musd": float(r["revenue_musd"]),
        "revenue_vs_trend": round(float(r["revenue_vs_trend"]), 2),
        "actual_profitable": bool(r["profitable"]),
        "prob_profitable": round(prob, 4),
        "probability_kind": "out-of-fold (this startup was not in the training fold)",
        "commentary": _commentary(r["name"], r["industry"], int(r["cohort_bin"]),
                                  prob, float(r["revenue_vs_trend"])),
    }


def analyze_custom(p: dict) -> dict:
    """p: funding_rounds, funding_amount_musd, valuation_musd, revenue_musd,
    employees, market_share_pct, year_founded, industry, region (+ optional name)."""
    df = get_data()
    match = df.loc[df["industry"].str.lower() == p["industry"].lower(), "industry"]
    if match.empty:
        raise KeyError(p["industry"])
    industry = match.iloc[0]
    row = pd.DataFrame([{**p, "industry": industry}])
    prob = float(get_model().predict_proba(row[FEATURES])[:, 1][0])
    cohort = (int(p["year_founded"]) // COHORT_STEP) * COHORT_STEP
    peers = df[(df["industry"] == industry) & (df["cohort_bin"] == cohort)]
    rvt = float(p["revenue_musd"] - peers["revenue_musd"].mean()) if len(peers) else 0.0
    name = p.get("name") or "Your startup"
    return {
        "name": name, "industry": industry, "cohort": cohort,
        "revenue_vs_trend": round(rvt, 2),
        "prob_profitable": round(prob, 4),
        "probability_kind": "final model trained on all 500 startups",
        "commentary": _commentary(name, industry, cohort, prob, rvt),
    }
