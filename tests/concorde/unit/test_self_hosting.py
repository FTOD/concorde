import json
import tempfile
import unittest
from pathlib import Path

from tests.concorde.self_hosting_support import initialize_checkout, load_self_hosting


self_host = load_self_hosting()


class SelfHostingUnitTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        initialize_checkout(self.root)

    def tearDown(self):
        self.temporary.cleanup()

    def test_source_model_is_complete_ordered_and_deterministic(self):
        components, first, integration = self_host.component_model(self.root)
        self.assertEqual([item["kind"] for item in components], ["preset", "extension", "bundle"])
        self.assertEqual([item["id"] for item in components], ["concorde", "concorde", "concorde-bundle"])
        self.assertEqual(integration, "codex")
        self.assertEqual(first, self_host.component_model(self.root)[1])

    def test_source_change_changes_digest(self):
        before = self_host.component_model(self.root)[1]
        readme = self.root / "extensions/concorde/README.md"
        readme.write_text(readme.read_text() + "\nobservable change\n")
        self.assertNotEqual(before, self_host.component_model(self.root)[1])

    def test_source_model_qualifies_same_id_bundle_pins_by_component_type(self):
        bundle = self.root / "bundles/concorde-bundle/bundle.yml"
        text = bundle.read_text(encoding="utf-8")
        preset_section = '  presets:\n    - id: "concorde"'
        self.assertIn(preset_section, text)
        bundle.write_text(text.replace(preset_section, '  presets:\n    - id: "missing"', 1), encoding="utf-8")
        with self.assertRaises(self_host.SelfHostError) as raised:
            self_host.component_model(self.root)
        self.assertEqual(raised.exception.finding["code"], "CONCORDE-SELF-HOST-008")

    def test_path_boundary_rejects_absolute_parent_backslash_and_symlink(self):
        for unsafe in ("/tmp/x", "../x", "a/../x", "a\\b", "a/"):
            with self.assertRaises(ValueError, msg=unsafe):
                self_host.safe_relative(unsafe)
        (self.root / "outside").mkdir()
        (self.root / "linked").symlink_to(self.root / "outside", target_is_directory=True)
        with self.assertRaises(ValueError):
            self_host.resolve_project_path(self.root, "linked/file")

    def test_source_inventory_rejects_symlinks(self):
        (self.root / "presets/concorde/linked").symlink_to(self.root / "bundles/concorde-bundle")
        with self.assertRaises(self_host.SelfHostError) as raised:
            self_host.component_model(self.root)
        self.assertEqual(raised.exception.finding["code"], "CONCORDE-SELF-HOST-002")

    def test_unsupported_host_and_integration_are_actionable(self):
        path = self.root / ".specify/integration.json"
        data = json.loads(path.read_text())
        data["version"] = "0.17.0"
        path.write_text(json.dumps(data))
        with self.assertRaises(self_host.SelfHostError) as raised:
            self_host.integration_state(self.root)
        self.assertEqual(raised.exception.finding["code"], "CONCORDE-SELF-HOST-006")

    def test_absent_status_is_read_only_and_activation_unknown(self):
        before = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result = self_host.status(self.root)
        after = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(result["status"], "absent")
        self.assertEqual(result["dimensions"]["activation"]["status"], "unknown")
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
