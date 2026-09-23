"""The `concorde` tool's refusals, native preparation, workflow polling and selection guard.

The tracked session extension (or a candidate's rendered private entry) is driven outside Pi by
``session_tool_harness.mjs``, which records every process the extension starts. Capability runs
and native steps go to ``session_launcher_fixture.py``; selection tests use a disposable built
copy of this checkout with a saved selection and its real launcher.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from concorde.spec.verification import verifies
from tests.concorde.support.environment import child_environment
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.pi_session_project import set_up_selected_project

HARNESS = REPOSITORY_ROOT / "tests/concorde/distribution/session_tool_harness.mjs"
EXTENSION = REPOSITORY_ROOT / "pi/extensions/concorde-session.ts"
LAUNCHER = "tests/concorde/distribution/session_launcher_fixture.py"
ENTRY = "generated/session/pi/concorde-session.ts"
JITI = REPOSITORY_ROOT / "pi/node_modules/jiti/package.json"
PI_SUBAGENTS = REPOSITORY_ROOT / "pi/node_modules/pi-subagents/package.json"
WORKFLOW_RESULT = {
    "state": "accepted",
    "accepted": True,
    "native_state": "completed",
    "result": {"status": "succeeded", "reconciled_by": "fixture-host"},
}


def operation(name: str, kind: str, native_actions=()) -> dict:
    return {
        "name": name,
        "kind": kind,
        "native_actions": list(native_actions),
        "description": f"{name} description.",
        "guidance": f"# {name}\n",
        "request_version": 1,
        "request_schema": {"type": "object"},
    }


CATALOG = {
    "schema_version": 3,
    "launcher": LAUNCHER,
    "interpreters": [sys.executable],
    "explicit_request_only": False,
    "operations": [
        operation("concorde-validate", "host"),
        operation("concorde-context-solve", "agent-entry"),
        operation("concorde-plan", "workflow"),
        operation("concorde-issues", "host", ["solve"]),
    ],
}


def request(name: str, data: dict, mode: str = "execute") -> dict:
    return {
        "type_id": "concorde-operation-invocation",
        "schema_version": 3,
        "operation_id": name,
        "mode": mode,
        "configuration": None,
        "input": {"type_id": f"{name}-request", "schema_version": 1, "data": data},
    }


def started_launcher(spawned: list[list[str]], launcher: str) -> list[list[str]]:
    return [argv for argv in spawned if any(item.endswith(launcher) for item in argv)]


@unittest.skipUnless(shutil.which("node"), "Node is required to load the extension")
@unittest.skipUnless(JITI.is_file(), "pi/node_modules is not installed")
class HarnessCase(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="concorde-session-tool-")
        self.addCleanup(temporary.cleanup)
        self.scratch = Path(temporary.name).resolve()
        self.log = self.scratch / "launcher.jsonl"

    def harness(
        self, extension: Path, root: Path, steps: list[dict], *, catalog=None, **env
    ) -> dict:
        argv = ["node", str(HARNESS), str(extension), str(root)]
        if catalog is not None:
            path = self.scratch / "catalog.json"
            path.write_text(json.dumps(catalog), encoding="utf-8")
            argv.append(str(path))
        process = subprocess.run(
            argv,
            input=json.dumps({"steps": steps}),
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
            cwd=str(root),
            env=child_environment(
                SESSION_LAUNCHER_LOG=str(self.log),
                SESSION_LAUNCHER_DIR=str(self.scratch),
                **env,
            ),
        )
        self.assertEqual(0, process.returncode, process.stderr)
        return json.loads(process.stdout)

    def launcher_log(self) -> list[dict]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]


class ToolRunTests(HarnessCase):
    def drive(self, steps: list[dict], **env) -> list[dict]:
        outcome = self.harness(
            EXTENSION, REPOSITORY_ROOT, steps, catalog=CATALOG, **env
        )
        self.assertIsNone(outcome["load_error"])
        return outcome["steps"]

    @verifies("scenario.session.run-refused")
    def test_blocked_failed_nonzero_and_unreadable_runs_are_tool_errors(self):
        run = {
            "operation": "concorde-validate",
            "action": "run",
            "input": {"task": "check"},
        }
        for scenario, status in (
            ("blocked", "blocked"),
            ("failed-zero", "failed"),
            ("nonzero", "succeeded"),
        ):
            with self.subTest(scenario=scenario):
                [step] = self.drive([{"call": run}], SESSION_LAUNCHER_SCENARIO=scenario)
                self.assertFalse(step["ok"], step)
                shown = json.loads(step["error"])
                # The envelope the launcher printed travels with the error, never as a success.
                self.assertEqual("concorde-operation-result", shown["type_id"])
                self.assertEqual(status, shown["status"])
                self.assertEqual("concorde-validate", shown["operation_id"])
                feedback = shown["failure"]
                self.assertEqual("session-launcher", feedback["layer"])
                self.assertEqual("host-refusal", feedback["category"])
        [step] = self.drive([{"call": run}], SESSION_LAUNCHER_SCENARIO="garbage")
        self.assertFalse(step["ok"], step)
        feedback = json.loads(step["error"])
        self.assertEqual("session-launcher", feedback["layer"])
        self.assertEqual("transport", feedback["category"])
        self.assertIn(
            "launcher crashed before printing an envelope",
            feedback["diagnostics"]["text"],
        )

    @verifies("scenario.session.run-invalid")
    def test_unknown_capability_and_missing_input_start_no_launcher(self):
        steps = self.drive(
            [
                {
                    "call": {
                        "operation": "concorde-unlisted",
                        "action": "run",
                        "input": {"task": "x"},
                    }
                },
                {"call": {"operation": "concorde-validate", "action": "run"}},
                {
                    "call": {
                        "operation": "concorde-validate",
                        "action": "run",
                        "input": ["not", "an", "object"],
                    }
                },
            ]
        )
        self.assertIn("unknown Concorde Operation concorde-unlisted", steps[0]["error"])
        self.assertIn("concorde-validate", steps[0]["error"])
        for step in steps[1:]:
            self.assertIn('action "run" needs `input`', step["error"])
        for step in steps:
            self.assertFalse(step["ok"], step)
            self.assertEqual([], step["spawned"])
        self.assertEqual([], self.launcher_log())

    @verifies("scenario.session.native-prepare")
    def test_agent_entries_and_native_actions_are_prepared_not_run(self):
        for name, data in (
            ("concorde-context-solve", {"target_id": "module.x", "task": "assess"}),
            ("concorde-issues", {"action": "solve", "issue": "issue.1"}),
        ):
            with self.subTest(operation=name):
                self.log.unlink(missing_ok=True)
                [step] = self.drive(
                    [{"call": {"operation": name, "action": "run", "input": data}}]
                )
                self.assertTrue(step["ok"], step)
                # One process: the launcher's native preparation step, and no Agent.
                self.assertEqual(1, len(step["spawned"]), step["spawned"])
                self.assertEqual(
                    ["--native-context", "prepare"], step["spawned"][0][-2:]
                )
                [entry] = self.launcher_log()
                self.assertEqual(["--native-context", "prepare"], entry["argv"])
                sent = json.loads(entry["stdin"])
                self.assertEqual(request(name, data), sent["invocation"])
                details = step["details"]
                self.assertEqual("prepared", details["state"])
                self.assertIs(False, details["accepted"])
                self.assertEqual(
                    {
                        "agent": "concorde-context-assessor",
                        "task": f"prepared for {name}",
                        "context": "fresh",
                    },
                    details["call"],
                )
        # A Host capability action outside native_actions goes to the launcher as usual.
        self.log.unlink(missing_ok=True)
        [step] = self.drive(
            [
                {
                    "call": {
                        "operation": "concorde-issues",
                        "action": "run",
                        "input": {"action": "list"},
                    }
                }
            ]
        )
        self.assertTrue(step["ok"], step)
        self.assertEqual(
            [["concorde-issues"]], [e["argv"] for e in self.launcher_log()]
        )

    @unittest.skipUnless(PI_SUBAGENTS.is_file(), "pi-subagents is not installed")
    @verifies("scenario.session.native-prepare")
    def test_a_workflow_is_prepared_and_registered_without_starting_it(self):
        [step] = self.drive(
            [
                {
                    "call": {
                        "operation": "concorde-plan",
                        "action": "run",
                        "input": {"task": "plan"},
                    }
                }
            ],
            SESSION_LAUNCHER_NATIVE="workflow",
        )
        self.assertTrue(step["ok"], step)
        self.assertEqual(1, len(step["spawned"]), step["spawned"])
        [entry] = self.launcher_log()
        self.assertEqual(["--native-context", "prepare"], entry["argv"])
        self.assertEqual(
            request("concorde-plan", {"task": "plan"}),
            json.loads(entry["stdin"])["invocation"],
        )
        details = step["details"]
        self.assertEqual("prepared", details["state"])
        self.assertIs(False, details["accepted"])
        self.assertEqual("concorde-fixture-workflow", details["workflow"]["name"])
        self.assertEqual(
            {
                "workflow": "concorde-fixture-workflow",
                "args": {"ticket": "fixture-ticket"},
                "cwd": str(REPOSITORY_ROOT),
                "async": True,
                "mission": False,
                "context": "fresh",
                "intercomBridge": {"mode": "off"},
            },
            details["call"],
        )

    @unittest.skipUnless(PI_SUBAGENTS.is_file(), "pi-subagents is not installed")
    @verifies("scenario.session.result-poll")
    def test_result_returns_the_workflow_state_the_host_reconciles(self):
        call = {
            "workflow": "concorde-fixture-workflow",
            "args": {"ticket": "fixture-ticket"},
            "cwd": str(REPOSITORY_ROOT),
            "async": True,
            "mission": False,
            "context": "fresh",
            "intercomBridge": {"mode": "off"},
        }
        result = {"operation": "concorde-plan", "action": "result"}
        steps = self.drive(
            [
                {"call": result},
                {
                    "call": {
                        "operation": "concorde-plan",
                        "action": "run",
                        "input": {"task": "plan"},
                    }
                },
                {
                    "emit": "tool_call",
                    "event": {
                        "toolName": "subagent",
                        "toolCallId": "w1",
                        "input": call,
                    },
                },
                {
                    "emit": "tool_result",
                    "event": {
                        "toolName": "subagent",
                        "toolCallId": "w1",
                        "input": call,
                        "isError": False,
                        "details": {"asyncDir": str(self.scratch), "runId": "run-1"},
                    },
                },
                {"call": result},
                {"call": {"operation": "concorde-validate", "action": "result"}},
            ],
            SESSION_LAUNCHER_NATIVE="workflow",
        )
        self.assertEqual({"state": "not-run", "accepted": False}, steps[0]["details"])
        self.assertTrue(steps[4]["ok"], steps[4])
        self.assertEqual(WORKFLOW_RESULT, steps[4]["details"])
        self.assertEqual(WORKFLOW_RESULT, json.loads(steps[4]["text"]))
        polled = self.launcher_log()[-1]
        self.assertEqual("workflow-result", polled["argv"][1])
        self.assertIn("result polling is only for workflows", steps[5]["error"])


class PrivateEntrySelectionTests(HarnessCase):
    """The candidate's rendered private entry against its own saved selection."""

    def setUp(self) -> None:
        super().setUp()
        set_up_selected_project(self)
        # The candidate copy is built without node_modules; share the checkout's packages.
        (self.project / "pi/node_modules").symlink_to(
            REPOSITORY_ROOT / "pi/node_modules", target_is_directory=True
        )
        self.entry = self.project / ENTRY

    def load(self, steps=(), **env) -> dict:
        return self.harness(
            self.entry,
            self.project,
            list(steps),
            **{"CONCORDE_SESSION_SELECTION": str(self.selection_path), **env},
        )

    @verifies("scenario.session.explicit-request-only")
    def test_the_selected_source_entry_states_explicit_request_only(self):
        outcome = self.load()
        self.assertIsNone(outcome["load_error"])
        self.assertEqual(["concorde"], [tool["name"] for tool in outcome["tools"]])
        prompt = " ".join(outcome["prompt"].split())
        self.assertIn(
            "run an Operation only when the user explicitly asks for it by name",
            prompt,
        )

    @verifies("scenario.session.entry-requires-selection")
    def test_loading_without_selection_conflicting_transports_or_interpreter_fails(
        self,
    ):
        other = self.project / ".concorde/work/other-selection.json"
        cases = {
            "no transport": (
                {"CONCORDE_SESSION_SELECTION": ""},
                "requires explicit candidate selection",
            ),
            "conflicting transports": (
                {
                    "PI_SUBAGENT_EXTENSION_BINDINGS": json.dumps(
                        {"concorde/1": {"selection": str(other)}}
                    )
                },
                "Conflicting private selection transports",
            ),
        }
        for case, (env, message) in cases.items():
            with self.subTest(case=case):
                outcome = self.load(**env)
                self.assertIn(message, outcome["load_error"] or "")
                self.assertEqual([], outcome["tools"])
        (self.project / ".venv").unlink()
        outcome = self.load()
        self.assertIn(
            "requires the candidate Python environment", outcome["load_error"] or ""
        )
        self.assertEqual([], outcome["tools"])

    @verifies("scenario.session.selection-changed")
    def test_a_changed_transport_or_selected_bytes_refuse_calls_without_a_launcher(
        self,
    ):
        run = {
            "operation": "concorde-validate",
            "action": "run",
            "input": {"target_id": "module.x", "task": "check"},
        }
        other = self.project / ".concorde/work/other-selection.json"
        shutil.copyfile(self.selection_path, other)
        outcome = self.load(
            [
                {"call": {"operation": "concorde-validate", "action": "describe"}},
                {"env": {"CONCORDE_SESSION_SELECTION": str(other)}, "call": run},
            ]
        )
        self.assertIsNone(outcome["load_error"])
        described, changed = outcome["steps"]
        self.assertTrue(described["ok"], described)
        self.assertFalse(changed["ok"], changed)
        self.assertIn("start a fresh session", changed["error"])
        self.assertEqual([], changed["spawned"])
        outcome = self.load(
            [
                {
                    "append": str(self.project / "src/concorde/harness/entry.py"),
                    "text": "\n# changed after the session loaded\n",
                    "call": run,
                }
            ]
        )
        self.assertIsNone(outcome["load_error"])
        [changed] = outcome["steps"]
        self.assertFalse(changed["ok"], changed)
        self.assertIn("start a fresh session", changed["error"])
        # Only the selection check ran; the launcher never started.
        self.assertEqual(
            [], started_launcher(changed["spawned"], "scripts/run-operation.py")
        )
        self.assertTrue(
            all("select-session" in argv for argv in changed["spawned"]),
            changed["spawned"],
        )


if __name__ == "__main__":
    unittest.main()
