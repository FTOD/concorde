from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


def _load(name: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, REPOSITORY_ROOT / "scripts/release" / name)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


builder = _load("build-release.py", "concorde_release_builder_contract")
verifier = _load("verify-release.py", "concorde_release_verifier_contract")


class ReleaseArtifactContractTests(unittest.TestCase):
    def test_build_is_byte_reproducible(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            base = "https://example.test/releases/v1.1.0"
            one = builder.build_release(Path(first), base)
            two = builder.build_release(Path(second), base)
            self.assertEqual(one, two)
            for name in ("concorde-1.1.0.zip", "release.json"):
                self.assertEqual((Path(first) / name).read_bytes(), (Path(second) / name).read_bytes())

    def test_release_pointer_binds_one_archive_identity_and_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            builder.build_release(output, "https://example.test/v1.1.0")
            pointer = json.loads((output / "release.json").read_text())
            self.assertEqual(pointer["schema_version"], 1)
            self.assertEqual((pointer["version"], pointer["tag"]), ("1.1.0", "v1.1.0"))
            self.assertEqual((pointer["architecture_profile"], pointer["workspace_protocol"]), (7, 12))
            self.assertEqual(pointer["archive"]["name"], "concorde-1.1.0.zip")
            digest = "sha256:" + hashlib.sha256((output / pointer["archive"]["name"]).read_bytes()).hexdigest()
            self.assertEqual(pointer["archive"]["sha256"], digest)
            for removed in ("catalogs", "bundle_id", "speckit_version"):
                self.assertNotIn(removed, pointer)

    def test_archive_has_single_safe_root_and_required_native_members(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            builder.build_release(output)
            with zipfile.ZipFile(output / "concorde-1.1.0.zip") as archive:
                names = archive.namelist()
                self.assertEqual(len(names), len(set(names)))
                self.assertTrue(all(name.startswith("concorde/") for name in names))
                for required in (
                    "concorde/concorde.json",
                    "concorde/LICENSE",
                    "concorde/scripts/install-concorde.py",
                    "concorde/src/concorde/alignment.py",
                    "concorde/src/concorde/cli.py",
                    "concorde/commands/speckit.constitution.md",
                    "concorde/templates/feature-template.md",
                    "concorde/agent-assets/reflections/manifest.json",
                ):
                    self.assertIn(required, names)
                self.assertEqual(archive.read("concorde/concorde.json"), (REPOSITORY_ROOT / "concorde.json").read_bytes())
                self.assertFalse(any("/.specify/" in f"/{name}" for name in names))
                self.assertFalse(any(name.startswith(("concorde/presets/", "concorde/extensions/", "concorde/bundles/")) for name in names))

    def test_archive_embeds_manifest_command_and_template_inventory(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            builder.build_release(output)
            with zipfile.ZipFile(output / "concorde-1.1.0.zip") as archive:
                manifest = json.loads(archive.read("concorde/concorde.json"))
                commands = sorted(Path(name).stem for name in archive.namelist() if name.startswith("concorde/commands/") and name.endswith(".md"))
                templates = sorted(Path(name).name for name in archive.namelist() if name.startswith("concorde/templates/") and name.endswith(".md"))
                self.assertEqual(sorted(manifest["commands"]), commands)
                self.assertEqual(sorted(manifest["templates"]), templates)

    def test_verifier_installs_and_rebuilds_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            base = "https://example.test/v1.1.0"
            built = builder.build_release(output, base)
            verified = verifier.verify_release(output, "1.1.0", base)
            self.assertEqual(verified, built)

    def test_verifier_rejects_digest_protocol_and_archive_corruption(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            base = "https://example.test/v1.1.0"
            builder.build_release(output, base)
            pointer_path = output / "release.json"
            pointer = json.loads(pointer_path.read_text())
            pointer["workspace_protocol"] = 11
            pointer_path.write_text(json.dumps(pointer))
            with self.assertRaisesRegex(ValueError, "workspace_protocol"):
                verifier.verify_release(output, "1.1.0", base)
            builder.build_release(output, base)
            archive = output / "concorde-1.1.0.zip"
            archive.write_bytes(archive.read_bytes() + b"corrupt")
            with self.assertRaisesRegex(ValueError, "digest"):
                verifier.verify_release(output, "1.1.0", base)

    def test_release_identity_rejects_wrong_repository_profile_or_protocol(self):
        original = json.loads((REPOSITORY_ROOT / "concorde.json").read_text())
        for field, value in (("repository", "https://example.test/other"), ("architecture_profile", 6), ("workspace_protocol", 11)):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                altered = {**original, field: value}
                (root / "concorde.json").write_text(json.dumps(altered))
                with self.assertRaises(builder.ReleaseIdentityError):
                    builder.read_release_identity(root)


if __name__ == "__main__":
    unittest.main()
