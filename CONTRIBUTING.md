# Contributing to repo-dna

Thanks for scanning in! 🧬 Issues and PRs are welcome — especially PRs that
add a new metric to the scan.

## Dev setup

```bash
git clone https://github.com/YOUR_USERNAME/repo-dna
cd repo-dna
pip install -e .
python -m unittest discover -s tests -v
```

That's the whole toolchain. There is no linter config, no pre-commit hook,
and no dependencies to sync — see the ground rules.

## Ground rules

- **Zero dependencies, forever.** If it can't be done with the Python
  standard library plus the `git` binary, it doesn't ship.
- One metric (or one fix) per PR.
- Everything is computed locally from `.git`. No network calls, ever.

## Adding a metric — the 10-minute recipe

1. Compute it in `analyzer.py`. Everything comes from `git log` / `git ls-files`.
2. Add it to the report dict — it's automatically in `--json`.
3. Render it in `terminal.py`, and in `svgcard.py` if it deserves a spot on the card.
4. Add a test in `tests/test_repo_dna.py` using the `make_repo()` helper.
5. Add a row to the metrics table in **both** READMEs.

## Commit style

Conventional Commits with an emoji prefix. We scan ourselves, after all —
`emoji_ratio` is watching you.
