"""Token accounting: native usage is parsed, labelled per step, persisted and summarized."""
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from concorde.harness.agent_executor import _claude_envelope, _codex_envelope
from concorde.harness.permissions import (ExecutionUsage, NormalizedPolicy, render_claude_configuration,
                                          render_codex_configuration)
from concorde.harness.usage import read_usage, record_usage, summarize_usage, usage_path
from concorde.spec.verification import verifies


def _policy() -> NormalizedPolicy:
    return NormalizedPolicy(capability="concorde-plan", stage="plan", occurrence=0, role="concorde-spec-engineer",
        agent="concorde-spec-engineer", read_paths=("context.json",), write_paths=(), deny_paths=(),
        default_deny=True, network_enabled=False, credentials="none", outer_sandbox_required=False,
        digest="sha256:" + "a" * 64)


class EnvelopeUsageTests(unittest.TestCase):
    @verifies("scenario.harness.usage-accounting")
    def test_codex_turn_completed_usage_and_item_count_are_reported(self):
        envelope = {"status": "success"}
        stdout = "\n".join(json.dumps(event) for event in (
            {"type": "thread.started", "thread_id": "t"},
            {"type": "item.completed", "item": {"type": "command_execution", "command": "ls"}},
            {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(envelope)}},
            {"type": "turn.completed", "usage": {"input_tokens": 1200, "cached_input_tokens": 1000, "output_tokens": 34}},
        ))
        payload, usage = _codex_envelope(stdout)
        self.assertEqual(envelope, payload)
        self.assertEqual({"turns": 2, "input_tokens": 1200, "cached_input_tokens": 1000, "output_tokens": 34}, usage)

    @verifies("scenario.harness.usage-accounting")
    def test_codex_without_usage_reports_unknown_figures_not_zero(self):
        stdout = "\n".join(json.dumps(event) for event in (
            {"type": "item.completed", "item": {"type": "agent_message", "text": "{}"}},
            {"type": "turn.completed"},
        ))
        _, usage = _codex_envelope(stdout)
        self.assertEqual({"turns": 1}, usage)

    @verifies("scenario.harness.usage-accounting")
    def test_claude_result_usage_cost_turns_and_model_are_reported(self):
        stdout = json.dumps({"type": "result", "subtype": "success", "is_error": False,
            "structured_output": {"status": "success"}, "num_turns": 7, "duration_ms": 4321,
            "total_cost_usd": 0.0421,
            "usage": {"input_tokens": 50, "cache_read_input_tokens": 9000, "cache_creation_input_tokens": 100,
                      "output_tokens": 800},
            "modelUsage": {"claude-sonnet-5": {"inputTokens": 50}}})
        payload, usage = _claude_envelope(stdout)
        self.assertEqual({"status": "success"}, payload)
        self.assertEqual({"input_tokens": 50, "cached_input_tokens": 9100, "output_tokens": 800,
                          "cost_usd": 0.0421, "turns": 7, "duration_ms": 4321, "model": "claude-sonnet-5"}, usage)


class ModelSelectionTests(unittest.TestCase):
    @verifies("scenario.harness.project-configured-model")
    def test_codex_launch_carries_the_project_model_and_effort_in_argv_and_digest(self):
        plain = render_codex_configuration(_policy(), native_enforcement=True)
        selected = render_codex_configuration(_policy(), native_enforcement=True,
                                              model="gpt-6-astra", reasoning_effort="medium")
        argv = selected.argv
        self.assertIn('model="gpt-6-astra"', argv)
        self.assertIn('model_reasoning_effort="medium"', argv)
        self.assertEqual("-", argv[-1])
        self.assertEqual(argv[argv.index('model="gpt-6-astra"') - 1], "-c")
        self.assertNotIn("model", plain.configuration)
        self.assertEqual(("gpt-6-astra", "medium"), (selected.model, selected.reasoning_effort))
        self.assertEqual({"model": "gpt-6-astra", "model_reasoning_effort": "medium"},
                         {key: selected.configuration[key] for key in ("model", "model_reasoning_effort")})
        self.assertNotEqual(plain.digest, selected.digest)
        self.assertNotIn('model=', " ".join(plain.argv))

    @verifies("scenario.harness.project-configured-model")
    def test_claude_launch_carries_the_model_and_effort_in_argv_and_digest(self):
        selected = render_claude_configuration(_policy(), native_enforcement=True,
                                               model="claude-sonnet-5", reasoning_effort="medium")
        self.assertEqual("claude-sonnet-5", selected.argv[selected.argv.index("--model") + 1])
        self.assertEqual("medium", selected.argv[selected.argv.index("--effort") + 1])
        self.assertEqual(("claude-sonnet-5", "medium"), (selected.model, selected.reasoning_effort))
        plain = render_claude_configuration(_policy(), native_enforcement=True)
        self.assertNotIn("--model", plain.argv)
        self.assertNotIn("--effort", plain.argv)
        self.assertNotEqual(plain.digest, selected.digest)


