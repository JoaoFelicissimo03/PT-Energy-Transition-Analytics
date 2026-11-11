"""Chapter 01 - Where we are."""
import numpy as np
import streamlit as st

from core import charts, data, i18n, stats, text, ui
from core.hero import svg_img
from core.i18n import t
from core.theme import SOURCE_COLORS

CH = "now"
ui.page_setup(CH)

prod = data.production()
if prod is None:
    ui.empty(t("empty.production"))
    st.stop()
prices = data.prices()

hero_slot = st.empty()
with ui.filter_bar():
    left, right, _ = st.columns([1.5, 1.2, 0.5])
    with left:
        period = ui.period_control(CH, ["30d", "12m", "ytd", "all"], "30d")
    with right:
        definition = ui.definition_control(CH)

period_text = t(f"period_in.{period}")
first, last = prod["date"].min(), prod["date"].max()
start, end = stats.period_bounds(period, first, last)
window = stats.between(prod, start, end)
share = stats.renewable_share(window, definition)

share_change = np.nan
if period != "all":
    prev_start, prev_end = stats.year_before(start, end)
    if stats.covers(prod, prev_start, prev_end):
        share_change = share - stats.renewable_share(stats.between(prod, prev_start, prev_end), definition)

ui.hero(hero_slot, CH, ui.chip(CH), text.now_headline(share, definition),
        text.now_subtitle(period, start, end, share, definition), t("updated.data", date=text.day(last)))

# ----------------------------------------------------------------------------- key figures
cols = st.columns(4, gap="medium")
with cols[0], ui.card("share"):
    ui.html(f'<div class="kpi"><div class="kpi-label">{t(f"c1.share.{definition}", period=period_text)}</div>'
            f'{ui.gauge(share)}<div class="kpi-note" style="text-align:center">'
            f'{text.change_note(share_change, period)}</div></div>')

with cols[1], ui.card("mix"):
    shares = stats.mix(window, definition)
    ui.html(f'<div class="kpi-label">{t("c1.mix.title", period=period_text)}</div>')
    circumference, offset, rings = 2 * np.pi * 60, 0.0, []
    for name, value in shares.items():
        length = value / 100 * circumference
        rings.append(f'<circle cx="80" cy="80" r="60" stroke="{SOURCE_COLORS[name]}" '
                     f'stroke-dasharray="{length:.1f} {circumference:.1f}" stroke-dashoffset="{-offset:.1f}"></circle>')
        offset += length
    rows = "".join(f'<div style="display:flex;gap:8px;align-items:center"><i class="dot" style="background:{SOURCE_COLORS[n]}"></i>'
                   f'<span style="flex:1">{t(f"mix.{n}")}</span><span>{text.pct(v)}</span></div>' for n, v in shares.items())
    donut = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160">'
             f'<g transform="rotate(-90 80 80)" fill="none" stroke-width="20">{"".join(rings)}</g></svg>')
    ui.html(f'<div style="display:flex;align-items:center;gap:16px;margin-top:8px">'
            f'{svg_img(donut, t("c1.mix.alt"), "width:118px;flex:none")}'
            f'<div style="display:flex;flex-direction:column;gap:5px;font-size:14px;flex:1">{rows}</div></div>')

with cols[2], ui.card("solar"):
    years = stats.full_years(prod)
    if period == "all" and len(years) >= 2:
        solar = prod[prod["date"].dt.year == years[-1]]["solar_mwh"].mean()
        first_solar = prod[prod["date"].dt.year == years[0]]["solar_mwh"].mean()
        note = t("c1.solar.times", ratio=text.num(solar / first_solar, 1), year=years[0])
        label = t("c1.solar.year", year=years[-1])
    else:
        solar = window["solar_mwh"].mean()
        solar_change = np.nan
        if period != "all":
            prev_start, prev_end = stats.year_before(start, end)
            if stats.covers(prod, prev_start, prev_end):
                solar_change = (solar / stats.between(prod, prev_start, prev_end)["solar_mwh"].mean() - 1) * 100
        note = text.change_note(solar_change, period, unit="%")
        label = t("c1.solar.period", period=period_text)
    ui.kpi(label, text.num(solar / 1000, 1), "GWh", note)
    by_year = prod[prod["date"].dt.year.isin(years)].groupby(prod["date"].dt.year)["solar_mwh"].mean()
    if len(by_year):
        bars = "".join(f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:4px">'
                       f'<div style="width:100%;height:{v / by_year.max() * 60:.0f}px;border-radius:8px;'
                       f'background:#E6A700;opacity:{0.45 + 0.55 * v / by_year.max():.2f}"></div>'
                       f'<span style="font-size:12px;color:var(--muted)">{y}</span></div>' for y, v in by_year.items())
        ui.html(f'<div style="display:flex;align-items:flex-end;gap:10px;height:86px;margin-top:6px" '
                f'aria-label="{t("c1.solar.alt")}">{bars}</div>')

