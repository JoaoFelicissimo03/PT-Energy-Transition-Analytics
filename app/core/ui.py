"""Page frame shared by every chapter: styles, hero, chapter navigation, filter bar, cards and footer."""
from html import escape

import streamlit as st

from core import i18n, theme
from core.hero import landscape
from core.i18n import t

STORY = ["now", "shift", "cost", "use", "next"]
ORDER = STORY + ["blackout"]
PAGES = {}  # filled by app.py with the st.Page objects


def nav_label(slug):
    """'02 How we got here' for the story chapters, 'Bonus: the 2025 blackout' for the bonus."""
    if slug == "blackout":
        return t("nav.blackout")
    return f"{STORY.index(slug) + 1:02d} {t(f'chapter.{slug}')}"


def chip(slug):
    """The small line above each title: 'Chapter 02 of 05 · How we got here'."""
    if slug == "blackout":
        return t("chip.bonus", title=t("chapter.blackout"))
    return t("chip.story", n=f"{STORY.index(slug) + 1:02d}", title=t(f"chapter.{slug}"))


def register_pages(pages):
    PAGES.update(pages)


def page_setup(chapter):
    i18n.init()
    st.html(theme.css(chapter))


# ----------------------------------------------------------------------------- remembered filter values
def remembered(store_key, default, allowed=None):
    value = st.session_state.get(f"_keep_{store_key}", default)
    if allowed is not None and value not in allowed:
        value = default
    return value


def keep(store_key, value):
    st.session_state[f"_keep_{store_key}"] = value


def segmented(label, options, labels, store_key, default, widget_key, hide_label=False):
    current = remembered(store_key, default, options)
    value = st.segmented_control(label, options, default=current, format_func=lambda o: labels[o],
                                 key=widget_key, required=True,
                                 label_visibility="collapsed" if hide_label else "visible")
    keep(store_key, value)
    return value


def definition_control(chapter):
    """Renewable share definition: shared by all chapters."""
    return segmented(t("def.label"), ["domestic", "imports"],
                     {"domestic": t("def.domestic"), "imports": t("def.imports")},
                     "definition", "domestic", f"definition_{chapter}")


def period_control(chapter, options, default, labels=None):
    """Period: each chapter remembers its own choice."""
    return segmented(t("filter.period"), options, labels or i18n.period_labels(options), f"period_{chapter}",
                     default, f"period_{chapter}")


def language_control():
    """EN | PT switch next to the title. The choice is kept while navigating and written in the page link."""
    with st.container(key="langswitch", width="content"):
        return segmented(t("lang.label"), list(i18n.LANGS), {"en": "EN", "pt": "PT"}, "lang", i18n.lang(),
                         "lang_widget", hide_label=True)


# ----------------------------------------------------------------------------- hero and navigation
BRAND_ICON = ('<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
              'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10">'
              '</circle><path d="M13 5 8 13h4l-1 6 5-8h-4z"></path></svg>')


