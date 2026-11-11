"""Calculations behind every figure and sentence in the dashboard. Pure pandas, no Streamlit."""
import numpy as np
import pandas as pd

RENEWABLE = ["hydro_mwh", "wind_mwh", "solar_mwh", "biomass_mwh", "wave_mwh"]
NON_RENEWABLE = ["natural_gas_mwh", "other_thermal_mwh", "coal_mwh"]
FULL_YEAR_MIN_DAYS = 360


# ----------------------------------------------------------------------------- periods
def period_bounds(period, first, last):
    """Start and end dates for a period key, counted back from the last day with data."""
    first, last = pd.Timestamp(first), pd.Timestamp(last)
    if period == "30d":
        start = last - pd.Timedelta(days=29)
    elif period == "12m":
        start = last - pd.Timedelta(days=364)
    elif period == "ytd":
        start = pd.Timestamp(year=last.year, month=1, day=1)
    elif period == "all":
        start = first
    else:
        raise ValueError(f"Unknown period: {period}")
    return max(start, first), last


def year_before(start, end):
    return start - pd.DateOffset(years=1), end - pd.DateOffset(years=1)


def between(df, start, end, column="date"):
    return df[(df[column] >= start) & (df[column] <= end)]


def covers(df, start, end, column="date", min_share=0.9):
    """True if the table has data for at least min_share of the days between start and end."""
    expected = (end - start).days + 1
    return len(between(df, start, end, column)) >= min_share * expected


def full_years(df):
    days = df.groupby(df["date"].dt.year).size()
    return [int(y) for y, n in days.items() if n >= FULL_YEAR_MIN_DAYS]


# ----------------------------------------------------------------------------- shares
def renewable_share(df, definition="domestic"):
    """Renewable share of a set of days, weighted by energy (not an average of daily shares)."""
    if df.empty:
        return np.nan
    denominator = df["total_production_mwh"].sum()
    if definition == "imports":
        denominator += df["import_mwh"].fillna(0).sum()
    return df["renewable_mwh"].sum() / denominator * 100 if denominator else np.nan


def yearly_shares(df, definition="domestic"):
    rows = []
    for year, group in df.groupby(df["date"].dt.year):
        rows.append({"year": int(year), "days": len(group), "share": renewable_share(group, definition)})
    out = pd.DataFrame(rows).set_index("year")
    out["full"] = out["days"] >= FULL_YEAR_MIN_DAYS
    return out


def mix(df, definition="domestic"):
    """Share of each source in production (plus imports with the import definition), in percent."""
    sources = {
        "hydro_mwh": "Hydro",
        "wind_mwh": "Wind",
        "solar_mwh": "Solar",
        "biomass_mwh": "Biomass",
    }
    totals = {label: df[col].fillna(0).sum() for col, label in sources.items()}
    totals["Gas and other"] = df[NON_RENEWABLE].fillna(0).sum().sum()
    if definition == "imports":
        totals["Imports"] = df["import_mwh"].fillna(0).sum()
    grand = sum(totals.values())
    return {k: v / grand * 100 for k, v in totals.items()} if grand else {}


def daily_profile(df, definition="domestic"):
    """Renewable vs non-renewable energy, bucketed so the chart keeps a readable number of bars."""
    days = len(df)
    freq = "D" if days <= 90 else ("W" if days <= 400 else "MS")
    frame = df.set_index("date")
    non_renewable = frame[NON_RENEWABLE].fillna(0).sum(axis=1)
    if definition == "imports":
        non_renewable = non_renewable + frame["import_mwh"].fillna(0)
    out = pd.DataFrame({"renewable": frame["renewable_mwh"], "non_renewable": non_renewable})
    out = out.resample(freq).mean().dropna()
    return out, {"D": "day", "W": "week", "MS": "month"}[freq]


def records(df, definition="domestic"):
    """Best and weakest full year, and the current year so far against the same days a year before."""
    yearly = yearly_shares(df, definition)
    full = yearly[yearly["full"]]
    last = df["date"].max()
    ytd_start = pd.Timestamp(year=last.year, month=1, day=1)
    this_year = renewable_share(between(df, ytd_start, last), definition)
    prev_start, prev_end = year_before(ytd_start, last)
    prev = between(df, prev_start, prev_end)
    last_year = renewable_share(prev, definition) if covers(df, prev_start, prev_end) else np.nan
    return {
        "best_year": int(full["share"].idxmax()) if len(full) else None,
        "best_share": full["share"].max() if len(full) else np.nan,
        "weak_year": int(full["share"].idxmin()) if len(full) else None,
        "weak_share": full["share"].min() if len(full) else np.nan,
        "this_year": this_year,
        "this_year_label": last.year,
        "this_year_change": this_year - last_year,
    }


