"""Readiness of planned and direct candidates through `concorde-validate` in real Git worktrees.

The accepted plan and completed tasks are recorded directly in Planning's section of the change
status, as planning and implementation would leave them; validation itself runs unmodified.
"""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from concorde.harness import checks as check_service
from concorde.harness.change_worktree import (
    ensure_change,
    read_change,
    save_change,
    snapshot_tree,
)
from concorde.harness.check_executor import CheckSandboxError
from concorde.harness.checks import check_revision
from concorde.harness.host import OperationHost
from concorde.harness.invocation import Invocation
from concorde.harness.revisions import implementation_digest, target_revision
from concorde.issues.store import report_issue
from concorde.planning.gaps import open_gaps, record_task_gaps
from concorde.planning.records import save_target_state, target_state, targets
from concorde.planning.scope import component_intent
from concorde.review.review import require_reviews
from concorde.spec.repository import SpecRepository
from concorde.spec.verification import verifies
from concorde.validation.records import validation_records
from tests.concorde.support.issue_reports import report, source
from tests.concorde.support.spec_project import CONFIGURATION, PACKAGE
from tests.concorde.support.worktree_project import WorktreeProject

TRANSFER = (
    "def transfer(balance, amount):\n"
    "    if amount <= 0 or amount > balance:\n"
    '        raise ValueError("invalid transfer")\n'
    "    return balance - amount\n"
)
LEDGER_CHECK = {
    "id": "check.ledger",
    "module": "module.ledger",
    "argv": [
        "{python}",
        "-c",
        (
            "import sys; sys.path.insert(0, '.'); from app.ledger import read; "
            "assert read('alice') == 5"
        ),
    ],
    "timeout_seconds": 10,
}
LEDGER_TASK = {
    "id": "T2",
    "target_id": "module.ledger",
    "description": "Store the balances transfers read.",
    "acceptance": "The ledger check passes.",
}
COMPONENT_TASK = component_intent([LEDGER_TASK])
LEDGER = "BALANCES = {'alice': 5}\n\ndef read(account_id):\n    return BALANCES[account_id]\n"


