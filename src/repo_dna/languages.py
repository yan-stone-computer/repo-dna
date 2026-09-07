"""Map file paths to languages, with linguist-flavored colors tuned for dark backgrounds."""

from __future__ import annotations

EXT_LANG = {
    ".py": "Python", ".pyw": "Python", ".pyi": "Python",
    ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".html": "HTML", ".htm": "HTML",
    ".css": "CSS", ".scss": "SCSS", ".less": "Less",
    ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin", ".swift": "Swift",
    ".c": "C", ".h": "C",
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".hpp": "C++", ".hh": "C++",
    ".cs": "C#", ".rb": "Ruby", ".php": "PHP",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell", ".fish": "Shell",
    ".ps1": "PowerShell", ".bat": "Batch", ".cmd": "Batch",
    ".md": "Markdown", ".markdown": "Markdown", ".rst": "reStructuredText", ".txt": "Text",
    ".json": "JSON", ".yml": "YAML", ".yaml": "YAML", ".toml": "TOML", ".ini": "INI", ".cfg": "INI",
    ".xml": "XML", ".sql": "SQL", ".lua": "Lua", ".vim": "Vim Script",
    ".r": "R", ".jl": "Julia", ".dart": "Dart", ".scala": "Scala", ".hs": "Haskell",
    ".ex": "Elixir", ".exs": "Elixir", ".erl": "Erlang", ".clj": "Clojure",
    ".vue": "Vue", ".svelte": "Svelte", ".ipynb": "Jupyter Notebook",
    ".proto": "Protocol Buffers", ".graphql": "GraphQL", ".svg": "SVG",
    ".cmake": "CMake", ".tf": "HCL", ".hcl": "HCL",
}

# GitHub Linguist colors, with a few darkened/lightened so they stay visible
# on the dark SVG card.
LANG_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#e8d44d",
    "TypeScript": "#3178c6",
    "HTML": "#e34c26",
    "CSS": "#a071c9",
    "SCSS": "#c6538c",
    "Less": "#5a6dd6",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Java": "#b07219",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
    "C": "#8a8a8a",
    "C++": "#f34b7d",
    "C#": "#178600",
    "Ruby": "#e0444f",
    "PHP": "#4F5D95",
    "Shell": "#89e051",
    "PowerShell": "#3b6ac4",
    "Batch": "#C1F12E",
    "Markdown": "#519aba",
    "reStructuredText": "#519aba",
    "Text": "#8b949e",
    "JSON": "#a2702a",
    "YAML": "#cb171e",
    "TOML": "#9c8a6b",
    "INI": "#8b949e",
    "XML": "#8b949e",
    "SQL": "#e38c00",
    "Lua": "#5c7fbf",
    "Vim Script": "#199f4b",
    "R": "#8bc7e0",
    "Julia": "#a270ba",
    "Dart": "#00B4AB",
    "Scala": "#c22d40",
    "Haskell": "#5e5086",
    "Elixir": "#8e6ce6",
    "Erlang": "#f07472",
    "Clojure": "#db5855",
    "Vue": "#41b883",
    "Svelte": "#ff3e00",
    "Jupyter Notebook": "#DA5B0B",
    "Protocol Buffers": "#7c6ce0",
    "GraphQL": "#e10098",
    "SVG": "#ffb13b",
    "CMake": "#da3434",
    "HCL": "#844FBA",
    "Docker": "#0db7ed",
    "Makefile": "#427819",
}

FALLBACK_COLOR = "#8b949e"

_SPECIAL = {
    "Dockerfile": "Docker",
    "Makefile": "Makefile",
    "CMakeLists.txt": "CMake",
}


def count_lines(data: bytes) -> int:
    """Count lines in raw file bytes without decoding."""
    if not data:
        return 0
    lines = data.count(b"\n")
    if not data.endswith(b"\n"):
        lines += 1
    return lines


def classify_path(path: str):
    """Return (language, color) for a repo-relative path, or (None, None)."""
    name = path.replace("\\", "/").rsplit("/", 1)[-1]
    if name in _SPECIAL:
        lang = _SPECIAL[name]
    else:
        dot = name.rfind(".")
        if dot <= 0:  # no extension, or a dotfile like .gitignore
            return None, None
        lang = EXT_LANG.get("." + name[dot + 1:].lower())
    if lang is None:
        return None, None
    return lang, LANG_COLORS.get(lang, FALLBACK_COLOR)