# ----------------------------------------------------------------------------- energy mix over years
def annual_production(df, sources):
    """Average MWh per day for each source and year."""
    out = df.groupby(df["date"].dt.year)[sources].mean()
    out.index.name = "year"
    return out


def seasonality(df, definition="domestic"):
    """Energy-weighted renewable share by calendar month."""
    rows = []
    for month, group in df.groupby(df["date"].dt.month):
        rows.append({"month": int(month), "share": renewable_share(group, definition)})
    return pd.DataFrame(rows).set_index("month")["share"]


def variability(df, years):
    """Coefficient of variation of daily output for each renewable source, in each of the given years."""
    active = [s for s in RENEWABLE if df[s].fillna(0).max() > 0]
    subset = df[df["date"].dt.year.isin(years)]
    return subset.groupby(subset["date"].dt.year)[active].agg(lambda s: s.std() / s.mean())


def biggest_drop(annual, weak_year, best_year, sources):
    """The renewable source with the largest shortfall in the weakest year compared with the best year."""
    gaps = {s: annual.loc[best_year, s] - annual.loc[weak_year, s] for s in sources if s in annual.columns}
    if not gaps:
        return None
    source = max(gaps, key=gaps.get)
    return source, annual.loc[weak_year, source], annual.loc[best_year, source]


# ----------------------------------------------------------------------------- prices
MARKET_COLUMN = {"pt": "price_avg_pt", "es": "price_avg_es"}


def price_summary(prices, period, market="pt"):
    col = MARKET_COLUMN[market]
    first, last = prices["date"].min(), prices["date"].max()
    start, end = period_bounds(period, first, last)
    now = between(prices, start, end)
    out = {
        "start": start,
        "end": end,
        "avg": now[col].mean(),
        "all_avg": prices[col].mean(),
        "split_share": now["market_split"].mean() * 100,
        "prev_avg": np.nan,
        "change_pct": np.nan,
    }
    if period != "all":
        prev_start, prev_end = year_before(start, end)
        if covers(prices, prev_start, prev_end):
            out["prev_avg"] = between(prices, prev_start, prev_end)[col].mean()
            out["change_pct"] = (out["avg"] / out["prev_avg"] - 1) * 100
    years = full_years(prices)
    out["first_full_year"] = years[0] if years else None
    out["first_full_split"] = (
        prices[prices["date"].dt.year == years[0]]["market_split"].mean() * 100 if years else np.nan
    )
    return out


def price_series(prices, start, end, markets):
    """Daily values for short periods, monthly averages otherwise."""
    window = between(prices, start, end).set_index("date")
    cols = [MARKET_COLUMN[m] for m in markets]
    if (end - start).days <= 120:
        return window[cols], "day"
    return window[cols].resample("MS").mean(), "month"


def price_correlation_by_year(production, prices, definition, start, end):
    """Correlation between the daily renewable share and the daily Portuguese price, inside each year."""
    share_col = "pct_renewable" if definition == "domestic" else "pct_renewable_incl_imports"
    merged = production[["date", share_col]].merge(prices[["date", "price_avg_pt"]], on="date")
    merged = between(merged, start, end)
    rows = []
    for year, group in merged.groupby(merged["date"].dt.year):
        if len(group) >= 20:
            rows.append({"year": int(year), "days": len(group), "corr": group[share_col].corr(group["price_avg_pt"])})
    return pd.DataFrame(rows)


def split_share_by_year(prices):
    out = prices.groupby(prices["date"].dt.year).agg(days=("date", "size"), share=("market_split", "mean"))
    out["share"] *= 100
    out["full"] = out["days"] >= FULL_YEAR_MIN_DAYS
    return out


# ----------------------------------------------------------------------------- electric mobility
def mobility_window(mob, month_start, month_end, district=None):
    out = mob[(mob["date"] >= month_start) & (mob["date"] <= month_end)]
    return out if not district else out[out["district"] == district]


def municipality_totals(mob_window, population=None):
    totals = (
        mob_window.groupby(["key", "district", "municipality"], as_index=False)["energy_mwh"].sum()
    )
    if population is not None:
        totals = totals.merge(population[["key", "population"]], on="key", how="left")
        totals["kwh_per_resident"] = totals["energy_mwh"] * 1000 / totals["population"]
    return totals


def district_shares(mob_window):
    shares = mob_window.groupby("district")["energy_mwh"].sum().sort_values(ascending=False)
    return shares / shares.sum() * 100


