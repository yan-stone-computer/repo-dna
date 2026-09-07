"""Render a DNA report as an ANSI terminal report."""

from __future__ import annotations

import os

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RED = "\033[31m"

# 5-step heat scale for the weekday × hour grid (dark → bright green).
HEAT = ["\033[38;5;236m", "\033[38;5;22m", "\033[38;5;28m", "\033[38;5;34m", "\033[38;5;46m"]
HEAT_CHARS = ["·", "░", "▒", "▓", "█"]
SPARK = "▁▂▃▄▅▆▇█"
RULE = "─" * 66
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _c(on: bool, code: str, text: str) -> str:
    return f"{code}{text}{RESET}" if on else text


def _bar(on: bool, frac: float, width: int = 20, code: str = CYAN) -> str:
    frac = max(0.0, min(1.0, frac))
    n = round(frac * width)
    return _c(on, code, "█" * n) + _c(on, DIM, "·" * (width - n))


def _score_code(score: int) -> str:
    if score >= 75:
        return GREEN
    if score >= 50:
        return CYAN
    if score >= 30:
        return YELLOW
    return RED


def _pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def _spark(values, on: bool) -> str:
    peak = max(values) if values else 0
    if not values or peak == 0:
        return "·" * len(values)
    return "".join(SPARK[min(len(SPARK) - 1, v * (len(SPARK) - 1) // peak)] for v in values)


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit - 1] + "…"


def render_terminal(report: dict, color: bool = True) -> str:
    on = color and os.environ.get("NO_COLOR") is None
    out = []

    c = report["commits"]
    t = report["totals"]
    act = report["activity"]
    msg = report["messages"]
    total = c["total"]

    out.append(_c(on, BOLD, "  🧬 REPO DNA") + _c(on, DIM, "  ·  ") + _c(on, MAGENTA, report["repo"]["name"]))
    out.append(_c(on, DIM, RULE))
    out.append(
        f"  age {c['age_days']} days · {t['files']} files · {t['lines']:,} lines · "
        f"{len(report['languages'])} languages · first commit {c['first']}"
    )
    out.append("")
    out.append(_c(on, BOLD, "  COMMITS") + _c(on, DIM, f"  {total:,} total · {c['avg_per_day']}/day avg"))
    out.append("  " + _spark(c["weekly_last_52"][-26:], on) + _c(on, DIM, "  weekly, last 26 weeks"))
    out.append("")

    out.append(_c(on, BOLD, "  LANGUAGES"))
    for lang in report["languages"][:6]:
        out.append(
            f"  {lang['name']:<14}{_bar(on, lang['share'] / 100, 22)}"
            f"  {lang['share']:5.1f}%  {lang['lines']:>7,} lines"
        )
    rest = report["languages"][6:]
    if rest:
        lines = sum(l["lines"] for l in rest)
        out.append(_c(on, DIM, f"  + {len(rest)} more ({lines:,} lines)"))
    out.append("")

    out.append(_c(on, BOLD, "  CONTRIBUTORS") + _c(on, DIM, f"  bus factor {report['bus_factor']}"))
    for a in report["authors"][:5]:
        share = a["commits"] / total
        out.append(
            f"  {a['name']:<14}{_bar(on, share, 22, MAGENTA)}"
            f"  {a['commits']:>5,} commits ({_pct(share)})"
        )
    more = len(report["authors"]) - 5
    if more > 0:
        out.append(_c(on, DIM, f"  + {more} more"))
    out.append("")

    out.append(_c(on, BOLD, "  ACTIVITY") + _c(on, DIM, "  commits by weekday × hour (local time)"))
    grid = act["grid"]
    peak = max(max(row) for row in grid) or 1
    for i, row in enumerate(grid):
        cells = []
        for v in row:
            level = 0 if v == 0 else 1 + round(v / peak * 3)
            cells.append(_c(on, HEAT[level], "██") if on else HEAT_CHARS[level] * 2)
        out.append(f"  {DOW[i]}  " + "".join(cells))
    ruler = "".join(f"{h:02d}" if h % 3 == 0 else "  " for h in range(24))
    out.append("      " + _c(on, DIM, ruler))
    out.append("")

    hot = _truncate(report["hot_files"][0]["path"], 36) if report["hot_files"] else "—"
    out.append(_c(on, BOLD, "  FUN STATS"))
    out.append(f"  🦉 Night Owl Index    {_pct(act['night_ratio']):>4}  commits between 00:00–06:00")
    out.append(f"  🎉 Weekend Warrior    {_pct(act['weekend_ratio']):>4}  commits on Sat/Sun")
    out.append(f"  🌪️ Chaos Coefficient  {report['chaos_coefficient']:>4.2f}  deletions per insertion")
    out.append(f"  📅 Longest Streak     {c['longest_streak_days']:>4}  consecutive days")
    out.append(f"  💬 Message Style      {_pct(msg['conventional_ratio']):>4}  conventional · avg {msg['avg_length']:.0f} chars")
    out.append(f"  🔥 Hot File           {hot}")
    out.append("")

    score = report["helix_score"]
    code = _score_code(score["score"])
    out.append(_c(on, DIM, RULE))
    out.append(
        "  🧬 HELIX SCORE  "
        + _c(on, BOLD + code, f"{score['score']:>3}/100")
        + _c(on, DIM, "  ·  ")
        + _c(on, code, score["verdict"])
    )
    out.append("  " + _bar(on, score["score"] / 100, 40, code))
    out.append("")
    out.append(_c(on, DIM, f"  generated {report['generated_at']} · repo-dna v{report['tool_version']}"))
    return "\n".join(out)
