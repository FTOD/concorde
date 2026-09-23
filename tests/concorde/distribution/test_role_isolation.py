"""Real Pi resource/effective-prompt regression; scripted provider, never task delegation."""

from __future__ import annotations

import hashlib
import json
import queue
import subprocess
import threading
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.distribution import installation
from concorde.distribution.build import write_build
from concorde.distribution.prompt_resolver import resolve_role_prompt
from concorde.distribution.session_selection import save_selection, select_session
from tests.concorde.support.pi_prompt_client import (
    PiRpcError,
    PiRun,
    read_records,
    run_prompt,
)
from concorde.spec.verification import verifies
from tests.concorde.support.fake_openai_provider import FakeOpenAIProvider
from tests.concorde.support.paths import REPOSITORY_ROOT

COORDINATOR = ".pi/extensions/concorde-coordinator.ts"
APPEND = ".pi/APPEND_SYSTEM.md"
IDENTITY = "You are the source user session and its coordinator, not a LangGraph node."


def install_fixture(target):
    """Real receipt/ownership transaction; provisioning is covered separately, not claimed here."""
    package = installation.Package(
        REPOSITORY_ROOT, json.loads((REPOSITORY_ROOT / "concorde.json").read_text())
    )
    with (
        patch.object(
            installation,
            "plan_runtime",
            return_value={
                "path": ".concorde/.venv",
                "role": "runtime",
                "action": "unchanged",
                "sha256": "unused",
            },
        ),
        patch.object(
            installation, "provision_runtime", return_value={"path": ".concorde/.venv"}
        ),
    ):
        actions, desired, _ = installation.installation_plan(target, package)
        return installation.apply_plan(target, package, actions, desired)


