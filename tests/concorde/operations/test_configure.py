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
        # These tests start from a worktree without a worker model configuration.
        (self.root / models.CONFIG).unlink()

    def configure(self, *argv, client="pi"):
        return self.project.run(
            "configure_workers", *argv, client=client, environ=self.environ
        )

    def stored(self, worktree):
        return json.loads((worktree / models.CONFIG).read_text())

    @verifies("scenario.operations.configure-list")
    def test_listing_without_a_task(self):
        status, envelope = self.configure(client="claude")
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertIsNone(envelope["task"])
        self.assertEqual([], envelope["worker_runs"])
        output = envelope["output"]
        self.assertEqual(
            ("list", "pi", "Concorde's default worker backend", False),
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
        self.assertEqual(
            ["reviewer1", "reviewer2", "reviewer3", "reviewer4", "reviewer5", "chair"],
            list(output["effective"]["spec_panel"]),
        )
        self.assertEqual(["worker"], list(output["effective"]["implement"]))
        self.assertEqual(
            {"pi"},
            {
                chosen["backend"]
                for workers in output["effective"].values()
                for chosen in workers.values()
            },
        )
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
            "--worker",
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
            ("local-openai/plain-7", "off", "operations.spec_review.workers.checker"),
            (checker["model"], checker["reasoning"], checker["model_source"]),
        )
        self.assertEqual(
            ("anthropic/claude-sonnet-5", "medium", "default"),
            (reviewer["model"], reviewer["reasoning"], reviewer["model_source"]),
        )
        self.assertEqual(
            {"backend": "pi", "backend_source": "Concorde's default worker backend"},
            {key: checker[key] for key in ("backend", "backend_source")},
        )
        self.assertEqual(self.stored(self.root), envelope["output"]["configured"])
        self.assertFalse((worktree / models.CONFIG).exists())
        before = store.load_task(self.root, "t1")
        status, envelope = self.configure(
            "--task",
            "t1",
            "--operation",
            "implement",
            "--worker",
            "worker",
            "--model",
            "a/unlisted",
            "--allow-unlisted",
        )
        self.assertEqual((0, "t1"), (status, envelope["task"]), envelope)
        self.assertEqual(
            {
                "schema_version": 3,
                "operations": {
                    "implement": {"workers": {"worker": {"model": "a/unlisted"}}}
                },
            },
            self.stored(worktree),
        )
        self.assertNotIn("implement", json.dumps(self.stored(self.root)))
        record = store.load_task(self.root, "t1")
        self.assertEqual(len(before["runs"]) + 1, len(record["runs"]))
        status, envelope = self.configure(
            "--operation", "spec_review", "--worker", "checker", "--unset"
        )
        self.assertEqual(
            (0, "unset", True),
            (status, envelope["output"]["action"], envelope["output"]["changed"]),
        )
        self.assertIsNone(envelope["output"]["candidates"])
        self.assertEqual(
            {
                "schema_version": 3,
                "default": {
                    "model": "anthropic/claude-sonnet-5",
                    "reasoning": "medium",
                },
            },
            self.stored(self.root),
        )

    @verifies("scenario.operations.configure-backend")
    def test_a_worker_may_be_put_on_claude_code_and_its_model_checked_there(self):
        status, envelope = self.configure(
            "--operation", "spec_panel", "--worker", "chair", "--backend", "claude"
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        output = envelope["output"]
        self.assertEqual(
            ("claude", "--backend"), (output["backend"], output["backend_from"])
        )
        self.assertEqual(
            {
                "schema_version": 3,
                "operations": {
                    "spec_panel": {"workers": {"chair": {"backend": "claude"}}}
                },
            },
            self.stored(self.root),
        )
        chair = output["effective"]["spec_panel"]["chair"]
        reviewer = output["effective"]["spec_panel"]["reviewer1"]
        self.assertEqual(
            ("claude", "operations.spec_panel.workers.chair"),
            (chair["backend"], chair["backend_source"]),
        )
        self.assertEqual("pi", reviewer["backend"])
        # A pi model is not a Claude Code model: the chair's entry is checked on Claude Code.
        status, envelope = self.configure(
            "--operation",
            "spec_panel",
            "--worker",
            "chair",
            "--model",
            "anthropic/claude-sonnet-5",
        )
        self.assertEqual(
            (1, "configuration_refused"), (status, envelope["error"]["code"])
        )
        self.assertIn("is not a claude model", envelope["error"]["detail"])
        status, envelope = self.configure("--candidates", "claude")
        self.assertEqual(
            ("list", "claude", "--candidates"),
            (
                envelope["output"]["action"],
                envelope["output"]["backend"],
                envelope["output"]["backend_from"],
            ),
        )
        validate(output, CONFIGURATION_SCHEMA)

    @verifies("scenario.operations.configure-worker")
    def test_each_worker_is_configured_by_its_id(self):
        for worker, model, level in (
            ("reviewer1", "anthropic/claude-sonnet-5", "high"),
            ("reviewer2", "local-openai/plain-7", "off"),
        ):
            status, envelope = self.configure(
                "--operation",
                "spec_panel",
                "--worker",
                worker,
                "--model",
                model,
                "--reasoning",
                level,
            )
            self.assertEqual(
                (0, "set"), (status, envelope["output"]["action"]), envelope
            )
        self.assertEqual(
            {
                "reviewer1": {
                    "model": "anthropic/claude-sonnet-5",
                    "reasoning": "high",
                },
                "reviewer2": {"model": "local-openai/plain-7", "reasoning": "off"},
            },
            self.stored(self.root)["operations"]["spec_panel"]["workers"],
        )
        panel = envelope["output"]["effective"]["spec_panel"]
        self.assertEqual(
            ["reviewer1", "reviewer2", "reviewer3", "reviewer4", "reviewer5", "chair"],
            list(panel),
        )
        self.assertEqual(
            ("local-openai/plain-7", "operations.spec_panel.workers.reviewer2"),
            (panel["reviewer2"]["model"], panel["reviewer2"]["model_source"]),
        )
        self.assertIsNone(panel["reviewer3"]["model"])
        self.assertIn("spec_panel reviewer2", envelope["host_evidence"][0]["detail"])
        status, envelope = self.configure(
            "--operation", "spec_panel", "--worker", "reviewer2", "--unset"
        )
        self.assertEqual((0, True), (status, envelope["output"]["changed"]), envelope)
        self.assertEqual(
            ["reviewer1"],
            list(self.stored(self.root)["operations"]["spec_panel"]["workers"]),
        )

    @verifies("scenario.operations.configure-refused")
    def test_a_refused_change_leaves_the_file_alone(self):
        for argv, fragment in (
            (["--operation", "validate", "--model", "x"], "implement"),
            (
                ["--operation", "spec_panel", "--worker", "reviewer6", "--model", "x"],
                "its workers: reviewer1, reviewer2, reviewer3, reviewer4, reviewer5, chair",
            ),
            (["--worker", "reviewer1", "--model", "x"], "no --operation"),
            (["--candidates", "claude", "--model", "x"], "--candidates only lists"),
        ):
            with self.subTest(argv=argv):
                status, envelope = self.configure(*argv)
                self.assertEqual(
                    (1, "invalid_request"), (status, envelope["error"]["code"])
                )
                self.assertIn(fragment, envelope["error"]["detail"])
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
