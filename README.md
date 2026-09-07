<div align="center">

<img src="examples/repo-dna-card.svg" width="840" alt="repo-dna card — repo-dna scanned itself">

# 🧬 repo-dna

**Your repo's git history is a personality test. This is the scanner.**

One command · Zero dependencies · Nothing leaves your machine

[![PyPI](https://img.shields.io/badge/PyPI-0.1.0-blue)](https://pypi.org/project/repo-dna/)
[![Python](https://img.shields.io/badge/python-3.9%2B-informational)](https://pypi.org/project/repo-dna/)
[![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)](#-faq)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](.github/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[Quick start](#-quick-start) · [The metrics](#-the-metrics) · [JSON mode](#-json-mode) · [FAQ](#-faq)

*The card above is real — repo-dna scanned this very repository. 中文版见 [README.zh-CN.md](README.zh-CN.md)。*

</div>

---

Every repository has a personality. Some are 2 a.m. caffeine-fueled sprints. Some are carefully
shepherded by a fleet of maintainers. Some are 90% YAML and pure chaos.

**repo-dna** reads your git history and tells you what your project actually *is* — then hands
you a gorgeous, embeddable card to brag about it.

- 🧬 **Helix Score** — one number for the whole genome (0–100, vibes-based but reproducible)
- 🚌 **Bus Factor** — how many people you can lose before the repo flatlines
- 🦉 **Night Owl Index** & 🎉 **Weekend Warrior** — when the work *really* happens
- 🌪️ **Chaos Coefficient** — deletions per insertion. An aggression metric.
- 🔥 **Hot Files** — where the churn lives
- 🖼️ **Shareable SVG card** — dark, gradient, and born for your README

## 🚀 Quick start

```bash
pip install repo-dna        # or: pipx install repo-dna · uvx repo-dna
repo-dna .
```

That's it. No config, no API token, no account. Works on any git repository:

```bash
repo-dna ~/my-project
repo-dna ~/dotfiles --svg card.svg      # + the shareable card
```

<details>
<summary><b>No pip? Run it from source</b></summary>

```bash
git clone https://github.com/YOUR_USERNAME/repo-dna
cd repo-dna
PYTHONPATH=src python -m repo_dna .
```
</details>

## 🖼️ The card

The centerpiece is a shareable SVG card — designed to be committed into your README, where
every visitor is one glance away from scanning their own repo. That's the whole growth loop,
and it fits on two lines:

```bash
repo-dna . --svg docs/dna-card.svg
```

```markdown
![repo dna](docs/dna-card.svg)
```

Prefer clicking to typing? `--html` writes a self-contained preview page — the card rendered
in your browser with a big **⬇️ Download SVG** button:

```bash
repo-dna . --html --open
```

## 🖥️ Web dashboard (GUI)

Don't want a terminal? One flag gives you a point-and-click dashboard in
your browser — type any repository path, hit **🧬 Scan**, and explore the
verdict, the weekday×hour heatmap, language bars, hot files, and the card:

```bash
repo-dna --web            # opens http://127.0.0.1:8642 automatically
repo-dna --web 9000       # or pick your own port
```

The dashboard is served by the stdlib's `http.server` — still zero
dependencies. It binds to `127.0.0.1` only and every request must carry a
random per-launch token, so no other local process (or drive-by web page)
can scan your disk or read reports from private repositories.

## 📊 The terminal report

```text
  🧬 REPO DNA  ·  repo-dna
──────────────────────────────────────────────────────────────────
  age 7 days · 19 files · 2,203 lines · 5 languages · first commit 2026-08-31

  COMMITS  20 total · 2.86/day avg
  ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▄█  weekly, last 26 weeks

  LANGUAGES
  Python        ███████████████·······   69.2%    1,524 lines
  Markdown      █████·················   24.9%      549 lines
  SVG           █·····················    2.3%       51 lines
  YAML          ······················    1.8%       39 lines
  TOML          ······················    1.8%       39 lines

  CONTRIBUTORS  bus factor 1
  3NF的共价键       ██████████████████████     20 commits (100%)

  ACTIVITY  commits by weekday × hour (local time)
  Mon  ▒▒▒▒······································▒▒▒▒··
  Tue  ▒▒····················▒▒························
  Wed  ······························▒▒······▒▒········
  Thu  ····················▒▒··························
  Fri  ····························▒▒··▒▒········▒▒····
  Sat  ························▒▒··············▒▒······
  Sun  ····················██▒▒▓▓······················
      00    03    06    09    12    15    18    21

  FUN STATS
  🦉 Night Owl Index     15%  commits between 00:00–06:00
  🎉 Weekend Warrior     40%  commits on Sat/Sun
  🌪️ Chaos Coefficient  0.04  deletions per insertion
  📅 Longest Streak        8  consecutive days
  💬 Message Style       85%  conventional · avg 44 chars
  🔥 Hot File           src/repo_dna/webgui.py

──────────────────────────────────────────────────────────────────
  🧬 HELIX SCORE   47/100  ·  Hybrid Vigor 🌱
  ███████████████████·····················
```

*Real output — repo-dna scanning itself. Yes, the helix score will improve after
the first contributor joins. That's the point.*

## 🧬 The metrics

| Metric | What it measures | How to read it |
|---|---|---|
| 🧬 **Helix Score** | Overall genome quality, 0–100 | Activity, collaboration, diversity, rhythm, consistency, discipline and maturity — combined with public weights in `_helix_score()`. Reproducible pseudo-science. |
| 🚌 **Bus Factor** | Contributors covering >50% of commits | `1` means one departure flatlines the project. You know what to do. |
| 🦉 **Night Owl Index** | % of commits between 00:00–06:00 | Under 5%: healthy adult. Over 30%: this repo has a sleep disorder. |
| 🎉 **Weekend Warrior** | % of commits on Sat/Sun | The side-project coefficient. |
| 🌪️ **Chaos Coefficient** | Deletions per insertion | ≈0.0: builds, never rewrites. ≈1.0: brutal editor. >1.0: the code writes itself back. |
| 🔥 **Hot File** | Most-churned file (lines in + out) | Where the battle actually is. Changelog ground zero. |
| 📅 **Longest Streak** | Most consecutive days with a commit | Consistency > intensity. |
| 💬 **Message Style** | Conventional-commits & emoji ratios | Yes, we scan ourselves. `emoji_ratio` is watching. |

## ⚙️ CLI reference

```text
repo-dna [PATH]          scan the repo at PATH (default: current directory)
  --web [PORT]           launch the local web dashboard (default port: 8642)
  --svg [FILE]           also write the SVG card (default: repo-dna-card.svg)
  --html [FILE]          also write a preview page with a download button
  --open                 open the preview page in your browser (implies --html)
  --json [FILE]          also write the raw report (default: print to stdout)
  --no-color             disable ANSI colors
  --version
```

## 📤 JSON mode

Everything the pretty renderers show — and a few things they don't — is one flag away:

```bash
repo-dna . --json
```

```json
{
  "commits": { "total": 20, "age_days": 7, "longest_streak_days": 8 },
  "bus_factor": 1,
  "languages": [{ "name": "Python", "share": 69.2 }],
  "chaos_coefficient": 0.04,
  "helix_score": { "score": 47, "verdict": "Hybrid Vigor 🌱" }
}
```

jq one-liners for the impatient:

```bash
repo-dna . --json | jq .helix_score              # the number and the verdict
repo-dna . --json | jq .bus_factor               # an existential crisis in one integer
repo-dna . --json | jq -r '.hot_files[0].path'   # git blame, but honest
```

## 🔒 Privacy

repo-dna reads `.git` locally and prints to stdout. **No network access, no telemetry, no
accounts, no dependencies.** Air-gapped machines are first-class citizens.

## 🆚 How it compares

| | repo-dna | cloc / scc | gitingest | contribution graph |
|---|:---:|:---:|:---:|:---:|
| Counts lines | ✅ | ✅ | ✅ | ❌ |
| Reads git history | ✅ | ❌ | ❌ | ✅ |
| Tells you what your repo *is* | ✅ | ❌ | ❌ | 😐 |
| Hands you a card to brag with | ✅ | ❌ | ❌ | 🐍 |

## 🤔 FAQ

<details>
<summary><b>Is the Helix Score scientific?</b></summary>
It's reproducible pseudo-science: the weights are public, the inputs are your real git history, and the verdicts are honest. The whole algorithm is ~15 lines in <code>analyzer.py</code> — PRs welcome.
</details>

<details>
<summary><b>My solo repo got bus factor 1. Rude?</b></summary>
Accurate. Bus factor 1 isn't a judgment, it's a dashboard. (The Helix Score does reward collaboration, if you ever feel like recruiting a co-maintainer.)
</details>

<details>
<summary><b>Does it work on huge repos?</b></summary>
Yes — it walks the full git log. Monorepos take a few seconds; everything else is instant.
</details>

<details>
<summary><b>Windows?</b></summary>
Tested on Windows, macOS and Linux in CI. Modern Windows terminals render the ANSI colors fine.
</details>

<details>
<summary><b>Why zero dependencies?</b></summary>
Because <code>pip install</code> should be the hardest part of the experience — and because a scanner this nosy has no business phoning home.
</details>

## 🗺️ Roadmap

- [ ] Light-theme card variant
- [ ] GitHub Action that refreshes the card in your README on every push
- [ ] `--since` time windows ("who was I in 2024?")
- [ ] DNA drift — diff two scans and watch your repo evolve

## 🤝 Contributing

Issues and PRs welcome — the [contributing guide](CONTRIBUTING.md) has a 10-minute recipe for
adding a new metric. One rule above all: **zero dependencies, forever.**

## ⭐ Show your support

If repo-dna scanned your repo and the verdict hurt — that's growth. Leave a ⭐ so others can
grow too.

## License

[MIT](LICENSE) · Made with 🧬 and a concerning number of 00:37 commits.
