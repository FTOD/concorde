"""The executable boundary: scripts/run-operation.py (proposal section 6.3, Stage B1 item 3)."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest

from concorde.spec.verification import verifies
from concorde.spec.wire_shapes import type_version
from tests.concorde.support.paths import REPOSITORY_ROOT

LAUNCHER = REPOSITORY_ROOT / "scripts/run-operation.py"

PUBLIC_SKILLS = (
    "concorde-context-solve",
    "concorde-plan",
    "concorde-tasks",
    "concorde-implement",
    "concorde-issues",
    "concorde-code-review",
    "concorde-spec-review",
    "concorde-init",
    "concorde-configure",
    "concorde-validate",
    "concorde-deliver",
)


def _run(argv, stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(LAUNCHER), *argv],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=REPOSITORY_ROOT,
    )


class RunOperationLauncherTests(unittest.TestCase):
    def test_accepts_each_public_skill_name(self):
        for name in PUBLIC_SKILLS:
            with self.subTest(skill=name):
                invocation = {
                    "type_id": "concorde-operation-invocation",
                    "schema_version": 3,
                    "operation_id": name,
                    "mode": "describe-policy",
                    "configuration": None,
                    "input": {
                        "type_id": f"{name}-request",
                        "schema_version": type_version(name + "-request"),
                        "data": {
                            "target_id": "module.harness",
                            "task": "Explain transfer",
                        },
                    },
                }
                process = _run([name], json.dumps(invocation))
                # Some of these payloads are still rejected as invalid input for that specific
                # skill's own required fields; what this test proves is that the launcher itself
                # routed the name through to the real dispatcher rather than refusing it.
                output = json.loads(process.stdout)
                self.assertNotEqual(
                    "unknown_operation",
                    (output.get("errors") or [{}])[0].get("code"),
                    process.stdout,
                )

    @verifies("scenario.operations.execute-unregistered")
    def test_refuses_a_nonpublic_operation_name(self):
        process = _run(["concorde-planner"], "")
        self.assertEqual(3, process.returncode)
        output = json.loads(process.stdout)
        self.assertEqual("blocked", output["status"])
        self.assertEqual("unknown_operation", output["errors"][0]["code"])

    @verifies("scenario.operations.execute-unregistered")
    def test_refuses_a_bare_operation_word(self):
        process = _run(["plan"], "")
        self.assertEqual(3, process.returncode)
        output = json.loads(process.stdout)
        self.assertEqual("unknown_operation", output["errors"][0]["code"])

    @verifies("scenario.operations.execute-unregistered")
    def test_refuses_an_unknown_name(self):
        process = _run(["concorde-does-not-exist"], "")
        self.assertEqual(3, process.returncode)
        output = json.loads(process.stdout)
        self.assertEqual("unknown_operation", output["errors"][0]["code"])

    def test_refuses_zero_or_multiple_arguments(self):
        for argv in ([], ["concorde-context-solve", "concorde-init"]):
            with self.subTest(argv=argv):
                process = _run(argv, "")
                self.assertEqual(3, process.returncode)
                output = json.loads(process.stdout)
                self.assertEqual("unknown_operation", output["errors"][0]["code"])

    def test_runtime_check_reports_langgraph_and_python_identity_for_each_skill(self):
        for name in PUBLIC_SKILLS:
            with self.subTest(skill=name):
                process = _run([name, "--runtime-check"])
                self.assertEqual(
                    0, process.returncode, process.stderr or process.stdout
                )
                payload = json.loads(process.stdout)
                self.assertEqual(payload["operation"], name)
                self.assertEqual(payload["status"], "ok")
                self.assertTrue(payload["langgraph"])
                self.assertTrue(payload["python_version"])

    def test_runtime_check_refuses_a_nonpublic_operation_and_extra_arguments(self):
        for argv in (
            ["concorde-planner", "--runtime-check"],
            ["concorde-context-solve", "--runtime-check", "extra"],
        ):
            with self.subTest(argv=argv):
                process = _run(argv)
                self.assertEqual(3, process.returncode)
                output = json.loads(process.stdout)
                self.assertEqual("unknown_operation", output["errors"][0]["code"])

    def test_accepted_skill_actually_reaches_the_dispatcher(self):
        invocation = {
            "type_id": "concorde-operation-invocation",
            "schema_version": 3,
            "operation_id": "concorde-context-solve",
            "mode": "describe-policy",
            "configuration": None,
            "input": {
                "type_id": "concorde-context-solve-request",
                "schema_version": 1,
                "data": {"target_id": "module.harness", "task": "Explain transfer"},
            },
        }
        process = _run(["concorde-context-solve"], json.dumps(invocation))
        output = json.loads(process.stdout)
        self.assertEqual("concorde-context-solve", output["operation_id"])
        self.assertIn(output["status"], {"described", "blocked", "failed"})
        # A well-formed describe-policy request against the real project must at least be
        # admitted and dispatched, not refused as an unknown or mismatched operation.
        for error in output["errors"]:
            self.assertNotIn(
                error["code"], {"unknown_operation", "incompatible_handoff"}
            )

    @verifies("scenario.harness.typed-reject")
    def test_invalid_payload_retains_the_admitted_mode_without_execution(self):
        for mode in ("execute", "describe-policy"):
            with self.subTest(mode=mode):
                value = {
                    "type_id": "concorde-operation-invocation",
                    "schema_version": 3,
                    "operation_id": "concorde-context-solve",
                    "mode": mode,
                    "configuration": None,
                    "input": {
                        "type_id": "concorde-context-solve-request",
                        "schema_version": 1,
                        "data": {
                            "target_id": "module.harness",
                            "task": "Assess",
                            "unknown": True,
                        },
                    },
                }
                process = _run(["concorde-context-solve"], json.dumps(value))
                result = json.loads(process.stdout)
                self.assertEqual(3, process.returncode)
                self.assertEqual(mode, result["mode"])
                self.assertEqual("blocked", result["status"])
                self.assertEqual("invalid_field", result["errors"][0]["code"])
                self.assertIsNone(result["output"])
                self.assertIsNone(result["workspace"])

    @verifies("scenario.review.standalone", "scenario.harness.describe-policy")
    def test_public_review_launcher_previews_scoped_code_authority(self):
        invocation = {
            "type_id": "concorde-operation-invocation",
            "schema_version": 3,
            "operation_id": "concorde-code-review",
            "mode": "describe-policy",
            "configuration": None,
            "input": {
                "type_id": "concorde-code-review-request",
                "schema_version": 2,
                "data": {
                    "task": "Review the operation dispatch",
                    "target_id": "module.operations",
                },
            },
        }
        process = _run(
            ["--native-context", "prepare"],
            json.dumps({"invocation": invocation, "session_id": "policy-preview"}),
        )
        self.assertEqual(0, process.returncode, process.stdout + process.stderr)
        value = json.loads(process.stdout)
        self.assertEqual("described", value["state"])
        self.assertNotIn("call", value)
        self.assertIn("module.operations", value["scope"])
        self.assertEqual(
            "concorde-code-review-response", value["result"]["output"]["type_id"]
        )


if __name__ == "__main__":
    unittest.main()
