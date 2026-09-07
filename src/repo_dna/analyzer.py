"""Turn a git repository into a DNA profile.

Everything is computed from the local ``.git`` directory — no network
access, no telemetry, no third-party dependencies.
"""

from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

from . import __version__
from .languages import classify_path, count_lines

DAY = 86400
WEEK = 7 * DAY

# Records are separated by \x1e and fields by \x1f so that author names,
# emails and commit subjects can never break the parser.
_RECORD = "\x1e"
_UNIT = "\x1f"

CONVENTIONAL_RE = re.compile(
    r"^(?:[^\w\s]{1,4}\s*)?(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert)(\(|:|!)",
    re.IGNORECASE,
)

HOT_FILE_LIMIT = 5
LANG_LIMIT = 8
MAX_FILE_BYTES = 1_000_000


class DNAError(Exception):
    """Raised when a path cannot be scanned."""


def verdict(score: int) -> str:
    """A fun label for a Helix Score."""
    if score >= 90:
        return "Mythic Organism 🦄"
    if score >= 75:
        return "Peak Evolution 🧬"
    if score >= 60:
        return "Healthy Genome 💪"
    if score >= 40:
        return "Hybrid Vigor 🌱"
    if score >= 20:
        return "Lab Experiment 🧪"
    return "Primordial Soup 🍲"


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if proc.returncode != 0:
        message = proc.stderr.decode("utf-8", "replace").strip()
        raise DNAError(message or "git failed")
    return proc.stdout.decode("utf-8", "replace")


def _parse_log(raw: str) -> list:
    commits = []
    for record in raw.split(_RECORD):
        record = record.strip()
        if not record:
            continue
        parts = record.split(_UNIT)
        commits.append({
            "hash": parts[0],
            "ts": int(parts[1]),
            "author": parts[2] or parts[3],
            "email": parts[3],
            "subject": parts[4] if len(parts) > 4 else "",
        })
    return commits


def _parse_numstat(raw: str):
    for record in raw.split(_RECORD):
        lines = [ln for ln in record.split("\n") if ln.strip()]
        if not lines:
            continue
        stats = []
        for line in lines[1:]:
            adds, _, rest = line.partition("\t")
            dels, _, path = rest.partition("\t")
            if adds == "-" or dels == "-":
                continue  # binary file
            stats.append((int(adds), int(dels), path.strip()))
        yield stats


def _is_emoji(subject: str) -> bool:
    if not subject:
        return False
    cp = ord(subject[0])
    return cp >= 0x1F300 or 0x2600 <= cp <= 0x27BF


def _helix_score(*, total: int, authors: int, languages: int,
                 distinct_hours: int, streak: int, care_ratio: float,
                 age_days: int) -> int:
    """A reproducible 0-100 vibe score. The weights are arbitrary but public."""
    parts = [
        min(total / 200, 1) * 20,        # activity
        min(authors / 3, 1) * 15,        # collaboration
        min(languages / 4, 1) * 15,      # diversity
        distinct_hours / 24 * 15,        # rhythm
        min(streak / 14, 1) * 15,        # consistency
        care_ratio * 10,                 # discipline
        min(age_days / 365, 1) * 10,     # maturity
    ]
    return round(sum(parts))


