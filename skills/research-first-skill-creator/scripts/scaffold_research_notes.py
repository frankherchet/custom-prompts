#!/usr/bin/env python3
"""Scaffold research notes from a template and a repo list."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path


def read_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def format_sources(repo_lines: list[str]) -> list[str]:
    # Expect lines in the form: "Label: URL"
    sources = []
    for line in repo_lines:
        if "://" in line:
            sources.append(f"- {line}")
    return sources


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold research notes.")
    parser.add_argument(
        "--template",
        default="references/research-notes-template.md",
        help="Path to the research notes template.",
    )
    parser.add_argument(
        "--repos",
        default="references/default-repos.md",
        help="Path to the default repos list.",
    )
    parser.add_argument(
        "--out",
        default="references/research-notes.md",
        help="Output file to write.",
    )
    parser.add_argument(
        "--date",
        default=str(date.today()),
        help="Date to stamp in YYYY-MM-DD format.",
    )

    args = parser.parse_args()

    template_path = Path(args.template)
    repos_path = Path(args.repos)
    out_path = Path(args.out)

    template = template_path.read_text()
    repo_lines = read_lines(repos_path)
    sources = "\n".join(format_sources(repo_lines))

    content = template.replace("- YYYY-MM-DD", f"- {args.date}")
    if "## Sources" in content:
        parts = content.split("## Sources", 1)
        content = parts[0] + "## Sources\n" + sources + "\n\n" + parts[1].lstrip()

    out_path.write_text(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
