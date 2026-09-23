"""Explicit installed-runtime contract tests; no provider or model is contacted.

Opt in with CONCORDE_NATIVE_SUBAGENTS and CONCORDE_NATIVE_PI pointing to the
reviewed absolute package roots. Ordinary portable suite runs skip this optional
host dependency, rather than selecting global packages implicitly.
"""

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
    "explicit reviewed native runtime roots required",
)
class NativePublicationTests(unittest.TestCase):
    @verifies("scenario.execution.workflow-coverage")
    def test_real_native_publication_and_failure_boundaries(self):
        for scenario in (
            "success",
            "session-file",
            "async-child",
            "failed-child",
            "interrupted-child",
            "metadata-write-failure",
            "status-write-failure",
            "malformed-metadata",
            "business-invalid",
            "duplicate-output",
            "gate-mixed-output",
            "gate-truncated-output",
            "missing-binding",
            "cancel-before-commit",
            "cancel-after-commit",
        ):
            with self.subTest(scenario=scenario):
                result = subprocess.run(
                    [
                        "node",
                        str(Path(__file__).with_name("native_publication_probe.mjs")),
                        os.environ["CONCORDE_NATIVE_SUBAGENTS"],
                        os.environ["CONCORDE_NATIVE_PI"],
                        str(REPOSITORY_ROOT),
                        scenario,
                    ],
                    cwd=REPOSITORY_ROOT,
                    capture_output=True,
                    text=True,
                    timeout=240,
                )
                self.assertEqual(result.returncode, 0, result.stderr[-16000:])
                report = json.loads(result.stdout.strip().splitlines()[-1])
                self.assertEqual(report["scenario"], scenario)
                # Full native files stay in the named disposable directory for
                # diagnostics; this output is not a successful model-run receipt.
                print(json.dumps(report, sort_keys=True))
