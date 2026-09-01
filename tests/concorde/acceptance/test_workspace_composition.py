import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.installed_command_surface import registered_artifact
from tests.concorde.support.paths import REPOSITORY_ROOT


PRESET_PHASES = (
    "specify", "clarify", "checklist", "plan", "tasks", "implement", "analyze",
    "converge", "taskstoissues", "fast-loop",
)


class WorkspaceCompositionAcceptance(unittest.TestCase):
    def install(self, root: Path, integration: str, skills: bool) -> None:
        init = ["specify", "init", "--here", "--force", "--ignore-agent-tools", "--integration", integration]
        if skills:
            init.append("--integration-options=--skills")
        subprocess.run(init, cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["specify", "extension", "add", str(REPOSITORY_ROOT / "extensions/concorde"), "--dev"],
            cwd=root, check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["specify", "preset", "add", "--dev", str(REPOSITORY_ROOT / "presets/concorde")],
            cwd=root, check=True, capture_output=True, text=True,
        )

    def test_public_components_compose_protocol12_in_skills_and_slash_modes(self):
        for integration, skills in (("codex", True), ("gemini", False)):
            with self.subTest(integration=integration), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                self.install(root, integration, skills)
                for phase in PRESET_PHASES:
                    surface = registered_artifact(root, integration, f"speckit.{phase}")
                    body = surface.read_text(encoding="utf-8")
                    self.assertIn("Protocol 12", body, phase)
                    self.assertIn("workspace.py --phase", body, phase)
                for command in (
                    "speckit.concorde.init", "speckit.concorde.context", "speckit.concorde.validate",
                    "speckit.concorde.ask", "speckit.concorde.deliver",
                ):
                    self.assertTrue(registered_artifact(root, integration, command).is_file(), command)

                deliver = registered_artifact(root, integration, "speckit.concorde.deliver").read_text(encoding="utf-8")
                self.assertIn("Delivery Proposal 8", deliver)
                self.assertIn("cleanup-only", deliver)
                self.assertFalse((root / ".specify/presets/concorde/templates/abstract-template.md").exists())
                self.assertFalse((root / ".specify/presets/concorde/templates/implementation-template.md").exists())

    def test_composed_phase_guidance_preserves_authority_evidence_and_reflection_rules(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.install(root, "codex", True)
            plan = registered_artifact(root, "codex", "speckit.plan").read_text(encoding="utf-8")
            tasks = registered_artifact(root, "codex", "speckit.tasks").read_text(encoding="utf-8")
            implement = registered_artifact(root, "codex", "speckit.implement").read_text(encoding="utf-8")
            specify = registered_artifact(root, "codex", "speckit.specify").read_text(encoding="utf-8")

            for field in (
                "feature_path", "module_architecture", "module_ancestry", "related_features",
                "executable_context", "attempt_dir", "attempt_state", "reflections",
            ):
                self.assertIn(field, "\n".join((plan, tasks, implement)), field)
            self.assertIn("Planning must leave durable sources byte-identical", " ".join(plan.split()))
            self.assertIn("dependency-ordered, test-first", tasks)
            self.assertIn("Attempt Evidence", implement)
            self.assertIn("Only a proportionate passed check permits", implement)
            self.assertIn("complete durable feature file", specify)
            self.assertIn("same unique target", specify)

            for phase in ("plan", "tasks", "implement", "analyze", "converge"):
                body = registered_artifact(root, "codex", f"speckit.{phase}").read_text(encoding="utf-8")
                self.assertIn("reflection", body.lower(), phase)

            resolved = subprocess.run(
                ["specify", "preset", "resolve", "reflections-template"],
                cwd=root, check=True, capture_output=True, text=True,
            )
            self.assertIn("reflections-template.md", resolved.stdout.replace("\n", ""))


if __name__ == "__main__":
    unittest.main()
