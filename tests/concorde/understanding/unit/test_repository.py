import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import CONTEXT_PROJECT, RUNTIME_ROOT, TWO_LEVEL_PROJECT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.understanding.repository import (  # noqa: E402
    ProjectRepository,
    RepositoryError,
    attempt_directory_for_feature_id,
    classify_feature_path,
    safe_relative_path,
)


class RepositoryTests(unittest.TestCase):
    def test_discovers_recursive_architectures_and_direct_features_deterministically(self):
        package = ProjectRepository(CONTEXT_PROJECT).load()
        paths = [source.path for source in package.sources]
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(paths, [
            "specs/example/architecture.md",
            "specs/example/features/001-deliver.md",
            "specs/example/modules/api/architecture.md",
            "specs/example/modules/api/features/001-invoke.md",
            "specs/example/modules/api/modules/store/architecture.md",
        ])
        self.assertEqual(paths, [source.path for source in ProjectRepository(CONTEXT_PROJECT).load().sources])

    def test_normalizes_typed_architecture_and_embedded_interfaces(self):
        package = ProjectRepository(VALID_PROJECT).load()
        entity = package.entities["entity.example.api.handler"]
        self.assertEqual((entity.entity_type, entity.owner), ("function", "module.example.api"))
        relationship = next(item for item in package.relationships if item.source_entity == "entity.example.runtime")
        self.assertEqual((relationship.predicate, relationship.target_entity), ("calls", "module.example.api"))
        self.assertEqual(package.interactions["interaction.example.deliver"].interfaces, ("contract.example.workflow",))
        interface = package.interfaces["contract.example.workflow"]
        self.assertEqual(interface.owner, "feature.example.deliver")
        self.assertIn("entity.example.runtime", interface.implementing_entities)
        self.assertRegex(package.source_digest, r"^sha256:[0-9a-f]{64}$")

    def test_profile_seven_features_are_direct_even_when_relationships_form_a_graph(self):
        package = ProjectRepository(TWO_LEVEL_PROJECT).load()
        self.assertEqual(list(package.features), [
            "feature.example.checkout",
            "feature.example.atomic",
            "feature.example.checkout.authorize",
            "feature.example.checkout.confirm",
        ])
        for feature in package.features.values():
            self.assertNotIn("subfeatures", feature.path)
        with self.assertRaisesRegex(RepositoryError, "one direct file"):
            classify_feature_path(
                "specs/example/features/001-checkout/subfeatures/001-authorize.md",
                "specs/example",
            )

    def test_rejects_wrapper_design_and_noncanonical_feature_filenames(self):
        for path in (
            "specs/example/features/001-checkout/design.md",
            "specs/example/features/001-Checkout.md",
            "specs/example/features/checkout.md",
            "specs/example/features/001-checkout.txt",
        ):
            with self.subTest(path=path), self.assertRaises(RepositoryError):
                classify_feature_path(path, "specs/example")

    def test_attempt_files_are_temporal_auxiliary_not_package_sources(self):
        package = ProjectRepository(TWO_LEVEL_PROJECT).load()
        plan = ".concorde/attempts/feature.example.checkout.authorize/plan.md"
        self.assertIn(plan, package.auxiliary)
        self.assertNotIn(plan, [source.path for source in package.sources])
        self.assertFalse(any(path.endswith(("abstract.md", "implementation.md", "contract.md")) for path in package.auxiliary))

    def test_digest_changes_with_architecture_or_feature_file(self):
        baseline = ProjectRepository(VALID_PROJECT).load().source_digest
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            architecture = root / "specs/example/architecture.md"
            architecture.write_text(architecture.read_text(encoding="utf-8") + "\nA reviewed note.\n", encoding="utf-8")
            self.assertNotEqual(ProjectRepository(root).load().source_digest, baseline)

    def test_rejects_absolute_traversal_and_backslash_paths(self):
        for value in ("/tmp/file", "../file", "a/../../file", "a\\b"):
            with self.subTest(value=value), self.assertRaises(RepositoryError):
                safe_relative_path(value)

    def test_attempt_path_uses_one_strict_stable_feature_id_component(self):
        self.assertEqual(
            attempt_directory_for_feature_id("feature.example.checkout.authorize"),
            ".concorde/attempts/feature.example.checkout.authorize",
        )
        for value in (
            "feature.example/escape",
            "feature.example..escape",
            "feature.example-",
            "feature.Example.escape",
            "module.example.escape",
            "../feature.example.escape",
        ):
            with self.subTest(value=value), self.assertRaises(RepositoryError):
                attempt_directory_for_feature_id(value)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_rejects_symlink_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outside = root.parent / "outside-concorde-profile7-test"
            outside.mkdir(exist_ok=True)
            (root / "link").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(RepositoryError):
                ProjectRepository(root).resolve("link/file.md")

    def test_rejects_unsupported_profile_version(self):
        for version in (99, 1, 5, 6):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / ".concorde").mkdir()
                (root / ".concorde/config.json").write_text('{"profile_version":%d,"specification_root":"specs/example","root_module_id":"module.example"}' % version)
                with self.assertRaisesRegex(RepositoryError, "expected profile_version 7"):
                    ProjectRepository(root).load_config()


if __name__ == "__main__":
    unittest.main()
