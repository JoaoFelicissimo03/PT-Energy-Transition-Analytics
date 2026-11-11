"""Chapter 05 - What comes next."""
import pandas as pd
import streamlit as st

from core import charts, data, i18n, stats, text, ui
from core.i18n import t

CH = "next"
ui.page_setup(CH)

preds, nxt, prod = data.predictions(), data.next_day(), data.production()
if preds is None or prod is None:
    ui.empty(t("empty.forecast"))
    st.stop()

ALL = [m for m in ["persistence", "mean_7d", "linear_regression", "climatology", "prophet"] if m in preds.columns]
LABELS = i18n.model_labels()
COLORS = {"persistence": "#10293A", "mean_7d": "#9E9E9E", "linear_regression": "#5FA2D3",
          "climatology": "#D9822B", "prophet": "#41AE76"}

hero_slot = st.empty()
with ui.filter_bar():
    c_period, c_models, c_window = st.columns([1.5, 2.5, 1.4])
    with c_period:
        period = ui.period_control(CH, ["12m", "all"], "all", {"12m": t("period.12m"), "all": t("c5.period.all")})
    starts = stats.windows_in_period(preds, period)
    with c_models:
        saved = ui.remembered("models_next", ["persistence", "linear_regression", "mean_7d"])
        models = st.pills(t("filter.models"), ALL, selection_mode="multi", default=[m for m in saved if m in ALL],
                          format_func=lambda m: LABELS[m], key="models_next")
        ui.keep("models_next", models)
    with c_window:
        def window_label(s):
            end = preds.loc[preds["window_start"] == s, "date"].max()
            return t("range", a=text.day(s), b=text.day(end))
        saved = ui.remembered("window_next", starts[-1])
        if saved not in starts:
            saved = starts[-1]
        window_start = st.selectbox(t("filter.window"), starts, index=starts.index(saved),
                                    format_func=window_label, key="window_next")
        ui.keep("window_next", window_start)

table, per_window = stats.leaderboard(preds, starts, ALL)
ui.hero(hero_slot, CH, ui.chip(CH), text.next_headline(table), text.next_subtitle(table),
        t("updated.data", date=text.day(prod["date"].max())))

# ----------------------------------------------------------------------------- tomorrow and the leaderboard
left, right = st.columns([1, 2], gap="medium")
with left, ui.card("tomorrow", dark=True):
    if nxt is not None:
        row = nxt.iloc[0]
        ui.html(f'<div class="kpi"><div class="kpi-label" style="text-align:center">'
                f'{t("c5.tomorrow.label", date=text.day(row["date"]))}</div>'
                f'{ui.gauge(row["persistence"], "#F2C94C", "#24445A", "#FFFFFF")}'
                f'<div class="kpi-note" style="text-align:center">{t("c5.tomorrow.same", date=text.day(row["based_on"]))}</div>'
                f'<div class="kpi-note" style="text-align:center">'
                f'{t("c5.tomorrow.detail", model=LABELS["linear_regression"], value=text.pct(row["linear_regression"]), error=text.num(table.loc["persistence", "mae"], 1))}'
                f'</div></div>')
    else:
        ui.empty(t("c5.tomorrow.empty"))

with right, ui.card("board"):
    windows = int(table["windows"].iloc[0])
    ui.title(t("c5.board.title"), t("c5.board.note", windows=windows))
    shown = [m for m in table.index if m in models] or list(table.index)
    top = table.loc[shown, "mae"].max()
    cells = []
    for m in shown:
        r = table.loc[m]
        color = COLORS[m]
        tag_bg = "#E3EEF6" if r["horizon"] == "1 day" else "#F6E6D9"
        horizon = t("horizon." + r["horizon"])
        cells.append(
            f'<span style="font-weight:{600 if m == "persistence" else 400}">{LABELS[m]}</span>'
            f'<span style="font-size:12px;padding:3px 8px;border-radius:999px;background:{tag_bg};text-align:center">{horizon}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{r["mae"] / top * 100:.1f}%;background:{color}"></div></div>'
            f'<span style="text-align:right">{text.num(r["mae"], 2)}</span>')
    ui.html(f'<div class="bars" style="grid-template-columns:150px 74px minmax(0,1fr) 54px">{"".join(cells)}</div>')
    challengers = table[(table["horizon"] == "1 day") & (table.index != "persistence")]
    if len(challengers):
        best = challengers["mae"].idxmin()
        note = t("c5.board.beats", model=i18n.cap(t(f"modelphrase.{best}")),
                 n=int(challengers.loc[best, "beats_persistence"]), windows=windows)
        if (table.loc[shown, "horizon"] != "1 day").any():
            note += " " + t("c5.board.long_models")
        ui.html(f'<p class="card-note" style="margin-top:12px">{note}</p>')

# ----------------------------------------------------------------------------- errors over time and one window
if not models:
    ui.empty(t("c5.empty_models"))
else:
    left, right = st.columns([3, 2], gap="medium")
    with left, ui.card("errors"):
        ui.title(t("c5.errors.title"), t("c5.errors.note"))
        st.plotly_chart(charts.window_errors(per_window, models, LABELS, COLORS), config=charts.CONFIG, key="errors")
    with right, ui.card("better"):
        ui.title(t("c5.better.title"))
        years = stats.full_years(prod)
        items = []
        if years:
            cv = stats.variability(prod, [years[-1]])
            least = i18n.cap(t(f"srcart.{cv.loc[years[-1]].idxmax()}"))
            items.append((t("c5.better.weather.title"), t("c5.better.weather.body", source=least, year=years[-1])))
        last12 = prod[prod["date"] > prod["date"].max() - pd.Timedelta(days=365)]
        biggest = i18n.cap(t(f"srcart.{last12[['hydro_mwh', 'wind_mwh', 'solar_mwh', 'biomass_mwh']].sum().idxmax()}"))
        items.append((t("c5.better.rain.title"), t("c5.better.rain.body", source=biggest)))
        if len(years) >= 2:
            growth = (prod[prod["date"].dt.year == years[-1]]["solar_mwh"].mean()
                      / prod[prod["date"].dt.year == years[0]]["solar_mwh"].mean())
            items.append((t("c5.better.sun.title"),
                          t("c5.better.sun.body", growth=text.num(growth, 1), a=years[0], b=years[-1])))
        ui.html("".join(f'<div style="margin-bottom:14px"><div style="font-weight:500;font-size:16px">{head}</div>'
                        f'<div class="card-note">{body}</div></div>' for head, body in items))

    with ui.card("detail"):
        window = preds[preds["window_start"] == window_start]
        ui.title(t("c5.detail.title", a=text.day(window["date"].min()), b=text.day(window["date"].max())))
        st.plotly_chart(charts.window_detail(window, models, LABELS, COLORS), config=charts.CONFIG, key="detail")

ui.footer(CH, t("c5.footer"))
