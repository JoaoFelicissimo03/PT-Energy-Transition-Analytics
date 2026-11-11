"""Checks that the generated sentences stay correct for any numbers the pipeline produces."""
import numpy as np
import pandas as pd
import pytest

from core import text


def test_formatters_handle_missing_values():
    for fn in (text.pct, text.pp, text.num):
        assert fn(np.nan) == "n/a" and fn(None) == "n/a"
    assert text.pct(81.63) == "81.6%"
    assert text.pp(5.06) == "+5.1 pp"
    assert text.num(23790.4) == "23,790"
    assert text.day("2026-10-07") == "7 Oct 2026"


@pytest.mark.parametrize("share, fraction", [(50, "half"), (62, "three in five"), (66, "two in three"),
                                             (76, "three in four"), (81, "four in five"), (89, "nine in ten"),
                                             (40, None)])
def test_share_fraction(share, fraction):
    assert text.share_fraction(share) == fraction


def test_now_headline_reads_naturally():
    assert text.now_headline(81.6, "domestic") == \
        "Four in every five units of electricity made in Portugal are renewable"
    assert text.now_headline(51, "imports") == "About half of the electricity supplied in Portugal is renewable"
    assert text.now_headline(38.2, "domestic") == "38% of the electricity made in Portugal is renewable"


@pytest.mark.parametrize("change, period, unit, expected", [
    (5.06, "30d", "pp", "+5.1 pp on the same 30 days last year"),
    (0.04, "ytd", "pp", "Almost no change on the same days last year"),
    (-0.04, "12m", "pp", "Almost no change on the 12 months before"),
    (np.nan, "30d", "pp", "No data for the same 30 days last year"),
    (1.0, "all", "pp", "Whole period in the data"),
    (119.4, "30d", "%", "+119% on the same 30 days last year"),
    (0.3, "30d", "%", "Almost no change on the same 30 days last year"),
])
def test_change_note(change, period, unit, expected):
    assert text.change_note(change, period, unit) == expected


@pytest.mark.parametrize("change, expected", [
    (250, "more than three times"), (119, "more than twice"), (9.6, "10% more than"),
    (-30, "30% less than"), (4.4, "about the same as"), (-4.6, "5% less than"),
])
def test_cost_headline(change, expected):
    assert expected in text.cost_headline(change, 80, "12m")


def test_cost_headline_without_comparison():
    assert text.cost_headline(np.nan, 98.2, "all") == "Wholesale electricity has averaged 98 EUR/MWh"
    assert text.cost_headline(10, 98.2, "all") == "Wholesale electricity has averaged 98 EUR/MWh"


def test_correlation_sentence():
    all_negative = pd.DataFrame({"corr": [-0.2, -0.4]})
    mixed = pd.DataFrame({"corr": [-0.2, 0.1, -0.3]})
    weak = pd.DataFrame({"corr": [0.2, 0.1, -0.3]})
    assert text.correlation_sentence(all_negative).startswith("Inside every year")
    assert text.correlation_sentence(mixed).startswith("In 2 of 3 years")
    assert "weak" in text.correlation_sentence(weak)
    assert text.correlation_sentence(pd.DataFrame()) == ""


def test_shift_headline_orders():
    assert text.shift_headline(None, None, None, None).startswith("Not enough")
    assert text.shift_headline(2022, 62.3, 2022, 62.3) == "62.3% renewable in 2022"
    assert text.shift_headline(2022, 62.3, 2024, 88.7) == "From 62.3% renewable in 2022 to 88.7% in 2024"
    assert text.shift_headline(2025, 70.0, 2023, 80.0).startswith("Renewables peaked at 80.0% in 2023")


def test_shift_subtitle_gas_direction():
    out = text.shift_subtitle(("hydro_mwh", 23790, 50333), 30000, 9000, 2022, 2024)
    assert "hydro: 23,790 MWh a day in 2022 against 50,333 in 2024" in out
    assert "70% lower in 2024" in out
    assert text.shift_subtitle(None, 1, 1, 2022, 2022).startswith("Pick a wider range")


def test_use_texts():
    shares = pd.Series({"Lisboa": 37.1, "Porto": 15.9, "Setubal": 10.8})
    assert text.use_headline(shares) == "Electric vehicle charging is concentrated around Lisboa and Porto"
    assert "spread" in text.use_headline(pd.Series({"A": 20.0, "B": 15.0, "C": 65.0}).iloc[[0, 1, 2]])
    assert text.use_headline(shares, "Porto").startswith("Porto district uses 15.9%")
    one_month = pd.Timestamp("2026-04-01")
    assert text.use_subtitle(shares, one_month, one_month).startswith("In Apr 2026")


def test_next_texts():
    table = pd.DataFrame({"mae": [2.6, 2.9, 5.0], "horizon": ["1 day", "1 day", "60 days"],
                          "beats_persistence": [np.nan, 8, 2], "windows": [18, 18, 18]},
                         index=["persistence", "linear_regression", "prophet"])
    assert text.next_headline(table) == "Tomorrow will most likely look a lot like today"
    assert "linear regression beat it in 8" in text.next_subtitle(table)
    table.loc["linear_regression", "mae"] = 2.0
    assert text.next_headline(table).startswith("Linear regression now beats")
