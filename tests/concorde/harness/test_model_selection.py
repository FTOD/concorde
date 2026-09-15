"""Per-Agent-node selection of integration, model and reasoning effort, and its admission."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.development.configuration import apply_configuration, load_configuration, propose_configuration  # noqa: E402
from concorde.harness.model_selection import AgentSelection, agent_selection, validate_agent_selections  # noqa: E402
from concorde.spec.typed_data import TypedDataError, typed  # noqa: E402
from concorde.spec.verification import verifies  # noqa: E402


def configuration(**data) -> dict:
    return typed("concorde-capability-configuration", {"integration": "codex", "enforcement": "native", **data})


class ResolutionTests(unittest.TestCase):
    @verifies("scenario.harness.project-configured-model")
    def test_node_entry_wins_over_agent_entry_over_project_default(self):
        value = configuration(model="gpt-6-astra", reasoning_effort="medium", agents={
            "spec_engineer": {"reasoning_effort": "high"},
            "spec_engineer/plan": {"model": "gpt-5.6-sol"},
        })
        self.assertEqual(AgentSelection("codex", "gpt-6-astra", "medium"), agent_selection(value, "coordinator", "route"))
        self.assertEqual(AgentSelection("codex", "gpt-6-astra", "high"), agent_selection(value, "spec_engineer", "tasks"))
        self.assertEqual(AgentSelection("codex", "gpt-5.6-sol", "high"), agent_selection(value, "spec_engineer", "plan"))
        # External and hyphenated Agent names resolve to the same entries.
        self.assertEqual(agent_selection(value, "spec_engineer", "plan"),
                         agent_selection(value, "concorde-spec-engineer", "plan"))

    @verifies("scenario.harness.project-configured-model")
    def test_switching_integration_inherits_no_model_or_effort_from_the_other_client(self):
        value = configuration(model="gpt-6-astra", reasoning_effort="ultra", agents={
            "programmer": {"integration": "claude"},
            "programmer/implementation": {"model": "claude-sonnet-5", "reasoning_effort": "high"},
            "programmer/investigation": {"integration": "codex"},
        })
        self.assertEqual(AgentSelection("claude"), agent_selection(value, "programmer", "code-review"))
        self.assertEqual(AgentSelection("claude", "claude-sonnet-5", "high"),
                         agent_selection(value, "programmer", "implementation"))
        # Switching back to Codex starts from Codex's own defaults, not the project default.
        self.assertEqual(AgentSelection("codex"), agent_selection(value, "programmer", "investigation"))
        validate_agent_selections(value)

    @verifies("scenario.harness.project-configured-model")
    def test_absent_values_keep_the_client_defaults(self):
        self.assertEqual(AgentSelection("claude"), agent_selection(
            typed("concorde-capability-configuration", {"integration": "claude", "enforcement": "native"}),
            "coordinator", "ask"))


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / ".concorde/config.json"
        self.path.parent.mkdir()
        self.original = configuration()
        self.write(self.original)

    def write(self, value: dict) -> None:
        self.path.write_text(json.dumps({"profile_version": 12, "registry": ".concorde/specs.json",
                                         "capability_configuration": value}))

    def stored(self) -> dict:
        return json.loads(self.path.read_text())["capability_configuration"]

    @verifies("scenario.harness.agent-selection-reject")
    def test_unknown_keys_unsupported_efforts_and_unknown_fields_are_rejected(self):
        invalid = {
            "unknown Agent": configuration(agents={"reviewer": {"model": "m"}}),
            "unknown Agent node": configuration(agents={"programmer/plan": {"model": "m"}}),
            "effort Claude does not admit": configuration(agents={"coordinator/route": {
                "integration": "claude", "reasoning_effort": "ultra"}}),
            "default effort Claude does not admit": typed("concorde-capability-configuration", {
                "integration": "claude", "enforcement": "native", "reasoning_effort": "minimal"}),
        }
        for label, value in invalid.items():
            with self.subTest(label):
                with self.assertRaises(TypedDataError) as raised:
                    validate_agent_selections(value)
                self.assertEqual("invalid_field", raised.exception.code)
                self.assertIn("/agents", raised.exception.field)
                self.assertEqual("invalid", propose_configuration(self.root, value).status)
                self.assertEqual(self.original, self.stored())
        for entry in ({"temperature": 1}, {"reasoning_effort": "extreme"}, "gpt-6-astra"):
            with self.subTest(entry=entry):
                with self.assertRaises(TypedDataError):
                    configuration(agents={"programmer": entry})

    @verifies("scenario.harness.agent-selection-reject")
    def test_forged_application_and_stored_invalid_selection_are_rejected(self):
        valid = configuration(agents={"programmer/implementation": {"integration": "claude", "model": "claude-sonnet-5"}})
        proposed = propose_configuration(self.root, valid)
        self.assertEqual("proposal", proposed.status)
        forged = {**proposed.result["proposal"],
                  "configuration": configuration(agents={"programmer/implementation": {
                      "integration": "claude", "reasoning_effort": "minimal"}})}
        (self.root / "forged.json").write_text(json.dumps(forged))
        self.assertEqual("invalid", apply_configuration(self.root, "forged.json").status)
        self.assertEqual(self.original, self.stored())
        (self.root / "accepted.json").write_text(json.dumps(proposed.result["proposal"]))
        self.assertEqual("success", apply_configuration(self.root, "accepted.json").status)
        self.assertEqual(valid, load_configuration(self.root))
        self.write(configuration(agents={"nobody": {}}))
        with self.assertRaises(TypedDataError):
            load_configuration(self.root)


if __name__ == "__main__":
    unittest.main()
