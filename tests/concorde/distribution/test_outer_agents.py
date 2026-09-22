from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))
from concorde.distribution.build import build, check_build, write_build, BuildError
from concorde.distribution import installation
from concorde.spec.verification import verifies


class OuterAgentsTests(unittest.TestCase):
    @verifies("scenario.distribution.outer-roles")
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
        self.assertIn(".pi/extensions/concorde-outer-lifecycle.ts", source)
        self.assertNotIn(".pi/extensions/concorde-outer-lifecycle.ts", installed)
        self.assertIn(
            "sourceMainLifecycle as default",
            source[".pi/extensions/concorde-outer-lifecycle.ts"].content.decode(),
        )
        self.assertNotIn(
            "sourceMainLifecycle",
            source[".pi/agents/maintenance-worker.md"].content.decode(),
        )
        self.assertIn(
            "concorde-outer-lifecycle.ts",
            source[".pi/agents/maintenance-worker.md"].content.decode(),
        )
        self.assertNotIn(
            "concorde-outer-lifecycle", source[".pi/agents/tester.md"].content.decode()
        )
        self.assertNotIn(".pi/APPEND_SYSTEM.md", source)
        self.assertNotIn(".pi/extensions/concorde-session.ts", source)
        self.assertIn(".pi/agents/tester.md", installed)
        self.assertNotIn(".pi/agents/maintenance-worker.md", installed)
        self.assertNotIn(".pi/APPEND_SYSTEM.md", installed)
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
                "prompts/outer/source/" in p
                or p.endswith(
                    ("concorde-maintenance.ts", "concorde-outer-lifecycle.ts")
                )
                for p in outputs
            )
        )
        self.assertIn(".concorde/framework/pi/extensions/concorde-observe.ts", outputs)
        self.assertIn(".concorde/framework/pi/extensions/concorde-tester.ts", outputs)
        self.assertIn(
            ".concorde/framework/src/concorde/distribution/outer_check.py", outputs
        )

    @verifies("scenario.distribution.outer-roles")
    def test_missing_source_and_modified_projection_fail_closed(self):
        from concorde.distribution.outer_agents import render
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

    @verifies("scenario.distribution.outer-roles")
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

    @verifies("scenario.distribution.outer-roles")
    def test_actual_project_discovery_and_effective_tools(self):
        subagents = Path(
            os.environ.get(
                "CONCORDE_TEST_SUBAGENTS_ROOT",
                Path.home() / ".pi/agent/npm/node_modules/pi-subagents",
            )
        )
        pi = shutil.which("pi")
        if not subagents.is_dir() or not pi:
            self.skipTest("outer pi-subagents and Pi are host prerequisites")
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
                        / "tests/concorde/support/outer_agents_preflight.mjs"
                    ),
                    str(subagents),
                    str(pi_root),
                    str(REPOSITORY_ROOT),
                ],
                env={
                    **os.environ,
                    "PI_CODING_AGENT_DIR": directory,
                    "TMPDIR": directory,
                },
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
                        / "tests/concorde/support/outer_agents_preflight.mjs"
                    ),
                    str(subagents),
                    str(pi_root),
                    str(consumer),
                ],
                env={
                    **os.environ,
                    "PI_CODING_AGENT_DIR": directory,
                    "TMPDIR": directory,
                },
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

    @verifies("scenario.harness.outer-observation", "scenario.distribution.outer-roles")
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
                        / "tests/concorde/support/outer_observer_harness.mts"
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

    @verifies("scenario.harness.outer-lifecycle", "scenario.distribution.outer-roles")
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
                        / "tests/concorde/distribution/outer_lifecycle_fixture.mjs"
                    ),
                    str(sdk),
                    str(REPOSITORY_ROOT),
                    scratch,
                    provider.base_url,
                ],
                env={
                    **os.environ,
                    "PI_CODING_AGENT_DIR": scratch,
                    "PI_OFFLINE": "1",
                    "PI_TELEMETRY": "0",
                },
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

    @verifies("scenario.harness.outer-lifecycle", "scenario.distribution.outer-roles")
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
                        / "tests/concorde/distribution/main_brief_fixture.mjs"
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
    def test_runner_fingerprints_and_legacy_cli(self):
        path = REPOSITORY_ROOT / "scripts/development/run-tests.py"
        spec = importlib.util.spec_from_file_location(
            "concorde_test_runner_fixture", path
        )
        runner = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = runner
        spec.loader.exec_module(runner)
        first = runner.fingerprint(
            sys.executable, ["tests.concorde.harness.test_timing"]
        )
        self.assertEqual(
            first,
            runner.fingerprint(sys.executable, ["tests.concorde.harness.test_timing"]),
        )
        self.assertNotEqual(
            first["digest"], runner.fingerprint(sys.executable, ["other"])["digest"]
        )
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(path),
                    "--filter",
                    "harness.test_timing",
                    "--json",
                    str(report),
                    "-j",
                    "1",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            value = json.loads(report.read_text())
            self.assertEqual(value["reason"], "manual")
            self.assertEqual(value["scope"], "unspecified")
            self.assertTrue(all(s["layer"] == "C" for s in value["spans"]))
            self.assertIsNone(value["units"][0]["setup_seconds"])
            self.assertGreaterEqual(value["units"][0]["queue_seconds"], 0)
            self.assertGreaterEqual(value["units"][0]["execution_seconds"], 0)
