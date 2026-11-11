"""Bonus chapter - The 2025 blackout. A fixed analysis of April to June 2025; the numbers still come from the data."""
import pandas as pd
import streamlit as st

from core import charts, data, i18n, stats, text, ui
from core.i18n import t
from core.theme import COLUMN_COLORS

CH = "blackout"
ui.page_setup(CH)

ENTSOE = "https://www.entsoe.eu/publications/blackout/28-april-2025-Iberian-blackout"
ARA = ("https://en.ara.cat/economy/red-electrica-estimates-the-cost-of-reinforcing-the-electrical-system-"
       "since-the-blackout-at-317-million-euros_1_5531132.amp.html")

prod = data.production()
if prod is None:
    ui.empty(t("empty.production"))
    st.stop()

years = [y for y in (2024, 2023) if stats.blackout_available(prod, y)]
if not years:
    ui.empty(t("bo.empty.window"))
    st.stop()

hero_slot = st.empty()
with ui.filter_bar():
    c_year, _ = st.columns([1, 3])
    with c_year:
        compare = ui.segmented(t("filter.compare"), years, {y: str(y) for y in years}, "compare_blackout",
                               years[0], "compare_blackout")

means, change, pct, share = stats.blackout_comparison(prod, compare)
timeline = stats.blackout_timeline(prod, compare)

ui.hero(hero_slot, CH, ui.chip(CH), t("bo.headline"), text.blackout_subtitle(share, change, compare),
        t("updated.data", date=text.day(prod["date"].max())), note=t("bo.note"))

# ----------------------------------------------------------------------------- key figures
cols = st.columns(4, gap="medium")
with cols[0], ui.card("share"):
    ui.kpi(t("bo.share.label"), t("bo.share.value", a=text.pct(share[compare]), b=text.pct(share[2025])), None,
           t("bo.share.note", year=compare))
with cols[1], ui.card("ren"):
    went_up = change["renewable_mwh"] > 0
    ui.kpi(t("bo.ren.label"), text.num(change["renewable_mwh"], signed=True), None,
           t("bo.ren.note") + (" " + t("bo.ren.up") if went_up else ""),
           color="#7CC7A0" if went_up else None)
with cols[2], ui.card("gas"):
    ui.kpi(t("bo.gas.label"), text.pct(pct["natural_gas_mwh"], 0, signed=True), None,
           t("bo.gas.note", value=text.num(change["natural_gas_mwh"], signed=True)), color="#FF9A8B")
with cols[3], ui.card("lowimp"):
    ui.kpi(t("bo.lowimp.label"), str(timeline["low_import_days"]), None,
           t("bo.lowimp.range", end=text.day(timeline["low_import_end"])) if timeline["low_import_days"]
           else t("bo.lowimp.after"))

# ----------------------------------------------------------------------------- day by day
daily = prod.set_index("date")
with ui.card("lines"):
    ui.title(t("bo.lines.title"))
    left, right = st.columns(2, gap="large")
    with left:
        ui.html(f'<div class="kpi-label">{t("src.natural_gas_mwh")}</div>')
        st.plotly_chart(charts.blackout_lines(daily, compare, "natural_gas_mwh", t("src.natural_gas_mwh"),
                                              {compare: "#6F8496", 2025: "#EAF2F6"}), config=charts.CONFIG, key="gas")
    with right:
        ui.html(f'<div class="kpi-label">{t("src.import_mwh")}</div>')
        st.plotly_chart(charts.blackout_lines(daily, compare, "import_mwh", t("src.import_mwh"),
                                              {compare: "#6B5E86", 2025: "#C3B1E6"}), config=charts.CONFIG, key="imports")

# ----------------------------------------------------------------------------- timeline and changes
left, right = st.columns([1, 1.2], gap="medium")
with left, ui.card("timeline"):
    ui.title(t("bo.timeline.title"))
    steps = [
        (text.day(stats.BLACKOUT_DAY), t("bo.step.blackout")),
        (i18n.day_month(stats.BLACKOUT_DAY + pd.Timedelta(days=1)),
         t("bo.step.imports", imports=text.num(timeline["imports_after"]), before=text.num(timeline["gas_before"]),
           after=text.num(timeline["gas_after"]))),
    ]
    if timeline["low_import_days"]:
        steps.append((i18n.day_month(timeline["low_import_end"]),
                      t("bo.step.last_low", days=timeline["low_import_days"])))
    if timeline["recovery_month"] is not None:
        steps.append((i18n.cap(i18n.month_name(timeline["recovery_month"])),
                      t("bo.step.recovery", year=compare)))
    steps.append((t("bo.step.range_label"),
                  t("bo.step.gas", year=compare, n=timeline["gas_months_higher"], total=timeline["gas_months_compared"],
                    a=text.num(timeline["gas_avg_2025"]), b=text.num(timeline["gas_avg_before"]))))
    ui.html('<ol style="margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:14px;font-size:15px;line-height:1.45">'
            + "".join(f'<li style="display:flex;gap:14px"><span style="flex:none;width:112px;color:#FF9A8B;font-weight:500">'
                      f'{when}</span><span>{what}</span></li>' for when, what in steps) + "</ol>")

with right, ui.card("change"):
    ui.title(t("bo.change.title", year=compare))
    order = ["hydro_mwh", "wind_mwh", "solar_mwh", "biomass_mwh", "natural_gas_mwh", "import_mwh", "consumption_mwh"]
    colors = dict(COLUMN_COLORS, hydro_mwh="#4A9BD1", natural_gas_mwh="#C9D2DA", import_mwh="#9C84C9",
                  consumption_mwh="#6F8496")
    st.plotly_chart(charts.change_bars(change[order], i18n.source_labels(order), colors), config=charts.CONFIG,
                    key="change")

with ui.card("context"):
    sources = t("bo.context.sources", entsoe=f'<a href="{ENTSOE}">ENTSO-E</a>', ara=f'<a href="{ARA}">Ara</a>')
    ui.html(f'<p class="card-note" style="color:#C9D6DF">{t("bo.context")} {sources}</p>')

ui.footer(CH, t("bo.footer", year=compare))
