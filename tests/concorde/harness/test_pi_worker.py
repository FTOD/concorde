"""Pi workers: the RPC client's framing, and real Pi processes against a scripted offline provider."""
from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.harness.pi_rpc import PiRpcError, PiRpcTimeout, run_prompt  # noqa: E402
from concorde.harness.pi_worker import (ChildAgent, PiWorkerRuntime, WorkerExecutionError,  # noqa: E402
                                        WorkerLaunch)
from concorde.spec.verification import verifies  # noqa: E402
from tests.concorde.support.fake_openai_provider import FakeOpenAIProvider  # noqa: E402

FAKE_PI = Path(__file__).resolve().parents[1] / "support" / "fake_pi_rpc.py"
RESULT = {"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"],
          "additionalProperties": False}
READ = ("read", "grep", "find", "ls")


def installed_pi() -> str | None:
    """The pi executable on PATH, or a Node version manager installation of it."""
    found = shutil.which("pi")
    if found:
        return found
    candidates = sorted(glob.glob(os.path.expanduser("~/.nvm/versions/node/*/bin/pi")))
    return candidates[-1] if candidates else None


class RpcClientTests(unittest.TestCase):
    def run_fake(self, scenario: str, timeout: float = 10):
        env = {"PATH": os.environ.get("PATH", ""), "FAKE_PI_SCENARIO": scenario}
        return run_prompt([sys.executable, str(FAKE_PI)], cwd=str(REPOSITORY_ROOT), env=env,
                          message="Do the task.", timeout=timeout)

    @verifies("scenario.harness.pi-rpc-client")
    def test_records_split_only_on_line_feed_and_dialogs_are_cancelled(self):
        run = self.run_fake("settle")
        details = run.results_of("submit_result")[0]["result"]["details"]
        self.assertEqual("line separator paragraph", details["text"])
        self.assertEqual({"type": "extension_ui_response", "id": "dialog-1", "cancelled": True}, details["dialog"])
        assert run.stats is not None
        self.assertEqual({"input": 7, "output": 3, "cacheRead": 1, "total": 10}, run.stats["tokens"])
        self.assertEqual("agent_settled", run.events[-1]["type"])
        self.assertEqual(0, run.exit_code)

    @verifies("scenario.harness.pi-rpc-client")
    def test_early_exit_and_missed_deadline_are_failures(self):
        with self.assertRaises(PiRpcError):
            self.run_fake("eof")
        with self.assertRaises(PiRpcTimeout):
            self.run_fake("hang", timeout=1)


