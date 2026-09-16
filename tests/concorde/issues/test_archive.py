"""Archival preserves historical problem records; it does not decide their status."""
import tempfile
import unittest
from pathlib import Path

from concorde.issues.archive import archive_reflections
from concorde.issues.store import list_issues
from concorde.spec.verification import verifies


class ArchiveTests(unittest.TestCase):
    @verifies("scenario.issues.archive")
    def test_preserves_bytes_and_relative_links_without_creating_issues(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            old = root / ".concorde/reflections"
            (old / "pending").mkdir(parents=True)
            (old / "evidence").mkdir()
            report = b"status: open\n[Evidence](../evidence/check.txt)\nUser comment\n"
            (old / "pending/R-001.md").write_bytes(report)
            (old / "evidence/check.txt").write_bytes(b"historical evidence\n")
            self.assertEqual("archived", archive_reflections(root)["status"])
            archived = root / ".concorde/archive/reflections"
            self.assertEqual(report, (archived / "pending/R-001.md").read_bytes())
            self.assertEqual(b"historical evidence\n", (archived / "evidence/check.txt").read_bytes())
            self.assertFalse(old.exists())
            self.assertEqual([], list_issues(root))
            self.assertEqual("unchanged", archive_reflections(root)["status"])

    @verifies("scenario.issues.archive")
    def test_conflicting_destination_or_symlink_never_discards_either_copy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            old, new = root / ".concorde/reflections", root / ".concorde/archive/reflections"
            old.mkdir(parents=True)
            new.mkdir(parents=True)
            (old / "record").write_text("source")
            (new / "record").write_text("destination")
            with self.assertRaisesRegex(ValueError, "already exists"):
                archive_reflections(root)
            self.assertEqual("source", (old / "record").read_text())
            self.assertEqual("destination", (new / "record").read_text())
            (old / "alias").symlink_to(new / "record")
            with self.assertRaisesRegex(ValueError, "symlink"):
                archive_reflections(root)
