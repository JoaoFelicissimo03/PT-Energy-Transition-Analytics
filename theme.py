"""Colours, chapter palettes and the CSS that turns Streamlit into the glass-card look of the sketches."""

from core.hero import SKIES

SOURCE_COLORS = {
    "Hydro": "#2C7FB8",
    "Wind": "#41AE76",
    "Solar": "#E6A700",
    "Biomass": "#8C6D31",
    "Wave": "#6BAED6",
    "Natural gas": "#8A97A3",
    "Gas and other": "#8A97A3",
    "Other thermal": "#B5B5B5",
    "Coal": "#4D4D4D",
    "Imports": "#8E6BB0",
    "Exports": "#C7B5DE",
    "Consumption": "#333333",
}
COLUMN_COLORS = {
    "hydro_mwh": "#2C7FB8", "wind_mwh": "#41AE76", "solar_mwh": "#E6A700", "biomass_mwh": "#8C6D31",
    "natural_gas_mwh": "#8A97A3", "other_thermal_mwh": "#B5B5B5", "coal_mwh": "#4D4D4D",
    "import_mwh": "#8E6BB0", "export_mwh": "#C7B5DE", "consumption_mwh": "#333333",
}
NAVY = "#10293A"
AMBER = "#D9822B"

# One palette per chapter. "dark" switches cards, text and widgets to the night look.
CHAPTERS = {
    "now": dict(bg="#E4EEF2", fg="#10293A", muted="#3C5A6E", card="rgba(255,255,255,0.82)",
                border="rgba(255,255,255,0.95)", accent="#2C7FB8", dark=False, hero_fg="#10293A",
                hero_muted="#24506E", chip="#24506E"),
    "shift": dict(bg="#E2EEF0", fg="#10293A", muted="#3C5A6E", card="rgba(255,255,255,0.82)",
                  border="rgba(255,255,255,0.95)", accent="#2C7FB8", dark=False, hero_fg="#10293A",
                  hero_muted="#24506E", chip="#24506E"),
    "cost": dict(bg="#F3EAE1", fg="#10293A", muted="#5E4B3E", card="rgba(255,255,255,0.84)",
                 border="rgba(255,255,255,0.95)", accent="#D9822B", dark=False, hero_fg="#10293A",
                 hero_muted="#5A3A22", chip="#6B3A17"),
    "use": dict(bg="#E6E9F0", fg="#10293A", muted="#45536A", card="rgba(255,255,255,0.86)",
                border="rgba(255,255,255,0.95)", accent="#1F5A8A", dark=False, hero_fg="#FFFFFF",
                hero_muted="#EEF1F7", chip="#F4DCC8"),
    "next": dict(bg="#EEF1F4", fg="#10293A", muted="#3F4D63", card="rgba(255,255,255,0.84)",
                 border="rgba(255,255,255,0.95)", accent="#1F5A8A", dark=False, hero_fg="#10293A",
                 hero_muted="#3F4D63", chip="#5A4A6E"),
    "blackout": dict(bg="#0F1E2A", fg="#EAF2F6", muted="#A9BDCB", card="rgba(24,44,61,0.86)",
                     border="rgba(255,255,255,0.10)", accent="#FF9A8B", dark=True, hero_fg="#EAF2F6",
                     hero_muted="#A9BDCB", chip="#FF9A8B"),
}


def css(chapter):
    p = CHAPTERS[chapter]
    dark = p["dark"]
    pill_bg = "rgba(255,255,255,0.08)" if dark else "rgba(255,255,255,0.62)"
    pill_border = "rgba(255,255,255,0.16)" if dark else "rgba(255,255,255,0.92)"
    on_bg, on_fg = ("#EAF2F6", "#0F1E2A") if dark else (NAVY, "#FFFFFF")
    control_bg = "rgba(255,255,255,0.08)" if dark else "#E6EFF3"
    input_bg = "#18303F" if dark else "#FFFFFF"
    shadow = "none" if dark else "0 12px 32px rgba(16,41,58,0.10)"
    # On phones the illustration sits behind the text, so a veil in the sky colour keeps the text readable.
    sky = SKIES[chapter]["stops"][0][1].lstrip("#")
    veil = "rgba({}, {}, {}, 0.6)".format(*(int(sky[i:i + 2], 16) for i in (0, 2, 4)))
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600&display=swap');
:root {{
  --bg: {p['bg']}; --fg: {p['fg']}; --muted: {p['muted']}; --card: {p['card']}; --card-border: {p['border']};
  --accent: {p['accent']}; --pill-bg: {pill_bg}; --pill-border: {pill_border}; --on-bg: {on_bg}; --on-fg: {on_fg};
  --control-bg: {control_bg}; --input-bg: {input_bg}; --shadow: {shadow};
}}
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{ background: var(--bg) !important; }}
body {{ overflow-x: hidden; }}
.stApp, .stApp p, .stApp label, .stApp input, .stApp button, .stApp li, .stApp h1, .stApp h2, .stApp h3,
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stWidgetLabel"], .stApp .hero, .stApp .kpi,
.stApp [data-baseweb="select"] div {{ font-family: 'Outfit', system-ui, sans-serif !important; }}
.stApp {{ color: var(--fg); }}
header[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}
[data-testid="stMainBlockContainer"] {{ max-width: 1384px; padding: 0 32px 56px !important; }}
[data-testid="stVerticalBlock"] {{ gap: 20px; }}