@unittest.skipUnless(installed_pi(), "the pi executable is not installed")
class PiWorkerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        (self.workspace / "granted.md").write_text("GRANTED CONTENT\n")
        (self.workspace / "hidden.md").write_text("HIDDEN\n")
        (self.root / "secret.md").write_text("SECRET\n")
        self.credentials = self.root / "credentials"
        self.credentials.mkdir()
        pi = installed_pi()
        assert pi is not None
        self.environment = {"HOME": str(self.root), "LANG": "C.UTF-8",
                            "PATH": f"{Path(pi).parent}:/usr/bin:/bin", "OPENAI_API_KEY": "sk-test"}
        self.runtime = PiWorkerRuntime(REPOSITORY_ROOT, pi_executable=pi, environment=self.environment,
                                       credentials_dir=self.credentials)

    def provider(self, turns):
        provider = FakeOpenAIProvider(turns)
        (self.credentials / "models.json").write_text(json.dumps({"providers": {"fake": {
            "baseUrl": provider.base_url, "api": "openai-completions", "apiKey": "fake-key",
            "compat": {"supportsDeveloperRole": False, "supportsReasoningEffort": False},
            "models": [{"id": "fake-model"}]}}}))
        return provider

    def launch(self, **changes) -> WorkerLaunch:
        values: dict[str, Any] = dict(worker="tester", workspace=str(self.workspace), system_prompt="WORKER-SYSTEM-PROMPT",
                      message='{"task": "answer"}', result_schema=RESULT, tools=(*READ, "submit_result"),
                      read_paths=("granted.md",), model="fake/fake-model", timeout_seconds=90)
        values.update(changes)
        return WorkerLaunch(**values)

    @staticmethod
    def results(run, tool):
        return [(item["isError"], item["result"]["content"][0]["text"]) for item in run.results_of(tool)]

    @verifies("scenario.harness.pi-worker-launch")
    @verifies("scenario.harness.pi-worker-gate")
    def test_worker_reads_only_its_grant_and_returns_its_single_submission(self):
        turns = [{"tool": "read", "arguments": {"path": "../secret.md"}},
                 {"tool": "grep", "arguments": {"pattern": "HIDDEN", "path": "."}},
                 {"tool": "bash", "arguments": {"command": "cat hidden.md"}},
                 {"tool": "read", "arguments": {"path": "granted.md"}},
                 {"tool": "submit_result", "arguments": {"answer": "done"}}]
        with self.provider(turns) as provider:
            result = self.runtime(self.launch())
        self.assertEqual({"answer": "done"}, result.value)
        gated = [item for item in self.results(result.run, "read") + self.results(result.run, "grep") if item[0]]
        self.assertEqual(2, len(gated), gated)
        self.assertTrue(all(text.startswith("Concorde worker policy:") for _, text in gated), gated)
        # bash is not in this worker's tool list, so Pi itself refuses the unadvertised call.
        self.assertTrue(all(failed for failed, _ in self.results(result.run, "bash")))
        self.assertEqual([(False, "GRANTED CONTENT\n")], [item for item in self.results(result.run, "read") if not item[0]])
        first = provider.requests[0]
        self.assertEqual({"role": "system", "content": "WORKER-SYSTEM-PROMPT"}, first["messages"][0])
        self.assertEqual([*READ, "submit_result"], [tool["function"]["name"] for tool in first["tools"]])
        self.assertEqual(RESULT, next(tool["function"]["parameters"] for tool in first["tools"]
                                      if tool["function"]["name"] == "submit_result"))
        # The scripted provider reports 100 input and 10 output tokens for each of its five responses.
        self.assertEqual((500, 50, "fake/fake-model"),
                         (result.usage["input_tokens"], result.usage["output_tokens"], result.usage["model"]))

    @verifies("scenario.harness.pi-worker-gate")
    def test_writes_stay_inside_the_write_grant_and_shell_commands_lose_provider_credentials(self):
        (self.workspace / "src").mkdir()
        turns = [{"tool": "write", "arguments": {"path": "hidden.md", "content": "overwritten"}},
                 {"tool": "write", "arguments": {"path": "src/new.py", "content": "print(1)\n"}},
                 {"tool": "bash", "arguments": {"command": "printf '%s' \"${OPENAI_API_KEY:-unset}\""}},
                 {"tool": "submit_result", "arguments": {"answer": "written"}}]
        launch = self.launch(tools=(*READ, "write", "bash", "submit_result"), read_paths=("granted.md",),
                             write_paths=("src/",))
        with self.provider(turns):
            result = self.runtime(launch)
        writes = self.results(result.run, "write")
        self.assertTrue(writes[0][0] and "outside the write grant" in writes[0][1], writes)
        self.assertFalse(writes[1][0], writes)
        self.assertEqual("HIDDEN\n", (self.workspace / "hidden.md").read_text())
        self.assertEqual("print(1)\n", (self.workspace / "src/new.py").read_text())
        self.assertIn("unset", self.results(result.run, "bash")[0][1])

    @verifies("scenario.harness.pi-worker-delegation")
    def test_one_level_children_run_under_the_same_gate_and_cannot_delegate(self):
        subagents = REPOSITORY_ROOT / "pi/node_modules/pi-subagents/index.ts"
        if not subagents.is_file():
            self.skipTest("pi-subagents is not installed; run npm ci --prefix pi")
        scout = ChildAgent("scout", "---\nname: scout\ndescription: Reads granted files.\ntools: read, grep, find, ls\n"
                                    "systemPromptMode: replace\ninheritProjectContext: false\ninheritSkills: false\n"
                                    "completionGuard: false\n---\nYou are a scout.\n")
        turns = [{"tool": "subagent", "arguments": {"agent": "scout", "task": "Read the files", "async": False}},
                 {"tool": "read", "arguments": {"path": "../secret.md"}},
                 {"tool": "read", "arguments": {"path": "granted.md"}},
                 {"text": "scout found GRANTED CONTENT"},
                 {"tool": "subagent", "arguments": {"agent": "worker", "task": "Not a declared child", "async": False}},
                 {"tool": "submit_result", "arguments": {"answer": "delegated"}}]
        launch = self.launch(tools=(*READ, "subagent", "submit_result"), children=(scout,), child_tools=READ)
        with self.provider(turns) as provider:
            result = self.runtime(launch)
        self.assertEqual({"answer": "delegated"}, result.value)
        delegated = self.results(result.run, "subagent")
        self.assertFalse(delegated[0][0], delegated)
        self.assertIn("scout found GRANTED CONTENT", delegated[0][1])
        self.assertTrue(delegated[1][0], delegated)
        child_requests = provider.requests[1:4]
        self.assertTrue(all([tool["function"]["name"] for tool in request["tools"]] == list(READ)
                            for request in child_requests))
        blocked = [message for message in child_requests[1]["messages"] if message.get("role") == "tool"]
        self.assertIn("outside the read grant", json.dumps(blocked))

    @verifies("scenario.issues.report-independent", "scenario.issues.report-authority")
    def test_issue_tool_persists_during_execution_and_reports_rejection_as_an_error(self):
        from concorde.issues.reporting import IssueReporter
        from concorde.issues.store import list_issues
        from tests.concorde.issues.test_store import report, source
        reporter = IssueReporter(self.workspace, source(), frozenset({"module.service"}), frozenset())
        one = report(evidence=[])
        two = report(report_key="second", evidence=[])
        turns = [{"tool": "report_issue", "arguments": report(owner_target_id="module.foreign", evidence=[])},
                 {"tool": "report_issue", "arguments": one},
                 {"tool": "report_issue", "arguments": one},
                 {"tool": "report_issue", "arguments": two},
                 {"tool": "submit_result", "arguments": {"answer": "reported and continued"}}]
        launch = self.launch(tools=(*READ, "report_issue", "submit_result"), report_schema=reporter.schema)
        with self.provider(turns):
            result = self.runtime(launch, report_issue=reporter)
        reports = self.results(result.run, "report_issue")
        self.assertTrue(reports[0][0], reports)
        self.assertIn("outside the admitted context", reports[0][1])
        self.assertTrue(all(not failed for failed, _ in reports[1:]), reports)
        self.assertEqual(reports[1][1], reports[2][1])
        self.assertEqual(2, len(list_issues(self.workspace)))
        self.assertEqual("reported and continued", result.value["answer"])
        self.assertEqual((), launch.write_paths)

    @verifies("scenario.issues.report-survives-failure")
    def test_issue_tool_report_survives_a_missing_final_submission(self):
        from concorde.issues.reporting import IssueReporter
        from concorde.issues.store import list_issues
        from tests.concorde.issues.test_store import report, source
        reporter = IssueReporter(self.workspace, source(), frozenset({"module.service"}), frozenset())
        launch = self.launch(tools=(*READ, "report_issue", "submit_result"), report_schema=reporter.schema)
        turns = [{"tool": "report_issue", "arguments": report(evidence=[])}, {"text": "No final submission."}]
        with self.provider(turns), self.assertRaises(WorkerExecutionError) as failure:
            self.runtime(launch, report_issue=reporter)
        self.assertEqual("invalid_completion", failure.exception.outcome)
        self.assertEqual(1, len(list_issues(self.workspace)))

    @verifies("scenario.harness.pi-worker-launch")
    def test_run_checks_is_answered_by_the_host(self):
        turns = [{"tool": "run_checks", "arguments": {}},
                 {"tool": "submit_result", "arguments": {"answer": "checked"}}]
        launch = self.launch(tools=(*READ, "run_checks", "submit_result"))
        with self.provider(turns):
            result = self.runtime(launch, checks=lambda: {"checks": [{"check_id": "unit", "status": "passed"}]})
        [(failed, text)] = self.results(result.run, "run_checks")
        self.assertFalse(failed)
        self.assertEqual({"checks": [{"check_id": "unit", "status": "passed"}]}, json.loads(text))

    @verifies("scenario.harness.pi-worker-launch")
    def test_missing_submission_and_missed_deadline_are_distinct_failures(self):
        with self.provider([{"text": "I will not submit."}]):
            with self.assertRaises(WorkerExecutionError) as missing:
                self.runtime(self.launch())
        self.assertEqual("invalid_completion", missing.exception.outcome)
        with self.provider([{"text": "slow", "delay": 5}]):
            with self.assertRaises(WorkerExecutionError) as late:
                self.runtime(self.launch(timeout_seconds=2))
        self.assertEqual("limit_exhausted", late.exception.outcome)

    @verifies("scenario.harness.pi-worker-launch")
    def test_invalid_launches_are_refused_before_any_process_starts(self):
        runtime = PiWorkerRuntime(REPOSITORY_ROOT, pi_executable="/nonexistent/pi", environment=self.environment,
                                  credentials_dir=self.credentials, popen=lambda *args, **kwargs: self.fail("started"))
        for changes in ({"tools": READ}, {"tools": (*READ, "subagent", "submit_result")},
                        {"tools": (*READ, "edit", "submit_result")}, {"tools": (*READ, "run_checks", "submit_result")},
                        {"thinking": "extreme"}, {"workspace": "relative"},
                        {"tools": (*READ, "report_issue", "submit_result")},
                        {"report_schema": RESULT}):
            with self.subTest(changes=changes), self.assertRaises(WorkerExecutionError):
                runtime(self.launch(**changes))


