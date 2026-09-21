"""Opt-in native programmer/reviewer integration with scripted reasoning, real tools/publication."""

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
    "explicit native roots required",
)
class NativeImplementationReviewTests(unittest.TestCase):
    def run_cases(self, probe, cases):
        for case in cases:
            with self.subTest(case=case):
                result = subprocess.run(
                    [
                        "node",
                        str(Path(__file__).with_name(probe)),
                        os.environ["CONCORDE_NATIVE_SUBAGENTS"],
                        os.environ["CONCORDE_NATIVE_PI"],
                        str(REPOSITORY_ROOT),
                        case,
                    ],
                    capture_output=True,
                    text=True,
                    cwd=REPOSITORY_ROOT,
                    timeout=600 if case == "many" else 110,
                )
                self.assertEqual(result.returncode, 0, result.stderr[-12000:])
                value = json.loads(result.stdout.strip().splitlines()[-1])
                self.assertEqual(value["realModelCalls"], 0)
                print(json.dumps(value, sort_keys=True))

    @verifies("scenario.implementation.native-programmer")
    def test_native_programmer_real_candidate_tools(self):
        cases = os.environ.get(
            "CONCORDE_NATIVE_IMPLEMENT_CASES",
            "success feedback tampered-feedback incomplete foreign-task malformed native-failure cancel stale-spec stale-plan stale-tasks stale-feedback missing-components missing-tasks stale-before",
        ).split()
        self.run_cases("native_programmer_probe.mjs", cases)

    @verifies("scenario.review.native-scope")
    def test_native_review_scope(self):
        cases = os.environ.get(
            "CONCORDE_NATIVE_REVIEW_CASES",
            "clean managed code-clean code-shared code-parent advisory blocking incomplete wrong-context wrong-mode wrong-receipt coverage stale native-failure missing budget shared many",
        ).split()
        self.run_cases("native_review_probe.mjs", cases)
