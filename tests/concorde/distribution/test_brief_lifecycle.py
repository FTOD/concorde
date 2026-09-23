"""The maintenance worker's brief lifecycle extension, driven event by event outside Pi."""

from __future__ import annotations

import json

from concorde.spec.verification import verifies
from tests.concorde.distribution.test_session_tool import HarnessCase
from tests.concorde.support.paths import REPOSITORY_ROOT

LIFECYCLE = REPOSITORY_ROOT / "pi/extensions/concorde-brief-lifecycle.ts"
BRIEF = {
    "goal": "CURRENT-GOAL",
    "grant": "candidate only",
    "stage": "component",
    "objective": "brief fixture",
    "blocker": "none",
    "next": "verify",
    "decisions": ["accepted scope"],
    "completed": ["extension"],
    "checks": ["fixture pending"],
    "evidence": ["test_brief_lifecycle.py"],
}
COMPACTION = [{"type": "compaction", "id": "compaction-1"}]
CONTEXT = {
    "emit": "context",
    "event": {"messages": [{"role": "user", "content": "continue"}]},
}


def progress(brief_text: str) -> dict:
    return {
        "emit": "tool_call",
        "event": {
            "toolName": "contact_supervisor",
            "toolCallId": "progress",
            "input": {
                "reason": "progress_update",
                "message": "UPDATE: stage done\n```task-brief\n" + brief_text + "\n```",
            },
        },
    }


class BriefLifecycleTests(HarnessCase):
    def drive(self, steps: list[dict]) -> dict:
        outcome = self.harness(LIFECYCLE, REPOSITORY_ROOT, steps)
        self.assertIsNone(outcome["load_error"])
        return outcome

    @staticmethod
    def injected(step: dict) -> list[str]:
        return [
            message["content"]
            for result in step["results"]
            if result
            for message in result["messages"]
            if message.get("customType") == "concorde.task-brief.v1"
        ]

    @verifies("scenario.session.brief-without-compaction")
    def test_checkpoints_compact_requests_and_failed_compactions_inject_nothing(self):
        outcome = self.drive(
            [
                {"command": "task-brief", "args": json.dumps(BRIEF)},
                progress(json.dumps(BRIEF)),  # a checkpoint
                CONTEXT,
                {
                    "emit": "context",
                    "event": {
                        "messages": [
                            {"role": "user", "content": "/compact"},
                            {"role": "assistant", "content": "Please compact now."},
                        ]
                    },
                },
                {
                    "emit": "session_compact_failed",
                    "event": {
                        "reason": "manual",
                        "aborted": False,
                        "errorMessage": "compaction model failed",
                    },
                },
                CONTEXT,
                # Positive control: only a completed compaction brings the brief back, once.
                {"branch": COMPACTION, "emit": "session_compact", "event": {}},
                CONTEXT,
                CONTEXT,
            ]
        )
        steps = outcome["steps"]
        self.assertTrue(steps[0]["ok"], steps[0])
        for index in (2, 3, 5):
            self.assertEqual([], self.injected(steps[index]), index)
            self.assertEqual([None], steps[index]["results"], index)
        types = [entry["customType"] for entry in outcome["entries"]]
        self.assertIn("concorde.compaction-failed.v1", types)
        [restored] = self.injected(steps[7])
        self.assertIn("CURRENT-GOAL", restored)
        self.assertEqual([], self.injected(steps[8]))

    @verifies("scenario.session.brief-invalid")
    def test_a_malformed_progress_brief_clears_the_brief_and_is_still_delivered(self):
        malformed = progress('{"goal": "only a goal"}')
        outcome = self.drive(
            [
                {"command": "task-brief", "args": json.dumps(BRIEF)},
                malformed,
                {"branch": COMPACTION, "emit": "session_compact", "event": {}},
                CONTEXT,
            ]
        )
        _, delivered, _, context = outcome["steps"]
        # Nothing blocks or rewrites the supervisor message.
        self.assertTrue(all(result is None for result in delivered["results"]))
        self.assertEqual(malformed["event"], delivered["event"])
        entries = [(entry["customType"], entry["data"]) for entry in outcome["entries"]]
        self.assertEqual(("concorde.task-brief.v1", BRIEF), entries[0])
        self.assertEqual(("concorde.task-brief.v1", None), entries[1])
        self.assertEqual("concorde.task-brief-error.v1", entries[2][0])
        # The cleared brief is not injected after the next compaction.
        self.assertEqual([], self.injected(context))
        self.assertIn(("concorde.task-brief-missing.v1", "compaction-1"), entries[3:])
