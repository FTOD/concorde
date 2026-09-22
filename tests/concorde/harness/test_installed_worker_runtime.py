"""Installed low-level diagnostic driver -> admitted relay -> sandboxed Pi RPC, with no live model.

The installer, managed interpreter, host-created candidate, worker profiles, tool extension,
TypeBox and bubblewrap all run for real. Only the loopback model's responses are scripted.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.distribution.local_installation import verify_installation
from concorde.harness.pi_worker import (
    PiWorkerRuntime,
    WorkerExecutionError,
    WorkerLaunch,
)
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.harness.test_pi_worker import installed_pi
from tests.concorde.spec.support import project
from tests.concorde.support.fake_openai_provider import FakeOpenAIProvider
from tests.concorde.support.environment import scrub_selection
from tests.concorde.support.managed_runtime import independent_runtime_environment
from tests.concorde.support.operation_json import configure
from tests.concorde.support.paths import REPOSITORY_ROOT


class ScriptedWorkerProvider(FakeOpenAIProvider):
    @staticmethod
    def _chunks(body, turn, number):
        if turn.get("submit"):
            message = next(
                m["content"] for m in body["messages"] if m["role"] == "user"
            )
            if isinstance(message, list):
                message = next(m["text"] for m in message if m["type"] == "text")
            context = json.loads(message)["data"]
            snapshot = context["snapshot"]["data"]
            phase = snapshot["phase"]
            data = {
                "context_id": snapshot["context_id"],
                "outcome": "sufficient" if phase == "context-solve" else "completed",
                "answer": "Scripted offline runtime integration; not semantic model evidence.",
                "blockers": [],
                "documents": [],
                "plan": "Implement and check the pure transfer contract."
                if phase == "plan"
                else "",
                "tasks": [],
            }
            if phase == "tasks":
                data["tasks"] = [
                    {
                        "id": "task.transfer",
                        "target_id": snapshot["target_id"],
                        "description": "Implement transfer.",
                        "acceptance": "Valid amounts subtract; invalid amounts raise ValueError.",
                        "complete": False,
                    }
                ]
            if phase == "implementation":
                task_input = next(
                    v["data"]
                    for v in snapshot["stage_inputs"]
                    if v["type_id"] == "concorde-implementation-task"
                )
                data["tasks"] = [
                    {**task, "complete": True} for task in task_input["tasks"]
                ]
            if phase == "code-review":
                review = context["review"]["data"]
                data = {
                    "context_id": snapshot["context_id"],
                    "input_digest": review["input_digest"],
                    "review_mode": "code",
                    "status": "no_findings",
                    "representative_tasks": [snapshot["task"]],
                    "issues": [],
                    "answer": "Scripted read-only runtime integration, not semantic review.",
                }
            turn = {"tool": "submit_result", "arguments": data}
        return FakeOpenAIProvider._chunks(body, turn, number)


class InstalledWorkerRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            installed_pi(), "real Pi is required for installed runtime acceptance"
        )
        temporary = tempfile.TemporaryDirectory(
            prefix="concorde-installed-worker-test-"
        )
        self.addCleanup(temporary.cleanup)
        # In-process verification launches the installed consumer runtime from os.environ; an
        # ambient candidate selection must not cross into that consumer for the whole test.
        scrubbed = patch.dict(os.environ, scrub_selection(os.environ), clear=True)
        scrubbed.start()
        self.addCleanup(scrubbed.stop)
        self.root = Path(temporary.name)
        self.primary = self.root / "consumer"
        self.primary.mkdir()
        project(self.primary)
        self.configuration = typed(
            "concorde-operation-configuration",
            {"model": "fake/fake-model", "timeout_seconds": 60},
        )
        configure(self.primary, self.configuration)
        (self.primary / ".gitignore").write_text(
            ".concorde/framework/\n.concorde/.venv/\n.concorde/install*\n"
            ".concorde/status/\n.concorde/runs/\n.concorde/work/\n.pi/\n"
        )
        self.git(self.primary, "init", "-q", "-b", "main")
        self.git(self.primary, "config", "user.email", "runtime-test@example.invalid")
        self.git(self.primary, "config", "user.name", "Runtime test")
        # Real independently provisioned wheels and locked TypeBox, never forwarding assets.
        pi = Path(installed_pi())
        self.environment = {
            **independent_runtime_environment(self.root, REPOSITORY_ROOT),
            "PATH": str(pi.parent) + os.pathsep + os.environ.get("PATH", ""),
            "CONCORDE_STUDIO_URL": "",
        }
        install = subprocess.run(
            [
                sys.executable,
                str(REPOSITORY_ROOT / "scripts/install-concorde.py"),
                "--target",
                str(self.primary),
                "--apply",
                "--format",
                "json",
            ],
            env=self.environment,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(0, install.returncode, install.stdout + install.stderr)
        self.framework = self.primary / ".concorde/framework"
        self.git(self.primary, "add", "-A")
        self.git(
            self.primary, "commit", "-qm", "consumer fixture without ignored runtime"
        )
        self.assertEqual(
            "",
            self.git(
                self.primary, "ls-files", ".concorde/framework", ".concorde/.venv"
            ).strip(),
        )
        (self.primary / "primary-secret.txt").write_text("PRIMARY-SECRET-CONTENT")
        self.other = self.root / "other"
        self.git(self.primary, "worktree", "add", "-qb", "other", str(self.other))
        (self.other / "other-secret.txt").write_text("OTHER-SECRET-CONTENT")
        self.credentials = self.root / "offline-config"
        self.credentials.mkdir(mode=0o700)
        self.environment["PI_CODING_AGENT_DIR"] = str(self.credentials)
        self.task = {
            "target_id": "service.transfer",
            "task": "Implement the pure transfer contract",
        }

    def git(self, root, *args):
        return subprocess.run(
            ["git", "-C", str(root), *args], check=True, text=True, capture_output=True
        ).stdout

    def call(self, operation, turns, *, local=False, expected="succeeded"):
        root = self.candidate if local else self.primary
        with ScriptedWorkerProvider(turns) as provider:
            (self.credentials / "models.json").write_text(
                json.dumps(
                    {
                        "providers": {
                            "fake": {
                                "baseUrl": provider.base_url,
                                "api": "openai-completions",
                                "apiKey": "offline-test",
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
            value = {
                "type_id": "concorde-operation-invocation",
                "schema_version": 3,
                "operation_id": operation,
                "mode": "execute",
                "configuration": None,
                "input": typed(operation + "-request", self.task),
            }
            completed = subprocess.run(
                [
                    str(root / ".concorde/.venv/bin/python"),
                    str(
                        REPOSITORY_ROOT
                        / "tests/concorde/support/installed_legacy_driver.py"
                    ),
                    operation,
                ],
                input=json.dumps(value),
                cwd=root,
                env=self.environment,
                capture_output=True,
                text=True,
                timeout=240,
            )
        self.assertIn(completed.returncode, {0, 3}, completed.stderr)
        result = json.loads(completed.stdout)
        # Register cleanup even on a failed relayed launch. This is only our disposable
        # fixture candidate, never a maintenance worktree or retained acceptance evidence.
        workspace = result.get("workspace") or {}
        if (
            workspace.get("path")
            and workspace["path"] != str(self.primary)
            and not hasattr(self, "candidate")
        ):
            self.candidate = Path(workspace["path"])
            self.addCleanup(self.remove_fixture_candidate)
        self.assertEqual(expected, result["status"], result)
        if turns:
            self.assertTrue(provider.requests, "no real Pi provider request")
        return result, [
            request
            for request in provider.requests
            if any(
                t["function"]["name"] == "submit_result"
                for t in request.get("tools", [])
            )
        ]

    @verifies("scenario.harness.local-installation-failure")
    def test_failed_acquisition_preserves_owner_and_explicit_retry_reuses_candidate(
        self,
    ):
        wheels = self.environment["PIP_FIND_LINKS"]
        empty = self.root / "empty-wheelhouse"
        empty.mkdir()
        self.environment["PIP_FIND_LINKS"] = str(empty)
        result, requests = self.call("concorde-plan", [], expected="blocked")
        self.assertEqual(
            [], requests, "no terminal worker before complete installation"
        )
        self.assertEqual("local_installation_required", result["errors"][0]["code"])
        change_id = result["workspace"]["change_id"]
        candidate = self.candidate
        self.task["change_id"] = change_id
        status_path = self.primary / f".concorde/status/{change_id}.json"
        state = json.loads(status_path.read_text())
        self.assertEqual("blocked", state["status"])
        self.assertEqual("local_installation_required", state["outcome"])
        self.assertEqual(self.task["task"], state["task"])
        self.assertFalse((candidate / ".concorde/install.json").exists())
        self.assertFalse((candidate / ".concorde/.venv").exists())
        self.environment["PIP_FIND_LINKS"] = wheels
        # Resume does not silently repair even though the primary is fully functional.
        result, requests = self.call("concorde-plan", [], expected="blocked")
        self.assertEqual([], requests)
        self.assertEqual(str(candidate), result["workspace"]["path"])
        repair = subprocess.run(
            [
                sys.executable,
                str(self.framework / "scripts/install-concorde.py"),
                "--target",
                str(candidate),
                "--preserve-project",
                "--apply",
                "--format",
                "json",
            ],
            env=self.environment,
            text=True,
            capture_output=True,
            timeout=120,
        )
        self.assertEqual(0, repair.returncode, repair.stdout + repair.stderr)
        result, _ = self.call("concorde-plan", [{"submit": True}, {"submit": True}])
        self.assertEqual(change_id, result["workspace"]["change_id"])
        self.assertEqual(str(candidate), result["workspace"]["path"])
        local = verify_installation(candidate)
        receipt = local.receipt.read_bytes()
        for corrupt in (None, b"{}"):
            if corrupt is None:
                local.receipt.unlink()
            else:
                local.receipt.write_bytes(corrupt)
            result, requests = self.call(
                "concorde-context-solve", [], local=True, expected="blocked"
            )
            self.assertEqual("local_installation_required", result["errors"][0]["code"])
            self.assertEqual([], requests)
            local.receipt.write_bytes(receipt)
        # A valid provider runtime is not an execution fallback for either failed case.
        primary = verify_installation(self.primary)
        self.assertNotEqual(primary.python, local.python)
        self.assertFalse((candidate / ".concorde/status").exists())
        self.assertFalse((candidate / ".concorde/runs").exists())
        verify_installation(candidate)

    def remove_fixture_candidate(self):
        self.git(self.primary, "worktree", "remove", "--force", str(self.candidate))
        self.candidate.parent.rmdir()

    def probe(self, review=False):
        # Shell execution, not the in-process read gate, must enforce these masks and writes.
        code = f"""
