"""Sanity checks on data/processed after a pipeline run.

The scheduled update (.github/workflows/update-data.yml) runs this before committing anything,
so a failed or partial download never replaces good data in the repository. It can also be run
by hand from the project root:

    python scripts/check_processed.py
"""
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"

MIN_PRODUCTION_DAYS = 1600   # the rolling window holds about 1,826 days
MAX_DAYS_BEHIND = 10         # REN publishes yesterday's data the next morning
MIN_MUNICIPALITIES = 270     # of the 278 mainland municipalities

REQUIRED = [
    "ren_daily_production.csv",
    "ren_market_prices_daily.csv",
    "eredes_mobility_monthly.csv",
    "model_predictions.csv",
    "model_metrics.csv",
    "model_window_errors.csv",
    "model_next_day.csv",
]


def main():
    problems = []

    missing = [name for name in REQUIRED if not (PROCESSED / name).exists()]
    if missing:
        problems.append(f"missing files: {', '.join(missing)}")
    else:
        production = pd.read_csv(PROCESSED / "ren_daily_production.csv", parse_dates=["date"])
        prices = pd.read_csv(PROCESSED / "ren_market_prices_daily.csv", parse_dates=["date"])
        mobility = pd.read_csv(PROCESSED / "eredes_mobility_monthly.csv")
        next_day = pd.read_csv(PROCESSED / "model_next_day.csv")

        last_day = production["date"].max().date()
        if len(production) < MIN_PRODUCTION_DAYS:
            problems.append(f"production has only {len(production)} days")
        if production["date"].duplicated().any():
            problems.append("production has duplicated dates")
        if last_day < date.today() - timedelta(days=MAX_DAYS_BEHIND):
            problems.append(f"production ends on {last_day}, more than {MAX_DAYS_BEHIND} days ago")
        if not production["pct_renewable"].dropna().between(0, 100).all():
            problems.append("renewable share outside 0-100%")
        if prices.empty:
            problems.append("no price data")
        if mobility["municipality"].nunique() < MIN_MUNICIPALITIES:
            problems.append(f"charging data covers {mobility['municipality'].nunique()} municipalities")
        if next_day.empty:
            problems.append("no next-day forecast")

        print(f"Production: {len(production)} days, last {last_day}")
        print(f"Prices: {len(prices)} days, last {prices['date'].max().date()}")
        print(f"Charging: {mobility['municipality'].nunique()} municipalities")

    if problems:
        print("Checks failed:")
        for problem in problems:
            print(f"  - {problem}")
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
