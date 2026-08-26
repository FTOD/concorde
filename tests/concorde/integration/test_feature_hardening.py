import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.concorde.support.feature_workspace import tree_hashes, write_selection
from tests.concorde.support.paths import CONTEXT_PROJECT, RUNTIME_ROOT, TWO_LEVEL_PROJECT

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

    def write_checklist(self, root: Path, name: str, content: str) -> Path:
        directory = root / "specs/example/features/001-deliver/implementation/checklists"
        directory.mkdir(exist_ok=True)
        path = directory / name
        path.write_text(content, encoding="utf-8")
        return path

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

    def test_missing_checklist_directory_is_eligible_with_zero_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            result = propose_hardening(root)
            self.assertEqual(result.status, "eligible")
            self.assertEqual(
                result.result["checklist_summary"],
                {"files": 0, "complete": 0, "incomplete": 0, "malformed": 0},
            )

    def test_resolved_multiple_checklists_are_eligible(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            self.write_checklist(root, "requirements.md", "# Requirements\n\n- [X] Clear\n- [x] Testable\n")
            self.write_checklist(root, "security.md", "# Security\n\n- [X] Threats reviewed\n")
            result = propose_hardening(root)
            self.assertEqual(result.status, "eligible")
            self.assertEqual(
                result.result["checklist_summary"],
                {"files": 2, "complete": 3, "incomplete": 0, "malformed": 0},
            )

    def test_unresolved_or_malformed_checklist_item_blocks_without_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            checklist = self.write_checklist(
                root,
                "requirements.md",
                "# Requirements\n\n- [X] Clear\n- [ ] Still unresolved\n",
            )
            before = tree_hashes(root)
            result = propose_hardening(root)
            self.assertEqual(result.status, "invalid")
            self.assertTrue(any(item.rule_id == "CONCORDE-HARDEN-009" for item in result.findings))
            self.assertEqual(result.result["checklist_summary"]["incomplete"], 1)
            self.assertEqual(tree_hashes(root), before)

            checklist.write_text("# Requirements\n\n- [X] Clear\n- [maybe] Invalid marker\n", encoding="utf-8")
            before = tree_hashes(root)
            result = propose_hardening(root)
            self.assertEqual(result.status, "invalid")
            self.assertTrue(any(item.rule_id == "CONCORDE-HARDEN-010" for item in result.findings))
            self.assertEqual(result.result["checklist_summary"]["malformed"], 1)
            self.assertEqual(tree_hashes(root), before)

    def test_symlinked_checklist_file_or_directory_is_invalid(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            implementation = root / "specs/example/features/001-deliver/implementation"
            external = root / "external-checklist.md"
            external.write_text("- [X] External\n", encoding="utf-8")
            checklists = implementation / "checklists"
            checklists.mkdir()
            (checklists / "requirements.md").symlink_to(external)
            result = propose_hardening(root)
            self.assertEqual(result.status, "invalid")
            self.assertTrue(any("symlink" in item.message for item in result.findings))

        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            implementation = root / "specs/example/features/001-deliver/implementation"
            external = root / "external-checklists"
            external.mkdir()
            (external / "requirements.md").write_text("- [X] External\n", encoding="utf-8")
            (implementation / "checklists").symlink_to(external, target_is_directory=True)
            result = propose_hardening(root)
            self.assertEqual(result.status, "invalid")
            self.assertTrue(any("symlink" in item.message for item in result.findings))

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

    def test_checklist_change_after_proposal_is_revalidated_without_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            checklist = self.write_checklist(root, "requirements.md", "# Requirements\n\n- [X] Reviewed\n")
            eligibility = propose_hardening(root)
            self.assertEqual(eligibility.status, "eligible")
            proposal = self.write_proposal(root, eligibility)
            checklist.write_text("# Requirements\n\n- [ ] Reviewed\n", encoding="utf-8")
            before = tree_hashes(root)
            result = apply_hardening(root, proposal.relative_to(root).as_posix())
            self.assertEqual(result.status, "invalid")
            self.assertTrue(any(item.rule_id == "CONCORDE-HARDEN-009" for item in result.findings))
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

    def test_subfeature_hardening_preserves_parent_and_sibling(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(TWO_LEVEL_PROJECT, root)
            child = root / "specs/example/features/001-checkout/subfeatures/001-authorize-payment"
            (child / "implementation/tasks.md").write_text("# Tasks\n\n- [X] T001 Complete child\n", encoding="utf-8")
            write_selection(root, child.relative_to(root).as_posix())
            parent = root / "specs/example/features/001-checkout"
            sibling = parent / "subfeatures/002-confirm-order"
            parent_bytes = {(parent / name).relative_to(root): (parent / name).read_bytes() for name in ("spec.md", "design.md")}
            sibling_before = tree_hashes(sibling)
            eligibility = propose_hardening(root)
            self.assertEqual(eligibility.status, "eligible")
            proposal = self.write_proposal(root, eligibility)
            result = apply_hardening(root, proposal.relative_to(root).as_posix())
            self.assertEqual(result.status, "hardened")
            self.assertFalse((child / "implementation").exists())
            self.assertEqual(sibling_before, tree_hashes(sibling))
            self.assertEqual(parent_bytes, {(parent / name).relative_to(root): (parent / name).read_bytes() for name in ("spec.md", "design.md")})
            self.assertIn("specs/example/features/001-checkout/spec.md", result.result["retained_artifacts"])


if __name__ == "__main__":
    unittest.main()
