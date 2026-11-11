"""Chapter 04 - Where it is used."""
import pandas as pd
import streamlit as st

from core import charts, data, i18n, stats, text, ui
from core.i18n import t

CH = "use"
ui.page_setup(CH)

ALL_DISTRICTS = "__all__"  # internal value of the district filter; the visible text depends on the language

mob = data.mobility()
if mob is None:
    ui.empty(t("empty.mobility"))
    st.stop()
population = data.population()
geojson = data.municipalities_geojson()

months = [pd.Timestamp(m) for m in sorted(mob["date"].unique())]
month_labels = {m: text.month(m) for m in months}
districts = sorted(mob["district"].unique())
district_options = [ALL_DISTRICTS] + districts

hero_slot = st.empty()
with ui.filter_bar():
    c_months, c_district, _ = st.columns([2, 1.2, 0.8])
    with c_months:
        saved = ui.remembered("months_use", (months[0], months[-1]))
        if saved[0] not in months or saved[1] not in months:
            saved = (months[0], months[-1])
        month_range = st.select_slider(t("filter.months"), options=months, value=saved,
                                       format_func=lambda m: month_labels[m], key="months_use")
        ui.keep("months_use", month_range)
    with c_district:
        saved = ui.remembered("district_use", ALL_DISTRICTS, district_options)
        choice = st.selectbox(t("filter.district"), district_options, index=district_options.index(saved),
                              format_func=lambda d: t("c4.all_districts") if d == ALL_DISTRICTS else d,
                              key="district_use")
        ui.keep("district_use", choice)
district = None if choice == ALL_DISTRICTS else choice

month_start, month_end = month_range
mainland = stats.mobility_window(mob, month_start, month_end)
window = stats.mobility_window(mob, month_start, month_end, district)
shares = stats.district_shares(mainland)
totals = stats.municipality_totals(window, population)
top_municipality = totals.sort_values("energy_mwh", ascending=False)["municipality"].iloc[0]

ui.hero(hero_slot, CH, ui.chip(CH), text.use_headline(shares, district),
        text.use_subtitle(shares, month_start, month_end, district, top_municipality),
        t("updated.data", date=text.month(months[-1])))

# ----------------------------------------------------------------------------- key figures
cols = st.columns(4, gap="medium")
with cols[0], ui.card("total"):
    where = i18n.district_label(district) if district else t("c4.total.municipalities", n=window["municipality"].nunique())
    ui.kpi(t("c4.total.label"), text.num(window["energy_mwh"].sum() / 1000, 1), "GWh", where)
with cols[1], ui.card("districts"):
    ui.html(f'<div class="kpi-label">{t("c4.districts.label")}</div>')
    top = shares.head(3)
    rows = [(d, v, text.pct(v), "#1F5A8A" if i == 0 else ("#3B78AE" if i == 1 else "#5FA2D3"))
            for i, (d, v) in enumerate(top.items())]
    rows.append((t("c4.districts.other", n=len(shares) - 3), 100 - top.sum(), text.pct(100 - top.sum()), "#C9D3DF"))
    ui.bar_list(rows, label_width=120, value_width=56, max_value=100)
with cols[2], ui.card("top10"):
    base = window["energy_mwh"].sum()
    top10 = totals.nlargest(10, "energy_mwh")["energy_mwh"].sum() / base * 100 if base else float("nan")
    ui.kpi(t("c4.top10.label"), text.pct(top10), None,
           t("c4.top10.note_district") if district else t("c4.top10.note_mainland"))
with cols[3], ui.card("perres", dark=True):
    if population is not None:
        pop = totals["population"].sum()
        value = window["energy_mwh"].sum() * 1000 / pop if pop else float("nan")
        ui.kpi(t("c4.perres.district") if district else t("c4.perres.mainland"), text.num(value), "kWh",
               t("c4.perres.note", year=population["year"].iloc[0]))
    else:
        ui.kpi(t("c4.perres.short"), t("na"), None, t("c4.perres.missing"))

# ----------------------------------------------------------------------------- map and ranking
left, right = st.columns([3, 2], gap="medium")
measures = {"total": t("measure.total")}
if population is not None:
    measures = {"resident": t("measure.resident"), "total": t("measure.total")}
with left, ui.card("map"):
    head, toggle = st.columns([1.4, 1], vertical_alignment="center")
    with head:
        ui.title(t("c4.map.title"))
    with toggle:
        if len(measures) > 1:
            measure = ui.segmented(t("filter.measure"), list(measures), measures, "measure_use", list(measures)[0],
                                   "measure_use")
        else:
            measure = "total"
    column = "kwh_per_resident" if measure == "resident" else "energy_mwh"
    if geojson is None:
        ui.empty(t("c4.map.missing"))
    else:
        st.plotly_chart(charts.municipality_map(totals, geojson, column, measures[measure]),
                        config=charts.CONFIG, key="map")
        ui.html(f'<p class="card-note">{t("c4.map.note")}</p>')
    if population is not None:
        ui.html(f'<span class="badge">{t("c4.map.badge", year=population["year"].iloc[0], indicator=population["indicator"].iloc[0])}</span>')
    else:
        ui.html(f'<span class="badge">{t("c4.map.badge_missing")}</span>')

with right:
    with ui.card("ranking"):
        ranked = totals.dropna(subset=[column]).nlargest(10, column)
        unit_text = t("unit.kwh_per_resident") if measure == "resident" else "MWh"
        ui.title(t("c4.ranking.title", unit=unit_text))
        decimals = 0 if measure == "total" else 1
        rows = [(r.municipality, getattr(r, column), text.num(getattr(r, column), decimals)) for r in ranked.itertuples()]
        ui.bar_list(rows, label_width=150, value_width=70)
    with ui.card("monthly"):
        monthly = window.groupby("date")["energy_mwh"].sum()
        ui.title(t("c4.monthly.title"),
                 t("c4.monthly.note_district", place=i18n.district_label(district)) if district
                 else t("c4.monthly.note_mainland"))
        st.plotly_chart(charts.monthly_line(monthly), config=charts.CONFIG, key="monthly")

ui.footer(CH, t("c4.footer"))
