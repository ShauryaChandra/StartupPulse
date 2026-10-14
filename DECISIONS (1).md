# StartupPulse — DECISIONS.md

Every non-obvious choice in this project, and why it was made. If asked "why did you do X and not Y" in an interview, the answer is in here.

---

## Project scope

**One-line pitch:** A full-stack platform that forecasts industry-level startup trends (by founding cohort) and predicts individual startup profitability, using industry trend context as a feature — with an LLM layer that explains the predictions in plain language.

**Core question:** Given a startup's own metrics and its industry's cohort trend, can we predict whether it's profitable — and does the industry-trend context measurably improve that prediction over firm-level features alone? Separately, how has the typical startup profile in each industry shifted across founding-cohort eras, and where is that shift heading?

**Deadline:** Nov 1, 2026 (11 weeks from project start, Aug 19 2026), built solo alongside college.

---

## Decision 1 — Frontend: Streamlit, not React

**Chosen:** Streamlit
**Rejected:** React + Recharts

**Why:** With ~1-2 hrs/day solo and a hard Nov 1 deadline, React would consume weeks on UI plumbing (routing, state management, API wiring) that don't demonstrate ML/data engineering skill — the actual point of the project. Streamlit gets a working, presentable frontend in days, not weeks, and is still a legitimate choice for a data/ML product (not a toy).

**Revisit:** If the project has legs after Goldman applications, React becomes the V2 frontend.

---

## Decision 2 — Classification: predict real "Profitable" label, industry-trend forecast as an engineered feature

**Chosen:** Classification target is the dataset's native `Profitable` column (binary, 284 not-profitable / 216 profitable — reasonably balanced). Features: Funding Rounds, Funding Amount, Valuation, Revenue, Employees, Market Share, Industry, Region, plus one engineered feature derived from the forecasting module — how this startup's Revenue compares to its Industry × Cohort-Bin forecasted trend (Decision 4).
**Rejected (earlier):** Binary label derived purely from a flat, arbitrary revenue-growth threshold with no real ground truth.
**Rejected (earlier):** Deriving the label by comparing a startup's growth to its industry's forecast, with no independently verified label.
**Rejected (considered, not chosen):** `Exit Status` (3-class: Private 348, Acquired 107, IPO 45) — real label too, but meaningfully imbalanced (IPO = 9% of rows), kept as a possible secondary/stretch classification task if time allows.

**Why this changed (second reframe):** Direct inspection of the real dataset (see Decision 3 update) revealed it already contains a genuine, dataset-native binary label (`Profitable`) — using it is strictly better than inventing a derived threshold, since it means the paper's classification results are validated against real ground truth rather than a synthetic label the project itself defined. This also resolves the earlier concern (Decision 2, first version) about classification depending on forecasting output being ready first — profitability can now be modeled independently of the forecasting module, while the industry-trend forecast is added as one *additional* engineered feature to test whether market context improves prediction over firm-level features alone. This is a stronger, more testable research question for the paper: "does industry-trend context improve profitability prediction over firm-level features alone?"

**Why "StartupPulse" is still accurate:** Classification checks an individual startup's actual profitability (its "pulse"); the industry-cohort forecast (Decision 4) checks the market's pulse and feeds in as context. The two modules are connected via a real feature, not a synthetic label — arguably a cleaner version of the same hybrid idea from the first version of this decision.

**Trade-off accepted:** `Profitable` is a static/current-state label (not itself a trend), so the "does the industry trend help predict future profitability" framing is slightly softer than a true forward-looking prediction would be — this is disclosed in the paper as a static classification task informed by trend context, not a forecast of future profitability.

---

## Decision 3 — Data source: Global Startup Funding & Valuation Cleaned Dataset (Kaggle, actual coverage 1990-2022)

**Chosen:** Global Startup Funding & Valuation Cleaned Dataset — cleaned, structured, includes growth, funding rounds, valuations, revenues, employee counts, profitability, market share trends. Actual timeline: startups founded 1990-2022 (not 2015-2024 as the Kaggle listing claimed — see Update below).
**Rejected:** Global Startup Success Dataset (5,000 startups, 15 features, has a built-in success score) — kept as backup only.
**Rejected:** Live APIs (Crunchbase-like) — access/rate-limit risk not worth it under deadline pressure.
**Rejected:** Fully synthetic data — would undermine the paper's credibility ("results on data I generated myself" is a weak claim).

