"""Local web dashboard: scan any repository from a browser.

A single-file GUI served by the standard library's ``http.server`` — no
frameworks, no CDN, no telemetry. The server binds to 127.0.0.1 only.
"""

from __future__ import annotations

import json
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import __version__
from .analyzer import DNAError, analyze
from .svgcard import render_svg

DEFAULT_PORT = 8642


def _esc_attr(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


class _Handler(BaseHTTPRequestHandler):
    server_version = f"repo-dna/{__version__}"

    def do_GET(self):  # noqa: N802 (http.server API)
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        # Every request must carry the per-launch token, so other local
        # processes (or drive-by web pages via DNS rebinding) can't drive
        # the API or read reports from private repositories.
        if query.get("token", [""])[0] != getattr(self.server, "app_token", ""):
            self._send(403, "text/plain; charset=utf-8", "forbidden")
            return
        path = (query.get("path") or ["."])[0]
        try:
            if parsed.path in ("/", "/index.html"):
                page = _page(getattr(self.server, "app_default_path", "."),
                             getattr(self.server, "app_token", ""))
                self._send(200, "text/html; charset=utf-8", page)
            elif parsed.path == "/api/scan":
                self._send(
                    200,
                    "application/json; charset=utf-8",
                    json.dumps(analyze(path), ensure_ascii=False),
                )
            elif parsed.path == "/api/card":
                self._send(200, "image/svg+xml", render_svg(analyze(path)))
            else:
                self._send(404, "text/plain; charset=utf-8", "not found")
        except DNAError as exc:
            self._send(
                400,
                "application/json; charset=utf-8",
                json.dumps({"error": str(exc)}, ensure_ascii=False),
            )

    def _send(self, status: int, ctype: str, body: str) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):  # keep the console clean
        pass


def make_server(path: str = ".", port: int = 0) -> ThreadingHTTPServer:
    """Create the dashboard server (port 0 lets the OS pick a free one)."""
    httpd = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    httpd.app_default_path = str(Path(path).resolve())
    httpd.app_token = secrets.token_urlsafe(16)
    return httpd


