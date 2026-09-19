"""Token accounting: Pi's session statistics are labelled per step, persisted and summarized."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from concorde.harness.model_selection import WorkerSelection
from concorde.harness.usage import read_usage, record_usage, summarize_usage, usage_path
from concorde.harness.worker_executor import ExecutionUsage
from concorde.spec.verification import verifies


class UsageRecordTests(unittest.TestCase):
    def host(self, root: Path, events: list):
        return SimpleNamespace(
            project_root=root,
            invocation_id="child-1",
            root_invocation_id="root-1",
            depth=2,
            observe=lambda event, **details: events.append((event, details)),
        )

    def invocation(self):
        return SimpleNamespace(
            invocation_id="launch-1",
            context_id="sha256:" + "b" * 64,
            selection=WorkerSelection("openai-codex/gpt-6-astra", "medium"),
        )

    @verifies("scenario.harness.usage-accounting")
    def test_each_launch_appends_one_labelled_line_under_the_root_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            events: list = []
            host = self.host(root, events)
            usage = ExecutionUsage(
                model="openai-codex/gpt-6-astra",
                thinking="medium",
                input_tokens=10,
                cached_input_tokens=None,
                output_tokens=5,
                total_tokens=15,
                cost_usd=None,
                turns=3,
                wall_seconds=1.5,
                prompt_bytes=100,
                context_bytes=2000,
            )
            record = record_usage(
                host,
                operation="concorde-plan",
                stage="plan",
                target_id="module.a",
                agent="concorde-planner",
                invocation=self.invocation(),
                result=SimpleNamespace(usage=usage),
                change_id="change-1",
            )
            record_usage(
                host,
                operation="concorde-code-review",
                stage="code-review",
                target_id="module.a",
                agent="concorde-code-reviewer",
                invocation=self.invocation(),
                result=SimpleNamespace(usage=None),
            )
            lines = (root / usage_path("root-1")).read_text().splitlines()
            self.assertEqual(2, len(lines))
            first = json.loads(lines[0])
            self.assertEqual(2, first["schema_version"])
            self.assertEqual(record, first)
            self.assertEqual(
                (
                    "root-1",
                    "child-1",
                    2,
                    "concorde-plan",
                    "plan",
                    "module.a",
                    "concorde-planner",
                    "change-1",
                    "launch-1",
                    "sha256:" + "b" * 64,
                    "openai-codex/gpt-6-astra",
                ),
                tuple(
                    first[key]
                    for key in (
                        "root_invocation_id",
                        "invocation_id",
                        "depth",
                        "operation",
                        "stage",
                        "target_id",
                        "agent",
                        "change_id",
                        "launch_invocation_id",
                        "context_id",
                        "model",
                    )
                ),
            )
            self.assertEqual(usage.wire(), first["usage"])
            # An unreported figure stays unknown rather than becoming zero.
            self.assertIsNone(first["usage"]["cost_usd"])
            self.assertIsNone(json.loads(lines[1])["usage"])
            self.assertEqual(
                ["agent_usage", "agent_usage"], [event for event, _ in events]
            )
            self.assertEqual(first, events[0][1])
            records = read_usage(root, "root-1")
            self.assertEqual(2, len(records))
            self.assertEqual(records, read_usage(root))

    @verifies("scenario.harness.usage-accounting")
    def test_summary_totals_per_step_stage_target_and_worker(self):
        records = [
            {
                "root_invocation_id": "r",
                "schema_version": 2,
                "operation": "concorde-plan",
                "stage": "plan",
                "target_id": "module.a",
                "agent": "concorde-planner",
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 1,
                    "total_tokens": 11,
                    "wall_seconds": 1.0,
                    "cost_usd": 0.5,
                },
            },
            {
                "root_invocation_id": "r",
                "schema_version": 2,
                "operation": "concorde-implement",
                "stage": "implementation",
                "target_id": "module.a",
                "agent": "concorde-programmer",
                "usage": {
                    "input_tokens": 20,
                    "output_tokens": 2,
                    "total_tokens": 22,
                    "wall_seconds": 2.0,
                },
            },
            {
                "root_invocation_id": "r",
                "schema_version": 2,
                "operation": "concorde-code-review",
                "stage": "code-review",
                "target_id": "module.b",
                "agent": "concorde-programmer",
                "usage": None,
            },
        ]
        summary = summarize_usage(records)
        self.assertEqual(
            {
                "launches": 3,
                "unreported": 1,
                "input_tokens": 30,
                "output_tokens": 3,
                "total_tokens": 33,
                "wall_seconds": 3.0,
                "cost_usd": 0.5,
            },
            summary["total"],
        )
        self.assertEqual(
            {
                "launches": 1,
                "input_tokens": 10,
                "output_tokens": 1,
                "total_tokens": 11,
                "wall_seconds": 1.0,
                "cost_usd": 0.5,
            },
            summary["by_step"]["concorde-plan/plan/module.a"],
        )
        self.assertEqual(33, summary["by_target"]["module.a"]["total_tokens"])
        self.assertEqual(
            {
                "launches": 2,
                "unreported": 1,
                "input_tokens": 20,
                "output_tokens": 2,
                "total_tokens": 22,
                "wall_seconds": 2.0,
            },
            summary["by_agent"]["concorde-programmer"],
        )
        self.assertEqual(
            {"launches": 1, "unreported": 1}, summary["by_stage"]["code-review"]
        )

    @verifies("scenario.harness.usage-accounting")
    def test_historical_usage_is_identified_without_rewriting_or_losing_step_labels(
        self,
    ):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / usage_path("historical")
            path.parent.mkdir(parents=True)
            legacy = {
                "capability": "concorde-plan",
                "stage": "plan",
                "target_id": "module.a",
                "usage": {"total_tokens": 7},
            }
            original = json.dumps(legacy) + "\n"
            path.write_text(original)
            rows = read_usage(root)
            summary = summarize_usage(rows)
            self.assertEqual(2, summary["schema_version"])
            self.assertTrue(summary["complete"])
            self.assertEqual(1, summary["historical_records"])
            self.assertEqual(
                7, summary["by_step"]["concorde-plan/plan/module.a"]["total_tokens"]
            )
            self.assertEqual([legacy], rows)
            self.assertEqual(original, path.read_text())
            unknown = summarize_usage(
                [
                    {
                        "schema_version": 99,
                        "operation": "concorde-plan",
                        "usage": {"total_tokens": 500},
                    }
                ]
            )
            self.assertFalse(unknown["complete"])
            self.assertEqual(1, unknown["unsupported_records"])
            self.assertEqual({}, unknown["total"])

    @verifies("scenario.harness.usage-accounting")
    def test_a_persistence_failure_never_fails_the_launch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".concorde").write_text("not a directory")
            events: list = []
            record = record_usage(
                self.host(root, events),
                operation="concorde-plan",
                stage="plan",
                target_id="module.a",
                agent="concorde-planner",
                invocation=self.invocation(),
                result=SimpleNamespace(usage=None),
            )
            self.assertIsNotNone(record)
            self.assertEqual(1, len(events))


if __name__ == "__main__":
    unittest.main()
