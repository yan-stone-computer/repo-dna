"""Render a self-contained preview page: view the card in a browser, download the SVG.

The page is a single HTML file — the card is inlined, the download button
serves the SVG from a data URL. No server, no assets, no JavaScript.
"""

from __future__ import annotations

import base64
import re

from .svgcard import render_svg


def _esc(text) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_html(report: dict) -> str:
    svg = render_svg(report)
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    repo_name = _esc(report["repo"]["name"])
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", report["repo"]["name"]).strip("-") or "repo"
    filename = f"{safe}-dna-card.svg"
    generated = _esc(report["generated_at"])

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🧬 {repo_name} · repo-dna card</title>
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; margin: 0; }}
  body {{ background: #0d1117; color: #e6edf3;
          font-family: 'Segoe UI', -apple-system, Roboto, Helvetica, Arial, sans-serif;
          min-height: 100vh; display: flex; flex-direction: column;
          align-items: center; gap: 22px; padding: 48px 16px; }}
  h1 {{ font-size: 20px; font-weight: 700; }}
  h1 span {{ color: #8b949e; font-weight: 400; }}
  .card {{ width: 100%; max-width: 880px; border-radius: 20px; overflow: hidden;
           box-shadow: 0 24px 80px rgba(0, 0, 0, .55); }}
  .card svg {{ display: block; width: 100%; height: auto; }}
  .actions {{ display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; }}
  a.btn {{ display: inline-block; padding: 12px 28px; border-radius: 12px;
           font-weight: 700; font-size: 15px; text-decoration: none; color: #050810;
           background: linear-gradient(90deg, #a78bfa, #38bdf8 50%, #34d399); }}
  a.btn:hover {{ filter: brightness(1.12); }}
  details {{ max-width: 880px; width: 100%; color: #8b949e; font-size: 14px; }}
  details pre {{ margin-top: 8px; padding: 12px 14px; background: #161b22;
                 border: 1px solid #21262d; border-radius: 10px; overflow-x: auto;
                 font-size: 12.5px; color: #c9d1d9; }}
  footer {{ color: #8b949e; font-size: 12.5px; }}
  footer code {{ color: #c9d1d9; }}
</style>
</head>
<body>
  <h1>🧬 {repo_name} <span>· repo-dna card preview</span></h1>
  <div class="card">{svg}</div>
  <div class="actions">
    <a class="btn" download="{filename}" href="data:image/svg+xml;base64,{b64}">⬇️ Download SVG</a>
  </div>
  <details>
    <summary>Embed it in your README</summary>
    <pre>1. commit the downloaded svg to your repo, e.g. docs/{filename}
2. reference it anywhere in your README:

   ![repo dna]({filename})</pre>
  </details>
  <footer>generated {generated} · <code>pip install repo-dna</code></footer>
</body>
</html>
"""
