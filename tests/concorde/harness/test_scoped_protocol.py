import copy
import json
import tempfile
import unittest
from pathlib import Path

from concorde.harness.status_store import all_status
from tests.concorde.support.native_planning import OperationHost
from concorde.harness.admission import run_operation
from concorde.harness.context import (
    recheck_context,
    resolve_context,
)
from concorde.spec.repository import SpecError, SpecRepository
from concorde.spec.typed_data import TypedDataError, typed
from concorde.spec.validation import validate_repository
from concorde.spec.verification import verifies
from tests.concorde.spec.support import (
    CONFIGURATION,
    PACKAGE,
    ModelProcessDouble,
    project,
    update_document_declaration,
    update_module,
)


class ScopedProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.registry = project(self.root)

    def call_operation(self, name, data, double=None, mode="execute"):
        self.host = OperationHost(
            self.root,
            PACKAGE,
            executor=double.executor if double else None,
            allow_primary_worktree=True,
            mode=mode,
        )
        return run_operation(
            name, CONFIGURATION, typed(name + "-request", data), host_context=self.host
        )

    @verifies("scenario.harness.context-freeze")
    def test_module_dependencies_and_complete_arbitrary_collections(self):
        repo = SpecRepository(self.root)
        target = repo.select("service.transfer", "scenario.transfer.debit")
        self.assertEqual(("module.ledger",), target.uses)
        self.assertIsNone(target.parent)
        context = resolve_context(
            repo, target.id, focus_id="scenario.transfer.debit"
        ).value
        # uses selects the provider's documents; its own relations select nothing further.
        expected = sorted(target.sources + repo.select("module.ledger").sources)
        self.assertEqual(
            expected,
            [source["path"] for source in context["spec_resolution"]["sources"]],
        )
        self.assertEqual(
            [".concorde/protocol/principles.md", ".concorde/protocol/kinds/module.md"],
            [d["path"] for d in context["protocol"]],
        )
        text = json.dumps(context)
        self.assertNotIn("PRIVATE_CODE", text)
        self.assertNotIn("specs/audit/module.md", text)
        self.assertNotIn("specs/bank/module.md", text)
        self.assertEqual("success", validate_repository(self.root).status)
        participants = repo.module_declaration("scope.bank").uses
        self.assertEqual(
            ["service.transfer", "module.ledger", "scope.audit"],
            [item["target"] for item in participants],
        )
        self.assertTrue(
            all(
                repo.meaning_text("scope.bank", item["meaning"])
                for item in participants
            )
        )

    def test_protocol_handoff_rules_are_bound_context_and_old_binding_is_rejected(self):
        (self.root / "AGENTS.md").write_text("UNTRUSTED_AMBIENT_GUIDANCE")
        (self.root / "CLAUDE.md").write_text("UNTRUSTED_AMBIENT_GUIDANCE")
        repository = SpecRepository(self.root)
        context = resolve_context(repository, "service.transfer").value
        # The rule bundle is indexed by path and digest and granted as a file, never embedded.
        self.assertNotIn("content", context["protocol"][0])
        self.assertIn(
            "### P10. Fresh task sessions, never session moves",
            repository.protocol_assets[context["protocol"][0]["path"]].decode(),
        )
        self.assertNotIn("UNTRUSTED_AMBIENT_GUIDANCE", json.dumps(context))
        path = self.root / ".concorde/config.json"
        config = json.loads(path.read_text())
        config["protocol"]["version"] = "1.0.0"
        path.write_text(json.dumps(config))
        with self.assertRaises(SpecError) as failure:
            SpecRepository(self.root)
        self.assertEqual("protocol_mismatch", failure.exception.code)
        self.assertEqual("1.0.0", json.loads(path.read_text())["protocol"]["version"])

    def test_document_identity_and_membership_are_validated(self):
        paths = [
            "specs/transfer/module.md",
            "specs/transfer/promises.md",
            "specs/ledger/module.md",
        ]
        original = {
            path + ".json": (self.root / (path + ".json")).read_text() for path in paths
        }
        update_document_declaration(
            self.root, "specs/transfer/module.md", owner="module.ledger"
        )
        with self.assertRaisesRegex(SpecError, "owner"):
            resolve_context(SpecRepository(self.root), "service.transfer")
        report = validate_repository(self.root)
        self.assertIn(
            "CHK.document.pair", {finding.rule_id for finding in report.findings}
        )
        for path, text in original.items():
            (self.root / path).write_text(text)
        update_document_declaration(
            self.root, "specs/ledger/module.md", id="document.transfer.feature"
        )
        report = validate_repository(self.root)
        self.assertIn("CHK.node.id", {finding.rule_id for finding in report.findings})
        for path, text in original.items():
            (self.root / path).write_text(text)

    @verifies("scenario.harness.context-gap")
    def test_missing_module_dependency_is_validated_and_stops_context_solving(self):
        path = self.root / "specs/bank/module.md.json"
        metadata = json.loads(path.read_text())
        update_module(
            self.root,
            "scope.bank",
            uses=[
                {**item, "meaning": "#unexplained-" + str(index)}
                for index, item in enumerate(metadata["module"]["uses"])
            ],
        )
        report = validate_repository(self.root)
        self.assertEqual("invalid", report.status)
        self.assertIn(
            "CHK.relation.meaning", {finding.rule_id for finding in report.findings}
        )
        for peer in ("service.transfer", "module.ledger", "scope.audit"):
            self.assertTrue(any(peer in finding.message for finding in report.findings))
        double = ModelProcessDouble()
        result = self.call_operation(
            "concorde-plan",
            {"target_id": "scope.bank", "task": "Plan a banking change"},
            double,
        )
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("spec_incomplete", result["output"]["data"]["outcome"])
        self.assertEqual([], [call["stage"] for call in double.calls])
        from tests.concorde.operations.test_review import issue_observation

        observations = [
            issue_observation(self.root, ref)
            for ref in result["output"]["data"]["blockers"]
        ]
        self.assertTrue(
            all(
                item["source"]["target_id"] == "scope.bank"
                and item["source"]["context_id"]
                == result["output"]["data"]["context_id"]
                for item in observations
            )
        )
        self.assertFalse((self.root / ".concorde/attempts").exists())

    @verifies("scenario.harness.context-gap")
    def test_duplicate_and_unrelated_dependency_declarations_are_rejected(self):
        path = self.root / "specs/bank/module.md.json"
        original = path.read_text()
        registry = (self.root / ".concorde/specs.json").read_text()
        participants = json.loads(original)["module"]["uses"]
        cases = [
            (participants + [copy.deepcopy(participants[0])], "CHK.uses.unique"),
            (
                [
                    {**participants[0], "relies_on": ["req.ledger.unknown"]},
                    *participants[1:],
                ],
                "CHK.relies-on.owned",
            ),
        ]
        for value, rule in cases:
            update_module(self.root, "scope.bank", uses=value)
            report = validate_repository(self.root)
            self.assertEqual("invalid", report.status)
            self.assertIn(rule, {f.rule_id for f in report.findings})
        double = ModelProcessDouble()
        result = self.call_operation(
            "concorde-plan",
            {"target_id": "scope.bank", "task": "Plan a banking change"},
            double,
        )
        self.assertEqual("conflicting", result["output"]["data"]["outcome"])
        self.assertEqual([], result["output"]["data"]["blockers"])
        self.assertEqual([], [call["stage"] for call in double.calls])
        path.write_text(original)
        (self.root / ".concorde/specs.json").write_text(registry)

    def test_module_scenario_focus_is_local(self):
        repo = SpecRepository(self.root)
        self.assertEqual(
            "module.ledger", repo.select("module.ledger", "scenario.ledger.read").id
        )
        with self.assertRaises(SpecError):
            repo.select("module.ledger", "scenario.transfer.debit")
        # The root is the first Module no other Module contains.
        self.registry["modules"].insert(0, self.registry["modules"].pop(3))
        (self.root / ".concorde/specs.json").write_text(json.dumps(self.registry))
        self.assertEqual("module.ledger", SpecRepository(self.root).entry_target)

    @verifies("scenario.harness.typed-reject")
    def test_internal_stage_operation_requires_target_id_at_the_top_level(self):
        with self.assertRaises(TypedDataError) as caught:
            typed("concorde-plan-request", {"task": "Plan the transfer promise"})
        self.assertEqual("invalid_field", caught.exception.code)
        self.assertIn("target_id", caught.exception.field)

    @verifies("scenario.harness.context-stale-recheck")
    def test_selected_context_rechecks_registered_document_bytes_and_membership(self):
        repository = SpecRepository(self.root)
        snapshot = resolve_context(
            repository,
            "scope.bank",
            task="Explain architecture",
        )
        path = self.root / "specs/bank/module.md"
        original = path.read_bytes()
        path.write_bytes(original + b"\nAn added architectural fact.\n")
        with self.assertRaisesRegex(SpecError, "changed"):
            recheck_context(repository, snapshot)
        path.write_bytes(original)
        update_module(
            self.root,
            "scope.bank",
            includes=[
                {
                    "kind": "document",
                    "target": "document.transfer.promises",
                    "reason": "the transfer amount rules",
                }
            ],
        )
        update_document_declaration(
            self.root, "specs/transfer/promises.md", owner="service.transfer"
        )
        with self.assertRaisesRegex(SpecError, "changed"):
            recheck_context(repository, snapshot)

    def test_selected_context_rejects_unavailable_required_source(self):
        (self.root / "specs/bank/module.md").unlink()
        with self.assertRaises(SpecError):
            resolve_context(
                SpecRepository(self.root),
                "scope.bank",
                task="Explain architecture",
            )

    @verifies("scenario.harness.context-stale-recheck")
    def test_membership_changes_invalidate_snapshot(self):
        repo = SpecRepository(self.root)
        snapshot = resolve_context(repo, "service.transfer")
        owns = self.registry["modules"][2]["owns"]
        update_module(self.root, "service.transfer", owns=list(reversed(owns)))
        with self.assertRaisesRegex(SpecError, "changed"):
            recheck_context(repo, snapshot)

    @verifies("scenario.harness.context-stale-recheck")
    def test_another_targets_reference_does_not_change_provider_context(self):
        repo = SpecRepository(self.root)
        snapshot = resolve_context(repo, "service.transfer")
        # Audit's own selection changes; transfer never selects Audit's documents.
        update_module(
            self.root,
            "scope.audit",
            includes=[
                {
                    "kind": "document",
                    "target": "document.transfer.promises",
                    "reason": "the transfer amount rules",
                }
            ],
        )
        update_document_declaration(
            self.root, "specs/transfer/promises.md", owner="service.transfer"
        )
        recheck_context(repo, snapshot)
        self.assertEqual(
            snapshot.id,
            resolve_context(SpecRepository(self.root), "service.transfer").id,
        )

    def test_module_parent_cycle_rejected(self):
        update_module(
            self.root,
            "scope.bank",
            contains=[{"target": "scope.audit", "meaning": "#a"}],
        )
        update_module(
            self.root,
            "scope.audit",
            contains=[{"target": "scope.bank", "meaning": "#b"}],
        )
        with self.assertRaisesRegex(SpecError, "cycle"):
            SpecRepository(self.root)

    def test_spec_symlink_rejected(self):
        (self.root / "specs/transfer/module.md").unlink()
        (self.root / "specs/transfer/module.md").symlink_to(self.root / "secret.py")
        with self.assertRaises(ValueError):
            resolve_context(SpecRepository(self.root), "service.transfer")

    def test_gap_is_recorded_without_creating_a_target_plan(self):
        def gap(stage, snapshot, data, cwd):
            if stage == "context-solve":
                data.update(
                    outcome="spec_incomplete",
                    blockers=[
                        {
                            "question": "Who owns the daily limit?",
                            "blocked_step": "Decide transfer admission",
                            "needed_contract": "Daily limit ownership",
                        }
                    ],
                )

        double = ModelProcessDouble(gap)
        result = self.call_operation(
            "concorde-plan",
            {"target_id": "service.transfer", "task": "Add a daily limit"},
            double,
        )
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("spec_incomplete", result["output"]["data"]["outcome"])
        self.assertEqual(["context-solve"], [call["stage"] for call in double.calls])
        self.assertFalse((self.root / ".concorde/attempts").exists())
        state = all_status(self.root)[0]
        self.assertEqual("blocked", state["status"])
        self.assertEqual({}, state["targets"])

    @verifies(
        "scenario.harness.context-freeze",
        "scenario.concorde.develop-change",
    )
    def test_explicit_work_real_checks_leave_a_ready_change(self):
        double = ModelProcessDouble()
        task = {
            "target_id": "service.transfer",
            "task": "Implement the transfer contract",
        }
        for operation in (
            "concorde-plan",
            "concorde-tasks",
            "concorde-implement",
            "concorde-validate",
        ):
            result = self.call_operation(operation, task, double)
            self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        self.assertEqual("passed", result["output"]["data"]["checks"][0]["status"])
        self.assertFalse((self.root / ".concorde/attempts").exists())
        state = all_status(self.root)[0]
        self.assertEqual("ready", state["status"])
        self.assertEqual(
            [
                "context-solve",
                "plan",
                "tasks",
                "implementation",
            ],
            [c["stage"] for c in double.calls],
        )
        for call in double.calls:
            if call["stage"] not in {"implementation", "code-review"}:
                self.assertNotEqual(self.root, call["cwd"])
                self.assertNotIn("PRIVATE_CODE", call["prompt"])
                self.assertNotIn("TRANSFER_IMPLEMENTATION_CODE", call["prompt"])
            if call["stage"] in {"plan", "tasks"}:
                self.assertEqual(
                    ["app/transfer.py", "checks/transfer_check.py"],
                    [item["path"] for item in call["snapshot"]["implementation_files"]],
                )
                self.assertEqual([], call["snapshot"]["implementation_artifacts"])
        self.assertTrue(
            all(
                d["write_paths"] == []
                for d in self.host.descriptions
                if d["phase"] != "implementation"
            )
        )

    @verifies("scenario.validation.blocked")
    def test_failed_behavioral_check_prevents_delivery(self):
        def broken(stage, snapshot, data, cwd):
            if stage == "implementation":
                (cwd / "app/transfer.py").write_text(
                    "def transfer(balance,amount):\n    return 0\n"
                )

        task = {"target_id": "service.transfer", "task": "Implement transfer"}
        double = ModelProcessDouble(broken)
        for operation in ("concorde-plan", "concorde-tasks", "concorde-implement"):
            result = self.call_operation(operation, task, double)
            self.assertEqual("succeeded", result["status"], result)
        result = self.call_operation("concorde-validate", task, double)
        self.assertEqual("failed", result["status"], result)
        self.assertEqual("failed", result["output"]["data"]["checks"][0]["status"])
        state = all_status(self.root)[0]
        self.assertEqual("failed", state["status"])

    def test_wrong_context_result_rejected(self):
        def wrong(stage, snapshot, data, cwd):
            data["context_id"] = "sha256:" + "0" * 64

        result = self.call_operation(
            "concorde-context-solve",
            {"target_id": "service.transfer", "task": "Explain transfer"},
            ModelProcessDouble(wrong),
        )
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("incompatible_handoff", result["errors"][0]["code"])


if __name__ == "__main__":
    unittest.main()
