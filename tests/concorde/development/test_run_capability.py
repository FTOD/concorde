"""The executable boundary: scripts/run-capability.py (proposal section 6.3, Stage B1 item 3)."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest

from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT

LAUNCHER = REPOSITORY_ROOT / "scripts/run-capability.py"

PUBLIC_SKILLS = (
    "concorde-main",
    "concorde-dev-loop",
    "concorde-reflections-triage",
    "concorde-review",
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


class RunCapabilityLauncherTests(unittest.TestCase):
    def test_accepts_each_public_skill_name(self):
        for name in PUBLIC_SKILLS:
            with self.subTest(skill=name):
                invocation = {
                    "type_id": "concorde-capability-invocation", "schema_version": 3,
                    "capability_id": name, "mode": "describe-policy", "configuration": None,
                    "input": {"type_id": f"{name}-request", "schema_version": 1,
                              "data": {"task": "Explain transfer"}},
                }
                process = _run([name], json.dumps(invocation))
                # Some of these payloads are still rejected as invalid input for that specific
                # skill's own required fields; what this test proves is that the launcher itself
                # routed the name through to the real dispatcher rather than refusing it.
                output = json.loads(process.stdout)
                self.assertNotEqual(
                    "unknown_capability",
                    (output.get("errors") or [{}])[0].get("code"),
                    process.stdout,
                )

    @verifies("scenario.development.execute-unregistered")
    def test_refuses_a_stage_capability_name(self):
        process = _run(["concorde-plan"], "")
        self.assertEqual(3, process.returncode)
        output = json.loads(process.stdout)
        self.assertEqual("blocked", output["status"])
        self.assertEqual("unknown_capability", output["errors"][0]["code"])

    @verifies("scenario.development.execute-unregistered")
    def test_refuses_a_bare_capability_word(self):
        process = _run(["plan"], "")
        self.assertEqual(3, process.returncode)
        output = json.loads(process.stdout)
        self.assertEqual("unknown_capability", output["errors"][0]["code"])

    @verifies("scenario.development.execute-unregistered")
    def test_refuses_an_unknown_name(self):
        process = _run(["concorde-does-not-exist"], "")
        self.assertEqual(3, process.returncode)
        output = json.loads(process.stdout)
        self.assertEqual("unknown_capability", output["errors"][0]["code"])

    def test_refuses_zero_or_multiple_arguments(self):
        for argv in ([], ["concorde-main", "concorde-init"]):
            with self.subTest(argv=argv):
                process = _run(argv, "")
                self.assertEqual(3, process.returncode)
                output = json.loads(process.stdout)
                self.assertEqual("unknown_capability", output["errors"][0]["code"])

    def test_runtime_check_reports_langgraph_and_python_identity_for_each_skill(self):
        for name in PUBLIC_SKILLS:
            with self.subTest(skill=name):
                process = _run([name, "--runtime-check"])
                self.assertEqual(0, process.returncode, process.stderr or process.stdout)
                payload = json.loads(process.stdout)
                self.assertEqual(payload["capability"], name)
                self.assertEqual(payload["status"], "ok")
                self.assertTrue(payload["langgraph"])
                self.assertTrue(payload["python_version"])

    def test_runtime_check_refuses_a_stage_capability_and_extra_arguments(self):
        for argv in (["concorde-plan", "--runtime-check"], ["concorde-main", "--runtime-check", "extra"]):
            with self.subTest(argv=argv):
                process = _run(argv)
                self.assertEqual(3, process.returncode)
                output = json.loads(process.stdout)
                self.assertEqual("unknown_capability", output["errors"][0]["code"])

    def test_accepted_skill_actually_reaches_the_dispatcher(self):
        invocation = {
            "type_id": "concorde-capability-invocation", "schema_version": 3,
            "capability_id": "concorde-main", "mode": "describe-policy", "configuration": None,
            "input": {"type_id": "concorde-main-request", "schema_version": 1,
                      "data": {"task": "Explain transfer"}},
        }
        process = _run(["concorde-main"], json.dumps(invocation))
        output = json.loads(process.stdout)
        self.assertEqual("concorde-main", output["capability_id"])
        self.assertIn(output["status"], {"described", "blocked", "failed"})
        # A well-formed describe-policy request against the real project must at least be
        # admitted and dispatched, not refused as an unknown or mismatched capability.
        for error in output["errors"]:
            self.assertNotIn(error["code"], {"unknown_capability", "incompatible_handoff"})

    @verifies("scenario.development.standalone-review", "scenario.development.describe-policy")
    def test_public_review_launcher_previews_scoped_code_authority(self):
        invocation = {
            "type_id": "concorde-capability-invocation", "schema_version": 3,
            "capability_id": "concorde-review", "mode": "describe-policy", "configuration": None,
            "input": {"type_id": "concorde-review-request", "schema_version": 1,
                      "data": {"task": "Review the capability boundary", "review_mode": "code",
                               "target_id": "module.development"}},
        }
        process = _run(["concorde-review"], json.dumps(invocation))
        self.assertEqual(0, process.returncode, process.stdout + process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual("described", result["status"])
        self.assertEqual("concorde-review-response", result["output"]["type_id"])
        self.assertEqual("not_run", result["output"]["data"]["reviews"][0]["data"]["status"])


if __name__ == "__main__":
    unittest.main()
