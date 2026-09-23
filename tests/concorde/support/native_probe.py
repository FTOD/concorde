"""Run the opt-in native probes that drive real Pi tools with scripted, model-free reasoning."""

import json
import os
import subprocess

from .paths import REPOSITORY_ROOT

PROBES = REPOSITORY_ROOT / "tests/concorde/harness"


def run_native_probe(test, probe, cases):
    """Run a native probe under ``tests/concorde/harness/`` once per case and print its record."""
    for case in cases:
        with test.subTest(case=case):
            result = subprocess.run(
                [
                    "node",
                    str(PROBES / probe),
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
            test.assertEqual(result.returncode, 0, result.stderr[-12000:])
            value = json.loads(result.stdout.strip().splitlines()[-1])
            test.assertEqual(value["realModelCalls"], 0)
            print(json.dumps(value, sort_keys=True))
