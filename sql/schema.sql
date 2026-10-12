-- StartupPulse schema (Module 1)
-- Safe to re-run: drops and recreates the table.

DROP TABLE IF EXISTS startups;

CREATE TABLE startups (
    id                   SERIAL PRIMARY KEY,
    name                 TEXT        NOT NULL UNIQUE,
    industry             TEXT        NOT NULL,
    funding_rounds       INTEGER     NOT NULL CHECK (funding_rounds >= 0),
    funding_amount_musd  NUMERIC     NOT NULL CHECK (funding_amount_musd >= 0),
    valuation_musd       NUMERIC     NOT NULL CHECK (valuation_musd >= 0),
    revenue_musd         NUMERIC     NOT NULL CHECK (revenue_musd >= 0),
    employees            INTEGER     NOT NULL CHECK (employees >= 0),
    market_share_pct     NUMERIC     NOT NULL CHECK (market_share_pct >= 0 AND market_share_pct <= 100),
    profitable           BOOLEAN     NOT NULL,   -- classification label
    year_founded         INTEGER     NOT NULL CHECK (year_founded BETWEEN 1900 AND 2100),
    cohort_bin           INTEGER     NOT NULL,   -- 5-year founding cohort, e.g. 1995
    region               TEXT        NOT NULL,
    exit_status          TEXT        NOT NULL CHECK (exit_status IN ('Private','Acquired','IPO'))
);

-- Module 2 groups by industry + cohort constantly, so index it.
CREATE INDEX idx_startups_industry_cohort ON startups (industry, cohort_bin);