import glob, json, subprocess
from pathlib import Path
out = {{}}
for name, path in {repr({"primary_secret": str(self.primary / "primary-secret.txt"), "primary_source": str(self.primary / "app/transfer.py"), "primary_extension": str(self.framework / "pi/extensions/concorde-worker.ts"), "other_secret": str(self.other / "other-secret.txt")})}.items():
    try: Path(path).read_bytes(); out[name] = "LEAK"
    except OSError: out[name] = "masked"
asset = Path({str(self.candidate / ".concorde/framework/pi/extensions/concorde-worker.ts")!r})
dep = Path({str(self.candidate / ".concorde/.venv/share/concorde/pi/node_modules/typebox")!r})
out["local_extension"] = asset.is_file()
out["typebox"] = json.loads((dep / "package.json").read_text())["version"]
resolved = str(dep / "build/index.mjs")
loaded = subprocess.check_output(["node", "--input-type=module", "-e", "const m = await import(process.argv[1]); console.log(m.Type.Object({{}}).type)", resolved], text=True).strip()
out["typebox_loaded"] = loaded == "object"
# The actual Pi worker imported this same module: missing it must fail startup.
out["local_runtime"] = Path({str(self.candidate / ".concorde/.venv/bin/python")!r}).is_file()
for name, path in {{"extension_write": asset, "dependency_write": dep / "build/index.mjs", "ungranted_write": Path("secret.py"), "code_write": Path("app/transfer.py")}}.items():
    if name == "code_write" and not {review!r}: continue
    try: path.open("ab").close(); out[name] = "WRITABLE"
    except OSError: out[name] = "readonly"
