"""
StartupPulse - Module 4: commentary layer (template-based v1).

The models predict; this module only EXPLAINS their outputs in plain English
(DECISIONS.md, Decision 6). It never changes or influences a prediction.
A real LLM call can later replace build_commentary() without touching callers,
because it takes the same inputs and returns the same text.
"""

# Headline numbers from Decision 14 (5-fold CV x3). Kept as constants so the
# honesty caveat always quotes the real results.
CLASSIFIER_AUC = 0.58        # best cross-validated ROC-AUC (0.5 = coin flip)
MAJORITY_ACCURACY = 0.568    # accuracy from always guessing "not profitable"


def describe_profitability(name: str, industry: str, prob: float) -> str:
    """One sentence on the model's profitability lean. prob = P(profitable)."""
    if prob >= 0.60:
        lean = "leans toward profitable"
    elif prob <= 0.40:
        lean = "leans toward not profitable"
    else:
        lean = "is close to a coin flip"
    return (f"For {name} ({industry}), the model estimates a {prob:.0%} chance "
            f"of being profitable, so it {lean}.")


def describe_peer_position(revenue_vs_trend: float, industry: str, cohort: int) -> str:
    """How this startup's revenue compares with peers (leave-one-out feature)."""
    if abs(revenue_vs_trend) < 1.0:
        return (f"Its revenue is about level with other {industry} startups "
                f"from the {cohort} cohort.")
    direction = "above" if revenue_vs_trend > 0 else "below"
    return (f"Its revenue is {abs(revenue_vs_trend):.1f}M USD {direction} the average of "
            f"other {industry} startups from the {cohort} cohort.")


def describe_forecast(industry: str, last_cohort: int, last_value: float,
                      forecast_value: float, forecast_cohort: int, model: str) -> str:
    """Plain-English reading of one industry's cohort-level revenue forecast."""
    change = (forecast_value - last_value) / last_value * 100 if last_value else 0.0
    if abs(change) < 3:
        move = "roughly flat"
    else:
        move = f"{'up' if change > 0 else 'down'} about {abs(change):.0f}%"
    return (f"{model} projects average revenue for {industry} startups in the "
            f"{forecast_cohort} cohort at about {forecast_value:.1f}M USD, {move} "
            f"versus the {last_cohort} cohort ({last_value:.1f}M USD).")


def reliability_note() -> str:
    """Fixed, honest caveat. Always included so results are never oversold."""
    return (f"Caution: the profitability model is only slightly better than chance "
            f"(ROC-AUC about {CLASSIFIER_AUC:.2f}, where 0.50 is a coin flip), and "
            f"guessing 'not profitable' every time is already right "
            f"{MAJORITY_ACCURACY:.0%} of the time. Industry forecasts come from very "
            f"short series (7 cohorts per industry) and no model beat simply "
            f"predicting the historical average. Treat both as rough context, not advice.")


def build_commentary(name, industry, cohort, prob, revenue_vs_trend,
                     last_cohort, last_value, forecast_cohort, forecast_value,
                     forecast_model="Prophet") -> str:
    """Combine all pieces into one summary.
    cohort = the startup's own cohort; last_cohort = last OBSERVED cohort of the
    industry series (the forecast is compared against that, not the startup's)."""
    parts = [
        describe_profitability(name, industry, prob),
        describe_peer_position(revenue_vs_trend, industry, cohort),
        describe_forecast(industry, last_cohort, last_value, forecast_value,
                          forecast_cohort, forecast_model),
        reliability_note(),
    ]
    return "\n\n".join(parts)


if __name__ == "__main__":
    # Demo with made-up numbers; real values are wired in later modules.
    print(build_commentary(
        name="Startup_1", industry="IoT", cohort=2005, prob=0.34,
        revenue_vs_trend=42.18, last_cohort=2015, last_value=45.11,
        forecast_cohort=2020, forecast_value=30.43))
