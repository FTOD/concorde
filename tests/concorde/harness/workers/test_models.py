"""The worker configuration: client detection, candidates, resolution, limits and refusals."""

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

    def save(self, config: dict) -> None:
        path = models.config_path(self.base)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config))

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
        empty = {"schema_version": 1}
        self.assertEqual(
            ("pi", "Concorde's default worker backend"),
            _backend(models.worker_choice(empty, "implement", "worker", session)),
        )
        config = {
            "schema_version": 1,
            "default": {"model": "a/pi"},
            "operations": {
                "spec_review": {
                    "workers": {"checker": {"backend": "claude", "reasoning": "high"}}
                }
            },
        }
        self.save(config)
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
        config = {
            "schema_version": 1,
            "default": {"model": "a/default", "reasoning": "medium"},
            "operations": {
                "spec_panel": {
                    "default": {"model": "a/panel"},
                    "workers": {
                        "reviewer2": {"model": "a/second"},
                        "chair": {"reasoning": "high"},
                    },
                }
            },
        }
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

    @verifies("scenario.workers.model-refused")
    def test_validation_accepts_custom_models_and_rejects_invalid_structure(self):
        config = {
            "schema_version": 1,
            "default": {"model": "offline/custom", "reasoning": "high"},
        }
        models.validate_config(config)
        self.save(config)
        self.assertEqual(
            "offline/custom",
            models.worker_choice(config, "implement", "worker", self.environ)["model"],
        )
        for invalid in (
            {"schema_version": 1, "default": {"model": " "}},
            {"schema_version": 1, "default": {"model": "\x00"}},
            {"schema_version": 1, "default": {"model": "custom\n"}},
            {"schema_version": 1, "default": {"reasoning": "bogus"}},
            {"schema_version": 1, "default": {"backend": "claude", "reasoning": "off"}},
            {"schema_version": 1, "operations": {"typo": {"default": {"model": "x"}}}},
            {"schema_version": 1, "operations": {"delivery": {}}},
            {"schema_version": 1, "limits": {"max_turns": 0}},
            {"schema_version": 1, "limits": {"timeout": 60}},
            {"schema_version": 1, "runtime": [".venv", ".venv"]},
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

    @verifies("scenario.workers.limits-configured")
    def test_limits_and_runtime_come_from_the_worker_configuration(self):
        empty = models.load(self.base)
        self.assertEqual(models.LIMITS, models.limits(empty))
        self.assertEqual((".venv", "node_modules"), models.runtime(empty))
        self.save(
            {
                "schema_version": 1,
                "limits": {"max_turns": 50, "rounds": 1},
                "runtime": ["env"],
            }
        )
        config = models.load(self.base)
        self.assertEqual(
            {**models.LIMITS, "max_turns": 50, "rounds": 1}, models.limits(config)
        )
        self.assertEqual(("env",), models.runtime(config))

    @verifies("scenario.workers.retired-configuration")
    def test_the_retired_untracked_file_is_refused_not_ignored(self):
        retired = self.base / models.RETIRED
        retired.parent.mkdir(parents=True)
        retired.write_text('{"schema_version": 3, "default": {"model": "x"}}')
        with self.assertRaises(models.ModelConfigError) as raised:
            models.load(self.base)
        self.assertEqual("config_invalid", raised.exception.code)
        for part in (models.RETIRED, models.CONFIG, "commit it"):
            self.assertIn(part, str(raised.exception))
        self.save({"schema_version": 1, "default": {"model": "y"}})
        self.assertEqual({"model": "y"}, models.load(self.base)["default"])

    def test_duplicate_json_keys_are_refused(self):
        path = models.config_path(self.base)
        path.parent.mkdir()
        path.write_text(
            '{"schema_version": 1, "default": {"model": "x", "model": "y"}}'
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
                    "schema_version": 1,
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
        self.assertIn("expected 1", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
