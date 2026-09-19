"""SIGTERM ends a running launcher the way Ctrl-C does: with a cancelled result envelope."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.harness import admission, operation_graph  # noqa: E402
from concorde.harness.host import OperationHost  # noqa: E402
from concorde.spec.verification import verifies  # noqa: E402

LAUNCHER = REPOSITORY_ROOT / "scripts/run-operation.py"


def _cpu_ticks(pid: int) -> int:
    fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    return int(fields[11]) + int(fields[12])


def _wait_until_idle(process: subprocess.Popen, timeout: float = 60) -> None:
    """Wait until the launcher stops consuming CPU, which means it blocks on its stdin."""
    deadline = time.monotonic() + timeout
    previous = _cpu_ticks(process.pid)
    while time.monotonic() < deadline:
        time.sleep(0.4)
        if process.poll() is not None:
            return
        current = _cpu_ticks(process.pid)
        if current == previous and current > 0:
            return
        previous = current
    raise AssertionError("the launcher never settled")


@unittest.skipUnless(sys.platform.startswith("linux"), "reads /proc to wait for the launcher")
class LauncherTerminationTests(unittest.TestCase):
    @verifies("scenario.distribution.launcher-terminated")
    def test_sigterm_while_waiting_for_the_invocation_prints_a_cancelled_envelope(self):
        process = subprocess.Popen(
            [sys.executable, str(LAUNCHER), "concorde-validate"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=REPOSITORY_ROOT,
            text=True,
            env={**os.environ, "CONCORDE_STUDIO_URL": ""},
        )
        try:
            _wait_until_idle(process)
            os.kill(process.pid, signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=30)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()
        self.assertEqual(3, process.returncode, stderr)
        result = json.loads(stdout)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("execution_cancelled", result["errors"][0]["code"], result)
        self.assertEqual("concorde-validate", result["operation_id"])

    @verifies("scenario.distribution.launcher-terminated")
    def test_an_interrupt_inside_the_graph_ends_it_with_the_cancelled_error(self):
        class Interrupted:
            def invoke(self, *_args, **_kwargs):
                raise KeyboardInterrupt

        host = OperationHost(
            REPOSITORY_ROOT, REPOSITORY_ROOT, mode="describe-policy"
        )
        runtime_input = {
            "type_id": "concorde-validate-request",
            "schema_version": 1,
            "data": {"target_id": "module.distribution", "task": "check"},
        }
        with mock.patch.object(
            operation_graph, "build_operation_graph", lambda *a, **k: Interrupted()
        ):
            result = admission.run_operation(
                "concorde-validate", None, runtime_input, host_context=host
            )
        self.assertEqual("failed", result["status"], result)
        self.assertEqual("execution_cancelled", result["errors"][0]["code"], result)
        self.assertEqual("operation cancelled by the host", result["errors"][0]["message"])


if __name__ == "__main__":
    unittest.main()
