"""Checks for the calculations behind the dashboard figures."""
import numpy as np
import pandas as pd
import pytest

from core import stats


# ----------------------------------------------------------------------------- periods
@pytest.mark.parametrize("period, days", [("30d", 30), ("12m", 365)])
def test_period_bounds_counts_back_from_last_day(period, days):
    start, end = stats.period_bounds(period, "2020-01-01", "2025-06-30")
    assert end == pd.Timestamp("2025-06-30")
    assert (end - start).days + 1 == days


def test_period_bounds_ytd_and_all():
    assert stats.period_bounds("ytd", "2020-01-01", "2025-06-30")[0] == pd.Timestamp("2025-01-01")
    assert stats.period_bounds("all", "2020-03-04", "2025-06-30")[0] == pd.Timestamp("2020-03-04")


def test_period_bounds_never_starts_before_the_data():
    start, _ = stats.period_bounds("12m", "2025-05-01", "2025-06-30")
    assert start == pd.Timestamp("2025-05-01")


def test_period_bounds_rejects_unknown_key():
    with pytest.raises(ValueError):
        stats.period_bounds("week", "2020-01-01", "2025-01-01")


def test_covers_detects_missing_comparison_year(production):
    assert stats.covers(production, pd.Timestamp("2023-01-01"), pd.Timestamp("2023-12-31"))
    assert not stats.covers(production, pd.Timestamp("2021-01-01"), pd.Timestamp("2021-12-31"))


def test_full_years_ignores_partial_years():
    df = pd.DataFrame({"date": pd.date_range("2021-10-27", "2024-03-01")})
    assert stats.full_years(df) == [2022, 2023]


# ----------------------------------------------------------------------------- shares
def test_renewable_share_is_energy_weighted():
    # Day 1: 90 of 100 MWh renewable. Day 2: 10 of 300 MWh. The mean of daily shares would be 46.7%.
    df = pd.DataFrame({"renewable_mwh": [90.0, 10.0], "total_production_mwh": [100.0, 300.0],
                       "import_mwh": [0.0, 100.0]})
    assert stats.renewable_share(df) == pytest.approx(100 / 400 * 100)
    assert stats.renewable_share(df, "imports") == pytest.approx(100 / 500 * 100)


def test_renewable_share_of_nothing_is_nan():
    empty = pd.DataFrame(columns=["renewable_mwh", "total_production_mwh", "import_mwh"])
    assert np.isnan(stats.renewable_share(empty))


def test_mix_adds_up_to_100(production):
    for definition in ("domestic", "imports"):
        shares = stats.mix(production, definition)
        assert sum(shares.values()) == pytest.approx(100)
        assert ("Imports" in shares) == (definition == "imports")


@pytest.mark.parametrize("days, unit", [(30, "day"), (200, "week"), (900, "month")])
def test_daily_profile_bucket_size(production, days, unit):
    _, got = stats.daily_profile(production.tail(days))
    assert got == unit


def test_records_without_previous_year():
    df = pd.DataFrame({"date": pd.date_range("2025-01-01", "2025-06-30")})
    df["renewable_mwh"], df["total_production_mwh"], df["import_mwh"] = 80.0, 100.0, 10.0
    rec = stats.records(df)
    assert rec["best_year"] is None
    assert np.isnan(rec["this_year_change"])
    assert rec["this_year"] == pytest.approx(80)


# ----------------------------------------------------------------------------- energy mix over years
def test_biggest_drop_finds_the_largest_gap():
    annual = pd.DataFrame({"hydro_mwh": [10, 30], "wind_mwh": [20, 25]}, index=[2022, 2024])
    assert stats.biggest_drop(annual, 2022, 2024, ["hydro_mwh", "wind_mwh"]) == ("hydro_mwh", 10, 30)


def test_variability_skips_sources_without_output(production):
    cv = stats.variability(production, [2022, 2025])
    assert "wave_mwh" not in cv.columns
    assert list(cv.index) == [2022, 2025]


