"""Run ONCE on your Mac with the Postgres container up:
    python3 export_data.py
Writes data/startups.csv from the `startups` table, so the deployed app needs no database."""
import pandas as pd
from sqlalchemy import create_engine

URL = "postgresql+psycopg2://postgres:startuppulse@localhost:5432/startuppulse"
df = pd.read_sql("SELECT * FROM startups;", create_engine(URL))
df["profitable"] = df["profitable"].astype(int)
df.to_csv("data/startups.csv", index=False)
print(len(df), "rows ->", "data/startups.csv", "| columns:", list(df.columns))