**Why:** Already cleaned (saves real time in weeks 1-2), has genuine year-over-year structure so forecasting isn't artificial, and contains revenue/valuation/funding so the forecast target could be chosen without switching datasets later.

**Fallback trigger:** If this dataset proves too messy or too small in practice once opened, fall back to the Global Startup Success Dataset and adjust the forecasting approach accordingly (cross-sectional rather than time-series framing).

**Update (post-inspection):** Confirmed real dataset via direct CSV inspection (uploaded, not from Kaggle listing description alone — the listing's stated date range, 2015-2024, turned out to be inaccurate). Actual data: 500 rows, 12 columns, no missing values, "Year Founded" spans 1990-2022, 8 Industries (EdTech 74, FinTech 71, E-Commerce 70, Gaming 62, AI 62, IoT 61, Cybersecurity 51, HealthTech 49 — reasonably balanced), 5 Regions (~90-108 rows each — balanced). Cross-sectional confirmed: one row per startup, no repeated per-startup observations over time. See Decision 4 for how this changed the forecast target (now Industry × 5-Year Cohort Bin, not Industry-Year).

**Actual columns:** Startup Name, Industry, Funding Rounds, Funding Amount (M USD), Valuation (M USD), Revenue (M USD), Employees, Market Share (%), Profitable (0/1), Year Founded, Region, Exit Status (Private/Acquired/IPO). `Profitable` became the real classification label — see Decision 2.

---

## Decision 4 — Forecast target: Revenue growth, aggregated by Industry × 5-Year Cohort Bin

**Chosen:** For each Industry, aggregate startup metrics (funding, valuation, revenue) by 5-year founding-cohort bin (1990-94, 1995-99, ..., 2020-24) — 7 bins × 8 industries = 56 data points, forming 8 parallel short time series (one per industry).
**Rejected:** Per-startup revenue growth forecast (original plan) — dataset has no per-startup repeated observations over time.
**Rejected:** Industry × Year (raw, yearly granularity) — real inspection showed 33 distinct "Year Founded" values × 8 industries = ~1.9 rows/cell on average, far too sparse to be usable.
**Rejected:** Single aggregate market-wide series — same sparsity problem, worse (fewer total points).
**Rejected:** Sourcing a new dataset with genuine per-year funding events — real cost (3-5+ hrs minimum to find/vet/clean) with no guarantee of a better free dataset (longitudinal funding data is often paywalled), against a deadline with little slack. Not pursued as the primary path but not ruled out if time allows later.

**Why this changed (second reframe):** After confirming the actual dataset (500 rows, "Year Founded" 1990-2022, no repeated per-startup observations), the original Industry-Year plan (Decision 4, first version) turned out to still be too sparse — raw yearly granularity averages under 2 rows per Industry-Year cell. Binning into 5-year cohorts brings this to ~8.9 rows/cell on average (range 1-17), which is workable, though still thin.

**What this means the forecast actually answers:** Not "what will Industry X's funding be next year" (true year-ahead forecasting), but "how has the typical startup profile in Industry X shifted across founding-cohort eras, and where is that trend heading." This is a genuine reframe from calendar-time forecasting to cohort-trend analysis, and is disclosed as such in the paper's Methodology and Limitations sections — not presented as if it were dense year-by-year forecasting.

**Known consequence — LSTM:** With only ~7 points per industry series (56 total across all industries), LSTM is very likely to underperform simpler models (possibly even the naive baseline). This is treated as an expected, reportable finding in the paper ("deep learning underperforms on short series, consistent with known sample-size sensitivity in the literature"), not as a failed experiment to hide. The 5-model forecasting comparison (Decision 5) is not weakened by this — an honest negative result on LSTM is still a valid result.

**Trade-off accepted:** This is the second scope reframe on the forecasting side (see Decision 3 update). It is the pragmatic choice given the Nov 1 deadline — it keeps the real dataset, costs no additional sourcing time, and is defensible in the paper as long as it is clearly labeled as cohort-trend analysis rather than calendar-time forecasting.

---

## Decision 5 — Evaluation: 5 regression metrics, 5 classification metrics, multiple models per task

**Regression (forecast) metrics:** MAE, RMSE, MAPE, R², SMAPE
**Classification metrics:** Accuracy, Precision, Recall, F1-score, ROC-AUC

**Forecasting models compared (5):** Naive/seasonal-naive baseline, ARIMA/SARIMA, Prophet, XGBoost, LSTM
**Classification models compared (4):** Logistic Regression, Random Forest, XGBoost, LightGBM

**Why:** A single-model, single-metric result reads as a tutorial project. A comparison table across multiple models × multiple metrics is what makes the Results section of the paper legitimate, and demonstrates understanding of trade-offs (e.g., why MAPE alone is misleading near-zero, hence SMAPE is included too).

**Why 5 forecasting models specifically:** The naive baseline exists to prove the more sophisticated models are actually adding value — no forecasting paper is credible without one. ARIMA/SARIMA is the classical statistical baseline reviewers expect. Prophet and XGBoost were the original picks (interpretable trend/seasonality model vs. tree-based nonlinear model). LSTM was added deliberately to give a "naive → statistical → ML → deep learning" progression across four method families — the strongest narrative shape for the paper's Results section, even though it is the single most time-expensive model to build (data windowing, training time, tuning). This cost was accepted knowingly; if LSTM overruns, it draws from the Week 10 buffer, not from the paper-writing or deployment schedule.

**Why LightGBM was added to classification:** Once forecasting expanded to 5 models for comparison depth, classification's original 3 models looked comparatively thin. LightGBM was added because it is cheap to implement (largely reuses the XGBoost pipeline/data prep) while giving the classification comparison table better symmetry with the forecasting one.

---

## Decision 6 — LLM as communicator, not analyst

**Chosen:** LLM layer generates plain-English commentary on forecasts/classifications already produced by the ML models.
**Rejected:** LLM making or influencing the actual predictions.

**Why:** Keeps the ML results scientifically clean and reproducible — the LLM's role is explanation, not decision-making. This is also the safer, more defensible architecture to explain in an interview: "the model predicts, the LLM explains."

---

## Decision 7 — Project name: kept "StartupPulse," scope made to match

**Context:** After the forecast target moved to Industry-Year aggregates, "StartupPulse" briefly stopped matching what the project did — it was checking an industry's pulse, not a startup's.

**Resolved by:** The hybrid architecture (Decision 2) restores the name's accuracy rather than renaming the project. Classification checks an individual startup's pulse; forecasting checks the market's pulse; the two are connected (startup performance is benchmarked against its industry's forecast). "StartupPulse" is therefore literally accurate again — it takes the pulse of a specific startup relative to the market it's in.