def topbar(chapter, updated):
    with st.container(key="topbar", gap="small"):
        with st.container(key="brandrow", horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
            with st.container(key="brandleft", horizontal=True, vertical_alignment="center", width="content"):
                st.html(f'<div class="brand">{BRAND_ICON}{escape(t("brand"))}</div>', width="content")
                language_control()
            st.html(f'<div class="updated">{escape(updated)}</div>', width="content")
        with st.container(key="nav", horizontal=True, gap=None, width="content", vertical_alignment="center"):
            for slug in ORDER:
                state = "on" if slug == chapter else "off"
                key = f"navbonus{state}" if slug == "blackout" else f"nav{state}-{slug}"
                with st.container(key=key, width="content"):
                    st.page_link(PAGES[slug], label=nav_label(slug))


def hero(slot, chapter, chip, title, subtitle, updated, note=None):
    with slot.container(key="hero"):
        st.html(landscape(chapter))
        topbar(chapter, updated)
        note_html = f'<div class="note">{escape(note)}</div>' if note else ""
        st.html(f'<div class="hero"><div class="chip">{escape(chip)}</div><h1>{escape(title)}</h1>'
                f'<p>{escape(subtitle)}</p>{note_html}</div>')


def filter_bar():
    return st.container(key="filterbar")


def card(name, dark=False):
    return st.container(key=f"{'dcard' if dark else 'card'}-{name}")


def footer(chapter, source_html):
    with st.container(key="footer", horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
        if chapter == "blackout":
            with st.container(key="footprev", width="content"):
                st.page_link(PAGES["next"], label=t("footer.back_end"))
            st.html(f'<div class="source-note">{source_html}</div>', width="stretch")
            with st.container(key="footnext", width="content"):
                st.page_link(PAGES["now"], label=t("footer.back_start"))
            return
        i = STORY.index(chapter)
        if i > 0:
            with st.container(key="footprev", width="content"):
                st.page_link(PAGES[STORY[i - 1]], label=t("footer.prev", title=t(f"chapter.{STORY[i - 1]}")))
        st.html(f'<div class="source-note">{source_html}</div>', width="stretch")
        if i < len(STORY) - 1:
            with st.container(key="footnext", width="content"):
                st.page_link(PAGES[STORY[i + 1]], label=t("footer.next", title=t(f"chapter.{STORY[i + 1]}")))
        else:
            with st.container(key="footnext", width="content"):
                st.page_link(PAGES["blackout"], label=t("footer.bonus"))


# ----------------------------------------------------------------------------- small HTML pieces
def html(markup):
    st.html(markup)


def title(text, note=None):
    note_html = f'<p class="card-note">{escape(note)}</p>' if note else ""
    st.html(f'<div style="display:flex;flex-direction:column;gap:6px"><h2 class="card-title">{escape(text)}</h2>{note_html}</div>')


def kpi(label, value, unit=None, note=None, color=None):
    unit_html = f"<small> {escape(unit)}</small>" if unit else ""
    style = f' style="color:{color}"' if color else ""
    note_html = f'<div class="kpi-note">{escape(note)}</div>' if note else ""
    st.html(f'<div class="kpi"><div class="kpi-label">{escape(label)}</div>'
            f'<div class="kpi-value"{style}>{escape(value)}{unit_html}</div>{note_html}</div>')


def legend(items):
    spans = "".join(f'<span><i class="dot" style="background:{c}"></i>{escape(t)}</span>' for t, c in items)
    st.html(f'<div class="legend">{spans}</div>')


def bar_list(rows, label_width=110, value_width=80, color="#1F5A8A", max_value=None):
    """Horizontal bars in HTML: rows are (label, value, value_text) or (label, value, value_text, color)."""
    if not rows:
        return
    top = max_value or max(abs(r[1]) for r in rows) or 1
    cells = []
    for row in rows:
        label, value, text = row[:3]
        c = row[3] if len(row) > 3 else color
        width = max(1.5, abs(value) / top * 100)
        cells.append(f'<span>{escape(label)}</span><div class="bar-track"><div class="bar-fill" '
                     f'style="width:{width:.1f}%;background:{c}"></div></div><span style="text-align:right">{escape(text)}</span>')
    st.html(f'<div class="bars" style="grid-template-columns:{label_width}px minmax(0,1fr) {value_width}px">{"".join(cells)}</div>')


def empty(message):
    st.html(f'<div class="empty">{escape(message)}</div>')


def gauge(value, color="#2C7FB8", track="#DCE7EC", text_color="#10293A"):
    """Semicircle gauge (0 to 100) drawn in SVG, with the number in HTML so it uses the page font."""
    import math
    from core.hero import svg_img
    v = max(0.0, min(100.0, value))
    angle = math.pi * (1 - v / 100)
    x, y = 110 + 90 * math.cos(angle), 110 - 90 * math.sin(angle)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 122">'
           f'<path d="M20,110 A90,90 0 0 1 200,110" fill="none" stroke="{track}" stroke-width="16" stroke-linecap="round"/>'
           f'<path d="M20,110 A90,90 0 0 1 {x:.1f},{y:.1f}" fill="none" stroke="{color}" stroke-width="16" stroke-linecap="round"/></svg>')
    return (f'<div style="position:relative;width:100%;max-width:240px;margin:6px auto 0">'
            f'{svg_img(svg, t("gauge.alt", value=i18n.num(v, 1)), "width:100%;display:block")}'
            f'<div style="position:absolute;left:0;right:0;bottom:8%;text-align:center;font-size:36px;'
            f'font-weight:500;color:{text_color}">{i18n.pct(v)}</div></div>')