# ----------------------------------------------------------------------------- forecasting
MODELS = ["persistence", "mean_7d", "linear_regression", "climatology", "prophet"]
HORIZON = {"persistence": "1 day", "mean_7d": "1 day", "linear_regression": "1 day",
           "climatology": "60 days", "prophet": "60 days"}


def windows_in_period(predictions, period):
    starts = predictions["window_start"].drop_duplicates().sort_values()
    if period == "12m":
        cutoff = predictions["date"].max() - pd.Timedelta(days=364)
        starts = starts[starts >= cutoff]
    return list(starts)


def leaderboard(predictions, window_starts, models):
    subset = predictions[predictions["window_start"].isin(window_starts)]
    errors = subset[models].sub(subset["actual"], axis=0)
    per_window = errors.abs().groupby(subset["window_start"]).mean()
    table = pd.DataFrame({
        "mae": per_window.mean(),
        "bias": errors.mean(),
        "horizon": pd.Series(HORIZON),
    }).loc[models]
    if "persistence" in per_window:
        beats = per_window.lt(per_window["persistence"], axis=0).sum()
        table["beats_persistence"] = beats
        table.loc["persistence", "beats_persistence"] = np.nan
    table["windows"] = len(per_window)
    return table.sort_values(["horizon", "mae"]), per_window


# ----------------------------------------------------------------------------- bonus: the 2025 blackout
BLACKOUT_DAY = pd.Timestamp("2025-04-28")
SPRING = [4, 5, 6]
BLACKOUT_SOURCES = ["hydro_mwh", "wind_mwh", "solar_mwh", "biomass_mwh", "natural_gas_mwh",
                    "other_thermal_mwh", "import_mwh", "export_mwh", "consumption_mwh"]


def blackout_available(production, compare_year):
    years = production["date"].dt.year
    spring = production["date"].dt.month.isin(SPRING)
    return all(((years == y) & spring).sum() >= 85 for y in (2025, compare_year))


def blackout_comparison(production, compare_year):
    spring = production[production["date"].dt.month.isin(SPRING)]
    means = spring[spring["date"].dt.year.isin([compare_year, 2025])].groupby(spring["date"].dt.year)[
        BLACKOUT_SOURCES + ["renewable_mwh", "total_production_mwh"]
    ].mean()
    share = {
        y: means.loc[y, "renewable_mwh"] / means.loc[y, "total_production_mwh"] * 100 for y in means.index
    }
    change = means.loc[2025] - means.loc[compare_year]
    pct = change / means.loc[compare_year].replace(0, np.nan) * 100
    return means, change, pct, share


def blackout_timeline(production, compare_year, low_import_mwh=1000):
    daily = production.set_index("date")
    before, after = daily.loc[BLACKOUT_DAY], daily.loc[BLACKOUT_DAY + pd.Timedelta(days=1)]
    run, day = 0, BLACKOUT_DAY + pd.Timedelta(days=1)
    while day in daily.index and daily.loc[day, "import_mwh"] < low_import_mwh:
        run += 1
        day += pd.Timedelta(days=1)
    monthly = daily[["natural_gas_mwh", "import_mwh"]].resample("MS").mean()
    recovery = None
    for month in range(5, 13):
        now, then = pd.Timestamp(2025, month, 1), pd.Timestamp(compare_year, month, 1)
        if now in monthly.index and then in monthly.index:
            if monthly.loc[now, "import_mwh"] >= 0.9 * monthly.loc[then, "import_mwh"]:
                recovery = now
                break
    # May to December: in how many months was gas output higher than in the comparison year?
    months = [m for m in range(5, 13)
              if pd.Timestamp(2025, m, 1) in monthly.index and pd.Timestamp(compare_year, m, 1) in monthly.index]
    gas_now = np.array([monthly.loc[pd.Timestamp(2025, m, 1), "natural_gas_mwh"] for m in months])
    gas_then = np.array([monthly.loc[pd.Timestamp(compare_year, m, 1), "natural_gas_mwh"] for m in months])
    return {
        "gas_before": before["natural_gas_mwh"],
        "gas_after": after["natural_gas_mwh"],
        "imports_after": after["import_mwh"],
        "low_import_days": run,
        "low_import_end": BLACKOUT_DAY + pd.Timedelta(days=run),
        "recovery_month": recovery,
        "gas_months_higher": int((gas_now > gas_then).sum()),
        "gas_months_compared": len(months),
        "gas_avg_2025": gas_now.mean() if months else np.nan,
        "gas_avg_before": gas_then.mean() if months else np.nan,
    }
