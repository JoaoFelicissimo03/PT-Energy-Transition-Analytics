"""Runs every chapter of the app headless across its filter combinations and fails on any exception.

Needs the processed files from the notebooks in data/processed. Without them the tests are skipped.
"""
import itertools
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "app.py"
PROCESSED = ROOT / "data" / "processed"

pytestmark = pytest.mark.skipif(not (PROCESSED / "ren_daily_production.csv").exists(),
                                reason="run the notebooks first to create data/processed")

PERIODS = ["30d", "12m", "ytd", "all"]
DEFINITIONS = ["domestic", "imports"]


def run(page, state=None, patch=None, lang="en"):
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.session_state["_keep_lang"] = lang
    for key, value in (state or {}).items():
        at.session_state[f"_keep_{key}"] = value
    if patch:
        patch()
    at.run()
    if page:
        at.switch_page(f"chapters/{page}.py")
        at.run()
    assert not at.exception, [e.message for e in at.exception]
    return at


def markdown_text(at):
    return " ".join(str(h.proto.body) for h in at.get("html"))


@pytest.mark.parametrize("period, definition", list(itertools.product(PERIODS, DEFINITIONS)))
def test_where_we_are(period, definition):
    at = run(None, {"period_now": period, "definition": definition})
    assert "Where we are" in markdown_text(at)


def test_how_we_got_here_ranges():
    years = sorted(pd.read_csv(PROCESSED / "ren_daily_production.csv", usecols=["date"],
                               parse_dates=["date"])["date"].dt.year.unique())
    ranges = [(years[0], years[-1]), (years[0], years[0]), (years[-1], years[-1]), (years[1], years[2])]
    for year_range, definition in itertools.product(ranges, DEFINITIONS):
        run("c2_shift", {"years_shift": tuple(int(y) for y in year_range), "definition": definition})


@pytest.mark.parametrize("sources", [[], ["solar_mwh"], ["hydro_mwh", "wind_mwh", "solar_mwh", "biomass_mwh",
                                                           "natural_gas_mwh", "import_mwh"]])
def test_how_we_got_here_sources(sources):
    run("c2_shift", {"sources_shift": sources})


@pytest.mark.parametrize("period, market, definition",
                         list(itertools.product(PERIODS, ["pt", "es", "both"], DEFINITIONS)))
def test_what_it_costs(period, market, definition):
    run("c3_cost", {"period_cost": period, "market_cost": market, "definition": definition})


def mobility_months():
    mob = pd.read_csv(PROCESSED / "eredes_mobility_monthly.csv", parse_dates=["date"])
    return [pd.Timestamp(m) for m in sorted(mob["date"].unique())], sorted(mob["district"].unique())


def test_where_it_is_used_months_and_districts():
    months, districts = mobility_months()
    ranges = [(months[0], months[-1]), (months[0], months[0]), (months[-1], months[-1])]
    for month_range, district in itertools.product(ranges, ["__all__", districts[0], "Lisboa"]):
        run("c4_use", {"months_use": month_range, "district_use": district})


def test_where_it_is_used_with_population(monkeypatch):
    """The per-resident view, using made-up population numbers (never written to disk)."""
    from core import data

    mob = data.mobility()
    fake = mob[["district", "municipality", "key"]].drop_duplicates().assign(
        population=20000, year=2024, indicator="0008273")
    monkeypatch.setattr(data, "population", lambda: fake)
    for measure in ["resident", "total"]:
        at = run("c4_use", {"measure_use": measure})
        assert "INE, resident population" in markdown_text(at)


@pytest.mark.parametrize("period, models", list(itertools.product(
    ["12m", "all"], [[], ["persistence"], ["persistence", "mean_7d", "linear_regression", "climatology", "prophet"]])))
def test_what_comes_next(period, models):
    run("c5_next", {"period_next": period, "models_next": models})


def test_what_comes_next_first_window():
    preds = pd.read_csv(PROCESSED / "model_predictions.csv", parse_dates=["window_start"])
    run("c5_next", {"window_next": preds["window_start"].min()})


@pytest.mark.parametrize("year", [2024, 2023])
def test_blackout(year):
    at = run("bonus_blackout", {"compare_blackout": year})
    assert "28 April 2025" in markdown_text(at)


@pytest.mark.parametrize("page, loader", [(None, "production"), (None, "prices"), (None, "mobility"),
                                          (None, "predictions"), (None, "next_day"), ("c2_shift", "production"), ("c3_cost", "prices"),
                                          ("c4_use", "mobility"), ("c4_use", "municipalities_geojson"),
                                          ("c5_next", "predictions"), ("c5_next", "next_day"),
                                          ("bonus_blackout", "production")])
def test_missing_pipeline_files_show_a_message(monkeypatch, page, loader):
    """A chapter whose input file is missing explains what to run instead of failing."""
    from core import data

    monkeypatch.setattr(data, loader, lambda: None)
    run(page)
