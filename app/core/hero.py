"""Illustrated landscapes for the top of each chapter (SVG, animated with CSS)."""
import base64

SKIES = {
    "now": dict(stops=[("0", "#8EC1DE"), ("0.7", "#DDEEF5"), ("1", "#E4EEF2")], sun=(1150, 190, "#FFF2C2"),
                far="#B4D2C8", near="#8DB8A8", tower="#F7FAFB", blade="#FFFFFF", panels=True),
    "shift": dict(stops=[("0", "#6FAFD8"), ("0.7", "#D6EBF3"), ("1", "#E2EEF0")], sun=(860, 70, "#FFF5CC"),
                  far="#A8CDB9", near="#7FB197", tower="#F7FAFB", blade="#FFFFFF", panels=True),
    "cost": dict(stops=[("0", "#D9845E"), ("0.45", "#F0B486"), ("0.8", "#F7DCC0"), ("1", "#F3EAE1")],
                 sun=(1120, 350, "#FFE2B5"), far="#D2A98C", near="#B98B6C", tower="#FFF3E8", blade="#FFF7EF",
                 panels=False),
    "use": dict(stops=[("0", "#3E5B86"), ("0.5", "#8E88A8"), ("0.8", "#D9C3C4"), ("1", "#E6E9F0")], sun=None,
                far="#7D7F9A", near="#5E6280", tower=None, blade=None, panels=False, city=True),
    "next": dict(stops=[("0", "#93AFD4"), ("0.55", "#E9CDC0"), ("0.8", "#F7E2CF"), ("1", "#EEF1F4")],
                 sun=(1000, 380, "#FFE4C2"), far="#B9C6CE", near="#98A9B4", tower="#F5F8FA", blade="#FFFFFF",
                 panels=True),
    "blackout": dict(stops=[("0", "#08131D"), ("0.75", "#1D3448"), ("1", "#0F1E2A")], sun=None, moon=True,
                     far="#1A2C3B", near="#132332", tower="#6E7F8F", blade="#7E8E9D", panels=False,
                     dark_city=True),
}

TURBINES = [(1010, 450, 240, ""), (1170, 445, 200, "s2"), (1300, 450, 160, "s3")]


def _turbine(x, base, height, cls, tower, blade):
    hub = base - height
    length = int(height * 0.5)
    blade_path = f"M{x},{hub} L{x - 5},{hub - 14} L{x},{hub - length} L{x + 4},{hub - 14} Z"
    return (
        f'<polygon points="{x - 3},{base} {x + 3},{base} {x + 1.5},{hub} {x - 1.5},{hub}" fill="{tower}"></polygon>'
        f'<g class="spin {cls}" style="transform-origin: {x}px {hub}px" fill="{blade}">'
        f'<path d="{blade_path}"></path>'
        f'<path d="{blade_path}" transform="rotate(120 {x} {hub})"></path>'
        f'<path d="{blade_path}" transform="rotate(240 {x} {hub})"></path></g>'
    )


