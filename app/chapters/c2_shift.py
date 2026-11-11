"""Chapter 02 - How we got here."""
import streamlit as st

from core import charts, data, i18n, stats, text, ui
from core.i18n import t

CH = "shift"
ui.page_setup(CH)

prod = data.production()
if prod is None:
    ui.empty(t("empty.production"))
    st.stop()

SOURCES = ["hydro_mwh", "wind_mwh", "solar_mwh", "biomass_mwh", "natural_gas_mwh", "import_mwh"]
DEFAULT_SOURCES = ["hydro_mwh", "wind_mwh", "solar_mwh", "biomass_mwh", "natural_gas_mwh"]
LABELS = i18n.source_labels()
years_available = sorted(prod["date"].dt.year.unique().tolist())

hero_slot = st.empty()
with ui.filter_bar():
    c_years, c_sources, c_def = st.columns([1.2, 2, 1.4])
    with c_years:
        saved = ui.remembered("years_shift", (years_available[0], years_available[-1]))
        if saved[0] not in years_available or saved[1] not in years_available:
            saved = (years_available[0], years_available[-1])
        year_range = st.select_slider(t("filter.years"), options=years_available, value=saved, key="years_shift")
        ui.keep("years_shift", year_range)
    with c_sources:
        saved = [s for s in ui.remembered("sources_shift", DEFAULT_SOURCES) if s in SOURCES]
        sources = st.pills(t("filter.sources"), SOURCES, selection_mode="multi", default=saved,
                           format_func=lambda c: t(f"pill.{c}"), key="sources_shift")
        ui.keep("sources_shift", sources)
    with c_def:
        definition = ui.definition_control(CH)

first_year, last_year = year_range
subset = prod[prod["date"].dt.year.between(first_year, last_year)]
yearly = stats.yearly_shares(subset, definition)
full = yearly[yearly["full"]]
full_years = list(full.index)
weak_year = int(full["share"].idxmin()) if len(full) else None
best_year = int(full["share"].idxmax()) if len(full) else None
annual = stats.annual_production(subset, SOURCES)
renewable_cols = ["hydro_mwh", "wind_mwh", "solar_mwh", "biomass_mwh"]
drop = stats.biggest_drop(annual, weak_year, best_year, renewable_cols) if weak_year and weak_year != best_year else None

title = text.shift_headline(weak_year, full["share"].min() if len(full) else None,
                            best_year, full["share"].max() if len(full) else None)
subtitle = text.shift_subtitle(drop,
                               annual.loc[weak_year, "natural_gas_mwh"] if weak_year else None,
                               annual.loc[best_year, "natural_gas_mwh"] if best_year else None,
                               weak_year, best_year)
ui.hero(hero_slot, CH, ui.chip(CH), title, subtitle, t("updated.data", date=text.day(prod["date"].max())))

# ----------------------------------------------------------------------------- production by year
left, right = st.columns([2, 1], gap="medium")
with left, ui.card("annual"):
    head, toggle = st.columns([2, 1], vertical_alignment="center")
    with head:
        ui.title(t("c2.annual.title", first=first_year, last=last_year), t("c2.annual.note"))
    with toggle:
        unit = ui.segmented(t("filter.unit"), ["mwh", "share"], {"mwh": t("c2.unit.mwh"), "share": t("c2.unit.share")},
                            "unit_shift", "mwh", "unit_shift")
    if not sources:
        ui.empty(t("c2.annual.empty"))
    else:
        partial = [y for y in annual.index if y not in full_years]
        st.plotly_chart(charts.stacked_annual(annual, sources, LABELS, unit, partial), config=charts.CONFIG, key="annual")

with right:
    with ui.card("solar", dark=True):
        if len(full_years) >= 2:
            a, b = full_years[0], full_years[-1]
            ratio = annual.loc[b, "solar_mwh"] / annual.loc[a, "solar_mwh"]
            ui.kpi(t("c2.solar.label"), f"{text.num(ratio, 1)}x", None,
                   t("c2.solar.note", a_value=text.num(annual.loc[a, "solar_mwh"]), a=a,
                     b_value=text.num(annual.loc[b, "solar_mwh"]), b=b),
                   color="#F2C94C")
        else:
            ui.kpi(t("c2.solar.short"), t("na"), None, t("c2.need_two_range"))
    with ui.card("weak"):
        if drop:
            source, low, high = drop
            ratio = low / high if high else float("nan")
            headline = (t("c2.weak.half", source=LABELS[source]) if ratio < 0.5 else
                        t("c2.weak.lower", source=LABELS[source], value=text.pct((1 - ratio) * 100, 0)))
            ui.kpi(t("c2.weak.label", year=weak_year, share=text.pct(full["share"].min())), headline, None,
                   t("c2.weak.note", year=best_year, low=text.num(low), high=text.num(high)))
        else:
            ui.kpi(t("c2.weak.short"), t("na"), None, t("c2.need_two_range"))

# ----------------------------------------------------------------------------- seasonality and variability
left, right = st.columns([3, 2], gap="medium")
with left, ui.card("season"):
    if full_years:
        season = stats.seasonality(subset[subset["date"].dt.year.isin(full_years)], definition)
        span = f"{full_years[0]}" if len(full_years) == 1 else t("range", a=full_years[0], b=full_years[-1])
        ui.title(t("c2.season.title"), t("c2.season.note", span=span))
        st.plotly_chart(charts.seasonality(season), config=charts.CONFIG, key="season")
    else:
        ui.title(t("c2.season.title"))
        ui.empty(t("c2.season.empty"))

with right, ui.card("variability"):
    ui.title(t("c2.var.title"), t("c2.var.note"))
    if len(full_years) >= 2:
        cv = stats.variability(subset, [full_years[0], full_years[-1]])
        a, b = full_years[0], full_years[-1]
        top = cv.max().max()
        colors = {"hydro_mwh": "#2C7FB8", "wind_mwh": "#41AE76", "solar_mwh": "#E6A700", "biomass_mwh": "#8C6D31"}
        rows = [(LABELS.get(col, col), cv.loc[b, col],
                 t("range", a=text.num(cv.loc[a, col], 2), b=text.num(cv.loc[b, col], 2)), colors.get(col, "#6BAED6"))
                for col in cv.columns]
        ui.bar_list(rows, label_width=80, value_width=110, max_value=top)
        most = cv.loc[b].idxmax()
        ui.html(f'<p class="card-note" style="margin-top:10px">{t("c2.var.bars", year=b, source=t(f"srcart.{most}"))}</p>')
    else:
        ui.empty(t("c2.need_two_selected"))

ui.footer(CH, t("c2.footer"))
