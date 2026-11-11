"""English and Portuguese: both dictionaries match, the Portuguese sentences read well, every page works in both
languages and no English is left over in the Portuguese pages."""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from core import i18n, text
from core.locale_en import STRINGS as EN
from core.locale_pt import STRINGS as PT

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "app.py"
PROCESSED = ROOT / "data" / "processed"
NBSP = " "
needs_data = pytest.mark.skipif(not (PROCESSED / "ren_daily_production.csv").exists(),
                                reason="run the notebooks first to create data/processed")


def placeholders(s):
    return sorted(re.findall(r"\{(\w+)\}", s))


# ----------------------------------------------------------------------------- the dictionaries
def test_both_languages_have_the_same_keys():
    assert sorted(set(EN) - set(PT)) == []
    assert sorted(set(PT) - set(EN)) == []


def test_placeholders_match_between_languages():
    bad = {k: (placeholders(EN[k]), placeholders(PT[k])) for k in EN if placeholders(EN[k]) != placeholders(PT[k])}
    assert bad == {}


def test_no_empty_texts_and_no_em_dashes():
    for table in (EN, PT):
        assert all(v.strip() for v in table.values())
        assert not [k for k, v in table.items() if "—" in v]


def test_every_key_used_in_the_code_exists():
    used = set()
    for path in (ROOT / "app").rglob("*.py"):
        if path.name.startswith("locale_"):
            continue
        used |= set(re.findall(r'\bt\(\s*"([^"]+)"', path.read_text(encoding="utf-8")))
    used -= {"horizon."}  # built from the horizon code, checked below
    assert sorted(k for k in used if k not in EN) == []
    for code in ("1 day", "60 days"):
        assert f"horizon.{code}" in EN


def test_keys_built_from_codes_exist():
    from core import stats

    checks = [f"period.{p}" for p in ("30d", "12m", "ytd", "all")] + [f"period_in.{p}" for p in ("30d", "12m", "ytd", "all")]
    checks += [f"{form}.{p}" for form in ("cmp", "cmp_in", "cmp_to") for p in ("30d", "12m", "ytd")]
    checks += [f"{form}.{c}" for form in ("src", "srcart") for c in
               ["hydro_mwh", "wind_mwh", "solar_mwh", "biomass_mwh", "wave_mwh", "natural_gas_mwh", "other_thermal_mwh",
                "coal_mwh", "import_mwh", "export_mwh", "consumption_mwh"]]
    checks += [f"srcin.{c}" for c in stats.RENEWABLE if c != "wave_mwh"]
    checks += [f"model.{m}" for m in stats.MODELS] + [f"modelphrase.{m}" for m in stats.MODELS]
    checks += [f"horizon.{h}" for h in set(stats.HORIZON.values())]
    checks += [f"mix.{n}" for n in ("Hydro", "Wind", "Solar", "Biomass", "Gas and other", "Imports")]
    checks += [f"frac.{f}" for _, f in text.FRACTIONS if f != "half"]
    checks += [f"place.{d}.{k}" for d in ("domestic", "imports") for k in ("mass", "units")]
    checks += [f"market.{m}" for m in ("pt", "es", "both")] + [f"market_adj.{m}" for m in ("pt", "es")]
    checks += [f"chapter.{c}" for c in ("now", "shift", "cost", "use", "next", "blackout")]
    checks += [f"unit.{u}" for u in ("pp", "day", "week", "month", "kwh_per_resident")]
    assert [k for k in checks if k not in EN or k not in PT] == []


# ----------------------------------------------------------------------------- numbers and dates
def test_portuguese_numbers_and_dates():
    i18n.set_lang("pt")
    assert text.pct(81.63) == "81,6%"
    assert text.num(23790.4) == f"23{NBSP}790"
    assert text.num(1234567.8, 1) == f"1{NBSP}234{NBSP}567,8"
    assert text.pp(5.06) == "+5,1 p.p."
    assert text.num(-3.2, 1, signed=True) == "-3,2"
    assert text.day("2026-10-07") == "7 out 2026"
    assert text.month("2026-04-01") == "abr 2026"
    assert text.num(np.nan) == text.pct(None) == text.pp(np.nan) == "n/d"
    assert i18n.separators() == f",{NBSP}"


def test_english_numbers_are_unchanged():
    assert text.num(1234567.8, 1) == "1,234,567.8"
    assert i18n.separators() == ".,"


