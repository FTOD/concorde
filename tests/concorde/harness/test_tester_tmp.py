"""Tester-only private /tmp: real mounted boundary and real nested Pi, no live provider."""

from __future__ import annotations

import json
import os
import queue
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import uuid
from pathlib import Path

from concorde.harness.check_executor import CheckSandboxError, execute_check
from concorde.spec.verification import verifies
from tests.concorde.distribution import test_pi_session as session_fixtures
from tests.concorde.support.environment import child_environment
from tests.concorde.support.fake_openai_provider import FakeOpenAIProvider
from tests.concorde.support.pi_prompt_client import PiRun, read_records, run_prompt
from tests.concorde.support.managed_runtime import (
    npm_cache_in_use,
)


class PrivateTemporaryBoundaryTests(unittest.TestCase):
    @verifies("scenario.checks.scratch")
    def test_bridge_policy_is_not_a_task_parameter(self):
        import io
        from unittest.mock import patch

        from concorde.distribution import tester_check
        from concorde.harness.check_executor import CheckResult

        with (
            tempfile.TemporaryDirectory() as project,
            patch.object(tester_check.Path, "cwd", return_value=Path(project)),
            patch.dict(os.environ, {}, clear=True),
            patch.object(tester_check.signal, "signal"),
        ):
            for field in (
                "private_tmp",
                "mount_sources",
                "host_tmp",
                "export_dir",
                "destination",
                "evidence_root",
            ):
                with (
                    patch(
                        "sys.stdin",
                        io.StringIO(
                            json.dumps({"command": "true", "timeout": 1, field: False})
                        ),
                    ),
                    patch.object(tester_check, "execute_check") as execute,
                ):
                    with self.assertRaises(ValueError):
                        tester_check.main()
                    execute.assert_not_called()
            with (
                patch("sys.stdin", io.StringIO('{"command":"true","timeout":1}')),
                patch("sys.stdout", io.StringIO()),
                patch.object(
                    tester_check,
                    "execute_check",
                    return_value=CheckResult(b"out", b"err", 0),
                ) as execute,
            ):
                self.assertEqual(0, tester_check.main())
                self.assertIs(True, execute.call_args.kwargs["private_tmp"])

    @verifies("scenario.checks.scratch", "scenario.checks.read-only")
    def test_default_unchanged_private_namespace_and_readonly_input_view(self):
        from concorde.harness import check_executor

        # Control the topology, not the caller's TMPDIR. In a tester, default tempfile
        # locations share /tmp/concorde-check-<issued>; distinct files there are NOT
        # necessarily outside the preserved governing/runtime ancestors. These fresh
        # top-level fixture roots work in both host /tmp and a tester's private /tmp.
        # execute_check still allocates its own scratch using the unchanged caller env.
        with (
            tempfile.TemporaryDirectory(
                prefix="concorde-governing-", dir="/tmp"
            ) as raw,
            tempfile.TemporaryDirectory(
                prefix="concorde-unpreserved-", dir="/tmp"
            ) as outside,
        ):
            project = Path(raw) / "project"
            project.mkdir()
            (project / "source").write_text("governing")
            roots = (
                project.resolve(),
                Path(check_executor.__file__).resolve().parents[3],
                Path(sys.prefix),
                Path(sys.base_prefix),
                Path(sys.executable),
            )
            # Establish the documented prerequisites independently of the mount result.
            preserved = {
                Path("/tmp") / root.relative_to("/tmp").parts[0]
                for root in roots
                if root.is_relative_to("/tmp") and root != Path("/tmp")
            }
            shared = Path(raw) / "input"
            unpreserved = Path(outside) / "input"
            self.assertIn(shared.parent, preserved)
            self.assertNotIn(unpreserved.parent, preserved)
            for source in (shared, unpreserved):
                source.write_bytes(b"host-input")
            code = """
import os,sys,tempfile
from pathlib import Path
private = sys.argv[1] == 'True'
source = Path(sys.argv[2])
canonical_visible = not private or sys.argv[3] == 'True'
protected = [Path.cwd()/'source']
if private:
    view = Path(os.environ['CONCORDE_TEST_HOST_TMP']) / source.relative_to('/tmp')
    assert view.read_text() == 'host-input'
    protected.append(view)
assert source.exists() == canonical_visible, (source, canonical_visible)
if canonical_visible:
    assert source.read_text() == 'host-input'
    protected.append(source)
else:
    assert not source.parent.exists(), 'unpreserved ancestor unexpectedly visible'
    assert not (Path('/proc/self/root')/source.relative_to('/')).exists()
for path in [*protected, *(Path('/proc/self/root')/p.relative_to('/') for p in protected)]:
    try: path.write_text('bad')
    except OSError as error: assert error.errno == 30, error
    else: raise AssertionError('host/project write allowed: '+str(path))
try: (Path.cwd()/'forbidden-new-file').write_text('bad')
except OSError as error: assert error.errno == 30, error
else: raise AssertionError('governing creation allowed')
if private:
    with tempfile.TemporaryDirectory(prefix='concorde-pi-worker-',dir='/tmp') as run:
        Path(run,'policy.json').write_text('private-policy')
    print(os.environ['CONCORDE_CHECK_TMPDIR'])
else:
    try: tempfile.TemporaryDirectory(prefix='concorde-pi-worker-',dir='/tmp')
    except OSError as error: assert error.errno == 30
    else: raise AssertionError('default boundary changed')
"""
            for source, visible in ((shared, True), (unpreserved, False)):
                for private in (False, True):
                    with self.subTest(preserved=visible, private_tmp=private):
                        result = execute_check(
                            project,
                            [
                                sys.executable,
                                "-c",
                                code,
                                str(private),
                                str(source),
                                str(visible),
                            ],
                            timeout=10,
                            environment=child_environment(),
                            private_tmp=private,
                        )
                        self.assertEqual(0, result.returncode, result.stderr)
                        if private:
                            self.assertFalse(
                                Path(result.stdout.decode().strip()).exists()
                            )
                        self.assertEqual(b"host-input", source.read_bytes())
                        self.assertEqual("governing", (project / "source").read_text())
                        self.assertFalse((project / "forbidden-new-file").exists())
            with self.assertRaises(CheckSandboxError):
                execute_check(
                    project,
                    [sys.executable],
                    timeout=1,
                    environment=child_environment(),
                    private_tmp="yes",
                )
            with self.assertRaises(CheckSandboxError):
                execute_check(
                    Path("/tmp"),
                    [sys.executable],
                    timeout=1,
                    environment=child_environment(),
                    private_tmp=True,
                )


