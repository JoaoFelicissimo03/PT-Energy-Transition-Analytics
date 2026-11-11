"""Plotly figures with a transparent background, so they sit inside the glass cards.

Plotly would write month names and numbers in English, so dates, tick labels and hover texts are built here with
the language module and passed to Plotly as plain text.
"""
import pandas as pd
import plotly.graph_objects as go

from core import i18n
from core.i18n import day, day_month, month, num, pct, t
from core.theme import COLUMN_COLORS

CONFIG = {"displayModeBar": False, "responsive": True}
HOVER = "%{hovertext}<extra></extra>"


def _layout(fig, dark=False, height=320, legend=False, ytitle=None, ysuffix=""):
    fg = "#EAF2F6" if dark else "#10293A"
    muted = "#A9BDCB" if dark else "#3C5A6E"
    grid = "#2A4256" if dark else "#E1EAEE"
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, system-ui, sans-serif", size=13, color=fg),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=muted)),
        hoverlabel=dict(font_family="Outfit, sans-serif", bgcolor="#10293A" if not dark else "#EAF2F6",
                        font_color="#FFFFFF" if not dark else "#0F1E2A", bordercolor="rgba(0,0,0,0)"),
        bargap=0.25,
        separators=i18n.separators(),
    )
    fig.update_xaxes(showgrid=False, linecolor=grid, tickfont=dict(color=muted), zeroline=False)
    fig.update_yaxes(gridcolor=grid, zeroline=False, tickfont=dict(color=muted), ticksuffix=ysuffix,
                     title=dict(text=ytitle, font=dict(color=muted, size=12)) if ytitle else None)
    return fig


def _date_axis(fig, start, end, max_ticks=6):
    """Tick labels for a date axis in the current language, with a readable number of ticks."""
    start, end = pd.Timestamp(start).normalize(), pd.Timestamp(end).normalize()
    ticks, kind = [], "day"
    for kind, step in [("day", n) for n in (1, 2, 3, 7, 14)] + [("month", n) for n in (1, 2, 3, 6, 12, 24, 60)]:
        if kind == "day":
            ticks = pd.date_range(start, end, freq=f"{step}D")
        elif step >= 12:
            first = start if (start.month, start.day) == (1, 1) else pd.Timestamp(start.year + 1, 1, 1)
            ticks = pd.date_range(first, end, freq=f"{step}MS")
        else:
            first = start if start.day == 1 else start + pd.offsets.MonthBegin(1)
            ticks = pd.date_range(first, end, freq=f"{step}MS")
        if 2 <= len(ticks) <= max_ticks:
            break
        if kind == "month" and step >= 12 and len(ticks) < 2:
            ticks = pd.DatetimeIndex([start, end])
            break
    if kind == "day":
        labels = [day_month(d) for d in ticks]
    elif (ticks[1] - ticks[0]).days > 300:
        labels = [str(d.year) for d in ticks]
    else:
        labels = [month(d) for d in ticks]
    fig.update_xaxes(tickmode="array", tickvals=[d.strftime("%Y-%m-%d") for d in ticks], ticktext=labels)


def daily_profile(profile, unit):
    def when(ts):
        if unit == "day":
            return day(ts)
        return t("chart.week_of", date=day(ts)) if unit == "week" else month(ts)

    unit_text = t("chart.mwh_a_day")
    fig = go.Figure()
    fig.add_bar(x=profile.index, y=profile["renewable"], name=t("chart.renewable"), marker_color="#2C7FB8",
                hovertext=[f"{when(d)}<br>{t('chart.renewable')}: {num(v)} {unit_text}"
                           for d, v in profile["renewable"].items()], hovertemplate=HOVER)
    fig.add_bar(x=profile.index, y=-profile["non_renewable"], name=t("chart.non_renewable"), marker_color="#8A97A3",
                hovertext=[f"{when(d)}<br>{t('chart.non_renewable')}: {num(v)} {unit_text}"
                           for d, v in profile["non_renewable"].items()], hovertemplate=HOVER)
    fig.update_layout(barmode="relative")
    _layout(fig, height=260, ytitle=t("chart.mwh_per_day"))
    fig.update_yaxes(tickformat="~s")
    _date_axis(fig, profile.index.min(), profile.index.max())
    return fig


