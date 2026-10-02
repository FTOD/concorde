"""The grant Spec core computes, projected by Method, satisfies the worker harness's grant input.

The spec part and the worker harness each keep their own copy of the shared fields, so neither
imports the other; this test keeps the copies equal: Spec core's ``task_type``, ``entries`` and
``context_identity`` for every task type, as Method projects them, satisfy
``contract.workers.grant-input``, and the task types and read-only task types the worker harness
knows are the Protocol's.
"""

from __future__ import annotations

import unittest

from concorde.method.workers import grant_input, withhold_writes
from concorde.spec import grants
from concorde.spec.repository import SpecRepository
from concorde.spec.schema import validate
from concorde.worker_harness import settings
from concorde.worker_harness.workers import GRANT_FIELDS, run_worker
from tests.concorde.harness.workers.test_workers import WorkerProject
from tests.concorde.support.adoption_case import contract
from tests.concorde.support.paths import REPOSITORY_ROOT

CONTRACTS = "specs/concorde/worker-harness/workers/contracts.md"
SCHEMA = contract(CONTRACTS, "contract.workers.grant-input")


class GrantInputContractTests(unittest.TestCase):
    def setUp(self):
        self.project = WorkerProject(self, linked=True)
        self.repository = SpecRepository(self.project.root, REPOSITORY_ROOT)

    def test_every_projected_grant_satisfies_the_grant_input(self):
        for task_type in grants.TASK_TYPES:
            with self.subTest(task_type=task_type):
                computed = grants.grant(self.repository, ["module.a"], task_type).value
                for value in (computed, withhold_writes(computed)):
                    projected = grant_input(value)
                    validate(projected, SCHEMA)
                    self.assertEqual(
                        {name: value[name] for name in GRANT_FIELDS}, projected
                    )

    def test_the_task_types_are_the_protocols(self):
        self.assertEqual(
            tuple(SCHEMA["properties"]["task_type"]["enum"]), settings.TASK_TYPES
        )
        self.assertEqual(grants.TASK_TYPES, settings.TASK_TYPES)
        self.assertEqual(
            tuple(
                task_type
                for task_type, levels in grants.LEVELS.items()
                if "rw" not in levels.values()
            ),
            settings.WRITING_NOTHING,
        )
        self.assertEqual(
            set(
                SCHEMA["properties"]["entries"]["items"]["properties"]["level"]["enum"]
            ),
            set(settings.RANK),
        )
        self.assertEqual(set(SCHEMA["required"]), set(GRANT_FIELDS))

    def test_a_grant_beyond_the_grant_input_is_refused(self):
        computed = grants.grant(self.repository, ["module.a"], "implement").value
        record = run_worker(
            self.project.request([{}], check_modules=None, grant=computed)
        )
        self.assertEqual("failed", record["status"])
        error = record["error"]
        self.assertEqual(
            ("grant_malformed", "input"), (error["code"], error["unhandled"]["reason"])
        )
        self.assertIn("glossary", error["detail"])
        self.assertEqual([], record["rounds"])


if __name__ == "__main__":
    unittest.main()
