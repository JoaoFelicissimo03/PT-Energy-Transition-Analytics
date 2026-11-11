"""Every sentence in the dashboard is built here from the numbers, so it stays true after each pipeline run.

The wording of each sentence lives in core/locale_en.py and core/locale_pt.py. Here only the choices are made:
which sentence applies, and which numbers go into it.
"""
import pandas as pd

from core import i18n
from core.i18n import missing, month, num, pct, pp, t

day = i18n.day  # re-exported for the chapters


# ----------------------------------------------------------------------------- periods
def period_phrase(period, start, end):
    """'Over the last 30 days', 'So far in 2026', 'Since October 2021'."""
    if period == "ytd":
        return t("phrase.ytd", year=pd.Timestamp(end).year)
    if period == "all":
        return t("phrase.all", month=i18n.month_name(start), year=pd.Timestamp(start).year)
    return t(f"phrase.{period}")


def comparison_phrase(period, form=""):
    """The earlier period a figure is compared with. `form` picks the grammatical form: '' , '_in' or '_to'."""
    return None if period == "all" else t(f"cmp{form}.{period}")


# ----------------------------------------------------------------------------- chapter 01
FRACTIONS = [(0.5, "half"), (0.6, "three in five"), (2 / 3, "two in three"), (0.75, "three in four"),
             (0.8, "four in five"), (5 / 6, "five in six"), (0.9, "nine in ten")]


def share_fraction(share):
    """The plain-language fraction closest to a share in percent, or None below about 45%."""
    if missing(share) or share < 45:
        return None
    value = share / 100
    return min(FRACTIONS, key=lambda f: abs(f[0] - value))[1]


def now_headline(share, definition):
    fraction = share_fraction(share)
    if fraction is None:
        return t("now.headline.low", share=pct(share, 0), place=t(f"place.{definition}.mass"))
    if fraction == "half":
        return t("now.headline.half", place=t(f"place.{definition}.mass"))
    return t("now.headline.fraction", fraction=t(f"frac.{fraction}"), place=t(f"place.{definition}.units"))


def now_subtitle(period, start, end, share, definition):
    return t(f"now.subtitle.{definition}", lead=period_phrase(period, start, end), share=pct(share))


def change_note(change, period, unit="pp"):
    phrase = comparison_phrase(period, "_to")
    if phrase is None:
        return t("note.whole")
    if missing(change):
        return t("note.nodata", phrase=comparison_phrase(period))
    if unit == "pp":
        if round(change, 1) == 0:
            return t("note.same", phrase=phrase)
        return t("note.change", value=pp(change), phrase=phrase)
    if round(change) == 0:
        return t("note.same", phrase=phrase)
    return t("note.change", value=pct(change, 0, signed=True), phrase=phrase)


# ----------------------------------------------------------------------------- chapter 02
def shift_headline(weak_year, weak_share, best_year, best_share):
    if weak_year is None:
        return t("shift.headline.none")
    if weak_year == best_year:
        return t("shift.headline.single", share=pct(best_share), year=best_year)
    if weak_year < best_year:
        return t("shift.headline.rise", weak_share=pct(weak_share), weak_year=weak_year,
                 best_share=pct(best_share), best_year=best_year)
    return t("shift.headline.fall", best_share=pct(best_share), best_year=best_year,
             weak_share=pct(weak_share), weak_year=weak_year)


def shift_subtitle(drop, gas_weak, gas_best, weak_year, best_year):
    if drop is None or weak_year is None or weak_year == best_year:
        return t("shift.subtitle.none")
    source, low, high = drop
    gas_change = (gas_best / gas_weak - 1) * 100 if gas_weak else float("nan")
    gas_part = ""
    if not missing(gas_change):
        direction = t("dir.lower") if gas_change < 0 else t("dir.higher")
        gas_part = t("shift.subtitle.gas", pct=num(abs(gas_change)), direction=direction, year=best_year)
    return t("shift.subtitle.main", source=t(f"srcin.{source}"), low=num(low), weak_year=weak_year,
             high=num(high), best_year=best_year, gas=gas_part)


