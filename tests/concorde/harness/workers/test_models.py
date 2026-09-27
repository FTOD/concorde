"""The worker model configuration: client detection, candidates, resolution and changes."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from concorde.harness import models
from concorde.spec.verification import verifies
from tests.concorde.support.agent_fakes import fake_agents


def _backend(chosen: dict) -> tuple[str, str]:
    return chosen["backend"], chosen["backend_source"]


class WorkerModelTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.home = self.base / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.environ = fake_agents(self.base / "bin", self.home)

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

    @verifies("scenario.workers.backend-configured")
    def test_workers_run_on_pi_unless_their_configuration_chooses_claude_code(self):
        session = dict(self.environ, CLAUDECODE="1")
        empty = {"schema_version": 3}
        self.assertEqual(
            ("pi", "Concorde's default worker backend"),
            _backend(models.worker_choice(empty, "implement", "worker", session)),
        )
        config = {
            "schema_version": 3,
            "default": {"model": "a/pi"},
            "operations": {
                "spec_review": {
                    "workers": {"checker": {"backend": "claude", "reasoning": "high"}}
                }
            },
        }
        models.save(self.base, config)
        self.assertEqual(config, models.load(self.base))
        reviewer = models.worker_choice(config, "spec_review", "reviewer", session)
        checker = models.worker_choice(config, "spec_review", "checker", session)
        self.assertEqual(("pi", "a/pi"), (reviewer["backend"], reviewer["model"]))
        # Choosing Claude Code starts that program afresh: the pi default model is not inherited.
        self.assertEqual(
            (
                "claude",
                "operations.spec_review.workers.checker",
                None,
                "the backend's own default",
                "high",
            ),
            (
                checker["backend"],
                checker["backend_source"],
                checker["model"],
                checker["model_source"],
                checker["reasoning"],
            ),
        )
        missing = dict(session, CONCORDE_PI=str(self.base / "nowhere"))
        with self.assertRaises(models.ModelConfigError) as raised:
            models.worker_choice(config, "implement", "worker", missing)
        self.assertEqual("backend_missing", raised.exception.code)
        for part in (
            "the worker worker of implement runs on pi",
            "Concorde's default worker backend",
            "CONCORDE_PI",
            "never falls back",
            "--backend claude",
        ):
            self.assertIn(part, str(raised.exception))
        self.assertEqual(
            "claude",
            models.worker_choice(config, "spec_review", "checker", missing)["backend"],
        )

    @verifies("scenario.workers.models-listed")
    def test_the_installed_programs_models_are_listed(self):
        pi = models.candidates("pi", self.environ)
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
        (self.home / ".claude/settings.json").write_text(
            json.dumps({"model": "claude-opus-5-5"})
        )
        claude = models.candidates(
            "claude",
            dict(self.environ, ANTHROPIC_DEFAULT_SONNET_MODEL="claude-sonnet-5"),
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
        missing = dict(self.environ, CONCORDE_PI=str(self.base / "nowhere"))
        with self.assertRaises(models.ModelConfigError) as raised:
            models.candidates("pi", missing)
        self.assertEqual("backend_missing", raised.exception.code)

    @verifies("scenario.workers.model-resolution")
    def test_the_most_specific_entry_wins_field_by_field(self):
        config = {"schema_version": 3}
        models.set_choice(config, None, None, None, "a/default", "medium")
        models.set_choice(config, "spec_panel", None, None, "a/panel", None)
        models.set_choice(config, "spec_panel", "reviewer2", None, "a/second", None)
        models.set_choice(config, "spec_panel", "chair", None, None, "high")
        first = models.choice(config, "spec_panel", "reviewer1")
        second = models.choice(config, "spec_panel", "reviewer2")
        chair = models.choice(config, "spec_panel", "chair")
        self.assertEqual(
            ("a/panel", "operations.spec_panel.default", "medium", "default"),
            (
                first["model"],
                first["model_source"],
                first["reasoning"],
                first["reasoning_source"],
            ),
        )
        self.assertEqual(
            ("a/second", "operations.spec_panel.workers.reviewer2"),
            (second["model"], second["model_source"]),
        )
        self.assertEqual(
            ("a/panel", "high", "operations.spec_panel.workers.chair"),
            (chair["model"], chair["reasoning"], chair["reasoning_source"]),
        )
        other = models.choice(config, "implement", "worker")
        self.assertEqual(
            ("a/default", "default"), (other["model"], other["model_source"])
        )
        self.assertTrue(models.unset_choice(config, "spec_panel", "reviewer2"))
        self.assertTrue(models.unset_choice(config, "spec_panel", "chair"))
        self.assertEqual(
            {"default": {"model": "a/panel"}}, config["operations"]["spec_panel"]
        )
        self.assertTrue(models.unset_choice(config, "spec_panel", None))
        self.assertFalse(models.unset_choice(config, "spec_panel", None))
        self.assertNotIn("operations", config)

    @verifies("scenario.workers.model-refused")
    def test_a_model_or_level_the_program_does_not_offer_is_refused(self):
        found = models.candidates("pi", self.environ)
        with self.assertRaises(models.ModelConfigError) as raised:
            models.check_choice(found, "pi", "a/nope", None, False, "a/nope")
        self.assertEqual("unknown_model", raised.exception.code)
        self.assertIn("anthropic/claude-sonnet-5", str(raised.exception))
        with self.assertRaises(models.ModelConfigError) as raised:
            models.check_choice(
                found, "pi", None, "high", False, "local-openai/plain-7"
            )
        self.assertEqual("unknown_level", raised.exception.code)
        self.assertIn("levels: off", str(raised.exception))
        models.check_choice(found, "pi", "a/nope", None, True, "a/nope")

    @verifies("scenario.workers.model-config-invalid")
    def test_an_unreadable_configuration_is_reported(self):
        worktree = self.base / "worktree"
        path = worktree / models.CONFIG
        path.parent.mkdir(parents=True)
        path.write_text("{not json")
        with self.assertRaises(models.ModelConfigError) as raised:
            models.load(worktree)
        self.assertEqual("config_invalid", raised.exception.code)
        self.assertIn(str(path), str(raised.exception))
        path.write_text(
            json.dumps(
                {
                    "schema_version": 3,
                    "operations": {
                        "understand": {
                            "workers": {"worker": {"model": "x", "modle": "y"}}
                        }
                    },
                }
            )
        )
        with self.assertRaises(models.ModelConfigError) as raised:
            models.load(worktree)
        self.assertEqual("config_invalid", raised.exception.code)
        self.assertIn("modle", str(raised.exception))
        path.write_text(
            json.dumps({"schema_version": 2, "pi": {"default": {"model": "x"}}})
        )
        with self.assertRaises(models.ModelConfigError) as raised:
            models.load(worktree)
        self.assertEqual("config_invalid", raised.exception.code)
        self.assertIn("schema_version 2", str(raised.exception))
        self.assertIn("keyed by worker id", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
