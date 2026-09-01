import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.feature_workspace import create_feature_root
from tests.concorde.support.paths import CONTEXT_PROJECT, REPOSITORY_ROOT, TWO_LEVEL_PROJECT


WORKSPACE_ADAPTER = REPOSITORY_ROOT / "extensions/concorde/scripts/python/workspace.py"
PYTHON = REPOSITORY_ROOT / ".venv/bin/python"


def copy_fixture(temporary: str, fixture: Path) -> Path:
    root = Path(temporary) / "project"
    shutil.copytree(fixture, root)
    return root


def run_phase(root: Path, feature: str, phase: str) -> dict:
    completed = subprocess.run(
        [
            str(PYTHON),
            str(WORKSPACE_ADAPTER),
            "--project-root",
            str(root),
            "--feature-directory",
            feature,
            "--phase",
            phase,
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def file_hashes(root: Path, relative_paths: tuple[str, ...]) -> dict[str, str]:
    return {
        relative: hashlib.sha256((root / relative).read_bytes()).hexdigest()
        for relative in relative_paths
    }


class PlanDeliveryWorkspaceIntegrationTests(unittest.TestCase):
    def test_top_level_phases_share_one_attempt_and_preserve_durable_authorities(self):
        feature = "specs/example/features/001-deliver"
        authorities = (
            f"{feature}/abstract.md",
            f"{feature}/design.md",
            f"{feature}/implementation.md",
            "specs/example/module.md",
            "specs/example/design.md",
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = copy_fixture(temporary, CONTEXT_PROJECT)
            before = file_hashes(root, authorities)
            payloads = [run_phase(root, feature, phase) for phase in ("plan", "tasks", "taskstoissues")]
            self.assertEqual(file_hashes(root, authorities), before)
            for payload in payloads:
                workspace = payload["workspace"]
                self.assertEqual(payload["schema_version"], 9)
                self.assertEqual(payload["phase_root"], f"{feature}/attempt")
                self.assertEqual(workspace["workspace_kind"], "feature")
                self.assertEqual(workspace["feature_implementation"], f"{feature}/implementation.md")
                self.assertEqual(workspace["attempt_dir"], f"{feature}/attempt")
            for forbidden in ("plan.md", "tasks.md", "checklists"):
                self.assertFalse((root / feature / forbidden).exists(), forbidden)

    def test_child_phases_expose_parent_trio_and_bounded_siblings_without_mutation(self):
        feature = "specs/example/features/001-checkout/subfeatures/002-confirm-order"
        parent = "specs/example/features/001-checkout"
        authorities = (
            f"{feature}/abstract.md",
            f"{feature}/design.md",
            f"{feature}/implementation.md",
            f"{parent}/abstract.md",
            f"{parent}/design.md",
            f"{parent}/implementation.md",
            "specs/example/module.md",
            "specs/example/design.md",
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = copy_fixture(temporary, TWO_LEVEL_PROJECT)
            before = file_hashes(root, authorities)
            payloads = [run_phase(root, feature, phase) for phase in ("plan", "tasks", "taskstoissues")]
            self.assertEqual(file_hashes(root, authorities), before)
            for payload in payloads:
                workspace = payload["workspace"]
                self.assertEqual(payload["phase_root"], f"{feature}/attempt")
                self.assertEqual(workspace["workspace_kind"], "subfeature")
                self.assertEqual(
                    set(workspace["parent_context"]),
                    {
                        "feature_id",
                        "feature_directory",
                        "feature_abstract",
                        "feature_design",
                        "feature_implementation",
                    },
                )
                self.assertEqual(workspace["parent_context"]["feature_abstract"], f"{parent}/abstract.md")
                self.assertEqual(workspace["parent_context"]["feature_design"], f"{parent}/design.md")
                self.assertEqual(
                    workspace["parent_context"]["feature_implementation"],
                    f"{parent}/implementation.md",
                )
                self.assertEqual(len(workspace["siblings"]), 1)
                self.assertEqual(
                    set(workspace["siblings"][0]),
                    {
                        "feature_id",
                        "title",
                        "outcome",
                        "evidence_status",
                        "feature_directory",
                        "abstract",
                        "design",
                        "implementation",
                    },
                )
                self.assertNotIn("body", json.dumps(workspace["siblings"]).lower())
            for forbidden in ("plan.md", "tasks.md", "checklists"):
                self.assertFalse((root / feature / forbidden).exists(), forbidden)

    def test_placeholder_and_accepted_baselines_remain_distinguishable_and_unchanged(self):
        feature = "specs/example/features/001-plan"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            selected = create_feature_root(root, feature, "feature.example.plan")
            placeholder = (selected / "implementation.md").read_bytes()
            payload = run_phase(root, feature, "plan")
            self.assertIn("No implementation realization has been accepted yet.", placeholder.decode())
            self.assertEqual((selected / "implementation.md").read_bytes(), placeholder)
            self.assertEqual(payload["workspace"]["feature_implementation"], f"{feature}/implementation.md")

        accepted_feature = "specs/example/features/001-deliver"
        with tempfile.TemporaryDirectory() as temporary:
            root = copy_fixture(temporary, CONTEXT_PROJECT)
            implementation = root / accepted_feature / "implementation.md"
            accepted = implementation.read_bytes()
            payload = run_phase(root, accepted_feature, "plan")
            self.assertIn("Accepted fixture baseline", accepted.decode())
            self.assertEqual(implementation.read_bytes(), accepted)
            self.assertEqual(
                payload["workspace"]["feature_implementation"],
                f"{accepted_feature}/implementation.md",
            )


if __name__ == "__main__":
    unittest.main()
