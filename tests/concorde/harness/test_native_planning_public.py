"""Managed native plan/tasks integration; real public entry/runtime, scripted model events."""

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
    "explicit reviewed runtime roots required",
)
class NativePlanningPublicTests(unittest.TestCase):
    @verifies("scenario.planning.native-plan-tasks")
    def test_managed_native_plan_and_tasks(self):
        scenarios = os.environ.get(
            "CONCORDE_NATIVE_PLANNING_CASES",
            "normal primary replan prior-gap assessor-gap native-failure cancel shutdown empty-plan stale-spec stale-metadata stale-intent missing-plan stale-plan empty-tasks duplicate-tasks reserved scope-repair stale-scope stale-review references stale-reference review-required",
        ).split()
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                result = subprocess.run(
                    [
                        "node",
                        str(Path(__file__).with_name("native_planning_probe.mjs")),
                        os.environ["CONCORDE_NATIVE_SUBAGENTS"],
                        os.environ["CONCORDE_NATIVE_PI"],
                        str(REPOSITORY_ROOT),
                        scenario,
                    ],
                    cwd=REPOSITORY_ROOT,
                    capture_output=True,
                    text=True,
                    timeout=100,
                )
                self.assertEqual(result.returncode, 0, result.stderr[-12000:])
                value = json.loads(result.stdout.strip().splitlines()[-1])
                self.assertEqual(value["realModelCalls"], 0)
                print(json.dumps(value, sort_keys=True))
