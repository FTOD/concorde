"""Actual native Issue workflow/publication with scripted terminal model events only."""

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
class NativeIssueTests(unittest.TestCase):
    @verifies("scenario.issues.native-solve")
    def test_native_issue_workflow(self):
        cases = os.environ.get(
            "CONCORDE_NATIVE_ISSUE_CASES",
            "prose-only observe-resolved needs-decision develop spec-repair resolved duplicate not-actionable stale-issue stale-input stale-duplicate native-failure cancel review-native-failure review-cancel budget incomplete-review final-failure exhaustion journal slot-change missing-slot call-mismatch control-extra control-large many",
        ).split()
        for case in cases:
            with self.subTest(case=case):
                result = subprocess.run(
                    [
                        "node",
                        str(Path(__file__).with_name("native_issue_probe.mjs")),
                        os.environ["CONCORDE_NATIVE_SUBAGENTS"],
                        os.environ["CONCORDE_NATIVE_PI"],
                        str(REPOSITORY_ROOT),
                        case,
                    ],
                    cwd=REPOSITORY_ROOT,
                    capture_output=True,
                    text=True,
                    timeout=1200 if case == "many" else 600,
                )
                self.assertEqual(result.returncode, 0, result.stderr[-14000:])
                value = json.loads(result.stdout.strip().splitlines()[-1])
                self.assertEqual(value["realModelCalls"], 0)
                print(json.dumps(value, sort_keys=True))
