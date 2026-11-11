"""Energy Transition & Electric Mobility in Portugal: dashboard entry point.

Run from the project root:
    streamlit run app/app.py
"""
import streamlit as st

from core import i18n, ui
from core.i18n import t

# The language is chosen before the page configuration, because the browser tab title depends on it
i18n.set_lang(i18n.resolve())

st.set_page_config(
    page_title=t("brand"),
    page_icon=":material/bolt:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# URL paths stay in English in both languages, so a shared link always works; only the visible titles change
PAGES = {
    "now": st.Page("chapters/c1_now.py", title=t("chapter.now"), url_path="where-we-are", default=True),
    "shift": st.Page("chapters/c2_shift.py", title=t("chapter.shift"), url_path="how-we-got-here"),
    "cost": st.Page("chapters/c3_cost.py", title=t("chapter.cost"), url_path="what-it-costs"),
    "use": st.Page("chapters/c4_use.py", title=t("chapter.use"), url_path="where-it-is-used"),
    "next": st.Page("chapters/c5_next.py", title=t("chapter.next"), url_path="what-comes-next"),
    "blackout": st.Page("chapters/bonus_blackout.py", title=t("chapter.blackout"), url_path="bonus-2025-blackout"),
}
ui.register_pages(PAGES)

st.navigation(list(PAGES.values()), position="hidden").run()