class UsageRecordTests(unittest.TestCase):
    def host(self, root: Path, events: list):
        return SimpleNamespace(project_root=root, invocation_id="child-1", root_invocation_id="root-1", depth=2,
                               observe=lambda event, **details: events.append((event, details)))

    def launch(self):
        return SimpleNamespace(invocation_id="launch-1", workspace_digest="sha256:" + "b" * 64, integration="codex")

    @verifies("scenario.harness.usage-accounting")
    def test_each_launch_appends_one_labelled_line_under_the_root_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            events: list = []
            host = self.host(root, events)
            usage = ExecutionUsage(integration="codex", model="gpt-6-astra", input_tokens=10, output_tokens=5,
                                   total_tokens=15, turns=3, wall_seconds=1.5, prompt_bytes=100, context_bytes=2000)
            result = SimpleNamespace(usage=usage)
            record = record_usage(host, capability="concorde-plan", stage="plan", target_id="module.a",
                                  agent="concorde-spec-engineer", mode="plan", launch=self.launch(), result=result,
                                  change_id="change-1")
            record_usage(host, capability="concorde-review", stage="code-review", target_id="module.a",
                         agent="concorde-programmer", mode="code-review", launch=self.launch(),
                         result=SimpleNamespace(usage=None))
            lines = (root / usage_path("root-1")).read_text().splitlines()
            self.assertEqual(2, len(lines))
            first = json.loads(lines[0])
            self.assertEqual(record, first)
            self.assertEqual(("root-1", "child-1", 2, "concorde-plan", "plan", "module.a", "change-1", "launch-1"),
                             (first["root_invocation_id"], first["invocation_id"], first["depth"], first["capability"],
                              first["stage"], first["target_id"], first["change_id"], first["launch_invocation_id"]))
            self.assertEqual(usage.wire(), first["usage"])
            self.assertIsNone(json.loads(lines[1])["usage"])
            self.assertEqual(["agent_usage", "agent_usage"], [event for event, _ in events])
            self.assertEqual(first, events[0][1])
            records = read_usage(root, "root-1")
            self.assertEqual(2, len(records))
            self.assertEqual(records, read_usage(root))

    @verifies("scenario.harness.usage-accounting")
    def test_summary_totals_per_step_stage_target_and_agent(self):
        records = [
            {"root_invocation_id": "r", "capability": "concorde-plan", "stage": "plan", "target_id": "module.a",
             "agent": "concorde-spec-engineer", "usage": {"input_tokens": 10, "output_tokens": 1, "total_tokens": 11,
                                                          "wall_seconds": 1.0, "cost_usd": 0.5}},
            {"root_invocation_id": "r", "capability": "concorde-implement", "stage": "implementation",
             "target_id": "module.a", "agent": "concorde-programmer",
             "usage": {"input_tokens": 20, "output_tokens": 2, "total_tokens": 22, "wall_seconds": 2.0}},
            {"root_invocation_id": "r", "capability": "concorde-review", "stage": "code-review",
             "target_id": "module.b", "agent": "concorde-programmer", "usage": None},
        ]
        summary = summarize_usage(records)
        self.assertEqual({"launches": 3, "unreported": 1, "input_tokens": 30, "output_tokens": 3, "total_tokens": 33,
                          "wall_seconds": 3.0, "cost_usd": 0.5}, summary["total"])
        self.assertEqual({"launches": 1, "input_tokens": 10, "output_tokens": 1, "total_tokens": 11,
                          "wall_seconds": 1.0, "cost_usd": 0.5}, summary["by_step"]["concorde-plan/plan/module.a"])
        self.assertEqual(33, summary["by_target"]["module.a"]["total_tokens"])
        self.assertEqual({"launches": 2, "unreported": 1, "input_tokens": 20, "output_tokens": 2, "total_tokens": 22,
                          "wall_seconds": 2.0}, summary["by_agent"]["concorde-programmer"])
        self.assertEqual({"launches": 1, "unreported": 1}, summary["by_stage"]["code-review"])

    @verifies("scenario.harness.usage-accounting")
    def test_a_persistence_failure_never_fails_the_launch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".concorde").write_text("not a directory")
            events: list = []
            record = record_usage(self.host(root, events), capability="concorde-plan", stage="plan",
                                  target_id="module.a", agent="a", mode="plan", launch=self.launch(),
                                  result=SimpleNamespace(usage=None))
            self.assertIsNotNone(record)
            self.assertEqual(1, len(events))


if __name__ == "__main__":
    unittest.main()
