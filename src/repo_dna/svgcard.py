"""Render the shareable SVG DNA card.

One card per repo: dark, gradient, self-contained — designed to be
committed into a project's README, where every view advertises the tool.
"""

from __future__ import annotations

import math

W, H = 840, 540
PAD = 36
CW = W - 2 * PAD  # content width: 768

BG_TOP = "#101725"
BG_BOTTOM = "#0a0e16"
PANEL = "#161b22"
BORDER = "#21262d"
TEXT = "#e6edf3"
MUTED = "#8b949e"
OTHER = "#30363d"

FONT = "'Segoe UI', -apple-system, Roboto, Helvetica, Arial, sans-serif"


def _esc(text) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _fmt_int(n: int) -> str:
    return f"{n:,}"


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit - 1] + "…"


def _age_label(days: int) -> str:
    if days < 14:
        return f"{days} days"
    if days < 90:
        return f"{days // 7} weeks"
    if days < 730:
        return f"{round(days / 30.4)} months"
    return f"{days / 365:.1f} yrs"


def _text(x, y, content, size, fill, anchor="start", weight=None, spacing=None, opacity=None) -> str:
    attrs = [f'x="{x}"', f'y="{y}"', f'font-size="{size}"', f'fill="{fill}"']
    if anchor != "start":
        attrs.append(f'text-anchor="{anchor}"')
    if weight:
        attrs.append(f'font-weight="{weight}"')
    if spacing:
        attrs.append(f'letter-spacing="{spacing}"')
    if opacity:
        attrs.append(f'opacity="{opacity}"')
    return '<text ' + " ".join(attrs) + f'>{content}</text>'


def _defs() -> str:
    return (
        '<defs>'
        '<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG_BOTTOM}"/>'
        '</linearGradient>'
        '<linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#a78bfa"/><stop offset="0.5" stop-color="#38bdf8"/>'
        '<stop offset="1" stop-color="#34d399"/>'
        '</linearGradient>'
        '<linearGradient id="spark" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#38bdf8" stop-opacity="0.30"/>'
        '<stop offset="1" stop-color="#38bdf8" stop-opacity="0"/>'
        '</linearGradient>'
        '</defs>'
    )


def _helix() -> str:
    """A faint DNA double helix stretched diagonally behind the content."""
    amp = 110.0
    mid = H * 0.42
    steps = 44
    pts1, pts2, rungs = [], [], []
    for i in range(steps + 1):
        x = PAD + CW * i / steps
        t = i / steps * math.pi * 3
        y1 = mid + amp * math.sin(t)
        y2 = mid + amp * math.sin(t + math.pi)
        pts1.append(f"{x:.1f},{y1:.1f}")
        pts2.append(f"{x:.1f},{y2:.1f}")
        if i % 4 == 0:
            rungs.append(f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}"/>')
    d1 = "M" + " L".join(pts1)
    d2 = "M" + " L".join(pts2)
    return (
        '<g stroke="#58a6ff" stroke-width="1.5" fill="none" opacity="0.05">'
        f'<path d="{d1}"/><path d="{d2}"/>' + "".join(rungs) + "</g>"
    )


def _score_ring(score: int, cx: float, cy: float, r: float = 46) -> str:
    frac = max(0.0, min(1.0, score / 100))
    circ = 2 * math.pi * r
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{BORDER}" stroke-width="9"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#accent)" stroke-width="9"'
        f' stroke-linecap="round" stroke-dasharray="{frac * circ:.1f} {circ:.1f}"'
        f' transform="rotate(-90 {cx} {cy})"/>'
        + _text(cx, cy + 9, str(score), 26, "url(#accent)", anchor="middle", weight=800)
        + _text(cx, cy + r + 18, "HELIX SCORE", 8, MUTED, anchor="middle", spacing=1.5)
    )


def _sparkline(weeks, x, top, width, height) -> str:
    base = top + height
    vmax = max(weeks) if weeks else 0
    n = len(weeks)
    axis = f'<line x1="{x}" y1="{base}" x2="{x + width}" y2="{base}" stroke="{BORDER}" stroke-width="1"/>'
    if n < 2 or vmax == 0:
        return axis + _text(x + width, top - 6, "not enough history yet", 9, MUTED, anchor="end")
    pts = []
    for i, v in enumerate(weeks):
        px = x + width * i / (n - 1)
        py = base - (v / vmax) * height
        pts.append(f"{px:.1f},{py:.1f}")
    poly = " ".join(pts)
    area = "M" + pts[0] + " L" + " L".join(pts[1:]) + f" L{x + width},{base} L{x},{base} Z"
    last_x, last_y = pts[-1].split(",")
    return (
        f'<path d="{area}" fill="url(#spark)"/>'
        f'<polyline points="{poly}" fill="none" stroke="url(#accent)" stroke-width="2.5"'
        ' stroke-linejoin="round" stroke-linecap="round"/>'
        + axis
        + f'<circle cx="{last_x}" cy="{last_y}" r="3" fill="#34d399"/>'
    )