def serve(path: str = ".", port: int = DEFAULT_PORT, open_browser: bool = True) -> int:
    """Run the dashboard until Ctrl+C. Returns a process exit code."""
    httpd = None
    last_exc = None
    for attempt in range(port, port + 10):
        try:
            httpd = make_server(path, attempt)
            break
        except OSError as exc:  # port already in use — try the next one
            last_exc = exc
    if httpd is None:
        raise DNAError(f"could not bind a port near {port}: {last_exc}")

    url = f"http://127.0.0.1:{httpd.server_address[1]}/?token={httpd.app_token}"
    print(f"🧬 repo-dna dashboard  →  {url}")
    print(f"   default repo: {httpd.app_default_path}")
    print("   press Ctrl+C to stop")
    if open_browser:
        threading.Timer(0.6, webbrowser.open, args=(url,)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🧬 dashboard stopped")
    finally:
        httpd.server_close()
    return 0


_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🧬 repo-dna dashboard</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; margin: 0; }
  body { background: #0d1117; color: #e6edf3;
         font-family: 'Segoe UI', -apple-system, Roboto, Helvetica, Arial, sans-serif;
         min-height: 100vh; }
  .wrap { max-width: 960px; margin: 0 auto; padding: 32px 20px 64px; }
  header { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
  h1 { font-size: 22px; }
  h1 span { color: #8b949e; font-weight: 400; font-size: 14px; }
  .scanbar { display: flex; gap: 10px; margin: 22px 0 8px; }
  #path { flex: 1; padding: 11px 14px; border-radius: 10px; border: 1px solid #30363d;
          background: #161b22; color: #e6edf3; font-size: 14px; }
  #path:focus { outline: none; border-color: #38bdf8; }
  button { padding: 11px 24px; border: none; border-radius: 10px; font-weight: 700;
           font-size: 14px; color: #050810; cursor: pointer;
           background: linear-gradient(90deg, #a78bfa, #38bdf8 50%, #34d399); }
  button:hover { filter: brightness(1.12); }
  button:disabled { opacity: .6; cursor: wait; }
  .hint { color: #8b949e; font-size: 12.5px; margin-bottom: 24px; }
  #error { display: none; background: rgba(248,81,73,.12); border: 1px solid rgba(248,81,73,.4);
           color: #f85149; padding: 12px 16px; border-radius: 10px; margin-bottom: 20px;
           font-size: 14px; }
  #result { display: none; }
  .verdict { text-align: center; margin: 6px 0 22px; }
  .verdict b { font-size: 36px; font-weight: 800;
               background: linear-gradient(90deg, #a78bfa, #38bdf8 50%, #34d399);
               -webkit-background-clip: text; background-clip: text; color: transparent; }
  .verdict span { color: #8b949e; font-size: 14px; }
  .cardbox { border-radius: 20px; overflow: hidden; box-shadow: 0 24px 80px rgba(0,0,0,.5);
             margin-bottom: 28px; }
  .cardbox img { display: block; width: 100%; height: auto; }
  .tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
           gap: 12px; margin-bottom: 18px; }
  .tile { background: #161b22; border: 1px solid #21262d; border-radius: 12px;
          padding: 14px 16px; }
  .tile .v { font-size: 19px; font-weight: 700; }
  .tile .k { font-size: 11px; color: #8b949e; letter-spacing: 1.2px; margin-top: 3px; }
  section { background: #161b22; border: 1px solid #21262d; border-radius: 14px;
            padding: 18px 20px; margin-bottom: 16px; }
  section h2 { font-size: 11px; letter-spacing: 2.5px; color: #8b949e; margin-bottom: 14px; }
  .heat { display: grid; grid-template-columns: 36px repeat(24, minmax(0, 1fr)); gap: 3px; }
  .heat .lbl { font-size: 10px; color: #8b949e; }
  .heat i { display: block; aspect-ratio: 1; border-radius: 2.5px; min-width: 0; }
  .h0 { background: #12181f; } .h1 { background: #0e4429; } .h2 { background: #006d32; }
  .h3 { background: #26a641; } .h4 { background: #39d353; }
  .row { display: flex; align-items: center; gap: 10px; margin: 9px 0; }
  .row .name { width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
               font-size: 13.5px; }
  .row .name.mono { width: 230px; flex: 0 0 230px; font-family: Consolas, monospace;
                    font-size: 12.5px; color: #c9d1d9; }
  .row .barwrap { flex: 1; background: #0d1117; border-radius: 6px; height: 10px;
                  overflow: hidden; }
  .row .bar { height: 100%; border-radius: 6px;
              background: linear-gradient(90deg, #a78bfa, #38bdf8); }
  .row .n { width: 130px; text-align: right; color: #8b949e; font-size: 12px;
            white-space: nowrap; }
  .actions { display: flex; gap: 12px; margin: 4px 0 8px; flex-wrap: wrap; }
  a.btn { display: inline-block; padding: 10px 22px; border-radius: 10px; font-weight: 700;
          font-size: 13.5px; text-decoration: none; color: #050810;
          background: linear-gradient(90deg, #a78bfa, #38bdf8 50%, #34d399); }
  a.btn:hover { filter: brightness(1.12); }
  details { margin-top: 14px; }
  summary { cursor: pointer; color: #8b949e; font-size: 14px; }
  pre { margin-top: 10px; padding: 14px; background: #0d1117; border: 1px solid #21262d;
        border-radius: 10px; overflow: auto; font-size: 12px; color: #c9d1d9;
        max-height: 420px; }
  footer { text-align: center; color: #8b949e; font-size: 12.5px; margin-top: 44px; }
  .spin { display: inline-block; animation: r 1s linear infinite; }
  @keyframes r { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>🧬 repo-dna</h1><span>local dashboard · v%VERSION%</span>
  </header>

  <div class="scanbar">
    <input id="path" value="%DEFAULT_PATH%" spellcheck="false"
           placeholder="path to any git repository"
           onkeydown="if (event.key === 'Enter') scan()">
    <button id="go" onclick="scan()">🧬 Scan</button>
  </div>
  <div class="hint">Everything runs on your machine — type any repository path on disk.</div>
  <div id="error"></div>

  <div id="result">
    <div class="verdict"><b id="score">–</b> <span id="verdict"></span></div>
    <div class="cardbox"><img id="card" alt="DNA card"></div>
    <div class="tiles">
      <div class="tile"><div class="v" id="t-commits">–</div><div class="k">COMMITS</div></div>
      <div class="tile"><div class="v" id="t-bus">–</div><div class="k">BUS FACTOR</div></div>
      <div class="tile"><div class="v" id="t-age">–</div><div class="k">AGE</div></div>
      <div class="tile"><div class="v" id="t-lines">–</div><div class="k">LINES OF CODE</div></div>
    </div>
    <section><h2>ACTIVITY · WEEKDAY × HOUR (LOCAL TIME)</h2><div class="heat" id="heat"></div></section>
    <section><h2>LANGUAGES</h2><div id="langs"></div></section>
    <section><h2>CONTRIBUTORS</h2><div id="authors"></div></section>
    <section><h2>HOT FILES · MOST CHURN</h2><div id="hot"></div></section>
    <div class="actions">
      <a class="btn" id="dl" download="dna-card.svg">⬇️ Download SVG card</a>
    </div>
    <details><summary>Raw JSON report</summary><pre id="raw"></pre></details>
  </div>

  <footer>repo-dna v%VERSION% · zero dependencies · nothing leaves your machine</footer>
</div>

<script>
const $ = (id) => document.getElementById(id);
const TOKEN = "%TOKEN%";
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
                            .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function ageLabel(d) {
  if (d < 14) return d + " days";
  if (d < 90) return Math.floor(d / 7) + " weeks";
  if (d < 730) return Math.round(d / 30.4) + " months";
  return (d / 365).toFixed(1) + " yrs";
}

function barRow(name, frac, note, mono, color) {
  let style = ' style="width:' + Math.max(2, Math.round(frac * 100)) + '%';
  if (color) style += ';background:' + esc(color);
  style += '"';
  return '<div class="row"><span class="name' + (mono ? " mono" : "") + '">'
       + esc(name) + '</span><div class="barwrap"><div class="bar"' + style
       + '></div></div><span class="n">' + esc(note) + "</span></div>";
}

function render(d, path) {
  const q = "path=" + encodeURIComponent(path) + "&token=" + encodeURIComponent(TOKEN)
          + "&t=" + Date.now();
  $("score").textContent = d.helix_score.score;
  $("verdict").textContent = "/ 100 · " + d.helix_score.verdict + " · " + d.repo.name;
  $("card").src = "/api/card?" + q;
  $("t-commits").textContent = d.commits.total.toLocaleString();
  $("t-bus").textContent = d.bus_factor;
  $("t-age").textContent = ageLabel(d.commits.age_days);
  $("t-lines").textContent = d.totals.lines.toLocaleString();

  const grid = d.activity.grid;
  const peak = Math.max(...grid.map((r) => Math.max(...r)), 1);
  let heat = "<i></i>";
  for (let h = 0; h < 24; h++) {
    heat += h % 3 === 0 ? '<span class="lbl">' + String(h).padStart(2, "0") + "</span>" : "<i></i>";
  }
  grid.forEach((row, i) => {
    heat += '<span class="lbl">' + DOW[i] + "</span>";
    row.forEach((v) => { heat += '<i class="h' + (v === 0 ? 0 : 1 + Math.round(v / peak * 3)) + '"></i>'; });
  });
  $("heat").innerHTML = heat;

  $("langs").innerHTML = d.languages.map((l) =>
    barRow(l.name, l.share / 100, l.share.toFixed(1) + "% · " + l.lines.toLocaleString() + " lines", false, l.color)
  ).join("") || '<div class="row"><span class="name" style="color:#8b949e">none</span></div>';

  $("authors").innerHTML = d.authors.slice(0, 8).map((a) =>
    barRow(a.name, a.commits / d.commits.total, a.commits.toLocaleString() + " commits")
  ).join("");

  const maxChurn = Math.max(...d.hot_files.map((f) => f.churn), 1);
  $("hot").innerHTML = d.hot_files.map((f) =>
    barRow(f.path, f.churn / maxChurn, f.churn.toLocaleString() + " churn", true)
  ).join("") || '<div class="row"><span class="name" style="color:#8b949e">no file stats yet</span></div>';

  const safe = (d.repo.name.replace(/[^A-Za-z0-9._-]+/g, "-") || "repo") + "-dna-card.svg";
  $("dl").setAttribute("download", safe);
  $("dl").href = "/api/card?" + q;
  $("raw").textContent = JSON.stringify(d, null, 2);
  $("result").style.display = "block";
}

async function scan() {
  const path = $("path").value.trim() || ".";
  $("go").disabled = true;
  $("go").innerHTML = '<span class="spin">◌</span> Scanning';
  $("error").style.display = "none";
  try {
    const res = await fetch("/api/scan?path=" + encodeURIComponent(path)
                            + "&token=" + encodeURIComponent(TOKEN));
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "scan failed");
    render(data, path);
  } catch (err) {
    $("error").textContent = "🧬 " + err.message;
    $("error").style.display = "block";
    $("result").style.display = "none";
  } finally {
    $("go").disabled = false;
    $("go").textContent = "🧬 Scan";
  }
}

window.addEventListener("load", scan);
</script>
</body>
</html>
"""


def _page(default_path: str, token: str) -> str:
    return _PAGE.replace("%VERSION%", __version__).replace(
        "%DEFAULT_PATH%", _esc_attr(default_path)
    ).replace("%TOKEN%", token)