/* Hero: full-width landscape, topbar and title on top of it */
.st-key-hero {{ position: relative; margin-left: calc(50% - 50vw) !important; margin-right: calc(50% - 50vw) !important; width: 100vw !important; max-width: none !important;
  min-height: 580px; overflow: hidden; padding: 22px max(32px, calc(50vw - 660px)) 120px; box-sizing: border-box; gap: 48px; }}
.st-key-hero [data-testid="stElementContainer"]:has(.hero-bg) {{ position: absolute; inset: 0; z-index: 0; margin: 0; }}
.st-key-hero [data-testid="stElementContainer"]:has(.hero-bg) > div, .hero-bg {{ width: 100%; height: 100%; }}
.hero-bg img {{ width: 100%; height: 100%; display: block; object-fit: cover; object-position: center bottom; }}
.st-key-hero > div {{ position: relative; z-index: 1; }}
.st-key-topbar {{ position: relative; z-index: 2; }}
.st-key-brandrow {{ align-items: center; }}
.brand {{ display: flex; align-items: center; gap: 10px; font-size: 20px; font-weight: 600; color: {p['hero_fg']}; }}
.updated {{ font-size: 14px; padding: 9px 14px; border-radius: 999px; background: var(--pill-bg); border: 1px solid var(--pill-border);
  color: {p['fg'] if not dark else p['fg']}; white-space: nowrap; }}
.st-key-brandleft {{ gap: 18px !important; flex-wrap: wrap; }}
.st-key-brandrow {{ flex-wrap: wrap; row-gap: 10px; }}
.st-key-langswitch {{ flex: none; }}
.st-key-langswitch button[data-variant="segmented_control"] {{ min-height: 30px !important; padding: 0 12px !important; margin-right: 2px; }}
.st-key-langswitch button[data-variant="segmented_control"] p {{ font-size: 13px !important; font-weight: 500; letter-spacing: 0.4px; }}
.hero {{ position: relative; z-index: 1; max-width: 680px; display: flex; flex-direction: column; gap: 16px; }}
.hero .chip {{ font-size: 14px; font-weight: 500; letter-spacing: 1.2px; text-transform: uppercase; color: {p['chip']}; }}
.hero h1 {{ margin: 0; padding: 0; font-size: 46px; line-height: 1.12; font-weight: 500; letter-spacing: -1px; color: {p['hero_fg']}; }}
.hero p {{ margin: 0; font-size: 18px; line-height: 1.5; color: {p['hero_muted']}; max-width: 600px; }}
.hero .note {{ align-self: flex-start; font-size: 13px; padding: 6px 12px; border-radius: 999px; background: var(--pill-bg);
  border: 1px solid var(--pill-border); color: {p['hero_muted']}; }}

/* Chapter navigation pills (st.page_link) */
.st-key-nav {{ padding: 5px; border-radius: 999px; background: var(--pill-bg); border: 1px solid var(--pill-border);
  backdrop-filter: blur(10px); gap: 4px !important; width: fit-content; }}