def test_district_names():
    assert i18n.district_label("Lisboa") == "Lisboa district"
    i18n.set_lang("pt")
    assert i18n.district_label("Lisboa") == "distrito de Lisboa"
    assert i18n.district_label("Porto") == "distrito do Porto"
    assert i18n.district_label("Guarda") == "distrito da Guarda"


# ----------------------------------------------------------------------------- sentences in Portuguese
def test_portuguese_sentences():
    i18n.set_lang("pt")
    assert text.now_headline(81.6, "domestic") == \
        "Quatro em cada cinco unidades de eletricidade produzidas em Portugal são renováveis"
    assert text.now_headline(51, "imports") == "Cerca de metade da eletricidade fornecida em Portugal é renovável"
    assert text.now_headline(38.2, "domestic") == "38% da eletricidade produzida em Portugal é renovável"
    assert text.change_note(5.06, "30d") == "+5,1 p.p. face aos mesmos 30 dias do ano anterior"
    assert text.change_note(0.04, "ytd") == "Quase sem alteração face aos mesmos dias do ano anterior"
    assert text.change_note(np.nan, "12m") == "Sem dados para os 12 meses anteriores"
    assert text.change_note(1.0, "all") == "Todo o período dos dados"
    assert text.cost_headline(9.6, 80, "12m") == "A eletricidade grossista custa 10% mais do que nos 12 meses anteriores"
    assert text.cost_headline(250, 80, "30d").endswith("o que custava nos mesmos 30 dias do ano anterior")
    assert text.cost_headline(np.nan, 98.2, "all") == "O preço grossista da eletricidade teve uma média de 98 EUR/MWh"
    assert text.shift_headline(2022, 62.3, 2024, 88.7) == "De 62,3% renovável em 2022 para 88,7% em 2024"
    out = text.shift_subtitle(("hydro_mwh", 23790, 50333), 30000, 9000, 2022, 2024)
    assert out.startswith(f"A maior diferença foi na energia hídrica: 23{NBSP}790 MWh por dia em 2022")
    assert out.endswith("A produção de gás foi 70% inferior em 2024.")
    sub = text.cost_subtitle("ytd", "2026-01-01", "2026-10-27", 80, 70, pd.DataFrame({"corr": [-0.2]}), "es")
    assert sub.startswith("Em 2026, até agora, o preço espanhol teve uma média de 80 EUR/MWh, contra 70 nos mesmos dias")
    assert text.period_phrase("all", "2021-10-27", "2026-10-27") == "Desde outubro de 2021"


def test_portuguese_district_and_forecast_sentences():
    i18n.set_lang("pt")
    shares = pd.Series({"Lisboa": 37.1, "Porto": 15.9, "Setubal": 10.8})
    assert text.use_headline(shares) == "O carregamento de veículos elétricos concentra-se em torno de Lisboa e Porto"
    assert text.use_headline(shares, "Porto").startswith("O distrito do Porto concentra 15,9%")
    one = pd.Timestamp("2026-04-01")
    assert text.use_subtitle(shares, one, one, "Lisboa", "Sintra") == \
        "Em abr 2026, o concelho com mais energia de carregamento no distrito de Lisboa foi Sintra."
    assert "o distrito do Porto 15,9%" in text.use_subtitle(shares, one, one)
    table = pd.DataFrame({"mae": [2.6, 2.9, 5.0], "horizon": ["1 day", "1 day", "60 days"],
                          "beats_persistence": [np.nan, 8, 2], "windows": [18, 18, 18]},
                         index=["persistence", "linear_regression", "prophet"])
    assert text.next_headline(table) == "Amanhã deverá ser muito parecido com hoje"
    assert "o modelo de regressão linear superou-a em 8" in text.next_subtitle(table)
    table.loc["linear_regression", "mae"] = 2.0
    assert text.next_headline(table).startswith("O modelo de regressão linear já bate")


# ----------------------------------------------------------------------------- the whole app
PAGES = [None, "c2_shift", "c3_cost", "c4_use", "c5_next", "bonus_blackout"]
# Words that only exist in English. Names such as "Open Data" or "Prophet" are fine and not listed.
ENGLISH_WORDS = {"the", "and", "of", "with", "was", "were", "than", "from", "for", "by", "this", "last", "first",
                 "best", "weakest", "renewable", "chapter", "lights", "average", "price", "prices", "day",
                 "days", "year", "years", "month", "months", "select", "needs", "not", "available", "mean"}
