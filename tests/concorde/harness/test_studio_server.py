"""Opt-in actual Studio API for the genuine optional Operation, not capability graph mirrors.

CONCORDE_TEST_STUDIO=1 uses the locked studio dependency group. A separate trusted service fixture
returns typed data; it is not native/model evidence. No provider, Agent or author task is launched.
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
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from concorde.spec.verification import verifies
from tests.concorde.harness.test_operation_node import _stage_context
from tests.concorde.spec.support import PACKAGE
from tests.concorde.support.environment import child_environment


@unittest.skipUnless(
    os.environ.get("CONCORDE_TEST_STUDIO") == "1", "requires optional Studio server"
)
class StudioServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="concorde-studio-operation-")
        cls.addClassCleanup(cls.temp.cleanup)
        directory = Path(cls.temp.name)
        fixture = directory / "trusted_service.py"
        fixture.write_text("""from concorde.harness.studio import build_studio_graph
from concorde.spec.typed_data import typed
async def trusted_service(context):
    return typed('concorde-agent-stage-result',dict(context_id=context['data']['snapshot']['data']['context_id'],outcome='completed',answer='Explicit trusted service fixture; not model evidence',blockers=[],documents=[],plan='Typed fixture plan',tasks=[]))
operation=build_studio_graph('planner',launcher=trusted_service)
""")
        source_config = PACKAGE / "generated/langgraph.json"
        config = json.loads(source_config.read_text())
        assert set(config["graphs"]) == {"terminal-agent-operation"}, config
        cls.assert_config = config
        # The CLI resolves graph and dependency paths from the selected package cwd.
        config["dependencies"] = [
            str((PACKAGE / p).resolve()) for p in config["dependencies"]
        ]
        config["graphs"] = {
            key: str((PACKAGE / value.split(":")[0]).resolve())
            + ":"
            + value.split(":")[1]
            for key, value in config["graphs"].items()
        }
        config["graphs"]["fixture-agent-operation"] = str(fixture) + ":operation"
        file = directory / "langgraph.json"
        file.write_text(json.dumps(config))
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        cls.base = f"http://127.0.0.1:{port}"
        cls.log = (directory / "server.log").open("w+")
        cls.addClassCleanup(cls.log.close)
        environment = child_environment(
            LANGSMITH_TRACING="false", LANGGRAPH_CLI_NO_ANALYTICS="1"
        )
        for key in ("PYTHONPATH", "CONCORDE_STUDIO_URL"):
            environment.pop(key, None)
        cls.server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "langgraph_cli",
                "dev",
                "--config",
                str(file),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--no-browser",
                "--no-reload",
            ],
            cwd=directory,
            env=environment,
            stdout=cls.log,
            stderr=subprocess.STDOUT,
        )
        cls.addClassCleanup(cls.stop)
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            try:
                cls.request("/ok")
                return
            except (OSError, ValueError):
                if cls.server.poll() is not None:
                    break
                time.sleep(0.2)
        cls.log.seek(0)
        raise AssertionError(cls.log.read())

    @classmethod
    def stop(cls):
        if cls.server.poll() is None:
            cls.server.terminate()
            try:
                cls.server.wait(timeout=15)
            except subprocess.TimeoutExpired:
                cls.server.kill()
                cls.server.wait()

    @classmethod
    def request(cls, path, body=None):
        request = Request(
            cls.base + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        except HTTPError as error:
            raise AssertionError(error.read().decode()) from error

    def run_graph(self, name, data):
        thread = self.request("/threads", {})["thread_id"]
        run = self.request(
            f"/threads/{thread}/runs", {"assistant_id": name, "input": data}
        )
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            run = self.request(f"/threads/{thread}/runs/{run['run_id']}")
            if run["status"] not in {"pending", "running"}:
                break
            time.sleep(0.1)
        return run, self.request(f"/threads/{thread}/state")

    @verifies(
        "scenario.harness.optional-operation", "scenario.harness.graph-inspection"
    )
    def test_default_export_is_real_inspectable_and_has_no_implicit_service(self):
        graph = self.request("/assistants/terminal-agent-operation/graph?xray=1")
        self.assertEqual(
            {node["id"] for node in graph["nodes"]},
            {"__start__", "terminal_agent", "__end__"},
        )
        assistant = self.request(
            "/assistants/search", {"graph_id": "terminal-agent-operation"}
        )[0]
        schemas = self.request("/assistants/" + assistant["assistant_id"] + "/schemas")
        self.assertIn("input_schema", schemas)
        context = _stage_context()["data"]
        context["snapshot"]["data"]["phase"] = "context-solve"
        run, state = self.run_graph("terminal-agent-operation", context)
        self.assertEqual(run["status"], "error", run)
        self.log.flush()
        self.log.seek(0)
        self.assertIn("inspection only", self.log.read())

    @verifies("scenario.harness.optional-operation")
    def test_explicit_async_service_executes_typed_state_and_rejects_invalid_input(
        self,
    ):
        run, state = self.run_graph("fixture-agent-operation", _stage_context()["data"])
        self.assertEqual(run["status"], "success", run)
        self.assertEqual(state["values"]["plan"], "Typed fixture plan")
        run, state = self.run_graph(
            "fixture-agent-operation", {"snapshot": {"foreign": True}}
        )
        self.assertEqual(run["status"], "error", run)