with cols[3], ui.card("price"):
    if prices is None:
        ui.empty(t("empty.prices_short"))
    else:
        ps = stats.price_summary(prices, period, "pt")
        ui.kpi(t("c1.price.label", period=period_text), text.num(ps["avg"]), "EUR/MWh",
               text.change_note(ps["change_pct"], period, unit="%"))
        series, unit = stats.price_series(prices, ps["start"], ps["end"], ["pt"])
        values = series["price_avg_pt"].dropna().values
        if len(values) > 1:
            lo, hi = values.min(), values.max()
            span = (hi - lo) or 1
            points = " ".join(f"{i / (len(values) - 1) * 200:.1f},{58 - (v - lo) / span * 52:.1f}" for i, v in enumerate(values))
            spark = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-4 0 208 64" preserveAspectRatio="none">'
                     f'<polyline fill="none" stroke="#D9822B" stroke-width="3" stroke-linecap="round" '
                     f'stroke-linejoin="round" points="{points}"/></svg>')
            ui.html(svg_img(spark, t("c1.price.alt"), "width:100%;height:70px;display:block"))
        if ps["end"] < end:
            ui.html(f'<div class="kpi-note">{t("c1.price.upto", date=text.day(ps["end"]))}</div>')

# ----------------------------------------------------------------------------- daily profile and records
left, right = st.columns([2, 1], gap="medium")
with left, ui.card("profile"):
    profile, unit = stats.daily_profile(window, definition)
    ui.title(t("c1.profile.title", period=period_text),
             t("c1.profile.note.day") if unit == "day" else t("c1.profile.note.avg", unit=t(f"unit.{unit}")))
    st.plotly_chart(charts.daily_profile(profile, unit), config=charts.CONFIG, key="profile")

with right, ui.card("records", dark=True):
    rec = stats.records(prod, definition)
    if text.missing(rec["this_year_change"]):
        so_far_note = t("c1.records.renewable")
    else:
        so_far_note = t("c1.records.renewable_change", note=i18n.lower_first(text.change_note(rec["this_year_change"], "ytd")))
    ui.kpi(t("c1.records.so_far", year=rec["this_year_label"]), text.pct(rec["this_year"]), None, so_far_note)
    split_now = (prices[prices["date"].dt.year == prices["date"].max().year]["market_split"].mean() * 100
                 if prices is not None else np.nan)
    rows = [(t("c1.records.best"),
             t("c1.records.year_share", year=rec["best_year"], share=text.pct(rec["best_share"])) if rec["best_year"] else t("na")),
            (t("c1.records.weak"),
             t("c1.records.year_share", year=rec["weak_year"], share=text.pct(rec["weak_share"])) if rec["weak_year"] else t("na")),
            (t("c1.records.split"), text.pct(split_now))]
    ui.html('<div style="height:1px;background:rgba(255,255,255,0.15);margin:12px 0"></div>' + "".join(
        f'<div style="display:flex;justify-content:space-between;gap:12px;font-size:15px;margin-bottom:10px">'
        f'<span style="color:#B9D3E2">{a}</span><span>{b}</span></div>' for a, b in rows))

# ----------------------------------------------------------------------------- the rest of the story
ui.html(f'<h2 class="card-title" style="margin-top:8px">{t("c1.story.title")}</h2>')
story = []
rec_dom = stats.records(prod, definition)
story.append(("shift", ui.nav_label("shift"),
              t("c1.story.shift.value", weak=text.pct(rec_dom["weak_share"], 0), best=text.pct(rec_dom["best_share"], 0)),
              t("c1.story.shift.note")))
if prices is not None:
    p30 = stats.price_summary(prices, "30d", "pt")
    value = (text.pct(p30["change_pct"], 0, signed=True) if not text.missing(p30["change_pct"])
             else f"{text.num(p30['avg'])} EUR")
    story.append(("cost", ui.nav_label("cost"), value, t("c1.story.cost.note")))
mob = data.mobility()
if mob is not None:
    top = stats.district_shares(mob)
    story.append(("use", ui.nav_label("use"), f"{text.pct(top.iloc[0], 0)} {top.index[0]}", t("c1.story.use.note")))
nxt = data.next_day()
if nxt is not None:
    story.append(("next", ui.nav_label("next"), text.pct(nxt["persistence"].iloc[0]),
                  t("c1.story.next.note", date=text.day(nxt["date"].iloc[0]))))
story.append(("blackout", t("c1.story.bonus.label"), t("chapter.blackout"), t("c1.story.bonus.note")))

story_cols = st.columns(len(story), gap="medium")
for col, (slug, label, value, note) in zip(story_cols, story):
    with col, ui.card(f"story-{slug}"):
        ui.html(f'<div class="kpi"><div class="kpi-label" style="font-size:13px">{label}</div>'
                f'<div class="kpi-value" style="font-size:26px">{value}</div><div class="kpi-note">{note}</div></div>')
        st.page_link(ui.PAGES[slug], label=t("open_chapter"))

ui.footer(CH, t("c1.footer", start=text.day(first), end=text.day(last)))