@unittest.skipUnless(shutil.which("pi"), "real Pi required")
class RegisteredTesterTemporaryTests(unittest.TestCase):
    # Reuse the source-private fixture construction, not its tests or a task launcher.
    setUp = session_fixtures.RealPiSessionTests.setUp

    def drive(self, command, *, timeout=150, cancel=False):
        pi = shutil.which("pi")
        self.storage = self.root / "storage"
        self.storage.mkdir(exist_ok=True)
        definition = (self.project / ".pi/agents/tester.md").read_text()
        _, header, body = definition.split("---", 2)
        fields = dict(
            line.split(": ", 1) for line in header.strip().splitlines() if ": " in line
        )
        prompt = self.root / "tester-system.md"
        prompt.write_text(body)
        with FakeOpenAIProvider(
            [
                {
                    "tool": "test_command",
                    "arguments": {"command": command, "timeout": timeout},
                },
                {"text": "done"},
            ]
        ) as provider:
            (self.agent / "models.json").write_text(
                json.dumps(
                    {
                        "providers": {
                            "fake": {
                                "baseUrl": provider.base_url,
                                "api": "openai-completions",
                                "apiKey": "fake-only",
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
                "PATH": f"{Path(pi).parent}:" + os.environ.get("PATH", ""),
                "PI_CODING_AGENT_DIR": str(self.agent),
                "PI_OFFLINE": "1",
                "PI_SKIP_VERSION_CHECK": "1",
                "PI_TELEMETRY": "0",
                "TMPDIR": str(self.storage),
                "PI_SUBAGENT_EXTENSION_BINDINGS": json.dumps(
                    {"concorde/1": {"selection": str(self.selection_path)}}
                ),
            }
            # Use the normal locked npm cache read-only; acquisition/writes go to issued scratch.
            if os.environ.get("npm_config_cache"):
                env["npm_config_cache"] = os.environ["npm_config_cache"]
            # The Pi process runs under a private HOME, so npm's default cache is empty there:
            # name this process's populated cache as the local source the nested offline
            # install is seeded from (the tester bridge issues its own scratch cache).
            env["CONCORDE_TEST_NPM_CACHE"] = str(npm_cache_in_use(os.environ))
            argv = [
                pi,
                "--mode",
                "rpc",
                "--no-session",
                "--approve",
                "--offline",
                "--no-context-files",
                "--no-skills",
                "--no-prompt-templates",
                "--no-themes",
                "--no-extensions",
                "--system-prompt",
                str(prompt),
                "--tools",
                fields["tools"].replace(" ", ""),
                "--model",
                "fake/fake-model",
            ]
            for extension in fields["extensions"].split(", "):
                argv += ["-e", str((self.project / ".pi/agents" / extension).resolve())]
            if cancel:
                run = self.cancel_run(argv, env)
            else:
                run = run_prompt(
                    argv,
                    cwd=str(self.project),
                    env=env,
                    message="Run the fixture test command.",
                    timeout=timeout + 40,
                )
            self.assertTrue(provider.requests)
            names = {t["function"]["name"] for t in provider.requests[0]["tools"]}
            self.assertIn("test_command", names)
            self.assertTrue(
                {"bash", "write", "edit", "subagent", "concorde"}.isdisjoint(names)
            )
        self.assertEqual(
            [], list(self.storage.glob("concorde-check-*")), "scratch survived command"
        )
        return run

    def cancel_run(self, argv, env):
        process = subprocess.Popen(
            argv,
            cwd=self.project,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        records = queue.Queue()
        threading.Thread(
            target=read_records, args=(process.stdout, records), daemon=True
        ).start()

        def send(value):
            process.stdin.write((json.dumps(value) + "\n").encode())
            process.stdin.flush()

        try:
            send(
                {
                    "id": "prompt",
                    "type": "prompt",
                    "message": "Run the fixture command.",
                }
            )
            deadline = time.monotonic() + 30
            while not list(
                self.storage.glob("concorde-check-*/private-tmp/cancel-ready")
            ):
                if time.monotonic() > deadline:
                    self.fail("command did not reach cancellation gate")
                time.sleep(0.05)
            send({"id": "abort", "type": "abort"})
            while True:
                kind, line = records.get(timeout=30)
                if kind == "eof":
                    self.fail("Pi exited before abort acknowledgement")
                value = json.loads(line)
                if value.get("type") == "response" and value.get("id") == "abort":
                    self.assertTrue(value["success"])
                    break
            process.stdin.close()
            process.wait(timeout=15)
            return PiRun(
                stderr=process.stderr.read().decode(), exit_code=process.returncode
            )
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()

    @verifies("scenario.checks.descendants-end", "scenario.checks.command-output")
    def test_exit_timeout_cancel_reap_descendants_before_private_tmp_cleanup(self):
        for mode in ("exit", "timeout", "cancel"):
            token = "concorde-tester-descendant-" + uuid.uuid4().hex
            daemon = "import os,ctypes,time;os.setsid();ctypes.CDLL(None).prctl(1,0,0,0,0);\nif os.fork():os._exit(0)\ntime.sleep(60)"
            code = (
                f"import subprocess,sys,time;from pathlib import Path;p=subprocess.Popen([sys.executable,'-c',{daemon!r},{token!r}]);p.wait();Path('/tmp/cancel-ready').write_text('ephemeral');print('ready',flush=True);"
                + (
                    "time.sleep(60)"
                    if mode != "exit"
                    else "print('finished',flush=True)"
                )
            )
            with self.subTest(mode=mode):
                run = self.drive(
                    shlex.quote(sys.executable) + " -c " + shlex.quote(code),
                    timeout=2 if mode == "timeout" else 40,
                    cancel=mode == "cancel",
                )
                if mode != "cancel":
                    [tool] = run.results_of("test_command")
                    self.assertEqual(mode == "timeout", tool["isError"])
                    self.assertIn("ready", str(tool["result"]))
                    if mode == "timeout":
                        self.assertIn(
                            '"timed_out":true',
                            json.dumps(tool["result"])
                            .replace(" ", "")
                            .replace('\\"', '"'),
                        )
                for path in Path("/proc").glob("[0-9]*/cmdline"):
                    try:
                        command = path.read_bytes()
                    except (FileNotFoundError, PermissionError, ProcessLookupError):
                        continue
                    self.assertNotIn(token.encode(), command, str(path))
