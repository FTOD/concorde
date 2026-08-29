import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.concorde.support.feature_workspace import reflection_entry, tree_hashes, write_reflection_log, write_selection
from tests.concorde.support.paths import CONTEXT_PROJECT, RUNTIME_ROOT, TWO_LEVEL_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.feature_hardening import apply_hardening, propose_hardening  # noqa: E402


CANDIDATE = """# Feature Implementation: Delivered Feature

**Realization status**: Hardened fixture milestone.

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

AMENDMENT = """# Design Reference: Example

## Implementation Notes

Delivery resolves the workspace once and caches nothing across phases.

## Design Rationale

A single deterministic resolution keeps every phase's path authority identical.

## Alternatives Considered

Per-phase re-resolution was rejected because it could observe a changed selection mid-lifecycle.

## Decision Log

- Hardened feature.example.deliver with the cached-resolution decision.
"""


class FeatureHardeningIntegrationTests(unittest.TestCase):
    def project_copy(self, temporary: str, complete: bool = True) -> Path:
        root = Path(temporary) / "project"
        shutil.copytree(CONTEXT_PROJECT, root)
        feature = root / "specs/example/features/001-deliver"
        attempt = feature / "attempt"
        attempt.mkdir()
        marker = "X" if complete else " "
        (attempt / "tasks.md").write_text(
            f"# Tasks\n\n- [{marker}] T001 Implement the fixture behavior\n",
            encoding="utf-8",
        )
        (attempt / "plan.md").write_text("# Plan\n", encoding="utf-8")
        write_selection(root, "specs/example/features/001-deliver")
        return root

    def write_checklist(self, root: Path, name: str, content: str) -> Path:
        directory = root / "specs/example/features/001-deliver/attempt/checklists"
        directory.mkdir(exist_ok=True)
        path = directory / name
        path.write_text(content, encoding="utf-8")
        return path

    def write_proposal(self, root: Path, eligibility, module_design: str | None = None, module_design_path: str | None = None, design_path: str | None = None) -> Path:
        path = root / eligibility.result["proposal_path"]
        proposal = {
            "proposal_version": 4,
            "operation": "feature.harden",
            "target": eligibility.target,
            "source_digest": eligibility.result["source_digest"],
            "implementation": {
                "path": design_path or eligibility.result["workspace"]["feature_implementation"],
                "content": CANDIDATE,
            },
            "remove": [eligibility.result["workspace"]["attempt_dir"]],
        }
        if module_design is not None:
            proposal["module_design"] = {
                "path": module_design_path or eligibility.result["workspace"]["module_design"],
                "content": module_design,
            }
        path.write_text(json.dumps(proposal) + "\n", encoding="utf-8")
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
            tasks = root / "specs/example/features/001-deliver/attempt/tasks.md"
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
            attempt = root / "specs/example/features/001-deliver/attempt"
            external = root / "external-checklist.md"
            external.write_text("- [X] External\n", encoding="utf-8")
            checklists = attempt / "checklists"
            checklists.mkdir()
            (checklists / "requirements.md").symlink_to(external)
            result = propose_hardening(root)
            self.assertEqual(result.status, "invalid")
            self.assertTrue(any("symlink" in item.message for item in result.findings))

        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            attempt = root / "specs/example/features/001-deliver/attempt"
            external = root / "external-checklists"
            external.mkdir()
            (external / "requirements.md").write_text("- [X] External\n", encoding="utf-8")
            (attempt / "checklists").symlink_to(external, target_is_directory=True)
            result = propose_hardening(root)
            self.assertEqual(result.status, "invalid")
            self.assertTrue(any("symlink" in item.message for item in result.findings))

    def test_approved_proposal_updates_realization_and_removes_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            eligibility = propose_hardening(root)
            self.assertEqual(eligibility.status, "eligible")
            self.assertEqual(eligibility.result["task_summary"]["complete"], 1)
            self.assertEqual(eligibility.result["workspace"]["module_design"], "specs/example/design.md")
            self.assertIn("specs/example/design.md", eligibility.artifacts)
            module_design_before = (root / "specs/example/design.md").read_bytes()
            proposal = self.write_proposal(root, eligibility)
            result = apply_hardening(root, proposal.relative_to(root).as_posix())
            feature = root / "specs/example/features/001-deliver"
            self.assertEqual(result.status, "hardened")
            self.assertEqual((feature / "implementation.md").read_text(encoding="utf-8"), CANDIDATE)
            self.assertFalse((feature / "attempt").exists())
            self.assertFalse((feature / "implementation").exists())
            self.assertTrue(result.result["removed_artifacts"])
            self.assertRegex(result.result["implementation_digest_before"], r"^sha256:[0-9a-f]{64}$")
            self.assertRegex(result.result["implementation_digest_after"], r"^sha256:[0-9a-f]{64}$")
            self.assertIn("specs/example/features/001-deliver/abstract.md", result.result["retained_artifacts"])
            self.assertIn("specs/example/features/001-deliver/design.md", result.result["retained_artifacts"])
            self.assertIsNone(result.result["module_design_digest_after"])
            self.assertEqual((root / "specs/example/design.md").read_bytes(), module_design_before)
            self.assertIn("specs/example/design.md", result.result["retained_artifacts"])
            self.assertIn("specs/example/module.md", result.result["retained_artifacts"])

    def test_approved_proposal_amends_module_design_reference_atomically(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            module_summary_before = (root / "specs/example/module.md").read_bytes()
            eligibility = propose_hardening(root)
            proposal = self.write_proposal(root, eligibility, module_design=AMENDMENT)
            result = apply_hardening(root, proposal.relative_to(root).as_posix())
            self.assertEqual(result.status, "hardened", result.findings)
            self.assertEqual((root / "specs/example/design.md").read_text(encoding="utf-8"), AMENDMENT)
            self.assertEqual((root / "specs/example/module.md").read_bytes(), module_summary_before)
            self.assertRegex(result.result["module_design_digest_before"], r"^sha256:[0-9a-f]{64}$")
            self.assertRegex(result.result["module_design_digest_after"], r"^sha256:[0-9a-f]{64}$")
            self.assertEqual([change["path"] for change in result.result["changes"]], [
                "specs/example/features/001-deliver/implementation.md",
                "specs/example/design.md",
                "specs/example/features/001-deliver/attempt",
            ])
            self.assertNotIn("specs/example/design.md", result.result["retained_artifacts"])

    def test_eligible_proposal_mode_with_module_reference_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            before = tree_hashes(root)
            result = propose_hardening(root)
            self.assertEqual(result.status, "eligible")
            self.assertEqual(result.result["workspace"]["module_design"], "specs/example/design.md")
            self.assertEqual(result.result["workspace"]["module_summary"], "specs/example/module.md")
            self.assertEqual([change["action"] for change in result.result["changes"]], ["update", "delete"])
            self.assertEqual(tree_hashes(root), before)

    def test_changed_module_design_after_proposal_is_a_conflict(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            eligibility = propose_hardening(root)
            proposal = self.write_proposal(root, eligibility, module_design=AMENDMENT)
            (root / "specs/example/design.md").write_text("# Design Reference: Example\n\n## Decision Log\n\n- edited after review\n", encoding="utf-8")
            before = tree_hashes(root)
            result = apply_hardening(root, proposal.relative_to(root).as_posix())
            self.assertEqual(result.status, "conflict")
            self.assertEqual(tree_hashes(root), before)

    def test_amendment_may_not_target_module_summary_or_feature_root_design(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            eligibility = propose_hardening(root)
            for bad_path, fragment in (
                ("specs/example/module.md", "module summary"),
                ("specs/example/features/001-deliver/design.md", "not a path inside the feature root"),
                ("specs/example/modules/api/design.md", "providing module"),
            ):
                proposal = self.write_proposal(root, eligibility, module_design=AMENDMENT, module_design_path=bad_path)
                before = tree_hashes(root)
                result = apply_hardening(root, proposal.relative_to(root).as_posix())
                self.assertEqual(result.status, "invalid", bad_path)
                self.assertTrue(any(fragment in item.message for item in result.findings), (bad_path, result.findings))
                self.assertEqual(tree_hashes(root), before)

    def test_changed_attempt_rejects_stale_proposal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            eligibility = propose_hardening(root)
            proposal = self.write_proposal(root, eligibility)
            attempt = root / "specs/example/features/001-deliver/attempt"
            (attempt / "plan.md").write_text("# Changed plan\n", encoding="utf-8")
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

    def test_commit_failure_restores_prior_realization_reference_and_attempt(self):
        for failing_parent in ("specs/example/features/001-deliver", "specs/example"):
            with tempfile.TemporaryDirectory() as temporary:
                root = self.project_copy(temporary)
                eligibility = propose_hardening(root)
                proposal = self.write_proposal(root, eligibility, module_design=AMENDMENT)
                feature = root / "specs/example/features/001-deliver"
                before = tree_hashes(root)
                original_replace = Path.replace
                staged_name = ".implementation.md.concorde-stage" if failing_parent.endswith("001-deliver") else ".design.md.concorde-stage"
                failing_stage = (root / failing_parent / staged_name).resolve()

                def fail_staged(path: Path, target: Path, _stage=failing_stage):
                    if path.resolve() == _stage:
                        raise OSError("injected promotion failure")
                    return original_replace(path, target)

                with patch.object(Path, "replace", new=fail_staged):
                    result = apply_hardening(root, proposal.relative_to(root).as_posix())
                self.assertEqual(result.status, "failed", failing_stage)
                self.assertTrue((feature / "attempt/tasks.md").is_file())
                self.assertEqual(tree_hashes(root), before, failing_stage)
                self.assertFalse(list(root.rglob(".*.concorde-stage")) + list(root.rglob(".*.concorde-backup")))

    def test_subfeature_hardening_preserves_parent_and_sibling(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(TWO_LEVEL_PROJECT, root)
            child = root / "specs/example/features/001-checkout/subfeatures/001-authorize-payment"
            (child / "attempt/tasks.md").write_text("# Tasks\n\n- [X] T001 Complete child\n", encoding="utf-8")
            write_selection(root, child.relative_to(root).as_posix())
            parent = root / "specs/example/features/001-checkout"
            sibling = parent / "subfeatures/002-confirm-order"
            parent_bytes = {(parent / name).relative_to(root): (parent / name).read_bytes() for name in ("abstract.md", "design.md", "implementation.md")}
            module_bytes = {name: (root / "specs/example" / name).read_bytes() for name in ("module.md", "design.md")}
            sibling_before = tree_hashes(sibling)
            eligibility = propose_hardening(root)
            self.assertEqual(eligibility.status, "eligible")
            proposal = self.write_proposal(root, eligibility)
            result = apply_hardening(root, proposal.relative_to(root).as_posix())
            self.assertEqual(result.status, "hardened")
            self.assertFalse((child / "attempt").exists())
            self.assertEqual(sibling_before, tree_hashes(sibling))
            self.assertEqual(parent_bytes, {(parent / name).relative_to(root): (parent / name).read_bytes() for name in ("abstract.md", "design.md", "implementation.md")})
            self.assertEqual(module_bytes, {name: (root / "specs/example" / name).read_bytes() for name in ("module.md", "design.md")})
            self.assertIn("specs/example/features/001-checkout/implementation.md", result.result["retained_artifacts"])
            self.assertIn("specs/example/features/001-checkout/design.md", result.result["retained_artifacts"])
            self.assertIn("specs/example/features/001-checkout/abstract.md", result.result["retained_artifacts"])
            self.assertIn("specs/example/module.md", result.result["retained_artifacts"])

    def test_proposal_may_not_target_abstract_spec_or_legacy_realization_name(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            eligibility = propose_hardening(root)
            for bad_path in (
                "specs/example/features/001-deliver/abstract.md",
                "specs/example/features/001-deliver/design.md",
                "specs/example/module.md",
            ):
                proposal = self.write_proposal(root, eligibility, design_path=bad_path)
                before = tree_hashes(root)
                result = apply_hardening(root, proposal.relative_to(root).as_posix())
                self.assertEqual(result.status, "invalid", bad_path)
                self.assertTrue(any("never writes abstract.md, design.md" in item.message for item in result.findings), (bad_path, result.findings))
                self.assertEqual(tree_hashes(root), before)
            legacy = root / eligibility.result["proposal_path"]
            payload = json.loads(legacy.read_text(encoding="utf-8"))
            payload["design"] = payload.pop("implementation")
            legacy.write_text(json.dumps(payload) + "\n", encoding="utf-8")
            before = tree_hashes(root)
            result = apply_hardening(root, legacy.relative_to(root).as_posix())
            self.assertEqual(result.status, "invalid")
            self.assertEqual(tree_hashes(root), before)

    def test_changed_abstract_after_proposal_is_a_conflict(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            eligibility = propose_hardening(root)
            self.assertIn("specs/example/features/001-deliver/abstract.md", eligibility.artifacts)
            proposal = self.write_proposal(root, eligibility)
            abstract = root / "specs/example/features/001-deliver/abstract.md"
            abstract.write_text(abstract.read_text(encoding="utf-8") + "\nEdited after review.\n", encoding="utf-8")
            before = tree_hashes(root)
            result = apply_hardening(root, proposal.relative_to(root).as_posix())
            self.assertEqual(result.status, "conflict")
            self.assertEqual(tree_hashes(root), before)

    def test_first_hardening_overwrites_placeholder_in_full(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            implementation = root / "specs/example/features/001-deliver/implementation.md"
            implementation.write_text(
                "# Feature Implementation: Deliver\n\n## Realization Overview\n\nNo implementation realization has been hardened yet.\n",
                encoding="utf-8",
            )
            eligibility = propose_hardening(root)
            proposal = self.write_proposal(root, eligibility)
            result = apply_hardening(root, proposal.relative_to(root).as_posix())
            self.assertEqual(result.status, "hardened", result.findings)
            self.assertEqual(implementation.read_text(encoding="utf-8"), CANDIDATE)
            self.assertNotIn("No implementation realization has been hardened yet.", implementation.read_text(encoding="utf-8"))


class ReflectionHardeningTests(FeatureHardeningIntegrationTests):
    """Hardening reads the project reflection log, summarizes the feature's entries, and gates on open ones."""

    def project_with_log(self, temporary: str, entries) -> Path:
        root = self.project_copy(temporary)
        write_reflection_log(root, entries)
        return root

    def test_eligible_result_summarizes_only_the_target_feature_entries(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_with_log(temporary, [
                reflection_entry("R-001"),
                reflection_entry("R-002", status="resolved"),
                reflection_entry("R-003", status="dismissed"),
                reflection_entry("R-004", feature="feature.example.api.invoke"),
            ])
            eligibility = propose_hardening(root)
            self.assertEqual(eligibility.status, "eligible", eligibility.findings)
            self.assertEqual(eligibility.result["reflection_summary"], {"entries": 3, "open": 1, "resolved": 1, "dismissed": 1})
            from concorde.diagnostics import operation_envelope
            self.assertEqual(operation_envelope(eligibility)["reflection_summary"], {"entries": 3, "open": 1, "resolved": 1, "dismissed": 1})
            self.assertEqual(eligibility.result["workspace"]["reflections"], "specs/example/reflections.md")
            self.assertEqual(eligibility.result["workspace"]["reflections_open"], 1)
            self.assertIn("specs/example/reflections.md", eligibility.artifacts)

    def test_project_without_a_log_still_hardens(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            eligibility = propose_hardening(root)
            self.assertEqual(eligibility.result["reflection_summary"], {"entries": 0, "open": 0, "resolved": 0, "dismissed": 0})
            result = apply_hardening(root, self.write_proposal(root, eligibility).relative_to(root).as_posix())
            self.assertEqual(result.status, "hardened", result.findings)

    def test_malformed_log_blocks_eligibility_without_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_with_log(temporary, [reflection_entry("R-001", Kind="bug")])
            before = tree_hashes(root)
            eligibility = propose_hardening(root)
            self.assertEqual(eligibility.status, "invalid")
            self.assertEqual([item.rule_id for item in eligibility.findings], ["CONCORDE-HARDEN-011"])
            self.assertEqual(eligibility.findings[0].source, "specs/example/reflections.md")
            self.assertEqual(tree_hashes(root), before)

    def test_uncited_open_entry_refuses_apply_and_preserves_attempt_and_log(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_with_log(temporary, [reflection_entry("R-001"), reflection_entry("R-002", feature="feature.example.api.invoke")])
            eligibility = propose_hardening(root)
            proposal = self.write_proposal(root, eligibility)
            before = tree_hashes(root)
            result = apply_hardening(root, proposal.relative_to(root).as_posix())
            self.assertEqual(result.status, "invalid")
            self.assertEqual([item.rule_id for item in result.findings], ["CONCORDE-HARDEN-012"])
            self.assertIn("R-001", result.findings[0].message)
            self.assertNotIn("R-002", result.findings[0].message)
            self.assertEqual(tree_hashes(root), before)

    def test_cited_open_entries_harden_and_leave_the_log_byte_identical(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_with_log(temporary, [reflection_entry("R-001"), reflection_entry("R-002", status="resolved"), reflection_entry("R-003", feature="feature.example.api.invoke")])
            log_before = (root / "specs/example/reflections.md").read_bytes()
            eligibility = propose_hardening(root)
            path = root / eligibility.result["proposal_path"]
            proposal = json.loads(self.write_proposal(root, eligibility).read_text(encoding="utf-8"))
            proposal["implementation"]["content"] = CANDIDATE.replace("No additional delivery variants are hardened in this fixture.", "Open reflection R-001 (fallback command) remains unresolved.")
            path.write_text(json.dumps(proposal) + "\n", encoding="utf-8")
            result = apply_hardening(root, path.relative_to(root).as_posix())
            self.assertEqual(result.status, "hardened", result.findings)
            self.assertEqual((root / "specs/example/reflections.md").read_bytes(), log_before)
            self.assertEqual(result.result["reflection_summary"], {"entries": 2, "open": 1, "resolved": 1, "dismissed": 0})
            self.assertIn("specs/example/reflections.md", result.result["retained_artifacts"])
            self.assertFalse((root / "specs/example/features/001-deliver/attempt").exists())

    def test_log_changed_after_proposal_is_a_conflict(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_with_log(temporary, [reflection_entry("R-001", status="resolved")])
            eligibility = propose_hardening(root)
            proposal = self.write_proposal(root, eligibility)
            write_reflection_log(root, [reflection_entry("R-001", status="resolved"), reflection_entry("R-002", status="dismissed")])
            result = apply_hardening(root, proposal.relative_to(root).as_posix())
            self.assertEqual(result.status, "conflict")
            self.assertEqual([item.rule_id for item in result.findings], ["CONCORDE-HARDEN-004"])


if __name__ == "__main__":
    unittest.main()
