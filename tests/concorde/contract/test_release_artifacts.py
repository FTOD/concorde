import importlib.util
import json
import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


def load_builder():
    path = REPOSITORY_ROOT / "scripts/release/build-components.py"
    spec = importlib.util.spec_from_file_location("concorde_release_builder", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class ReleaseArtifactTests(unittest.TestCase):
    def test_two_builds_are_byte_equivalent_and_catalogs_match(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            builder.build_release(Path(first), "http://127.0.0.1:8765")
            builder.build_release(Path(second), "http://127.0.0.1:8765")
            names = ["concorde-core-0.1.0.zip", "concorde-0.1.0.zip", "concorde-bundle-0.1.0.zip"]
            for name in names:
                self.assertEqual((Path(first) / name).read_bytes(), (Path(second) / name).read_bytes())
            self.assertEqual((Path(first) / "presets.json").read_bytes(), (Path(second) / "presets.json").read_bytes())

    def test_default_catalog_urls_are_https(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as temporary:
            builder.build_release(Path(temporary), builder.DEFAULT_BASE_URL)
            for name in ("extensions.json", "presets.json", "bundles.json"):
                self.assertNotIn('"http://', (Path(temporary) / name).read_text())
                self.assertEqual(
                    json.loads((Path(temporary) / name).read_text()),
                    json.loads((REPOSITORY_ROOT / "catalogs" / name).read_text()),
                )

    def test_catalog_capability_counts_match_component_manifests(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            builder.build_release(output, builder.DEFAULT_BASE_URL)
            preset_catalog = json.loads((output / "presets.json").read_text(encoding="utf-8"))
            extension_catalog = json.loads((output / "extensions.json").read_text(encoding="utf-8"))
            preset_manifest = (REPOSITORY_ROOT / "presets/concorde-core/preset.yml").read_text(
                encoding="utf-8"
            )
            extension_manifest = (REPOSITORY_ROOT / "extensions/concorde/extension.yml").read_text(
                encoding="utf-8"
            )

            self.assertEqual(
                preset_catalog["presets"]["concorde-core"]["provides"],
                {
                    "templates": preset_manifest.count('type: "template"'),
                    "commands": preset_manifest.count('type: "command"'),
                },
            )
            self.assertEqual(
                extension_catalog["extensions"]["concorde"]["provides"]["commands"],
                extension_manifest.count('- name: "speckit.concorde.'),
            )
            self.assertEqual(extension_catalog["extensions"]["concorde"]["provides"], {
                "commands": 7,
                "scripts": 4,
            })

    def test_archives_match_explicit_allowlists_and_installed_handoff(self):
        builder = load_builder()
        sources = {
            "concorde-core-0.1.0.zip": ("concorde-core", REPOSITORY_ROOT / "presets/concorde-core"),
            "concorde-0.1.0.zip": ("concorde", REPOSITORY_ROOT / "extensions/concorde"),
            "concorde-bundle-0.1.0.zip": ("concorde-bundle", REPOSITORY_ROOT / "bundles/concorde-bundle"),
        }
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            builder.build_release(output, "http://127.0.0.1:8765")
            for archive_name, (component, source) in sources.items():
                expected = {
                    path.relative_to(source).as_posix()
                    for path in builder._source_files(source, component)
                }
                with zipfile.ZipFile(output / archive_name) as archive:
                    self.assertEqual(set(archive.namelist()), expected)

            with zipfile.ZipFile(output / "concorde-core-0.1.0.zip") as preset_archive:
                command_members = sorted(
                    name for name in preset_archive.namelist() if name.startswith("commands/")
                )
                self.assertEqual(len(command_members), 9)
                self.assertTrue(all(b"Concorde Installed Workspace Gate" in preset_archive.read(name) for name in command_members))

            with zipfile.ZipFile(output / "concorde-0.1.0.zip") as extension_archive:
                handoff_members = sorted(
                    name
                    for name in extension_archive.namelist()
                    if name.startswith(("commands/", "scripts/", "runtime/", "schemas/"))
                )
                digest = hashlib.sha256()
                for name in handoff_members:
                    digest.update(name.encode("utf-8"))
                    digest.update(b"\0")
                    digest.update(extension_archive.read(name))
                    digest.update(b"\0")
                self.assertEqual(len(digest.hexdigest()), 64)
                self.assertIn("scripts/python/workspace.py", handoff_members)
                self.assertIn("commands/speckit.concorde.ask.md", handoff_members)
                self.assertNotIn(".agents/", "\n".join(handoff_members))


if __name__ == "__main__":
    unittest.main()
