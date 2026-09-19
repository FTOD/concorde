"""Failed RPC runs retain private diagnostics without publishing process output."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.harness.pi_rpc import (
    PiRpcCancelled,
    PiRpcError,
    PiRpcTimeout,
    PiRun,
    run_prompt,
)
from concorde.harness.pi_worker import (
    PiWorkerRuntime,
    WorkerExecutionError,
    WorkerLaunch,
)
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT


class RpcDiagnosticsTests(unittest.TestCase):
    def run_script(self, script, timeout=5):
        return run_prompt(
            [sys.executable, "-c", script],
            cwd=str(REPOSITORY_ROOT),
            env={"PATH": os.environ.get("PATH", "")},
            message="PRIVATE PROMPT",
            timeout=timeout,
        )

    @verifies("scenario.harness.pi-rpc-client")
    def test_early_eof_keeps_exit_status_and_private_stderr(self):
        for code in (0, 23):
            with self.subTest(code=code), self.assertRaises(PiRpcError) as raised:
                self.run_script(
                    "import sys; sys.stdin.readline(); "
                    "sys.stderr.write('PRIVATE STARTUP DIAGNOSTIC'); "
                    f"sys.exit({code})"
                )
            error = raised.exception
            self.assertNotIn("PRIVATE", str(error))
            self.assertEqual(code, error.run.exit_code)
            self.assertEqual("PRIVATE STARTUP DIAGNOSTIC", error.run.stderr)
            self.assertGreater(error.run.wall_seconds, 0)

    @verifies("scenario.harness.pi-rpc-client")
    def test_rejected_response_keeps_details_private(self):
        with self.assertRaises(PiRpcError) as raised:
            self.run_script(
                "import sys, json; sys.stdin.readline(); "
                "print(json.dumps({'type':'response', 'id':'prompt', "
                "'command':'PRIVATE COMMAND', 'success':False, "
                "'error':'PRIVATE AUTH VALUE'}), flush=True)"
            )
        self.assertNotIn("PRIVATE", str(raised.exception))
        self.assertIsNotNone(raised.exception.run)
        self.assertIn("PRIVATE AUTH VALUE", str(raised.exception.run.events))

    @verifies("scenario.harness.pi-rpc-client")
    def test_invalid_record_keeps_stderr_without_exposing_raw_bytes(self):
        with self.assertRaises(PiRpcError) as raised:
            self.run_script(
                "import sys; sys.stdin.readline(); "
                "sys.stderr.write('PRIVATE DIAGNOSTIC'); "
                "sys.stdout.buffer.write(b'PRIVATE \\xff RECORD\\n'); sys.stdout.flush()"
            )
        self.assertEqual("Pi wrote a record that is not JSON", str(raised.exception))
        self.assertEqual("PRIVATE DIAGNOSTIC", raised.exception.run.stderr)

    @verifies("scenario.harness.pi-rpc-client")
    def test_interrupt_and_io_failure_retain_finished_run(self):
        for problem, expected in (
            (KeyboardInterrupt(), PiRpcCancelled),
            (OSError("PRIVATE IO DETAIL"), PiRpcError),
        ):
            with (
                self.subTest(expected=expected),
                patch("concorde.harness.pi_rpc.json.dumps", side_effect=problem),
                self.assertRaises(expected) as raised,
            ):
                self.run_script("import time; time.sleep(10)")
            self.assertIsNotNone(raised.exception.run.exit_code)
            self.assertNotIn("PRIVATE", str(raised.exception))

    @verifies("scenario.harness.pi-rpc-client")
    def test_timeout_retains_bounded_stderr_and_outcome(self):
        with self.assertRaises(PiRpcTimeout) as raised:
            self.run_script(
                "import sys, time; sys.stdin.readline(); "
                "sys.stderr.write('x' * 100000 + 'TAIL'); sys.stderr.flush(); time.sleep(10)",
                timeout=0.5,
            )
        run = raised.exception.run
        self.assertIsNotNone(run.exit_code)
        self.assertLessEqual(len(run.stderr.encode()), 20000)
        self.assertTrue(run.stderr.endswith("TAIL"))
        self.assertNotIn("TAIL", str(raised.exception))

    @verifies("scenario.harness.pi-worker-launch")
    def test_runtime_preserves_failed_run_and_failure_class(self):
        with tempfile.TemporaryDirectory() as temporary:
            launch = WorkerLaunch(
                worker="test",
                workspace=temporary,
                system_prompt="PRIVATE SYSTEM PROMPT",
                message="PRIVATE TASK",
                result_schema={"type": "object"},
                tools=("submit_result",),
            )
            run = PiRun(stderr="PRIVATE STDERR", exit_code=23)
            for error_type, outcome in (
                (PiRpcError, "failed"),
                (PiRpcTimeout, "limit_exhausted"),
                (PiRpcCancelled, "cancelled"),
            ):
                error = error_type("safe failure")
                error.run = run
                with (
                    self.subTest(outcome=outcome),
                    patch(
                        "concorde.harness.pi_worker.unavailable_reason",
                        return_value=None,
                    ),
                    patch("concorde.harness.pi_worker.plan_mounts") as mounts,
                    patch(
                        "concorde.harness.pi_worker.create_placeholders",
                        return_value=(),
                    ),
                    patch(
                        "concorde.harness.pi_worker.bubblewrap_argv", return_value=[]
                    ),
                    patch("concorde.harness.pi_worker.run_prompt", side_effect=error),
                    self.assertRaises(WorkerExecutionError) as raised,
                ):
                    PiWorkerRuntime(
                        REPOSITORY_ROOT,
                        pi_executable="unused",
                        credentials_dir=Path(temporary) / "absent",
                    )(launch)
                self.assertEqual(
                    (REPOSITORY_ROOT / "pi/extensions/concorde-worker.ts",),
                    mounts.call_args.kwargs["runtime_files"],
                )
                self.assertEqual(
                    (REPOSITORY_ROOT / "pi/node_modules/typebox",),
                    mounts.call_args.kwargs["runtime_directories"],
                )
                self.assertEqual(outcome, raised.exception.outcome)
                self.assertIs(run, raised.exception.run)
                self.assertNotIn("PRIVATE", str(raised.exception))
