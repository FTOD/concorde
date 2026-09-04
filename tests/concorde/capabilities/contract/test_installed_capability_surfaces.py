from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import CONTEXT_PROJECT, REPOSITORY_ROOT
from tests.concorde.support.managed_runtime import (
    create_langgraph_index,
    runtime_install_environment,
)


class InstalledCapabilitySurfaceContractTests(unittest.TestCase):
    def install(self, base: str, integration: str) -> Path:
        root = Path(base) / integration
        environment = runtime_install_environment(create_langgraph_index(Path(base)))
        result = subprocess.run(
            [
                sys.executable,
                str(REPOSITORY_ROOT / "scripts/install-concorde.py"),
                "--target",
                str(root),
                "--integration",
                integration,
                "--apply",
                "--format",
                "json",
            ],
            text=True,
            capture_output=True,
            env=environment,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertEqual(json.loads(result.stdout)["status"], "installed")
        shutil.copytree(CONTEXT_PROJECT / ".concorde", root / ".concorde", dirs_exist_ok=True)
        shutil.copytree(CONTEXT_PROJECT / "specs", root / "specs", dirs_exist_ok=True)
        (root / ".concorde/feature.json").write_text(
            '{"feature_path":"specs/example/features/001-deliver.md"}\n'
        )
        return root

    def test_both_integrations_receive_all_leaf_and_operation_skills(self):
        with tempfile.TemporaryDirectory() as temporary:
            for integration, skill_root in (
                ("codex", ".agents/skills"),
                ("claude", ".claude/skills"),
            ):
                with self.subTest(integration=integration):
                    root = self.install(temporary, integration)
                    capabilities = sorted((root / skill_root).glob("concorde-*/SKILL.md"))
                    self.assertEqual(len(capabilities), 18)
                    for operation in (
                        "concorde-standard-dev-loop",
                        "concorde-reflections-triage",
                        "concorde-plan",
                    ):
                        projected = root / skill_root / operation / "SKILL.md"
                        framework = root / ".concorde/framework/operations" / operation
                        self.assertTrue(projected.is_file())
                        self.assertEqual(
                            sorted(path.name for path in framework.iterdir()),
                            ["SKILL.md", "operation.py"],
                        )
                        content = projected.read_text()
                        self.assertIn('kind: "operation"', content)
                        self.assertIn(
                            f".concorde/framework/operations/{operation}/operation.py",
                            content,
                        )
                    if integration == "codex":
                        self.assertTrue(
                            (root / ".codex/agents/reflection_investigator.toml").is_file()
                        )
                    else:
                        self.assertTrue(
                            (root / ".claude/agents/reflection-investigator.md").is_file()
                        )
                    for capability in capabilities:
                        content = capability.read_text()
                        self.assertIn('author: "concorde"', content)
                        self.assertIn(
                            'compatibility: "Requires a Concorde project"', content
                        )
                        self.assertNotIn(".specify/", content)
                        self.assertNotIn("github-spec-kit", content)

    def test_phase_skills_use_installed_workspace_and_templates(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.install(temporary, "codex")
            plan = (root / ".agents/skills/concorde-plan/SKILL.md").read_text()
            specify = (root / ".agents/skills/concorde-specify/SKILL.md").read_text()
            self.assertIn(
                "python3 .concorde/framework/scripts/run-operation.py "
                ".concorde/framework/operations/concorde-plan/operation.py",
                plan,
            )
            self.assertIn('kind: "operation"', plan)
            self.assertIn(".concorde/framework/templates/feature-template.md", specify)
            self.assertIn("Protocol 13", plan)
            self.assertNotIn(str(REPOSITORY_ROOT), plan + specify)

    def test_installed_workspace_adapter_executes_protocol13(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.install(temporary, "codex")
            result = subprocess.run(
                [
                    sys.executable,
                    str(root / ".concorde/framework/scripts/workspace.py"),
                    "--project-root",
                    str(root),
                    "--phase",
                    "plan",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["schema_version"], 13)
            self.assertEqual(payload["workspace"]["feature_id"], "feature.example.deliver")
            self.assertEqual(
                payload["phase_root"], ".concorde/attempts/feature.example.deliver"
            )

    def test_installed_operation_skill_points_to_an_executable_framework_graph(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.install(temporary, "codex")
            projected = (root / ".agents/skills/concorde-standard-dev-loop/SKILL.md").read_text()
            relative = ".concorde/framework/operations/concorde-standard-dev-loop/operation.py"
            self.assertIn(relative, projected)
            result = subprocess.run(
                [
                    "python3",
                    ".concorde/framework/scripts/run-operation.py",
                    relative,
                    "Add audit logging",
                    "--framework-prefix",
                    ".concorde/framework",
                ],
                cwd=root,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["operation"], "concorde-standard-dev-loop")
            self.assertEqual(
                [item["stage"] for item in payload["capabilities"]],
                ["specify", "plan", "tasks", "tasks", "deliver", "deliver"],
            )

    def test_every_installed_operation_passes_managed_runtime_check(self):
        with tempfile.TemporaryDirectory() as temporary:
            for integration in ("codex", "claude"):
                root = self.install(temporary, integration)
                for operation in (
                    "concorde-standard-dev-loop",
                    "concorde-reflections-triage",
                    "concorde-plan",
                ):
                    with self.subTest(integration=integration, operation=operation):
                        result = subprocess.run(
                            [
                                "python3",
                                ".concorde/framework/scripts/run-operation.py",
                                f".concorde/framework/operations/{operation}/operation.py",
                                "--runtime-check",
                            ],
                            cwd=root,
                            text=True,
                            capture_output=True,
                            env={**os.environ, "PIP_NO_INDEX": "1", "UV_OFFLINE": "1"},
                        )
                        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
                        payload = json.loads(result.stdout)
                        self.assertEqual(payload["operation"], operation)
                        self.assertEqual(Path(payload["venv"]), root / ".concorde/.venv")
                        self.assertEqual(
                            Path(payload["python"]),
                            root / ".concorde/.venv/bin/python",
                        )

    def test_receipt_roles_cover_framework_skills_operations_and_agents(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.install(temporary, "codex")
            receipt = json.loads((root / ".concorde/install.json").read_text())
            self.assertEqual(receipt["concorde_version"], "2.1.0")
            self.assertEqual(receipt["integration"], "codex")
            self.assertEqual(receipt["runtime"]["path"], ".concorde/.venv")
            self.assertEqual(
                receipt["runtime"]["verified_operations"],
                [
                    "concorde-standard-dev-loop",
                    "concorde-reflections-triage",
                    "concorde-plan",
                ],
            )
            roles = {item["role"] for item in receipt["outputs"]}
            self.assertEqual(roles, {"framework", "skill", "operation", "agent"})
            paths = {item["path"] for item in receipt["outputs"]}
            self.assertIn(".concorde/framework/concorde.json", paths)
            self.assertIn(".agents/skills/concorde-constitution/SKILL.md", paths)
            self.assertIn(
                ".agents/skills/concorde-standard-dev-loop/SKILL.md", paths
            )
            self.assertNotIn(".concorde/config.json", paths)
            self.assertTrue(os.access(root / ".concorde/framework/scripts/concorde.py", os.X_OK))
            self.assertTrue(os.access(root / ".concorde/framework/scripts/concorde.sh", os.X_OK))

    def test_installed_framework_canonical_bytes_match_root_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.install(temporary, "codex")
            for relative in (
                "concorde.json",
                "skills/concorde-plan-context/SKILL.md",
                "skills/concorde-plan-author/SKILL.md",
                "operations/concorde-plan/SKILL.md",
                "operations/concorde-plan/operation.py",
                "operations/concorde-standard-dev-loop/SKILL.md",
                "operations/concorde-standard-dev-loop/operation.py",
                "templates/feature-template.md",
                "src/concorde/understanding/alignment.py",
                "src/concorde/capabilities/cli.py",
                "agent-assets/reflections/manifest.json",
            ):
                self.assertEqual(
                    (root / ".concorde/framework" / relative).read_bytes(),
                    (REPOSITORY_ROOT / relative).read_bytes(),
                    relative,
                )


if __name__ == "__main__":
    unittest.main()
