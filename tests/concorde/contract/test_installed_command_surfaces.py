import json
import shutil
import tempfile
import unittest
import subprocess
import sys
from pathlib import Path

from tests.concorde.support.catalog_server import CatalogServer
from tests.concorde.support.installed_command_surface import (
    CONCORDE_COMMANDS,
    FAST_LOOP_PHASES,
    NORMAL_PHASES,
    PRESET_COMMANDS,
    execute_workspace_surface,
    handoff_digest,
    registered_artifact,
)
from tests.concorde.support.paths import CONTEXT_PROJECT, REPOSITORY_ROOT
from tests.concorde.support.specify_project import SpecifyProject

import importlib.util


_builder_spec = importlib.util.spec_from_file_location(
    "concorde_release_builder", REPOSITORY_ROOT / "scripts/release/build-components.py"
)
assert _builder_spec and _builder_spec.loader
_builder = importlib.util.module_from_spec(_builder_spec)
_builder_spec.loader.exec_module(_builder)


class InstalledCommandSurfaceContractTests(unittest.TestCase):
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

    def installed_project(self, temporary: str, integration: str = "codex") -> Path:
        root = Path(temporary) / "target"
        project = SpecifyProject(root, integration=integration, skills=integration == "codex")
        project.initialize()
        project.register_catalogs(self.server.base_url)
        project.run("bundle", "install", "concorde-bundle")
        subprocess.run(
            [
                sys.executable,
                str(root / ".specify/extensions/concorde/scripts/python/concorde.py"),
                "--project-root",
                str(root),
                "agent-assets",
                "sync",
                "--integration",
                integration,
                "--concorde-version",
                "0.5.0",
            ],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        shutil.copytree(CONTEXT_PROJECT / ".concorde", root / ".concorde", dirs_exist_ok=True)
        shutil.copytree(CONTEXT_PROJECT / "specs", root / "specs", dirs_exist_ok=True)
        (root / ".specify/feature.json").write_text(
            json.dumps({"feature_directory": "specs/example/features/001-deliver"}, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        return root

    def test_release_materializes_commands_and_native_reflection_agents(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.installed_project(temporary)
            normal = {registered_artifact(root, "codex", command) for command in NORMAL_PHASES}
            fast_loop = {registered_artifact(root, "codex", command) for command in FAST_LOOP_PHASES}
            concorde = {registered_artifact(root, "codex", command) for command in CONCORDE_COMMANDS}
            self.assertEqual(len(normal), 9)
            self.assertEqual(len(fast_loop), 1)
            self.assertEqual(len(concorde), 5)
            self.assertTrue(all(path.is_file() for path in normal | fast_loop | concorde))
            self.assertTrue((root / ".agents/skills/reflections-triage/SKILL.md").is_file())
            self.assertTrue((root / ".codex/agents/reflection_investigator.toml").is_file())
            self.assertTrue((root / ".codex/agents/reflection_implementer.toml").is_file())
            self.assertTrue((root / ".specify/concorde-agent-assets.json").is_file())
            fast_content = next(iter(fast_loop)).read_text(encoding="utf-8")
            for requirement in (
                "$ARGUMENTS",
                "--phase fast-loop",
                "Eligibility Preflight",
                "anchor feature",
                "affected feature set",
                "Every affected feature",
                "inter-module contract",
                "module responsibility",
                "dependency direction",
                "users of the whole project",
                "Pure rename",
                "old-to-new mapping",
                "referential-only",
                "stale-name",
                "architecture evidence state",
                "needs no separate post-edit",
                "No attempt: yes",
                "No acceptance: yes",
            ):
                self.assertIn(requirement, fast_content)
            self.assertNotIn("review_pending", fast_content)
            self.assertNotIn(str(REPOSITORY_ROOT), fast_content)
            ask = registered_artifact(root, "codex", "speckit.concorde.ask")
            content = ask.read_text(encoding="utf-8")
            for requirement in ("$ARGUMENTS", "citation", "uncertainty", "read-only"):
                self.assertIn(requirement, content)
            for executable in ("concorde.sh", "concorde.ps1", "concorde.py", "workspace.py"):
                self.assertNotIn(executable, content)
            self.assertNotIn(str(REPOSITORY_ROOT), content)
            triage = (root / ".agents/skills/reflections-triage/SKILL.md").read_text(encoding="utf-8")
            self.assertIn("reflection-triage/v1", triage)
            self.assertNotIn(str(REPOSITORY_ROOT), triage)

    def test_every_preset_winner_executes_the_installed_workspace_bootstrap(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.installed_project(temporary)
            receipts = []
            for command, phase in PRESET_COMMANDS.items():
                artifact = registered_artifact(root, "codex", command)
                receipt = execute_workspace_surface(
                    root,
                    artifact,
                    command,
                    phase,
                    REPOSITORY_ROOT,
                )
                receipts.append(receipt)
                self.assertEqual(receipt.exit_status, 0)
                expected = receipt.workspace["feature_directory"] if phase in {"specify", "clarify", "checklist", "fast-loop"} else receipt.workspace["attempt_dir"]
                self.assertEqual(receipt.phase_root, expected)
                self.assertEqual(
                    receipt.workspace["checklists_dir"],
                    receipt.workspace["attempt_dir"] + "/checklists",
                )
                if phase in {"specify", "clarify", "checklist", "implement"}:
                    content = artifact.read_text(encoding="utf-8")
                    self.assertNotIn("FEATURE_DIR/checklists", content)
                    self.assertIn("CHECKLISTS_DIR", content)
                self.assertEqual(receipt.checkout_reads, ())
            self.assertEqual(len({item.handoff_digest for item in receipts}), 1)

    def test_installed_handoff_bytes_match_release_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.installed_project(temporary)
            installed = handoff_digest(
                root / ".specify/extensions/concorde",
                root / ".specify/presets/concorde",
            )
            source = handoff_digest(
                REPOSITORY_ROOT / "extensions/concorde",
                REPOSITORY_ROOT / "presets/concorde",
            )
            self.assertEqual(installed, source)


if __name__ == "__main__":
    unittest.main()
