"""Loading the tables written by the pipeline (data/processed) and the reference files."""
import json
import unicodedata
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED = PROJECT_ROOT / "data" / "processed"
REFERENCE = PROJECT_ROOT / "data" / "reference"


def name_key(name):
    """Upper case, no accents, single spaces: the same key the pipeline uses to match place names."""
    plain = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    return " ".join(plain.upper().replace("-", " ").split())


def _mtime(path):
    return path.stat().st_mtime


@st.cache_data(show_spinner=False)
def _read_csv(path, mtime, parse_dates=None, dtype=None):
    # mtime is part of the cache key, so a new pipeline run is picked up automatically
    return pd.read_csv(path, parse_dates=parse_dates, dtype=dtype)


def _load(name, parse_dates=None, dtype=None):
    path = PROCESSED / name
    if not path.exists():
        return None
    return _read_csv(str(path), _mtime(path), parse_dates=parse_dates, dtype=dtype).copy()


def production():
    df = _load("ren_daily_production.csv", parse_dates=["date"])
    return None if df is None else df.sort_values("date").reset_index(drop=True)


def prices():
    df = _load("ren_market_prices_daily.csv", parse_dates=["date"])
    return None if df is None else df.sort_values("date").reset_index(drop=True)


def mobility():
    df = _load("eredes_mobility_monthly.csv", parse_dates=["date"])
    if df is None:
        return None
    df["key"] = df["municipality"].map(name_key)
    return df


def population():
    df = _load("ine_population_municipalities.csv", dtype={"indicator": str})
    if df is None or df["population"].notna().sum() == 0:
        return None
    return df


def predictions():
    df = _load("model_predictions.csv", parse_dates=["date", "window_start"])
    if df is None or not {"window", "actual", "persistence"} <= set(df.columns):
        return None  # older schema, from before the dashboard version of 04_predictive_model
    return df


def window_errors():
    return _load("model_window_errors.csv", parse_dates=["window_start"])


def next_day():
    return _load("model_next_day.csv", parse_dates=["date", "based_on"])


@st.cache_data(show_spinner=False)
def _read_json(path, mtime):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def municipalities_geojson():
    path = REFERENCE / "municipalities_mainland.geojson"
    if not path.exists():
        return None
    return _read_json(str(path), _mtime(path))
