import os
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.repository import ProjectRepository, RepositoryError, safe_relative_path  # noqa: E402


class RepositoryTests(unittest.TestCase):
    def test_discovers_sources_in_deterministic_order(self):
        repository = ProjectRepository(VALID_PROJECT)
        first = [source.path for source in repository.load().sources]
        second = [source.path for source in repository.load().sources]
        self.assertEqual(first, sorted(first))
        self.assertEqual(first, second)

    def test_indexes_stable_ids_and_source_digest(self):
        package = ProjectRepository(VALID_PROJECT).load()
        self.assertEqual(package.by_id["module.example"][0].kind, "module")
        self.assertEqual(len(package.source_digest), len("sha256:") + 64)

    def test_rejects_absolute_traversal_and_backslash_paths(self):
        for value in ("/tmp/file", "../file", "a/../../file", "a\\b"):
            with self.subTest(value=value), self.assertRaises(RepositoryError):
                safe_relative_path(value)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_rejects_symlink_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outside = root.parent / "outside-concorde-test"
            outside.mkdir(exist_ok=True)
            (root / "link").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(RepositoryError):
                ProjectRepository(root).resolve("link/file.md")

    def test_rejects_unsupported_profile_version(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".concorde").mkdir()
            (root / ".concorde/config.json").write_text(
                '{"profile_version":99,"specification_root":"specs/example","root_module_id":"module.example"}'
            )
            with self.assertRaisesRegex(RepositoryError, "unsupported"):
                ProjectRepository(root).load_config()


if __name__ == "__main__":
    unittest.main()
