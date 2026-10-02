#!/usr/bin/env python3
"""Vendor the complete Claude Code documentation under ``references/claude-code/``.

Concorde's Harness runs headless Claude Code workers and confines them with Claude Code's own
settings, permission rules, hooks and sandbox, so the Module that generates those settings
declares this documentation as an ``includes`` of kind ``external``. The documentation has no
public repository to pin as a submodule; this script instead replaces the directory with a
snapshot of every page that ``llms.txt`` lists, in Markdown, plus ``llms.txt`` itself and
``SOURCE.json`` recording where and when the snapshot was taken. Commit the result.

Every page is fetched before anything is written, and the snapshot is written into a temporary
directory beside the target and swapped in only once it is complete, so a failed refresh leaves the
previous snapshot as it was. Files of the previous snapshot that the index no longer lists are gone
after a successful refresh.

    python3 scripts/development/fetch-claude-code-docs.py
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "references" / "claude-code"
INDEX = "https://code.claude.com/docs/llms.txt"
PAGE = re.compile(r"\((https://code\.claude\.com/docs/en/([A-Za-z0-9._/-]+\.md))\)")


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "concorde-references"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError, UnicodeDecodeError) as error:
        raise RuntimeError(f"{url}: {error}") from error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.parse_args(argv)
    try:
        index = fetch(INDEX)
    except RuntimeError as error:
        print(f"cannot fetch the documentation index: {error}", file=sys.stderr)
        return 1
    pages = dict.fromkeys(PAGE.findall(index))
    if not pages:
        print(f"{INDEX} lists no page under /docs/en/", file=sys.stderr)
        return 1
    for _, name in pages:
        if ".." in Path(name).parts:
            print(f"{INDEX} lists an unsafe page path: {name}", file=sys.stderr)
            return 1
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(_attempt, [url for url, _ in pages]))
    failures = [message for _, message in results if message]
    if failures:
        print(
            f"{len(failures)} of {len(pages)} pages could not be fetched; "
            f"{TARGET.relative_to(ROOT)} is unchanged:",
            file=sys.stderr,
        )
        for message in failures:
            print(f"  {message}", file=sys.stderr)
        return 1
    source = {
        "index": INDEX,
        "fetched": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pages": [name for _, name in pages],
    }
    try:
        publish(
            index,
            [(name, text) for (_, name), (text, _) in zip(pages, results, strict=True)],
            source,
        )
    except OSError as error:
        print(
            f"cannot write the snapshot: {error}; {TARGET.relative_to(ROOT)} is unchanged",
            file=sys.stderr,
        )
        return 1
    print(f"wrote {len(pages)} pages to {TARGET.relative_to(ROOT)}")
    return 0


def publish(index: str, pages: list[tuple[str, str]], source: dict) -> None:
    """Write the snapshot beside ``TARGET`` and swap it in; on failure ``TARGET`` is unchanged."""
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{TARGET.name}.new-", dir=TARGET.parent))
    previous = staging.with_name(f".{TARGET.name}.old-{staging.name.rsplit('-', 1)[1]}")
    try:
        (staging / "llms.txt").write_text(index, encoding="utf-8")
        for name, text in pages:
            path = staging / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        (staging / "SOURCE.json").write_text(
            json.dumps(source, indent=2) + "\n", encoding="utf-8"
        )
        if TARGET.exists():
            TARGET.rename(previous)
        try:
            staging.rename(TARGET)
        except OSError:
            if previous.exists():
                previous.rename(TARGET)
            raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)
        shutil.rmtree(previous, ignore_errors=True)


def _attempt(url: str) -> tuple[str, str | None]:
    try:
        return fetch(url), None
    except RuntimeError as error:
        return "", str(error)


if __name__ == "__main__":
    sys.exit(main())
