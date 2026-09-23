"""Component requests: a request for another Module enters the owner's candidate only as derived."""

import os
import tempfile
import unittest
from pathlib import Path

from concorde.planning.scope import component_intent
from concorde.spec.verification import verifies
from tests.concorde.planning.native_steps import NativeCandidate, task_item

LEDGER_TASKS = [
    task_item("ledger-read", "module.ledger"),
    task_item("ledger-lock", "module.ledger"),
]


class ComponentRequestTests(NativeCandidate, unittest.TestCase):
    def owner_with_component_tasks(self):
        self.own()
        self.accepted_plan()
        self.accepted_tasks([task_item("transfer-rounding"), *LEDGER_TASKS])

    def component(self, **changes):
        return {
            "target_id": "module.ledger",
            "task": component_intent(LEDGER_TASKS),
            **changes,
        }

    def owner(self):
        state = self.change_state()
        return {key: state[key] for key in ("target_id", "task", "constraints")}

    def workflows(self):
        return sorted(Path(tempfile.gettempdir()).glob("concorde-native-workflow-*"))

    @verifies("scenario.planning.component-request")
    def test_a_derived_component_request_is_admitted_in_the_owners_candidate(self):
        self.owner_with_component_tasks()
        owner = self.owner()
        prepared = self.prepare("concorde-plan", self.component())
        self.assertEqual("prepared", prepared["state"], prepared)
        self.assertEqual(
            str(self.change), prepared["result"]["workspace"]["path"], prepared
        )
        slot = self.workflow(prepared)
        self.assertEqual({"state": "ready"}, slot.host_step("bind"))
        self.assertEqual(
            "module.ledger", slot.slot_descriptor("assessor")["snapshot"]["target_id"]
        )
        # The candidate's owner does not change.
        self.assertEqual(owner, self.owner())
        self.assertEqual("service.transfer", owner["target_id"])

    @verifies("scenario.planning.component-stale-parent")
    def test_a_component_request_needs_the_owners_current_derived_task(self):
        self.owner_with_component_tasks()
        spec = self.change / "specs/transfer/module.md"
        original = spec.read_bytes()

        def refused(request):
            before = self.change_state()
            workflows = self.workflows()
            value = self.prepare("concorde-plan", request)
            self.assertEqual("rejected", value["state"], value)
            self.assertEqual(
                ["incompatible_handoff"],
                [e["code"] for e in value["result"]["errors"]],
            )
            # No Agent was prepared and no recorded work changed.
            self.assertEqual(workflows, self.workflows())
            after = self.change_state()
            self.assertEqual(
                (before["sections"], self.owner()),
                (after["sections"], {k: before[k] for k in self.owner()}),
            )

        with self.subTest(case="different task"):
            refused(self.component(task="Rewrite the ledger"))
        with self.subTest(case="different constraints"):
            refused(self.component(constraints=["Keep the old API"]))
        with self.subTest(case="focused request"):
            refused(self.component(focus_id="scenario.ledger.unknown"))
        with self.subTest(case="owner Spec changed since its plan"):
            spec.write_bytes(original + b"\nA later owner promise.\n")
            refused(self.component())
            # Planning the owner again makes the component request admissible.
            self.accepted_plan()
            self.accepted_tasks(
                [
                    task_item("transfer-rounding-2"),
                    task_item("ledger-read-2", "module.ledger"),
                ]
            )
            request = {
                "target_id": "module.ledger",
                "task": component_intent([task_item("ledger-read-2", "module.ledger")]),
            }
            self.assertEqual(
                "prepared", self.prepare("concorde-plan", request)["state"]
            )
        os.chdir(self.change)


if __name__ == "__main__":
    unittest.main()
