"""Language support: translated strings plus number and date formatting for English and Portuguese.

The language of the running script is kept in a context variable, so two visitors using the dashboard at the
same time never see each other's language. `init()` reads the choice (language switch, then the link, then the
browser) at the start of every page run.
"""
import contextvars

import pandas as pd
import streamlit as st

from core.locale_en import STRINGS as EN
from core.locale_pt import STRINGS as PT

LANGS = ("en", "pt")
STRINGS = {"en": EN, "pt": PT}
NBSP = " "

MONTHS = {
    "en": {
        "abbr": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "full": ["January", "February", "March", "April", "May", "June", "July", "August", "September",
                 "October", "November", "December"],
    },
    "pt": {
        "abbr": ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
        "full": ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro",
                 "outubro", "novembro", "dezembro"],
    },
}
# Districts whose name takes an article in Portuguese: "distrito do Porto", "distrito da Guarda"
DISTRICT_ARTICLE = {"Porto": "do Porto", "Guarda": "da Guarda"}

_current = contextvars.ContextVar("lang", default="en")


# ----------------------------------------------------------------------------- choosing the language
def set_lang(lang):
    _current.set(lang if lang in LANGS else "en")


def lang():
    return _current.get()


def browser_language():
    """Portuguese if the visitor's browser is set to Portuguese, English otherwise."""
    try:
        locale = st.context.locale
    except Exception:
        return "en"
    return "pt" if locale and str(locale).lower().startswith("pt") else "en"


def resolve():
    """The language for this run: the switch, then the previous choice, then the link, then the browser."""
    for candidate in (st.session_state.get("lang_widget"), st.session_state.get("_keep_lang")):
        if candidate in LANGS:
            return candidate
    query = st.query_params.get("lang")
    return query if query in LANGS else browser_language()


def init():
    """Set the language for this run and mirror it in the link, so a shared link opens in the same language."""
    chosen = resolve()
    st.session_state["_keep_lang"] = chosen
    if st.query_params.get("lang") != chosen:
        st.query_params["lang"] = chosen
    set_lang(chosen)
    return chosen


# ----------------------------------------------------------------------------- strings
def t(key, **values):
    """A translated string. Falls back to English if a key is missing in Portuguese."""
    table = STRINGS[lang()]
    text = table[key] if key in table else EN[key]
    return text.format(**values) if values else text


def cap(text):
    """First letter in capitals, leaving the rest as it is."""
    return text[:1].upper() + text[1:]


def lower_first(text):
    """First letter in lower case, leaving the rest as it is."""
    return text[:1].lower() + text[1:]


def separators():
    """Plotly decimal and thousands separators."""
    return ", " if lang() == "pt" else ".,"


# ----------------------------------------------------------------------------- numbers
def missing(x):
    return x is None or bool(pd.isna(x))


def _localise(text):
    if lang() == "pt":
        return text.replace(",", "\x00").replace(".", ",").replace("\x00", NBSP)
    return text


def num(x, decimals=0, signed=False):
    """1,234.5 in English and 1 234,5 in Portuguese; the 'not available' text for missing values."""
    if missing(x):
        return t("na")
    return _localise(format(x, f"{'+' if signed else ''},.{decimals}f"))


def pct(x, decimals=1, signed=False):
    return t("na") if missing(x) else num(x, decimals, signed) + "%"


def pp(x, decimals=1):
    return t("na") if missing(x) else f"{num(x, decimals, signed=True)} {t('unit.pp')}"


# ----------------------------------------------------------------------------- dates
def month_abbr(m):
    """Short month name for a month number (1 to 12)."""
    return MONTHS[lang()]["abbr"][int(m) - 1]


def month_name(ts):
    """Full month name: capitalised in English, lower case in Portuguese."""
    return MONTHS[lang()]["full"][pd.Timestamp(ts).month - 1]


def day(ts):
    ts = pd.Timestamp(ts)
    return f"{ts.day} {month_abbr(ts.month)} {ts.year}"


def month(ts):
    ts = pd.Timestamp(ts)
    return f"{month_abbr(ts.month)} {ts.year}"


def day_month(ts):
    ts = pd.Timestamp(ts)
    return f"{ts.day} {month_abbr(ts.month)}"


# ----------------------------------------------------------------------------- labels that depend on a code
def period_labels(options=("30d", "12m", "ytd", "all")):
    return {p: t(f"period.{p}") for p in options}


def source_labels(columns=None):
    columns = columns or ["hydro_mwh", "wind_mwh", "solar_mwh", "biomass_mwh", "wave_mwh", "natural_gas_mwh",
                          "other_thermal_mwh", "coal_mwh", "import_mwh", "export_mwh", "consumption_mwh"]
    return {c: t(f"src.{c}") for c in columns}


def model_labels(models=("persistence", "mean_7d", "linear_regression", "climatology", "prophet")):
    return {m: t(f"model.{m}") for m in models}


def district_label(name):
    """'Lisboa district' in English, 'distrito de Lisboa' in Portuguese (with the article where it is needed)."""
    if lang() == "pt":
        return f"distrito {DISTRICT_ARTICLE.get(name, f'de {name}')}"
    return f"{name} district"
