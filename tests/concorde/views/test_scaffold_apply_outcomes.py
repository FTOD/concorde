"""Applying a docsite scaffold proposal twice, and while another process creates a destination."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from concorde.distribution.cli import main
from concorde.distribution.project_defaults import install_project_defaults
from concorde.spec import changes
from concorde.spec.initialize import apply_project_proposal, project_proposal
from concorde.spec.verification import verifies
from concorde.views import docsite_scaffold
from concorde.views.docsite_scaffold import propose_docsite
from tests.concorde.support.paths import REPOSITORY_ROOT

PROPOSAL = ".concorde/docsite-proposal.json"


def tree(root: Path) -> dict[str, tuple[bytes, int, int]]:
    """Every file with its bytes, inode and modification time."""
    return {
        path.relative_to(root).as_posix(): (
            path.read_bytes(),
            path.stat().st_ino,
            path.stat().st_mtime_ns,
        )
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class ScaffoldApplyOutcomeTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        install_project_defaults(self.root, REPOSITORY_ROOT)
        apply_project_proposal(
            self.root,
            REPOSITORY_ROOT,
            project_proposal(self.root, REPOSITORY_ROOT, "Atlas", "module.atlas"),
        )
        proposed = propose_docsite(self.root)
        self.assertEqual("proposal", proposed.status, proposed.findings)
        self.files = [item["path"] for item in proposed.result["proposal"]["files"]]
        (self.root / PROPOSAL).write_text(json.dumps(proposed.result), "utf-8")

    def apply(self) -> dict:
        """Run ``concorde.py docsite --apply --proposal PATH`` and return its JSON result."""
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main(
                [
                    "--project-root",
                    str(self.root),
                    "docsite",
                    "--apply",
                    "--proposal",
                    PROPOSAL,
                ]
            )
        return json.loads(buffer.getvalue())

    @verifies("scenario.views.scaffold-apply-repeat")
    def test_applying_an_applied_proposal_is_unchanged_and_writes_nothing(self):
        first = self.apply()
        self.assertEqual("success", first["status"], first)
        before = tree(self.root)
        with mock.patch.object(
            docsite_scaffold,
            "apply_files",
            side_effect=AssertionError("an unchanged apply must not write"),
        ):
            repeated = self.apply()
        self.assertEqual("unchanged", repeated["status"], repeated)
        self.assertEqual(before, tree(self.root))

    @verifies("scenario.views.scaffold-concurrent-create")
    def test_a_destination_created_during_apply_fails_and_removes_only_our_files(
        self,
    ):
        self.assertGreater(len(self.files), 2)
        ordered = sorted(self.files)
        first, contested = ordered[0], ordered[-1]
        spec = self.root / "specs/project/module.md"
        untouched = tree(self.root)
        replace = changes.os.replace

        def concurrent_create(source, destination):
            replace(source, destination)
            if Path(destination) == self.root / first:
                # Another process creates a later destination once applying has started.
                target = self.root / contested
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"created by another process\n")

        with mock.patch.object(changes.os, "replace", side_effect=concurrent_create):
            result = self.apply()
        self.assertEqual("failed", result["status"], result)
        self.assertEqual(
            b"created by another process\n", (self.root / contested).read_bytes()
        )
        for path in ordered[:-1]:
            self.assertFalse((self.root / path).exists(), path)
        after = tree(self.root)
        self.assertEqual(
            {path: value[0] for path, value in untouched.items()},
            {path: value[0] for path, value in after.items() if path != contested},
        )
        self.assertTrue(spec.is_file())


if __name__ == "__main__":
    unittest.main()
