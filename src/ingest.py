"""
StartupPulse - Module 1: ingestion pipeline
CSV -> clean/validate -> PostgreSQL

Usage:
    python3 src/ingest.py --dry-run   # clean + validate only, no database
    python3 src/ingest.py             # clean + validate + load into Postgres
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "startup.csv"
SCHEMA_PATH = ROOT / "sql" / "schema.sql"
DB_URL = "postgresql+psycopg2://postgres:startuppulse@localhost:5432/startuppulse"

COLUMN_MAP = {
    "Startup Name": "name",
    "Industry": "industry",
    "Funding Rounds": "funding_rounds",
    "Funding Amount (M USD)": "funding_amount_musd",
    "Valuation (M USD)": "valuation_musd",
    "Revenue (M USD)": "revenue_musd",
    "Employees": "employees",
    "Market Share (%)": "market_share_pct",
    "Profitable": "profitable",
    "Year Founded": "year_founded",
    "Region": "region",
    "Exit Status": "exit_status",
}
VALID_EXIT = {"Private", "Acquired", "IPO"}


def load_raw(path: Path) -> pd.DataFrame:
    # utf-8-sig strips the invisible BOM this CSV starts with
    return pd.read_csv(path, encoding="utf-8-sig")


def clean(df: pd.DataFrame) -> pd.DataFrame:
    report = []
    n0 = len(df)

    missing = [c for c in COLUMN_MAP if c not in df.columns]
    if missing:
        sys.exit(f"ERROR: missing expected columns: {missing}")

    df = df.rename(columns=COLUMN_MAP)[list(COLUMN_MAP.values())].copy()

    # nulls
    nulls = int(df.isnull().sum().sum())
    report.append(f"null cells: {nulls}")
    df = df.dropna()

    # strip whitespace on text columns
    for col in ["name", "industry", "region", "exit_status"]:
        df[col] = df[col].astype(str).str.strip()

    # duplicates
    dupes = int(df.duplicated(subset="name").sum())
    report.append(f"duplicate startup names dropped: {dupes}")
    df = df.drop_duplicates(subset="name")

    # types
    df["profitable"] = df["profitable"].astype(int).astype(bool)
    for col in ["funding_rounds", "employees", "year_founded"]:
        df[col] = df[col].astype(int)

    # value checks
    bad_exit = ~df["exit_status"].isin(VALID_EXIT)
    report.append(f"invalid exit_status rows dropped: {int(bad_exit.sum())}")
    df = df[~bad_exit]

    num_cols = ["funding_amount_musd", "valuation_musd", "revenue_musd",
                "employees", "funding_rounds"]
    neg = (df[num_cols] < 0).any(axis=1)
    report.append(f"negative-value rows dropped: {int(neg.sum())}")
    df = df[~neg]

    bad_share = ~df["market_share_pct"].between(0, 100)
    report.append(f"market share outside 0-100 dropped: {int(bad_share.sum())}")
    df = df[~bad_share]

    # derived: 5-year founding cohort (Decision 4)
    df["cohort_bin"] = (df["year_founded"] // 5) * 5

    print("--- cleaning report ---")
    print(f"rows in: {n0}, rows out: {len(df)}")
    for line in report:
        print(" ", line)
    return df.reset_index(drop=True)


def load_to_postgres(df: pd.DataFrame) -> None:
    from sqlalchemy import create_engine, text

    engine = create_engine(DB_URL)
    with engine.begin() as conn:
        conn.execute(text(SCHEMA_PATH.read_text()))
        df.to_sql("startups", conn, if_exists="append", index=False)
        count = conn.execute(text("SELECT COUNT(*) FROM startups")).scalar()
    print(f"--- loaded into Postgres: {count} rows in table 'startups' ---")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="clean only, skip database")
    args = ap.parse_args()

    df = clean(load_raw(CSV_PATH))
    print("\nIndustry x cohort_bin counts:")
    print(df.groupby(["industry", "cohort_bin"]).size().unstack(fill_value=0))

    if args.dry_run:
        print("\nDry run complete - nothing written to database.")
    else:
        load_to_postgres(df)


if __name__ == "__main__":
    main()