def analyze(path=".") -> dict:
    """Scan the git repository at ``path`` and return its DNA report."""
    repo = Path(path).resolve()
    if not repo.exists():
        raise DNAError(f"path does not exist: {repo}")
    try:
        _git(repo, "rev-parse", "--git-dir")
    except DNAError:
        raise DNAError(f"'{repo.name}' is not a git repository (no .git found)") from None

    commits = _parse_log(
        _git(repo, "log", f"--format={_RECORD}%H{_UNIT}%at{_UNIT}%an{_UNIT}%ae{_UNIT}%s")
    )
    if not commits:
        raise DNAError("this repository has no commits yet")
    total = len(commits)

    # --- contributors -----------------------------------------------------
    by_email = {}
    for c in commits:
        entry = by_email.setdefault(c["email"], {"name": c["author"], "commits": 0})
        entry["commits"] += 1
    authors = sorted(
        ({"name": v["name"], "email": email, "commits": v["commits"]}
         for email, v in by_email.items()),
        key=lambda a: a["commits"],
        reverse=True,
    )
    acc = 0
    bus_factor = 0
    for a in authors:
        acc += a["commits"]
        bus_factor += 1
        if acc * 2 >= total:
            break
    bus_factor = max(bus_factor, 1)

    # --- time patterns ----------------------------------------------------
    hour_hist = [0] * 24
    dow_hist = [0] * 7
    grid = [[0] * 24 for _ in range(7)]
    weekly = {}
    days = set()
    for c in commits:
        dt = datetime.fromtimestamp(c["ts"])
        hour_hist[dt.hour] += 1
        dow_hist[dt.weekday()] += 1
        grid[dt.weekday()][dt.hour] += 1
        week = c["ts"] // WEEK
        weekly[week] = weekly.get(week, 0) + 1
        days.add(dt.date())

    longest = current = 0
    prev = None
    for day in sorted(days):
        current = current + 1 if prev is not None and (day - prev).days == 1 else 1
        longest = max(longest, current)
        prev = day

    last_week = max(weekly)
    weeks = [weekly.get(w, 0) for w in range(last_week - 51, last_week + 1)]

    weekend_ratio = (dow_hist[5] + dow_hist[6]) / total
    night_ratio = sum(hour_hist[0:6]) / total
    distinct_hours = sum(1 for v in hour_hist if v)

    # --- churn --------------------------------------------------------------
    total_adds = total_dels = 0
    churn = {}
    for stats in _parse_numstat(_git(repo, "log", "--numstat", f"--format={_RECORD}%H")):
        for adds, dels, fpath in stats:
            total_adds += adds
            total_dels += dels
            churn[fpath] = churn.get(fpath, 0) + adds + dels
    hot_files = sorted(
        ({"path": p, "churn": v} for p, v in churn.items()),
        key=lambda f: f["churn"],
        reverse=True,
    )[:HOT_FILE_LIMIT]

    # --- languages ----------------------------------------------------------
    files = [f for f in _git(repo, "ls-files", "-z").split("\0") if f]
    langs = {}
    binary_files = 0
    for rel in files:
        fp = repo / rel
        try:
            if fp.stat().st_size > MAX_FILE_BYTES:
                continue
            data = fp.read_bytes()
        except OSError:
            continue
        if b"\0" in data[:8192]:
            binary_files += 1
            continue
        lang, color = classify_path(rel)
        if lang is None:
            continue
        entry = langs.setdefault(lang, {"lines": 0, "files": 0, "color": color})
        entry["lines"] += count_lines(data)
        entry["files"] += 1
    language_list = sorted(
        ({"name": name, "lines": v["lines"], "files": v["files"], "color": v["color"]}
         for name, v in langs.items()),
        key=lambda l: l["lines"],
        reverse=True,
    )
    total_lines = sum(l["lines"] for l in language_list)
    for l in language_list:
        l["share"] = round(l["lines"] / total_lines * 100, 1) if total_lines else 0.0

    # --- commit messages ----------------------------------------------------
    subjects = [c["subject"] for c in commits]
    conventional = sum(1 for s in subjects if CONVENTIONAL_RE.match(s))
    emojis = sum(1 for s in subjects if _is_emoji(s))

    first_ts = min(c["ts"] for c in commits)
    last_ts = max(c["ts"] for c in commits)
    age_days = max(1, (last_ts - first_ts) // DAY + 1)
    chaos = round(total_dels / total_adds, 2) if total_adds else 0.0

    score = _helix_score(
        total=total,
        authors=len(authors),
        languages=len(language_list),
        distinct_hours=distinct_hours,
        streak=longest,
        care_ratio=conventional / total,
        age_days=age_days,
    )

    return {
        "schema": 1,
        "tool_version": __version__,
        "generated_at": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z"),
        "repo": {"name": repo.name, "path": str(repo)},
        "commits": {
            "total": total,
            "first": datetime.fromtimestamp(first_ts).strftime("%Y-%m-%d"),
            "last": datetime.fromtimestamp(last_ts).strftime("%Y-%m-%d"),
            "age_days": age_days,
            "avg_per_day": round(total / age_days, 2),
            "longest_streak_days": longest,
            "weekly_last_52": weeks,
        },
        "authors": authors,
        "bus_factor": bus_factor,
        "languages": language_list,
        "totals": {
            "files": len(files),
            "lines": total_lines,
            "binary_files": binary_files,
            "insertions": total_adds,
            "deletions": total_dels,
            "churn_per_commit": round((total_adds + total_dels) / total, 1),
        },
        "activity": {
            "hour": hour_hist,
            "weekday": dow_hist,
            "grid": grid,
            "weekend_ratio": round(weekend_ratio, 3),
            "night_ratio": round(night_ratio, 3),
            "distinct_hours": distinct_hours,
        },
        "chaos_coefficient": chaos,
        "hot_files": hot_files,
        "messages": {
            "avg_length": round(sum(len(s) for s in subjects) / total, 1),
            "conventional_ratio": round(conventional / total, 3),
            "emoji_ratio": round(emojis / total, 3),
        },
        "helix_score": {"score": score, "max": 100, "verdict": verdict(score)},
    }
