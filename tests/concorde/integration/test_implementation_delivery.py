import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.concorde.support.feature_workspace import attempt_path, create_feature_file, tree_hashes, write_complete_attempt, write_selection
from tests.concorde.support.paths import CONTEXT_PROJECT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.cli import create_parser, dispatch  # noqa: E402
from concorde.delivery import apply_delivery, propose_delivery  # noqa: E402


FEATURE = "specs/example/features/001-deliver.md"
ATTEMPT = ".concorde/attempts/feature.example.deliver"


class ImplementationDeliveryIntegrationTests(unittest.TestCase):
    def project_copy(self, temporary: str, complete: bool = True) -> Path:
        root = Path(temporary) / "project"
        shutil.copytree(CONTEXT_PROJECT, root)
        feature = root / FEATURE
        if complete:
            write_complete_attempt(feature)
        else:
            attempt = attempt_path(feature)
            attempt.mkdir(parents=True)
            (attempt / "tasks.md").write_text("# Tasks\n\n- [ ] T001 Complete fixture work\n", encoding="utf-8")
            (attempt / "validation.md").write_text("# Validation\n", encoding="utf-8")
        write_selection(root, FEATURE)
        return root

    def write_proposal(self, root: Path, eligibility, **extra) -> Path:
        path = root / eligibility.result["proposal_path"]
        proposal = {
            "proposal_version": 9,
            "tool": "deliver",
            "target": eligibility.target,
            "source_digest": eligibility.result["source_digest"],
            "remove": [eligibility.result["workspace"]["attempt_dir"]],
            **extra,
        }
        path.write_text(json.dumps(proposal) + "\n", encoding="utf-8")
        return path

    def cli_delivery(self, root: Path, *arguments: str):
        parsed = create_parser().parse_args(["--project-root", str(root), "deliver", *arguments])
        return dispatch(parsed)

    def test_cli_propose_materializes_exact_proposal_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            result = self.cli_delivery(root, "--propose")
            self.assertEqual(result.status, "eligible", result.findings)
            proposal = root / result.result["proposal_path"]
            expected = {
                "proposal_version": 9,
                "tool": "deliver",
                "target": result.target,
                "source_digest": result.result["source_digest"],
                "remove": [ATTEMPT],
            }
            self.assertEqual(json.loads(proposal.read_text(encoding="utf-8")), expected)
            self.assertEqual(set(expected), {"proposal_version", "tool", "target", "source_digest", "remove"})
            before = tree_hashes(root)
            pure = propose_delivery(root)
            self.assertEqual(pure.status, "eligible", pure.findings)
            self.assertEqual(pure.result["source_digest"], result.result["source_digest"])
            with patch.object(Path, "replace", side_effect=AssertionError("idempotent propose replaced the proposal")):
                repeated = self.cli_delivery(root, "--propose")
            self.assertEqual(repeated.status, "eligible", repeated.findings)
            self.assertEqual(repeated.result["source_digest"], result.result["source_digest"])
            self.assertEqual(tree_hashes(root), before)

    def test_cli_propose_replaces_an_existing_regular_proposal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            eligibility = propose_delivery(root)
            proposal = root / eligibility.result["proposal_path"]
            proposal.write_text('{"stale":true}\n', encoding="utf-8")
            result = self.cli_delivery(root, "--propose")
            self.assertEqual(result.status, "eligible", result.findings)
            payload = json.loads(proposal.read_text(encoding="utf-8"))
            self.assertEqual(set(payload), {"proposal_version", "tool", "target", "source_digest", "remove"})
            self.assertEqual(payload["source_digest"], eligibility.result["source_digest"])
            self.assertTrue((root / ATTEMPT).is_dir())

    def test_invalid_cli_propose_does_not_mutate_an_existing_proposal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary, complete=False)
            proposal = root / ATTEMPT / "deliver-proposal.json"
            proposal.write_bytes(b"preserve invalid proposal bytes\n")
            before = tree_hashes(root)
            result = self.cli_delivery(root, "--propose")
            self.assertEqual(result.status, "invalid")
            self.assertEqual(tree_hashes(root), before)
            self.assertEqual(proposal.read_bytes(), b"preserve invalid proposal bytes\n")

    def test_cli_propose_rejects_symlink_and_directory_targets_without_mutation(self):
        for target_kind in ("symlink", "directory"):
            with self.subTest(target_kind=target_kind), tempfile.TemporaryDirectory() as temporary:
                root = self.project_copy(temporary)
                eligibility = propose_delivery(root)
                proposal = root / eligibility.result["proposal_path"]
                if target_kind == "symlink":
                    external = root / "external-proposal.json"
                    external.write_bytes(b"external bytes\n")
                    proposal.symlink_to(external)
                else:
                    proposal.mkdir()
                before = tree_hashes(root)
                result = self.cli_delivery(root, "--propose")
                self.assertEqual(result.status, "invalid")
                self.assertEqual(tree_hashes(root), before)
                self.assertEqual(proposal.is_symlink(), target_kind == "symlink")
                self.assertTrue(proposal.exists())

    def test_cli_propose_rejects_a_symlinked_attempt_parent_without_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            attempt = root / ATTEMPT
            external = root / "external-attempt"
            attempt.replace(external)
            attempt.symlink_to(external, target_is_directory=True)
            before = tree_hashes(root)
            result = self.cli_delivery(root, "--propose")
            self.assertEqual(result.status, "invalid")
            self.assertEqual(tree_hashes(root), before)
            self.assertTrue(attempt.is_symlink())
            self.assertFalse((external / "deliver-proposal.json").exists())

    def test_cli_propose_replace_failure_preserves_attempt_and_cleans_stage(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            eligibility = propose_delivery(root)
            proposal = (root / eligibility.result["proposal_path"]).resolve()
            proposal.write_bytes(b"preserve previous proposal bytes\n")
            before = tree_hashes(root)
            original = Path.replace

            def fail_proposal_replace(path: Path, target: Path):
                if Path(target).resolve() == proposal:
                    raise OSError("injected proposal replace failure")
                return original(path, target)

            with patch.object(Path, "replace", new=fail_proposal_replace):
                result = self.cli_delivery(root, "--propose")
            self.assertEqual(result.status, "failed")
            self.assertEqual(tree_hashes(root), before)
            self.assertTrue((root / ATTEMPT).is_dir())
            self.assertEqual(proposal.read_bytes(), b"preserve previous proposal bytes\n")
            self.assertEqual(list((root / ATTEMPT).glob(".deliver-proposal.json.*.concorde-stage")), [])

    def test_cli_apply_revalidates_a_materialized_proposal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            source = root / "src/runtime.py"
            source.parent.mkdir()
            source.write_text("before\n", encoding="utf-8")
            eligibility = self.cli_delivery(root, "--propose")
            self.assertEqual(eligibility.status, "eligible", eligibility.findings)
            proposal_path = eligibility.result["proposal_path"]
            source.write_text("after\n", encoding="utf-8")
            before = tree_hashes(root)
            result = self.cli_delivery(root, "--apply", "--proposal", proposal_path)
            self.assertEqual(result.status, "conflict")
            self.assertEqual(tree_hashes(root), before)
            self.assertTrue((root / ATTEMPT).is_dir())
            self.assertTrue((root / proposal_path).is_file())

    def test_eligible_proposal_is_cleanup_only_and_non_mutating(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            before = tree_hashes(root)
            result = propose_delivery(root)
            self.assertEqual(result.status, "eligible", result.findings)
            self.assertEqual(result.result["proposal_version"], 9)
            self.assertEqual(result.result["changes"], [{"path": ATTEMPT, "action": "delete", "meaning": "Remove the complete temporal attempt; retain every durable and executable authority."}])
            self.assertEqual(result.result["evidence_summary"], {"passed": 1, "missing": 0})
            self.assertNotIn("feature_implementation", result.result["workspace"])
            self.assertEqual(tree_hashes(root), before)

    def test_incomplete_tasks_or_missing_passing_evidence_block_without_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary, complete=False)
            before = tree_hashes(root)
            result = propose_delivery(root)
            self.assertEqual(result.status, "invalid")
            self.assertIn("CONCORDE-DELIVER-002", {item.rule_id for item in result.findings})
            self.assertEqual(tree_hashes(root), before)
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            validation = root / ATTEMPT / "validation.md"
            validation.write_text("# Validation\n\n### T001\n\n- **Outcome**: failed\n", encoding="utf-8")
            before = tree_hashes(root)
            result = propose_delivery(root)
            self.assertEqual(result.status, "invalid")
            self.assertIn("CONCORDE-DELIVER-013", {item.rule_id for item in result.findings})
            self.assertEqual(tree_hashes(root), before)

    def test_compact_evidence_statuses_are_task_bounded_and_read_only(self):
        for outcome, expected_status, passed in (
            ("passed", "eligible", 1),
            ("failed", "invalid", 0),
            ("skipped", "invalid", 0),
        ):
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory() as temporary:
                root = self.project_copy(temporary)
                validation = root / ATTEMPT / "validation.md"
                validation.write_text(
                    "# Validation\n\n## Attempt Evidence\n\n"
                    "- **T001 · Fixture trace**\n"
                    "  - **Check**: deterministic fixture check.\n"
                    f"  - **Outcome**: {outcome}.\n"
                    "  - **Evidence**: fixture record.\n",
                    encoding="utf-8",
                )
                before = tree_hashes(root)
                result = propose_delivery(root)
                self.assertEqual(result.status, expected_status, result.findings)
                self.assertEqual(result.result["evidence_summary"], {"passed": passed, "missing": 1 - passed})
                self.assertEqual(tree_hashes(root), before)

    def test_malformed_compact_evidence_boundaries_are_ignored(self):
        malformed = (
            "- **T01 · Short task ID**",
            "- **T001 - Wrong separator**",
            "- **T001 · **",
            "- **T001 · Missing closing bold",
            "- **T001 · Trailing content** extra",
            "  - **T001 · Nested task record**",
        )
        for boundary in malformed:
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as temporary:
                root = self.project_copy(temporary)
                validation = root / ATTEMPT / "validation.md"
                validation.write_text(
                    "# Validation\n\n## Attempt Evidence\n\n"
                    f"{boundary}\n"
                    "  - **Check**: deterministic fixture check.\n"
                    "  - **Outcome**: passed.\n",
                    encoding="utf-8",
                )
                before = tree_hashes(root)
                result = propose_delivery(root)
                self.assertEqual(result.status, "invalid")
                self.assertEqual(result.result["evidence_summary"], {"passed": 0, "missing": 1})
                self.assertEqual(tree_hashes(root), before)

    def test_legacy_and_compact_evidence_mix_and_deduplicate_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            write_complete_attempt(root / FEATURE, ("T001", "T002"))
            validation = root / ATTEMPT / "validation.md"
            validation.write_text(
                "# Validation\n\n## Attempt Evidence\n\n"
                "### T001 — Legacy trace\n\n"
                "- **Outcome**: passed.\n\n"
                "- **T001 · Duplicate compact trace**\n"
                "  - **Outcome**: passed.\n\n"
                "- **T002 · Compact trace**\n"
                "  - **Check**: deterministic fixture check.\n"
                "  - **Outcome**: passed.\n",
                encoding="utf-8",
            )
            before = tree_hashes(root)
            result = propose_delivery(root)
            self.assertEqual(result.status, "eligible", result.findings)
            self.assertEqual(result.result["evidence_summary"], {"passed": 2, "missing": 0})
            self.assertEqual(tree_hashes(root), before)

    def test_existing_checklists_must_be_complete(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            checklists = root / ATTEMPT / "checklists"
            checklists.mkdir()
            (checklists / "requirements.md").write_text("- [X] Clear\n- [ ] Reviewed\n", encoding="utf-8")
            result = propose_delivery(root)
            self.assertEqual(result.status, "invalid")
            self.assertIn("CONCORDE-DELIVER-009", {item.rule_id for item in result.findings})
            (checklists / "requirements.md").write_text("- [X] Clear\n- [x] Reviewed\n", encoding="utf-8")
            self.assertEqual(propose_delivery(root).status, "eligible")

    def test_success_removes_exactly_attempt_and_retains_authorities_byte_identically(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            source = root / "src/runtime.py"
            source.parent.mkdir()
            source.write_text("def run():\n    return 'ok'\n", encoding="utf-8")
            feature = root / FEATURE
            architecture = root / "specs/example/architecture.md"
            reflection = root / ".concorde/reflections/log.md"
            reflection.parent.mkdir(parents=True, exist_ok=True)
            reflection.write_text("# Reflections: Delivery fixture\n", encoding="utf-8")
            retained_before = {path: path.read_bytes() for path in (source, feature, architecture, reflection)}
            eligibility = propose_delivery(root)
            proposal = self.write_proposal(root, eligibility)
            result = apply_delivery(root, proposal.relative_to(root).as_posix())
            self.assertEqual(result.status, "delivered", result.findings)
            self.assertFalse((root / ATTEMPT).exists())
            self.assertTrue((root / FEATURE).is_file())
            self.assertEqual(retained_before, {path: path.read_bytes() for path in retained_before})
            self.assertEqual([change["action"] for change in result.result["changes"]], ["delete"])
            self.assertIn("executable_context", result.result["retained_digests"])
            self.assertTrue(all(value.startswith("sha256:") for value in result.result["retained_digests"].values()))

    def test_attempt_feature_or_executable_change_makes_proposal_stale(self):
        for mutation in ("attempt", "feature", "source"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                root = self.project_copy(temporary)
                source = root / "src/runtime.py"
                source.parent.mkdir()
                source.write_text("before\n", encoding="utf-8")
                eligibility = propose_delivery(root)
                proposal = self.write_proposal(root, eligibility)
                if mutation == "attempt":
                    (root / ATTEMPT / "tasks.md").write_text("# Tasks\n\n- [X] T001 Complete fixture work\n\nChanged.\n", encoding="utf-8")
                elif mutation == "feature":
                    feature = root / FEATURE
                    feature.write_text(feature.read_text(encoding="utf-8") + "\nChanged.\n", encoding="utf-8")
                else:
                    source.write_text("after\n", encoding="utf-8")
                before = tree_hashes(root)
                result = apply_delivery(root, proposal.relative_to(root).as_posix())
                self.assertEqual(result.status, "conflict")
                self.assertEqual(tree_hashes(root), before)

    def test_proposal_rejects_narrative_updates_and_wrong_remove_set(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            eligibility = propose_delivery(root)
            proposal = self.write_proposal(root, eligibility, implementation={"content": "forbidden"})
            before = tree_hashes(root)
            result = apply_delivery(root, proposal.relative_to(root).as_posix())
            self.assertEqual(result.status, "invalid")
            self.assertEqual(tree_hashes(root), before)
            payload = json.loads(proposal.read_text(encoding="utf-8"))
            payload.pop("implementation")
            payload["remove"] = ["specs/example"]
            proposal.write_text(json.dumps(payload) + "\n", encoding="utf-8")
            before = tree_hashes(root)
            result = apply_delivery(root, proposal.relative_to(root).as_posix())
            self.assertEqual(result.status, "invalid")
            self.assertEqual(tree_hashes(root), before)

    def test_proposal_rejects_undeclared_metadata_without_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            eligibility = propose_delivery(root)
            proposal = self.write_proposal(root, eligibility, metadata={"request_id": "arbitrary"})
            before = tree_hashes(root)
            result = apply_delivery(root, proposal.relative_to(root).as_posix())
            self.assertEqual(result.status, "invalid")
            self.assertIn("unexpected fields: metadata", result.findings[0].message)
            self.assertEqual(tree_hashes(root), before)
            self.assertTrue((root / ATTEMPT).is_dir())

    def test_proposal_rejects_the_legacy_operation_discriminator(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            eligibility = propose_delivery(root)
            proposal = self.write_proposal(root, eligibility)
            payload = json.loads(proposal.read_text(encoding="utf-8"))
            payload["operation"] = payload.pop("tool")
            proposal.write_text(json.dumps(payload) + "\n", encoding="utf-8")
            before = tree_hashes(root)
            result = apply_delivery(root, proposal.relative_to(root).as_posix())
            self.assertEqual(result.status, "invalid")
            self.assertIn("operation discriminator", result.findings[0].message)
            self.assertEqual(tree_hashes(root), before)

    def test_symlinked_attempt_input_is_invalid_and_non_mutating(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            external = root / "external.txt"
            external.write_text("external", encoding="utf-8")
            (root / ATTEMPT / "link.txt").symlink_to(external)
            before = tree_hashes(root)
            result = propose_delivery(root)
            self.assertEqual(result.status, "invalid")
            self.assertTrue(any("symlink" in item.message for item in result.findings))
            self.assertEqual(tree_hashes(root), before)

    def test_atomic_rename_failure_leaves_complete_attempt_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            eligibility = propose_delivery(root)
            proposal = self.write_proposal(root, eligibility)
            before = tree_hashes(root)
            original = Path.replace
            attempt = (root / ATTEMPT).resolve()

            def fail_attempt(path: Path, target: Path):
                if path.resolve() == attempt:
                    raise OSError("injected rename failure")
                return original(path, target)

            with patch.object(Path, "replace", new=fail_attempt):
                result = apply_delivery(root, proposal.relative_to(root).as_posix())
            self.assertEqual(result.status, "failed")
            self.assertEqual(tree_hashes(root), before)

    def test_cleanup_failure_rolls_back_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            eligibility = propose_delivery(root)
            proposal = self.write_proposal(root, eligibility)
            before = tree_hashes(root)
            original = shutil.rmtree
            tombstone = (root / ".concorde/attempts/.feature.example.deliver.concorde-remove").resolve()

            def fail_tombstone(path, *args, **kwargs):
                if Path(path).resolve() == tombstone:
                    raise OSError("injected removal failure")
                return original(path, *args, **kwargs)

            with patch("concorde.delivery.shutil.rmtree", side_effect=fail_tombstone):
                result = apply_delivery(root, proposal.relative_to(root).as_posix())
            self.assertEqual(result.status, "failed")
            self.assertEqual(tree_hashes(root), before)
            self.assertFalse((root / ".concorde/attempts/.feature.example.deliver.concorde-remove").exists())

    def test_partial_cleanup_failure_restores_complete_attempt_from_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            eligibility = propose_delivery(root)
            proposal = self.write_proposal(root, eligibility)
            before = tree_hashes(root)
            original = shutil.rmtree
            tombstone = (root / ".concorde/attempts/.feature.example.deliver.concorde-remove").resolve()

            def partially_remove_tombstone(path, *args, **kwargs):
                if Path(path).resolve() == tombstone:
                    (tombstone / "tasks.md").unlink()
                    raise OSError("injected partial removal failure")
                return original(path, *args, **kwargs)

            with patch("concorde.delivery.shutil.rmtree", side_effect=partially_remove_tombstone):
                result = apply_delivery(root, proposal.relative_to(root).as_posix())
            self.assertEqual(result.status, "failed")
            self.assertEqual(tree_hashes(root), before)
            self.assertTrue((root / ATTEMPT).is_dir())
            self.assertFalse(tombstone.exists())

    def test_delivery_tombstone_is_feature_specific_and_does_not_collide_with_a_sibling_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            sibling = create_feature_file(root, "specs/example/features/002-sibling.md", "feature.example.sibling")
            sibling_attempt = write_complete_attempt(sibling)
            sibling_before = tree_hashes(sibling_attempt)
            eligibility = propose_delivery(root, "feature.example.deliver")
            proposal = self.write_proposal(root, eligibility)
            observed: list[Path] = []
            original = Path.replace
            selected_attempt = (root / ATTEMPT).resolve()

            def observe_tombstone(path: Path, target: Path):
                if path.resolve() == selected_attempt:
                    observed.append(Path(target).resolve())
                return original(path, target)

            with patch.object(Path, "replace", new=observe_tombstone):
                result = apply_delivery(root, proposal.relative_to(root).as_posix())
            self.assertEqual(result.status, "delivered", result.findings)
            self.assertEqual(observed, [(root / ".concorde/attempts/.feature.example.deliver.concorde-remove").resolve()])
            self.assertEqual(tree_hashes(sibling_attempt), sibling_before)


if __name__ == "__main__":
    unittest.main()
