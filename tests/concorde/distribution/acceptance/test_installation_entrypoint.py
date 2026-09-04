from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.managed_runtime import (
    create_langgraph_index,
    runtime_install_environment,
)


INSTALLER = REPOSITORY_ROOT / "scripts/install-concorde.py"


class InstallationEntrypointAcceptance(unittest.TestCase):
    def run_installer(self, target: Path, *arguments: str):
        environment = runtime_install_environment(
            create_langgraph_index(target.parent)
        )
        return subprocess.run(
            [sys.executable, str(INSTALLER), "--target", str(target), "--format", "json", *arguments],
            text=True, capture_output=True, env=environment,
        )

    def test_preview_is_default_and_explicit_apply_installs(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "project"
            preview = self.run_installer(target, "--integration", "codex")
            self.assertEqual(preview.returncode, 0, preview.stderr)
            value = json.loads(preview.stdout)
            self.assertEqual(value["status"], "preview")
            self.assertEqual(list(target.rglob("*")), [])
            applied = self.run_installer(target, "--integration", "codex", "--apply")
            self.assertEqual(applied.returncode, 0, applied.stderr or applied.stdout)
            self.assertEqual(json.loads(applied.stdout)["status"], "installed")
            self.assertTrue((target / ".agents/skills/concorde-init/SKILL.md").is_file())
            self.assertTrue((target / ".concorde/install.json").is_file())

    def test_each_supported_integration_installs_all_capabilities(self):
        with tempfile.TemporaryDirectory() as temporary:
            for integration, root_name in (("codex", ".agents/skills"), ("claude", ".claude/skills")):
                target = Path(temporary) / integration
                result = self.run_installer(target, "--integration", integration, "--apply")
                self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
                self.assertEqual(len(list((target / root_name).glob("concorde-*/SKILL.md"))), 18)
                self.assertTrue(
                    (target / root_name / "concorde-standard-dev-loop/SKILL.md").is_file()
                )

    def test_existing_project_control_and_sources_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            config = target / ".concorde/config.json"
            config.parent.mkdir()
            config.write_text('{"profile_version":7,"root_module_id":"module.app","specification_root":"specs/app"}\n')
            source = target / "specs/app/architecture.md"
            source.parent.mkdir(parents=True)
            source.write_text("project authority\n")
            before = (config.read_bytes(), source.read_bytes())
            result = self.run_installer(target, "--apply")
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(before, (config.read_bytes(), source.read_bytes()))
            receipt_paths = {item["path"] for item in json.loads((target / ".concorde/install.json").read_text())["outputs"]}
            self.assertNotIn(".concorde/config.json", receipt_paths)
            self.assertNotIn("specs/app/architecture.md", receipt_paths)

    def test_unowned_collision_returns_conflict_and_preserves_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            collision = target / ".agents/skills/concorde-plan/SKILL.md"
            collision.parent.mkdir(parents=True)
            collision.write_text("mine\n")
            result = self.run_installer(target, "--apply")
            self.assertEqual(result.returncode, 2)
            value = json.loads(result.stdout)
            self.assertEqual(value["status"], "conflict")
            self.assertEqual(collision.read_text(), "mine\n")
            self.assertFalse((target / ".concorde/install.json").exists())

    def test_invalid_package_fails_without_framework_projection(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            target = base / "target"
            invalid = base / "invalid"
            invalid.mkdir()
            (invalid / "concorde.json").write_text("{}\n")
            result = self.run_installer(target, "--checkout", str(invalid), "--apply")
            self.assertEqual(result.returncode, 3)
            self.assertEqual(json.loads(result.stdout)["status"], "failed")
            self.assertFalse((target / ".concorde/framework").exists())

    def test_explicit_checkout_matches_in_checkout_runtime_and_stable_actions(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            implicit = base / "implicit"
            explicit = base / "explicit"
            first = self.run_installer(implicit, "--integration", "codex", "--apply")
            second = self.run_installer(
                explicit,
                "--checkout",
                str(REPOSITORY_ROOT),
                "--integration",
                "codex",
                "--apply",
            )
            self.assertEqual(first.returncode, 0, first.stderr or first.stdout)
            self.assertEqual(second.returncode, 0, second.stderr or second.stdout)
            first_value = json.loads(first.stdout)
            second_value = json.loads(second.stdout)
            self.assertEqual(
                [(item["path"], item["action"], item["role"], item["sha256"]) for item in first_value["actions"]],
                [(item["path"], item["action"], item["role"], item["sha256"]) for item in second_value["actions"]],
            )
            first_receipt = json.loads((implicit / ".concorde/install.json").read_text())
            second_receipt = json.loads((explicit / ".concorde/install.json").read_text())
            self.assertEqual(first_receipt["runtime"], second_receipt["runtime"])
            self.assertEqual(
                (implicit / ".agents/skills/concorde-plan/SKILL.md").read_bytes(),
                (explicit / ".agents/skills/concorde-plan/SKILL.md").read_bytes(),
            )
            repeat = self.run_installer(
                explicit,
                "--checkout",
                str(REPOSITORY_ROOT),
                "--integration",
                "codex",
                "--apply",
            )
            self.assertEqual(json.loads(repeat.stdout)["status"], "unchanged")

    def test_installed_official_viewer_launches_raw_graph_and_rejects_explore_envelope(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            target = base / "project"
            applied = self.run_installer(
                target, "--integration", "codex", "--apply"
            )
            self.assertEqual(applied.returncode, 0, applied.stderr or applied.stdout)
            graph = target / ".ua/knowledge-graph.json"
            graph.parent.mkdir(parents=True)
            graph.write_text(
                json.dumps(
                    {
                        "version": "1.0.0",
                        "project": {"name": "fixture"},
                        "nodes": [],
                        "edges": [],
                        "layers": [],
                        "tour": [],
                    }
                ),
                encoding="utf-8",
            )
            environment = runtime_install_environment(create_langgraph_index(base))
            launcher = target / ".concorde/framework/scripts/run-viewer.py"
            launched = subprocess.run(
                [
                    sys.executable,
                    str(launcher),
                    "--project-root",
                    str(target),
                    "--port",
                    "0",
                    "--no-open",
                ],
                text=True,
                capture_output=True,
                env=environment,
            )
            self.assertEqual(launched.returncode, 0, launched.stderr or launched.stdout)
            self.assertIn(".ua/knowledge-graph.json", launched.stdout)
            self.assertIn("FAKE NODE", launched.stdout)
            self.assertIn("--no-open", launched.stdout)

            graph.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "tool": "explore",
                        "result": {"alignment": {}},
                    }
                ),
                encoding="utf-8",
            )
            rejected = subprocess.run(
                [sys.executable, str(launcher), "--project-root", str(target)],
                text=True,
                capture_output=True,
                env=environment,
            )
            self.assertEqual(rejected.returncode, 3)
            self.assertIn("explore JSON is not Viewer input", rejected.stderr)
            self.assertNotIn("FAKE NODE", rejected.stdout)

    def test_installed_viewer_preserves_official_legacy_first_graph_rule(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            target = base / "project"
            applied = self.run_installer(target, "--apply")
            self.assertEqual(applied.returncode, 0, applied.stderr or applied.stdout)
            raw = {
                "version": "1.0.0",
                "project": {"name": "fixture"},
                "nodes": [],
                "edges": [],
            }
            for directory in (".ua", ".understand-anything"):
                graph = target / directory / "knowledge-graph.json"
                graph.parent.mkdir(parents=True)
                graph.write_text(json.dumps(raw), encoding="utf-8")
            environment = runtime_install_environment(create_langgraph_index(base))
            result = subprocess.run(
                [
                    sys.executable,
                    str(target / ".concorde/framework/scripts/run-viewer.py"),
                    "--project-root",
                    str(target),
                    "--no-open",
                ],
                text=True,
                capture_output=True,
                env=environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertIn(".understand-anything/knowledge-graph.json", result.stdout)


if __name__ == "__main__":
    unittest.main()
