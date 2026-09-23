"""The tester's `test_command` tool and the maintenance worker's tool guard, driven outside Pi.

The tester extension is loaded from a disposable built candidate with a saved selection, so the
tool starts that candidate's own bridge (``concorde.distribution.tester_check``) with its own
interpreter; commands really run in Check execution's read-only boundary.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from concorde.spec.verification import verifies
from tests.concorde.distribution.test_session_tool import HarnessCase
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.pi_session_project import set_up_selected_project

TESTER = "pi/extensions/concorde-tester.ts"
MAINTENANCE = REPOSITORY_ROOT / "pi/extensions/concorde-maintenance.ts"
BRIDGE = "concorde.distribution.tester_check"


class TesterCommandTests(HarnessCase):
    def setUp(self) -> None:
        super().setUp()
        set_up_selected_project(self)
        (self.project / "pi/node_modules").symlink_to(
            REPOSITORY_ROOT / "pi/node_modules", target_is_directory=True
        )
        self.governing = self.root / "governing"
        self.governing.mkdir()

    def command(self, *steps: dict) -> list[dict]:
        outcome = self.harness(
            self.project / TESTER,
            self.governing,
            [
                {"tool": "test_command", "cwd": str(self.governing), **step}
                for step in steps
            ],
            CONCORDE_SESSION_SELECTION=str(self.selection_path),
        )
        self.assertIsNone(outcome["load_error"])
        return outcome["steps"]

    def bridges(self, spawned: list[list[str]]) -> list[list[str]]:
        return [argv for argv in spawned if BRIDGE in argv]

    @verifies("scenario.session.tester-command")
    def test_a_passing_command_runs_read_only_with_fresh_scratch_and_exports_reports(
        self,
    ):
        script = (
            'printf \'{"ok": true}\' > "$CONCORDE_CHECK_REPORT_DIR/summary.json"; '
            'echo "scratch=$CONCORDE_CHECK_TMPDIR"; '
            'touch "$CONCORDE_CHECK_TMPDIR/probe" && echo SCRATCH-WRITABLE; '
            'if touch "$PWD/canary" 2>/dev/null; then echo GOVERNING-WRITABLE; '
            "else echo GOVERNING-READONLY; fi"
        )
        [step] = self.command(
            {"call": {"command": script, "reports": ["summary.json"], "timeout": 60}}
        )
        self.assertTrue(step["ok"], step)
        # The candidate's own bridge with its own interpreter, once.
        [bridge] = self.bridges(step["spawned"])
        self.assertEqual(str(self.project / ".venv/bin/python"), bridge[0])
        response = step["details"]
        self.assertEqual(response, json.loads(step["text"]))
        self.assertEqual(0, response["returncode"])
        self.assertFalse(response["timed_out"])
        self.assertFalse(response["cancelled"])
        self.assertIsNone(response["error"])
        stdout = response["stdout"]
        self.assertIn("SCRATCH-WRITABLE", stdout)
        self.assertIn("GOVERNING-READONLY", stdout)
        self.assertFalse((self.governing / "canary").exists())
        scratch = Path(stdout.split("scratch=", 1)[1].split()[0])
        self.assertFalse(scratch.exists(), "the command scratch is removed afterwards")
        self.assertEqual(len(stdout.encode()), response["stdout_bytes"])
        self.assertFalse(response["stdout_truncated"])
        self.assertIn("stderr", response)
        self.assertIn("stderr_bytes", response)
        evidence = response["evidence"]
        self.assertTrue(evidence["complete"], evidence)
        manifest = json.loads(Path(evidence["manifest"]["path"]).read_text())
        self.assertEqual(["summary.json"], manifest["reports_requested"])
        exported = {record["name"]: record for record in manifest["artifacts"]}
        self.assertIn("reports/summary.json", exported)
        self.assertEqual(
            b'{"ok": true}',
            Path(exported["reports/summary.json"]["artifact"]["path"]).read_bytes(),
        )
        self.assertEqual(
            json.loads(self.selection_path.read_text())["build_digest"],
            manifest["selection"]["build_digest"],
        )

    @verifies("scenario.session.tester-command-failed")
    def test_failed_timed_out_cancelled_or_unexported_commands_fail_the_call(self):
        steps = self.command(
            {"call": {"command": "echo failing; exit 3", "timeout": 60}},
            {"call": {"command": "sleep 30", "timeout": 1}},
            {"call": {"command": "sleep 30", "timeout": 60}, "abort_after_ms": 3000},
            {"call": {"command": "true", "timeout": 60, "reports": ["absent.json"]}},
        )
        for name, step in zip(
            ("non-zero", "timeout", "cancelled", "unexported"), steps
        ):
            with self.subTest(case=name):
                self.assertFalse(step["ok"], step)
                # The whole bridge response is the error, not a summary of it.
                response = json.loads(step["error"])
                for key in (
                    "returncode",
                    "timed_out",
                    "cancelled",
                    "error",
                    "evidence",
                    "stdout",
                    "stdout_bytes",
                    "stderr",
                ):
                    self.assertIn(key, response)
        nonzero, timeout, cancelled, unexported = (
            json.loads(step["error"]) for step in steps
        )
        self.assertEqual(3, nonzero["returncode"])
        self.assertIn("failing", nonzero["stdout"])
        self.assertTrue(timeout["timed_out"])
        self.assertTrue(cancelled["cancellation_requested"])
        self.assertEqual(0, unexported["returncode"])
        self.assertFalse(unexported["evidence"]["complete"])

    @verifies("scenario.session.tester-selection-changed")
    def test_a_changed_or_stale_selection_runs_no_command(self):
        other = self.project / ".concorde/work/other-selection.json"
        shutil.copyfile(self.selection_path, other)
        command = {"command": "echo RAN", "timeout": 60}
        [changed] = self.command(
            {"env": {"CONCORDE_SESSION_SELECTION": str(other)}, "call": command}
        )
        self.assertFalse(changed["ok"], changed)
        self.assertIn("Tester selection changed", changed["error"])
        self.assertEqual([], changed["spawned"])
        [stale] = self.command(
            {
                "append": str(self.project / "src/concorde/harness/entry.py"),
                "text": "\n# changed after the tester was launched\n",
                "call": command,
            }
        )
        self.assertFalse(stale["ok"], stale)
        # The bridge refused the selection before announcing readiness or running anything.
        self.assertIn("Tester bridge exited", stale["error"])
        self.assertNotIn("tester_check_ready", stale["error"])
        self.assertNotIn("RAN", stale["error"])
        self.assertFalse((self.governing / ".concorde/runs").exists())


class MaintenanceGuardTests(HarnessCase):
    def guard(self, cwd: Path, tools: tuple[str, ...]) -> dict[str, bool]:
        outcome = self.harness(
            MAINTENANCE,
            cwd,
            [
                {
                    "emit": "tool_call",
                    "cwd": str(cwd),
                    "event": {"toolName": tool, "toolCallId": tool, "input": {}},
                }
                for tool in tools
            ],
        )
        self.assertIsNone(outcome["load_error"])
        return {
            tool: any(result and result.get("block") for result in step["results"])
            for tool, step in zip(tools, outcome["steps"])
        }

    @verifies("scenario.session.maintenance-guard")
    def test_delegation_and_capabilities_are_blocked_in_the_source_checkout(self):
        self.assertEqual(
            {
                "subagent": True,
                "concorde": True,
                "read": False,
                "bash": False,
                "edit": False,
            },
            self.guard(
                REPOSITORY_ROOT, ("subagent", "concorde", "read", "bash", "edit")
            ),
        )

    @verifies("scenario.session.maintenance-outside-source")
    def test_every_tool_is_blocked_outside_a_concorde_source_checkout(self):
        tools = ("read", "grep", "bash", "write", "subagent")
        with tempfile.TemporaryDirectory() as directory:
            other = Path(directory)
            self.assertEqual(dict.fromkeys(tools, True), self.guard(other, tools))
            # A project that only looks like Concorde from one marker is still refused.
            (other / "concorde.json").write_text("{}")
            self.assertEqual(dict.fromkeys(tools, True), self.guard(other, tools))
