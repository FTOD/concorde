import importlib.util
import json
import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


def _load_script(name: str, module_name: str):
    path = REPOSITORY_ROOT / "scripts/release" / name
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def load_builder():
    return _load_script("build-components.py", "concorde_release_builder")


def load_verifier():
    return _load_script("verify-release.py", "concorde_release_verifier")


class ReleaseArtifactTests(unittest.TestCase):
    def test_two_builds_are_byte_equivalent_and_catalogs_match(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            builder.build_release(Path(first), "http://127.0.0.1:8765")
            builder.build_release(Path(second), "http://127.0.0.1:8765")
            names = ["concorde-core-0.3.0.zip", "concorde-0.3.0.zip", "concorde-bundle-0.3.0.zip"]
            for name in names:
                self.assertEqual((Path(first) / name).read_bytes(), (Path(second) / name).read_bytes())
            self.assertEqual((Path(first) / "presets.json").read_bytes(), (Path(second) / "presets.json").read_bytes())

    def test_default_catalog_urls_are_the_published_release_location(self):
        builder = load_builder()
        version = builder.read_release_version()
        base_url = builder.default_base_url(version)
        self.assertEqual(base_url, f"https://github.com/FTOD/concorde/releases/download/v{version}")
        with tempfile.TemporaryDirectory() as temporary:
            builder.build_release(Path(temporary))
            for name, (collection, identifier) in {
                "extensions.json": ("extensions", "concorde"),
                "presets.json": ("presets", "concorde-core"),
                "bundles.json": ("bundles", "concorde-bundle"),
            }.items():
                text = (Path(temporary) / name).read_text(encoding="utf-8")
                self.assertNotIn('"http://', text)
                catalog = json.loads(text)
                entry = catalog[collection][identifier]
                self.assertEqual(catalog["catalog_url"], f"{base_url}/{name}")
                self.assertTrue(entry["download_url"].startswith(f"{base_url}/"))
                self.assertEqual(entry["repository"], builder.REPOSITORY)
                self.assertEqual(entry["version"], version)

    def test_manifests_share_one_release_version_and_repository(self):
        builder = load_builder()
        identity = builder.read_release_identity()
        self.assertEqual(identity.repository, "https://github.com/FTOD/concorde")
        for relative in (builder.BUNDLE_MANIFEST, builder.PRESET_MANIFEST, builder.EXTENSION_MANIFEST):
            self.assertIn(f'"{identity.version}"', (REPOSITORY_ROOT / relative).read_text(encoding="utf-8"))

        def patched_root(relative: str, old: str, new: str) -> Path:
            root = Path(tempfile.mkdtemp())
            for manifest in (builder.BUNDLE_MANIFEST, builder.PRESET_MANIFEST, builder.EXTENSION_MANIFEST):
                target = root / manifest
                target.parent.mkdir(parents=True, exist_ok=True)
                content = (REPOSITORY_ROOT / manifest).read_text(encoding="utf-8")
                if manifest == relative:
                    self.assertIn(old, content)
                    content = content.replace(old, new, 1)
                target.write_text(content, encoding="utf-8")
            return root

        with self.assertRaisesRegex(builder.ReleaseIdentityError, "version disagreement.*preset.version declares 9.9.9"):
            builder.read_release_identity(patched_root(builder.PRESET_MANIFEST, f'version: "{identity.version}"', 'version: "9.9.9"'))
        with self.assertRaisesRegex(builder.ReleaseIdentityError, "repository disagreement"):
            builder.read_release_identity(
                patched_root(builder.EXTENSION_MANIFEST, builder.REPOSITORY, "https://github.com/someone-else/concorde")
            )

    def test_verifier_rejects_wrong_version_or_base_url(self):
        builder = load_builder()
        verifier = load_verifier()
        version = builder.read_release_version()
        base_url = builder.default_base_url(version)
        with tempfile.TemporaryDirectory() as temporary:
            builder.build_release(Path(temporary))
            verified = verifier.verify_release(Path(temporary), expect_version=version, expect_base_url=base_url)
            self.assertEqual(set(verified), {
                f"concorde-core-{version}.zip", f"concorde-{version}.zip", f"concorde-bundle-{version}.zip",
            })
            with self.assertRaisesRegex(ValueError, "expected release version 9.9.9"):
                verifier.verify_release(Path(temporary), expect_version="9.9.9")
            with self.assertRaisesRegex(ValueError, "download_url .* is not https://example.invalid/releases/"):
                verifier.verify_release(Path(temporary), expect_base_url="https://example.invalid/releases")

    def test_catalog_capability_counts_match_component_manifests(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            builder.build_release(output)
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
                "commands": 5,
                "scripts": 4,
            })

    def test_archives_match_explicit_allowlists_and_installed_handoff(self):
        builder = load_builder()
        sources = {
            "concorde-core-0.3.0.zip": ("concorde-core", REPOSITORY_ROOT / "presets/concorde-core"),
            "concorde-0.3.0.zip": ("concorde", REPOSITORY_ROOT / "extensions/concorde"),
            "concorde-bundle-0.3.0.zip": ("concorde-bundle", REPOSITORY_ROOT / "bundles/concorde-bundle"),
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

            with zipfile.ZipFile(output / "concorde-core-0.3.0.zip") as preset_archive:
                command_members = sorted(
                    name for name in preset_archive.namelist() if name.startswith("commands/")
                )
                self.assertEqual(len(command_members), 9)
                self.assertTrue(all(b"Concorde Installed Workspace Gate" in preset_archive.read(name) for name in command_members))

            with zipfile.ZipFile(output / "concorde-0.3.0.zip") as extension_archive:
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
