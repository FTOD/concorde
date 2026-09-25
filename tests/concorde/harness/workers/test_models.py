"""The worker model configuration: client detection, candidates, resolution and changes."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from concorde.harness import models
from concorde.spec.verification import verifies
from tests.concorde.support.agent_fakes import fake_agents


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
    def test_the_configuration_may_choose_another_program(self):
        config = {
            "schema_version": 2,
            "backend": {
                "default": "pi",
                "operations": {"spec_review": {"roles": {"checker": "claude"}}},
            },
            "pi": {"default": {"model": "a/pi"}},
            "claude": {"default": {"model": "opus"}},
        }
        path = models.save(self.base, config)
        self.assertEqual(config, models.load(self.base))
        session = dict(self.environ, CLAUDECODE="1")
        self.assertEqual(
            ("pi", "backend.default"),
            models.worker_backend(config, "implement", "worker", session),
        )
        self.assertEqual(
            ("pi", "backend.default"),
            models.worker_backend(config, "spec_review", "reviewer", session),
        )
        self.assertEqual(
            ("claude", "backend.operations.spec_review.roles.checker"),
            models.worker_backend(config, "spec_review", "checker", session),
        )
        self.assertEqual(
            ("a/pi", "opus"),
            (
                models.selection(config, "pi", "spec_review", "reviewer")["model"],
                models.selection(config, "claude", "spec_review", "checker")["model"],
            ),
        )
        self.assertEqual(
            ("pi", "backend.default"),
            models.worker_backend(config, "implement", "worker", self.environ),
        )
        self.assertEqual(
            ("claude", "CLAUDECODE=1"),
            models.worker_backend(
                {"schema_version": 2}, "implement", "worker", session
            ),
        )
        missing = dict(session, CONCORDE_PI=str(self.base / "nowhere"))
        with self.assertRaises(models.ModelConfigError) as raised:
            models.worker_backend(config, "implement", "worker", missing)
        self.assertEqual("backend_missing", raised.exception.code)
        for part in ("backend.default", "CONCORDE_PI", "never falls back"):
            self.assertIn(part, str(raised.exception))
        self.assertEqual(
            "claude",
            models.worker_backend(config, "spec_review", "checker", missing)[0],
        )
        path.write_text(
            json.dumps({"schema_version": 2, "backend": {"default": "codex"}})
        )
        with self.assertRaises(models.ModelConfigError) as raised:
            models.load(self.base)
        self.assertEqual("config_invalid", raised.exception.code)

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
        config = {"schema_version": 2}
        models.set_choice(config, "pi", None, None, "a/default", "medium")
        models.set_choice(config, "pi", "spec_review", None, "a/review", None)
        models.set_choice(config, "pi", "spec_review", "checker", None, "low")
        checker = models.selection(config, "pi", "spec_review", "checker")
        self.assertEqual(
            (
                "a/review",
                "low",
                "pi.operations.spec_review",
                "pi.operations.spec_review.roles.checker",
            ),
            (
                checker["model"],
                checker["reasoning"],
                checker["model_source"],
                checker["reasoning_source"],
            ),
        )
        reviewer = models.selection(config, "pi", "spec_review", "reviewer")
        self.assertEqual(
            ("a/review", "medium"), (reviewer["model"], reviewer["reasoning"])
        )
        other = models.selection(config, "pi", "implement", "worker")
        self.assertEqual(
            ("a/default", "pi.default"), (other["model"], other["model_source"])
        )
        self.assertIsNone(
            models.selection(config, "claude", "implement", "worker")["model"]
        )
        self.assertTrue(models.unset_choice(config, "pi", "spec_review", "checker"))
        self.assertEqual(
            {
                "default": {"model": "a/default", "reasoning": "medium"},
                "operations": {"spec_review": {"model": "a/review"}},
            },
            config["pi"],
        )
        self.assertTrue(models.unset_choice(config, "pi", "spec_review", None))
        self.assertFalse(models.unset_choice(config, "pi", "spec_review", None))
        self.assertNotIn("operations", config["pi"])

    @verifies("scenario.workers.model-refused")
    def test_a_model_or_level_the_program_does_not_offer_is_refused(self):
        found = models.candidates("pi", self.environ)
        config = {"schema_version": 2}
        with self.assertRaises(models.ModelConfigError) as raised:
            models.check_choice(found, config, "pi", None, None, "a/nope", None, False)
        self.assertEqual("unknown_model", raised.exception.code)
        self.assertIn("anthropic/claude-sonnet-5", str(raised.exception))
        with self.assertRaises(models.ModelConfigError) as raised:
            models.check_choice(
                found, config, "pi", None, None, "local-openai/plain-7", "high", False
            )
        self.assertEqual("unknown_level", raised.exception.code)
        self.assertIn("levels: off", str(raised.exception))
        models.check_choice(found, config, "pi", None, None, "a/nope", None, True)

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
                    "schema_version": 2,
                    "pi": {"operations": {"understand": {"modle": "x"}}},
                }
            )
        )
        with self.assertRaises(models.ModelConfigError) as raised:
            models.load(worktree)
        self.assertEqual("config_invalid", raised.exception.code)
        self.assertIn("modle", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
