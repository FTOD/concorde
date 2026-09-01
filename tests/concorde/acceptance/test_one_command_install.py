from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import re
import socket
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from tests.concorde.support.catalog_server import CatalogServer
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.specify_project import SpecifyProject


INSTALLER_PATH = REPOSITORY_ROOT / "scripts/install-concorde.py"
SPEC = importlib.util.spec_from_file_location("concorde_installer_acceptance", INSTALLER_PATH)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)

BUILDER_SPEC = importlib.util.spec_from_file_location(
    "concorde_release_builder_for_installer",
    REPOSITORY_ROOT / "scripts/release/build-components.py",
)
assert BUILDER_SPEC and BUILDER_SPEC.loader
builder = importlib.util.module_from_spec(BUILDER_SPEC)
BUILDER_SPEC.loader.exec_module(builder)


def _release(server: CatalogServer, version: str = "0.6.0") -> installer.ReleaseDescriptor:
    return installer.validate_release_pointer(
        {
            "schema_version": "1.0",
            "version": version,
            "tag": f"v{version}",
            "speckit_version": ">=0.16.4,<0.16.5",
            "bundle_id": "concorde-bundle",
            "catalogs": {
                "extensions": f"{server.base_url}/extensions.json",
                "presets": f"{server.base_url}/presets.json",
                "bundles": f"{server.base_url}/bundles.json",
            },
        },
        expected_version=version,
        allow_local=True,
        source=f"{server.base_url}/release.json",
    )


