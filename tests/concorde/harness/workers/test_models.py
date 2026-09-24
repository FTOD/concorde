"""The worker model configuration and ``concorde workers``, with fake ``claude`` and ``pi``."""

from __future__ import annotations

import json
import subprocess
import unittest

from concorde.errors import ERROR_SCHEMA
from concorde.harness import models
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from tests.concorde.support.agent_fakes import command, fake_agents
from tests.concorde.support.operation_project import OperationProject


class WorkerModelTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        self.environ = fake_agents(self.project.base / "bin", self.project.home)

    def run_command(self, *argv, client="pi", **extra):
        environ = dict(self.environ, **extra)
        if client:
            environ["CONCORDE_CLIENT"] = client
        return command(argv, self.root, environ)

    @verifies("scenario.workers.backend-from-client")
    def test_the_backend_is_the_main_sessions_program(self):
        self.assertEqual(
            ("claude", "CLAUDECODE=1"), models.detect_client({"CLAUDECODE": "1"})
        )
        self.assertEqual(
            ("pi", "CONCORDE_CLIENT=pi"),
            models.detect_client({"CONCORDE_CLIENT": "pi", "CLAUDECODE": "1"}),
        )
        self.assertEqual("pi", models.detect_client({"PI_SESSION_ID": "s1"})[0])
        with self.assertRaises(models.ModelConfigError) as raised:
            models.detect_client({})
        self.assertEqual("client_unknown", raised.exception.code)
        for name in (
            "CONCORDE_CLIENT",
            "CLAUDECODE",
            "PI_SESSION_ID",
            "PI_CODING_AGENT",
        ):
            self.assertIn(name, str(raised.exception))
        with self.assertRaises(models.ModelConfigError) as raised:
            models.detect_client({"CONCORDE_CLIENT": "codex"})
        self.assertEqual("invalid_client", raised.exception.code)
        status, value = self.run_command("show", client=None)
        self.assertEqual((1, "client_unknown"), (status, value["error"]["code"]))
        self.assertIn("CONCORDE_CLIENT", " ".join(value["error"]["options"]))
        validate(value["error"], ERROR_SCHEMA)

    @verifies("scenario.workers.models-listed")
    def test_the_installed_programs_models_are_listed(self):
        status, pi = self.run_command("models", "--backend", "pi")
        self.assertEqual(0, status, pi)
        self.assertTrue(pi["complete"])
        listed = {item["id"]: item for item in pi["models"]}
        self.assertEqual(
            ["anthropic/claude-sonnet-5", "local-openai/plain-7"], list(listed)
        )
        self.assertEqual(
            ["off", "minimal", "low", "medium", "high", "xhigh", "max"],
            listed["anthropic/claude-sonnet-5"]["levels"],
        )
        self.assertEqual(["off"], listed["local-openai/plain-7"]["levels"])
        self.assertEqual(str(self.root / models.CONFIG), pi["config"])
        self.assertEqual(sorted(models.TASK_TYPES), sorted(pi["effective"]))

        (self.project.home / ".claude/settings.json").write_text(
            json.dumps({"model": "claude-opus-5-5"})
        )
        status, claude = self.run_command(
            "models",
            client="claude",
            ANTHROPIC_DEFAULT_SONNET_MODEL="claude-sonnet-5",
        )
        self.assertEqual(0, status, claude)
        self.assertEqual(
            ("claude", "CONCORDE_CLIENT=claude"),
            (claude["backend"], claude["backend_from"]),
        )
        self.assertFalse(claude["complete"])
        self.assertIn("no command that lists", claude["note"])
        ids = [item["id"] for item in claude["models"]]
        self.assertTrue({"fable", "opus", "sonnet", "haiku"} <= set(ids))
        self.assertIn("claude-opus-5-5", ids)
        self.assertIn("claude-sonnet-5", ids)
        self.assertEqual(
            ["low", "medium", "high", "xhigh", "max"], claude["reasoning_levels"]
        )

    @verifies("scenario.workers.models-configured")
    def test_a_default_and_a_task_type_override(self):
        status, value = self.run_command(
            "set", "--model", "anthropic/claude-sonnet-5", "--reasoning", "medium"
        )
        self.assertEqual(0, status, value)
        status, value = self.run_command(
            "set",
            "--task-type",
            "implement",
            "--model",
            "local-openai/plain-7",
            "--reasoning",
            "off",
        )
        self.assertEqual(0, status, value)
        status, value = self.run_command(
            "set", "--task-type", "understand", "--model", "local-openai/plain-7"
        )
        self.assertEqual(0, status, value)
        stored = json.loads((self.root / models.CONFIG).read_text())
        self.assertEqual(
            {"model": "anthropic/claude-sonnet-5", "reasoning": "medium"},
            stored["pi"]["default"],
        )
        understand = value["effective"]["understand"]
        self.assertEqual(
            (
                "local-openai/plain-7",
                "medium",
                "pi.task_types.understand",
                "pi.default",
            ),
            (
                understand["model"],
                understand["reasoning"],
                understand["model_source"],
                understand["reasoning_source"],
            ),
        )
        self.assertEqual(
            "anthropic/claude-sonnet-5", value["effective"]["test"]["model"]
        )
        status_text = subprocess.run(
            ["git", "status", "--porcelain"],
            check=True,
            cwd=self.root,
            capture_output=True,
            text=True,
        ).stdout
        self.assertNotIn("worker-models", status_text)
        status, value = self.run_command("unset", "--task-type", "implement")
        self.assertEqual((0, True), (status, value["removed"]))
        self.assertEqual(
            ("anthropic/claude-sonnet-5", "medium"),
            (
                value["effective"]["implement"]["model"],
                value["effective"]["implement"]["reasoning"],
            ),
        )

    @verifies("scenario.workers.model-refused")
    def test_a_model_or_level_the_program_does_not_offer_is_refused(self):
        status, value = self.run_command("set", "--model", "anthropic/claude-nope")
        self.assertEqual((1, "unknown_model"), (status, value["error"]["code"]))
        self.assertIn("anthropic/claude-sonnet-5", value["error"]["detail"])
        validate(value["error"], ERROR_SCHEMA)
        status, value = self.run_command(
            "set", "--model", "local-openai/plain-7", "--reasoning", "high"
        )
        self.assertEqual((1, "unknown_level"), (status, value["error"]["code"]))
        self.assertIn("levels: off", value["error"]["detail"])
        self.assertFalse((self.root / models.CONFIG).exists())
        status, value = self.run_command(
            "set", "--model", "anthropic/claude-nope", "--allow-unlisted"
        )
        self.assertEqual(0, status, value)
        self.assertEqual(
            "anthropic/claude-nope", value["configured"]["default"]["model"]
        )

    @verifies("scenario.workers.model-config-invalid")
    def test_an_unreadable_configuration_is_reported(self):
        path = self.root / models.CONFIG
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{not json")
        status, value = self.run_command("show")
        self.assertEqual((1, "config_invalid"), (status, value["error"]["code"]))
        self.assertIn(str(path), value["error"]["detail"])
        path.write_text(
            json.dumps(
                {"schema_version": 1, "pi": {"task_types": {"deploy": {"model": "x"}}}}
            )
        )
        status, value = self.run_command("show")
        self.assertEqual((1, "config_invalid"), (status, value["error"]["code"]))
        self.assertIn("deploy", value["error"]["detail"])


if __name__ == "__main__":
    unittest.main()
