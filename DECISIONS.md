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

**Update (Oct 16) — checkpoint met:** Module 2 (all 5 forecasting models) was completed on Oct 14, ahead of the Oct 17 trigger, so no scope cut is forced. Full scope stands (Decision 9 unchanged). The out-of-scope list that previously sat here now has its own section at the end of this file.

---

## Deliverables

- GitHub repo (pipeline, models, API, frontend)
- README.md
- ROADMAP.md (V1 vs V2 scope)
- DECISIONS.md (this file)
- Deployed demo (Docker)
- Research paper: forecasting + classification comparison forms the Results section

---

## Decision 10 — Division of labor: boilerplate vs. modeling logic (Oct 12)

**Context:** The original intent (stated when Module 1 was handed over as Claude-written) was to shift toward the person writing the modeling logic themselves starting at Module 2 (forecasting), since that's the part that actually needs to be understood and defended in the paper and in interviews — not the database/pipeline plumbing. In practice, under Oct 12's time pressure (19 days to Nov 1, already behind the Sep 26 checkpoint), `forecast.py` was again fully written by Claude, without revisiting that intent explicitly.

**Decision:** Keep momentum — run the Claude-written, already-tested `forecast.py` now to get Module 2 results on schedule. Afterward, once results are in and Module 2 is functionally done, rewrite `forecast.py` independently, using the working version as a reference, purely to build real understanding of the modeling choices (why ARIMA(1,1,0), why the LSTM input is normalized, why evaluation is leave-last-cohort-out pooled across industries, etc.).

**Why this split, not a stricter one:** Rewriting block-by-block *before* seeing results would cost real debugging time that isn't available right now without risking the timeline further. Rewriting *after* a working version exists is lower-risk (a reference implementation to check against) and still forces genuine engagement with the logic, rather than having it stay as code that was only ever run, never understood.

**Going forward:** Module 3 (classification) is the higher-priority module to write hands-on from the start — it uses a real label (`Profitable`) over the full 500 rows, is more central to the paper's core claim, and has a comparatively more favorable time position than Module 2 did. Default for Module 3 is Claude explaining and guiding block-by-block, not writing the full script outright, unless time pressure forces another explicit exception like this one.

---

## Decision 11 — Module 2 forecasting results (Oct 14)

**Status: Module 2 complete.** All 5 models ran successfully (`brew install libomp` resolved an initial XGBoost load failure on macOS — a known issue, not a bug in the code). Pooled metrics, leave-last-cohort-out (train 1990-2015, predict held-out 2020), across all 8 industries:

| Model | MAE | RMSE | MAPE | R² | SMAPE |
|---|---|---|---|---|---|
| **Prophet** | **10.28** | **14.97** | **31.4%** | **-0.059** | **23.3%** |
| Naive | 14.26 | 17.07 | 38.1% | -0.377 | 31.4% |
| XGBoost | 14.28 | 17.08 | 38.2% | -0.379 | 31.5% |
| ARIMA | 14.41 | 18.15 | 39.7% | -0.556 | 32.3% |
| LSTM | 40.29 | 57.30 | 95.5% | -14.52 | 66.5% |