class ReadinessTests(WorktreeProject, unittest.TestCase):
    def repository(self):
        return SpecRepository(self.change, PACKAGE)

    def record_work(self, target_id, task, *, complete=True, components=()):
        """Record an accepted plan with one task, as planning and implementation leave it."""
        repository = self.repository()
        target = repository.module(target_id)
        entry = target_state(self.change, target_id, None, create=True)
        entry.update(
            task=task,
            constraints=[],
            plan="Implement the contract.",
            tasks=[
                {
                    "id": "T1",
                    "target_id": target_id,
                    "description": task,
                    "acceptance": "The configured checks pass.",
                    "complete": complete,
                }
            ],
            spec_digest=target_revision(repository, target),
            implementation_digest=implementation_digest(repository, target),
            phase="implementation",
            status="completed" if complete else "active",
        )
        if components:
            entry["component_revisions"] = {
                item: {
                    "spec": target_revision(repository, repository.module(item)),
                    "implementation": implementation_digest(
                        repository, repository.module(item)
                    ),
                }
                for item in components
            }
        save_target_state(self.change, entry)

    def planned_change(self, *, complete=True):
        """A change about the transfer Module whose candidate implemented its one task."""
        (self.change / "app/transfer.py").write_text(TRANSFER)
        change = ensure_change(self.change, task=self.task)
        change["target_id"] = self.task["target_id"]
        save_change(self.change, change)
        self.record_work(self.task["target_id"], self.task["task"], complete=complete)
        return read_change(self.change, required=True)["change_id"]

    def validate(self, root=None, **extra):
        return self.call_operation(
            root or self.change, "concorde-validate", {**self.task, **extra}
        )

    def change_status(self):
        return read_change(self.change, required=True)

    def entry(self, target_id="service.transfer"):
        return targets(self.change_status())[target_id]

    def assert_not_ready(self):
        change = self.change_status()
        self.assertNotEqual("ready", change["status"])
        self.assertIsNone(validation_records(change).get("validated_tree"))

    def refused(self, result, code):
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual(code, result["errors"][0]["code"], result)

    @verifies("scenario.validation.ready")
    def test_a_planned_change_meeting_every_gate_becomes_ready(self):
        self.planned_change()
        result = self.validate()
        self.assertEqual("succeeded", result["status"], result)
        data = result["output"]["data"]
        self.assertEqual("ready", data["outcome"], result)
        self.assertNotIn("complete", data["answer"].lower())
        self.assertEqual(
            ["check.transfer"], [item["check_id"] for item in data["checks"]]
        )
        entry = self.entry()
        repository = self.repository()
        transfer = repository.module("service.transfer")
        self.assertEqual(("ready", "ready"), (entry["phase"], entry["status"]))
        self.assertEqual(
            [check_revision(repository, transfer)],
            [item["source_digest"] for item in entry["checks"]],
        )
        self.assertTrue(entry["validation_spec_digest"].startswith("sha256:"))
        self.assertTrue(entry["implementation_impacts"])
        change = self.change_status()
        self.assertEqual(("ready", "ready"), (change["status"], change["outcome"]))
        self.assertEqual(
            snapshot_tree(self.change), validation_records(change)["validated_tree"]
        )

    @verifies("scenario.validation.incomplete-tasks")
    def test_passing_checks_with_an_unfinished_task_is_only_completed(self):
        self.planned_change(complete=False)
        result = self.validate()
        self.assertEqual("succeeded", result["status"], result)
        data = result["output"]["data"]
        self.assertEqual("completed", data["outcome"])
        self.assertIn("semantic completeness is not proven", data["answer"])
        self.assertEqual(
            ["passed"], [item["status"] for item in self.entry()["checks"]]
        )
        self.assert_not_ready()

    def component_change(self, *, ledger_check_passes=True):
        """A transfer change whose plan also has ledger component work, completed in the candidate."""
        config = json.loads((self.change / ".concorde/config.json").read_text())
        check = json.loads(json.dumps(LEDGER_CHECK))
        if not ledger_check_passes:
            check["argv"][-1] += " + 1"
        config["checks"].append(check)
        (self.change / ".concorde/config.json").write_text(json.dumps(config, indent=2))
        self.commit(self.change, "Configure the ledger check")
        self.planned_change()
        (self.change / "app/ledger.py").write_text(LEDGER)
        # The owner's plan holds a task for the ledger; its component task derives from it.
        entry = self.entry()
        entry["tasks"].append({**LEDGER_TASK, "complete": True})
        save_target_state(self.change, entry)
        self.record_work("module.ledger", COMPONENT_TASK)
        # Implementation of the owner then records the completed component's revisions.
        entry = self.entry()
        repository = self.repository()
        ledger = repository.module("module.ledger")
        entry["component_revisions"] = {
            "module.ledger": {
                "spec": target_revision(repository, ledger),
                "implementation": implementation_digest(repository, ledger),
            }
        }
        entry["implementation_digest"] = implementation_digest(
            repository, repository.module("service.transfer")
        )
        save_target_state(self.change, entry)

    def validate_component(self):
        """The component request validates the ledger work and records only its entry."""
        result = self.validate(target_id="module.ledger", task=COMPONENT_TASK)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"], result)
        self.assertEqual("ready", self.entry("module.ledger")["status"])
        self.assertNotEqual("ready", self.change_status()["status"])

    @verifies("scenario.validation.multi-module")
    def test_every_edited_module_is_checked_and_readiness_needs_each_component(self):
        self.component_change()
        self.validate_component()
        result = self.validate()
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"], result)
        entry = self.entry()
        self.assertEqual(
            {"check.transfer", "check.ledger"},
            {item["check_id"] for item in entry["checks"]},
        )
        self.assertEqual(
            {"service.transfer", "module.ledger"},
            {item["target_id"] for item in entry["implementation_impacts"]},
        )

    @verifies("scenario.validation.multi-module")
    def test_a_failing_check_of_an_edited_module_keeps_the_change_from_ready(self):
        self.component_change(ledger_check_passes=False)
        result = self.validate()
        self.assertEqual("failed", result["output"]["data"]["outcome"], result)
        self.assertIn(
            ("check.ledger", "failed"),
            {
                (item["check_id"], item["status"])
                for item in result["output"]["data"]["checks"]
            },
        )
        self.assert_not_ready()

    @verifies("scenario.validation.multi-module")
    def test_a_component_failing_its_own_completion_check_keeps_the_change_from_ready(
        self,
    ):
        self.component_change()
        self.validate_component()
        entry = self.entry("module.ledger")
        entry["tasks"][0]["complete"] = False
        save_target_state(self.change, entry)
        self.refused(self.validate(), "incomplete_change")
        self.assert_not_ready()

    @verifies("scenario.validation.component-stale")
    def test_a_component_changed_after_completing_stops_readiness(self):
        self.component_change()
        self.validate_component()
        (self.change / "app/ledger.py").write_text(LEDGER + "\n# changed later\n")
        self.refused(self.validate(), "stale_evidence")
        self.assert_not_ready()

    @verifies("scenario.validation.invalid-spec")
    def test_invalid_specs_block_the_change_before_any_check(self):
        self.planned_change()
        path = self.change / "specs/ledger/module.md.json"
        metadata = json.loads(path.read_text())
        metadata["relations"][0]["target"] = "concept.ledger.missing"
        path.write_text(json.dumps(metadata, indent=2))
        with patch.object(check_service, "execute_check") as execute:
            result = self.validate()
        execute.assert_not_called()
        data = result["output"]["data"]
        self.assertEqual("failed", data["outcome"], result)
        self.assertIn("concept.ledger.missing", data["answer"])
        change = self.change_status()
        self.assertEqual(
            ("blocked", "invalid_spec"), (change["status"], change["outcome"])
        )
        self.assertEqual("blocked", self.entry()["status"])

    @verifies("scenario.validation.review-required")
    def test_a_missing_required_review_stops_readiness(self):
        self.planned_change()
        run = Invocation(
            "concorde-validate",
            CONFIGURATION,
            self.task,
            OperationHost(self.change, PACKAGE),
        )
        require_reviews(run, True)
        self.refused(self.validate(), "review_required")
        change = self.change_status()
        # The gate refusal withdrew readiness and marked neither the change nor its entry blocked.
        self.assertNotIn(change["status"], {"ready", "blocked"}, change)
        self.assertNotEqual("blocked", self.entry()["status"])
        self.assertEqual(
            ["passed"], [item["status"] for item in self.entry()["checks"]]
        )

    @verifies("scenario.validation.open-blocker")
    def test_an_open_blocker_stops_readiness_and_stays_open(self):
        self.planned_change()
        receipt = report_issue(
            self.change,
            report(owner_target_id="service.transfer", evidence=[]),
            source(target_id="service.transfer"),
        )
        record_task_gaps(
            self.change,
            "service.transfer",
            self.task["task"],
            "implementation",
            [{**receipt, "blocked_step": "Implement the transfer contract"}],
            "revision",
        )
        before = open_gaps(self.change_status())
        self.assertEqual(1, len(before))
        self.refused(self.validate(), "spec_incomplete")
        self.assertEqual(before, open_gaps(self.change_status()))
        self.assert_not_ready()

    @verifies("scenario.validation.changed-during-run")
    def test_a_candidate_edited_while_checks_run_is_refused(self):
        self.planned_change()
        execute = check_service.execute_check

        def edit_during_check(*args, **kwargs):
            result = execute(*args, **kwargs)
            (self.change / "shared.txt").write_text("edited during the checks\n")
            return result

        with patch.object(
            check_service, "execute_check", side_effect=edit_during_check
        ):
            self.refused(self.validate(), "stale_evidence")
        self.assert_not_ready()

    @verifies("scenario.validation.changed-during-run")
    def test_an_affected_module_changed_while_checks_run_is_refused(self):
        self.planned_change()
        execute = check_service.execute_check

        def edit_during_check(*args, **kwargs):
            result = execute(*args, **kwargs)
            (self.change / "app/transfer.py").write_text(TRANSFER + "# edited\n")
            return result

        with patch.object(
            check_service, "execute_check", side_effect=edit_during_check
        ):
            self.refused(self.validate(), "stale_evidence")
        self.assert_not_ready()

    @verifies("scenario.validation.sandbox-unavailable")
    def test_without_the_check_boundary_nothing_is_recorded(self):
        self.planned_change()
        before = self.entry()["checks"]
        with patch.object(
            check_service,
            "execute_check",
            side_effect=CheckSandboxError("no read-only boundary on this host"),
        ):
            self.refused(self.validate(), "check_sandbox_unavailable")
        self.assertEqual(before, self.entry()["checks"])
        self.assert_not_ready()

    @verifies("scenario.validation.relayed")
    def test_validation_from_the_primary_runs_in_the_candidate(self):
        change_id = self.planned_change()
        result = self.call_operation(
            self.primary,
            "concorde-validate",
            {**self.task, "change_id": change_id},
            host=self.primary_host(self.relay_in_process()),
        )
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual(1, len(self.relayed))
        relayed = self.relayed[0]
        self.assertEqual(self.change.resolve(), relayed["candidate"].resolve())
        self.assertEqual(relayed["result"]["output"]["data"], result["output"]["data"])
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        self.assertEqual("ready", self.change_status()["status"])

    @verifies("scenario.validation.checks-skipped")
    def test_skipping_checks_never_fakes_them(self):
        self.planned_change()
        with patch.object(check_service, "execute_check") as execute:
            result = self.validate(run_checks=False)
        execute.assert_not_called()
        self.refused(result, "stale_evidence")
        self.assertEqual([], self.entry()["checks"])
        self.assert_not_ready()

    @verifies("scenario.validation.repeat")
    def test_a_repeated_validation_withdraws_the_earlier_ready_state_first(self):
        self.planned_change()
        self.assertEqual("ready", self.validate()["output"]["data"]["outcome"])
        self.assertIsNotNone(validation_records(self.change_status())["validated_tree"])
        observed = []
        execute = check_service.execute_check

        def observe(*args, **kwargs):
            change = self.change_status()
            observed.append(
                (change["status"], validation_records(change)["validated_tree"])
            )
            return execute(*args, **kwargs)

        with patch.object(check_service, "execute_check", side_effect=observe):
            again = self.validate()
        self.assertEqual([("active", None)], observed)
        self.assertEqual("ready", again["output"]["data"]["outcome"], again)
        self.assertEqual("ready", self.change_status()["status"])
        # Without current check results the gates no longer hold, so the change stays withdrawn.
        self.refused(self.validate(run_checks=False), "stale_evidence")
        self.assert_not_ready()


if __name__ == "__main__":
    unittest.main()