def stacked_annual(annual, columns, labels, unit="mwh", partial_years=()):
    data = annual[columns]
    if unit == "share":
        data = data.div(data.sum(axis=1), axis=0) * 100
    years = [f"{y}*" if y in partial_years else str(y) for y in data.index]
    fig = go.Figure()
    for col in columns:
        values = [pct(v) if unit == "share" else f"{num(v)} {t('chart.mwh_a_day')}" for v in data[col]]
        fig.add_bar(x=years, y=data[col], name=labels[col], marker_color=COLUMN_COLORS.get(col, "#888888"),
                    hovertext=[f"{y}<br>{labels[col]}: {v}" for y, v in zip(years, values)], hovertemplate=HOVER)
    fig.update_layout(barmode="stack")
    fig.update_xaxes(type="category")
    _layout(fig, height=330, legend=True,
            ytitle=t("chart.percent_of_total") if unit == "share" else t("chart.mwh_per_day"),
            ysuffix="%" if unit == "share" else "")
    if unit != "share":
        fig.update_yaxes(tickformat="~s")
    return fig


def seasonality(monthly, color="#2C7FB8"):
    names = [i18n.month_abbr(m) for m in monthly.index]
    fig = go.Figure()
    fig.add_scatter(x=names, y=monthly.values, mode="lines+markers",
                    line=dict(color=color, width=3, shape="spline"), marker=dict(size=8, color="#FFFFFF",
                    line=dict(color=color, width=2.5)), fill="tozeroy", fillcolor="rgba(44,127,184,0.12)",
                    hovertext=[f"{n}: {pct(v)}" for n, v in zip(names, monthly.values)], hovertemplate=HOVER)
    hi, lo = monthly.idxmax(), monthly.idxmin()
    for m, pos in ((hi, "top center"), (lo, "bottom center")):
        fig.add_annotation(x=i18n.month_abbr(m), y=monthly[m], text=f"{i18n.month_abbr(m)} {pct(monthly[m])}",
                           showarrow=False, yshift=18 if pos == "top center" else -20, font=dict(size=13))
    _layout(fig, height=280, ysuffix="%")
    fig.update_xaxes(type="category")
    fig.update_yaxes(range=[max(0, monthly.min() - 10), min(100, monthly.max() + 8)])
    return fig


def price_lines(series, unit, labels, colors):
    fig = go.Figure()
    for col in series.columns:
        when = day if unit == "day" else month
        fig.add_scatter(x=series.index, y=series[col], mode="lines", name=labels[col],
                        line=dict(color=colors[col], width=3, shape="spline" if unit == "month" else "linear"),
                        fill="tozeroy" if len(series.columns) == 1 else None, fillcolor="rgba(217,130,43,0.15)",
                        hovertext=[f"{when(d)}: {num(v)} EUR/MWh" for d, v in series[col].items()],
                        hovertemplate="%{hovertext}<extra>" + labels[col] + "</extra>")
    _layout(fig, height=300, legend=len(series.columns) > 1, ytitle="EUR/MWh")
    _date_axis(fig, series.index.min(), series.index.max())
    return fig


def yearly_bars(values, labels, color, suffix="%", highlight=()):
    colors = [color if y in highlight or not highlight else "rgba(217,130,43,0.35)" for y in values.index]
    texts = [f"{num(v, 1)}{suffix}" for v in values.values]
    fig = go.Figure(go.Bar(x=labels, y=values.values, marker_color=colors, text=texts, textposition="outside",
                           cliponaxis=False, hovertext=[f"{x}: {v}" for x, v in zip(labels, texts)],
                           hovertemplate=HOVER))
    _layout(fig, height=240, ysuffix=suffix)
    fig.update_xaxes(type="category")
    fig.update_yaxes(range=[0, values.max() * 1.25])
    return fig


def monthly_line(series, color="#1F5A8A", ytitle="MWh"):
    fig = go.Figure(go.Scatter(x=series.index, y=series.values, mode="lines+markers", line=dict(color=color, width=3),
                               marker=dict(size=7), fill="tozeroy", fillcolor="rgba(31,90,138,0.12)",
                               hovertext=[f"{month(d)}: {num(v)} MWh" for d, v in series.items()],
                               hovertemplate=HOVER))
    _layout(fig, height=240, ytitle=ytitle)
    fig.update_yaxes(rangemode="tozero", tickformat="~s")
    _date_axis(fig, series.index.min(), series.index.max())
    return fig