def _installed_snapshot(root: Path) -> dict[str, object]:
    project = SpecifyProject(root)
    bundles = project.json("bundle", "list", "--json")
    normalized = [
        {
            "bundle_id": item["bundle_id"],
            "version": item["version"],
            "components": sorted(
                (component["kind"], component["id"], component["version"])
                for component in item["contributed_components"]
            ),
        }
        for item in bundles
    ]
    files: dict[str, str] = {}
    for relative_root in (
        ".agents/skills",
        ".claude/skills/reflections-triage",
        ".claude/agents",
        ".codex/agents",
        ".specify/extensions/concorde",
        ".specify/presets/concorde",
    ):
        source = root / relative_root
        for path in sorted(source.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    for relative in (
        ".concorde/reflections/config.json",
        ".concorde/reflections/.gitignore",
        ".specify/concorde-agent-assets.json",
    ):
        path = root / relative
        if path.is_file():
            files[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"bundles": normalized, "files": files}


def _all_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class OneCommandInstallAcceptanceTests(unittest.TestCase):
    def test_fresh_target_matches_manual_native_lifecycle(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            dist = base / "dist"
            with CatalogServer(dist) as server:
                builder.build_release(dist, server.base_url)
                release = _release(server)

                manual_root = base / "manual"
                manual = SpecifyProject(manual_root, integration="codex", skills=True)
                manual.initialize()
                manual.run(
                    "extension", "catalog", "add", release.catalogs["extensions"],
                    "--name", "concorde", "--install-allowed",
                )
                manual.run(
                    "preset", "catalog", "add", release.catalogs["presets"],
                    "--name", "concorde", "--install-allowed",
                )
                manual.run(
                    "bundle", "catalog", "add", release.catalogs["bundles"],
                    "--id", "concorde", "--policy", "install-allowed",
                )
                manual.run("bundle", "info", "concorde-bundle", "--json")
                manual.run("bundle", "install", "concorde-bundle")
                installer.run_agent_assets(manual_root, "codex", "sync", release.version)
                installer.run_agent_assets(manual_root, "codex", "verify", release.version)

                installer_root = base / "installer"
                installer_root.mkdir()
                with mock.patch.object(installer, "fetch_release", return_value=release):
                    result = installer.main(
                        ["--target", str(installer_root), "--integration", "codex"]
                    )
                self.assertEqual(result, installer.EXIT_OK)
                self.assertEqual(_installed_snapshot(installer_root), _installed_snapshot(manual_root))
                self.assertTrue((installer_root / ".agents/skills/speckit-concorde-init/SKILL.md").is_file())
                self.assertTrue((installer_root / ".agents/skills/reflections-triage/SKILL.md").is_file())
                self.assertTrue((installer_root / ".codex/agents/reflection_investigator.toml").is_file())
                self.assertTrue((installer_root / ".codex/agents/reflection_implementer.toml").is_file())

    def test_fresh_install_materializes_reflection_triage_for_claude_and_codex(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            dist = base / "dist"
            with CatalogServer(dist) as server:
                builder.build_release(dist, server.base_url)
                release = _release(server)
                expected = {
                    "codex": (
                        ".agents/skills/reflections-triage/SKILL.md",
                        ".codex/agents/reflection_investigator.toml",
                        ".codex/agents/reflection_implementer.toml",
                    ),
                    "claude": (
                        ".claude/skills/reflections-triage/SKILL.md",
                        ".claude/agents/reflection-investigator.md",
                        ".claude/agents/reflection-implementer.md",
                    ),
                }
                for integration, paths in expected.items():
                    with self.subTest(integration=integration):
                        target = base / integration
                        target.mkdir()
                        with mock.patch.object(installer, "fetch_release", return_value=release):
                            result = installer.main(["--target", str(target), "--integration", integration])
                        self.assertEqual(result, installer.EXIT_OK)
                        self.assertTrue(all((target / path).is_file() for path in paths))
                        receipt = json.loads((target / ".specify/concorde-agent-assets.json").read_text())
                        self.assertIn(integration, receipt["integrations"])
                        self.assertTrue((target / ".concorde/reflections/config.json").is_file())

    def test_three_current_repeats_change_no_target_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            dist = base / "dist"
            with CatalogServer(dist) as server:
                builder.build_release(dist, server.base_url)
                release = _release(server)
                target = base / "target"
                target.mkdir()
                with mock.patch.object(installer, "fetch_release", return_value=release):
                    self.assertEqual(
                        installer.main(["--target", str(target), "--integration", "codex"]),
                        installer.EXIT_OK,
                    )
                    expected = _all_hashes(target)
                    for _ in range(3):
                        self.assertEqual(
                            installer.main(["--target", str(target), "--integration", "codex"]),
                            installer.EXIT_OK,
                        )
                        self.assertEqual(_all_hashes(target), expected)

    def test_existing_project_integration_conflict_stops_before_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            dist = base / "dist"
            with CatalogServer(dist) as server:
                builder.build_release(dist, server.base_url)
                release = _release(server)
                target = base / "target"
                target.mkdir()
                project = SpecifyProject(target)
                project.initialize()
                before = _all_hashes(target)
                with mock.patch.object(installer, "fetch_release", return_value=release):
                    result = installer.main(
                        ["--target", str(target), "--integration", "gemini"]
                    )
                self.assertEqual(result, installer.EXIT_REQUEST)
                self.assertEqual(_all_hashes(target), before)

    def test_older_install_updates_natively_and_preserves_authored_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            old_dist = base / "old-dist"
            new_dist = base / "new-dist"
            with CatalogServer(old_dist) as old_server, CatalogServer(new_dist) as new_server:
                builder.build_release(old_dist, old_server.base_url, version="0.3.1")
                builder.build_release(new_dist, new_server.base_url)
                old_release = _release(old_server, "0.3.1")
                new_release = _release(new_server)
                target = base / "target"
                target.mkdir()
                with mock.patch.object(installer, "fetch_release", return_value=old_release):
                    self.assertEqual(
                        installer.main(["--target", str(target), "--integration", "codex"]),
                        installer.EXIT_OK,
                    )
                authored = target / "specs/user/notes.md"
                authored.parent.mkdir(parents=True)
                authored.write_text("maintainer-owned\n", encoding="utf-8")
                authored_digest = hashlib.sha256(authored.read_bytes()).hexdigest()
                config = target / ".concorde/reflections/config.json"
                config.write_text(config.read_text().replace('"investigators": 1', '"investigators": 3'))
                config_digest = hashlib.sha256(config.read_bytes()).hexdigest()
                plan = target / ".concorde/reflections/plans/R-001.md"
                plan.parent.mkdir(parents=True)
                plan.write_text("maintainer plan\n")
                plan_digest = hashlib.sha256(plan.read_bytes()).hexdigest()
                unrelated = target / ".agents/skills/user-skill/SKILL.md"
                unrelated.parent.mkdir(parents=True)
                unrelated.write_text("user skill\n")
                unrelated_digest = hashlib.sha256(unrelated.read_bytes()).hexdigest()

                with mock.patch.object(installer, "fetch_release", return_value=new_release):
                    self.assertEqual(
                        installer.main(["--target", str(target), "--integration", "codex"]),
                        installer.EXIT_OK,
                    )
                snapshot = _installed_snapshot(target)
                self.assertEqual(snapshot["bundles"][0]["version"], "0.6.0")
                self.assertEqual(hashlib.sha256(authored.read_bytes()).hexdigest(), authored_digest)
                self.assertEqual(hashlib.sha256(config.read_bytes()).hexdigest(), config_digest)
                self.assertEqual(hashlib.sha256(plan.read_bytes()).hexdigest(), plan_digest)
                self.assertEqual(hashlib.sha256(unrelated.read_bytes()).hexdigest(), unrelated_digest)

    def test_modified_projection_blocks_rerun_without_overwrite_or_false_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            dist = base / "dist"
            with CatalogServer(dist) as server:
                builder.build_release(dist, server.base_url)
                release = _release(server)
                target = base / "target"
                target.mkdir()
                with mock.patch.object(installer, "fetch_release", return_value=release):
                    self.assertEqual(installer.main(["--target", str(target), "--integration", "codex"]), installer.EXIT_OK)
                role = target / ".codex/agents/reflection_investigator.toml"
                role.write_text(role.read_text() + "\n# maintainer edit\n")
                before = role.read_bytes()
                output = io.StringIO()
                with mock.patch.object(installer, "fetch_release", return_value=release):
                    with redirect_stdout(output), redirect_stderr(output):
                        result = installer.main(["--target", str(target), "--integration", "codex"])
                self.assertEqual(result, installer.EXIT_SPECIFY)
                self.assertEqual(role.read_bytes(), before)
                self.assertIn("agent-projection-preview", output.getvalue())
                self.assertNotIn("CONCORDE INSTALL SUCCESS", output.getvalue())

    def test_projection_remove_deletes_only_matching_owned_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            dist = base / "dist"
            with CatalogServer(dist) as server:
                builder.build_release(dist, server.base_url)
                release = _release(server)
                target = base / "target"
                target.mkdir()
                with mock.patch.object(installer, "fetch_release", return_value=release):
                    self.assertEqual(installer.main(["--target", str(target), "--integration", "codex"]), installer.EXIT_OK)
                config = target / ".concorde/reflections/config.json"
                plan = target / ".concorde/reflections/plans/R-001.md"
                plan.parent.mkdir(parents=True)
                plan.write_text("plan\n")
                result = installer.run_agent_assets(target, "codex", "remove", release.version)
                self.assertEqual(result["status"], "success")
                self.assertTrue(config.is_file())
                self.assertTrue(plan.is_file())
                self.assertFalse((target / ".codex/agents/reflection_investigator.toml").exists())
                self.assertFalse((target / ".agents/skills/reflections-triage/SKILL.md").exists())

    def test_preview_leaves_empty_and_absent_targets_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            dist = base / "dist"
            with CatalogServer(dist) as server:
                builder.build_release(dist, server.base_url)
                release = _release(server)
                empty = base / "empty"
                empty.mkdir()
                absent = base / "absent"
                for target in (empty, absent):
                    output = io.StringIO()
                    with mock.patch.object(installer, "fetch_release", return_value=release):
                        with redirect_stdout(output), redirect_stderr(output):
                            result = installer.main(
                                [
                                    "--target", str(target),
                                    "--integration", "codex",
                                    "--preview",
                                ]
                            )
                    self.assertEqual(result, installer.EXIT_OK)
                    self.assertIn('"id": "concorde-bundle"', output.getvalue())
                    self.assertIn('"version": "0.6.0"', output.getvalue())
                    self.assertIn('"operation": "agent-assets.preview"', output.getvalue())
                    self.assertIn("reflection_investigator.toml", output.getvalue())
                    if target == empty:
                        self.assertEqual(list(target.iterdir()), [])
                    else:
                        self.assertFalse(target.exists())

    def test_existing_project_preview_is_read_only_and_matches_apply_components(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            dist = base / "dist"
            with CatalogServer(dist) as server:
                builder.build_release(dist, server.base_url)
                release = _release(server)
                target = base / "target"
                target.mkdir()
                SpecifyProject(target).initialize()
                before = _all_hashes(target)
                preview = io.StringIO()
                with mock.patch.object(installer, "fetch_release", return_value=release):
                    with redirect_stdout(preview), redirect_stderr(preview):
                        result = installer.main(["--target", str(target), "--preview"])
                self.assertEqual(result, installer.EXIT_OK)
                self.assertEqual(_all_hashes(target), before)
                self.assertIn('"id": "concorde"', preview.getvalue())
                self.assertGreaterEqual(preview.getvalue().count('"id": "concorde"'), 2)

                with mock.patch.object(installer, "fetch_release", return_value=release):
                    self.assertEqual(installer.main(["--target", str(target)]), installer.EXIT_OK)
                components = _installed_snapshot(target)["bundles"][0]["components"]
                self.assertEqual(
                    components,
                    [("extensions", "concorde", "0.6.0"), ("presets", "concorde", "0.6.0")],
                )

    def test_checkout_mode_builds_installs_repeats_and_releases_server(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target"
            target.mkdir()
            output = io.StringIO()
            with redirect_stdout(output), redirect_stderr(output):
                result = installer.main(
                    [
                        "--target", str(target),
                        "--integration", "codex",
                        "--checkout", str(REPOSITORY_ROOT),
                    ]
                )
            self.assertEqual(result, installer.EXIT_OK, output.getvalue())
            self.assertEqual(_installed_snapshot(target)["bundles"][0]["version"], "0.6.0")
            match = re.search(r"http://127\.0\.0\.1:(\d+)", output.getvalue())
            self.assertIsNotNone(match, output.getvalue())
            port = int(match.group(1))
            with self.assertRaises(OSError):
                socket.create_connection(("127.0.0.1", port), timeout=1)
            with socket.socket() as probe:
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                probe.bind(("127.0.0.1", port))

            expected = _all_hashes(target)
            second = io.StringIO()
            with redirect_stdout(second), redirect_stderr(second):
                result = installer.main(
                    [
                        "--target", str(target),
                        "--integration", "codex",
                        "--checkout", str(REPOSITORY_ROOT),
                    ]
                )
            self.assertEqual(result, installer.EXIT_OK, second.getvalue())
            self.assertIn("already-current", second.getvalue())
            self.assertEqual(_all_hashes(target), expected)

    def test_checkout_verification_failure_leaves_target_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            target = base / "target"
            target.mkdir()
            before = _all_hashes(target)
            output = io.StringIO()
            original = installer._run_release_script

            def fail_verification(checkout, script, *arguments, stage):
                if stage == "checkout-verification":
                    raise installer.InstallationError(
                        installer.EXIT_RELEASE,
                        stage,
                        "seeded verification failure",
                        "Repair the checkout release.",
                    )
                return original(checkout, script, *arguments, stage=stage)

            with mock.patch.object(installer, "_run_release_script", side_effect=fail_verification):
                with redirect_stdout(output), redirect_stderr(output):
                    result = installer.main(
                        [
                            "--target", str(target),
                            "--integration", "codex",
                            "--checkout", str(REPOSITORY_ROOT),
                        ]
                    )
            self.assertEqual(result, installer.EXIT_RELEASE)
            self.assertIn("checkout-verification", output.getvalue())
            self.assertNotIn("CONCORDE INSTALL SUCCESS", output.getvalue())
            self.assertEqual(_all_hashes(target), before)


if __name__ == "__main__":
    unittest.main()
