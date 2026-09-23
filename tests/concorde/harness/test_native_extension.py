"""The native call extension, workflow registrar and Host-step transport, driven by a Node probe.

The probe loads the real ``pi/`` plumbing with a scripted Host command and a stand-in pi-subagents
package; no Pi process, pi-subagents run or model call happens.
"""

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
class NativeExtensionTests(unittest.TestCase):
    def probe(self, section: str) -> dict:
        result = subprocess.run(
            [
                "node",
                str(Path(__file__).with_name("native_extension_probe.mjs")),
                str(REPOSITORY_ROOT),
                section,
            ],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr[-6000:])
        value = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(0, value.pop("models"))
        return value

    @verifies(
        "scenario.execution.foreign-call",
        "scenario.execution.cancelled-call",
        "scenario.execution.failed-run",
        "scenario.execution.stale-call",
    )
    def test_the_call_extension_launches_only_the_prepared_call_once(self):
        self.assertEqual(
            {"foreignCall": True, "cancelledCall": True}, self.probe("call")
        )

    @verifies(
        "scenario.execution.workflow-register",
        "scenario.execution.workflow-foreign-call",
        "scenario.execution.workflow-launch-failure",
        "scenario.execution.workflow-running",
        "scenario.execution.workflow-accepted",
        "scenario.execution.workflow-stop",
    )
    def test_the_registrar_runs_only_the_prepared_workflow(self):
        self.assertEqual(
            {
                "workflowRegister": True,
                "workflowForeignCall": True,
                "workflowRunning": True,
                "workflowAccepted": True,
                "workflowLaunchFailure": True,
                "workflowReplacementRefused": True,
                "workflowStop": True,
            },
            self.probe("workflow"),
        )

    @verifies("scenario.execution.host-step-failure")
    def test_a_failing_host_step_is_never_a_result(self):
        self.assertEqual({"hostStepFailure": True}, self.probe("transport"))


if __name__ == "__main__":
    unittest.main()
