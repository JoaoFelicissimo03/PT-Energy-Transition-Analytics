"""Chapter 03 - What it costs."""
import streamlit as st

from core import charts, data, i18n, stats, text, ui
from core.i18n import t

CH = "cost"
ui.page_setup(CH)

prod, prices = data.production(), data.prices()
if prices is None or prod is None:
    ui.empty(t("empty.prices"))
    st.stop()

hero_slot = st.empty()
with ui.filter_bar():
    c_period, c_market, c_def = st.columns([1.8, 1.1, 1.5])
    with c_period:
        period = ui.period_control(CH, ["30d", "12m", "ytd", "all"], "12m")
    with c_market:
        market = ui.segmented(t("filter.market"), ["pt", "es", "both"],
                              {m: t(f"market.{m}") for m in ("pt", "es", "both")}, "market_cost", "pt", "market_cost")
    with c_def:
        definition = ui.definition_control(CH)

kpi_market = "es" if market == "es" else "pt"
summary = stats.price_summary(prices, period, kpi_market)
start, end = summary["start"], summary["end"]
correlations = stats.price_correlation_by_year(prod, prices, definition, start, end)

ui.hero(hero_slot, CH, ui.chip(CH),
        text.cost_headline(summary["change_pct"], summary["avg"], period),
        text.cost_subtitle(period, start, end, summary["avg"], summary["prev_avg"], correlations, kpi_market),
        t("updated.prices", date=text.day(prices["date"].max())))

# ----------------------------------------------------------------------------- key figures
cols = st.columns(4, gap="medium")
with cols[0], ui.card("avg", dark=True):
    ui.kpi(t(f"period.{period}"), text.num(summary["avg"]), "EUR/MWh",
           t("c3.avg.note", market=t(f"market.{kpi_market}")), color="#F7B57A")
with cols[1], ui.card("prev"):
    phrase = text.comparison_phrase(period)
    if phrase and not text.missing(summary["prev_avg"]):
        ui.kpi(i18n.cap(phrase), text.num(summary["prev_avg"]), "EUR/MWh",
               t("c3.prev.note", value=text.pct(summary["change_pct"], 0, signed=True)))
    else:
        ui.kpi(t("c3.prev.label"), t("na"), None, t("c3.prev.unavailable"))
with cols[2], ui.card("allavg"):
    ui.kpi(t("c3.all.label"), text.num(summary["all_avg"]), "EUR/MWh",
           t("range", a=text.day(prices["date"].min()), b=text.day(prices["date"].max())))
with cols[3], ui.card("split"):
    first_year = summary["first_full_year"]
    note = (t("c3.split.note_year", share=text.pct(summary["first_full_split"]), year=first_year)
            if first_year else t("c3.split.note"))
    ui.kpi(t("c3.split.label"), text.pct(summary["split_share"]), None, note)

# ----------------------------------------------------------------------------- price over time
with ui.card("prices"):
    markets = ["pt", "es"] if market == "both" else [kpi_market]
    series, unit = stats.price_series(prices, start, end, markets)
    ui.title(t("c3.prices.title", unit=t(f"unit.{unit}"), period=t(f"period_in.{period}")))
    labels = {"price_avg_pt": t("market.pt"), "price_avg_es": t("market.es")}
    colors = {"price_avg_pt": "#D9822B", "price_avg_es": "#1F5A8A"}
    st.plotly_chart(charts.price_lines(series, unit, labels, colors), config=charts.CONFIG, key="prices")

# ----------------------------------------------------------------------------- renewables, prices and splits
left, right = st.columns(2, gap="medium")
with left, ui.card("corr"):
    ui.title(t("c3.corr.title"), t("c3.corr.note"))
    if correlations.empty:
        ui.empty(t("c3.corr.empty"))
    else:
        rows = [(t("c3.corr.row", year=int(r.year), days=int(r.days)), r.corr, text.num(r.corr, 2, signed=True),
                 "#2C7FB8" if r.corr < 0 else "#C9B3A2") for r in correlations.itertuples()]
        ui.bar_list(rows, label_width=130, value_width=56, max_value=1)
        ui.html(f'<p class="card-note" style="margin-top:10px">{text.correlation_sentence(correlations)}</p>')

with right, ui.card("splits"):
    ui.title(t("c3.splits.title"), t("c3.splits.note"))
    by_year = stats.split_share_by_year(prices)
    labels = [f"{y}*" if not by_year.loc[y, "full"] else str(y) for y in by_year.index]
    in_period = [y for y in by_year.index if start.year <= y <= end.year]
    st.plotly_chart(charts.yearly_bars(by_year["share"], labels, "#D9822B", "%", in_period),
                    config=charts.CONFIG, key="splits")

ui.footer(CH, t("c3.footer"))
