from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.concorde.support.environment import child_environment
from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))
from concorde.distribution.build import build, check_build, write_build, BuildError
from concorde.distribution import installation
from concorde.spec.verification import verifies


class TaskSubagentsTests(unittest.TestCase):
    @verifies("scenario.distribution.task-subagents")
    def test_projection_membership_and_installed_prompt_separation(self):
        source = {o.path: o for o in build(REPOSITORY_ROOT).outputs}
        installed = {
            o.path: o
            for o in build(
                REPOSITORY_ROOT, framework_prefix=".concorde/framework"
            ).outputs
        }
        self.assertIn(".pi/agents/maintenance-worker.md", source)
        self.assertIn(".pi/extensions/concorde-coordinator.ts", source)
        self.assertIn(".pi/extensions/concorde-brief-lifecycle.ts", source)
        self.assertNotIn(".pi/extensions/concorde-brief-lifecycle.ts", installed)
        self.assertIn(
            "userSessionLifecycle as default",
            source[".pi/extensions/concorde-brief-lifecycle.ts"].content.decode(),
        )
        self.assertNotIn(
            "userSessionLifecycle",
            source[".pi/agents/maintenance-worker.md"].content.decode(),
        )
        self.assertIn(
            "concorde-brief-lifecycle.ts",
            source[".pi/agents/maintenance-worker.md"].content.decode(),
        )
        self.assertNotIn(
            "concorde-brief-lifecycle", source[".pi/agents/tester.md"].content.decode()
        )
        self.assertNotIn(".pi/extensions/concorde-session.ts", source)
        self.assertIn(".pi/agents/tester.md", installed)
        self.assertNotIn(".pi/agents/maintenance-worker.md", installed)
        self.assertNotIn(".pi/extensions/concorde-coordinator.ts", installed)
        self.assertNotIn(
            "Source maintenance worker",
            installed[".pi/agents/tester.md"].content.decode(),
        )
        package = installation.Package(
            REPOSITORY_ROOT, json.loads((REPOSITORY_ROOT / "concorde.json").read_text())
        )
        outputs = installation.desired_outputs(package)
        self.assertIn(".pi/agents/tester.md", outputs)
        self.assertFalse(
            any(
                "prompts/task-subagent/source/" in p
                or "prompts/user-session/" in p
                or p.endswith(
                    ("concorde-maintenance.ts", "concorde-brief-lifecycle.ts")
                )
                for p in outputs
            )
        )
        self.assertIn(".concorde/framework/pi/extensions/concorde-observe.ts", outputs)
        self.assertIn(".concorde/framework/pi/extensions/concorde-tester.ts", outputs)
        self.assertIn(
            ".concorde/framework/src/concorde/distribution/tester_check.py", outputs
        )

    @verifies("scenario.distribution.task-subagents")
    def test_missing_source_and_modified_projection_fail_closed(self):
        from concorde.distribution.task_subagents import render
        from tests.concorde.support.build_fixture import build_package_copy

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "concorde.json").write_text("{}")
            with self.assertRaises(BuildError):
                render(root)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            build_package_copy(root)
            path = root / ".pi/agents/tester.md"
            path.write_text("local edit")
            self.assertFalse(check_build(root)[0])
            with self.assertRaisesRegex(BuildError, "unowned or modified"):
                write_build(root)
            self.assertEqual(path.read_text(), "local edit")

    @verifies("scenario.distribution.task-subagents")
    def test_installer_collision_is_not_adopted(self):
        package = installation.Package(
            REPOSITORY_ROOT, json.loads((REPOSITORY_ROOT / "concorde.json").read_text())
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / ".pi/agents/tester.md"
            path.parent.mkdir(parents=True)
            path.write_text("user-owned tester")
            actions, _, _ = installation.installation_plan(root, package)
            action = next(a for a in actions if a["path"] == ".pi/agents/tester.md")
            self.assertEqual(action["action"], "conflict")
            self.assertEqual(path.read_text(), "user-owned tester")

    @verifies(
        "scenario.distribution.task-subagents", "scenario.agents.tester-independent"
    )
    def test_actual_project_discovery_and_effective_tools(self):
        subagents = Path(
            os.environ.get(
                "CONCORDE_TEST_SUBAGENTS_ROOT",
                Path.home() / ".pi/agent/npm/node_modules/pi-subagents",
            )
        )
        pi = shutil.which("pi")
        if not subagents.is_dir() or not pi:
            self.skipTest(
                "pi-subagents and Pi in the user session are host prerequisites"
            )
        # Official npm layout, no dependency or settings mutation.
        pi_root = next(
            p
            for p in Path(pi).resolve().parents
            if (p / "package.json").is_file()
            and json.loads((p / "package.json").read_text()).get("name")
            == "@earendil-works/pi-coding-agent"
        )
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    "node",
                    str(
                        REPOSITORY_ROOT
                        / "tests/concorde/support/task_subagents_preflight.mjs"
                    ),
                    str(subagents),
                    str(pi_root),
                    str(REPOSITORY_ROOT),
                ],
                env=child_environment(PI_CODING_AGENT_DIR=directory, TMPDIR=directory),
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            for name, value in zip(
                ("maintenance-worker", "tester"), json.loads(result.stdout)
            ):
                self.assertTrue(value["ok"], value)
                contract = value["contract"]
                self.assertEqual(contract["agent"]["source"], "project")
                self.assertEqual(contract["agent"]["name"], name)
                self.assertEqual(
                    contract["agent"]["filePath"],
                    str(REPOSITORY_ROOT / f".pi/agents/{name}.md"),
                )
                self.assertEqual(contract["context"], "fresh")
                self.assertFalse(contract["inheritSkills"])
                self.assertFalse(contract["inheritProjectContext"])
                tools = contract["tools"]
                self.assertFalse(tools["fanoutAuthorized"])
                self.assertTrue(tools["disableAmbientExtensions"])
                self.assertNotIn("subagent", tools["effectiveAllowlist"])
                if name == "tester":
                    self.assertTrue(
                        {"write", "edit", "bash"}.isdisjoint(
                            tools["effectiveAllowlist"]
                        )
                    )
                    self.assertIn("test_command", tools["effectiveAllowlist"])
            consumer = Path(directory) / "consumer"
            package = installation.Package(
                REPOSITORY_ROOT,
                json.loads((REPOSITORY_ROOT / "concorde.json").read_text()),
            )
            for relative, (content, _role) in installation.desired_outputs(
                package
            ).items():
                destination = consumer / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
            installed = subprocess.run(
                [
                    "node",
                    str(
                        REPOSITORY_ROOT
                        / "tests/concorde/support/task_subagents_preflight.mjs"
                    ),
                    str(subagents),
                    str(pi_root),
                    str(consumer),
                ],
                env=child_environment(PI_CODING_AGENT_DIR=directory, TMPDIR=directory),
                capture_output=True,
                text=True,
            )
            self.assertEqual(installed.returncode, 0, installed.stderr)
            absent, tester = json.loads(installed.stdout)
            self.assertFalse(absent["ok"])
            self.assertEqual(absent["code"], "missing_agent")
            self.assertTrue(tester["ok"], tester)
            self.assertEqual(
                tester["contract"]["agent"]["filePath"],
                str(consumer / ".pi/agents/tester.md"),
            )
            self.assertTrue(
                all(
                    str(consumer) in p
                    for p in tester["contract"]["tools"]["configuredExtensions"]
                )
            )

    @verifies(
        "scenario.harness.session-observation",
        "scenario.distribution.task-subagents",
        "scenario.agents.tester-independent",
    )
    def test_native_hook_observation_and_readonly_commands(self):
        if not shutil.which("node"):
            self.skipTest("Node is required for Pi extensions")
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    "node",
                    "--experimental-strip-types",
                    str(
                        REPOSITORY_ROOT
                        / "tests/concorde/support/session_observer_harness.mts"
                    ),
                    str(REPOSITORY_ROOT),
                    directory,
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["readonly"])
            self.assertFalse((Path(directory) / "governing-canary").exists())

    @verifies(
        "scenario.harness.brief-lifecycle", "scenario.distribution.task-subagents"
    )
    def test_actual_sdk_compaction_and_current_brief(self):
        from tests.concorde.support.fake_openai_provider import FakeOpenAIProvider

        pi = shutil.which("pi")
        if not pi:
            self.skipTest("Pi SDK is a host prerequisite")
        sdk = next(
            p
            for p in Path(pi).resolve().parents
            if (p / "package.json").is_file()
            and json.loads((p / "package.json").read_text()).get("name")
            == "@earendil-works/pi-coding-agent"
        )
        with (
            tempfile.TemporaryDirectory() as scratch,
            FakeOpenAIProvider([{"text": "fixture complete"}] * 2) as provider,
        ):
            result = subprocess.run(
                [
                    "node",
                    str(
                        REPOSITORY_ROOT
                        / "tests/concorde/distribution/brief_lifecycle_fixture.mjs"
                    ),
                    str(sdk),
                    str(REPOSITORY_ROOT),
                    scratch,
                    provider.base_url,
                ],
                env=child_environment(
                    PI_CODING_AGENT_DIR=scratch, PI_OFFLINE="1", PI_TELEMETRY="0"
                ),
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(len(provider.requests), 2)
            for request in provider.requests:
                serialized = json.dumps(request)
                self.assertEqual(serialized.count("CURRENT-GOAL"), 1)
                self.assertNotIn("OBSOLETE-GOAL", serialized)
            print(result.stdout)

    @verifies(
        "scenario.harness.brief-lifecycle", "scenario.distribution.task-subagents"
    )
    def test_source_main_sdk_brief_tool_and_latest_compacted_memory(self):
        pi = shutil.which("pi")
        if not pi:
            self.skipTest("Pi SDK is a host prerequisite")
        sdk = next(
            p
            for p in Path(pi).resolve().parents
            if (p / "package.json").is_file()
            and json.loads((p / "package.json").read_text()).get("name")
            == "@earendil-works/pi-coding-agent"
        )
        with tempfile.TemporaryDirectory() as scratch:
            result = subprocess.run(
                [
                    "node",
                    str(
                        REPOSITORY_ROOT
                        / "tests/concorde/distribution/user_session_brief_fixture.mjs"
                    ),
                    str(sdk),
                    str(REPOSITORY_ROOT),
                    scratch,
                ],
                capture_output=True,
                text=True,
                timeout=45,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            print(result.stdout)

    @verifies("scenario.distribution.test-timing")
    def test_runner_fingerprints_and_default_cli(self):
        from tests.concorde.support import pytest_timing as runner

        selected = ["tests/concorde/harness/test_timing.py::TimingTests::test_x"]
        first = runner.fingerprint(selected)
        self.assertEqual(first, runner.fingerprint(selected))
        self.assertNotEqual(first["digest"], runner.fingerprint(["other"])["digest"])
        read_bytes = Path.read_bytes
        role = REPOSITORY_ROOT / "agents/planner/spec.md"

        def changed_role(path):
            content = read_bytes(path)
            return content + b"\nchanged role\n" if path == role else content

        with patch.object(Path, "read_bytes", changed_role):
            changed = runner.fingerprint(selected)
        self.assertNotEqual(first["input"], changed["input"])
        with tempfile.TemporaryDirectory() as directory:
            command = [
                sys.executable,
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "-n",
                "2",
                "tests/concorde/harness/test_timing.py",
                "tests/concorde/harness/test_rpc_diagnostics.py",
            ]
            report = Path(directory) / "report.json"
            # A caller may pass no reason, scope, phase or attempt.
            result = subprocess.run(
                [*command, f"--json={report}"],
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            value = json.loads(report.read_text())
            self.assertEqual(value["reason"], "manual")
            self.assertEqual(value["scope"], "unspecified")
            self.assertEqual(value["phase"], "unspecified")
            self.assertEqual(value["attempt"], 1)
            self.assertIsNone(value["prior_run_id"])
            self.assertIsNone(value["same_declared_inputs"])
            self.assertTrue(all(s["layer"] == "C" for s in value["spans"]))
            self.assertEqual(
                {"test.total", "test.discovery", "test.unit"},
                {s["name"] for s in value["spans"]},
            )
            self.assertEqual(value["totals"]["tests"], value["totals"]["collected"])
            self.assertEqual(value["totals"]["failed"] + value["totals"]["error"], 0)
            self.assertEqual(value["totals"]["workers"], 2)
            self.assertGreaterEqual(value["discovery_seconds"], 0)
            self.assertGreaterEqual(
                value["elapsed_seconds"], value["discovery_seconds"]
            )
            self.assertIn("not elapsed wall time", value["timing_note"])
            units = {unit["nodeid"]: unit for unit in value["units"]}
            self.assertEqual(len(units), value["totals"]["tests"])
            # Elapsed is the controller's own interval; unit seconds are summed concurrent work.
            self.assertGreaterEqual(
                value["elapsed_seconds"],
                max(unit["execution_seconds"] for unit in units.values()),
            )
            self.assertAlmostEqual(
                value["totals"]["unit_seconds"],
                sum(unit["execution_seconds"] for unit in units.values()),
                places=1,
            )
            for unit in units.values():
                self.assertIsNone(unit["setup_seconds"])
                self.assertGreaterEqual(unit["queue_seconds"], 0)
                self.assertGreaterEqual(unit["execution_seconds"], 0)
                self.assertEqual(
                    {"setup", "call", "teardown"}, set(unit["phase_seconds"])
                )
            rpc = units[
                "tests/concorde/harness/test_rpc_diagnostics.py::RpcDiagnosticsTests::"
                "test_rejected_response_keeps_details_private"
            ]
            self.assertTrue(rpc["telemetry_complete"])
            self.assertEqual(
                {"pi.rpc_total", "pi.process_start", "pi.rpc_accept"},
                {span["name"] for span in rpc["runtime_spans"]},
            )
            self.assertTrue(all(s["layer"] == "B" for s in rpc["runtime_spans"]))
            self.assertEqual(
                {rpc["process_id"]}, {s["process_id"] for s in rpc["runtime_spans"]}
            )
            self.assertIn(rpc["worker"], {"gw0", "gw1"})
            # An explicitly scoped rerun recognizes unchanged declared inputs.
            # Values are joined with "=": an existing prior path as a separate argument would
            # be taken for a test path while pytest decides its rootdir.
            again = Path(directory) / "again.json"
            result = subprocess.run(
                [
                    *command,
                    f"--json={again}",
                    f"--prior={report}",
                    "--reason=failure",
                    "--scope=targeted",
                    "--phase=maintenance",
                    "--attempt=2",
                ],
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            second = json.loads(again.read_text())
            self.assertEqual(second["prior_run_id"], value["run_id"])
            self.assertEqual(
                (second["reason"], second["scope"], second["phase"], second["attempt"]),
                ("failure", "targeted", "maintenance", 2),
            )
            self.assertEqual(
                second["fingerprint"]["digest"], value["fingerprint"]["digest"]
            )
            self.assertEqual(
                second["same_declared_inputs"],
                True if value["fingerprint"]["input_complete"] else None,
            )
            self.assertIn("same declared inputs as prior run", result.stdout)
            self.assertFalse(second["fingerprint"]["environment_complete"])