def landscape(chapter):
    s = SKIES[chapter]
    gid = f"sky-{chapter}"
    stops = "".join(f'<stop offset="{o}" stop-color="{c}"></stop>' for o, c in s["stops"])
    parts = [
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">{stops}</linearGradient></defs>',
        f'<rect width="1440" height="560" fill="url(#{gid})"></rect>',
    ]
    if s.get("sun"):
        x, y, color = s["sun"]
        parts.append(f'<circle cx="{x}" cy="{y}" r="110" fill="{color}" opacity="0.35"></circle>'
                     f'<circle cx="{x}" cy="{y}" r="48" fill="{color}"></circle>')
    if s.get("moon"):
        stars = [(720, 60), (820, 110), (940, 50), (1060, 90), (1180, 40), (1330, 80), (640, 130), (560, 70)]
        parts.append("".join(
            f'<circle class="star" cx="{x}" cy="{y}" r="1.4" fill="#FFFFFF" style="animation-delay: {i * 0.6:.1f}s"></circle>'
            for i, (x, y) in enumerate(stars)))
        parts.append('<circle cx="1240" cy="110" r="34" fill="#E8EEF2" opacity="0.9"></circle>'
                     '<circle cx="1254" cy="100" r="30" fill="#132535"></circle>')
    parts.append(f'<path d="M0,430 C240,390 420,410 640,400 C860,390 1100,368 1440,398 L1440,560 L0,560 Z" fill="{s["far"]}"></path>')
    if s.get("city") or s.get("dark_city"):
        window = "#1E3346" if s.get("dark_city") else "#FFD68A"
        cls = "" if s.get("dark_city") else ' class="lit"'
        blocks = [(60, 390, 70), (140, 350, 60), (210, 410, 90), (310, 370, 55), (375, 420, 80)] if s.get("dark_city") else \
                 [(760, 330, 60), (830, 280, 54), (894, 350, 80), (984, 300, 46), (1040, 260, 70), (1120, 340, 64),
                  (1194, 310, 50), (1254, 360, 90), (1354, 330, 60)]
        building = "#122230" if s.get("dark_city") else "#2E3A55"
        parts.append("".join(f'<rect x="{x}" y="{y}" width="{w}" height="{520 - y}" fill="{building}"></rect>'
                             for x, y, w in blocks))
        lights = "".join(f'<rect x="{x + 10 + (i % 2) * 22}" y="{y + 16 + (i % 3) * 30}" width="9" height="9"></rect>'
                         for i, (x, y, w) in enumerate(blocks * 2))
        parts.append(f'<g fill="{window}"{cls}>{lights}</g>')
    if s.get("tower"):
        parts.append("".join(_turbine(x, b, h, c, s["tower"], s["blade"]) for x, b, h, c in TURBINES))
    parts.append(f'<path d="M0,500 C300,470 560,485 820,476 C1080,467 1260,480 1440,470 L1440,560 L0,560 Z" fill="{s["near"]}"></path>')
    if s.get("panels"):
        panels = "".join(
            f'<polygon points="{x},{496 - i} {x + 40},{496 - i} {x + 50},{480 - i} {x + 10},{480 - i}"></polygon>'
            for i, x in enumerate(range(520, 830, 52)))
        parts.append(f'<g fill="#2F4B63" stroke="#86ABC4" stroke-width="1">{panels}</g>')
    if s.get("dark_city"):
        parts.append('<g stroke="#55687A" stroke-width="2" fill="none" transform="translate(70 0)"><path d="M760,490 L790,330 L820,490 '
                     'M770,440 L810,440 M778,390 L802,390 M765,350 L815,350"></path>'
                     '<path d="M765,350 C735,358 700,368 660,378 M815,350 C880,360 920,370 990,380"></path></g>')
    if s.get("city"):
        parts.append('<g transform="translate(700 410)"><rect x="0" y="0" width="34" height="72" rx="6" fill="#E9EEF5"></rect>'
                     '<rect x="7" y="10" width="20" height="14" rx="3" fill="#7FD1A8"></rect>'
                     '<path d="M34,30 C54,30 54,60 70,64" fill="none" stroke="#E9EEF5" stroke-width="4"></path></g>'
                     '<g transform="translate(760 450)" fill="#E9EEF5"><path d="M0,30 L10,12 C14,6 20,4 28,4 L62,4 '
                     'C70,4 76,8 80,14 L92,30 L92,44 L0,44 Z"></path><circle cx="22" cy="46" r="9" fill="#2E3A55"></circle>'
                     '<circle cx="72" cy="46" r="9" fill="#2E3A55"></circle></g>')
    body = "".join(parts)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 560" preserveAspectRatio="xMidYMax slice">'
           f'<style>{SVG_ANIMATIONS}</style>{body}</svg>')
    return f'<div class="hero-bg">{svg_img(svg, "")}</div>'


SVG_ANIMATIONS = (
    "@keyframes spin{to{transform:rotate(360deg)}}.spin{animation:spin 10s linear infinite}"
    ".spin.s2{animation-duration:13s}.spin.s3{animation-duration:8s}"
    "@keyframes twinkle{0%,100%{opacity:.9}50%{opacity:.35}}.star{animation:twinkle 4s ease-in-out infinite}"
    "@keyframes glow{0%,100%{opacity:1}50%{opacity:.55}}.lit{animation:glow 5s ease-in-out infinite}"
    "@media (prefers-reduced-motion: reduce){.spin,.star,.lit{animation:none}}"
)


def svg_img(svg, alt, style=""):
    """Streamlit strips inline <svg> from st.html, so SVG goes in as an image (animations still run)."""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    role = f'alt="{alt}"' if alt else 'alt="" aria-hidden="true"'
    return f'<img {role} src="data:image/svg+xml;base64,{encoded}" style="{style}">'