**Findings (for the paper's Results/Discussion sections):**
- **Prophet is the clear best performer** across every metric — likely because it handles the irregular, non-monotonic shape of these short series more gracefully than a hand-tuned ARIMA order or a model with no explicit trend/seasonality structure.
- **Naive, XGBoost, and ARIMA cluster closely together**, all meaningfully worse than Prophet but far better than LSTM. This supports the Decision 4 read that there is no strong, easily exploitable trend in the cohort-level data — a flat "last value" guess is nearly as good as a tree-based or classical statistical model here.
- **LSTM fails badly, exactly as predicted in Decision 4's methodology notes** — MAE roughly 3x the next-worst model, R² of -14.5 (far worse than guessing the mean). This is the expected consequence of training a neural network on 6 data points per series, not a bug. Reported as a legitimate negative result: "deep learning underperforms markedly on short cohort series, consistent with known sample-size sensitivity," not hidden or re-run to "fix."
- **All models show negative R²** — none beat simply predicting the historical mean. This is an honest limitation of the thin, noisy cohort-bin data (Decision 4's trade-off), disclosed directly in the paper rather than glossed over.

Results saved to `results_forecasting.csv`. Committing now; Module 3 (classification) starts next.

---

## Decision 12 — Module 3 redesign after external review (Oct 14): leave-one-out trend feature, ablation framing

**Context:** An external review of the project (not from this assistant) was shared partway through writing Module 3's Block 1. It caught a real methodological flaw before any code was built around it: the originally planned `revenue_vs_trend` feature (Decision 2) — fitting Prophet on all 7 cohort points per industry, including the startup's own cohort, then using that fitted value as a feature for that same startup — is mildly circular. The startup's own revenue partially shapes the aggregate cohort point used to describe it. Not literal label leakage (profitability is never used to build the forecast), but strong enough to weaken the paper's central claim that industry-trend context improves classification over firm-level features alone.

**Decision 1 — simplified, de-circularized feature:** Replace the Prophet-fitted-value feature with a **leave-one-out industry-cohort mean**. For each startup: `revenue_vs_trend = startup's revenue_musd − mean(revenue_musd of all OTHER startups in the same industry × cohort_bin, excluding itself)`. This removes the circularity (the startup's own value is explicitly excluded from the baseline it's compared against), is cheaper to compute than refitting Prophet 500 times, and still captures the intended idea — how a startup compares to its industry-cohort peers.

**Decision 2 — ablation framing adopted for Module 3:** Instead of training each of the 4 classifiers once on a fixed feature set, train each **twice**: once on firm-level features only (baseline), once with the leave-one-out trend feature added (context). This reframes the central research question from "which classifier is best" to **"does industry-cohort context improve profitability prediction beyond firm-level features alone?"** — a stronger, more testable claim, and the one Decision 2 always intended but hadn't formalized as an explicit comparison.

**Scope note:** The same external review suggested further scope cuts (simplify the LLM layer, treat full-app Docker deployment as optional) echoing the same risk flagged in Decision 9. Re-raised explicitly and **declined again** — Decision 9's call (full scope, risk accepted) stands. Revisit only if a future concrete checkpoint shows it's genuinely not achievable, not preemptively based on this review alone.

---

## Decision 13 — Module 3 feature set and evaluation protocol (Oct 16)

**Features (target: `profitable`):**
- **Included (firm-level baseline):** funding_rounds, funding_amount_musd, valuation_musd, revenue_musd, employees, market_share_pct, year_founded (company-age proxy), industry, region.
- **Context feature (ablation arm only):** `revenue_vs_trend` — revenue minus the leave-one-out mean revenue of the same industry × cohort (Decision 12).
- **Excluded — `cohort_bin`:** it is `year_founded` rounded to a 5-year bucket, so it adds no information once `year_founded` is present. It remains in use for grouping (forecasting module, trend feature).
- **Excluded — `exit_status`:** Acquired / IPO are outcomes that occur after a startup succeeds, so using them to predict profitability would be leakage. Stated explicitly in the paper's Methodology.
- **`year_founded` tested, not assumed:** adding it (or `cohort_bin`) changed cross-validated ROC-AUC by under 0.003, far inside the ±0.04 split-to-split noise; it is included for completeness and defensibility, not because it helps.

**Edge case fixed:** The AI × 1995 cohort contains a single startup, so its leave-one-out mean is 0/0 (NaN) and crashed model fitting. Fixed with `.fillna(0.0)` (no peers → zero deviation). One row of 500 affected; disclosed as a limitation.

**Evaluation protocol:**
- A stratified 80/20 split (400 train / 100 test, seed 42) is run for a first look only. A 100-row test set has a standard error of roughly 5 accuracy points, and tree-model results differed slightly between two machines with different library versions — so the single split is **not** the reported result.
- **Reported result: 5-fold stratified CV repeated 3 times (15 paired splits)**, same seed for every model and feature set so comparisons are paired. Preprocessing (scaling, one-hot encoding) lives inside the sklearn Pipeline, so it is fit on training folds only.
- **Metrics:** Accuracy, Precision, Recall, F1, ROC-AUC, plus confusion matrices (out-of-fold, all 500 rows) and the **majority-class baseline accuracy (0.568)**, which any classifier must beat to be useful.
- **Ablation statistic:** paired ROC-AUC difference (context − baseline) over the 15 splits, per model.

**Known limitation (disclosed):** `revenue_vs_trend` is computed on all 500 rows before splitting, so a training row's feature uses test-row *revenues* (never labels). This is feature-level information sharing, not label leakage, but a stricter design would recompute the feature inside each fold.

**Resolved (Oct 21):** the feature is now recomputed inside each fold; see Decision 15.

---

## Decision 14 — Module 3 results (Oct 16): weak signal, context feature gives no measurable gain

**Note (Oct 21):** the Context rows in the three tables below were produced with `revenue_vs_trend` computed on all 500 rows before CV. They are kept as the audit trail and are **superseded by Decision 15** (in-fold feature). Baseline rows are unchanged and remain final.

**Status: Module 3 complete.** 4 classifiers x 2 feature sets, 5-fold stratified CV repeated 3 times (15 paired splits, seed 42). Majority-class baseline accuracy = 0.568 (284/500).

**Cross-validated results (mean over 15 splits):**

| Features | Model | Accuracy | Precision | Recall | F1 | ROC-AUC | AUC std |
|---|---|---|---|---|---|---|---|
| Baseline | LogisticRegression | 0.574 | 0.508 | 0.367 | 0.424 | 0.580 | 0.045 |
| Baseline | RandomForest | 0.577 | 0.517 | 0.347 | 0.412 | 0.581 | 0.045 |
| Baseline | XGBoost | 0.569 | 0.502 | 0.406 | 0.447 | 0.565 | 0.049 |
| Baseline | LightGBM | 0.546 | 0.470 | 0.392 | 0.425 | 0.551 | 0.037 |
| Context | LogisticRegression | 0.568 | 0.498 | 0.361 | 0.417 | 0.579 | 0.044 |
| Context | RandomForest | 0.577 | 0.516 | 0.347 | 0.414 | 0.575 | 0.038 |
| Context | XGBoost | 0.569 | 0.501 | 0.396 | 0.441 | 0.562 | 0.033 |
| Context | LightGBM | 0.543 | 0.462 | 0.389 | 0.420 | 0.549 | 0.039 |

**Ablation (paired ROC-AUC difference, context - baseline, 15 splits):**

| Model | delta AUC | std | Splits where context better (of 15) |
|---|---|---|---|
| LogisticRegression | -0.0017 | 0.0048 | 5 |
| RandomForest | -0.0067 | 0.0348 | 4 |
| XGBoost | -0.0027 | 0.0320 | 8 |
| LightGBM | -0.0017 | 0.0188 | 8 |

**Confusion matrices (out-of-fold, 500 rows; TN / FP / FN / TP):**

| Features | Model | TN | FP | FN | TP |
|---|---|---|---|---|---|
| Baseline | LogisticRegression | 212 | 72 | 140 | 76 |
| Baseline | RandomForest | 225 | 59 | 146 | 70 |
| Baseline | XGBoost | 204 | 80 | 133 | 83 |
| Baseline | LightGBM | 200 | 84 | 137 | 79 |
| Context | LogisticRegression | 207 | 77 | 141 | 75 |
| Context | RandomForest | 213 | 71 | 148 | 68 |
| Context | XGBoost | 205 | 79 | 130 | 86 |
| Context | LightGBM | 191 | 93 | 137 | 79 |

**Findings (for the paper's Results/Discussion):**
- **Weak signal overall.** Only LogisticRegression (0.574) and RandomForest (0.577) beat the 0.568 majority baseline on accuracy, by under one point. XGBoost ties it; LightGBM falls below it. ROC-AUC is 0.55-0.58, slightly above chance but with ~0.04 split-to-split noise, so the four models are not meaningfully different from each other.
- **The industry-cohort context feature does not help.** Mean delta AUC is negative for all four models (-0.0017 to -0.0067), each smaller in magnitude than its std (except LogReg, where both are tiny). Context was better in only 4-8 of 15 splits. Answer to the research question: no measurable improvement from `revenue_vs_trend` over firm-level features.
- **Models lean toward "not profitable".** In every matrix FN > FP (e.g. RandomForest baseline: 146 FN vs 59 FP), consistent with recall of 0.35-0.41 and with features that carry little signal.
- **Interpretation.** The dataset appears to be mostly noise with respect to profitability (likely simplified/synthetic). This is reported as a rigorous negative result, enabled by the ablation design (Decision 12), not tuned away.

**Caveats (disclosed):**
- The 15 CV splits overlap (repeated k-fold), so they are not independent; the std and "splits better" counts are descriptive, not a formal significance test.
- Hyperparameters were fixed, not tuned. Tuning on a 500-row, near-noise problem would mostly fit noise.
- Tree-model numbers can shift slightly across library versions, which is why CV means (not the single 100-row split) are the reported result.

---

## Decision 15 — Context feature recomputed inside each CV fold (Oct 21)

**Context:** Decision 13 disclosed that `revenue_vs_trend` was computed on all 500 rows before CV, so a training row's feature used validation rows' revenues (never labels). The same weakness was raised again on Oct 21 (suggestion from another AI assistant, relayed by the user; also already flagged by Claude). Fixed rather than only disclosed, because the feature is the center of the paper's ablation.

**Change:** a custom pipeline step, `PeerTrend` (`src/peer_trend.py`), computes the feature from the training rows of each fold only:
- **Training rows:** leave-one-out mean of the other *training* startups in the same industry x cohort (itself excluded, Decision 12).
- **Validation rows / new startups:** revenue minus the mean of the *training* startups in the same industry x cohort.
- **No peers** (empty or single-member group): 0.0, same rule as before.
- `cohort_bin` is used only as an input to this step; it is still not a model feature (Decision 13's exclusion stands).

**Verification (on stand-in data, before the real run):** (1) changing validation rows' revenues leaves every training feature unchanged; (2) one validation row's feature is unaffected by other validation rows; (3) training features equal a manual leave-one-out computed on training data only; (4) a validation row's feature equals its revenue minus the training-group mean. All passed. On the real data, the **Baseline rows reproduced exactly** (AUC 0.580 / 0.581 / 0.565 / 0.551), confirming nothing else changed.

**Final results, Context arm (5-fold stratified CV x3, 15 paired splits, seed 42):**

| Features | Model | Accuracy | Precision | Recall | F1 | ROC-AUC | AUC std |
|---|---|---|---|---|---|---|---|
| Context (in-fold) | LogisticRegression | 0.569 | 0.501 | 0.363 | 0.419 | 0.579 | 0.044 |
| Context (in-fold) | RandomForest | 0.573 | 0.506 | 0.329 | 0.396 | 0.566 | 0.036 |
| Context (in-fold) | XGBoost | 0.559 | 0.481 | 0.381 | 0.423 | 0.559 | 0.037 |
| Context (in-fold) | LightGBM | 0.554 | 0.481 | 0.411 | 0.441 | 0.546 | 0.037 |

**Final ablation (paired ROC-AUC difference, context - baseline, 15 splits):**

| Model | delta AUC | std | Splits where context better (of 15) |
|---|---|---|---|
| LogisticRegression | -0.0011 | 0.0073 | 7 |
| RandomForest | -0.0156 | 0.0292 | 4 |
| XGBoost | -0.0058 | 0.0281 | 6 |
| LightGBM | -0.0044 | 0.0220 | 6 |

**Final confusion matrices, Context arm (out-of-fold, 500 rows; TN / FP / FN / TP):**

| Features | Model | TN | FP | FN | TP |
|---|---|---|---|---|---|
| Context (in-fold) | LogisticRegression | 209 | 75 | 143 | 73 |
| Context (in-fold) | RandomForest | 214 | 70 | 148 | 68 |
| Context (in-fold) | XGBoost | 203 | 81 | 135 | 81 |
| Context (in-fold) | LightGBM | 195 | 89 | 128 | 88 |

**Findings:**
- **The conclusion is unchanged, now on a leak-free evaluation:** mean delta AUC is negative for all four models (-0.0011 to -0.0156), each smaller in magnitude than its split-to-split std, and context was better in only 4-7 of 15 splits. The industry-cohort context feature gives no measurable improvement over firm-level features.
- **If anything the feature adds noise:** RandomForest drops the most (-0.0156), but this is still inside its std (0.029), so it is reported as "no measurable gain", not as harm.
- **Accuracy vs the 0.568 majority baseline (Context arm):** only RandomForest (0.573) is above it; LogisticRegression (0.569) ties; XGBoost (0.559) and LightGBM (0.554) are below. FN > FP for all four models.

**Remaining caveats:** the 15 splits overlap, so std and "splits better" are descriptive, not a significance test. Each fold's peer groups are built from about 80% of the data, so the in-fold feature is somewhat noisier than the all-data version by construction. A descriptive `revenue_vs_trend` column is still computed on all rows, but only for the app's peer-comparison text; no model reads it.

---

## Decision 16 — Modules 4-6 built; priorities reset (Oct 21)

**Context:** The final report is now due Oct 22 (to the supervising professor); the presentation is at the end of the month. The user chose to finish the working project first and write the report afterward.

**What was built:** a template-based commentary layer (`commentary.py`), a shared service layer (`service.py`), a FastAPI backend (`api.py`), a Streamlit frontend (`app.py`, calls the API over HTTP), README, ROADMAP, and Docker files. The user confirmed on Oct 21 that the app runs on their machine.

**Choices:**
- **Served model:** Logistic Regression on firm-level (baseline) features. The context feature gave no gain (Decisions 14-15), and Logistic Regression's AUC (0.580) ties the best model while giving the simplest probabilities to explain. Chosen after seeing CV results, a mild selection effect that is inside noise.
- **Known startups** get an out-of-fold probability (scored by a fold that did not train on them); startups entered by hand use the model trained on all 500 rows.
- **Commentary is template-based, not an LLM call:** no API key was available and the deadline is tight. The function signature is stable, so a real LLM can replace it later (V2). It always includes a reliability caveat quoting the real numbers (AUC about 0.58, 56.8% majority baseline, 7-point series). Wording thresholds: P >= 0.60 "leans profitable", <= 0.40 "leans not profitable", otherwise "close to a coin flip". The text only explains; it never changes a prediction (Decision 6).
- **Forecast in the app:** Prophet (seasonality off) fit on all 7 cohorts, predicting the 2025 cohort. This is re-implemented in `service.py`, so its settings may differ slightly from Module 2's `forecast.py`; Module 2's reported numbers are unchanged.
- **Auth:** one shared API key in the `X-API-Key` header, read from an environment variable. Demo-grade, not production security.

**Not verified:** the Docker files are untested and need `DB_URL` in `classify.py` to read an environment variable.

**Decision 10 note:** these modules are mostly plumbing and were written by Claude. The owed rewrite of `forecast.py` by the user (for understanding) is still outstanding.

---

## Decision 17 — Final report, presentation and demo fixes (Oct 27): project closed

**Status: V1 complete and submitted.** The final report went to the supervisor; the presentation was delivered on Oct 27, ahead of the Nov 1 deadline. Full scope was kept (Decisions 9, 12), and the deadline was met.

**Final report (PBL format, ~37 pages incl. annexures):** follows the department template (Introduction, Background Theory, Methodology, Result and Analysis, Conclusion, References) with a clickable table of contents, list of tables and list of figures; all code is in Annexures A-F. A review pass removed unsupported claims (e.g. a statement that most published studies overstate accuracy), redrew Fig.5, added a Fig.8 slot for an app screenshot, and fixed the Chapter 4 title and all static page numbers.

**Demo bug fixed (commentary.py):** the commentary wrote money as `$35.3M ... $38.2M`. Streamlit renders text between two `$` signs as a LaTeX formula, which produced garbled text ("downabout838.2M"). Amounts are now written as `35.3M USD`, matching the rest of the app. Lesson: never put raw `$` in text passed to `st.write` / `st.markdown`. Predictions and metrics were unaffected; this was display-only.

**Reading of the numbers (for the demo and viva):** an individual prediction such as 56% is a probability for one startup; ROC-AUC about 0.58 is how well the model ranks profitable above unprofitable startups across all 500. Neither is evidence of high predictive accuracy, and the app says so.

**Still open (not blocking V1):** Docker files untested; the user's independent rewrite of `forecast.py` (Decision 10) is still owed; the Python version in the report's Table 1 (3.9) was inferred and should be confirmed; region effect was never tested separately.

---

## Checkpoint status (Oct 16)

- **Oct 17 checkpoint (Decision 9): met.** Module 2 completed Oct 14, so no scope cut is triggered. Full scope stands, with the Nov 1 deadline risk still accepted.
- Modules 1-3 complete. Next: Module 4 (LLM commentary layer), then API, Streamlit, Docker, paper.
- **Update (Oct 21):** Modules 4-6 built and running locally (Decision 16); in-fold context feature adopted (Decision 15). Remaining: final report (due Oct 22), presentation preparation, Docker verification.
- **Update (Oct 27):** report submitted and presentation done (Decision 17). Only optional follow-ups remain (Docker check, `forecast.py` rewrite).

---

## Explicitly out of scope (V1)

- React dashboard (deferred to V2)
- Plotly interactive visualizations (deferred to V2)
- Real-time data feeds
- Multi-user roles beyond basic auth

**Reasoning:** Each of these adds real time (2-3+ days apiece) without adding to the core question being answered. Cutting them protects the Nov 1 deadline and the research paper timeline running in parallel.
