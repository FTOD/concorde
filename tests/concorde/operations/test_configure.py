"""The ``configure_workers`` Operation, with and without a task, against fake agent programs."""

from __future__ import annotations

import json
import unittest

from concorde.errors import ERROR_SCHEMA
from concorde.harness import models
from concorde.operations.configure import CONFIGURATION_SCHEMA
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.tasks import store
from tests.concorde.support.agent_fakes import fake_agents
from tests.concorde.support.operation_project import OperationProject
from tests.concorde.support.paths import REPOSITORY_ROOT


class ConfigureWorkersTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        self.environ = fake_agents(self.project.base / "bin", self.project.home)

    def configure(self, *argv, client="pi"):
        return self.project.run(
            "configure_workers", *argv, client=client, environ=self.environ
        )

    def stored(self, worktree):
        return json.loads((worktree / models.CONFIG).read_text())

    @verifies("scenario.operations.configure-list")
    def test_listing_without_a_task(self):
        status, envelope = self.configure()
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertIsNone(envelope["task"])
        self.assertEqual([], envelope["worker_runs"])
        output = envelope["output"]
        self.assertEqual(
            ("list", "pi", "CONCORDE_CLIENT=pi", False),
            (
                output["action"],
                output["backend"],
                output["backend_from"],
                output["changed"],
            ),
        )
        self.assertEqual(str(self.root / models.CONFIG), output["config"])
        self.assertEqual(
            ["anthropic/claude-sonnet-5", "local-openai/plain-7"],
            [item["id"] for item in output["candidates"]["models"]],
        )
        self.assertEqual(
            ["reviewer", "checker"], list(output["effective"]["spec_review"])
        )
        self.assertEqual(["worker"], list(output["effective"]["implement"]))
        self.assertNotIn("validate", output["effective"])
        self.assertNotIn("configure_workers", output["effective"])
        self.assertFalse((self.root / models.CONFIG).exists())

    @verifies("scenario.operations.configure-change")
    def test_changes_reach_only_the_named_worktree(self):
        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        status, envelope = self.configure(
            "--model", "anthropic/claude-sonnet-5", "--reasoning", "medium"
        )
        self.assertEqual(
            (0, "set", True),
            (status, envelope["output"]["action"], envelope["output"]["changed"]),
            envelope,
        )
        status, envelope = self.configure(
            "--operation",
            "spec_review",
            "--role",
            "checker",
            "--model",
            "local-openai/plain-7",
            "--reasoning",
            "off",
        )
        self.assertEqual(0, status, envelope)
        checker = envelope["output"]["effective"]["spec_review"]["checker"]
        reviewer = envelope["output"]["effective"]["spec_review"]["reviewer"]
        self.assertEqual(
            ("local-openai/plain-7", "off"), (checker["model"], checker["reasoning"])
        )
        self.assertEqual(
            ("anthropic/claude-sonnet-5", "medium"),
            (reviewer["model"], reviewer["reasoning"]),
        )
        self.assertFalse((worktree / models.CONFIG).exists())
        before = store.load_task(self.root, "t1")
        status, envelope = self.configure(
            "--task",
            "t1",
            "--operation",
            "implement",
            "--model",
            "a/unlisted",
            "--allow-unlisted",
        )
        self.assertEqual((0, "t1"), (status, envelope["task"]), envelope)
        self.assertEqual(
            {
                "schema_version": 2,
                "pi": {"operations": {"implement": {"model": "a/unlisted"}}},
            },
            self.stored(worktree),
        )
        self.assertNotIn("implement", json.dumps(self.stored(self.root)))
        record = store.load_task(self.root, "t1")
        self.assertEqual(len(before["runs"]) + 1, len(record["runs"]))
        status, envelope = self.configure(
            "--operation", "spec_review", "--role", "checker", "--unset"
        )
        self.assertEqual(
            (0, "unset", True),
            (status, envelope["output"]["action"], envelope["output"]["changed"]),
        )
        self.assertIsNone(envelope["output"]["candidates"])
        self.assertEqual(
            {"default": {"model": "anthropic/claude-sonnet-5", "reasoning": "medium"}},
            self.stored(self.root)["pi"],
        )

    @verifies("scenario.operations.configure-refused")
    def test_a_refused_change_leaves_the_file_alone(self):
        status, envelope = self.configure("--operation", "validate", "--model", "x")
        self.assertEqual((1, "invalid_request"), (status, envelope["error"]["code"]))
        self.assertIn("implement", envelope["error"]["detail"])
        status, envelope = self.configure(
            "--operation", "implement", "--role", "checker", "--model", "x"
        )
        self.assertEqual((1, "invalid_request"), (status, envelope["error"]["code"]))
        self.assertIn("its roles: worker", envelope["error"]["detail"])
        status, envelope = self.configure("--model", "anthropic/claude-nope")
        self.assertEqual(
            (1, "configuration_refused"), (status, envelope["error"]["code"])
        )
        [cause] = envelope["error"]["causes"]
        self.assertEqual(
            ("component", "unknown_model"), (cause["level"], cause["code"])
        )
        self.assertIn("anthropic/claude-sonnet-5", cause["detail"])
        validate(envelope["error"], ERROR_SCHEMA)
        status, envelope = self.configure(client=None)
        self.assertEqual(
            (1, "configuration_refused"), (status, envelope["error"]["code"])
        )
        self.assertEqual("client_unknown", envelope["error"]["causes"][0]["code"])
        self.assertFalse((self.root / models.CONFIG).exists())

    def test_the_output_schema_is_the_contract(self):
        text = (REPOSITORY_ROOT / "specs/concorde/operations/contracts.md").read_text()
        fence = json.loads(
            text.split("## Worker configuration", 1)[1]
            .split("```concorde-contract\n", 1)[1]
            .split("```", 1)[0]
        )
        self.assertEqual("contract.operations.worker-configuration", fence["id"])
        self.assertEqual(CONFIGURATION_SCHEMA, fence["schema"])
        validate(fence["example"], CONFIGURATION_SCHEMA)


if __name__ == "__main__":
    unittest.main()
