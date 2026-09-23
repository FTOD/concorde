"""Per-worker selection of Pi model, thinking level and timeout, and its admission."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.harness import configure  # noqa: E402
from concorde.harness.configuration import (
    admit_configuration,
    load_configuration,
)  # noqa: E402
from concorde.harness.model_selection import (
    WorkerSelection,
    validate_worker_selections,
    worker_selection,
)  # noqa: E402
from concorde.spec.typed_data import TypedDataError, typed  # noqa: E402
from concorde.spec.verification import verifies  # noqa: E402
from tests.concorde.support.spec_project import PACKAGE, project  # noqa: E402


def configuration(**data) -> dict:
    return typed("concorde-operation-configuration", data)


class ResolutionTests(unittest.TestCase):
    @verifies("scenario.execution.model-selection")
    def test_worker_entry_wins_over_project_default(self):
        value = configuration(
            model="openai-codex/gpt-6-astra",
            thinking="medium",
            timeout_seconds=1200,
            workers={
                "programmer": {"thinking": "high", "timeout_seconds": 5400},
            },
        )
        self.assertEqual(
            WorkerSelection("openai-codex/gpt-6-astra", "medium", 1200),
            worker_selection(value, "router"),
        )
        self.assertEqual(
            WorkerSelection("openai-codex/gpt-6-astra", "high", 5400),
            worker_selection(value, "programmer"),
        )
        # Hyphenated and external worker names resolve to the same entries.
        self.assertEqual(
            worker_selection(value, "code_reviewer"),
            worker_selection(value, "concorde-code-reviewer"),
        )
        validate_worker_selections(value)

    @verifies("scenario.execution.model-selection")
    def test_absent_values_keep_pi_and_profile_defaults(self):
        self.assertEqual(
            WorkerSelection(), worker_selection(configuration(), "answerer")
        )
        self.assertEqual(
            WorkerSelection(thinking="xhigh"),
            worker_selection(
                configuration(workers={"planner": {"thinking": "xhigh"}}),
                "planner",
            ),
        )


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / ".concorde/config.json"
        self.path.parent.mkdir()
        self.original = configuration(model="openai-codex/gpt-6-astra")
        self.write(self.original)

    def write(self, value: dict) -> None:
        self.path.write_text(
            json.dumps(
                {
                    "profile_version": 13,
                    "registry": ".concorde/specs.json",
                    "operation_configuration": value,
                }
            )
        )

    def stored(self) -> dict:
        return json.loads(self.path.read_text())["operation_configuration"]

    @verifies("scenario.execution.model-selection-reject")
    def test_unknown_keys_child_timeouts_bad_timeouts_and_models_are_rejected(self):
        invalid = {
            "unknown worker": (
                configuration(workers={"reviewer": {"model": "openai-codex/m"}}),
                "/workers/reviewer",
            ),
            "undeclared child": (
                configuration(workers={"answerer/scout": {"thinking": "low"}}),
                "/workers/answerer~1scout",
            ),
            "child timeout": (
                configuration(workers={"programmer/scout": {"thinking": "low"}}),
                "/workers/programmer~1scout",
            ),
            "nonpositive worker timeout": (
                configuration(workers={"planner": {"timeout_seconds": 0}}),
                "/timeout_seconds",
            ),
            "nonpositive default timeout": (
                configuration(timeout_seconds=-5),
                "/data/timeout_seconds",
            ),
            "model without provider": (
                configuration(model="gpt-6-astra"),
                "/data/model",
            ),
        }
        for label, (value, field) in invalid.items():
            with self.subTest(label):
                with self.assertRaises(TypedDataError) as raised:
                    validate_worker_selections(value)
                self.assertEqual("invalid_field", raised.exception.code)
                self.assertIn(field, raised.exception.field)
                with self.assertRaises(TypedDataError):
                    admit_configuration(value)
        for entry in (
            {"temperature": 1},
            {"thinking": "extreme"},
            "openai-codex/gpt-6-astra",
        ):
            with self.subTest(entry=entry):
                with self.assertRaises(TypedDataError):
                    configuration(workers={"programmer": entry})

    @verifies("scenario.execution.model-selection-reject")
    def test_forged_application_and_stored_invalid_selection_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project(root)
            valid = configuration(
                workers={"programmer": {"model": "anthropic/claude-sonnet-5"}}
            )
            proposed = configure.propose(root, PACKAGE, valid)["data"]
            self.assertEqual("proposed", proposed["status"])
            forged = copy.deepcopy(proposed["proposal"])
            forged["data"]["configuration"] = configuration(
                workers={"programmer/verifier": {"timeout_seconds": 30}}
            )
            before = (root / ".concorde/config.json").read_bytes()
            with self.assertRaises(TypedDataError):
                configure.apply(
                    root, PACKAGE, forged, configure.proposal_digest(forged)
                )
            self.assertEqual(before, (root / ".concorde/config.json").read_bytes())
            configure.apply(
                root, PACKAGE, proposed["proposal"], proposed["proposal_digest"]
            )
            self.assertEqual(valid, load_configuration(root))
        self.write(configuration(workers={"nobody": {}}))
        with self.assertRaises(TypedDataError):
            load_configuration(self.root)


if __name__ == "__main__":
    unittest.main()
