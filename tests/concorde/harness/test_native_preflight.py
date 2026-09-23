"""Native preflight admits only the prepared launch shape; scripted, no model or pi-subagents run."""

import json
import shutil
import subprocess
import unittest
from pathlib import Path

from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT


def _node_strips_types() -> bool:
    node = shutil.which("node")
    if node is None:
        return False
    probe = subprocess.run(
        # -e with a plain write: -p prints through util.inspect, which colours output when
        # FORCE_COLOR is set and would make "true" unrecognizable.
        [
            node,
            "-e",
            "process.stdout.write(String(Boolean(process.features.typescript)))",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return probe.stdout.strip() == "true"


@unittest.skipUnless(
    _node_strips_types(), "requires Node with TypeScript type stripping"
)
class NativePreflightTests(unittest.TestCase):
    @verifies("scenario.execution.preflight-refusal")
    def test_launch_outside_the_prepared_shape_is_refused(self):
        result = subprocess.run(
            [
                "node",
                str(Path(__file__).with_name("native_preflight_driver.mjs")),
                str(REPOSITORY_ROOT),
            ],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr[-4000:])
        value = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual({"preflightCalls": 14, "models": 0}, value)