.st-key-nav a {{ border-radius: 999px !important; padding: 7px 15px !important; text-decoration: none !important; }}
.st-key-nav a p, .st-key-nav a span {{ font-size: 14px !important; color: {p['hero_fg'] if chapter != 'use' else NAVY} !important; }}
.st-key-nav a:hover {{ background: rgba(127,127,127,0.12) !important; }}
[class*="st-key-navon"] a {{ background: var(--on-bg) !important; }}
[class*="st-key-navon"] a p, [class*="st-key-navon"] a span {{ color: var(--on-fg) !important; }}
[class*="st-key-navbonus"] a {{ border: 1px dashed {'#FF9A8B' if dark else '#8A5A44'} !important; margin-left: 6px; }}
[class*="st-key-navbonus"] a p {{ color: {'#FF9A8B' if dark else '#7A3E22'} !important; }}
[class*="st-key-navbonuson"] a {{ background: #FF9A8B !important; border-style: solid !important; }}
[class*="st-key-navbonuson"] a p {{ color: #0F1E2A !important; }}

/* Filter bar */
.st-key-filterbar {{ position: relative; z-index: 3; margin-top: -110px; background: var(--card); backdrop-filter: blur(14px);
  border: 1px solid var(--card-border); border-radius: 22px; box-shadow: var(--shadow); padding: 14px 20px 16px; }}
.st-key-filterbar [data-testid="stWidgetLabel"] p {{ font-size: 13px !important; color: var(--muted) !important; }}
.stApp [data-testid="stWidgetLabel"] p {{ color: var(--muted); }}

/* Segmented controls and pills: rounded, chapter colours */
.stApp button[data-variant="segmented_control"], .stApp button[data-variant="pills"] {{
  border-radius: 999px !important; min-height: 36px; background: var(--control-bg) !important;
  border: 1px solid transparent !important; color: var(--fg) !important; margin-right: 4px; }}
.stApp button[data-variant="segmented_control"] p, .stApp button[data-variant="pills"] p {{ font-size: 14px !important; color: var(--fg) !important; }}
.stApp button[data-variant][aria-checked="true"], .stApp button[data-variant][data-selected="true"],
.stApp button[data-variant][aria-pressed="true"] {{ background: var(--on-bg) !important; border-color: var(--on-bg) !important; }}
.stApp button[data-variant][aria-checked="true"] p, .stApp button[data-variant][data-selected="true"] p,
.stApp button[data-variant][aria-pressed="true"] p {{ color: var(--on-fg) !important; }}
.stApp [data-baseweb="select"] > div {{ background: var(--input-bg) !important; border-radius: 999px !important; color: var(--fg) !important; }}
.stApp [data-testid="stSlider"] [data-testid="stSliderThumbValue"], .stApp [data-testid="stSlider"] div {{ color: var(--fg); }}

/* Cards: same height within a row */
[data-testid="stHorizontalBlock"]:has([class*="st-key-card-"]), [data-testid="stHorizontalBlock"]:has([class*="st-key-dcard-"]) {{ align-items: stretch; }}
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] {{ height: 100%; }}
[data-testid="stColumn"] [data-testid="stLayoutWrapper"]:has(> [class*="st-key-card-"]),
[data-testid="stColumn"] [data-testid="stLayoutWrapper"]:has(> [class*="st-key-dcard-"]) {{ height: 100%; }}
[class*="st-key-card-story"] [data-testid="stElementContainer"]:has([data-testid="stPageLink"]) {{ margin-top: auto; }}
[class*="st-key-card-story"] a[data-testid="stPageLink-NavLink"] {{ border: 1px solid #2C7FB8; border-radius: 999px !important;
  padding: 6px 14px !important; width: fit-content; background: transparent !important; }}
[class*="st-key-card-story"] a[data-testid="stPageLink-NavLink"] p,
[class*="st-key-card-story"] a[data-testid="stPageLink-NavLink"] span {{ color: #1F5A8A !important; font-weight: 500; }}
[class*="st-key-card-story"] a[data-testid="stPageLink-NavLink"]:hover {{ background: #2C7FB8 !important; }}
[class*="st-key-card-story"] a[data-testid="stPageLink-NavLink"]:hover p,
[class*="st-key-card-story"] a[data-testid="stPageLink-NavLink"]:hover span {{ color: #FFFFFF !important; }}
/* Cards */
[class*="st-key-card-"] {{ background: var(--card); backdrop-filter: blur(14px); border: 1px solid var(--card-border);
  border-radius: 22px; box-shadow: var(--shadow); padding: 22px 24px; height: 100%; }}
[class*="st-key-dcard-"] {{ background: {'#132B3B' if dark else NAVY}; border-radius: 22px; padding: 24px; height: 100%; }}
[class*="st-key-dcard-"] * {{ color: #FFFFFF; }}
.card-title {{ margin: 0; font-size: 20px; font-weight: 500; color: var(--fg); }}
.card-note {{ margin: 0; font-size: 14px; color: var(--muted); line-height: 1.45; }}
.kpi {{ display: flex; flex-direction: column; gap: 6px; }}
.kpi-label {{ font-size: 15px; color: var(--muted); }}
.kpi-value {{ font-size: 42px; font-weight: 500; line-height: 1.05; color: var(--fg); }}
.kpi-value small {{ font-size: 18px; font-weight: 400; color: var(--muted); }}
.kpi-note {{ font-size: 14px; color: var(--muted); }}
[class*="st-key-dcard-"] .kpi-label, [class*="st-key-dcard-"] .kpi-note, [class*="st-key-dcard-"] .kpi-value small {{ color: #B9D3E2; }}
[class*="st-key-dcard-"] .kpi-value {{ color: #FFFFFF; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 14px; font-size: 13px; color: var(--muted); }}
.legend span {{ display: inline-flex; align-items: center; gap: 6px; }}
.dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
.bars {{ display: grid; gap: 10px 12px; align-items: center; font-size: 14px; color: var(--fg); }}
.bar-track {{ height: 12px; border-radius: 6px; background: {'rgba(255,255,255,0.08)' if dark else '#E6EDF1'}; overflow: hidden; }}
.bar-fill {{ height: 12px; border-radius: 6px; }}
.story a {{ text-decoration: none; }}
.story-card {{ display: flex; flex-direction: column; gap: 6px; padding: 18px; border-radius: 18px;
  background: {'rgba(255,255,255,0.06)' if dark else 'rgba(255,255,255,0.7)'}; border: 1px solid var(--card-border); height: 100%; }}
.timeline li {{ display: flex; gap: 14px; }}
.empty {{ font-size: 15px; color: var(--muted); padding: 18px; border-radius: 14px; border: 1px dashed var(--muted); }}
.source-note {{ font-size: 13px; color: var(--muted); text-align: center; line-height: 1.45; }}
.source-note a {{ color: {'#9CC8E8' if dark else '#1F5A8A'}; }}
.badge {{ display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px; border-radius: 999px;
  background: {'rgba(255,255,255,0.08)' if dark else '#FFF4E0'}; color: {'#F4DCC8' if dark else '#6B4A12'}; font-size: 13px; }}

/* Segmented controls and pills wrap instead of scrolling sideways on narrow screens */
[data-testid="stButtonGroup"] > div {{ flex-wrap: wrap !important; row-gap: 6px; overflow: visible !important; }}

/* Footer navigation */
.st-key-footer {{ align-items: center; }}
.st-key-footer > .stElementContainer {{ flex: 1 1 0 !important; min-width: 220px; }}
.st-key-footer [class*="st-key-foot"] a {{ border-radius: 999px !important; padding: 10px 18px !important; background: var(--pill-bg) !important;
  border: 1px solid var(--pill-border) !important; }}
.st-key-footer [class*="st-key-footprev"] a p {{ color: var(--fg) !important; }}
.st-key-footer [class*="st-key-footnext"] a {{ background: var(--on-bg) !important; }}
.st-key-footer [class*="st-key-footnext"] a p {{ color: var(--on-fg) !important; }}

.card-note a, [class*="st-key-dcard-"] a {{ color: {'#9FD3FF' if dark else '#1F5A8A'}; }}
.source-note a {{ color: inherit; text-decoration: underline; text-underline-offset: 2px; }}

@media (prefers-reduced-motion: reduce) {{ .spin, .lit, .star, .sun {{ animation: none !important; }} }}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}
@keyframes twinkle {{ 0%, 100% {{ opacity: .9; }} 50% {{ opacity: .35; }} }}
@keyframes glow {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: .55; }} }}
.spin {{ animation: spin 10s linear infinite; }} .spin.s2 {{ animation-duration: 13s; }} .spin.s3 {{ animation-duration: 8s; }}
.star {{ animation: twinkle 4s ease-in-out infinite; }} .lit {{ animation: glow 5s ease-in-out infinite; }}
@media (max-width: 760px) {{
  .hero h1 {{ font-size: 34px; }} .st-key-hero {{ min-height: 520px; }}
  .st-key-nav {{ border-radius: 22px !important; }}
  .hero-bg {{ position: relative; }}
  .hero-bg::after {{ content: ""; position: absolute; inset: 0; background: {veil}; }}
}}
</style>
"""
