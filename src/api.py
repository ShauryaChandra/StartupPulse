"""
StartupPulse - FastAPI backend (Module 5).

Run from the project root:
    STARTUPPULSE_API_KEY=your-secret uvicorn src.api:app --port 8000
(or, from inside src/:  uvicorn api:app --port 8000)

Every endpoint except /health requires the header  X-API-Key: <your key>.
The key is read from the STARTUPPULSE_API_KEY environment variable; if unset,
the development key "dev-key" is used (fine for a local demo, not for deployment).
"""
import os
import secrets
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # import siblings

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

import service

API_KEY = os.environ.get("STARTUPPULSE_API_KEY", "dev-key")


def require_key(x_api_key: str = Header(default="")):
    if not secrets.compare_digest(x_api_key.encode(), API_KEY.encode()):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


app = FastAPI(
    title="StartupPulse API",
    version="1.0",
    description="Industry cohort forecasts, startup profitability probabilities, "
                "and plain-English commentary. Predictions come from the models; "
                "commentary only explains them.",
)


class StartupInput(BaseModel):
    name: str = "Your startup"
    industry: str
    region: str
    year_founded: int = Field(ge=1990, le=2024)
    funding_rounds: int = Field(ge=0, le=20)
    funding_amount_musd: float = Field(ge=0)
    valuation_musd: float = Field(ge=0)
    revenue_musd: float = Field(ge=0)
    employees: int = Field(ge=0)
    market_share_pct: float = Field(ge=0, le=100)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/model-info", dependencies=[Depends(require_key)])
def model_info():
    return service.MODEL_INFO


@app.get("/industries", dependencies=[Depends(require_key)])
def industries():
    return {"industries": service.industries()}


@app.get("/regions", dependencies=[Depends(require_key)])
def regions():
    return {"regions": sorted(service.get_data()["region"].unique().tolist())}


@app.get("/startups", dependencies=[Depends(require_key)])
def startups(industry: str = None, limit: int = Query(50, ge=1, le=500)):
    return {"startups": service.list_startups(industry, limit)}


@app.get("/startups/{name}", dependencies=[Depends(require_key)])
def startup(name: str):
    try:
        return service.analyze_known(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Startup '{name}' not found")


@app.get("/forecast/{industry}", dependencies=[Depends(require_key)])
def forecast(industry: str):
    try:
        return service.forecast_industry(industry)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Industry '{industry}' not found")


@app.post("/predict", dependencies=[Depends(require_key)])
def predict(body: StartupInput):
    try:
        return service.analyze_custom(body.model_dump())
    except KeyError:
        raise HTTPException(status_code=404,
                            detail=f"Industry '{body.industry}' not found")
