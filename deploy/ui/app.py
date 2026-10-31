"""
StartupPulse - Streamlit frontend (Module 6).

Talks to the FastAPI backend over HTTP; it contains no model code.
Run (with the API already running on port 8000):
    streamlit run app.py
"""
import os

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="StartupPulse", page_icon="📈", layout="wide")

DEFAULT_URL = os.environ.get("STARTUPPULSE_API_URL", "http://localhost:8000")
DEFAULT_KEY = os.environ.get("STARTUPPULSE_API_KEY", "dev-key")

if os.environ.get("STARTUPPULSE_API_KEY"):
    # Deployed: URL and key come from secrets; visitors never see or edit them.
    api_url, api_key = DEFAULT_URL, DEFAULT_KEY
else:
    with st.sidebar:
        st.header("Connection")
        api_url = st.text_input("API URL", DEFAULT_URL)
        api_key = st.text_input("API key", DEFAULT_KEY, type="password")


class ApiError(Exception):
    pass


@st.cache_data(ttl=300, show_spinner=False)
def call(method: str, path: str, url: str, key: str, payload: dict = None):
    try:
        r = requests.request(method, url.rstrip("/") + path, json=payload,
                             headers={"X-API-Key": key}, timeout=60)
    except requests.RequestException:
        raise ApiError(f"Cannot reach the API at {url}. Is it running?")
    if r.status_code == 401:
        raise ApiError("API key rejected. Check the key in the sidebar.")
    if r.status_code == 404:
        raise ApiError(r.json().get("detail", "Not found"))
    if r.status_code >= 400:
        raise ApiError(f"API error {r.status_code}: {r.text[:200]}")
    return r.json()


def get(path):
    return call("GET", path, api_url, api_key)


st.title("📈 StartupPulse")
st.caption("Industry cohort forecasts and startup profitability, explained in "
           "plain English. The models predict; the text only explains.")

try:
    info = get("/model-info")
    industries = get("/industries")["industries"]
    regions = get("/regions")["regions"]
except ApiError as e:
    st.error(str(e))
    st.stop()

st.info(f"**Read this first:** {info['note']} Guessing 'not profitable' every time "
        f"is right {info['majority_baseline_accuracy']:.1%} of the time; the model "
        f"reaches {info['cv_accuracy']:.1%} (ROC-AUC {info['cv_roc_auc']:.2f}).")

tab_lookup, tab_forecast, tab_custom, tab_about = st.tabs(
    ["Startup lookup", "Industry forecast", "Try your own startup", "About"])


def show_result(res: dict):
    c1, c2, c3 = st.columns(3)
    c1.metric("P(profitable)", f"{res['prob_profitable']:.0%}")
    c2.metric("Revenue vs. industry-cohort peers",
              f"{res['revenue_vs_trend']:+.1f} M USD")
    if "actual_profitable" in res:
        c3.metric("Actual label", "Profitable" if res["actual_profitable"]
                  else "Not profitable")
    st.caption(f"Probability type: {res['probability_kind']}")
    st.subheader("Plain-English summary")
    st.write(res["commentary"])


with tab_lookup:
    c1, c2 = st.columns([1, 2])
    ind = c1.selectbox("Industry", ["All"] + industries, key="lk_ind")
    path = "/startups?limit=500" + ("" if ind == "All" else f"&industry={ind}")
    names = get(path)["startups"]
    name = c2.selectbox("Startup", names, key="lk_name")
    if name:
        try:
            show_result(get(f"/startups/{name}"))
        except ApiError as e:
            st.error(str(e))

with tab_forecast:
    ind = st.selectbox("Industry", industries, key="fc_ind")
    try:
        f = get(f"/forecast/{ind}")
    except ApiError as e:
        st.error(str(e))
    else:
        hist = pd.DataFrame(f["history"]).set_index("cohort")
        fc = f["forecast"]
        last_c = hist.index.max()
        chart = pd.DataFrame(index=sorted(list(hist.index) + [fc["cohort"]]))
        chart["Observed"] = hist["revenue_musd"]
        chart.loc[[last_c, fc["cohort"]], "Forecast (Prophet)"] = [
            hist.loc[last_c, "revenue_musd"], fc["revenue_musd"]]
        st.line_chart(chart, y_label="Mean revenue (M USD)",
                      x_label="Founding cohort (5-year bins)")
        st.write(f"Forecast for the **{fc['cohort']}** cohort: "
                 f"**{fc['revenue_musd']:.1f} M USD** "
                 f"(model interval {fc['lower']:.1f} to {fc['upper']:.1f}).")
        st.caption("This is a cohort-trend forecast built from 7 points per "
                   "industry, not a calendar-year forecast. In our backtest no "
                   "model beat predicting the historical mean (all R² negative).")

with tab_custom:
    st.write("Enter a startup's numbers to get the model's probability. "
             "The peer comparison uses existing startups in the same industry "
             "and founding cohort.")
    with st.form("custom"):
        c1, c2, c3 = st.columns(3)
        name_in = c1.text_input("Name", "Your startup")
        industry = c2.selectbox("Industry", industries)
        region = c3.selectbox("Region", regions)
        c1, c2, c3 = st.columns(3)
        year = c1.number_input("Year founded", 1990, 2024, 2015)
        rounds = c2.number_input("Funding rounds", 0, 20, 2)
        funding = c3.number_input("Funding amount (M USD)", 0.0, 10000.0, 50.0)
        c1, c2, c3 = st.columns(3)
        val = c1.number_input("Valuation (M USD)", 0.0, 100000.0, 200.0)
        rev = c2.number_input("Revenue (M USD)", 0.0, 10000.0, 30.0)
        emp = c3.number_input("Employees", 0, 100000, 100)
        share = st.number_input("Market share (%)", 0.0, 100.0, 5.0)
        go = st.form_submit_button("Predict")
    if go:
        payload = dict(name=name_in, industry=industry, region=region,
                       year_founded=int(year), funding_rounds=int(rounds),
                       funding_amount_musd=float(funding), valuation_musd=float(val),
                       revenue_musd=float(rev), employees=int(emp),
                       market_share_pct=float(share))
        try:
            show_result(call("POST", "/predict", api_url, api_key, payload))
        except ApiError as e:
            st.error(str(e))

with tab_about:
    st.markdown("""
**What this is.** A pipeline, two models, and a commentary layer.

- **Forecast:** mean revenue per industry and 5-year founding cohort, 5 models
  compared (Prophet best, LSTM failed on 6 points per series).
- **Profitability classifier:** 4 models, repeated 5-fold cross-validation.
  Only weak signal; the industry-context feature gave no measurable gain.
- **Commentary:** template text that explains the numbers. It never changes a
  prediction (the model predicts, the text explains).

**Limits, stated plainly.** 500 startups, likely simplified data; the
profitability label is a static snapshot, not a forecast of future profit.
Treat everything here as rough context, not investment advice.
""")
    st.json(info)
