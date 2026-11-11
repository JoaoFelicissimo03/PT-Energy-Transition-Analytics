"""Shared fixtures: small synthetic tables with the same columns as the processed pipeline files."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))


@pytest.fixture(autouse=True)
def english():
    """Every test starts in English; tests of the Portuguese texts switch language themselves."""
    from core import i18n

    i18n.set_lang("en")
    yield
    i18n.set_lang("en")


def make_production(start="2022-01-01", end="2025-12-31", seed=1):
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start, end, freq="D")
    n = len(dates)
    df = pd.DataFrame({"date": dates})
    df["hydro_mwh"] = rng.uniform(20000, 50000, n)
    df["wind_mwh"] = rng.uniform(15000, 40000, n)
    df["solar_mwh"] = rng.uniform(5000, 20000, n)
    df["biomass_mwh"] = rng.uniform(6000, 8000, n)
    df["wave_mwh"] = np.nan
    df["natural_gas_mwh"] = rng.uniform(5000, 30000, n)
    df["other_thermal_mwh"] = 500.0
    df["coal_mwh"] = 0.0
    df["import_mwh"] = rng.uniform(5000, 40000, n)
    df["export_mwh"] = rng.uniform(1000, 10000, n)
    df["consumption_mwh"] = rng.uniform(120000, 150000, n)
    renewable = ["hydro_mwh", "wind_mwh", "solar_mwh", "biomass_mwh"]
    non_renewable = ["natural_gas_mwh", "other_thermal_mwh", "coal_mwh"]
    df["renewable_mwh"] = df[renewable].sum(axis=1)
    df["non_renewable_mwh"] = df[non_renewable].sum(axis=1)
    df["total_production_mwh"] = df["renewable_mwh"] + df["non_renewable_mwh"]
    df["pct_renewable"] = df["renewable_mwh"] / df["total_production_mwh"] * 100
    df["pct_renewable_incl_imports"] = df["renewable_mwh"] / (df["total_production_mwh"] + df["import_mwh"]) * 100
    return df


def make_prices(start="2022-01-01", end="2025-12-31", seed=2):
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start, end, freq="D")
    pt = rng.uniform(20, 150, len(dates))
    es = pt + rng.choice([0, 0, 0, 5], len(dates))
    return pd.DataFrame({"date": dates, "price_avg_pt": pt, "price_avg_es": es,
                         "market_split": np.abs(pt - es) > 1})


@pytest.fixture
def production():
    return make_production()


@pytest.fixture
def prices():
    return make_prices()
