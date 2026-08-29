import os
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, VALID_PROJECT


class AgentCommandContractTests(unittest.TestCase):
    def test_four_operations_have_launchers_and_ask_is_agent_only(self):
        commands = REPOSITORY_ROOT / "extensions/concorde/commands"
        expected = {
            "speckit.concorde.init.md",
            "speckit.concorde.impl.accept.md",
            "speckit.concorde.context.md",
            "speckit.concorde.validate.md",
            "speckit.concorde.ask.md",
        }
        self.assertEqual({path.name for path in commands.glob("*.md")}, expected)
        ask = commands / "speckit.concorde.ask.md"
        runtime_commands = expected - {ask.name}
        for filename in runtime_commands:
            path = commands / filename
            content = path.read_text()
            self.assertIn(".specify/extensions/concorde/scripts/", content)
            self.assertNotIn(str(REPOSITORY_ROOT), content)
        ask_content = ask.read_text(encoding="utf-8")
        for invariant in (
            "$ARGUMENTS",
            ".specify/extensions/concorde/",
            ".specify/presets/concorde-core/",
            "project-relative",
            "citation",
            "bounded",
            "clarification",
            "uncertainty",
            "read-only",
        ):
            self.assertIn(invariant, ask_content)
        for executable in ("concorde.sh", "concorde.ps1", "concorde.py", "workspace.py"):
            self.assertNotIn(executable, ask_content)
        self.assertNotIn(str(REPOSITORY_ROOT), ask_content)

        init_content = (commands / "speckit.concorde.init.md").read_text(encoding="utf-8")
        for invariant in (
            "interaction_model",
            "Skills",
            "Scripts",
            "Workspace Files",
            "attempt/",
            "status is `unchanged`",
            "do not invent product modules",
        ):
            self.assertIn(invariant, init_content)

    def test_distribution_handoff_names_nine_normal_and_five_concorde_intents(self):
        contracts = REPOSITORY_ROOT / "specs/concorde/features/001-concorde-workflow/contracts"
        command_contract = (contracts / "agent-commands.md").read_text(encoding="utf-8")
        schema = json.loads((contracts / "feature-workspace.schema.json").read_text(encoding="utf-8"))
        for command in (
            "specify",
            "clarify",
            "checklist",
            "plan",
            "tasks",
            "implement",
            "analyze",
            "converge",
            "taskstoissues",
        ):
            self.assertIn(command, command_contract)
        for command in ("init", "impl.accept", "context", "validate", "ask"):
            self.assertIn(command, command_contract)
        self.assertEqual(schema["$defs"]["workspacePaths"]["required"], [
            "workspace_kind",
            "feature_id",
            "providing_module",
            "parent_context",
            "siblings",
            "feature_directory",
            "feature_abstract",
            "feature_design",
            "feature_implementation",
            "module_summary",
            "module_design",
            "contracts_dir",
            "checklists_dir",
            "diagrams_dir",
            "attempt_dir",
            "attempt_state",
            "plan",
            "research",
            "data_model",
            "quickstart",
            "tasks",
            "validation",
        ])
        self.assertIn("Workflow Distribution Handoff", command_contract)

    def test_checklist_surfaces_use_only_temporal_checklist_path(self):
        package_surfaces = [
            REPOSITORY_ROOT / "presets/concorde-core/commands" / f"speckit.{name}.md"
            for name in ("specify", "clarify", "checklist", "implement")
        ]
        local_surfaces = [
            REPOSITORY_ROOT / ".agents/skills" / f"speckit-{name}" / "SKILL.md"
            for name in ("specify", "clarify", "checklist", "implement")
        ]
        for path in package_surfaces:
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("FEATURE_DIR/checklists", content, path.as_posix())
            self.assertIn("CHECKLISTS_DIR", content, path.as_posix())
        for path in local_surfaces:
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("FEATURE_DIR/checklists", content, path.as_posix())
            self.assertTrue(
                "attempt/checklists" in content
                or "ATTEMPT_DIR/checklists" in content
                or "CHECKLISTS_DIR" in content,
                path.as_posix(),
            )

    def test_acceptance_surfaces_require_checklists_and_return_review_metadata(self):
        surfaces = (
            REPOSITORY_ROOT / "extensions/concorde/commands/speckit.concorde.impl.accept.md",
            REPOSITORY_ROOT / ".agents/skills/speckit-concorde-impl-accept/SKILL.md",
        )
        for path in surfaces:
            content = path.read_text(encoding="utf-8")
            self.assertIn("attempt/checklists", content, path.as_posix())
            self.assertIn("proposal_path", content, path.as_posix())
            self.assertIn("task_summary", content, path.as_posix())
            self.assertIn("checklist_summary", content, path.as_posix())

    def test_python_launcher_preserves_exit_and_handles_quoted_root(self):
        launcher = REPOSITORY_ROOT / "extensions/concorde/scripts/python/concorde.py"
        result = subprocess.run(
            [sys.executable, str(launcher), "--project-root", str(VALID_PROJECT), "validate", "--format", "json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"operation":"validate"', result.stdout)
        self.assertGreaterEqual(sys.version_info, (3, 11))

    @unittest.skipUnless(os.name != "nt", "POSIX launcher test")
    def test_posix_launcher_is_relative_and_executable(self):
        launcher = REPOSITORY_ROOT / "extensions/concorde/scripts/bash/concorde.sh"
        self.assertTrue(os.access(launcher, os.X_OK))
        result = subprocess.run([str(launcher), "--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_powershell_launcher_uses_join_path_and_propagates_exit(self):
        content = (REPOSITORY_ROOT / "extensions/concorde/scripts/powershell/concorde.ps1").read_text()
        self.assertIn("Join-Path $PSScriptRoot", content)
        self.assertIn("@args", content)
        self.assertIn("exit $LASTEXITCODE", content)


if __name__ == "__main__":
    unittest.main()
