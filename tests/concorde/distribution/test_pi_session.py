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
)
from concorde.distribution.build import (
    PRIVATE_PI_SESSION_SHIM as PI_SESSION_SHIM,
)
from concorde.spec.verification import verifies
from tests.concorde.support.pi_prompt_client import (
    PiRpcError,
    installed_pi,
    run_prompt,
)
from tests.concorde.support.fake_openai_provider import FakeOpenAIProvider
from tests.concorde.support.pi_session_project import set_up_selected_project

GOLDEN = REPOSITORY_ROOT / "tests/concorde/fixtures/build/golden/pi/concorde-session.ts"
HARNESS = REPOSITORY_ROOT / "tests/concorde/support/pi_session_harness.mts"
FAKE_LAUNCHER = "tests/concorde/support/fake_launcher.py"
EXTENSION = REPOSITORY_ROOT / PI_SESSION_EXTENSION
TYPEBOX = REPOSITORY_ROOT / "pi/node_modules/typebox/package.json"
RUN = {
    "operation": "concorde-validate",
    "action": "run",
    "input": {"target_id": "module.x", "task": "check"},
}


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
            "schema_version": 3,
            "launcher": FAKE_LAUNCHER,
            "interpreters": [sys.executable],
            "explicit_request_only": True,
            "operations": [
                {
                    "name": "concorde-validate",
                    "kind": "host",
                    "native_actions": [],
                    "description": "Run checks.",
                    "guidance": "# concorde-validate\n\nGuidance.\n",
                    "request_version": 1,
                    "request_schema": {"type": "object"},
                },
                {
                    "name": "concorde-plan",
                    "kind": "workflow",
                    "native_actions": [],
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
        return json.loads(text)

    @verifies("scenario.session.prompt")
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

    @verifies("scenario.session.describe")
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

    @verifies("scenario.session.run-host")
    def test_run_wraps_the_input_in_the_invocation_envelope(self):
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
        self.assertEqual(
            {
                "operation": "concorde-validate",
                "action": "run",
                "mode": "execute",
                "exit_code": 0,
            },
            result["details"],
        )

    @verifies("scenario.session.run-host")
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

    @verifies("scenario.session.run-host")
    def test_a_blocked_result_is_an_error_carrying_the_envelope(self):
        [result] = self.drive([{"params": RUN}], scenario="blocked")["results"]
        self.assertFalse(result["ok"], result)
        self.assertEqual("blocked", self.envelope(result["error"])["status"])

    @verifies("scenario.session.cancel")
    def test_abort_terminates_the_launcher_and_returns_its_cancelled_result(self):
        [result] = self.drive(
            [{"params": RUN, "abort_after_ms": 500}], scenario="hang"
        )["results"]
        self.assertFalse(result["ok"], result)
        self.assertIn("concorde-validate was cancelled", result["error"])
        self.assertIn("execution_cancelled", result["error"])
        self.assertLess(result["elapsed_ms"], 4000)

    @verifies("scenario.session.cancel")
    def test_a_launcher_ignoring_sigterm_is_killed_after_the_grace_period(self):
        [result] = self.drive(
            [{"params": RUN, "abort_after_ms": 200}], scenario="stubborn"
        )["results"]
        self.assertFalse(result["ok"], result)
        self.assertIn("concorde-validate was cancelled", result["error"])
        self.assertGreaterEqual(result["elapsed_ms"], 5000)
        self.assertLess(result["elapsed_ms"], 30000)

    @verifies("scenario.session.run-host")
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

    setUp = set_up_selected_project

    @verifies(
        "scenario.session.prompt",
        "scenario.session.describe",
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
        "scenario.session.select",
        "scenario.session.describe",
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
        "scenario.session.select",
        "scenario.session.run-host",
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
        # The fixture project stores no configuration; admission checks it before the request.
        self.assertEqual("configuration_mismatch", envelope["errors"][0]["code"])

    @verifies(
        "scenario.session.select",
        "scenario.session.task-subagents",
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

    @verifies("scenario.session.select")
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

    @verifies("scenario.session.select")
    def test_missing_selection_cannot_load_private_entry(self):
        with self.assertRaises(PiRpcError) as raised:
            self.drive([{"text": "no operation"}], use_selection=False)
        self.assertIn(
            "requires explicit candidate selection", raised.exception.run.stderr
        )
        self.assertEqual([], raised.exception.run.tool_results)


if __name__ == "__main__":
    unittest.main()