def municipality_map(totals, geojson, column, title):
    # A few large municipalities would wash out the rest, so the colour scale tops out at the 95th percentile.
    cap = totals[column].quantile(0.95)
    has_population = "kwh_per_resident" in totals
    hover = []
    for r in totals.itertuples():
        text = f"<b>{r.municipality}</b> ({r.district})<br>{num(r.energy_mwh)} MWh"
        if has_population:
            text += f"<br>{num(r.kwh_per_resident)} {t('chart.kwh_per_resident')}"
        hover.append(text)
    fig = go.Figure(go.Choropleth(
        geojson=geojson, locations=totals["key"], z=totals[column], featureidkey="properties.key",
        zmin=0, zmax=cap if cap else None,
        colorscale=[[0, "#DCE9F5"], [0.5, "#5FA2D3"], [1, "#1F5A8A"]], marker_line_color="#FFFFFF",
        marker_line_width=0.4, hovertext=hover, hovertemplate=HOVER,
        colorbar=dict(title=dict(text=title, side="top"), orientation="h", x=0.5, xanchor="center", y=-0.02,
                      yanchor="top", thickness=10, len=0.7, outlinewidth=0, tickformat="~s"),
    ))
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)", projection_type="mercator")
    _layout(fig, height=600)
    return fig


def window_errors(per_window, models, labels, colors):
    fig = go.Figure()
    for m in models:
        fig.add_scatter(x=per_window.index, y=per_window[m], mode="lines+markers", name=labels[m],
                        line=dict(color=colors[m], width=3), marker=dict(size=6),
                        hovertext=[t("chart.window_from", date=day(d), value=num(v, 2))
                                   for d, v in per_window[m].items()],
                        hovertemplate="%{hovertext}<extra>" + labels[m] + "</extra>")
    _layout(fig, height=280, legend=True, ytitle=t("chart.mae"))
    _date_axis(fig, per_window.index.min(), per_window.index.max())
    return fig


def window_detail(window, models, labels, colors):
    fig = go.Figure()
    fig.add_scatter(x=window["date"], y=window["actual"], mode="lines+markers", name=t("chart.actual"),
                    line=dict(color="#10293A", width=2), marker=dict(size=4),
                    hovertext=[f"{day(d)}: {pct(v)}" for d, v in zip(window["date"], window["actual"])],
                    hovertemplate="%{hovertext}<extra>" + t("chart.actual") + "</extra>")
    for m in models:
        fig.add_scatter(x=window["date"], y=window[m], mode="lines", name=labels[m],
                        line=dict(color=colors[m], width=2.5, dash="dot" if m == "persistence" else None),
                        hovertext=[f"{day(d)}: {pct(v)}" for d, v in zip(window["date"], window[m])],
                        hovertemplate="%{hovertext}<extra>" + labels[m] + "</extra>")
    _layout(fig, height=300, legend=True, ysuffix="%")
    _date_axis(fig, window["date"].min(), window["date"].max())
    return fig


def blackout_lines(daily, compare_year, column, label, colors, dark=True):
    fig = go.Figure()
    for year, dash, width in ((compare_year, "dash", 2), (2025, None, 3)):
        part = daily.loc[f"{year}-03-01":f"{year}-08-31", column].rolling(7, min_periods=4).mean()
        part.index = part.index.map(lambda d: d.replace(year=2025))
        fig.add_scatter(x=part.index, y=part.values, mode="lines", name=str(year),
                        line=dict(color=colors[year], width=width, dash=dash),
                        hovertext=[f"{day_month(d)}: {num(v)} {t('chart.mwh_a_day')}" for d, v in part.items()],
                        hovertemplate="%{hovertext}<extra>" + str(year) + "</extra>")
    fig.add_vline(x="2025-04-28", line_color="#FF7A6B", line_width=1.5)
    fig.add_annotation(x="2025-04-28", y=1, yref="paper", text=t("chart.blackout"), showarrow=False,
                       xanchor="left", xshift=6, font=dict(color="#FF9A8B", size=12))
    _layout(fig, dark=dark, height=280, legend=True, ytitle=t("chart.mwh_per_day"))
    months = list(range(3, 9))
    fig.update_xaxes(tickmode="array", tickvals=[f"2025-{m:02d}-01" for m in months],
                     ticktext=[i18n.month_abbr(m) for m in months])
    fig.update_yaxes(tickformat="~s", rangemode="tozero")
    return fig


def change_bars(change, labels, colors, dark=True):
    order = list(change.index)
    texts = [num(v, signed=True) for v in change.values]
    fig = go.Figure(go.Bar(y=[labels[c] for c in order], x=change.values, orientation="h",
                           marker_color=[colors[c] for c in order], text=texts, textposition="outside",
                           cliponaxis=False,
                           hovertext=[f"{labels[c]}: {x} {t('chart.mwh_a_day')}" for c, x in zip(order, texts)],
                           hovertemplate=HOVER))
    _layout(fig, dark=dark, height=320)
    fig.update_yaxes(autorange="reversed")
    span = max(abs(change.min()), abs(change.max())) * 1.3
    fig.update_xaxes(range=[-span, span], zeroline=True, zerolinecolor="#6F8496", tickformat="~s")
    return fig