def replacement_prompts(argv, project, env, session):
    """Exercise documented RPC new_session/switch_session with the real resource reload path."""
    process = subprocess.Popen(
        argv,
        cwd=project,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    records = queue.Queue()
    threading.Thread(
        target=read_records, args=(process.stdout, records), daemon=True
    ).start()
    events = []

    def send(value):
        process.stdin.write((json.dumps(value) + "\n").encode())
        process.stdin.flush()

    def until(predicate):
        while True:
            kind, line = records.get(timeout=90)
            if kind == "eof":
                raise AssertionError("Pi exited before RPC replacement completed")
            value = json.loads(line)
            events.append(value)
            if value.get("type") == "response" and value.get("success") is False:
                raise AssertionError(value)
            if predicate(value):
                return value

    ids = []
    try:
        for index in range(3):
            if index:
                send(
                    {"id": "replace", "type": "new_session"}
                    if index == 1
                    else {
                        "id": "replace",
                        "type": "switch_session",
                        "sessionPath": str(session),
                    }
                )
                response = until(
                    lambda value: (
                        value.get("id") == "replace" and value.get("type") == "response"
                    )
                )
                assert not response.get("data", {}).get("cancelled")
            send(
                {
                    "id": "prompt",
                    "type": "prompt",
                    "message": "Return fixture complete.",
                }
            )
            until(lambda value: value.get("type") == "agent_settled")
            send({"id": "state", "type": "get_state"})
            ids.append(
                until(
                    lambda value: (
                        value.get("id") == "state" and value.get("type") == "response"
                    )
                )["data"]["sessionId"]
            )
        process.stdin.close()
        process.wait(timeout=15)
        assert ids[0] == ids[2] and ids[0] != ids[1], ids
        return PiRun(
            events=events,
            stderr=process.stderr.read().decode(),
            exit_code=process.returncode,
        )
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()


class ConsumerInstallRoleTests(unittest.TestCase):
    @verifies("scenario.session.task-subagents")
    def test_consumer_install_update_preserve_user_append_bytes_and_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            append = root / APPEND
            append.parent.mkdir()
            append.write_bytes(b"USER-APPEND\r\nIndependent consumer instructions.\r\n")
            append.chmod(0o640)
            original = append.read_bytes()
            self.assertEqual("installed", install_fixture(root))
            self.assertEqual("unchanged", install_fixture(root))
            self.assertEqual(original, append.read_bytes())
            self.assertEqual(0o640, append.stat().st_mode & 0o777)
            receipt = json.loads((root / installation.RECEIPT_PATH).read_text())
            self.assertNotIn(APPEND, {r["path"] for r in receipt["outputs"]})
            self.assertFalse((root / COORDINATOR).exists())
            self.assertFalse((root / ".pi/agents/maintenance-worker.md").exists())
            for source_only in (
                ".concorde/framework/prompts/task-subagent/source",
                ".concorde/framework/prompts/user-session",
            ):
                self.assertFalse((root / source_only).exists())


@unittest.skipUnless(shutil.which("pi"), "real Pi is required")
class EffectiveRolePromptTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="concorde-role-prompt-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / "source"
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
                self.source / directory,
                ignore=shutil.ignore_patterns("node_modules", "__pycache__"),
            )
        write_build(self.source)
        (self.source / ".venv").symlink_to(Path(sys.prefix), target_is_directory=True)
        self.selection = self.source / ".concorde/work/pi-selection.json"
        save_selection(
            self.source,
            self.selection,
            select_session(
                self.source,
                mode="test",
                pi_entry=self.source / "generated/session/pi/concorde-session.ts",
                runtime=self.source / "scripts/run-operation.py",
            ),
        )
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

    def run_role(self, project, role, session, *, binding=True, replacements=False):
        pi = shutil.which("pi")
        with FakeOpenAIProvider(
            [{"text": "fixture complete"}] * (3 if replacements else 1)
        ) as provider:
            (self.agent / "models.json").write_text(
                json.dumps(
                    {
                        "providers": {
                            "fake": {
                                "baseUrl": provider.base_url,
                                "api": "openai-completions",
                                "apiKey": "fixture",
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
            }
            if binding and project == self.source and role == "tester":
                env["PI_SUBAGENT_EXTENSION_BINDINGS"] = json.dumps(
                    {"concorde/1": {"selection": str(self.selection)}}
                )
            argv = [
                pi,
                "--mode",
                "rpc",
                "--session",
                str(session),
                "--approve",
                "--offline",
                "--no-skills",
                "--no-prompt-templates",
                "--no-themes",
                "--model",
                "fake/fake-model",
            ]
            if role != "user-session":
                definition = project / f".pi/agents/{role}.md"
                _, front, body = definition.read_text().split("---", 2)
                fields = dict(
                    line.split(": ", 1)
                    for line in front.strip().splitlines()
                    if ": " in line
                )
                self.assertEqual("replace", fields["systemPromptMode"])
                for key in (
                    "inheritProjectContext",
                    "inheritGlobalContext",
                    "inheritSkills",
                ):
                    self.assertEqual("false", fields[key])
                prompt = self.root / f"{role}-system.md"
                prompt.write_text(body)
                argv += [
                    "--no-context-files",
                    "--no-extensions",
                    "--system-prompt",
                    str(prompt),
                    "--tools",
                    fields["tools"].replace(" ", ""),
                ]
                for extension in fields["extensions"].split(", "):
                    argv += ["-e", str((definition.parent / extension).resolve())]
            # The user session uses normal discovery/default activation. An explicit --tools read
            # ceiling would intentionally exclude the new model-callable brief tool.
            run = (
                replacement_prompts(argv, project, env, session)
                if replacements
                else run_prompt(
                    argv,
                    cwd=str(project),
                    env=env,
                    message="Return fixture complete.",
                    timeout=90,
                )
            )
            self.assertEqual(
                3 if replacements else 1, len(provider.requests), run.stderr
            )
            if replacements:
                for observed in provider.requests:
                    effective = "\n".join(
                        m["content"]
                        for m in observed["messages"]
                        if m["role"] == "system"
                    )
                    self.assertEqual(
                        role == "user-session" and project == self.source,
                        IDENTITY in effective,
                    )
                    self.assertEqual(
                        role == "user-session" and project == self.source,
                        ".concorde/todos/" in effective,
                    )
            for observed in provider.requests:
                names = {t["function"]["name"] for t in observed.get("tools", [])}
                self.assertEqual(
                    role == "user-session" and project == self.source,
                    "update_task_brief" in names,
                )
            request = provider.requests[-1]
        system = "\n".join(
            m["content"] for m in request["messages"] if m["role"] == "system"
        )
        entries = [json.loads(line) for line in session.read_text().splitlines()]
        spans = [
            e["data"] for e in entries if e.get("customType") == "concorde.timing.v1"
        ]
        self.assertTrue(spans, "actual observer must persist records")
        self.assertEqual({role}, {s["metadata"]["role"] for s in spans})
        self.assertTrue(any(s["name"] == "session.request_roundtrip" for s in spans))
        print(
            json.dumps(
                {
                    "case": f"{project.name}/{role}",
                    "session": session.stem,
                    "system_sha256": hashlib.sha256(system.encode()).hexdigest(),
                    "coordinator_present": IDENTITY in system,
                    "observer_role": role,
                    "spans": len(spans),
                }
            )
        )
        return (
            system,
            {t["function"]["name"] for t in request.get("tools", [])},
            entries[0]["id"],
        )

    @verifies(
        "scenario.session.task-subagents",
        "scenario.session.todo-collection",
    )
    def test_source_user_session_and_child_effective_prompts_fresh_and_resumed(self):
        identities = {
            "user-session": IDENTITY,
            "maintenance-worker": "# Source maintenance worker",
            "tester": "# Independent tester",
        }
        for role in identities:
            with self.subTest(role=role):
                first = self.root / f"{role}-first.jsonl"
                fresh = self.root / f"{role}-new.jsonl"
                ids = []
                for session in (first, fresh, first):
                    system, tools, identity = self.run_role(self.source, role, session)
                    ids.append(identity)
                    self.assertIn(identities[role], system)
                    for other in ("maintenance-worker", "tester"):
                        if role != other:
                            self.assertNotIn(identities[other], system)
                    if role == "tester":
                        self.assertIn("## Concorde", system)
                        self.assertIn(
                            "- concorde-validate:", system
                        )  # Actual bound catalog loading, not just observer registration.
                    self.assertEqual(role == "user-session", IDENTITY in system)
                    self.assertEqual(
                        role == "user-session", ".concorde/todos/" in system
                    )
                    self.assertEqual(
                        1 if role == "user-session" else 0,
                        system.count("# Concorde source coordinator"),
                    )
                    self.assertNotIn("concorde", tools)
                    if role == "tester":
                        self.assertIn("test_command", tools)
                        self.assertTrue(
                            {"bash", "write", "edit", "subagent"}.isdisjoint(tools)
                        )
                self.assertEqual(ids[0], ids[2])
                self.assertNotEqual(ids[0], ids[1])

    @verifies("scenario.session.task-subagents")
    def test_installed_user_session_generic_and_tester_isolated_with_user_append(self):
        consumer = self.root / "consumer"
        consumer.mkdir()
        install_fixture(consumer)
        append = consumer / APPEND
        append.write_text("USER-APPEND: retain this unrelated consumer guidance.\n")
        install_fixture(consumer)
        for role in ("user-session", "tester"):
            for phase in ("first", "new", "first"):
                system, _, _ = self.run_role(
                    consumer, role, self.root / f"consumer-{role}-{phase}.jsonl"
                )
                self.assertNotIn(IDENTITY, system)
                self.assertNotIn(".concorde/todos/", system)
                self.assertIn(
                    "USER-APPEND", system
                )  # Real append discovery remains active, not masked by the fixture.
                if role == "user-session":
                    self.assertIn("## Concorde", system)
                else:
                    self.assertIn("# Independent tester", system)

    @verifies("scenario.session.task-subagents")
    def test_rpc_new_and_switch_session_reload_role_safe_resources(self):
        for role in ("user-session", "maintenance-worker", "tester"):
            self.run_role(
                self.source, role, self.root / f"rpc-{role}.jsonl", replacements=True
            )
        consumer = self.root / "consumer"
        consumer.mkdir()
        install_fixture(consumer)
        self.run_role(
            consumer,
            "tester",
            self.root / "rpc-consumer-tester.jsonl",
            replacements=True,
        )

    @verifies("scenario.session.task-subagents")
    def test_negative_control_reproduces_unconditional_append_leak(self):
        (self.source / APPEND).write_text(
            resolve_role_prompt(
                REPOSITORY_ROOT, "prompts/user-session/source/coordinator.md"
            ).body
        )
        system, _, _ = self.run_role(
            self.source, "maintenance-worker", self.root / "legacy.jsonl"
        )
        self.assertIn(IDENTITY, system)
        (self.source / APPEND).unlink()
        system, _, _ = self.run_role(
            self.source, "maintenance-worker", self.root / "repaired.jsonl"
        )
        self.assertNotIn(IDENTITY, system)

    @verifies(
        "scenario.session.select",
        "scenario.session.task-subagents",
        "scenario.session.tester-independent",
    )
    def test_missing_binding_still_blocks_private_entry_loading(self):
        with self.assertRaises(PiRpcError) as raised:
            self.run_role(
                self.source, "tester", self.root / "unbound.jsonl", binding=False
            )
        self.assertIn(
            "requires explicit candidate selection", raised.exception.run.stderr
        )
        self.assertEqual([], raised.exception.run.tool_results)
