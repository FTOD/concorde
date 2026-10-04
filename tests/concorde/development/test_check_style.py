"""The style check of the prompts measures any Markdown with Spec core's style checks."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from concorde.spec.style import style_problems
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT

SCRIPT = REPOSITORY_ROOT / "scripts/development/check-style.py"
LONG = " ".join(["word"] * 36)


def check(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


class CheckStyleTests(unittest.TestCase):
    @verifies("scenario.concorde.check-style")
    def test_problems_and_counts_are_those_of_spec_core(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "nested").mkdir()
            prompt = root / "nested/prompt.md"
            prompt.write_text(
                "---\naudience: worker\n---\n\n"
                f"A {LONG} end.\n\n"
                "Read the brief; then act.\n\n"
                "- You MUST report and MAY stop.\n"
            )
            (root / "clean.md").write_text("# Clean\n\nOne short sentence.\n")
            expected = [
                {
                    "path": prompt.as_posix(),
                    "line": item.line,
                    "rule": item.check,
                    "message": item.message,
                }
                for item in style_problems(prompt.read_text())
            ]
            self.assertEqual(
                [
                    ("CHK.style.sentence-length", 5),
                    ("CHK.style.semicolon", 7),
                    ("CHK.style.one-obligation", 9),
                ],
                [(item["rule"], item["line"]) for item in expected],
            )

            found = check(str(root), "--format", "json")
            self.assertEqual(1, found.returncode, found.stderr)
            self.assertEqual(
                {
                    "counts": {
                        "CHK.style.sentence-length": 1,
                        "CHK.style.semicolon": 1,
                        "CHK.style.one-obligation": 1,
                    },
                    "files": {prompt.as_posix(): 3},
                    "problems": expected,
                },
                json.loads(found.stdout),
            )

            text = check(str(prompt))
            self.assertEqual(1, text.returncode)
            self.assertIn(f"{prompt.as_posix()}:7: CHK.style.semicolon: ", text.stdout)
            self.assertIn("CHK.style.one-obligation: 1", text.stdout)

            self.assertEqual(0, check(str(root / "clean.md")).returncode)
