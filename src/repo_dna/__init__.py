"""repo-dna — scan a git repository and print its DNA."""

__version__ = "0.1.0"

from .analyzer import DNAError, analyze, verdict
from .html import render_html
from .svgcard import render_svg
from .terminal import render_terminal
from .webgui import serve

__all__ = ["DNAError", "analyze", "render_html", "render_svg", "render_terminal", "serve", "verdict", "__version__"]
