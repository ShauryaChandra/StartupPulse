"""
StartupPulse - Module 3: classification pipeline
Predicts profitable using firm-level features + industry-cohort context.
"""
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
from sklearn.model_selection import (RepeatedStratifiedKFold, StratifiedKFold,
                                     cross_validate, cross_val_predict,
                                     train_test_split)
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score, confusion_matrix)
from peer_trend import PeerTrend

import os
from pathlib import Path

# Local development reads Postgres (Module 1). A deployed copy has no database,
# so it reads the bundled CSV exported from that same table (data/startups.csv).
DB_URL = os.environ.get("DATABASE_URL",
                        "postgresql+psycopg2://postgres:startuppulse@localhost:5432/startuppulse")
CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "startups.csv"
SEED = 42  # fixed so results are reproducible

NUMERIC = ["funding_rounds", "funding_amount_musd", "valuation_musd",
           "revenue_musd", "employees", "market_share_pct", "year_founded"]
CATEGORICAL = ["industry", "region"]

# The ablation: same models, with and without the industry-cohort context feature.
FEATURE_SETS = {
    "baseline (firm-level only)": NUMERIC + CATEGORICAL,
    # cohort_bin is NOT a model input: build_pipeline uses it only to compute the
    # in-fold peer trend (Decision 15).
    "context (+ revenue_vs_trend)": NUMERIC + CATEGORICAL + ["cohort_bin"],
}

SCORING = {"Accuracy": "accuracy", "Precision": "precision", "Recall": "recall",
           "F1": "f1", "ROC-AUC": "roc_auc"}


def load_data() -> pd.DataFrame:
    """Load all 500 startups: bundled CSV if present, otherwise Postgres."""
    if CSV_PATH.exists() and not os.environ.get("USE_DB"):
        df = pd.read_csv(CSV_PATH)
        df["profitable"] = df["profitable"].astype(int)
        return df
    from sqlalchemy import create_engine
    return pd.read_sql("SELECT * FROM startups;", create_engine(DB_URL))


def add_trend_feature(df: pd.DataFrame) -> pd.DataFrame:
    """Descriptive column: revenue minus the leave-one-out mean revenue of the
    same industry x cohort. Used only for the app's peer-comparison text; the
    models compute their own in-fold version (see peer_trend.py)."""
    df = df.copy()
    group_sum = df.groupby(["industry", "cohort_bin"])["revenue_musd"].transform("sum")
    group_count = df.groupby(["industry", "cohort_bin"])["revenue_musd"].transform("count")
    leave_one_out_mean = (group_sum - df["revenue_musd"]) / (group_count - 1)
    df["revenue_vs_trend"] = (df["revenue_musd"] - leave_one_out_mean).fillna(0.0)
    return df


def make_models() -> dict:
    return {
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=SEED),
        "RandomForest": RandomForestClassifier(n_estimators=200, random_state=SEED),
        "XGBoost": XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.1,
                                 random_state=SEED, eval_metric="logloss"),
        "LightGBM": LGBMClassifier(n_estimators=100, max_depth=3, learning_rate=0.1,
                                   random_state=SEED, verbose=-1),
    }


def build_pipeline(model, features: list) -> Pipeline:
    """Scale numeric columns, one-hot encode categoricals, then fit the model.
    Preprocessing lives INSIDE the pipeline, so it is fit on training data only."""
    numeric = [c for c in features if c in NUMERIC]
    categorical = [c for c in features if c in CATEGORICAL]
    parts = [("num", StandardScaler(), numeric),
             ("cat", OneHotEncoder(handle_unknown="ignore"), categorical)]
    if "cohort_bin" in features:  # context arm: peer trend computed inside each fold
        parts.append(("trend", Pipeline([("peer", PeerTrend()),
                                         ("scale", StandardScaler())]),
                      ["industry", "cohort_bin", "revenue_musd"]))
    return Pipeline([("prep", ColumnTransformer(parts)), ("model", model)])


