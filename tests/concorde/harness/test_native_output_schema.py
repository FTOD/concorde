"""The complete native schema crosses SDK argument validation, not just tool.execute."""

import copy
import json
import os
import subprocess
import unittest
from pathlib import Path

from concorde.harness.native_context import native_output_schema
from concorde.spec.typed_data import DATA_SCHEMAS
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT


class NativeOutputSchemaTests(unittest.TestCase):
    @verifies("scenario.harness.native-result-gate")
    def test_supported_payloads_are_reference_free_closed_and_independent(self):
        for kind in ("concorde-agent-stage-result", "concorde-review-stage-result"):
            before = copy.deepcopy(DATA_SCHEMAS[kind])
            result = native_output_schema(kind, "ticket")
            self.assertEqual(
                result["properties"]["result"]["properties"]["data"], before
            )
            self.assertNotIn("$ref", json.dumps(result))
            self.assertFalse(result["additionalProperties"])
            self.assertFalse(result["properties"]["result"]["additionalProperties"])
            self.assertEqual(result["required"], ["invocation_id", "result"])
            self.assertIn(
                "context_id",
                result["properties"]["result"]["properties"]["data"]["required"],
            )
            result["properties"]["result"]["properties"]["data"]["properties"].clear()
            self.assertEqual(DATA_SCHEMAS[kind], before)
        with self.assertRaises(ValueError):
            native_output_schema("concorde-context-snapshot")

    @unittest.skipUnless(
        os.environ.get("CONCORDE_NATIVE_SUBAGENTS")
        and os.environ.get("CONCORDE_NATIVE_PI"),
        "explicit native SDK roots required",
    )
    @verifies("scenario.harness.native-result-gate")
    def test_actual_sdk_double_wrapping_valid_values_and_preserved_live_rejections(
        self,
    ):
        result = subprocess.run(
            [
                "node",
                str(Path(__file__).with_name("native_schema_probe.mjs")),
                os.environ["CONCORDE_NATIVE_SUBAGENTS"],
                os.environ["CONCORDE_NATIVE_PI"],
                str(REPOSITORY_ROOT),
            ],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr[-8000:])
        evidence = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(evidence["realModelCalls"], 0)
        print(json.dumps(evidence))
