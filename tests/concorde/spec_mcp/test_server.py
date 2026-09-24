"""The Spec MCP server over a real stdio MCP connection to ``concorde spec-mcp``."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from concorde.spec.grants import grant
from concorde.spec.repository import SpecRepository
from concorde.spec.errors import ERROR_SCHEMA
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from tests.concorde.spec.test_grants import document, realization
from tests.concorde.support.environment import child_environment
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.spec_project import SpecProject, sync_registry

COMMAND = [sys.executable, str(REPOSITORY_ROOT / "scripts/concorde.py"), "spec-mcp"]
TOOLS = {"boundary", "modules", "module", "context", "impact", "validate"}


class Client:
    """A minimal MCP client: initialize, answer ``roots/list``, call tools."""

    def __init__(self, test, environment, roots=None):
        self.roots = roots
        self.process = subprocess.Popen(
            COMMAND,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            env=environment,
        )
        test.addCleanup(self.close)
        self.next = 0
        capabilities = {"roots": {"listChanged": False}} if roots is not None else {}
        self.initialized = self.request(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": capabilities,
                "clientInfo": {"name": "test", "version": "0"},
            },
        )
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.close()
            self.process.wait(10)
        self.process.stdout.close()

    def send(self, message):
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def request(self, method, params=None):
        self.next += 1
        identity = self.next
        self.send(
            {"jsonrpc": "2.0", "id": identity, "method": method, "params": params or {}}
        )
        while True:
            message = json.loads(self.process.stdout.readline())
            if message.get("method") == "roots/list":
                self.send(
                    {
                        "jsonrpc": "2.0",
                        "id": message["id"],
                        "result": {
                            "roots": [
                                {"uri": Path(root).as_uri(), "name": "root"}
                                for root in self.roots or ()
                            ]
                        },
                    }
                )
                continue
            if message.get("id") == identity:
                return message["result"]

    def call(self, name, **arguments):
        result = self.request("tools/call", {"name": name, "arguments": arguments})
        value = json.loads(result["content"][0]["text"])
        return value, result["isError"]


class SpecMcpTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(os.path.realpath(directory.name)) / "primary"
        self.root.mkdir()
        self.project = SpecProject(self.root)
        for path in ("src/a/one.py", "src/bmod/b.py", "src/shared.py"):
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            (self.root / path).write_text("value = 1\n")
        self.project.module(
            "module.a",
            "specs/a/module.md",
            document(
                "a", "A", [realization("realization.a.code", ["src/a/"])], used=("b",)
            ),
        )
        self.project.module(
            "module.b",
            "specs/b/module.md",
            document("b", "B", [realization("realization.b.code", ["src/bmod/"])]),
        )
        self.project.module(
            "module.d",
            "specs/d/module.md",
            document("d", "D", [realization("realization.d.code", ["src/shared.py"])]),
        )

    def client(self, root=None, roots=None):
        environment = child_environment()
        environment.pop("CLAUDE_PROJECT_DIR", None)
        if root is not None:
            environment["CLAUDE_PROJECT_DIR"] = str(root)
        return Client(self, environment, roots)

    def repository(self, root=None):
        return SpecRepository(root or self.root, REPOSITORY_ROOT)

    def snapshot(self, root=None):
        base = root or self.root
        return {
            path.relative_to(base).as_posix(): path.read_bytes()
            for path in sorted(base.rglob("*"))
            if path.is_file()
        }

    @verifies("scenario.spec-mcp.configured-session")
    def test_a_configured_session_uses_the_project_directory(self):
        client = self.client(root=self.root)
        self.assertIn("tools", client.initialized["capabilities"])
        listed = client.request("tools/list")["tools"]
        self.assertEqual(TOOLS, {tool["name"] for tool in listed})
        value, error = client.call("modules")
        self.assertFalse(error)
        self.assertEqual(
            ["module.a", "module.b", "module.d"], [m["id"] for m in value["modules"]]
        )

    @verifies("scenario.spec-mcp.client-root")
    def test_the_client_root_is_used_without_the_variable(self):
        client = self.client(roots=[self.root])
        value, error = client.call("modules")
        self.assertFalse(error, value)
        self.assertEqual(3, len(value["modules"]))

    @verifies("scenario.spec-mcp.no-root")
    def test_without_a_root_every_call_fails(self):
        other = self.root.parent / "other"
        other.mkdir()
        for roots in (None, [], [self.root, other]):
            with self.subTest(roots=roots):
                client = self.client(roots=roots)
                value, error = client.call("modules")
                self.assertTrue(error)
                self.assertEqual("no_root", value["error"]["code"])

    @verifies("scenario.spec-mcp.boundary")
    def test_boundary_is_spec_cores_grant(self):
        before = self.snapshot()
        value, error = self.client(root=self.root).call(
            "boundary", modules=["module.a"], task_type="implement"
        )
        self.assertFalse(error, value)
        expected = grant(self.repository(), ["module.a"], "implement").value
        self.assertEqual(
            {
                "context_identity": expected["context_identity"],
                "entries": expected["entries"],
            },
            value,
        )
        levels = {entry["path"]: entry["level"] for entry in value["entries"]}
        self.assertEqual("rw", levels["src/a/"])
        self.assertEqual("ro", levels["specs/a/module.md"])
        self.assertEqual("ro", levels["specs/b/module.md"])
        self.assertEqual(before, self.snapshot())

    @verifies("scenario.spec-mcp.boundary-refused")
    def test_a_refused_grant_is_a_tool_error(self):
        value = self.project.metadata("specs/a/module.md")
        for record in value["defines"]:
            if record["id"] == "realization.a.code":
                record["entries"] = ["src/a/", "src/shared.py"]
        self.project.save_metadata("specs/a/module.md", value)
        sync_registry(self.root)
        result, error = self.client(root=self.root).call(
            "boundary", modules=["module.a"], task_type="implement"
        )
        self.assertTrue(error)
        self.assertEqual("shared_file", result["error"]["code"])
        self.assertIn("src/shared.py", result["error"]["message"])
        self.assertIn("module.d", result["error"]["message"])
        self.assertNotIn("entries", result)
        validate(result["error"], ERROR_SCHEMA)
        self.assertIn("every Module that binds it", result["error"]["reason"])
        self.assertTrue(result["error"]["remediation"])

    @verifies("scenario.spec-mcp.queries")
    def test_queries_equal_spec_core(self):
        client = self.client(root=self.root)
        repository = self.repository()
        modules, _ = client.call("modules")
        self.assertEqual(
            [(r["id"], r["entry"]) for r in repository.registry["modules"]],
            [(m["id"], m["entry"]) for m in modules["modules"]],
        )
        module, error = client.call("module", id="module.a")
        self.assertFalse(error, module)
        self.assertEqual(["module.b"], [item["target"] for item in module["uses"]])
        self.assertEqual(["src/a/"], module["realizations"][0]["entries"])
        context, _ = client.call("context", id="module.a")
        self.assertEqual(
            repository.spec_context("module.a").value["sources"], context["sources"]
        )
        impact, _ = client.call("impact", paths=["src/a/one.py", "specs/b/module.md"])
        self.assertEqual(["module.a"], impact["paths"][0]["modules"])
        self.assertEqual(["module.a", "module.b"], impact["paths"][1]["modules"])
        for text in json.dumps([modules, module, context, impact]).split('"'):
            self.assertFalse(text.startswith(str(self.root)), text)

    @verifies("scenario.spec-mcp.validate")
    def test_validate_returns_the_command_envelope(self):
        path = self.root / "specs/a/module.md"
        path.write_text(path.read_text().replace("## Usage", "## Use"))
        before = self.snapshot()
        value, error = self.client(root=self.root).call("validate")
        self.assertFalse(error)
        self.assertEqual(("validate", "invalid"), (value["tool"], value["status"]))
        self.assertTrue(any(f["severity"] == "error" for f in value["findings"]))
        self.assertEqual(before, self.snapshot())

    @verifies("scenario.spec-mcp.current-specs")
    def test_a_spec_change_is_seen_at_once(self):
        client = self.client(root=self.root)
        first, _ = client.call("context", id="module.a")
        path = self.root / "specs/b/module.md"
        path.write_text(path.read_text() + "\nMore explanation.\n")
        second, _ = client.call("context", id="module.a")
        self.assertNotEqual(first["context_identity"], second["context_identity"])
        digests = lambda value: {s["path"]: s["digest"] for s in value["sources"]}  # noqa: E731
        self.assertNotEqual(
            digests(first)["specs/b/module.md"], digests(second)["specs/b/module.md"]
        )

    @verifies("scenario.spec-mcp.worktree-answers")
    def test_two_worktrees_answer_differently(self):
        task = self.root.parent / "task"
        shutil.copytree(self.root, task)
        value = json.loads((task / "specs/a/module.md.json").read_text())
        for record in value["defines"]:
            if record["id"] == "realization.a.code":
                record["entries"] = ["src/a/", "src/extra.py"]
                record["pending"] = ["src/extra.py"]
        (task / "specs/a/module.md.json").write_text(json.dumps(value, indent=2))
        sync_registry(task)
        answers = [
            self.client(root=root).call(
                "boundary", modules=["module.a"], task_type="implement"
            )[0]
            for root in (self.root, task)
        ]
        paths = [{entry["path"] for entry in answer["entries"]} for answer in answers]
        self.assertNotIn("src/extra.py", paths[0])
        self.assertIn("src/extra.py", paths[1])
        self.assertNotEqual(
            answers[0]["context_identity"], answers[1]["context_identity"]
        )

    @verifies("scenario.spec-mcp.outside-root")
    def test_paths_outside_the_root_are_refused(self):
        outside = self.root.parent / "outside.py"
        outside.write_text("secret = 1\n")
        (self.root / "link.py").symlink_to(outside)
        client = self.client(root=self.root)
        for path in ("../outside.py", str(outside), "link.py", "src/../../outside.py"):
            with self.subTest(path=path):
                value, error = client.call("impact", paths=[path])
                self.assertTrue(error)
                self.assertEqual("outside_root", value["error"]["code"])

    @verifies("scenario.spec-mcp.unloadable-specs")
    def test_specs_that_cannot_be_loaded_answer_nothing(self):
        config = json.loads((self.root / ".concorde/config.json").read_text())
        config["protocol"]["digest"] = "sha256:" + "0" * 64
        (self.root / ".concorde/config.json").write_text(json.dumps(config))
        client = self.client(root=self.root)
        for name, arguments in (
            ("modules", {}),
            ("module", {"id": "module.a"}),
            ("context", {"id": "module.a"}),
            ("boundary", {"modules": ["module.a"], "task_type": "test"}),
            ("impact", {"paths": ["src/a/one.py"]}),
        ):
            with self.subTest(tool=name):
                value, error = client.call(name, **arguments)
                self.assertTrue(error)
                self.assertEqual("protocol_mismatch", value["error"]["code"])


if __name__ == "__main__":
    unittest.main()
