"""Creation-only scaffold publication keeps every file it did not create and removes its own."""

import errno
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.spec.repository import SpecError
from concorde.spec.verification import verifies
from concorde.spec.views import creation

FILES = {"first.json": b"accepted", "nested/second.json": b"accepted"}


class ScaffoldCreationTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    @verifies("scenario.views.scaffold-concurrent-create")
    def test_an_existing_destination_is_kept_and_the_created_files_removed(self):
        (self.root / "nested").mkdir()
        (self.root / "nested/second.json").write_bytes(b"concurrent bytes")
        with self.assertRaises(SpecError) as raised:
            creation.create_files(self.root, FILES)
        self.assertEqual("stale_proposal", raised.exception.code)
        self.assertEqual("nested/second.json", raised.exception.path)
        self.assertFalse((self.root / "first.json").exists())
        self.assertEqual(
            b"concurrent bytes", (self.root / "nested/second.json").read_bytes()
        )

    @verifies("scenario.views.scaffold-concurrent-create")
    def test_a_destination_created_just_before_its_publication_survives(self):
        link = creation.os.link

        def create_first(source, destination):
            # Another process wins the race between every earlier check and the publication.
            if Path(destination) == self.root / "nested/second.json":
                Path(destination).write_bytes(b"concurrent bytes")
            return link(source, destination)

        with patch.object(creation.os, "link", side_effect=create_first):
            with self.assertRaises(SpecError) as raised:
                creation.create_files(self.root, FILES)
        self.assertEqual("stale_proposal", raised.exception.code)
        self.assertFalse((self.root / "first.json").exists())
        self.assertEqual(
            b"concurrent bytes", (self.root / "nested/second.json").read_bytes()
        )
        self.assertEqual([], [p.name for p in self.root.rglob(".concorde-create-*")])

    @verifies("scenario.views.scaffold-concurrent-create")
    def test_a_created_file_another_process_replaced_is_not_removed(self):
        link = creation.os.link

        def replace_first_then_fail(source, destination):
            if Path(destination) == self.root / "nested/second.json":
                # Another process replaces the file this application created first.
                replacement = self.root / "replacement"
                replacement.write_bytes(b"theirs")
                os.replace(replacement, self.root / "first.json")
                raise OSError(errno.EIO, "injected failure", destination)
            return link(source, destination)

        with patch.object(creation.os, "link", side_effect=replace_first_then_fail):
            with self.assertRaises(SpecError) as raised:
                creation.create_files(self.root, FILES)
        self.assertEqual("system_error", raised.exception.code)
        self.assertIn("first.json had been replaced", str(raised.exception))
        self.assertEqual(b"theirs", (self.root / "first.json").read_bytes())
        self.assertFalse((self.root / "nested/second.json").exists())

    @verifies("scenario.views.scaffold-apply")
    def test_a_failed_creation_removes_every_created_file(self):
        link = creation.os.link

        def fail_second(source, destination):
            if Path(destination) == self.root / "nested/second.json":
                raise OSError(errno.EIO, "injected failure", destination)
            return link(source, destination)

        with patch.object(creation.os, "link", side_effect=fail_second):
            with self.assertRaises(SpecError) as raised:
                creation.create_files(self.root, FILES)
        self.assertEqual("system_error", raised.exception.code)
        self.assertEqual("nested/second.json", raised.exception.path)
        self.assertEqual(
            [], [p for p in self.root.rglob("*") if p.is_file()], "no file is left"
        )

    @verifies("scenario.views.scaffold-apply")
    def test_without_hard_links_files_are_still_created_exclusively(self):
        refused = OSError(errno.EPERM, "hard links are not supported")
        with patch.object(creation.os, "link", side_effect=refused):
            created = creation.create_files(self.root, FILES)
        self.assertEqual(sorted(FILES), created)
        for path, data in FILES.items():
            self.assertEqual(data, (self.root / path).read_bytes())
        (self.root / "first.json").unlink()
        with patch.object(creation.os, "link", side_effect=refused):
            with self.assertRaises(SpecError):
                creation.create_files(self.root, FILES)
        self.assertFalse((self.root / "first.json").exists())
        self.assertEqual(b"accepted", (self.root / "nested/second.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
