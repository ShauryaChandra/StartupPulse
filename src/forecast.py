"""
StartupPulse - Module 2: industry cohort-trend forecasting

Forecasts the LEVEL of average Revenue (M USD) per Industry x 5-Year
Founding-Cohort bin (not growth directly - see DECISIONS.md Decision 4
update, Oct 12, for why).

Evaluation: leave-last-cohort-out, pooled across industries.
Each model trains on cohorts 1990-2015 (6 points) per industry and
predicts the held-out 2020 cohort. The 8 actual-vs-predicted pairs
(one per industry) are pooled to compute each model's metrics - see
DECISIONS.md for why a per-series split isn't meaningful here.

Models: Naive, ARIMA, Prophet, XGBoost, LSTM (PyTorch)
Metrics: MAE, RMSE, MAPE, R2, SMAPE

Usage:
    python3 src/forecast.py
"""
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sqlalchemy import create_engine

DB_URL = "postgresql+psycopg2://postgres:startuppulse@localhost:5432/startuppulse"
COHORTS = [1990, 1995, 2000, 2005, 2010, 2015, 2020]
TRAIN_COHORTS = COHORTS[:-1]   # 1990-2015, 6 points
TEST_COHORT = COHORTS[-1]      # 2020, held out


def load_series() -> pd.DataFrame:
    """Industry x cohort_bin mean Revenue, pivoted. Rows = industries."""
    engine = create_engine(DB_URL)
    query = """
        SELECT industry, cohort_bin, AVG(revenue_musd) AS revenue
        FROM startups
        GROUP BY industry, cohort_bin
        ORDER BY industry, cohort_bin;
    """
    df = pd.read_sql(query, engine)
    pivot = df.pivot(index="industry", columns="cohort_bin", values="revenue")
    return pivot[COHORTS]  # enforce column order


# ---------- individual models: each takes 6 train values, returns 1 prediction ----------

def predict_naive(train: np.ndarray) -> float:
    return train[-1]


def predict_arima(train: np.ndarray) -> float:
    from statsmodels.tsa.arima.model import ARIMA
    try:
        model = ARIMA(train, order=(1, 1, 0)).fit()
        return float(model.forecast(steps=1)[0])
    except Exception:
        return predict_naive(train)  # thin series can make ARIMA fail to converge


def predict_prophet(train: np.ndarray) -> float:
    try:
        from prophet import Prophet
    except ImportError:
        return None  # signals "skipped" to the caller

    dates = pd.to_datetime([f"{y}-01-01" for y in TRAIN_COHORTS])
    df = pd.DataFrame({"ds": dates, "y": train})
    m = Prophet(yearly_seasonality=False, weekly_seasonality=False,
                daily_seasonality=False)
    m.fit(df)
    future = pd.DataFrame({"ds": [pd.Timestamp(f"{TEST_COHORT}-01-01")]})
    forecast = m.predict(future)
    return float(forecast["yhat"].iloc[0])


def predict_xgboost(train: np.ndarray) -> float:
    from xgboost import XGBRegressor
    X_train = np.arange(len(train)).reshape(-1, 1)
    model = XGBRegressor(n_estimators=50, max_depth=2, learning_rate=0.3)
    model.fit(X_train, train)
    X_test = np.array([[len(train)]])
    return float(model.predict(X_test)[0])


def predict_lstm(train: np.ndarray) -> float:
    try:
        import torch
        import torch.nn as nn
    except ImportError:
        return None

    torch.manual_seed(0)

    # Normalize - small raw values + tiny dataset make unnormalized LSTMs unstable
    mean, std = train.mean(), train.std() if train.std() > 0 else 1.0
    norm = (train - mean) / std

    # Build sliding windows of size 1: value[t] -> value[t+1]
    X = torch.tensor(norm[:-1], dtype=torch.float32).view(-1, 1, 1)
    y = torch.tensor(norm[1:], dtype=torch.float32).view(-1, 1)

    class TinyLSTM(nn.Module):
        def __init__(self):
            super().__init__()
            self.lstm = nn.LSTM(input_size=1, hidden_size=8, batch_first=True)
            self.fc = nn.Linear(8, 1)

        def forward(self, x):
            out, _ = self.lstm(x)
            return self.fc(out[:, -1, :])

    model = TinyLSTM()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.05)
    loss_fn = nn.MSELoss()

    model.train()
    for _ in range(200):  # tiny dataset, cheap to run many epochs
        optimizer.zero_grad()
        pred = model(X)
        loss = loss_fn(pred, y)
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        last = torch.tensor(norm[-1:], dtype=torch.float32).view(1, 1, 1)
        pred_norm = model(last).item()
    return pred_norm * std + mean


MODELS = {
    "Naive": predict_naive,
    "ARIMA": predict_arima,
    "Prophet": predict_prophet,
    "XGBoost": predict_xgboost,
    "LSTM": predict_lstm,
}


# ---------- metrics ----------

def regression_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
    actual, predicted = np.array(actual), np.array(predicted)
    errors = actual - predicted
    mae = np.mean(np.abs(errors))
    rmse = np.sqrt(np.mean(errors ** 2))
    mape = np.mean(np.abs(errors / actual)) * 100
    smape = np.mean(2 * np.abs(errors) / (np.abs(actual) + np.abs(predicted) + 1e-9)) * 100
    ss_res = np.sum(errors ** 2)
    ss_tot = np.sum((actual - np.mean(actual)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {"MAE": mae, "RMSE": rmse, "MAPE": mape, "R2": r2, "SMAPE": smape}


def main():
    pivot = load_series()
    print("Industry x Cohort-Bin mean Revenue (M USD):")
    print(pivot.round(2))
    print()

    results = {name: {"actual": [], "predicted": []} for name in MODELS}
    skipped = set()

    for industry in pivot.index:
        series = pivot.loc[industry].values.astype(float)
        train, actual_test = series[:-1], series[-1]

        for name, fn in MODELS.items():
            pred = fn(train)
            if pred is None:
                skipped.add(name)
                continue
            results[name]["actual"].append(actual_test)
            results[name]["predicted"].append(pred)

    print("--- Per-industry predictions for held-out cohort (2020) ---")
    rows = []
    for name in MODELS:
        if name in skipped:
            continue
        for ind, a, p in zip(pivot.index, results[name]["actual"], results[name]["predicted"]):
            rows.append({"model": name, "industry": ind, "actual": round(a, 2), "predicted": round(p, 2)})
    print(pd.DataFrame(rows).pivot(index="industry", columns="model", values="predicted").round(2))
    print()

    print("--- Pooled metrics across all 8 industries (held-out 2020 cohort) ---")
    metric_rows = []
    for name in MODELS:
        if name in skipped:
            print(f"{name}: SKIPPED (library not installed)")
            continue
        m = regression_metrics(results[name]["actual"], results[name]["predicted"])
        m["model"] = name
        metric_rows.append(m)

    metrics_df = pd.DataFrame(metric_rows).set_index("model")[["MAE", "RMSE", "MAPE", "R2", "SMAPE"]]
    print(metrics_df.round(3))

    metrics_df.to_csv("results_forecasting.csv")
    print("\nSaved: results_forecasting.csv")

    if skipped:
        print(f"\nNOTE: skipped models (not installed): {sorted(skipped)}")
        print("Run: pip3 install -r requirements-module2.txt")


if __name__ == "__main__":
    main()
