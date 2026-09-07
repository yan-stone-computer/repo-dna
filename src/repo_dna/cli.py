"""Command line interface for repo-dna."""

from __future__ import annotations

import argparse
import json
import os
import sys
import webbrowser
from pathlib import Path

from . import __version__
from .analyzer import DNAError, analyze
from .html import render_html
from .svgcard import render_svg
from .terminal import render_terminal
from .webgui import DEFAULT_PORT, serve


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-dna",
        description="🧬 Scan a git repository and print its DNA — plus a shareable SVG card.",
        epilog="examples: repo-dna . | repo-dna ~/my-project --svg card.svg | repo-dna . --json",
    )
    parser.add_argument(
        "path", nargs="?", default=".",
        help="path to a git repository (default: current directory)",
    )
    parser.add_argument(
        "--json", nargs="?", const="-", default=None, metavar="FILE",
        help="also write the raw report as JSON (default: print to stdout)",
    )
    parser.add_argument(
        "--svg", nargs="?", const="repo-dna-card.svg", default=None, metavar="FILE",
        help="also write the shareable SVG card (default: repo-dna-card.svg)",
    )
    parser.add_argument(
        "--html", nargs="?", const="repo-dna-card.html", default=None, metavar="FILE",
        help="also write a preview page where the card can be downloaded",
    )
    parser.add_argument(
        "--open", action="store_true",
        help="open the preview page in your browser (implies --html)",
    )
    parser.add_argument(
        "--web", nargs="?", const=DEFAULT_PORT, default=None, type=int, metavar="PORT",
        help="launch the local web dashboard instead of printing a report (default port: 8642)",
    )
    parser.add_argument("--no-color", action="store_true", help="disable ANSI colors")
    parser.add_argument("--version", action="version", version=f"repo-dna {__version__}")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if os.name == "nt":
        os.system("")  # enable ANSI escape sequences on Windows 10+ consoles

    if args.web is not None:
        try:
            return serve(args.path, port=args.web)
        except DNAError as exc:
            print(f"🧬 repo-dna: {exc}", file=sys.stderr)
            return 2

    try:
        report = analyze(args.path)
    except DNAError as exc:
        print(f"🧬 repo-dna: {exc}", file=sys.stderr)
        return 2

    if args.json is not None:
        payload = json.dumps(report, indent=2, ensure_ascii=False)
        if args.json == "-":
            print(payload)
        else:
            Path(args.json).write_text(payload + "\n", encoding="utf-8")
            print(f"📄 JSON report written to {args.json}")

    if args.svg is not None:
        Path(args.svg).write_text(render_svg(report), encoding="utf-8")
        print(f"🖼  SVG card written to {args.svg}")

    if args.open and args.html is None:
        args.html = build_parser().get_default("html")
    if args.html is not None:
        html_path = Path(args.html)
        html_path.write_text(render_html(report), encoding="utf-8")
        print(f"🌐 Preview page written to {args.html}")
        if args.open:
            webbrowser.open(html_path.resolve().as_uri())

    if args.json != "-":  # JSON-to-stdout mode replaces the pretty report
        color = (
            not args.no_color
            and sys.stdout.isatty()
            and os.environ.get("NO_COLOR") is None
            and os.environ.get("TERM") != "dumb"
        )
        print(render_terminal(report, color=color))
    return 0