def render_svg(report: dict) -> str:
    name = _esc(_truncate(report["repo"]["name"], 34))
    total = report["commits"]["total"]
    age_days = report["commits"]["age_days"]
    score = report["helix_score"]["score"]
    langs = report["languages"]
    act = report["activity"]

    s = []
    s.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"'
        f' viewBox="0 0 {W} {H}" font-family="{FONT}">'
    )
    s.append(_defs())
    s.append(f'<rect width="{W}" height="{H}" rx="18" fill="url(#bg)"/>')
    s.append(f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="{BORDER}"/>')
    s.append(_helix())

    # header ---------------------------------------------------------------
    s.append(_text(PAD, 66, name, 24, TEXT, weight=700))
    subtitle = f"REPO DNA · GENERATED {_esc(report['generated_at'][:10])} · V{_esc(report['tool_version'])}"
    s.append(_text(PAD, 88, subtitle, 10, MUTED, spacing=2.5))
    s.append(_score_ring(score, 760, 84))

    # stat chips -------------------------------------------------------------
    n_authors = len(report["authors"])
    chips = [
        (_fmt_int(total), "COMMITS"),
        (str(n_authors), "CONTRIBUTOR" if n_authors == 1 else "CONTRIBUTORS"),
        (_age_label(age_days), "AGE"),
        (_fmt_int(report["totals"]["lines"]), "LINES OF CODE"),
    ]
    for i, (value, label) in enumerate(chips):
        x = PAD + i * 194
        value, label = _esc(value), _esc(label)
        s.append(f'<rect x="{x}" y="170" width="180" height="56" rx="10" fill="{PANEL}" stroke="{BORDER}"/>')
        s.append(_text(x + 16, 204, value, 20, TEXT, weight=700))
        s.append(_text(x + 16, 217, label, 8.5, MUTED, spacing=1.2))

    # languages --------------------------------------------------------------
    s.append(_text(PAD, 266, "LANGUAGES", 10, MUTED, spacing=2.5))
    if langs:
        top = langs[:7]
        bar_y = 278
        s.append(f'<clipPath id="langclip"><rect x="{PAD}" y="{bar_y}" width="{CW}" height="14" rx="7"/></clipPath>')
        s.append('<g clip-path="url(#langclip)">')
        x = float(PAD)
        for lang in top:
            color = lang["color"]
            w = CW * lang["share"] / 100
            if w <= 0:
                continue
            s.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{w:.1f}" height="14" fill="{color}"/>')
            x += w
        if x < PAD + CW:
            s.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{PAD + CW - x:.1f}" height="14" fill="{OTHER}"/>')
        s.append("</g>")
        for i, lang in enumerate(top[:8]):
            color = lang["color"]
            lname = _esc(_truncate(lang["name"], 18))
            lshare = lang["share"]
            lx = PAD + (i % 2) * 388
            ly = 318 + (i // 2) * 20
            s.append(f'<circle cx="{lx + 5}" cy="{ly - 4}" r="4.5" fill="{color}"/>')
            s.append(_text(lx + 17, ly, f"{lname} · {lshare:.1f}%", 11.5, TEXT))
    else:
        s.append(_text(PAD, 318, "no trackable source files", 11, MUTED))

    # activity ----------------------------------------------------------------
    s.append(_text(PAD, 414, "COMMIT ACTIVITY · LAST 52 WEEKS", 10, MUTED, spacing=2.5))
    s.append(_sparkline(report["commits"]["weekly_last_52"], PAD, 424, CW, 34))

    # fun stats -----------------------------------------------------------------
    fun = [
        ("🦉", f"{act['night_ratio'] * 100:.0f}%", "NIGHT OWL"),
        ("🎉", f"{act['weekend_ratio'] * 100:.0f}%", "WEEKEND WARRIOR"),
        ("🌪️", f"{report['chaos_coefficient']:.2f}", "CHAOS COEFF."),
        ("🚌", str(report["bus_factor"]), "BUS FACTOR"),
    ]
    for i, (icon, value, label) in enumerate(fun):
        x = PAD + i * 194
        s.append(_text(x, 488, f"{icon} {value}", 14, TEXT, weight=700))
        s.append(_text(x, 504, label, 8, MUTED, spacing=1.2))

    # footer ----------------------------------------------------------------
    s.append(
        _text(W / 2, 528, "generated by repo-dna · pip install repo-dna", 9.5, MUTED, anchor="middle", opacity=0.9)
    )
    s.append("</svg>")
    return "\n".join(s)
