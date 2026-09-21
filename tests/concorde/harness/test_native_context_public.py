"""Opt-in actual candidate-entry/native-executor tests with scripted model events."""

import json
import os
import subprocess
import unittest
from pathlib import Path

from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT


@unittest.skipUnless(
    os.environ.get("CONCORDE_NATIVE_SUBAGENTS")
    and os.environ.get("CONCORDE_NATIVE_PI"),
    "explicit native package roots required",
)
class NativeContextPublicTests(unittest.TestCase):
    @verifies(
        "scenario.harness.native-context-public",
        "scenario.planning.assessment-sufficient",
        "scenario.planning.assessment-gap",
    )
    def test_actual_candidate_entry_and_native_context_agent(self):
        for scenario in (
            "sufficient",
            "duplicate-launch",
            "unsupported",
            "gap-result",
            "business-invalid",
            "malformed",
            "foreign",
            "duplicate",
            "native-failure",
            "proposal-tamper",
            "cancel",
            "stale",
            "preflight-gap",
            "describe",
            "shadow",
            "agent-tamper",
            "extension-tamper",
            "missing-capsule",
        ):
            with self.subTest(scenario=scenario):
                result = subprocess.run(
                    [
                        "node",
                        str(Path(__file__).with_name("native_context_probe.mjs")),
                        os.environ["CONCORDE_NATIVE_SUBAGENTS"],
                        os.environ["CONCORDE_NATIVE_PI"],
                        str(REPOSITORY_ROOT),
                        scenario,
                    ],
                    cwd=REPOSITORY_ROOT,
                    capture_output=True,
                    text=True,
                    timeout=45,
                )
                self.assertEqual(result.returncode, 0, result.stderr[-12000:])
                value = json.loads(result.stdout.strip().splitlines()[-1])
                self.assertEqual(value["realModelCalls"], 0)
                print(json.dumps(value, sort_keys=True))