---

## Decision 8 — Timeline replan after scooty accident (Sep 5)

**What happened:** A scooty accident interrupted the project from ~Aug 19 to Sep 5 (17 days). Reduced-hours recovery began Sep 6.
**New effective timeline:** 8 weeks (Sep 6 – Nov 1), down from the original 11 weeks (Aug 19 – Nov 1).
**Daily budget:** 1-2 hrs/day combined across StartupPulse and LeetCode (down from 1-2 hrs/day for StartupPulse alone, plus separate LeetCode/StatQuest/open-source slots).

**Decision:** Keep full project scope (5 forecasting models, 4 classifiers, LLM layer, full app, research paper) rather than cutting immediately — but with a hard checkpoint at end of Week 3 (Sep 26) to force a real scope-cut decision (most likely dropping LightGBM or simplifying the LLM layer) if the forecasting + LSTM + first two classifiers aren't functionally complete by then. This avoids two failure modes: cutting scope prematurely before knowing if the tighter schedule is actually infeasible, and drifting past Nov 1 without ever making an explicit cut decision.

**What paused (not cancelled):** StatQuest and open-source contribution slots, previously alternating daily. At this reduced hour budget there isn't room for a 3rd/4th daily commitment alongside StartupPulse + LeetCode. Revisit after the Week 3 checkpoint; StatQuest may return as a one-off before specific modules (e.g. right before LSTM) rather than a recurring slot.