# ----------------------------------------------------------------------------- chapter 03
def cost_headline(change_pct, avg, period):
    phrase = comparison_phrase(period, "_in")
    if missing(change_pct) or phrase is None:
        return t("cost.headline.average", avg=num(avg))
    ratio = 1 + change_pct / 100
    rounded = round(change_pct)
    if ratio >= 3:
        return t("cost.headline.triple", phrase=phrase)
    if ratio >= 2:
        return t("cost.headline.double", phrase=phrase)
    if rounded >= 5:
        return t("cost.headline.more", value=rounded, phrase=phrase)
    if rounded <= -5:
        return t("cost.headline.less", value=abs(rounded), phrase=phrase)
    return t("cost.headline.same", phrase=phrase)


def correlation_sentence(correlations):
    """How consistently days with more renewables had lower prices, year by year."""
    if correlations is None or len(correlations) == 0:
        return ""
    negative = int((correlations["corr"] < 0).sum())
    total = len(correlations)
    if negative == total:
        return t("cost.corr.all")
    if negative >= total / 2:
        return t("cost.corr.some", negative=negative, total=total)
    return t("cost.corr.weak")


def cost_subtitle(period, start, end, avg, prev_avg, correlations, market):
    phrase = comparison_phrase(period, "_in")
    first = t("cost.subtitle.main", lead=period_phrase(period, start, end), market=t(f"market_adj.{market}"),
              avg=num(avg))
    if phrase and not missing(prev_avg):
        first += t("cost.subtitle.prev", prev=num(prev_avg), phrase=phrase)
    return f"{first}. {correlation_sentence(correlations)}".strip()


# ----------------------------------------------------------------------------- chapter 04
def use_headline(shares, district=None):
    if district:
        share = shares.get(district, float("nan"))
        return t("use.headline.district", district=i18n.district_label(district), share=pct(share))
    top = list(shares.index[:2])
    if len(top) == 2 and shares.iloc[:2].sum() >= 40:
        return t("use.headline.top", first=top[0], second=top[1])
    return t("use.headline.spread")


def use_subtitle(shares, month_start, month_end, district=None, top_municipality=None):
    span = (t("use.span.one", month=month(month_start)) if month_start == month_end
            else t("use.span.range", start=month(month_start), end=month(month_end)))
    if district:
        return t("use.subtitle.district", span=span, district=i18n.district_label(district),
                 municipality=top_municipality)
    return t("use.subtitle.top", span=span, first=i18n.district_label(shares.index[0]),
             first_share=pct(shares.iloc[0]), second=i18n.district_label(shares.index[1]),
             second_share=pct(shares.iloc[1]))


# ----------------------------------------------------------------------------- chapter 05
def next_headline(table):
    one_day = table[table["horizon"] == "1 day"]
    best = one_day["mae"].idxmin()
    if best == "persistence":
        return t("next.headline.persistence")
    return t("next.headline.challenger", model=i18n.cap(t(f"modelphrase.{best}")))


def next_subtitle(table):
    windows = int(table["windows"].iloc[0])
    one_day = table[(table["horizon"] == "1 day") & (table.index != "persistence")]
    if one_day.empty:
        return t("next.subtitle.only", windows=windows)
    challenger = one_day["mae"].idxmin()
    beats = int(one_day.loc[challenger, "beats_persistence"])
    return t("next.subtitle.main", windows=windows, model=t(f"modelphrase.{challenger}"), beats=beats)


# ----------------------------------------------------------------------------- bonus
def blackout_subtitle(share, change, compare_year):
    direction = t("dir.higher") if change["renewable_mwh"] >= 0 else t("dir.lower")
    return t("blackout.subtitle", compare_share=pct(share[compare_year]), compare_year=compare_year,
             share=pct(share[2025]), output=num(abs(change["renewable_mwh"])), direction=direction)
