import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.concorde.support.catalog_server import CatalogServer
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.specify_project import SpecifyProject

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts/release"))

import importlib.util

_builder_spec = importlib.util.spec_from_file_location("concorde_release_builder", REPOSITORY_ROOT / "scripts/release/build-components.py")
assert _builder_spec and _builder_spec.loader
_builder = importlib.util.module_from_spec(_builder_spec)
_builder_spec.loader.exec_module(_builder)


class BundleLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.distribution_temporary = tempfile.TemporaryDirectory()
        cls.dist = Path(cls.distribution_temporary.name)
        cls.server = CatalogServer(cls.dist)
        _builder.build_release(cls.dist, cls.server.base_url)
        cls.server.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.server.__exit__(None, None, None)
        cls.distribution_temporary.cleanup()

    def setUp(self):
        _builder.build_release(self.dist, self.server.base_url)
        self.project_temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.project_temporary.name)
        self.project = SpecifyProject(self.root)
        self.project.initialize()
        self.project.register_catalogs(self.server.base_url)
        (self.root / ".concorde").mkdir()
        (self.root / ".concorde/user.json").write_text('{"owned_by":"maintainer"}\n')
        (self.root / "specs/user").mkdir(parents=True)
        (self.root / "specs/user/notes.md").write_text("# Maintained intent\n")
        (self.root / "docs").mkdir()
        (self.root / "docs/user.md").write_text("# Maintained documentation\n")
        unrelated = self.root / ".agents/skills/user-owned/SKILL.md"
        unrelated.parent.mkdir(parents=True)
        unrelated.write_text("---\nname: user-owned\n---\n# User-owned skill\n")

    def tearDown(self):
        self.project_temporary.cleanup()

    def shared_component_fixture(self) -> Path:
        """Render the shared-source fixture against the maintained preset version."""
        source = REPOSITORY_ROOT / "tests/concorde/fixtures/releases/shared-component"
        target = self.root / "shared-component-fixture"
        shutil.copytree(source, target)
        manifest = target / "bundle.yml"
        content = yaml.safe_load(manifest.read_text(encoding="utf-8"))
        presets = content["provides"]["presets"]
        concorde = next(item for item in presets if item["id"] == "concorde")
        concorde["version"] = _builder.read_release_version()
        manifest.write_text(
            yaml.safe_dump(content, sort_keys=False),
            encoding="utf-8",
            newline="\n",
        )
        return target

    def test_preview_install_repeat_and_provenance_match(self):
        preview = self.project.json("bundle", "info", "concorde-bundle", "--json")
        self.assertEqual(preview["version"], "0.8.0")
        self.assertIsNone(preview["integration"])
        self.assertEqual(
            [(item["kind"], item["id"], item["version"]) for item in preview["components"]],
            [("extensions", "concorde", "0.8.0"), ("presets", "concorde", "0.8.0")],
        )
        source_hashes = self.project.source_hashes()
        self.project.run("bundle", "install", "concorde-bundle")
        validated = self.project.run("bundle", "validate", "--offline", "--path", str(REPOSITORY_ROOT / "bundles/concorde-bundle"))
        self.assertIn("valid", validated.stdout.lower())
        for _ in range(3):
            self.project.run("bundle", "install", "concorde-bundle")
        installed = self.project.json("bundle", "list", "--json")
        self.assertEqual(len(installed), 1)
        self.assertEqual(installed[0]["bundle_id"], preview["id"])
        self.assertEqual(
            {(item["kind"], item["id"], item["version"]) for item in installed[0]["contributed_components"]},
            {(item["kind"], item["id"], item["version"]) for item in preview["components"]},
        )
        self.assertEqual(self.project.source_hashes(), source_hashes)
        skills = {path.parent.name for path in (self.root / ".agents/skills").glob("speckit-concorde-*/SKILL.md")}
        self.assertEqual(len(skills), 5)
        self.assertIn("speckit-concorde-deliver", skills)
        self.assertIn("speckit-concorde-ask", skills)
        self.project.run("extension", "disable", "concorde")
        self.assertIn("disabled", self.project.run("extension", "list").stdout.lower())
        self.project.run("extension", "enable", "concorde")
        self.project.run("preset", "disable", "concorde")
        self.assertIn("disabled", self.project.run("preset", "list").stdout.lower())
        self.project.run("preset", "enable", "concorde")

    def test_directory_manifest_and_artifact_install_forms_are_equivalent(self):
        forms = [
            REPOSITORY_ROOT / "bundles/concorde-bundle",
            REPOSITORY_ROOT / "bundles/concorde-bundle/bundle.yml",
            self.dist / "concorde-bundle-0.8.0.zip",
        ]
        expected = None
        for form in forms:
            self.project.run("bundle", "install", str(form))
            installed = self.project.json("bundle", "list", "--json")
            components = installed[0]["contributed_components"]
            normalized = {(item["kind"], item["id"], item["version"]) for item in components}
            expected = expected or normalized
            self.assertEqual(normalized, expected)
            self.project.run("bundle", "remove", "concorde-bundle")

    def test_uninitialized_project_uses_isolated_user_catalogs(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            project_root = base / "new-project"
            project_root.mkdir()
            home = base / "home"
            config = home / ".specify"
            config.mkdir(parents=True)
            (config / "extension-catalogs.yml").write_text(
                f"catalogs:\n- name: concorde-dev\n  url: {self.server.base_url}/extensions.json\n  priority: 10\n  install_allowed: true\n"
            )
            (config / "preset-catalogs.yml").write_text(
                f"catalogs:\n- name: concorde-dev\n  url: {self.server.base_url}/presets.json\n  priority: 10\n  install_allowed: true\n"
            )
            (config / "bundle-catalogs.yml").write_text(
                f"schema_version: '1.0'\ncatalogs:\n- id: concorde-dev\n  url: {self.server.base_url}/bundles.json\n  priority: 10\n  install_policy: install-allowed\n"
            )
            project = SpecifyProject(project_root, home=home)
            project.run("bundle", "init", "concorde-bundle", "--integration", "codex")
            installed = project.json("bundle", "list", "--json")
            self.assertEqual(installed[0]["bundle_id"], "concorde-bundle")
            self.assertTrue((project_root / ".specify/extensions/concorde/extension.yml").is_file())

    def test_unsupported_platform_range_stops_before_installation(self):
        incompatible = self.root / "incompatible"
        shutil.copytree(REPOSITORY_ROOT / "bundles/concorde-bundle", incompatible)
        manifest = incompatible / "bundle.yml"
        manifest.write_text(manifest.read_text().replace(">=0.16.4,<0.16.5", ">=9.0.0,<10.0.0"))
        before = self.project.registry_snapshot()
        result = self.project.run("bundle", "install", str(incompatible), check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("compatible", (result.stdout + result.stderr).lower())
        self.assertEqual(self.project.registry_snapshot(), before)

    def test_failed_update_retains_prior_record_and_sources(self):
        self.project.run("bundle", "install", "concorde-bundle")
        source_hashes = self.project.source_hashes()
        artifacts = _builder.build_release(self.dist, self.server.base_url, "0.3.1")
        extension_names = [name for name in artifacts if name.startswith("concorde-extension-")]
        self.assertEqual(extension_names, ["concorde-extension-0.3.1.zip"])
        extension = self.dist / extension_names[0]
        extension.write_bytes(extension.read_bytes() + b"integrity failure")
        self.project.clear_catalog_caches()
        result = self.project.run("bundle", "update", "concorde-bundle", check=False)
        self.assertNotEqual(result.returncode, 0)
        installed = self.project.json("bundle", "list", "--json")
        self.assertEqual(installed[0]["version"], "0.8.0")
        self.assertNotIn("0.3.1", json.dumps(installed))
        self.assertEqual(self.project.source_hashes(), source_hashes)

    def test_compatible_update_and_remove_preserve_sources(self):
        self.project.run("bundle", "install", "concorde-bundle")
        source_hashes = self.project.source_hashes()
        unrelated_hashes = self.project.source_hashes((".agents/skills/user-owned",))
        _builder.build_release(self.dist, self.server.base_url, "0.3.1")
        self.project.clear_catalog_caches()
        update_plan = self.project.json("bundle", "info", "concorde-bundle", "--json")
        self.assertEqual(update_plan["version"], "0.3.1")
        self.project.run("bundle", "update", "concorde-bundle")
        installed = self.project.json("bundle", "list", "--json")
        self.assertEqual(installed[0]["version"], "0.3.1")
        self.assertEqual(self.project.source_hashes(), source_hashes)
        self.assertEqual(self.project.source_hashes((".agents/skills/user-owned",)), unrelated_hashes)
        self.project.run("bundle", "remove", "concorde-bundle")
        self.assertEqual(self.project.json("bundle", "list", "--json"), [])
        self.assertEqual(self.project.source_hashes(), source_hashes)
        self.assertEqual(self.project.source_hashes((".agents/skills/user-owned",)), unrelated_hashes)

    def test_component_shared_with_another_bundle_is_not_removed(self):
        shared_bundle = self.shared_component_fixture()
        self.project.run("bundle", "install", str(shared_bundle))
        self.project.run("bundle", "install", "concorde-bundle")
        installed = self.project.json("bundle", "list", "--json")
        self.assertEqual({item["bundle_id"] for item in installed}, {"concorde-shared-fixture", "concorde-bundle"})
        self.project.run("bundle", "remove", "concorde-bundle")
        self.assertTrue((self.root / ".specify/presets/concorde/preset.yml").is_file())
        self.assertFalse((self.root / ".specify/extensions/concorde").exists())
        remaining = self.project.json("bundle", "list", "--json")
        self.assertEqual([item["bundle_id"] for item in remaining], ["concorde-shared-fixture"])

    def test_locally_modified_component_is_reported_without_touching_project_sources(self):
        self.project.run("bundle", "install", "concorde-bundle")
        source_hashes = self.project.source_hashes()
        readme = self.root / ".specify/extensions/concorde/README.md"
        readme.write_text(readme.read_text() + "\nLocal maintainer note.\n")
        result = self.project.run("bundle", "remove", "concorde-bundle", check=False)
        self.assertEqual(self.project.source_hashes(), source_hashes)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(readme.exists())
        self.assertEqual(self.project.json("bundle", "list", "--json"), [])


if __name__ == "__main__":
    unittest.main()