# ----------------------------------------------------------------------------- prices
@pytest.mark.parametrize("period", ["30d", "12m", "ytd", "all"])
def test_price_summary_every_period(prices, period):
    out = stats.price_summary(prices, period)
    assert out["avg"] > 0
    if period == "all":
        assert np.isnan(out["change_pct"])
    else:
        assert out["change_pct"] == pytest.approx((out["avg"] / out["prev_avg"] - 1) * 100)


def test_price_summary_without_previous_year():
    df = pd.DataFrame({"date": pd.date_range("2025-01-01", "2025-03-31"), "price_avg_pt": 50.0,
                       "price_avg_es": 50.0, "market_split": False})
    out = stats.price_summary(df, "30d")
    assert np.isnan(out["prev_avg"]) and out["first_full_year"] is None


def test_price_series_switches_to_months(prices):
    _, unit = stats.price_series(prices, pd.Timestamp("2025-10-01"), pd.Timestamp("2025-12-31"), ["pt"])
    assert unit == "day"
    series, unit = stats.price_series(prices, pd.Timestamp("2024-01-01"), pd.Timestamp("2025-12-31"), ["pt", "es"])
    assert unit == "month" and len(series) == 24


def test_price_correlation_needs_twenty_days(production, prices):
    short = stats.price_correlation_by_year(production, prices, "domestic",
                                            pd.Timestamp("2025-12-20"), pd.Timestamp("2025-12-31"))
    assert short.empty
    full = stats.price_correlation_by_year(production, prices, "imports",
                                           pd.Timestamp("2024-01-01"), pd.Timestamp("2025-12-31"))
    assert list(full["year"]) == [2024, 2025]
    assert full["corr"].between(-1, 1).all()


# ----------------------------------------------------------------------------- electric mobility
def test_municipality_totals_per_resident():
    mob = pd.DataFrame({"date": pd.to_datetime(["2025-01-01", "2025-02-01"]), "key": ["LISBOA"] * 2,
                        "district": ["Lisboa"] * 2, "municipality": ["Lisboa"] * 2, "energy_mwh": [10.0, 20.0]})
    pop = pd.DataFrame({"key": ["LISBOA"], "population": [1000]})
    totals = stats.municipality_totals(mob, pop)
    assert totals.loc[0, "energy_mwh"] == 30
    assert totals.loc[0, "kwh_per_resident"] == pytest.approx(30)
    assert "kwh_per_resident" not in stats.municipality_totals(mob).columns


def test_district_shares_sum_to_100():
    mob = pd.DataFrame({"district": ["A", "A", "B"], "energy_mwh": [1.0, 1.0, 2.0]})
    shares = stats.district_shares(mob)
    assert shares.sum() == pytest.approx(100) and shares.index[0] in ("A", "B")


# ----------------------------------------------------------------------------- forecasting
def make_predictions():
    dates = pd.date_range("2024-01-01", periods=120)
    window_start = np.where(np.arange(120) < 60, dates[0], dates[60])
    actual = np.full(120, 80.0)
    return pd.DataFrame({"date": dates, "window": np.repeat([1, 2], 60), "window_start": window_start,
                         "actual": actual, "persistence": actual + 1, "mean_7d": actual + 2,
                         "linear_regression": np.r_[actual[:60] + 0.5, actual[60:] + 3],
                         "climatology": actual - 5, "prophet": actual + 4})


def test_leaderboard_scores_and_counts():
    preds = make_predictions()
    starts = stats.windows_in_period(preds, "all")
    table, per_window = stats.leaderboard(preds, starts, stats.MODELS)
    assert table.loc["persistence", "mae"] == pytest.approx(1)
    assert table.loc["linear_regression", "beats_persistence"] == 1
    assert table.loc["climatology", "bias"] == pytest.approx(-5)
    assert table["windows"].iloc[0] == 2 and len(per_window) == 2
    assert list(table.index[:3]) == ["persistence", "linear_regression", "mean_7d"]


def test_windows_in_last_12_months():
    preds = make_predictions()
    assert len(stats.windows_in_period(preds, "12m")) == 2
