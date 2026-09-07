"""Opt-in real Agent Server checks: CONCORDE_TEST_STUDIO=1 with uv's studio group.

Only temporary consumer fixtures run operations. No source/primary-worktree state is changed.
Model responses are deterministic; AgentProcessExecutor and permission gates remain real.
"""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib.request import Request, urlopen

from tests.concorde.specification.support import PACKAGE, project
from tests.concorde.capabilities.unit.test_studio import invocation, stable


@unittest.skipUnless(os.environ.get("CONCORDE_TEST_STUDIO") == "1", "requires optional Studio server")
class StudioServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="concorde-studio-test-")
        cls.addClassCleanup(cls.temp.cleanup)
        directory = Path(cls.temp.name)
        cls.root = directory / "consumer"
        cls.root.mkdir()
        project(cls.root)
        from tests.concorde.specification.test_worktree_lifecycle import WorktreeLifecycleTests
        cls.change_fixture = WorktreeLifecycleTests()
        cls.change_fixture.setUp()
        cls.addClassCleanup(cls.change_fixture.doCleanups)
        source = directory / "graphs.py"
        source.write_text(
            "from pathlib import Path\n"
            "from concorde.capabilities.protocol_contracts import PUBLIC_OPERATIONS\n"
            "from concorde.capabilities.studio import build_studio_graph\n"
            "from tests.concorde.specification.support import ModelProcessDouble\n"
            "double = ModelProcessDouble()\n"
            "def executor(launch):\n"
            "    if launch.request == 'Trigger executor failure':\n"
            "        raise RuntimeError('fixture executor failure')\n"
            "    return double.executor(launch)\n"
            "for op in PUBLIC_OPERATIONS:\n"
            f"    root = Path({str(cls.change_fixture.change)!r}) if op == 'concorde-dev-loop' else Path({str(cls.root)!r})\n"
            "    globals()[op.replace('-', '_')] = build_studio_graph(op, root, "
            f"Path({str(PACKAGE)!r}), executor=executor)\n"
        )
        manifest = json.loads((PACKAGE / "generated/langgraph.json").read_text())
        manifest["graphs"] = {op: f"{source}:{op.replace('-', '_')}" for op in manifest["graphs"]}
        manifest["dependencies"] = [str(PACKAGE)]
        config = directory / "langgraph.json"
        config.write_text(json.dumps(manifest))
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        cls.base = f"http://127.0.0.1:{port}"
        cls.log = (directory / "server.log").open("w+")
        cls.addClassCleanup(cls.log.close)
        environment = {**os.environ, "PYTHONPATH": os.pathsep.join([str(PACKAGE / "src"), str(PACKAGE)]),
                       "LANGSMITH_TRACING": "false", "LANGGRAPH_CLI_NO_ANALYTICS": "1"}
        environment.pop("CONCORDE_STUDIO_URL", None)
        cls.server = subprocess.Popen([sys.executable, "-m", "langgraph_cli", "dev", "--no-browser",
            "--no-reload", "--host", "127.0.0.1", "--port", str(port), "--config", str(config),
            "--n-jobs-per-worker", "1"], cwd=directory, env=environment, stdout=cls.log, stderr=cls.log)
        cls.addClassCleanup(cls.stop_server)
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            try:
                cls.request("/ok")
                return
            except Exception:
                if cls.server.poll() is not None:
                    break
                time.sleep(0.2)
        cls.log.flush()
        cls.log.seek(0)
        raise AssertionError("Studio failed to start:\n" + cls.log.read()[-12000:])

    @classmethod
    def stop_server(cls):
        cls.server.terminate()
        try:
            cls.server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            cls.server.kill()
            cls.server.wait(timeout=10)

    @classmethod
    def request(cls, path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        with urlopen(Request(cls.base + path, data=data, headers={"Content-Type": "application/json"}), timeout=20) as response:
            return json.load(response)

    def run_graph(self, value, **extra):
        thread = self.request("/threads", {})["thread_id"]
        state = self.request(f"/threads/{thread}/runs/wait", {
            "assistant_id": value["operation_id"], "input": {"invocation": value, **extra}})
        self.assertNotIn("__error__", state, state)
        return thread, state

    def cli(self, value, forwarded=True, launcher=False):
        entry = PACKAGE / "operations" / value["operation_id"] / "operation.py"
        argv = [sys.executable, str(entry)]
        if launcher:
            argv = [sys.executable, str(PACKAGE / "scripts/run-operation.py"), str(entry)]
        env = {**os.environ}
        env.pop("CONCORDE_STUDIO_URL", None)
        if forwarded:
            env["CONCORDE_STUDIO_URL"] = self.base
        return subprocess.run(argv, input=json.dumps(value), text=True, capture_output=True,
                              cwd=self.root, env=env, timeout=30)

    def test_all_public_registered_assistants_have_schemas_and_execute_validation(self):
        assistants = self.request("/assistants/search", {"limit": 100})
        self.assertEqual(7, len(assistants))
        for assistant in assistants:
            operation = assistant["graph_id"]
            with self.subTest(operation=operation):
                schema = self.request(f"/assistants/{assistant['assistant_id']}/schemas")
                self.assertIn("invocation", schema["input_schema"]["properties"])
                _, state = self.run_graph(invocation(operation, data={"invalid_field": True}))
                self.assertEqual("blocked", state["result"]["status"], state)

    def test_direct_execution_and_cli_skill_launcher_json_parity(self):
        value = invocation()
        _, direct = self.run_graph(value)
        self.assertEqual("succeeded", direct["result"]["status"], direct)
        for forwarded, launcher in [(False, False), (True, False), (True, True)]:
            with self.subTest(forwarded=forwarded, launcher=launcher):
                result = self.cli(value, forwarded, launcher)
                self.assertEqual(0, result.returncode, result.stderr + result.stdout)
                self.assertEqual(stable(direct["result"]), stable(json.loads(result.stdout)))
                if forwarded:
                    self.assertIn("Concorde Studio thread:", result.stderr)
                    thread = result.stderr.split("Concorde Studio thread: ")[1].split()[0]
                    saved = self.request(f"/threads/{thread}/state")["values"]
                    self.assertEqual(json.loads(result.stdout), saved["result"])

    def test_live_custom_stream_contains_process_stages_and_persisted_result(self):
        value = invocation("concorde-main", data={"task": "Explain transfer"})
        thread = self.request("/threads", {})["thread_id"]
        payload = {"assistant_id": value["operation_id"], "input": {"invocation": value},
                   "stream_mode": ["custom", "updates"]}
        with urlopen(Request(self.base + f"/threads/{thread}/runs/stream", data=json.dumps(payload).encode(),
                             headers={"Content-Type": "application/json"}), timeout=30) as response:
            stream = response.read().decode()
        self.assertIn("event: custom", stream)
        self.assertIn('"agent_started"', stream)
        state = self.request(f"/threads/{thread}/state")["values"]
        self.assertEqual("succeeded", state["result"]["status"], state)
        self.assertEqual(["route", "route", "ask", "synthesize"],
                         [e["stage"] for e in state["events"] if e["event"] == "agent_finished"])
        self.assertEqual("operation_finished", state["events"][-1]["event"])

    def test_describe_policy_stderr_and_error_exit_compatibility(self):
        value = invocation("concorde-main", "describe-policy")
        result = self.cli(value, launcher=True)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        self.assertEqual("described", json.loads(result.stdout)["status"])
        policies = [json.loads(line) for line in result.stderr.splitlines() if line.startswith('{"policies"')]
        self.assertTrue(policies[0]["policies"])
        value["input"]["data"]["unknown"] = True
        local = self.cli(value, forwarded=False)
        remote = self.cli(value)
        self.assertEqual(3, remote.returncode)
        self.assertEqual(stable(json.loads(local.stdout)), stable(json.loads(remote.stdout)))

    def test_wrong_workspace_is_blocked_before_any_operation_event(self):
        _, state = self.run_graph(invocation(), expected_workspace={
            "project_root": str(PACKAGE), "package_root": str(PACKAGE)})
        self.assertEqual("workspace_mismatch", state["result"]["errors"][0]["code"])
        self.assertEqual([], state["events"])
        # Same CLI entry, but its cwd belongs to another workspace.
        result = subprocess.run([sys.executable, str(PACKAGE / "operations/concorde-reflections-triage/operation.py")],
            input=json.dumps(invocation()), text=True, capture_output=True, cwd=PACKAGE,
            env={**os.environ, "CONCORDE_STUDIO_URL": self.base}, timeout=30)
        self.assertEqual(3, result.returncode)
        self.assertEqual("workspace_mismatch", json.loads(result.stdout)["errors"][0]["code"])

    def test_loop_executes_mutations_and_checkpoints_only_inside_fixture_worktree(self):
        thread, state = self.run_graph(invocation("concorde-dev-loop",
            data={**self.change_fixture.task, "specify": False, "run_reviews": False}))
        self.assertEqual("succeeded", state["result"]["status"], state)
        self.assertEqual("ready", state["result"]["output"]["data"]["outcome"])
        phases = [e["stage"] for e in state["events"] if e["event"] == "stage_finished"]
        self.assertIn("validate", phases)
        self.assertEqual("ready", phases[-1])
        self.assertTrue(any(e["event"] == "operation_started" and e["depth"] == 2
                            for e in state["events"]))
        saved = self.request(f"/threads/{thread}/state")["values"]
        self.assertEqual(state["result"], saved["result"])
        self.assertIn("return balance - amount", (self.change_fixture.change / "app/transfer.py").read_text())
        self.assertEqual("def transfer(balance, amount):\n    return balance\n",
                         (self.change_fixture.primary / "app/transfer.py").read_text())

    def test_executor_failure_survives_forwarding_with_events_and_exit_three(self):
        value = invocation("concorde-main", data={"task": "Trigger executor failure"})
        _, state = self.run_graph(value)
        self.assertEqual("failed", state["result"]["status"], state)
        self.assertTrue(any(event["event"] == "agent_failed" for event in state["events"]))
        self.assertEqual("operation_finished", state["events"][-1]["event"])
        result = self.cli(value)
        self.assertEqual(3, result.returncode)
        self.assertEqual(stable(state["result"]), stable(json.loads(result.stdout)))

    def test_invalid_envelope_resets_a_previously_successful_thread(self):
        thread, _ = self.run_graph(invocation())
        state = self.request(f"/threads/{thread}/runs/wait", {
            "assistant_id": "concorde-reflections-triage", "input": {"invocation": {}}})
        self.assertEqual("invalid_input", state["result"]["errors"][0]["code"])
        self.assertIsNone(state["result"]["output"])
        self.assertEqual([], state["events"])
