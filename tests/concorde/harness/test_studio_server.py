"""Opt-in real WorkerProfile Server checks: CONCORDE_TEST_STUDIO=1 with uv's studio group.

Only temporary consumer fixtures run capabilities. No source/primary-worktree state is changed.
Model responses are deterministic; WorkerExecutor admission and compiled policy checks remain real.
These server tests do not substitute for the separate real Pi tool-gate tests.
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

from tests.concorde.spec.support import PACKAGE, project
from tests.concorde.harness.test_studio import invocation, stable, assert_public_inventory
from concorde.spec.verification import verifies
from concorde.spec.contracts import SKILL_NAMES
from concorde.harness.change_worktree import read_change


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
        from tests.concorde.harness.test_worktree_lifecycle import WorktreeLifecycleTests
        cls.change_fixture = WorktreeLifecycleTests()
        cls.change_fixture.setUp()
        cls.addClassCleanup(cls.change_fixture.doCleanups)
        cls.spec_fixture = WorktreeLifecycleTests()
        cls.spec_fixture.setUp()
        cls.addClassCleanup(cls.spec_fixture.doCleanups)
        cls.review_mode = directory / "review-mode.txt"
        cls.review_mode.write_text("success")
        source = directory / "graphs.py"
        source.write_text(
            "from pathlib import Path\n"
            "import json\n"
            "from concorde.spec.contracts import SKILL_NAMES\n"
            "from concorde.harness.studio import build_studio_graph\n"
            "from tests.concorde.spec.support import ModelProcessDouble\n"
            f"review_mode = Path({str(cls.review_mode)!r})\n"
            "def review_response(stage, snapshot, data, cwd):\n"
            "    if stage != 'spec-review':\n"
            "        return\n"
            "    mode = review_mode.read_text()\n"
            "    if mode == 'failed':\n"
            "        raise RuntimeError('controlled reviewer failure')\n"
            "    if mode == 'incomplete':\n"
            "        data.update(status='incomplete', representative_tasks=[], answer='Coverage incomplete.')\n"
            "    if mode == 'blocking':\n"
            "        gap = dict(question='Which limit applies?', blocked_step='Review limit admission', needed_contract='Limit admission')\n"
            "        data.update(status='findings', blockers=[gap], issues=[dict(id='limit', severity='blocking',\n"
            "            target_id=snapshot['target_id'], document='specs/transfer/module.md', contract=gap['needed_contract'],\n"
            "            location=dict(path='specs/transfer/module.md', line=1), problem='Limit is unspecified.',\n"
            "            affected_task=gap['blocked_step'])])\n"
            "double = ModelProcessDouble(review_response)\n"
            "def executor(launch, *, checks=None, report_issue=None):\n"
            "    value = json.loads(launch.context_json)['data']\n"
            "    snapshot = value.get('snapshot', {}).get('data', value)\n"
            "    if snapshot.get('task') == 'Trigger executor failure':\n"
            "        raise RuntimeError('fixture executor failure')\n"
            "    return double.executor(launch, checks=checks, report_issue=report_issue)\n"
            "for op in SKILL_NAMES:\n"
            f"    roots = {{'concorde-dev-loop': {str(cls.change_fixture.change)!r}, 'concorde-specify-loop': {str(cls.spec_fixture.change)!r}}}\n"
            f"    root = Path(roots.get(op, {str(cls.root)!r}))\n"
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
            "assistant_id": value["capability_id"], "input": {"invocation": value, **extra}})
        self.assertNotIn("__error__", state, state)
        return thread, state

    def cli(self, value, forwarded=True):
        argv = [sys.executable, str(PACKAGE / "scripts/run-capability.py"), value["capability_id"]]
        env = {**os.environ}
        env.pop("CONCORDE_STUDIO_URL", None)
        if forwarded:
            env["CONCORDE_STUDIO_URL"] = self.base
        return subprocess.run(argv, input=json.dumps(value), text=True, capture_output=True,
                              cwd=self.root, env=env, timeout=30)

    # Inventory, schemas and admission rejection do not establish successful execution.
    @verifies("scenario.harness.flow-inspection")
    def test_all_public_registered_assistants_have_schemas_and_execute_validation(self):
        assistants = self.request("/assistants/search", {"limit": 100})
        assert_public_inventory(self, [assistant["graph_id"] for assistant in assistants])
        self.assertEqual(len(assistants), len({assistant["assistant_id"] for assistant in assistants}))
        for assistant in assistants:
            capability = assistant["graph_id"]
            with self.subTest(capability=capability):
                schema = self.request(f"/assistants/{assistant['assistant_id']}/schemas")
                self.assertIn("invocation", schema["input_schema"]["properties"])
                _, state = self.run_graph(invocation(capability, data={"invalid_field": True}))
                self.assertEqual("blocked", state["result"]["status"], state)

    @verifies("scenario.harness.flow-inspection")
    def test_flow_topology_expands_over_the_real_viewer_api(self):
        assistants = self.request("/assistants/search", {"limit": 100})
        for assistant in assistants:
            capability = assistant["graph_id"]
            with self.subTest(capability=capability):
                drawing = self.request(f"/assistants/{assistant['assistant_id']}/graph?xray=true")
                nodes = {node["id"] for node in drawing["nodes"]}
                self.assertIn(capability + ":admit_request", nodes)
                self.assertIn(capability + ":execute:select_capability", nodes)
                if capability == "concorde-main":
                    self.assertTrue(any(node.endswith(":discover:expand_context") for node in nodes))
                    self.assertTrue(any(node.endswith(":apply_atomically") for node in nodes))
                if capability == "concorde-dev-loop":
                    self.assertTrue(any(edge["source"].endswith(":review_code")
                                        and edge["target"].endswith(":tasks") for edge in drawing["edges"]))
                if capability == "concorde-specify-loop":
                    self.assertTrue(any(node.endswith(":specify_loop:specify") for node in nodes))
                    self.assertTrue(any(node.endswith(":specify_loop:review_spec") for node in nodes))
                    self.assertFalse(any(node.endswith((":plan", ":tasks", ":implement", ":ready"))
                                         for node in nodes))

    @verifies("scenario.development.execute-capability")
    def test_direct_execution_and_cli_skill_launcher_json_parity(self):
        value = invocation()
        _, direct = self.run_graph(value)
        self.assertEqual("succeeded", direct["result"]["status"], direct)
        self.assertEqual(value["capability_id"] + "-response", direct["result"]["output"]["type_id"])
        for forwarded in (False, True):
            with self.subTest(forwarded=forwarded):
                result = self.cli(value, forwarded)
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
        payload = {"assistant_id": value["capability_id"], "input": {"invocation": value},
                   "stream_mode": ["custom", "updates"]}
        with urlopen(Request(self.base + f"/threads/{thread}/runs/stream", data=json.dumps(payload).encode(),
                             headers={"Content-Type": "application/json"}), timeout=30) as response:
            stream = response.read().decode()
        self.assertIn("event: custom", stream)
        self.assertIn('"agent_started"', stream)
        state = self.request(f"/threads/{thread}/state")["values"]
        self.assertEqual("succeeded", state["result"]["status"], state)
        self.assertEqual(["route", "route"],
                         [e["stage"] for e in state["events"] if e["event"] == "agent_finished"])
        self.assertEqual("capability_finished", state["events"][-1]["event"])

    def test_describe_policy_stderr_and_error_exit_compatibility(self):
        value = invocation("concorde-main", "describe-policy")
        result = self.cli(value)
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
        result = subprocess.run([sys.executable, str(PACKAGE / "scripts/run-capability.py"),
            "concorde-issues"],
            input=json.dumps(invocation()), text=True, capture_output=True, cwd=PACKAGE,
            env={**os.environ, "CONCORDE_STUDIO_URL": self.base}, timeout=30)
        self.assertEqual(3, result.returncode)
        self.assertEqual("workspace_mismatch", json.loads(result.stdout)["errors"][0]["code"])

    @verifies("scenario.development.flow-execution")
    def test_loop_executes_mutations_and_checkpoints_only_inside_fixture_worktree(self):
        primary_transfer = self.change_fixture.primary / "app/transfer.py"
        primary_before = primary_transfer.read_bytes()
        thread, state = self.run_graph(invocation("concorde-dev-loop",
            data={**self.change_fixture.task, "specify": False, "run_reviews": False}))
        self.assertEqual("succeeded", state["result"]["status"], state)
        self.assertEqual("ready", state["result"]["output"]["data"]["outcome"])
        phases = [e["stage"] for e in state["events"] if e["event"] == "stage_finished"]
        self.assertIn("validate", phases)
        self.assertEqual("ready", phases[-1])
        self.assertTrue(any(e["event"] == "capability_started" and e["depth"] == 2
                            for e in state["events"]))
        saved = self.request(f"/threads/{thread}/state")["values"]
        self.assertEqual(state["result"], saved["result"])
        self.assertIn("return balance - amount", (self.change_fixture.change / "app/transfer.py").read_text())
        self.assertEqual(primary_before, primary_transfer.read_bytes())

    @verifies("scenario.development.specify-loop", "scenario.harness.flow-inspection")
    def test_standalone_specify_loop_finishes_spec_only_in_its_own_fixture(self):
        fixture = self.spec_fixture
        def tracked_bytes(root):
            paths = subprocess.run(["git", "ls-files", "-z"], cwd=root,
                                   capture_output=True, check=True).stdout.decode().split("\0")
            return {path: (root / path).read_bytes() for path in paths if path}
        primary_before = tracked_bytes(fixture.primary)
        other_primary_before = tracked_bytes(self.change_fixture.primary)
        other_candidate_before = tracked_bytes(self.change_fixture.change)
        other_lifecycle_before = read_change(self.change_fixture.change, required=True)
        implementation_before = (fixture.change / "app/transfer.py").read_bytes()
        thread, state = self.run_graph(invocation("concorde-specify-loop",
            data={**fixture.task, "run_reviews": True}))
        self.assertEqual("succeeded", state["result"]["status"], state)
        self.assertEqual("concorde-capability-result", state["result"]["type_id"])
        self.assertEqual(3, state["result"]["schema_version"])
        self.assertEqual("concorde-specify-loop", state["result"]["capability_id"])
        self.assertEqual("concorde-specify-loop-response", state["result"]["output"]["type_id"])
        self.assertEqual(2, state["result"]["output"]["schema_version"])
        self.assertEqual("completed", state["result"]["output"]["data"]["outcome"])
        stages = [e["stage"] for e in state["events"] if e["event"] == "agent_finished"]
        self.assertEqual(["route", "specify", "spec-review"], stages)
        started = [e for e in state["events"] if e["event"] == "agent_started"]
        self.assertEqual(3, len({e["invocation_id"] for e in started}))
        self.assertEqual([(e["stage"], e["invocation_id"]) for e in started],
                         [(e["stage"], e["invocation_id"]) for e in state["events"]
                         if e["event"] == "agent_finished"])
        self.assertEqual([], state["result"]["output"]["data"]["checks"])
        self.assertFalse(any(e.get("stage") in {"plan", "tasks", "implement", "implementation",
                                                "validate", "code-review", "ready"}
                             for e in state["events"]))
        change = read_change(fixture.change, required=True)
        self.assertNotEqual("ready", change["status"])
        self.assertFalse(change["targets"].get(fixture.task["target_id"], {}).get("plan"))
        self.assertEqual({"spec": True}, change["review_requirements"][fixture.task["target_id"]])
        self.assertEqual(implementation_before, (fixture.change / "app/transfer.py").read_bytes())
        self.assertEqual(primary_before, tracked_bytes(fixture.primary))
        self.assertEqual(other_primary_before, tracked_bytes(self.change_fixture.primary))
        self.assertEqual(other_candidate_before, tracked_bytes(self.change_fixture.change))
        self.assertEqual(other_lifecycle_before, read_change(self.change_fixture.change, required=True))
        saved = self.request(f"/threads/{thread}/state")["values"]
        self.assertEqual(state["result"], saved["result"])
        self.assertEqual({"invocation", "result", "policies", "events"}, set(saved))
        self.assertEqual(saved, json.loads(json.dumps(saved, allow_nan=False)))
        history = self.request(f"/threads/{thread}/history", {"limit": 100})
        self.assertTrue(history)
        for checkpoint in history:
            values = checkpoint["values"]
            self.assertLessEqual(set(values), {"invocation", "expected_workspace", "result", "policies", "events"})
            self.assertEqual(values, json.loads(json.dumps(values, allow_nan=False)))
            def check_private_keys(value):
                if isinstance(value, dict):
                    self.assertFalse({"session", "snapshot", "context_json", "input_json",
                                      "resolve_context", "node_factory"} & value.keys())
                    for child in value.values():
                        check_private_keys(child)
                elif isinstance(value, list):
                    for child in value:
                        check_private_keys(child)
            check_private_keys(values)

        # Change real fixture bytes so a previously accepted review cannot be reused.
        # The server remains real; only its model response is controlled by this seam.
        document = fixture.change / "specs/transfer/module.md"
        original = document.read_text()
        try:
            for mode in ("failed", "incomplete", "blocking"):
                with self.subTest(review=mode):
                    document.write_text(original + "\nReview fixture revision: " + mode + "\n")
                    self.review_mode.write_text(mode)
                    request = {**fixture.task, "change_id": change["change_id"],
                               "specify": False, "run_reviews": True}
                    _, stopped = self.run_graph(invocation("concorde-specify-loop", data=request))
                    self.assertNotEqual("succeeded", stopped["result"]["status"], stopped)
                    self.assertTrue(any(e.get("stage") == "spec-review"
                                        and e["event"] == "agent_started" for e in stopped["events"]))
                    self.assertFalse(any(e.get("stage") in {"plan", "tasks", "implementation",
                                                            "validate", "code-review", "ready"}
                                         for e in stopped["events"]))
                    current = read_change(fixture.change, required=True)
                    self.assertTrue(current["review_requirements"][fixture.task["target_id"]]["spec"])
                    self.assertNotEqual("ready", current["status"])
                    self.assertEqual(primary_before, tracked_bytes(fixture.primary))
                    self.assertEqual(implementation_before, (fixture.change / "app/transfer.py").read_bytes())
                    _, disabled = self.run_graph(invocation("concorde-specify-loop",
                        data={**request, "run_reviews": False}))
                    self.assertNotEqual("succeeded", disabled["result"]["status"], disabled)
                    self.assertTrue(read_change(fixture.change, required=True)["review_requirements"][fixture.task["target_id"]]["spec"])
                    self.assertFalse(any(e.get("stage") in {"plan", "tasks", "implementation",
                                                            "validate", "code-review", "ready"}
                                         for e in disabled["events"]))
                    self.assertEqual(primary_before, tracked_bytes(fixture.primary))
        finally:
            self.review_mode.write_text("success")

    def test_executor_failure_survives_forwarding_with_events_and_exit_three(self):
        value = invocation("concorde-main", data={"task": "Trigger executor failure"})
        _, state = self.run_graph(value)
        self.assertEqual("failed", state["result"]["status"], state)
        self.assertTrue(any(event["event"] == "agent_failed" for event in state["events"]))
        self.assertEqual("capability_finished", state["events"][-1]["event"])
        result = self.cli(value)
        self.assertEqual(3, result.returncode)
        self.assertEqual(stable(state["result"]), stable(json.loads(result.stdout)))

    def test_invalid_envelope_resets_a_previously_successful_thread(self):
        thread, _ = self.run_graph(invocation())
        state = self.request(f"/threads/{thread}/runs/wait", {
            "assistant_id": "concorde-issues", "input": {"invocation": {}}})
        self.assertEqual("invalid_input", state["result"]["errors"][0]["code"])
        self.assertIsNone(state["result"]["output"])
        self.assertEqual([], state["events"])