**LeetCode change:** Switched from an ad-hoc sliding-window/prefix-sum/two-pointer rotation to Striver's A2Z DSA Sheet, followed in its own topic order, 1 problem/day. More structured sequencing matters more now that there's less time to course-correct an unstructured rotation.

---

## Decision 9 — Late checkpoint (Oct 7): full scope kept, risk accepted explicitly

**Context:** The Week 3 checkpoint set in Decision 8 (Sep 26) to force a scope-cut decision was missed — it did not happen on that date. By Oct 7, the project was still at the Module 1 verification step, well behind the Week 5 position the 8-week replan expected. Cause: a combination of heavier-than-expected college workload, continued post-accident recovery, and lost momentum after the long gap.

**Decision:** Offered a concrete scope cut (drop LSTM from forecasting, simplify the LLM layer to a single prompt template, minimal auth) to protect Nov 1. **Declined — full original scope kept, including LSTM, with the time risk knowingly accepted.**

**Why this is logged as a real decision, not just a status update:** The project now has ~25 days left (Oct 7 → Nov 1) for work the original plan budgeted 100-130 hours for alone, let alone the paper. Keeping full scope is a legitimate choice, but it means the Week 3 checkpoint's purpose — forcing an early, calm cut rather than a late, rushed one — did not happen. This is disclosed honestly rather than pretending the timeline is comfortable.

**New forcing function:** Since a calendar date alone did not trigger a real review last time, the next checkpoint is tied to a concrete deliverable, not just a date: **when Module 2 (all 5 forecasting models) is either complete or still not done by Oct 17**, scope gets revisited then, explicitly, in this document — not silently carried forward again.

**Update (Oct 12):** Module 1 confirmed fully complete via `verify.py` — 500 rows, 8 industries, 5 regions, profitable split 216/284 matching the source CSV exactly, all 7 cohort bins present, sample rows spot-checked correct (e.g. year 2006 correctly binned to cohort 2005). Committed and pushed to GitHub. Module 2 (forecasting) starts now, with **19 days to Nov 1** and the Oct 17 checkpoint 5 days away.

**Module 2 methodology notes (Oct 12):**
- **Forecast target refined to level, not growth:** Decision 4 named "revenue growth" as the target, but with only 7 cohort points per industry, differencing to get period-over-period growth drops this to 6 points — worse than already thin. Models instead forecast the **level** (mean Revenue (M USD) per Industry × Cohort-Bin). Growth is derived afterward for narrative/interpretation (e.g. "forecasted level implies X% growth over the prior cohort"), not used as the direct model target. This preserves all available data points.
- **Evaluation — leave-last-cohort-out, pooled across industries:** With only 7 points per series, no single industry supports a real train/test split. Each model trains on the first 6 cohorts (1990–2015) per industry and predicts the held-out 7th (2020) cohort, for all 8 industries. The 8 actual-vs-predicted pairs are pooled across industries to compute each model's 5 regression metrics — this is a panel/cross-sectional backtest, not a per-series one, and is disclosed as such in the paper's Methodology section.




- React dashboard (deferred to V2)
- Plotly interactive visualizations (deferred to V2)
- Real-time data feeds
- Multi-user roles beyond basic auth
- Stockfish-style "what would you add" extensions — N/A, carried over format from Chess project, kept as a placeholder pattern for this doc

**Reasoning:** Each of these adds real time (2-3+ days apiece) without adding to the core question being answered. Cutting them protects the Nov 1 deadline and the research paper timeline running in parallel.

---

## Deliverables

- GitHub repo (pipeline, models, API, frontend)
- README.md
- ROADMAP.md (V1 vs V2 scope)
- DECISIONS.md (this file)
- Deployed demo (Docker)
- Research paper: forecasting + classification comparison forms the Results section