ENGLISH_MONTHS = re.compile(r"\b(Jan|Feb|Apr|May|Aug|Sep|Oct|Dec|January|February|April|June|July|August|"
                            r"September|October|December)\b")


def run(page, lang, state=None):
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.session_state["_keep_lang"] = lang
    for key, value in (state or {}).items():
        at.session_state[f"_keep_{key}"] = value
    at.run()
    if page:
        at.switch_page(f"chapters/{page}.py")
        at.run()
    assert not at.exception, [e.message for e in at.exception]
    return at


def visible_text(at):
    """Words shown on the page: texts of the html blocks (without markup) and the widget labels."""
    parts = []
    for h in at.get("html"):
        body = str(h.proto.body)
        if body.lstrip().startswith("<style") or "hero-bg" in body:
            continue
        parts.append(re.sub(r"<[^>]+>", " ", body))
    for group in at.get("button_group"):
        parts.append(str(group.label))
        parts.extend(str(o) for o in group.options)
    for w in list(at.select_slider) + list(at.selectbox):
        parts.append(str(w.label))
    return " ".join(parts)


def figures(at):
    return [json.loads(c.proto.spec) for c in at.get("plotly_chart")]


@needs_data
@pytest.mark.parametrize("page", PAGES)
def test_every_page_works_in_both_languages(page):
    en, pt = run(page, "en"), run(page, "pt")
    assert "Energy Transition Portugal" in visible_text(en)
    assert "Transição Energética Portugal" in visible_text(pt)
    assert len(figures(en)) == len(figures(pt))


@needs_data
@pytest.mark.parametrize("page", PAGES)
def test_no_english_left_in_the_portuguese_pages(page):
    at = run(page, "pt")
    words = {w.lower() for w in re.findall(r"[A-Za-zÀ-ÿ]+", visible_text(at))}
    assert sorted(words & ENGLISH_WORDS) == []
    assert not ENGLISH_MONTHS.search(visible_text(at))


@needs_data
@pytest.mark.parametrize("page", PAGES)
def test_figures_follow_the_language(page):
    for spec in figures(run(page, "pt")):
        assert spec["layout"]["separators"] == f",{NBSP}"
        texts = []
        for trace in spec["data"]:
            texts += list(trace.get("hovertext") or []) + [trace.get("name") or ""]
            texts += [str(x) for x in (trace.get("text") or []) if isinstance(x, str)]
        texts += list(spec["layout"].get("xaxis", {}).get("ticktext") or [])
        assert not ENGLISH_MONTHS.search(" ".join(map(str, texts)))
        assert not [t for t in texts if re.search(r"\bMWh a day\b|\bRenewable\b|\bWindow from\b", str(t))]
    for spec in figures(run(page, "en")):
        assert spec["layout"]["separators"] == ".,"


@needs_data
def test_language_comes_from_the_link_and_is_written_back():
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.query_params["lang"] = "pt"
    at.run()
    assert not at.exception
    assert "Onde estamos" in visible_text(at)
    assert at.query_params["lang"] == ["pt"] or at.query_params["lang"] == "pt"


@needs_data
def test_language_switch_changes_the_page_and_the_link():
    at = run(None, "en")
    switch = next(g for g in at.get("button_group") if g.label == "Language")
    switch.set_value("pt").run()
    assert not at.exception
    assert "Transição Energética Portugal" in visible_text(at)
    assert at.session_state["_keep_lang"] == "pt"
    switch = next(g for g in at.get("button_group") if g.label == "Idioma")
    switch.set_value("en").run()
    assert "Energy Transition Portugal" in visible_text(at)


@needs_data
def test_filters_survive_a_language_change():
    at = run("c3_cost", "en", {"period_cost": "ytd", "market_cost": "es"})
    next(g for g in at.get("button_group") if g.label == "Language").set_value("pt").run()
    assert not at.exception
    assert at.session_state["_keep_period_cost"] == "ytd" and at.session_state["_keep_market_cost"] == "es"
    assert "Em 2026" in visible_text(at) or "Em 20" in visible_text(at)


@needs_data
def test_district_choice_survives_a_language_change():
    at = run("c4_use", "en", {"district_use": "Lisboa"})
    next(g for g in at.get("button_group") if g.label == "Language").set_value("pt").run()
    assert not at.exception
    assert at.session_state["_keep_district_use"] == "Lisboa"
    assert "distrito de Lisboa" in visible_text(at)
