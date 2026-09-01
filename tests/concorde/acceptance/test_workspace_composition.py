import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.installed_command_surface import CONCORDE_COMMANDS, registered_artifact
from tests.concorde.support.paths import REPOSITORY_ROOT


class WorkspaceCompositionAcceptance(unittest.TestCase):
    def test_public_preset_composes_routing_in_skills_and_slash_modes(self):
        for integration, skills, artifact in (
            ("codex", True, ".agents/skills/speckit-plan/SKILL.md"),
            ("gemini", False, ".gemini/commands/speckit.plan.toml"),
        ):
            with self.subTest(integration=integration), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                init = ["specify", "init", "--here", "--force", "--ignore-agent-tools", "--integration", integration]
                if skills:
                    init.append("--integration-options=--skills")
                subprocess.run(init, cwd=root, check=True, capture_output=True)
                subprocess.run(
                    ["specify", "extension", "add", str(REPOSITORY_ROOT / "extensions/concorde"), "--dev"],
                    cwd=root,
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    ["specify", "preset", "add", "--dev", str(REPOSITORY_ROOT / "presets/concorde")],
                    cwd=root,
                    check=True,
                    capture_output=True,
                )
                rendered = (root / artifact).read_text(encoding="utf-8")
                self.assertIn("Concorde Installed Workspace Gate", rendered)
                self.assertIn("workspace.attempt_dir", rendered)
                self.assertIn("attempt_state", rendered)
                self.assertIn(".specify/extensions/concorde/scripts/python/workspace.py", rendered)
                self.assertNotIn("Concorde selected-workspace routing", rendered)
                self.assertTrue((root / ".specify/extensions/concorde/scripts/python/workspace.py").is_file())
                # Every phase after specification carries the byte-identical Reflection Recording block.
                block_start = rendered.index("## Reflection Recording")
                block = rendered[block_start:rendered.index("## Mandatory Post-Execution Hooks", block_start)]
                self.assertIn("workspace.reflections", block)
                self.assertIn("only file that may persist", block)
                self.assertIn("never become a second reflection record", block)
                self.assertIn("Reflections added:", block)
                self.assertIn("Maintained reconciliation", block)
                self.assertIn("preserve each exact `R-NNN` identifier", block)
                self.assertIn("complete log MUST pass", block)
                self.assertNotIn("Append only; never rewrite", block)
                for phase in ("tasks", "implement", "analyze", "converge"):
                    surface = registered_artifact(root, integration, f"speckit.{phase}").read_text(encoding="utf-8")
                    self.assertIn(block, surface, phase)
                analyze_surface = registered_artifact(root, integration, "speckit.analyze").read_text(encoding="utf-8")
                self.assertIn("READ-ONLY EXCEPT REFLECTION RECORDING", analyze_surface)
                self.assertIn("Every other file MUST remain byte-identical", analyze_surface)
                self.assertIn("no recordable problem MUST make zero filesystem changes", analyze_surface)
                self.assertNotIn("**STRICTLY READ-ONLY**", analyze_surface)
                implement_surface = registered_artifact(root, integration, "speckit.implement").read_text(encoding="utf-8")
                self.assertIn("`Effect: blocked`", implement_surface)
                specify_surface = registered_artifact(root, integration, "speckit.specify").read_text(encoding="utf-8")
                plan_surface = registered_artifact(root, integration, "speckit.plan").read_text(encoding="utf-8")
                tasks_surface = registered_artifact(root, integration, "speckit.tasks").read_text(encoding="utf-8")
                issues_surface = registered_artifact(root, integration, "speckit.taskstoissues").read_text(encoding="utf-8")
                normalized_specify = " ".join(specify_surface.split())
                normalized_plan = " ".join(plan_surface.split())
                for invariant in (
                    "normalized project-relative `.html` path beneath `generated/`",
                    "diagram-relative `meta.output`",
                    "resolves to that same project-relative target",
                    "unique across all maintained diagram declarations",
                    "correct the invalid declaration before reporting specification readiness",
                ):
                    self.assertIn(invariant, normalized_specify, invariant)
                for invariant in (
                    "workspace.feature_abstract",
                    "parent_context.feature_abstract",
                    "no accepted baseline",
                    "ATTEMPT_DIR/contracts/",
                    "MUST NOT update",
                ):
                    self.assertIn(invariant, plan_surface, invariant)
                for invariant in (
                    "validate every existing diagram declaration",
                    "same unique target beneath `generated/`",
                    "route the invalid durable declaration back to specification authority",
                    "MUST NOT repair `design.md`",
                    "Only after every declaration passes",
                ):
                    self.assertIn(invariant, normalized_plan, invariant)
                for invariant in (
                    "requirement ID or acceptance-outcome",
                    "ATTEMPT_DIR/contracts/",
                    "parent_context.feature_abstract",
                ):
                    self.assertIn(invariant, tasks_surface, invariant)
                for invariant in (
                    "Invocation authorization",
                    "task-file order",
                    "prerequisite task IDs",
                    "issue links",
                    "attempt/tasks.md remains authoritative",
                ):
                    self.assertIn(invariant, issues_surface, invariant)
                execute_surface = registered_artifact(root, integration, "speckit.implement").read_text(encoding="utf-8")
                analyze_surface = registered_artifact(root, integration, "speckit.analyze").read_text(encoding="utf-8")
                converge_surface = registered_artifact(root, integration, "speckit.converge").read_text(encoding="utf-8")
                execute_content = " ".join(execute_surface.split())
                converge_content = " ".join(converge_surface.split())
                for surface in (execute_surface, analyze_surface, converge_surface):
                    self.assertIn("workspace.feature_abstract", surface)
                    self.assertIn("parent_context.feature_abstract", surface)
                for invariant in (
                    "Evidence before completion",
                    "ATTEMPT_DIR/validation.md",
                    "MUST remain unchecked",
                    "protected-authority",
                    "setup-file inspection as read-only by default",
                    "one dependency-ready executable task",
                    "stable task ID",
                    "requirement, acceptance-outcome, or named plan-section trace token",
                    "detected tool",
                    "exact project-relative setup file being changed",
                    "cannot independently authorize a setup mutation",
                    "Repository/tool detection alone MUST NOT authorize a write",
                    "preserve every setup file byte-for-byte",
                ):
                    self.assertIn(invariant, execute_content, invariant)
                for invariant in (
                    "absent evidence",
                    "prevailing `design.md` requirement",
                    "no recordable problem MUST make zero filesystem changes",
                ):
                    self.assertIn(invariant, analyze_surface, invariant)
                for invariant in (
                    "Attempt Evidence",
                    "semantic duplicate",
                    "preserve completed tasks",
                    "no empty Convergence header",
                    "implementation-owned diagram source/evidence",
                    "missing required diagram declaration",
                    "incorrect core role/kind",
                    "prose/contract authority disagreement",
                    "specification or architecture review",
                    "never append a task that edits feature `design.md`",
                    "maintained JSON that is already authorized, validation, delivery, automatic embedding",
                    "truthful visual-review evidence, and freshness",
                ):
                    self.assertIn(invariant, converge_content, invariant)
                self.assertNotIn(
                    "Append work for `diagrams/` placement, declaration in `design.md`, maintained "
                    "Archify JSON, prose alignment, contract references, delivery, automatic "
                    "feature-page embedding, truthful visual-review evidence, and freshness",
                    converge_content,
                )
                resolved = subprocess.run(["specify", "preset", "resolve", "reflections-template"], cwd=root, check=True, capture_output=True, text=True)
                self.assertIn("reflections-template.md", resolved.stdout.replace("\n", ""))
                surfaces = {registered_artifact(root, integration, command) for command in CONCORDE_COMMANDS}
                self.assertEqual(len(surfaces), 5)
                self.assertTrue(all(path.is_file() for path in surfaces))


if __name__ == "__main__":
    unittest.main()
