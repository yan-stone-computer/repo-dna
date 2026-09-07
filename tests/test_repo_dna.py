"""Tests for repo-dna.

Each test builds a throwaway git repository with controlled authors,
dates and files, then asserts on the DNA report.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from repo_dna.analyzer import DNAError, analyze  # noqa: E402
from repo_dna.html import render_html  # noqa: E402
from repo_dna.svgcard import render_svg  # noqa: E402
from repo_dna.terminal import render_terminal  # noqa: E402
from repo_dna.webgui import make_server  # noqa: E402


def _git(repo: Path, *args: str, date: str = None, name: str = None, email: str = None):
    cmd = ["git", "-C", str(repo)]
    if name:
        cmd += ["-c", f"user.name={name}"]
    if email:
        cmd += ["-c", f"user.email={email}"]
    cmd += list(args)
    env = dict(os.environ)
    if date:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = date
    return subprocess.run(cmd, check=True, capture_output=True, env=env)


def make_repo(plan, root=None):
    """Build a demo repo. ``plan`` items are (message, files, date, author)."""
    root = root or Path(tempfile.mkdtemp())
    repo = root / "demo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "core.autocrlf", "false")
    for message, files, date, who in plan:
        for rel, content in files.items():
            fp = repo / rel
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content, encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", message, date=date, name=who[0], email=who[1])
    return repo


ADA = ("Ada Lovelace", "ada@example.com")
BOB = ("Bob Tester", "bob@example.com")


class AnalyzerTests(unittest.TestCase):
    def test_not_a_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(DNAError):
                analyze(tmp)

    def test_basic_counts_and_bus_factor(self):
        plan = [
            ("feat: alpha", {"a.py": "x = 1\n"}, "2026-09-01T10:00:00", ADA),
            ("feat: beta", {"b.py": "y = 2\n"}, "2026-09-02T10:00:00", ADA),
            ("fix: gamma", {"c.py": "z = 3\n"}, "2026-09-03T10:00:00", ADA),
            ("docs: delta", {"d.py": "w = 4\n"}, "2026-09-04T10:00:00", BOB),
        ]
        report = analyze(make_repo(plan))
        self.assertEqual(report["commits"]["total"], 4)
        self.assertEqual(len(report["authors"]), 2)
        # Ada holds 75% of commits, so one person already crosses 50%.
        self.assertEqual(report["bus_factor"], 1)
        self.assertEqual(report["authors"][0]["name"], "Ada Lovelace")

    def test_weekend_and_night_owl(self):
        # 2026-09-05 is a Saturday; 02:00 is night. Both in local time, and
        # timestamps round-trip through the same local clock we test with.
        saturday_noon = datetime(2026, 9, 5, 12, 0).strftime("%Y-%m-%dT%H:%M:%S")
        wednesday_night = datetime(2026, 9, 2, 2, 0).strftime("%Y-%m-%dT%H:%M:%S")
        plan = [
            ("feat: weekend", {"a.py": "1\n"}, saturday_noon, ADA),
            ("feat: night", {"b.py": "2\n"}, wednesday_night, ADA),
        ]
        act = analyze(make_repo(plan))["activity"]
        self.assertEqual(act["weekend_ratio"], 0.5)
        self.assertEqual(act["night_ratio"], 0.5)

    def test_streak_and_age(self):
        plan = [
            ("one", {"a.py": "1\n"}, "2026-09-02T10:00:00", ADA),
            ("two", {"b.py": "2\n"}, "2026-09-03T11:00:00", ADA),
            ("three", {"c.py": "3\n"}, "2026-09-04T12:00:00", ADA),
        ]
        report = analyze(make_repo(plan))
        self.assertEqual(report["commits"]["longest_streak_days"], 3)
        self.assertEqual(report["commits"]["age_days"], 3)

    def test_languages_and_binary_files(self):
        plan = [
            ("feat: files", {
                "src/a.py": "print('hi')\n" * 3,
                "README.md": "# hello\n" * 5,
                "logo.png": b"\x89PNG\r\n\x1a\n\0\0".decode("latin-1"),
            }, "2026-09-01T10:00:00", ADA),
        ]
        report = analyze(make_repo(plan))
        names = {l["name"] for l in report["languages"]}
        self.assertIn("Python", names)
        self.assertIn("Markdown", names)
        python = next(l for l in report["languages"] if l["name"] == "Python")
        self.assertEqual(python["lines"], 3)
        self.assertEqual(report["totals"]["binary_files"], 1)

    def test_hot_files_and_chaos(self):
        plan = [
            ("feat: create", {"core.py": "a\n"}, "2026-09-01T10:00:00", ADA),
            ("feat: churn", {"core.py": "b\n", "gone.py": "c\n"}, "2026-09-02T10:00:00", ADA),
        ]
        report = analyze(make_repo(plan))
        self.assertEqual(report["hot_files"][0]["path"], "core.py")
        # 3 insertions, 1 deletion across the two commits.
        self.assertEqual(report["chaos_coefficient"], 0.33)

    def test_message_style(self):
        plan = [
            ("feat: plain", {"a.py": "1\n"}, "2026-09-01T10:00:00", ADA),
            ("🎉 chore: emoji", {"b.py": "2\n"}, "2026-09-02T10:00:00", ADA),
            ("updated some stuff", {"c.py": "3\n"}, "2026-09-03T10:00:00", ADA),
        ]
        msg = analyze(make_repo(plan))["messages"]
        self.assertEqual(msg["conventional_ratio"], 0.667)
        self.assertEqual(msg["emoji_ratio"], 0.333)

    def test_web_dashboard(self):
        import json
        import threading
        import urllib.error
        import urllib.parse
        import urllib.request

        plan = [
            ("feat: one", {"a.py": "1\n"}, "2026-09-01T10:00:00", ADA),
            ("feat: two", {"b.py": "2\n"}, "2026-09-02T10:00:00", ADA),
        ]
        repo = make_repo(plan)
        httpd = make_server(str(repo.parent), port=0)
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{port}"
        token = httpd.app_token
        try:
            # no token, no service
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(base + "/")
            ctx.exception.close()

            with urllib.request.urlopen(f"{base}/?token={token}") as res:
                page = res.read().decode("utf-8")
            self.assertIn("repo-dna dashboard", page)
            self.assertNotIn("%VERSION%", page)
            self.assertNotIn("%DEFAULT_PATH%", page)

            query = urllib.parse.urlencode({"path": str(repo), "token": token})
            with urllib.request.urlopen(f"{base}/api/scan?{query}") as res:
                report = json.load(res)
            self.assertEqual(report["commits"]["total"], 2)

            with urllib.request.urlopen(f"{base}/api/card?{query}") as res:
                self.assertIn("image/svg+xml", res.headers["Content-Type"])
                self.assertIn("HELIX", res.read().decode("utf-8"))

            empty = tempfile.mkdtemp()
            bad = f"{base}/api/scan?path={urllib.parse.quote(empty)}&token={token}"
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(bad)
            ctx.exception.close()
        finally:
            httpd.shutdown()
            httpd.server_close()

    def test_json_and_renderers(self):
        plan = [
            ("feat: one", {"a.py": "1\n"}, "2026-09-01T10:00:00", ADA),
            ("feat: two", {"b.py": "2\n"}, "2026-09-02T10:00:00", ADA),
        ]
        report = analyze(make_repo(plan))

        payload = json.dumps(report, ensure_ascii=False)  # must be serializable
        self.assertIn("helix_score", payload)

        text = render_terminal(report, color=False)
        self.assertIn("HELIX SCORE", text)

        svg = render_svg(report)
        self.assertIn("HELIX SCORE", svg)
        self.assertIn("demo", svg)
        self.assertNotIn("None", svg)

    def test_html_preview_page(self):
        plan = [
            ("feat: one", {"a.py": "1\n"}, "2026-09-01T10:00:00", ADA),
        ]
        report = analyze(make_repo(plan))
        page = render_html(report)
        self.assertIn("Download SVG", page)
        self.assertIn('download="demo-dna-card.svg"', page)
        self.assertIn("data:image/svg+xml;base64,", page)
        self.assertIn("<svg", page)
        self.assertNotIn(">None<", page)


if __name__ == "__main__":
    unittest.main()