print(json.dumps(out))
"""
        return {
            "tool": "bash",
            "arguments": {"command": "python3 -c " + shlex.quote(code)},
        }

    @verifies(
        "scenario.harness.local-installation",
        "scenario.harness.worktree-relay",
        "scenario.harness.worker-sandbox",
        "scenario.harness.pi-worker-gate",
    )
    def test_ignored_installed_runtime_launches_programmer_and_readonly_reviewer(self):
        result, _ = self.call("concorde-plan", [{"submit": True}, {"submit": True}])
        local = verify_installation(self.candidate)
        self.assertEqual(str(self.framework), local.provider_root)
        self.assertEqual(self.candidate / ".concorde/.venv/bin/python", local.python)
        receipt_before = local.receipt.read_bytes()
        marker = self.candidate / ".concorde/.venv/.concorde-runtime.json"
        marker_before = marker.read_bytes()
        self.task["change_id"] = result["workspace"]["change_id"]
        self.call("concorde-tasks", [{"submit": True}])
        implementation = 'def transfer(balance, amount):\n    if amount <= 0 or amount > balance:\n        raise ValueError("invalid transfer")\n    return balance - amount\n'
        result, requests = self.call(
            "concorde-implement",
            [
                self.probe(),
                {"tool": "read", "arguments": {"path": "app/ledger.py"}},
                {
                    "tool": "write",
                    "arguments": {"path": "secret.py", "content": "forbidden"},
                },
                {
                    "tool": "write",
                    "arguments": {"path": "app/transfer.py", "content": implementation},
                },
                {"submit": True},
            ],
        )
        self.assertEqual(
            implementation, (self.candidate / "app/transfer.py").read_text()
        )
        self.assertNotEqual(
            implementation, (self.primary / "app/transfer.py").read_text()
        )
        self.assert_probe(requests)
        messages = json.dumps(requests[-1]["messages"])
        self.assertIn("outside the read grant", messages)
        self.assertIn("outside the write grant", messages)
        _, requests = self.call(
            "concorde-code-review",
            [
                self.probe(review=True),
                {"tool": "read", "arguments": {"path": "app/transfer.py"}},
                {
                    "tool": "write",
                    "arguments": {"path": "app/transfer.py", "content": "forbidden"},
                },
                {"submit": True},
            ],
            local=True,
        )
        self.assert_probe(requests, review=True)
        self.assertEqual(
            implementation, (self.candidate / "app/transfer.py").read_text()
        )
        tools = {t["function"]["name"] for t in requests[0]["tools"]}
        self.assertFalse(tools & {"write", "edit", "concorde", "subagent"})
        self.assertFalse((self.candidate / ".concorde/runs").exists())
        self.assertTrue((self.primary / ".concorde/runs").is_dir())
        self.assertFalse((self.candidate / ".concorde/status").exists())
        self.assertEqual(receipt_before, local.receipt.read_bytes())
        self.assertEqual(marker_before, marker.read_bytes())
        runs = [
            json.loads(p.read_text())
            for p in (self.primary / ".concorde/runs").glob("*/run.json")
        ]
        candidate_runs = [
            r for r in runs if r["runtime"]["root"] == str(local.framework)
        ]
        self.assertGreaterEqual(len(candidate_runs), 4)
        self.assertTrue(
            all(r["runtime"]["python"] == str(local.python) for r in candidate_runs)
        )
        # Actual Pi startup must import the local dependency, not its bundled bare-name alias.
        entry = (
            self.candidate
            / ".concorde/.venv/share/concorde/pi/node_modules/typebox/build/index.mjs"
        )
        held = entry.with_suffix(".held")
        entry.rename(held)
        try:
            runtime = PiWorkerRuntime(
                local.framework,
                pi_executable=installed_pi(),
                environment=self.environment,
            )
            with self.assertRaises(WorkerExecutionError) as failed:
                runtime(
                    WorkerLaunch(
                        worker="fixture",
                        workspace=str(self.candidate),
                        system_prompt="Fixture",
                        message="No model should start",
                        result_schema={"type": "object"},
                        tools=("submit_result",),
                        model="fake/fake-model",
                        timeout_seconds=15,
                    )
                )
            self.assertIsNotNone(failed.exception.run)
            self.assertIn(str(entry), failed.exception.run.stderr)
        finally:
            held.rename(entry)
        verify_installation(self.candidate)

    def assert_probe(self, requests, review=False):
        content = next(
            m["content"] for m in requests[1]["messages"] if m["role"] == "tool"
        )
        if isinstance(content, list):
            content = next(m["text"] for m in content if m["type"] == "text")
        observed = json.loads(content)
        expected = {
            "primary_secret": "masked",
            "primary_source": "masked",
            "primary_extension": "masked",
            "other_secret": "masked",
            "local_extension": True,
            "local_runtime": True,
            "typebox": "1.1.38",
            "typebox_loaded": True,
            "extension_write": "readonly",
            "dependency_write": "readonly",
            "ungranted_write": "readonly",
        }
        if review:
            expected["code_write"] = "readonly"
        self.assertEqual(expected, observed)


if __name__ == "__main__":
    unittest.main()