def score(y_true, y_pred, y_prob) -> dict:
    return {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision": precision_score(y_true, y_pred, zero_division=0),
        "Recall": recall_score(y_true, y_pred, zero_division=0),
        "F1": f1_score(y_true, y_pred, zero_division=0),
        "ROC-AUC": roc_auc_score(y_true, y_prob),
    }


def run_experiment(df: pd.DataFrame) -> pd.DataFrame:
    """First look only: one stratified 80/20 split (not the reported result)."""
    y = df["profitable"].astype(int)
    train_idx, test_idx = train_test_split(
        df.index, test_size=0.2, stratify=y, random_state=SEED)
    y_train, y_test = y.loc[train_idx], y.loc[test_idx]
    print(f"Train: {len(train_idx)}  Test: {len(test_idx)}")
    print(f"Majority-class baseline accuracy: {max(y_test.mean(), 1 - y_test.mean()):.3f}\n")
    rows = []
    for fs_name, features in FEATURE_SETS.items():
        for model_name, model in make_models().items():
            pipe = build_pipeline(model, features)
            pipe.fit(df.loc[train_idx, features], y_train)
            pred = pipe.predict(df.loc[test_idx, features])
            prob = pipe.predict_proba(df.loc[test_idx, features])[:, 1]
            rows.append({"features": fs_name, "model": model_name,
                         **score(y_test, pred, prob)})
    return pd.DataFrame(rows)


def cross_validate_all(df: pd.DataFrame):
    """5-fold CV repeated 3 times (15 splits) for every model x feature set.
    Same random_state => every model sees identical splits (paired comparison)."""
    y = df["profitable"].astype(int)
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=SEED)
    rows, auc_scores = [], {}
    for fs_name, features in FEATURE_SETS.items():
        for model_name, model in make_models().items():
            pipe = build_pipeline(model, features)
            res = cross_validate(pipe, df[features], y, cv=cv, scoring=SCORING)
            row = {"features": fs_name, "model": model_name}
            for metric in SCORING:
                row[metric] = res[f"test_{metric}"].mean()
            row["AUC_std"] = res["test_ROC-AUC"].std()
            rows.append(row)
            auc_scores[(fs_name, model_name)] = res["test_ROC-AUC"]
    return pd.DataFrame(rows), auc_scores


def ablation_summary(auc_scores: dict) -> pd.DataFrame:
    """Paired ROC-AUC difference (context - baseline) across the 15 splits."""
    base, ctx = list(FEATURE_SETS)
    rows = []
    for model_name in make_models():
        diff = auc_scores[(ctx, model_name)] - auc_scores[(base, model_name)]
        rows.append({"model": model_name, "delta_AUC": diff.mean(),
                     "std": diff.std(), "folds_context_better": int((diff > 0).sum())})
    return pd.DataFrame(rows)


def confusion_report(df: pd.DataFrame) -> pd.DataFrame:
    """Out-of-fold predictions over all 500 rows -> one confusion matrix per model."""
    y = df["profitable"].astype(int)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    rows = []
    for fs_name, features in FEATURE_SETS.items():
        for model_name, model in make_models().items():
            pred = cross_val_predict(build_pipeline(model, features),
                                     df[features], y, cv=cv)
            tn, fp, fn, tp = confusion_matrix(y, pred).ravel()
            rows.append({"features": fs_name, "model": model_name,
                         "TN": tn, "FP": fp, "FN": fn, "TP": tp})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = add_trend_feature(load_data())
    y = df["profitable"].astype(int)
    pd.set_option("display.width", 220)

    print(f"Majority-class baseline accuracy: {max(y.mean(), 1 - y.mean()):.3f}\n")
    cv_results, auc_scores = cross_validate_all(df)
    print(cv_results.round(3).to_string(index=False))
    cv_results.to_csv("results_classification_cv.csv", index=False)

    print("\nAblation (context - baseline), ROC-AUC over 15 paired splits:")
    print(ablation_summary(auc_scores).round(4).to_string(index=False))

    print("\nConfusion matrices (out-of-fold, 500 rows):")
    print(confusion_report(df).to_string(index=False))
