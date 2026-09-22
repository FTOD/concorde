"""The Pi session projection: the rendered shim, the extension's tool, and a real Pi loading it."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.environment import child_environment
from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.distribution.build import (
    PI_SESSION_EXTENSION,
    build,
    write_build,
)
from concorde.distribution.build import (
    PI_SESSION_SHIM as INSTALLED_PI_SESSION_SHIM,
)
from concorde.distribution.build import (
    PRIVATE_PI_SESSION_SHIM as PI_SESSION_SHIM,
)
from concorde.harness.pi_rpc import PiRpcError, run_prompt
from concorde.spec.contracts import PUBLIC_OPERATIONS
from concorde.spec.typed_data import json_schema
from concorde.spec.verification import verifies
from tests.concorde.harness.test_pi_worker import installed_pi
from tests.concorde.support.fake_openai_provider import FakeOpenAIProvider

GOLDEN = REPOSITORY_ROOT / "tests/concorde/fixtures/build/golden/pi/concorde-session.ts"
HARNESS = REPOSITORY_ROOT / "tests/concorde/support/pi_session_harness.mts"
FAKE_LAUNCHER = "tests/concorde/support/fake_launcher.py"
EXTENSION = REPOSITORY_ROOT / PI_SESSION_EXTENSION
TYPEBOX = REPOSITORY_ROOT / "pi/node_modules/typebox/package.json"
CATALOG_PATTERN = re.compile(
    r"const CATALOG: SessionCatalog = (\{.*?\n\});\n\nexport default", re.DOTALL
)
RUN = {
    "operation": "concorde-validate",
    "action": "run",
    "input": {"target_id": "module.x", "task": "check"},
}


def shim_catalog(content: bytes) -> dict:
    match = CATALOG_PATTERN.search(content.decode("utf-8"))
    assert match, "the shim embeds one CATALOG constant"
    return json.loads(match.group(1))


def node_version() -> tuple[int, ...]:
    node = shutil.which("node")
    if not node:
        return ()
    output = subprocess.run([node, "--version"], capture_output=True, text=True)
    try:
        return tuple(
            int(part) for part in output.stdout.strip().lstrip("v").split(".")[:3]
        )
    except ValueError:
        return ()


class ShimRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.checkout = {o.path: o for o in build(REPOSITORY_ROOT).outputs}
        cls.installed = {
            o.path: o
            for o in build(
                REPOSITORY_ROOT, framework_prefix=".concorde/framework"
            ).outputs
        }

    @verifies("scenario.distribution.build-pi-session")
    def test_the_pi_integration_renders_one_shim_and_no_skills(self):
        projected = [
            path for path in self.checkout if path.startswith("generated/session/")
        ]
        self.assertEqual([PI_SESSION_SHIM], projected)

    @verifies("scenario.distribution.build-pi-session")
    def test_checkout_shim_binds_the_tracked_extension_and_waits_for_explicit_requests(
        self,
    ):
        content = self.checkout[PI_SESSION_SHIM].content
        text = content.decode("utf-8")
        self.assertIn('from "../../../pi/extensions/concorde-session.ts"', text)
        self.assertIn('new URL("../../../", import.meta.url)', text)
        catalog = shim_catalog(content)
        self.assertEqual(2, catalog["schema_version"])
        self.assertTrue(catalog["explicit_request_only"])
        self.assertEqual("scripts/run-operation.py", catalog["launcher"])
        self.assertEqual(
            [".venv/bin/python", ".venv/Scripts/python.exe"], catalog["interpreters"]
        )
        self.assertEqual(
            list(PUBLIC_OPERATIONS), [o["name"] for o in catalog["operations"]]
        )
        for operation in catalog["operations"]:
            with self.subTest(operation=operation["name"]):
                schema = json_schema(f"{operation['name']}-request")
                self.assertEqual(schema, operation["request_schema"])
                self.assertEqual(
                    schema["properties"]["schema_version"]["const"],
                    operation["request_version"],
                )
                self.assertTrue(operation["description"].strip())
                self.assertTrue(
                    operation["guidance"].startswith(f"# {operation['name']}\n")
                )
                self.assertNotIn("stdin", operation["guidance"])
                self.assertNotIn("{OPERATION}", operation["guidance"])
                self.assertNotIn("\n\n\n", operation["guidance"])

    @verifies("scenario.distribution.build-pi-session")
    def test_public_descriptions_name_execution_kinds_not_generic_operations(self):
        prefixes = {
            "concorde-context-solve": "Agent entry:",
            "concorde-tasks": "Agent entry:",
            "concorde-implement": "Agent entry:",
            "concorde-plan": "Workflow:",
            "concorde-spec-review": "Workflow:",
            "concorde-code-review": "Workflow:",
            "concorde-init": "Host service:",
            "concorde-configure": "Host service:",
            "concorde-validate": "Host service:",
            "concorde-deliver": "Host service:",
            "concorde-issues": "Host bookkeeping or native solve workflow:",
        }
        for content in (
            self.checkout[PI_SESSION_SHIM].content,
            self.installed[INSTALLED_PI_SESSION_SHIM].content,
        ):
            catalog = shim_catalog(content)
            self.assertEqual(set(prefixes), {o["name"] for o in catalog["operations"]})
            for entry in catalog["operations"]:
                with self.subTest(entry=entry["name"]):
                    self.assertTrue(
                        entry["description"].startswith(prefixes[entry["name"]])
                    )
                    self.assertNotIn("other Operations", entry["guidance"])
                    self.assertNotIn("poll this same operation", entry["guidance"])
                    for obsolete in (
                        "Invoke this operation",
                        "deterministic lifecycle operation",
                        "public Operations",
                        "Operation workers",
                        "scheduled by the Graph/host",
                        "Non-implementation workers never receive",
                    ):
                        self.assertNotIn(obsolete, entry["guidance"])
                    self.assertEqual(
                        json_schema(f"{entry['name']}-request"), entry["request_schema"]
                    )

    @verifies("scenario.distribution.build-pi-session")
    def test_installed_shim_points_below_the_framework_prefix(self):
        content = self.installed[INSTALLED_PI_SESSION_SHIM].content
        self.assertIn(
            'from "../../.concorde/framework/pi/extensions/concorde-session.ts"',
            content.decode("utf-8"),
        )
        catalog = shim_catalog(content)
        self.assertFalse(catalog["explicit_request_only"])
        self.assertEqual(
            ".concorde/framework/scripts/run-operation.py", catalog["launcher"]
        )
        self.assertEqual(
            [".concorde/.venv/bin/python", ".concorde/.venv/Scripts/python.exe"],
            catalog["interpreters"],
        )

    @verifies("scenario.distribution.build-render")
    def test_shim_matches_golden_bytes_exactly(self):
        self.assertEqual(GOLDEN.read_bytes(), self.checkout[PI_SESSION_SHIM].content)

    @verifies("scenario.distribution.build-pi-session")
    def test_guidance_sources_have_no_standalone_invocation_mechanics(self):
        sources = self.checkout[PI_SESSION_SHIM].sources
        self.assertEqual(
            11, sum(s.startswith("prompts/operation-guidance/") for s in sources)
        )
        self.assertFalse(
            any("stdin-invocation" in s or "prompts/skills/" in s for s in sources)
        )
        catalog = shim_catalog(self.checkout[PI_SESSION_SHIM].content)
        issues = next(
            o for o in catalog["operations"] if o["name"] == "concorde-issues"
        )
        self.assertIn(
            "Solve returns needed implementation or Spec repair to the calling agent",
            issues["guidance"],
        )
        self.assertIn(
            "A return-to-caller result preserves the open Issue", issues["guidance"]
        )


class CurrentGuidanceTests(unittest.TestCase):
    def test_guides_distinguish_role_discovery_from_public_capabilities(self):
        roles = (
            "context-assessor",
            "planner",
            "task-author",
            "programmer",
            "spec-reviewer",
            "code-reviewer",
            "issue-solver",
            "maintenance-worker",
            "tester",
        )
        for path in ("README.md", "docs/workflow-guide.md"):
            with self.subTest(path=path):
                text = (REPOSITORY_ROOT / path).read_text()
                self.assertIn("specs/concorde/agents/module.md", text)
                self.assertTrue(
                    (REPOSITORY_ROOT / "specs/concorde/agents/module.md").is_file()
                )
                for role in roles:
                    self.assertIn(f"`{role}`", text)
                self.assertIn("source-only", text)
                self.assertIn("external", text)
                self.assertIn("StateGraph", text)
                self.assertNotIn("eleven public Operations", text)
                self.assertNotIn("operations/<role>/spec.md", text)
                self.assertNotIn("Bounded Operation workers", text)


@unittest.skipUnless(
    node_version() >= (22, 6), "Node 22.6+ is required to run TypeScript"
)
@unittest.skipUnless(
    TYPEBOX.is_file(), "typebox is not installed; run npm ci --prefix pi"
)
class SessionToolTests(unittest.TestCase):
    """The extension's tool against a fake launcher, driven by a Node harness outside Pi."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.catalog_path = Path(temporary.name) / "catalog.json"

    @staticmethod
    def catalog(**changes) -> dict:
        catalog = {
            "schema_version": 2,
            "launcher": FAKE_LAUNCHER,
            "interpreters": [sys.executable],
            "explicit_request_only": True,
            "operations": [
                {
                    "name": "concorde-validate",
                    "description": "Run checks.",
                    "guidance": "# concorde-validate\n\nGuidance.\n",
                    "request_version": 1,
                    "request_schema": {"type": "object"},
                },
                {
                    "name": "concorde-plan",
                    "description": "Ask.",
                    "guidance": "# concorde-main\n",
                    "request_version": 1,
                    "request_schema": {"type": "object"},
                },
            ],
        }
        catalog.update(changes)
        return catalog

    def drive(self, calls: list[dict], *, scenario: str = "echo", **changes) -> dict:
        self.catalog_path.write_text(
            json.dumps(self.catalog(**changes)), encoding="utf-8"
        )
        process = subprocess.run(
            [
                "node",
                "--experimental-strip-types",
                str(HARNESS),
                str(EXTENSION),
                str(REPOSITORY_ROOT),
                str(self.catalog_path),
            ],
            input=json.dumps({"calls": calls}),
            capture_output=True,
            text=True,
            timeout=120,
            env=child_environment(FAKE_LAUNCHER_SCENARIO=scenario),
            cwd=str(REPOSITORY_ROOT),
        )
        self.assertEqual(0, process.returncode, process.stderr)
        return json.loads(process.stdout)

    @staticmethod
    def envelope(text: str) -> dict:
        body, _, usage = text.rpartition("\n")
        assert usage.startswith("usage: "), text
        return json.loads(body)

    @verifies("scenario.distribution.pi-session-prompt")
    def test_prompt_and_tool_name_every_public_operation(self):
        outcome = self.drive([])
        self.assertTrue(outcome["prompt"].startswith("BASE PROMPT\n\n## Concorde\n"))
        self.assertIn("- concorde-validate: Run checks.", outcome["prompt"])
        self.assertIn("- concorde-plan: Ask.", outcome["prompt"])
        self.assertIn("only when the user explicitly asks", outcome["prompt"])
        self.assertEqual("concorde", outcome["tool"]["name"])
        parameters = outcome["tool"]["parameters"]
        self.assertEqual(
            ["concorde-validate", "concorde-plan"],
            parameters["properties"]["operation"]["enum"],
        )
        self.assertEqual(
            ["run", "describe", "result"], parameters["properties"]["action"]["enum"]
        )
        self.assertEqual(["operation", "action"], parameters["required"])
        installed = self.drive([], explicit_request_only=False)
        self.assertNotIn("explicitly asks", installed["prompt"])

    @verifies("scenario.distribution.pi-session-describe")
    def test_describe_returns_guidance_and_the_request_schema(self):
        [result] = self.drive(
            [{"params": {"operation": "concorde-validate", "action": "describe"}}]
        )["results"]
        self.assertTrue(result["ok"], result)
        self.assertIn("# concorde-validate", result["text"])
        self.assertIn("Guidance.", result["text"])
        self.assertIn("schema_version 1", result["text"])
        self.assertIn('"type": "object"', result["text"])
        self.assertEqual(
            {"operation": "concorde-validate", "action": "describe"}, result["details"]
        )

    @verifies("scenario.distribution.pi-session-run")
    def test_run_wraps_the_input_in_the_invocation_envelope_and_reports_usage(self):
        [result] = self.drive([{"params": RUN}])["results"]
        self.assertTrue(result["ok"], result)
        self.assertEqual(
            {
                "type_id": "concorde-operation-invocation",
                "schema_version": 3,
                "operation_id": "concorde-validate",
                "mode": "execute",
                "configuration": None,
                "input": {
                    "type_id": "concorde-validate-request",
                    "schema_version": 1,
                    "data": {"target_id": "module.x", "task": "check"},
                },
            },
            self.envelope(result["text"])["output"]["echo"],
        )
        self.assertTrue(
            result["text"].endswith(
                "usage: input 120, output 30, cost 0.0125 USD, 4.5 s"
            )
        )
        self.assertEqual(
            {
                "operation": "concorde-validate",
                "action": "run",
                "mode": "execute",
                "exit_code": 0,
            },
            result["details"],
        )

    @verifies("scenario.distribution.pi-session-run")
    def test_describe_policy_mode_missing_input_and_unknown_operation(self):
        results = self.drive(
            [
                {
                    "params": {
                        **RUN,
                        "operation": "concorde-validate",
                        "mode": "describe-policy",
                    }
                },
                {"params": {"operation": "concorde-plan", "action": "run"}},
                {"params": {"operation": "concorde-other", "action": "describe"}},
            ]
        )["results"]
        self.assertEqual(
            "describe-policy",
            self.envelope(results[0]["text"])["output"]["echo"]["mode"],
        )
        self.assertFalse(results[1]["ok"])
        self.assertIn("needs `input`", results[1]["error"])
        self.assertFalse(results[2]["ok"])
        self.assertIn("unknown Concorde Operation", results[2]["error"])

    @verifies("scenario.distribution.pi-session-run")
    def test_a_blocked_result_is_an_error_carrying_the_envelope(self):
        [result] = self.drive([{"params": RUN}], scenario="blocked")["results"]
        self.assertFalse(result["ok"], result)
        self.assertEqual("blocked", self.envelope(result["error"])["status"])

    @verifies("scenario.distribution.pi-session-cancel")
    def test_abort_terminates_the_launcher_and_returns_its_cancelled_result(self):
        [result] = self.drive(
            [{"params": RUN, "abort_after_ms": 500}], scenario="hang"
        )["results"]
        self.assertFalse(result["ok"], result)
        self.assertIn("concorde-validate was cancelled", result["error"])
        self.assertIn("execution_cancelled", result["error"])
        self.assertLess(result["elapsed_ms"], 4000)

    @verifies("scenario.distribution.pi-session-cancel")
    def test_a_launcher_ignoring_sigterm_is_killed_after_the_grace_period(self):
        [result] = self.drive(
            [{"params": RUN, "abort_after_ms": 200}], scenario="stubborn"
        )["results"]
        self.assertFalse(result["ok"], result)
        self.assertIn("concorde-validate was cancelled", result["error"])
        self.assertGreaterEqual(result["elapsed_ms"], 5000)
        self.assertLess(result["elapsed_ms"], 30000)

    @verifies("scenario.distribution.pi-session-run")
    def test_a_large_result_is_saved_to_a_file(self):
        [result] = self.drive([{"params": RUN}], scenario="large")["results"]
        self.assertTrue(result["ok"], result)
        match = re.search(r"saved at (\S+)\]", result["text"])
        self.assertTrue(match, result["text"][-300:])
        saved = Path(match.group(1))
        self.addCleanup(shutil.rmtree, saved.parent, True)
        self.assertEqual(
            "succeeded", json.loads(saved.read_text(encoding="utf-8"))["status"]
        )


