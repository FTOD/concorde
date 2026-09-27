"""The worker model configuration: client detection, candidates, resolution and changes."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from concorde.harness import models
from concorde.harness.available_models import candidates
from concorde.spec.verification import verifies
from tests.concorde.support.agent_fakes import fake_agents
from tests.concorde.support.paths import REPOSITORY_ROOT


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
            "edit its backend",
        ):
            self.assertIn(part, str(raised.exception))
        self.assertEqual(
            "claude",
            models.worker_choice(config, "spec_review", "checker", missing)["backend"],
        )

    @verifies("scenario.workers.models-listed")
    def test_the_installed_programs_models_are_listed(self):
        pi = candidates("pi", self.environ)
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
        claude = candidates(
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
            candidates("pi", missing)
        self.assertEqual("backend_missing", raised.exception.code)

    @verifies("scenario.workers.model-resolution")
    def test_the_most_specific_entry_wins_field_by_field(self):
        config: dict = {"schema_version": 3}
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
    def test_validation_accepts_custom_models_and_rejects_invalid_structure(self):
        config = {
            "schema_version": 3,
            "default": {"model": "offline/custom", "reasoning": "high"},
        }
        models.validate_config(config)
        models.save(self.base, config)
        self.assertEqual(
            "offline/custom",
            models.worker_choice(config, "implement", "worker", self.environ)["model"],
        )
        for invalid in (
            {"schema_version": 3, "default": {"model": " "}},
            {"schema_version": 3, "default": {"model": "\x00"}},
            {"schema_version": 3, "default": {"model": "custom\n"}},
            {"schema_version": 3, "default": {"reasoning": "bogus"}},
            {"schema_version": 3, "default": {"backend": "claude", "reasoning": "off"}},
            {"schema_version": 3, "operations": {"typo": {"default": {"model": "x"}}}},
            {"schema_version": 3, "operations": {"delivery": {}}},
        ):
            with (
                self.subTest(config=invalid),
                self.assertRaises(models.ModelConfigError),
            ):
                models.validate_config(invalid)

    @verifies("scenario.workers.models-standalone")
    def test_standalone_discovery_outside_git_and_missing_program(self):
        script = REPOSITORY_ROOT / "scripts/available_models.py"
        for backend in ("pi", "claude"):
            done = subprocess.run(
                [sys.executable, str(script), "--backend", backend, "--json"],
                cwd=self.base,
                env=dict(os.environ, **self.environ),
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, done.returncode, done.stderr)
            value = json.loads(done.stdout)
            self.assertEqual(backend, value["backend"])
            self.assertIn("no API call is probed", value["note"])
        done = subprocess.run(
            [sys.executable, str(script), "--backend", "pi", "--json"],
            cwd=self.base,
            env=dict(
                os.environ, **dict(self.environ, CONCORDE_PI=str(self.base / "missing"))
            ),
            capture_output=True,
            text=True,
        )
        self.assertEqual(1, done.returncode)
        self.assertEqual("backend_missing", json.loads(done.stdout)["error"]["code"])

    def test_duplicate_json_keys_are_refused(self):
        path = models.config_path(self.base)
        path.parent.mkdir()
        path.write_text(
            '{"schema_version": 3, "default": {"model": "x", "model": "y"}}'
        )
        with self.assertRaisesRegex(models.ModelConfigError, "duplicate key"):
            models.load(self.base)

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
