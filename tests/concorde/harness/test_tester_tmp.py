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

from concorde.harness.check_executor import execute_check, CheckSandboxError
from concorde.harness.pi_rpc import _records, run_prompt
from concorde.spec.verification import verifies
from tests.concorde.distribution import test_pi_session as session_fixtures
from tests.concorde.support.fake_openai_provider import FakeOpenAIProvider
from tests.concorde.support.managed_runtime import independent_runtime_environment
from tests.concorde.support.paths import REPOSITORY_ROOT


class PrivateTemporaryBoundaryTests(unittest.TestCase):
    @verifies("scenario.harness.check-scratch")
    def test_bridge_policy_is_not_a_task_parameter(self):
        import io
        from unittest.mock import patch
        from concorde.distribution import outer_check
        from concorde.harness.check_executor import CheckResult

        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(outer_check.signal, "signal"),
        ):
            for field in ("private_tmp", "mount_sources", "host_tmp"):
                with (
                    patch(
                        "sys.stdin",
                        io.StringIO(
                            json.dumps({"command": "true", "timeout": 1, field: False})
                        ),
                    ),
                    patch.object(outer_check, "execute_check") as execute,
                ):
                    with self.assertRaises(ValueError):
                        outer_check.main()
                    execute.assert_not_called()
            with (
                patch("sys.stdin", io.StringIO('{"command":"true","timeout":1}')),
                patch("sys.stdout", io.StringIO()),
                patch.object(
                    outer_check,
                    "execute_check",
                    return_value=CheckResult(b"out", b"err", 0),
                ) as execute,
            ):
                self.assertEqual(0, outer_check.main())
                self.assertIs(True, execute.call_args.kwargs["private_tmp"])

    @verifies("scenario.harness.check-scratch", "scenario.harness.check-read-only")
    def test_default_unchanged_private_namespace_and_readonly_input_view(self):
        with (
            tempfile.TemporaryDirectory() as raw,
            tempfile.NamedTemporaryFile() as source,
        ):
            project = Path(raw) / "project"
            project.mkdir()
            (project / "source").write_text("governing")
            source.write(b"host-input")
            source.flush()
            code = """
import os,sys,tempfile,json
from pathlib import Path
private = sys.argv[1] == 'True'
source = Path(sys.argv[2])
if private:
    view = Path(os.environ['CONCORDE_TEST_HOST_TMP']) / source.relative_to('/tmp')
    assert view.read_text() == 'host-input'
    assert not source.exists(), 'unpreserved old /tmp name should be hidden'
    for path in (view, Path.cwd()/'source', Path('/proc/self/root')/view.relative_to('/')):
        try: path.write_text('bad')
        except OSError: pass
        else: raise AssertionError('host write allowed')
    with tempfile.TemporaryDirectory(prefix='concorde-pi-worker-',dir='/tmp') as run:
        Path(run,'policy.json').write_text('private-policy')
    print(os.environ['CONCORDE_CHECK_TMPDIR'])
else:
    assert source.read_text() == 'host-input'
    try: tempfile.TemporaryDirectory(prefix='concorde-pi-worker-',dir='/tmp')
    except OSError as error: assert error.errno == 30
    else: raise AssertionError('default boundary changed')
"""
            for private in (False, True):
                result = execute_check(
                    project,
                    [sys.executable, "-c", code, str(private), source.name],
                    timeout=10,
                    environment=os.environ,
                    private_tmp=private,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                if private:
                    self.assertFalse(Path(result.stdout.decode().strip()).exists())
            self.assertEqual("governing", (project / "source").read_text())
            self.assertEqual(b"host-input", Path(source.name).read_bytes())
            with self.assertRaises(CheckSandboxError):
                execute_check(
                    project,
                    [sys.executable],
                    timeout=1,
                    environment=os.environ,
                    private_tmp="yes",
                )
            with self.assertRaises(CheckSandboxError):
                execute_check(
                    Path("/tmp"),
                    [sys.executable],
                    timeout=1,
                    environment=os.environ,
                    private_tmp=True,
                )


# The input script is read through the explicit host-/tmp view, never copied into a runtime.
NESTED = r"""
import json,os,sys,subprocess,tempfile
from pathlib import Path
repo = Path(sys.argv[1]); host_input = Path(sys.argv[2]); wheels = sys.argv[3]
sys.path.insert(0,str(repo))
from tests.concorde.spec.support import project
from tests.concorde.harness.test_installed_worker_runtime import ScriptedWorkerProvider
from tests.concorde.support.fake_openai_provider import FakeOpenAIProvider
from concorde.distribution.local_installation import admit_package,ensure_installation,verify_installation
from concorde.spec.typed_data import typed
from concorde.harness.pi_worker import PiWorkerRuntime,WorkerLaunch,WorkerExecutionError
scratch = Path(os.environ['CONCORDE_CHECK_TMPDIR'])
old_boundary = sys.argv[4] == 'old'
view = Path('/tmp') if old_boundary else Path(os.environ['CONCORDE_TEST_HOST_TMP'])
assert (view/host_input.relative_to('/tmp')).read_text() == 'HOST-READONLY'
if not old_boundary: assert not host_input.exists()
for path in (repo/'AGENTS.md',Path.cwd()/'pi/extensions/concorde-tester.ts',view/host_input.relative_to('/tmp')):
    try: path.open('a').close()
    except OSError: pass
    else: raise AssertionError('governing/host path writable: '+str(path))
trace_dir = scratch/'traces'; trace_dir.mkdir()
os.environ['CONCORDE_DIAGNOSTIC_TIMING_DIR'] = str(trace_dir)
# The parent bridge already verified its private source selection. The separately installed
# fixture has its own complete local provenance; do not redirect it into source-private mode.
for key in ('CONCORDE_SESSION_SELECTION','PI_SUBAGENT_EXTENSION_BINDINGS','CONCORDE_STUDIO_URL'):
    os.environ.pop(key,None)
wheel_path = Path(wheels)
if wheel_path.is_relative_to('/tmp'):
    wheel_path = view/wheel_path.relative_to('/tmp')
os.environ.update(PIP_NO_INDEX='1',PIP_FIND_LINKS=str(wheel_path),PYTHONNOUSERSITE='1',NPM_CONFIG_OFFLINE='false')
consumer = scratch/'consumer'; consumer.mkdir()
project(consumer)
config = json.loads((consumer/'.concorde/config.json').read_text())
config['operation_configuration'] = typed('concorde-operation-configuration',{'model':'fake/fake-model','timeout_seconds':45})
(consumer/'.concorde/config.json').write_text(json.dumps(config))
def git(*args):
    return subprocess.run(['git','-C',str(consumer),*args],check=True,capture_output=True,text=True).stdout
(consumer/'.gitignore').write_text('.concorde/framework/\n.concorde/.venv/\n.concorde/install*\n.concorde/runs/\n.concorde/status/\n.concorde/work/\n.pi/\n')
git('init','-q'); git('config','user.name','Fixture'); git('config','user.email','fixture@example.invalid')
git('add','.'); git('commit','-qm','fixture')
other = scratch/'other'; git('worktree','add','-qb','other',str(other))
(other/'other-secret').write_text('MUST-NOT-APPEAR')
local = ensure_installation(consumer,admit_package(repo),bootstrap=True)
assert local.python.is_relative_to(consumer/'.concorde/.venv')
assert local.framework == consumer/'.concorde/framework'
verify_installation(consumer)
probe = subprocess.run([str(local.python),'-I','-c',"import sys,langgraph.graph;print(sys.prefix);print(langgraph.graph.__file__)"],capture_output=True,text=True,check=True)
assert all(Path(p).is_relative_to(consumer/'.concorde/.venv') for p in probe.stdout.splitlines())
typebox = consumer/'.concorde/.venv/share/concorde/pi/node_modules/typebox'
assert (typebox/'build/index.mjs').is_file()
credentials = scratch/'fake-agent'; credentials.mkdir()
def provider_config(provider):
    (credentials/'models.json').write_text(json.dumps({'providers':{'fake':{'baseUrl':provider.base_url,'api':'openai-completions','apiKey':'fake-only','compat':{'supportsDeveloperRole':False,'supportsReasoningEffort':False},'models':[{'id':'fake-model'}]}}}))
environment = dict(os.environ,PI_CODING_AGENT_DIR=str(credentials))
for key in ('PYTHONPATH','PYTHONHOME'):
    environment.pop(key,None)
with ScriptedWorkerProvider([{'submit':True}]) as provider:
    provider_config(provider)
    envelope = {'type_id':'concorde-operation-invocation','schema_version':3,'operation_id':'concorde-context-solve','mode':'execute','configuration':None,'input':typed('concorde-context-solve-request',{'target_id':'service.transfer','task':'Assess the fixture contract'})}
    completed = subprocess.run([str(local.python),str(local.launcher),'concorde-context-solve'],input=json.dumps(envelope),cwd=consumer,env=environment,capture_output=True,text=True,timeout=80)
    if old_boundary:
        assert completed.returncode != 0, completed.stdout
        assert 'Read-only file system' in completed.stdout and '/tmp/concorde-pi-worker-' in completed.stdout, completed.stdout
        assert provider.requests == [], 'old boundary must fail before model execution'
        print(json.dumps({'scratch':str(scratch),'operation':'worker-preparation-refused','provider_requests':0}))
        sys.exit(0)
    assert completed.returncode == 0, (completed.stdout,completed.stderr)
    result = json.loads(completed.stdout)
    assert result['status'] == 'succeeded',result
    assert result['output']['data']['outcome'] == 'completed',result
    assert len(provider.requests)==1
    names = {t['function']['name'] for t in provider.requests[0]['tools']}
    assert 'submit_result' in names and {'subagent','concorde','bash'}.isdisjoint(names)
# Project-workspace leaf also keeps the unchanged other-worktree mask and tool ceiling.
runtime = PiWorkerRuntime(local.framework,environment=environment,credentials_dir=credentials)
launch = WorkerLaunch(worker='mask-fixture',workspace=str(consumer),system_prompt='Terminal fixture',message='Check masks',result_schema={'type':'object','properties':{'answer':{'type':'string'}},'required':['answer'],'additionalProperties':False},tools=('read','bash','submit_result'),read_paths=('src/',),model='fake/fake-model',timeout_seconds=45)
with FakeOpenAIProvider([{'tool':'bash','arguments':{'command':f'test ! -e {other}/other-secret && echo MASK_OK'}},{'tool':'subagent','arguments':{}},{'tool':'submit_result','arguments':{'answer':'done'}}]) as provider:
    provider_config(provider)
    outcome = runtime(launch)
    assert outcome.value == {'answer':'done'}
    assert 'MASK_OK' in str(outcome.run.results_of('bash'))
    assert 'MUST-NOT-APPEAR' not in str(outcome.run.tool_results)
    assert outcome.run.results_of('subagent')[0]['isError']
# The actual local TypeBox is required even though Pi has a bundled TypeBox available.
missing = typebox.with_name('typebox-disabled'); typebox.rename(missing)
with FakeOpenAIProvider([]) as provider:
    provider_config(provider)
    try: runtime(launch)
    except WorkerExecutionError: pass
    else: raise AssertionError('local dependency fallback')
    assert provider.requests == []
missing.rename(typebox)
assert not list(Path('/tmp').glob('concorde-pi-worker-*'))
traces = [json.loads(p.read_text()) for p in trace_dir.glob('*.json')]
assert traces and any(s['name']=='managed_runtime.launcher_probe' for t in traces for s in t['spans'])
assert 'fake-only' not in json.dumps(traces)
print(json.dumps({'scratch':str(scratch),'operation':'succeeded','local_runtime':True,'local_typebox_required':True,'masks':True,'terminal_tools':True,'host_readonly':True,'worker_temp_clean':True,'trace_count':len(traces)}))
"""


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
            target=_records, args=(process.stdout, records), daemon=True
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
            from concorde.harness.pi_rpc import PiRun

            return PiRun(
                stderr=process.stderr.read().decode(), exit_code=process.returncode
            )
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()

    @verifies("scenario.harness.check-scratch", "scenario.harness.pi-worker-launch")
    def test_installed_operation_and_terminal_worker_through_registered_tool(self):
        inputs = self.root / "inputs"
        inputs.mkdir()
        environment = independent_runtime_environment(inputs, REPOSITORY_ROOT)
        # Real locked npm acquisition writes only the issued cache/runtime, not forwarding assets.
        script = inputs / "nested.py"
        script.write_text(NESTED)
        with tempfile.NamedTemporaryFile(dir="/tmp") as host_input:
            host_input.write(b"HOST-READONLY")
            host_input.flush()
            source_input = (
                '"${CONCORDE_TEST_HOST_TMP:-/tmp}/'
                + str(script.relative_to("/tmp"))
                + '"'
            )
            command = f"{shlex.quote(sys.executable)} {source_input} {shlex.quote(str(REPOSITORY_ROOT))} {shlex.quote(host_input.name)} {shlex.quote(environment['PIP_FIND_LINKS'])}"
            for mode in ("new", "old"):
                if mode == "old":
                    # Fault injection in the disposable governing fixture BEFORE Pi launch.
                    # Rebuild/reselect that fixture; never alter the real candidate or a running tester.
                    from concorde.distribution.build import write_build
                    from concorde.distribution.session_selection import (
                        save_selection,
                        select_session,
                    )

                    bridge = self.project / "src/concorde/distribution/outer_check.py"
                    bridge.write_text(
                        bridge.read_text().replace(
                            "private_tmp=True", "private_tmp=False"
                        )
                    )
                    write_build(self.project)
                    save_selection(
                        self.project,
                        self.selection_path,
                        select_session(
                            self.project,
                            mode="test",
                            pi_entry=self.project
                            / "generated/session/pi/concorde-session.ts",
                            runtime=self.project / "scripts/run-operation.py",
                        ),
                    )
                run = self.drive(command + " " + mode, timeout=180)
                [tool] = run.results_of("test_command")
                self.assertFalse(tool["isError"], tool)
                result = tool["result"]["details"]
                summary = json.loads(result["stdout"].splitlines()[-1])
                self.assertEqual(
                    "succeeded" if mode == "new" else "worker-preparation-refused",
                    summary["operation"],
                )
                self.assertFalse(Path(summary["scratch"]).exists())
                self.assertEqual(b"HOST-READONLY", Path(host_input.name).read_bytes())
                print(json.dumps(summary))

    @verifies("scenario.harness.check-lifetime", "scenario.harness.check-result")
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
