"""
StartupPulse - in-fold industry-cohort context feature (Decision 15).

revenue_vs_trend = a startup's revenue minus the mean revenue of its industry x
cohort peers, computed ONLY from training rows of each CV fold:

  * rows the step is FIT on (training rows): leave-one-out mean of the OTHER
    training startups in the same industry x cohort (itself excluded, Decision 12)
  * rows it only TRANSFORMS (validation/test rows, or new startups): the mean of
    the training startups in the same industry x cohort

So no validation startup ever influences a training row's feature, and a
validation startup's own revenue never enters its own baseline.
No peers (empty or single-member group) -> 0.0, same rule as before.
"""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator

KEYS = ["industry", "cohort_bin"]
VALUE = "revenue_musd"


class PeerTrend(BaseEstimator):
    """Expects a DataFrame with columns industry, cohort_bin, revenue_musd
    and returns one column (n_rows, 1)."""

    def fit(self, X, y=None):
        self.stats_ = X.groupby(KEYS)[VALUE].agg(["sum", "count"])
        return self

    def _lookup(self, X):
        return self.stats_.reindex(pd.MultiIndex.from_frame(X[KEYS]))

    def transform(self, X):
        s = self._lookup(X)
        with np.errstate(divide="ignore", invalid="ignore"):
            peer_mean = s["sum"].to_numpy(dtype=float) / s["count"].to_numpy(dtype=float)
        out = X[VALUE].to_numpy(dtype=float) - peer_mean
        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0).reshape(-1, 1)

    def fit_transform(self, X, y=None, **fit_params):
        # Training rows: leave-one-out, using training rows only.
        self.fit(X)
        s = self._lookup(X)
        rev = X[VALUE].to_numpy(dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            loo_mean = (s["sum"].to_numpy(dtype=float) - rev) / (
                s["count"].to_numpy(dtype=float) - 1.0)
        out = rev - loo_mean
        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0).reshape(-1, 1)