@unittest.skipUnless(installed_pi(), "the pi executable is not installed")
class RealPiSessionTests(unittest.TestCase):
    """A real Pi process loads the rendered shim and calls the tool it registers."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.project = self.root / "project"
        for directory in (
            "agents",
            "prompts",
            "protocol",
            "operations",
            "src",
            "pi",
            "scripts",
        ):
            shutil.copytree(
                REPOSITORY_ROOT / directory,
                self.project / directory,
                ignore=shutil.ignore_patterns("node_modules", "__pycache__"),
            )
        write_build(self.project)
        # Host infrastructure is explicit and local to this disposable fixture, not installed globally.
        (self.project / ".venv").symlink_to(Path(sys.prefix), target_is_directory=True)
        from concorde.distribution.session_selection import (
            save_selection,
            select_session,
        )

        self.selection_path = self.project / ".concorde/work/pi-selection.json"
        self.selection = select_session(
            self.project,
            mode="test",
            pi_entry=self.project / PI_SESSION_SHIM,
            runtime=self.project / "scripts/run-operation.py",
        )
        save_selection(self.project, self.selection_path, self.selection)
        self.agent = self.root / "agent"
        self.agent.mkdir()
        (self.agent / "settings.json").write_text(
            json.dumps(
                {
                    "defaultProjectTrust": "never",
                    "quietStartup": True,
                    "enableInstallTelemetry": False,
                }
            )
        )

    @verifies(
        "scenario.distribution.pi-session-prompt",
        "scenario.distribution.pi-session-describe",
    )
    def drive(self, turns, *, use_selection=True, binding=False, conflict=False):
        pi = installed_pi()
        assert pi is not None
        with FakeOpenAIProvider(turns) as provider:
            (self.agent / "models.json").write_text(
                json.dumps(
                    {
                        "providers": {
                            "fake": {
                                "baseUrl": provider.base_url,
                                "api": "openai-completions",
                                "apiKey": "fake-key",
                                "compat": {
                                    "supportsDeveloperRole": False,
                                    "supportsReasoningEffort": False,
                                },
                                "models": [{"id": "fake-model"}],
                            }
                        }
                    }
                )
            )
            env = {
                "HOME": str(self.root),
                "LANG": "C.UTF-8",
                "PATH": f"{Path(pi).parent}:/usr/bin:/bin",
                "PI_CODING_AGENT_DIR": str(self.agent),
                "PI_OFFLINE": "1",
                "PI_SKIP_VERSION_CHECK": "1",
                "PI_TELEMETRY": "0",
                "CONCORDE_SESSION_SELECTION": str(self.selection_path),
            }
            if not use_selection or binding:
                env.pop("CONCORDE_SESSION_SELECTION")
            if binding:
                env["PI_SUBAGENT_EXTENSION_BINDINGS"] = json.dumps(
                    {"concorde/1": {"selection": str(self.selection_path)}}
                )
            if conflict:
                env["CONCORDE_SESSION_SELECTION"] = str(
                    self.root / "foreign-selection.json"
                )
            argv = [
                pi,
                "--mode",
                "rpc",
                "--no-session",
                "--no-context-files",
                "--no-skills",
                "--no-prompt-templates",
                "--no-themes",
                "--no-extensions",
                "-e",
                str(self.project / PI_SESSION_SHIM),
                "--no-approve",
                "--offline",
                "--tools",
                "read,concorde",
                "--model",
                "fake/fake-model",
            ]
            run = run_prompt(
                argv,
                cwd=str(self.project),
                env=env,
                message="Describe validate.",
                timeout=90,
            )
        return run, provider.requests

    @verifies(
        "scenario.distribution.private-selection",
        "scenario.distribution.pi-session-describe",
    )
    def test_pi_advertises_the_exact_candidate_tool_and_answers_describe(self):
        run, requests = self.drive(
            [
                {
                    "tool": "concorde",
                    "arguments": {
                        "operation": "concorde-validate",
                        "action": "describe",
                    },
                },
                {"text": "done"},
            ]
        )
        results = run.results_of("concorde")
        self.assertEqual(1, len(results), run.stderr)
        self.assertFalse(results[0]["isError"], results[0])
        text = results[0]["result"]["content"][0]["text"]
        self.assertIn("# concorde-validate", text)
        self.assertIn("concorde-validate-request", text)
        first = requests[0]
        system = first["messages"][0]["content"]
        self.assertIn("## Concorde", system)
        self.assertIn("- concorde-validate:", system)
        self.assertIn("only when the user explicitly asks", system)
        self.assertIn("concorde", [tool["function"]["name"] for tool in first["tools"]])

    @verifies(
        "scenario.distribution.private-selection",
        "scenario.distribution.pi-session-run",
    )
    def test_pi_calls_selected_candidate_runtime_and_preserves_rejection_envelope(self):
        run, _ = self.drive(
            [
                {
                    "tool": "concorde",
                    "arguments": {
                        "operation": "concorde-validate",
                        "action": "run",
                        "input": {},
                    },
                },
                {"text": "done"},
            ]
        )
        [result] = run.results_of("concorde")
        self.assertTrue(result["isError"], result)
        text = result["result"]["content"][0]["text"]
        envelope = json.loads(text)
        self.assertEqual("concorde-operation-result", envelope["type_id"])
        self.assertEqual(3, envelope["schema_version"])
        self.assertEqual("concorde-validate", envelope["operation_id"])
        self.assertEqual("invalid_field", envelope["errors"][0]["code"])

    @verifies(
        "scenario.distribution.private-selection", "scenario.distribution.outer-roles"
    )
    def test_native_child_binding_loads_exact_entry_without_global_env(self):
        run, _ = self.drive(
            [
                {
                    "tool": "concorde",
                    "arguments": {
                        "operation": "concorde-validate",
                        "action": "describe",
                    },
                },
                {"text": "done"},
            ],
            binding=True,
        )
        self.assertFalse(run.results_of("concorde")[0]["isError"])
        with self.assertRaises(PiRpcError) as raised:
            self.drive([{"text": "no operation"}], binding=True, conflict=True)
        self.assertIn("Conflicting private selection", raised.exception.run.stderr)
        self.assertEqual([], raised.exception.run.tool_results)

    @verifies("scenario.distribution.private-selection")
    def test_stale_selected_implementation_registers_no_tool(self):
        implementation = self.project / PI_SESSION_EXTENSION
        implementation.write_text(implementation.read_text() + "\n// stale\n")
        with self.assertRaises(PiRpcError) as raised:
            self.drive([{"text": "no operation"}])
        self.assertIsNotNone(raised.exception.run)
        self.assertIn(
            "private Pi selection verification failed", raised.exception.run.stderr
        )
        self.assertEqual([], raised.exception.run.tool_results)

    @verifies("scenario.distribution.private-selection")
    def test_missing_selection_cannot_load_private_entry(self):
        with self.assertRaises(PiRpcError) as raised:
            self.drive([{"text": "no operation"}], use_selection=False)
        self.assertIn(
            "requires explicit candidate selection", raised.exception.run.stderr
        )
        self.assertEqual([], raised.exception.run.tool_results)


if __name__ == "__main__":
    unittest.main()
