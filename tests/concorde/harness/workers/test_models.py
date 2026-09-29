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


def _enabled(*names: str, **levels: str) -> dict:
    """``enabled_models`` admitting ``names``, with a level for each model in ``levels``."""
    return {
        name: {"reasoning": levels[name]} if name in levels else {} for name in names
    }


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

    @verifies("scenario.workers.backend-default")
    def test_a_worker_without_an_entry_runs_on_pi(self):
        session = dict(self.environ, CLAUDECODE="1")
        bare = {
            "schema_version": 1,
            "enabled_models": _enabled("a/pi"),
            "default": {"model": "a/pi"},
        }
        self.assertEqual(
            ("pi", "Concorde's default worker backend"),
            _backend(models.worker_choice(bare, "implement", "worker", session)),
        )

    def _checker_on_claude(self) -> dict:
        config = {
            "schema_version": 1,
            "enabled_models": _enabled("a/pi", "opus"),
            "default": {"model": "a/pi"},
            "operations": {
                "spec_review": {
                    "workers": {
                        "checker": {
                            "backend": "claude",
                            "model": "opus",
                            "reasoning": "high",
                        }
                    }
                }
            },
        }
        self.save(config)
        self.assertEqual(config, models.load(self.base))
        return config

    @verifies("scenario.workers.backend-configured")
    def test_workers_run_on_pi_unless_their_configuration_chooses_claude_code(self):
        session = dict(self.environ, CLAUDECODE="1")
        config = self._checker_on_claude()
        reviewer = models.worker_choice(config, "spec_review", "reviewer", session)
        checker = models.worker_choice(config, "spec_review", "checker", session)
        self.assertEqual(("pi", "a/pi"), (reviewer["backend"], reviewer["model"]))
        # Choosing Claude Code starts that program afresh: the pi default model is not inherited.
        self.assertEqual(
            (
                "claude",
                "operations.spec_review.workers.checker",
                "opus",
                "operations.spec_review.workers.checker",
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

    @verifies("scenario.workers.backend-missing")
    def test_a_worker_whose_backend_is_not_installed_is_refused(self):
        config = self._checker_on_claude()
        missing = dict(
            self.environ, CLAUDECODE="1", CONCORDE_PI=str(self.base / "nowhere")
        )
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
            "enabled_models": _enabled("a/default", "a/panel", "a/second"),
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

    @verifies("scenario.workers.model-levels")
    def test_a_models_own_level_applies_when_the_entry_choosing_it_sets_none(self):
        config = {
            "schema_version": 1,
            "enabled_models": _enabled(
                "a/default",
                "a/deep",
                "a/plain",
                **{"a/default": "low", "a/deep": "high"},
            ),
            "default": {"model": "a/default"},
            "operations": {
                "spec_panel": {
                    "default": {"reasoning": "medium"},
                    "workers": {
                        "reviewer1": {"model": "a/deep"},
                        "reviewer2": {"model": "a/deep", "reasoning": "xhigh"},
                        "reviewer3": {"model": "a/plain"},
                    },
                }
            },
        }
        models.validate_config(config)

        def level(operation, worker):
            chosen = models.choice(config, operation, worker)
            return chosen["reasoning"], chosen["reasoning_source"]

        # The default's model at its own level: the entry that chose it sets none.
        self.assertEqual(
            ("low", 'enabled_models["a/default"]'), level("implement", "worker")
        )
        # A level set more specifically than the model is meant for it.
        self.assertEqual(
            ("medium", "operations.spec_panel.default"), level("spec_panel", "chair")
        )
        # A model chosen more specifically than any level takes its own level...
        self.assertEqual(
            ("high", 'enabled_models["a/deep"]'), level("spec_panel", "reviewer1")
        )
        # ...unless its own entry sets one,
        self.assertEqual(
            ("xhigh", "operations.spec_panel.workers.reviewer2"),
            level("spec_panel", "reviewer2"),
        )
        # and a model without a level of its own keeps the one inherited.
        self.assertEqual(
            ("medium", "operations.spec_panel.default"),
            level("spec_panel", "reviewer3"),
        )
        bare = dict(config, enabled_models=_enabled("a/default"), operations={})
        self.assertEqual(
            (None, "the backend's own default"),
            (
                models.choice(bare, "implement", "worker")["reasoning"],
                models.choice(bare, "implement", "worker")["reasoning_source"],
            ),
        )
        for wrong in (
            # a level of neither backend,
            _enabled("a/default", **{"a/default": "bogus"}),
            # and a pi level a worker on Claude Code would take.
            _enabled("a/default", **{"a/default": "off"}),
        ):
            invalid = {
                "schema_version": 1,
                "enabled_models": wrong,
                "default": {"backend": "claude", "model": "a/default"},
            }
            with (
                self.subTest(enabled=wrong),
                self.assertRaises(models.ModelConfigError) as raised,
            ):
                models.validate_config(invalid)
            self.assertEqual("config_invalid", raised.exception.code)
            self.assertIn("reasoning", str(raised.exception))

    @verifies("scenario.workers.model-unresolved")
    def test_a_worker_whose_configuration_names_no_model_is_refused(self):
        config = {
            "schema_version": 1,
            "enabled_models": _enabled("a/pi"),
            "default": {"reasoning": "high"},
            "operations": {
                "spec_review": {"default": {"model": "a/pi"}},
                "spec_panel": {"workers": {"chair": {"backend": "claude"}}},
            },
        }
        self.assertEqual(
            "a/pi",
            models.worker_choice(config, "spec_review", "checker", self.environ)[
                "model"
            ],
        )
        for operation, worker, entries in (
            (
                "implement",
                "worker",
                (
                    "operations.implement.workers.worker, operations.implement.default, "
                    "default"
                ),
            ),
            ("spec_panel", "chair", "(operations.spec_panel.workers.chair)"),
        ):
            with (
                self.subTest(worker=worker),
                self.assertRaises(models.ModelConfigError) as raised,
            ):
                models.worker_choice(config, operation, worker, self.environ)
            self.assertEqual("model_unresolved", raised.exception.code)
            for part in (
                f"the {worker} worker of {operation}",
                entries,
                models.CONFIG,
                "`enabled_models`",
                "never runs a worker on its program's own default model",
            ):
                self.assertIn(part, str(raised.exception))

    @verifies("scenario.workers.model-not-enabled")
    def test_a_model_outside_the_enabled_models_is_refused(self):
        base = {"schema_version": 1, "enabled_models": _enabled("a/one", "a/two")}
        models.validate_config(dict(base, default={"model": "a/one"}))
        for config, where in (
            (dict(base, default={"model": "a/three"}), "default.model"),
            (
                dict(
                    base,
                    default={"model": "a/one"},
                    operations={"spec_panel": {"default": {"model": "a/three"}}},
                ),
                "operations.spec_panel.default.model",
            ),
            (
                dict(
                    base,
                    default={"model": "a/one"},
                    operations={
                        "spec_panel": {"workers": {"chair": {"model": "a/three"}}}
                    },
                ),
                "operations.spec_panel.workers.chair.model",
            ),
        ):
            with (
                self.subTest(where=where),
                self.assertRaises(models.ModelConfigError) as raised,
            ):
                models.validate_config(config)
            self.assertEqual("model_not_enabled", raised.exception.code)
            for part in (where, "'a/three'", "a/one, a/two", "add it to"):
                self.assertIn(part, str(raised.exception))
        for missing, text in (
            ({"schema_version": 1, "default": {"model": "a/one"}}, "is missing"),
            (dict(base, enabled_models={}), "is empty"),
        ):
            with (
                self.subTest(enabled=missing.get("enabled_models")),
                self.assertRaises(models.ModelConfigError) as raised,
            ):
                models.validate_config(missing)
            self.assertEqual("config_invalid", raised.exception.code)
            self.assertIn("`enabled_models` " + text, str(raised.exception))

    @verifies("scenario.workers.config-missing")
    def test_a_worktree_without_a_worker_configuration_runs_no_worker(self):
        with self.assertRaises(models.ModelConfigError) as raised:
            models.load(self.base)
        self.assertEqual("config_missing", raised.exception.code)
        for part in (
            str(models.config_path(self.base)),
            "every worker needs it",
            "`enabled_models`",
            "`default` model",
            "commit it",
            "never takes a worker's model from the developer's own pi",
        ):
            self.assertIn(part, str(raised.exception))

    @verifies("scenario.workers.model-refused")
    def test_validation_accepts_custom_models_and_rejects_invalid_structure(self):
        config = {
            "schema_version": 1,
            "enabled_models": _enabled("offline/custom"),
            "default": {"model": "offline/custom", "reasoning": "high"},
        }
        models.validate_config(config)
        self.save(config)
        self.assertEqual(
            "offline/custom",
            models.worker_choice(config, "implement", "worker", self.environ)["model"],
        )
        enabled = {"schema_version": 1, "enabled_models": _enabled("x")}
        for invalid in (
            dict(enabled, default={"model": " "}),
            dict(enabled, default={"model": "\x00"}),
            dict(enabled, default={"model": "custom\n"}),
            dict(enabled, default={"reasoning": "bogus"}),
            dict(enabled, default={"backend": "claude", "reasoning": "off"}),
            dict(enabled, operations={"typo": {"default": {"model": "x"}}}),
            dict(enabled, operations={"delivery": {}}),
            dict(enabled, limits={"max_turns": 0}),
            dict(enabled, limits={"timeout": 60}),
            dict(enabled, runtime=[".venv", ".venv"]),
            dict(enabled, enabled_models={" x": {}}),
            dict(enabled, enabled_models={"x": {"level": "high"}}),
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
        enabled = {
            "schema_version": 1,
            "enabled_models": _enabled("x"),
            "default": {"model": "x"},
        }
        self.save(enabled)
        plain = models.load(self.base)
        self.assertEqual(models.LIMITS, models.limits(plain))
        self.assertEqual((".venv", "node_modules"), models.runtime(plain))
        self.save(dict(enabled, limits={"max_turns": 50, "rounds": 1}, runtime=["env"]))
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
        self.save(
            {
                "schema_version": 1,
                "enabled_models": _enabled("y"),
                "default": {"model": "y"},
            }
        )
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
                    "enabled_models": _enabled("x"),
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
