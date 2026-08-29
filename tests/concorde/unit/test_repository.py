import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import CONTEXT_PROJECT, RUNTIME_ROOT, TWO_LEVEL_PROJECT, VALID_PROJECT

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

    def test_discovers_exactly_two_feature_levels(self):
        package = ProjectRepository(TWO_LEVEL_PROJECT).load()
        self.assertEqual(
            [item.identifier for item in package.documents("feature")],
            [
                "feature.example.checkout",
                "feature.example.checkout.authorize",
                "feature.example.checkout.confirm",
                "feature.example.atomic",
            ],
        )

    def test_rejects_third_feature_level_instead_of_ignoring_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(TWO_LEVEL_PROJECT, root)
            third = root / "specs/example/features/001-checkout/subfeatures/001-authorize-payment/subfeatures/001-retry"
            third.mkdir(parents=True)
            (third / "design.md").write_text("---\nid: feature.example.retry\nkind: feature\n---\n# Retry\n", encoding="utf-8")
            with self.assertRaisesRegex(RepositoryError, "must be features"):
                ProjectRepository(root).load()

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
        for version in (99, 1, 3):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / ".concorde").mkdir()
                (root / ".concorde/config.json").write_text(
                    '{"profile_version":%d,"specification_root":"specs/example","root_module_id":"module.example"}' % version
                )
                with self.assertRaisesRegex(RepositoryError, "expected profile_version 4"):
                    ProjectRepository(root).load_config()

    def test_discovers_module_and_feature_implementation_references_and_abstracts_as_durable_auxiliary(self):
        package = ProjectRepository(VALID_PROJECT).load()
        self.assertIn("specs/example/design.md", package.auxiliary)
        self.assertIn("specs/example/architecture/modules/api/design.md", package.auxiliary)
        self.assertIn("specs/example/features/001-deliver/implementation.md", package.auxiliary)
        self.assertIn("specs/example/features/001-deliver/abstract.md", package.auxiliary)
        self.assertNotIn("specs/example/features/001-deliver/attempt/plan.md", package.auxiliary)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            (root / "specs/example/design.md").write_text("# Design Reference: Example\n\n## Decision Log\n\n- changed\n", encoding="utf-8")
            self.assertNotEqual(ProjectRepository(root).load().source_digest, package.source_digest)

    def test_rejects_declared_feature_diagram_outside_diagrams_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, root)
            feature_root = root / "specs/example/features/001-deliver"
            source = feature_root / "design.md"
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "specs/example/features/001-deliver/diagrams/delivery-sequence.json",
                    "specs/example/features/001-deliver/delivery-sequence.json",
                ),
                encoding="utf-8",
            )
            shutil.copyfile(feature_root / "diagrams/delivery-sequence.json", feature_root / "delivery-sequence.json")
            with self.assertRaisesRegex(RepositoryError, "directly under diagrams"):
                ProjectRepository(root).load()

    def test_rejects_sequence_diagram_as_feature_core(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, root)
            source = root / "specs/example/features/001-deliver/design.md"
            source.write_text(
                source.read_text(encoding="utf-8").replace("role: supplemental", "role: core"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RepositoryError, "core feature diagram must use the architecture kind"):
                ProjectRepository(root).load()


if __name__ == "__main__":
    unittest.main()
