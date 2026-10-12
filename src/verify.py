"""
StartupPulse - quick post-load sanity check.
Run after ingest.py to confirm the database matches expectations.
"""
from sqlalchemy import create_engine, text

DB_URL = "postgresql+psycopg2://postgres:startuppulse@localhost:5432/startuppulse"

CHECKS = [
    ("Total rows", "SELECT COUNT(*) FROM startups;"),
    ("Distinct industries", "SELECT COUNT(DISTINCT industry) FROM startups;"),
    ("Distinct regions", "SELECT COUNT(DISTINCT region) FROM startups;"),
    ("Profitable count", "SELECT COUNT(*) FROM startups WHERE profitable = true;"),
    ("Not profitable count", "SELECT COUNT(*) FROM startups WHERE profitable = false;"),
    ("Year range", "SELECT MIN(year_founded), MAX(year_founded) FROM startups;"),
    ("Cohort bins present", "SELECT DISTINCT cohort_bin FROM startups ORDER BY cohort_bin;"),
]

engine = create_engine(DB_URL)
with engine.connect() as conn:
    for label, query in CHECKS:
        result = conn.execute(text(query)).fetchall()
        print(f"{label}: {result}")

    print("\nSample rows:")
    sample = conn.execute(text("SELECT * FROM startups LIMIT 3;")).fetchall()
    for row in sample:
        print(" ", row)
