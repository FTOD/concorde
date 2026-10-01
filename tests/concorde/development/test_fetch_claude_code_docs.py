"""The documentation fetcher publishes a complete snapshot or leaves the previous one untouched."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT

INDEX = """# Claude Code

- [Overview](https://code.claude.com/docs/en/overview.md): what it is
- [Hooks](https://code.claude.com/docs/en/agent-sdk/hooks.md): hooks
"""
PAGES = {
    "https://code.claude.com/docs/en/overview.md": "# Overview\n",
    "https://code.claude.com/docs/en/agent-sdk/hooks.md": "# Hooks\n",
}
PREVIOUS = {
    "llms.txt": "old index\n",
    "overview.md": "# Old overview\n",
    "retired.md": "# Retired\n",
    "SOURCE.json": '{"pages": ["overview.md", "retired.md"]}\n',
}


def load_fetcher():
    spec = importlib.util.spec_from_file_location(
        "fetch_claude_code_docs",
        REPOSITORY_ROOT / "scripts/development/fetch-claude-code-docs.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot(directory: Path) -> dict[str, str]:
    return {
        str(path.relative_to(directory)): path.read_text()
        for path in directory.rglob("*")
        if path.is_file()
    }


class FetchClaudeCodeDocsTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.fetcher = load_fetcher()
        self.fetcher.ROOT = self.root
        self.fetcher.TARGET = self.root / "references/claude-code"
        self.target = self.fetcher.TARGET
        for name, content in PREVIOUS.items():
            path = self.target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)

    def run_fetcher(self, pages: dict[str, str]) -> tuple[int, str]:
        def fetch(url):
            if url == self.fetcher.INDEX:
                return INDEX
            if url not in pages:
                raise RuntimeError(f"{url}: HTTP Error 404: Not Found")
            return pages[url]

        stderr = io.StringIO()
        with (
            patch.object(self.fetcher, "fetch", fetch),
            contextlib.redirect_stderr(stderr),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            status = self.fetcher.main([])
        return status, stderr.getvalue()

    def assert_no_leftovers(self):
        self.assertEqual(
            ["claude-code"], sorted(p.name for p in self.target.parent.iterdir())
        )

    @verifies("scenario.concorde.docs-refresh-replaces")
    def test_refresh_replaces_the_snapshot_whole(self):
        status, stderr = self.run_fetcher(PAGES)
        self.assertEqual(status, 0, stderr)
        files = snapshot(self.target)
        self.assertEqual(
            {"llms.txt", "overview.md", "agent-sdk/hooks.md", "SOURCE.json"}, set(files)
        )
        self.assertEqual(files["overview.md"], "# Overview\n")
        self.assertEqual(files["llms.txt"], INDEX)
        source = json.loads(files["SOURCE.json"])
        self.assertEqual(source["index"], self.fetcher.INDEX)
        self.assertEqual(source["pages"], ["overview.md", "agent-sdk/hooks.md"])
        self.assertRegex(source["fetched"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assert_no_leftovers()

    @verifies("scenario.concorde.docs-refresh-failed-unchanged")
    def test_failed_refresh_leaves_the_snapshot_as_it_was(self):
        page = "https://code.claude.com/docs/en/agent-sdk/hooks.md"
        write_text = Path.write_text
        rename = Path.rename

        def failing_write(path, *arguments, **keywords):
            if path.name == "hooks.md":
                raise OSError(28, "No space left on device")
            return write_text(path, *arguments, **keywords)

        def failing_swap(path, destination):
            if Path(destination) == self.target and path.name.startswith(
                ".claude-code.new-"
            ):
                raise OSError(16, "Device or resource busy")
            return rename(path, destination)

        cases = {
            "fetch": (
                {url: text for url, text in PAGES.items() if url != page},
                None,
                page,
            ),
            "write": (
                PAGES,
                patch.object(Path, "write_text", failing_write),
                "No space left",
            ),
            "swap": (
                PAGES,
                patch.object(Path, "rename", failing_swap),
                "resource busy",
            ),
        }
        for case, (pages, failure, message) in cases.items():
            with self.subTest(case=case):
                with failure or contextlib.nullcontext():
                    status, stderr = self.run_fetcher(pages)
                self.assertEqual(status, 1)
                self.assertIn(message, stderr)
                self.assertIn("references/claude-code is unchanged", stderr)
                self.assertEqual(PREVIOUS, snapshot(self.target))
                self.assert_no_leftovers()


if __name__ == "__main__":
    unittest.main()
