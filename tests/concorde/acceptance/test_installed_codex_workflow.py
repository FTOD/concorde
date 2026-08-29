import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.contract.test_installed_command_surfaces import _builder
from tests.concorde.support.catalog_server import CatalogServer
from tests.concorde.support.installed_command_surface import (
    CONCORDE_COMMANDS,
    CONCORDE_RUNTIME_COMMANDS,
    registered_artifact,
)
from tests.concorde.support.paths import TWO_LEVEL_PROJECT
from tests.concorde.support.specify_project import SpecifyProject


class InstalledCodexWorkflowTests(unittest.TestCase):
    def test_five_surfaces_preserve_four_runtime_operations_and_hardening(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            dist = base / "dist"
            server = CatalogServer(dist)
            _builder.build_release(dist, server.base_url)
            with server:
                root = base / "target"
                project = SpecifyProject(root)
                project.initialize()
                project.register_catalogs(server.base_url)
                project.run("bundle", "install", "concorde-bundle")
                shutil.copytree(TWO_LEVEL_PROJECT / ".concorde", root / ".concorde", dirs_exist_ok=True)
                shutil.copytree(TWO_LEVEL_PROJECT / "specs", root / "specs", dirs_exist_ok=True)
                (root / ".specify/feature.json").write_text(
                    json.dumps({"feature_directory": "specs/example/features/001-checkout/subfeatures/001-authorize-payment"}, separators=(",", ":")) + "\n",
                    encoding="utf-8",
                )
                self.assertEqual(
                    len({registered_artifact(root, "codex", command) for command in CONCORDE_COMMANDS}),
                    5,
                )
                self.assertEqual(len(CONCORDE_RUNTIME_COMMANDS), 4)
                workspace_adapter = root / ".specify/extensions/concorde/scripts/python/workspace.py"
                checklist_paths = subprocess.run(
                    [sys.executable, str(workspace_adapter), "--project-root", str(root), "--phase", "checklist"],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=True,
                )
                checklist_payload = json.loads(checklist_paths.stdout)
                self.assertEqual(checklist_payload["schema_version"], 6)
                workspace_payload = checklist_payload["workspace"]
                self.assertEqual(workspace_payload["workspace_kind"], "subfeature")
                self.assertEqual(workspace_payload["parent_context"]["feature_id"], "feature.example.checkout")
                self.assertEqual(
                    workspace_payload["parent_context"]["feature_implementation"],
                    "specs/example/features/001-checkout/implementation.md",
                )
                self.assertEqual(
                    workspace_payload["parent_context"]["feature_abstract"],
                    "specs/example/features/001-checkout/abstract.md",
                )
                self.assertEqual(
                    workspace_payload["feature_implementation"],
                    "specs/example/features/001-checkout/subfeatures/001-authorize-payment/implementation.md",
                )
                self.assertEqual(
                    workspace_payload["feature_abstract"],
                    "specs/example/features/001-checkout/subfeatures/001-authorize-payment/abstract.md",
                )
                self.assertEqual(workspace_payload["module_summary"], "specs/example/module.md")
                self.assertEqual(workspace_payload["module_design"], "specs/example/design.md")
                self.assertIn("feature_implementation", workspace_payload)
                self.assertEqual(
                    workspace_payload["checklists_dir"],
                    workspace_payload["attempt_dir"] + "/checklists",
                )
                launcher = root / ".specify/extensions/concorde/scripts/python/concorde.py"
                operations = (
                    (["validate"], {"success"}),
                    (["context", "module.example"], {"success"}),
                )
                for arguments, statuses in operations:
                    result = subprocess.run(
                        [sys.executable, str(launcher), "--project-root", str(root), *arguments],
                        cwd=root,
                        text=True,
                        capture_output=True,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn(json.loads(result.stdout)["status"], statuses)
                attempt = root / "specs/example/features/001-checkout/subfeatures/001-authorize-payment/attempt"
                attempt.mkdir(exist_ok=True)
                (attempt / "tasks.md").write_text("# Tasks\n\n- [X] T001 Complete installed fixture\n", encoding="utf-8")
                harden = subprocess.run(
                    [sys.executable, str(launcher), "--project-root", str(root), "feature", "harden", "--propose"],
                    cwd=root,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(harden.returncode, 0, harden.stdout + harden.stderr)
                harden_payload = json.loads(harden.stdout)
                self.assertEqual(harden_payload["status"], "eligible")
                self.assertEqual(
                    harden_payload["proposal_path"],
                    harden_payload["workspace"]["attempt_dir"] + "/harden-proposal.json",
                )
                self.assertEqual(harden_payload["task_summary"], {"complete": 1, "incomplete": 0, "malformed": 0})
                self.assertEqual(
                    harden_payload["checklist_summary"],
                    {"files": 0, "complete": 0, "incomplete": 0, "malformed": 0},
                )
                self.assertEqual(harden_payload["schema_version"], 6)
                self.assertEqual(harden_payload["workspace"]["module_design"], "specs/example/design.md")
                self.assertIn("specs/example/design.md", harden_payload["artifacts"])
                # Proposal v4 with a module-reference amendment: review boundary holds until explicit apply.
                before = {
                    path.relative_to(root): path.read_bytes()
                    for path in (root / "specs").rglob("*")
                    if path.is_file()
                }
                candidate = (
                    "# Feature Implementation: Authorize Payment\n\n**Realization status**: Hardened in the installed fixture.\n\n"
                    "## Realization Overview\n\nInstalled.\n\n## Module and Feature Collaboration\n\nInstalled.\n\n"
                    "## Scenario Realization\n\nInstalled.\n\n## Durable Implementation Decisions\n\nInstalled.\n\n"
                    "## Traceability and Evidence\n\nInstalled.\n\n## Known Limitations\n\nNone.\n"
                )
                amendment = "# Design Reference: Example Commerce\n\n## Decision Log\n\n- Hardened authorize-payment in the installed fixture.\n"
                proposal_path = root / harden_payload["proposal_path"]
                proposal_path.write_text(
                    json.dumps(
                        {
                            "proposal_version": 4,
                            "operation": "feature.harden",
                            "target": harden_payload["target"],
                            "source_digest": harden_payload["source_digest"],
                            "implementation": {"path": harden_payload["workspace"]["feature_implementation"], "content": candidate},
                            "module_design": {"path": harden_payload["workspace"]["module_design"], "content": amendment},
                            "remove": [harden_payload["workspace"]["attempt_dir"]],
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
                reviewed = subprocess.run(
                    [sys.executable, str(launcher), "--project-root", str(root), "feature", "harden", "--propose"],
                    cwd=root,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(reviewed.returncode, 0, reviewed.stdout + reviewed.stderr)
                after_review = {
                    path.relative_to(root): path.read_bytes()
                    for path in (root / "specs").rglob("*")
                    if path.is_file() and path.name != "harden-proposal.json"
                }
                self.assertEqual({k: v for k, v in before.items() if k.name != "harden-proposal.json"}, after_review)
                applied = subprocess.run(
                    [
                        sys.executable, str(launcher), "--project-root", str(root),
                        "feature", "harden", "--apply", "--proposal", harden_payload["proposal_path"],
                    ],
                    cwd=root,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
                applied_payload = json.loads(applied.stdout)
                self.assertEqual(applied_payload["status"], "hardened")
                self.assertRegex(applied_payload["module_design_digest_after"], r"^sha256:[0-9a-f]{64}$")
                self.assertEqual((root / "specs/example/design.md").read_text(encoding="utf-8"), amendment)
                self.assertEqual(
                    (root / "specs/example/features/001-checkout/subfeatures/001-authorize-payment/implementation.md").read_text(encoding="utf-8"),
                    candidate,
                )
                self.assertFalse(attempt.exists())
                adapter = workspace_adapter
                adapter.unlink()
                missing = subprocess.run(
                    [sys.executable, str(adapter), "--project-root", str(root), "--phase", "plan"],
                    cwd=root,
                    text=True,
                    capture_output=True,
                )
                self.assertNotEqual(missing.returncode, 0)


if __name__ == "__main__":
    unittest.main()
