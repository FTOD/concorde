"""Creation-only scaffold transactions retain concurrent files and recover prior writes."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.spec import changes
from concorde.spec.verification import verifies


class ScaffoldCreationTests(unittest.TestCase):
    @verifies("scenario.views.scaffold-stale-rejected")
    def test_null_before_digest_rejects_existing_destination_before_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "second.json").write_bytes(b"concurrent bytes")
            proposal = [{"path": name, "before_digest": None, "content": "accepted"}
                        for name in ("first.json", "second.json")]
            with self.assertRaises(changes.SpecError):
                changes.apply_files(root, proposal, {item["path"] for item in proposal})
            self.assertFalse((root / "first.json").exists())
            self.assertEqual((root / "second.json").read_bytes(), b"concurrent bytes")

    @verifies("scenario.views.scaffold-stale-rejected", "scenario.views.scaffold-apply")
    def test_concurrent_creation_after_first_write_rolls_back_only_our_created_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            proposal = [{"path": name, "before_digest": None, "content": "accepted"}
                        for name in ("first.json", "second.json")]
            replace = changes.os.replace

            def concurrent_create(source, destination):
                replace(source, destination)
                if destination == root / "first.json":
                    (root / "second.json").write_bytes(b"concurrent bytes")

            with patch.object(changes.os, "replace", side_effect=concurrent_create):
                with self.assertRaises(changes.SpecError):
                    changes.apply_files(root, proposal, {item["path"] for item in proposal})
            self.assertFalse((root / "first.json").exists())
            self.assertEqual((root / "second.json").read_bytes(), b"concurrent bytes")

    @verifies("scenario.views.scaffold-apply")
    def test_failed_second_write_recovers_created_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            proposal = [{"path": name, "before_digest": None, "content": "accepted"}
                        for name in ("first.json", "second.json")]
            replace = changes.os.replace

            def fail_second(source, destination):
                if destination == root / "second.json":
                    raise OSError("injected staging failure")
                replace(source, destination)

            with patch.object(changes.os, "replace", side_effect=fail_second):
                with self.assertRaises(OSError):
                    changes.apply_files(root, proposal, {item["path"] for item in proposal})
            self.assertEqual(list(root.iterdir()), [])
