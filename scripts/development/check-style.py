#!/usr/bin/env python3
"""Measure the Protocol's sentence style on Markdown that is not a registered Spec document.

``concorde spec-validation`` reports the style checks (``CHK.style.*``) for the Specs. Concorde's
own checkout asks the same style of the Markdown under ``prompts/``, and the Protocol's chapters
under ``protocol/`` are written in it too, but neither is a Spec document. This script applies the
same checks, from ``concorde.spec.style``, to every Markdown file under the paths it is given,
relative to the checkout unless absolute (``prompts/`` by default). It prints each problem as
``path:line: rule: message``, then the count of each rule and the problems of each file;
``--format json`` prints the same as one object. It exits with status 1 when it found a problem
and 0 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from concorde.spec.style import STYLE_CHECKS, style_problems  # noqa: E402


def markdown_files(paths: list[str]) -> list[Path]:
    """Every Markdown file named or found below the paths, which are relative to the checkout
    unless absolute, in order."""
    files: set[Path] = set()
    for name in paths:
        path = (ROOT / name).resolve()
        if path.is_dir():
            files.update(path.rglob("*.md"))
        elif path.is_file():
            files.add(path)
        else:
            raise SystemExit(f"check-style: no file or directory {name}")
    return sorted(files)


def shown(file: Path) -> str:
    """A file's path relative to the checkout when it lies inside it, otherwise absolute."""
    return (file.relative_to(ROOT) if file.is_relative_to(ROOT) else file).as_posix()


def main() -> int:
    parser = argparse.ArgumentParser(prog="check-style", description=__doc__)
    parser.add_argument("paths", nargs="*", default=["prompts"])
    parser.add_argument("--format", choices=["text", "json"], default="text")
    arguments = parser.parse_args()
    problems = [
        {
            "path": shown(file),
            "line": item.line,
            "rule": item.check,
            "message": item.message,
        }
        for file in markdown_files(arguments.paths)
        for item in style_problems(file.read_text(encoding="utf-8"))
    ]
    rules = Counter(item["rule"] for item in problems)
    counts = {rule: rules[rule] for rule in STYLE_CHECKS}
    files = dict(sorted(Counter(item["path"] for item in problems).items()))
    if arguments.format == "json":
        print(
            json.dumps(
                {"counts": counts, "files": files, "problems": problems}, indent=2
            )
        )
    else:
        for item in problems:
            print(f"{item['path']}:{item['line']}: {item['rule']}: {item['message']}")
        print()
        for rule, count in counts.items():
            print(f"{rule}: {count}")
        for path, count in files.items():
            print(f"{path}: {count}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
