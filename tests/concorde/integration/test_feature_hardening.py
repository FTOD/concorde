import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.concorde.support.feature_workspace import tree_hashes, write_selection
from tests.concorde.support.paths import CONTEXT_PROJECT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.feature_hardening import apply_hardening, propose_hardening  # noqa: E402


CANDIDATE = """# Feature Design: Delivered Feature

## Realization Overview

The accepted implementation realizes delivery through the providing module.

## Module and Feature Collaboration

The root and API features collaborate through their maintained workflow contract.

## Scenario Realization

The primary scenario invokes the providing module and returns the contract-defined result.

## Durable Implementation Decisions

The implementation keeps workspace resolution deterministic and project-relative.

## Traceability and Evidence

Contract and integration tests demonstrate the accepted behavior.

## Known Limitations

No additional delivery variants are hardened in this fixture.
"""


class FeatureHardeningIntegrationTests(unittest.TestCase):
    def project_copy(self, temporary: str, complete: bool = True) -> Path:
        root = Path(temporary) / "project"
        shutil.copytree(CONTEXT_PROJECT, root)
        feature = root / "specs/example/features/001-deliver"
        implementation = feature / "implementation"
        implementation.mkdir()
        marker = "X" if complete else " "
        (implementation / "tasks.md").write_text(
            f"# Tasks\n\n- [{marker}] T001 Implement the fixture behavior\n",
            encoding="utf-8",
        )
        (implementation / "plan.md").write_text("# Plan\n", encoding="utf-8")
        write_selection(root, "specs/example/features/001-deliver")
        return root

    def write_proposal(self, root: Path, eligibility) -> Path:
        path = root / eligibility.result["proposal_path"]
        path.write_text(
            json.dumps(
                {
                    "proposal_version": 1,
                    "operation": "feature.harden",
                    "target": eligibility.target,
                    "source_digest": eligibility.result["source_digest"],
                    "design": {
                        "path": eligibility.result["workspace"]["feature_design"],
                        "content": CANDIDATE,
                    },
                    "remove": [eligibility.result["workspace"]["implementation_dir"]],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return path

    def test_incomplete_tasks_block_without_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary, complete=False)
            before = tree_hashes(root)
            result = propose_hardening(root)
            self.assertEqual(result.status, "invalid")
            self.assertTrue(any(item.rule_id == "CONCORDE-HARDEN-002" for item in result.findings))
            self.assertEqual(tree_hashes(root), before)

    def test_malformed_checkbox_blocks_but_reference_lists_do_not(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            tasks = root / "specs/example/features/001-deliver/implementation/tasks.md"
            tasks.write_text(
                "# Tasks\n\n- [X] T001 Implement the fixture behavior\n\n- T001/T002 may run in parallel.\n",
                encoding="utf-8",
            )
            self.assertEqual(propose_hardening(root).status, "eligible")
            tasks.write_text(
                "# Tasks\n\n- [X] T001 Implement the fixture behavior\n- [maybe] T002 Invalid marker\n",
                encoding="utf-8",
            )
            result = propose_hardening(root)
            self.assertEqual(result.status, "invalid")
            self.assertTrue(any(item.rule_id == "CONCORDE-HARDEN-003" for item in result.findings))

    def test_approved_proposal_updates_design_and_removes_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            eligibility = propose_hardening(root)
            self.assertEqual(eligibility.status, "eligible")
            self.assertEqual(eligibility.result["task_summary"]["complete"], 1)
            proposal = self.write_proposal(root, eligibility)
            result = apply_hardening(root, proposal.relative_to(root).as_posix())
            feature = root / "specs/example/features/001-deliver"
            self.assertEqual(result.status, "hardened")
            self.assertEqual((feature / "design.md").read_text(encoding="utf-8"), CANDIDATE)
            self.assertFalse((feature / "implementation").exists())
            self.assertTrue(result.result["removed_artifacts"])
            self.assertRegex(result.result["design_digest_after"], r"^sha256:[0-9a-f]{64}$")

    def test_changed_attempt_rejects_stale_proposal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            eligibility = propose_hardening(root)
            proposal = self.write_proposal(root, eligibility)
            implementation = root / "specs/example/features/001-deliver/implementation"
            (implementation / "plan.md").write_text("# Changed plan\n", encoding="utf-8")
            before = tree_hashes(root)
            result = apply_hardening(root, proposal.relative_to(root).as_posix())
            self.assertEqual(result.status, "conflict")
            self.assertEqual(tree_hashes(root), before)

    def test_commit_failure_restores_prior_design_and_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            eligibility = propose_hardening(root)
            proposal = self.write_proposal(root, eligibility)
            feature = root / "specs/example/features/001-deliver"
            old_design = (feature / "design.md").read_bytes()
            original_replace = Path.replace

            def fail_staged_design(path: Path, target: Path):
                if path.name == ".design.md.concorde-stage":
                    raise OSError("injected promotion failure")
                return original_replace(path, target)

            with patch.object(Path, "replace", new=fail_staged_design):
                result = apply_hardening(root, proposal.relative_to(root).as_posix())
            self.assertEqual(result.status, "failed")
            self.assertEqual((feature / "design.md").read_bytes(), old_design)
            self.assertTrue((feature / "implementation/tasks.md").is_file())


if __name__ == "__main__":
    unittest.main()