class RuntimeHelperTests(unittest.TestCase):
    @verifies("scenario.harness.pi-worker-launch")
    def test_pi_subagents_resolves_from_the_checkout_else_the_managed_runtime(self):
        from concorde.harness.pi_worker import subagents_entry
        with tempfile.TemporaryDirectory() as temporary:
            framework = Path(temporary) / ".concorde/framework"
            managed = Path(temporary) / ".concorde/.venv/share/concorde/pi/node_modules/pi-subagents/index.ts"
            local = framework / "pi/node_modules/pi-subagents/index.ts"
            self.assertEqual(local.resolve(), subagents_entry(framework))
            managed.parent.mkdir(parents=True)
            managed.write_text("// managed\n")
            self.assertEqual(managed.resolve(), subagents_entry(framework))
            local.parent.mkdir(parents=True)
            local.write_text("// checkout\n")
            self.assertEqual(local.resolve(), subagents_entry(framework))

    @verifies("scenario.harness.pi-worker-launch")
    def test_a_refreshed_credential_returns_only_over_the_bytes_the_run_was_issued(self):
        from concorde.harness.pi_worker import _return_refreshed_auth
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original, copy = root / "auth.json", root / "run-auth.json"
            issued = b'{"openai-codex": {"refresh": "r1"}}'
            for label, refreshed, current, expected in (
                ("refresh returns", b'{"openai-codex": {"refresh": "r2"}}', issued, b'{"openai-codex": {"refresh": "r2"}}'),
                ("concurrent refresh wins", b'{"openai-codex": {"refresh": "r2"}}', b'{"openai-codex": {"refresh": "r9"}}',
                 b'{"openai-codex": {"refresh": "r9"}}'),
                ("unchanged copy", issued, issued, issued),
                ("malformed copy", b"not json", issued, issued),
            ):
                with self.subTest(label):
                    original.write_bytes(current)
                    copy.write_bytes(refreshed)
                    _return_refreshed_auth(copy, original, issued)
                    self.assertEqual(expected, original.read_bytes())
            self.assertEqual(0o600, original.stat().st_mode & 0o777)


if __name__ == "__main__":
    unittest.main()
