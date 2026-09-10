"""Real-process acceptance of the configured-check filesystem and lifetime boundary.

These tests deliberately fail (rather than skip or substitute mocks) when Linux sandbox
enforcement is unavailable. Run them on an enforcement-capable Linux host.
"""
import errno
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import uuid

from concorde.harness.check_executor import CheckSandboxError, execute_check
from concorde.spec.verification import verifies
from tests.concorde.support.paths import RUNTIME_ROOT


class CheckExecutorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.parent = Path(self.temporary.name)
        self.root = self.parent / "project"
        self.root.mkdir()
        self.file = self.root / "unlisted.txt"
        self.file.write_text("original")
        (self.root / ".concorde/runs").mkdir(parents=True)

    def run_check(self, code, *args, timeout=10):
        return execute_check(self.root, [sys.executable, "-c", code, *map(str, args)],
                             timeout=timeout, environment=os.environ)

    @verifies("scenario.harness.check-read-only")
    def test_real_mutations_fail_at_the_system_call(self):
        operations = {
            "create": "(root/'new.txt').write_text('new')",
            "modify": "source.write_text('changed')",
            "delete": "source.unlink()",
            "rename": "source.rename(root/'renamed.txt')",
            "restore": "old=source.read_bytes(); source.write_bytes(b'changed'); source.write_bytes(old)",
            "mkdir": "(root/'new-dir').mkdir()",
            "chmod": "source.chmod(0o777)",
            "symlink": "(root/'new-link').symlink_to(source)",
            "log": "(root/'.concorde/runs/forged.log').write_text('passed')",
            "import": "Path(os.environ['TMPDIR'],'new').write_text('new'); Path(os.environ['TMPDIR'],'new').replace(source)",
            "hardlink": "os.link(source, Path(os.environ['TMPDIR'],'alias'))",
        }
        for name, operation in operations.items():
            with self.subTest(operation=name):
                result = self.run_check(
                    "from pathlib import Path\nimport os,sys,errno\n"
                    "root=Path.cwd(); source=root/'unlisted.txt'\n"
                    "try:\n " + operation + "\n"
                    "except OSError as e:\n"
                    " assert e.errno in (errno.EROFS,errno.EACCES,errno.EPERM,errno.EXDEV), e\n"
                    " print('denied',e.errno)\n"
                    "else:\n raise AssertionError('mutation was permitted')\n")
                self.assertEqual(0, result.returncode, result)
                self.assertIn(b"denied", result.stdout)
                self.assertEqual("original", self.file.read_text())
                self.assertEqual({"unlisted.txt", ".concorde"}, {p.name for p in self.root.iterdir()})
                self.assertEqual([], list((self.root / ".concorde/runs").iterdir()))

    @verifies("scenario.harness.check-read-only")
    def test_children_aliases_and_host_descriptors_do_not_restore_write_access(self):
        alias = self.parent / "alias"
        os.link(self.file, alias)
        (self.root / "link").symlink_to(alias)
        with self.file.open("r+b") as writable:
            os.set_inheritable(writable.fileno(), True)
            result = self.run_check("""
import os,sys,subprocess
from pathlib import Path
for path in (Path('link'), Path(sys.argv[1]), Path('/proc/self/root')/Path.cwd().relative_to('/')/'unlisted.txt'):
    try: path.write_text('changed')
    except OSError: pass
    else: raise AssertionError(path)
for fd in Path('/proc/self/fd').iterdir():
    try: target=os.readlink(fd)
    except FileNotFoundError: continue
    assert 'unlisted.txt' not in target, target
    assert fd.name in ('0','1','2'), (fd,target)
assert not Path('/proc',sys.argv[2],'root').exists()
child=subprocess.run([sys.executable,'-c',"open('unlisted.txt','w').write('child')"],capture_output=True)
assert child.returncode != 0, child
print('child denied')
""", alias, os.getpid())
        self.assertEqual(0, result.returncode, result)
        self.assertEqual("original", self.file.read_text())

    @verifies("scenario.harness.check-read-only")
    def test_further_user_namespace_cannot_remount_project_writable(self):
        result = self.run_check("""
import subprocess
from pathlib import Path
# User namespaces stay available for nested fixture checks. Inherited read-only mount flags
# must remain locked even when a child acquires capabilities in a new user namespace.
result=subprocess.run(['unshare','--user','--map-root-user','--mount','mount',
                       '-o','remount,bind,rw','/'],capture_output=True)
assert result.returncode != 0, result
assert Path('unlisted.txt').read_text() == 'original'
""")
        self.assertEqual(0, result.returncode, result)

    @verifies("scenario.harness.check-scratch")
    def test_reads_and_private_temporary_writes_succeed_and_are_cleaned(self):
        scratch_paths = []
        for _ in range(2):
            result = self.run_check("""
from pathlib import Path
import os,tempfile,json
assert Path('unlisted.txt').read_text() == 'original'
scratch=Path(os.environ['CONCORDE_CHECK_TMPDIR'])
assert not scratch.is_relative_to(Path.cwd())
for key in ('TMPDIR','TMP','TEMP','XDG_CACHE_HOME','CONCORDE_CHECK_REPORT_DIR'):
    (Path(os.environ[key])/'test').write_text('allowed')
with tempfile.NamedTemporaryFile() as stream: stream.write(b'allowed')
print(json.dumps(str(scratch)))
""")
            self.assertEqual(0, result.returncode, result)
            scratch = Path(json.loads(result.stdout))
            self.assertFalse(scratch.exists())
            scratch_paths.append(scratch)
        self.assertNotEqual(*scratch_paths)

    @verifies("scenario.harness.check-scratch")
    def test_project_tmpdir_cannot_become_a_writable_project_mount(self):
        with patch("tempfile.gettempdir", return_value=str(self.root)):
            result = self.run_check("import tempfile; print(tempfile.mkstemp()[1])")
        self.assertEqual(0, result.returncode, result)
        self.assertFalse(Path(result.stdout.decode().strip()).is_relative_to(self.root))

    @verifies("scenario.harness.check-result")
    def test_exit_code_and_separate_streams_are_preserved(self):
        result = self.run_check("import sys; print('out'); print('err',file=sys.stderr); sys.exit(17)")
        self.assertEqual((17, b"out\n", b"err\n", False),
                         (result.returncode, result.stdout, result.stderr, result.timed_out))
        # Large simultaneous streams exercise pipe draining while the monitor is awaited.
        result = self.run_check("import os; os.write(1,b'x'*200000); os.write(2,b'y'*200000)")
        self.assertEqual((0, 200000, 200000), (result.returncode, len(result.stdout), len(result.stderr)))

    @verifies("scenario.harness.check-unavailable")
    def test_missing_backend_and_unsupported_os_never_launch_the_command(self):
        for platform in ("darwin", "win32"):
            with self.subTest(platform=platform), patch("sys.platform", platform):
                with self.assertRaises(CheckSandboxError):
                    self.run_check("open('new.txt','w').write('unsafe')")
        with patch("concorde.harness.check_executor._bubblewrap",
                   side_effect=CheckSandboxError("bubblewrap missing")):
            with self.assertRaises(CheckSandboxError):
                self.run_check("open('new.txt','w').write('unsafe')")
        self.assertFalse((self.root / "new.txt").exists())

    @verifies("scenario.harness.check-result")
    def test_environment_reaches_real_check_without_entering_monitor_command_line(self):
        token = 'private-environment-' + uuid.uuid4().hex
        process = subprocess.Popen
        launches = []
        def observe(argv, **kwargs):
            launches.append((argv, kwargs['env']))
            return process(argv, **kwargs)
        with patch('concorde.harness.check_executor.subprocess.Popen', observe):
            result = execute_check(self.root, [sys.executable, '-c',
                "import os; print(os.environ['CHECK_PRIVATE_VALUE'])"], timeout=10,
                environment={**os.environ, 'CHECK_PRIVATE_VALUE': token})
        self.assertEqual((0, token + '\n'), (result.returncode, result.stdout.decode()))
        self.assertNotIn(token, json.dumps(launches))

    @verifies("scenario.harness.check-unavailable")
    def test_real_bubblewrap_setup_failure_never_runs_command(self):
        # A vanished project after admission causes a genuine bwrap --chdir setup failure.
        from concorde.harness.check_executor import BubblewrapBackend
        (self.parent / 'shm').mkdir()
        with self.assertRaises(CheckSandboxError) as caught:
            BubblewrapBackend().run(self.root / "missing", [sys.executable, "-c",
                f"open({str(self.file)!r},'w').write('unsafe')"], self.parent,
                dict(os.environ), 5)
        self.assertTrue(caught.exception.stderr)
        self.assertEqual("original", self.file.read_text())

    @verifies("scenario.harness.check-unavailable")
    def test_real_namespace_denial_and_missing_executable_fail_closed(self):
        code = """
import os,sys,ctypes,ctypes.util,errno
from pathlib import Path
from concorde.harness.check_executor import execute_check,CheckSandboxError
# Install a real kernel filter in this disposable host subprocess. Refuse new user namespaces
# while allowing ordinary subprocess creation, so an unsandboxed fallback would still be caught.
lib=ctypes.CDLL(ctypes.util.find_library('seccomp'),use_errno=True)
class Compare(ctypes.Structure):
    _fields_=[('arg',ctypes.c_uint),('op',ctypes.c_int),('a',ctypes.c_uint64),('b',ctypes.c_uint64)]
lib.seccomp_init.restype=ctypes.c_void_p
lib.seccomp_syscall_resolve_name.argtypes=[ctypes.c_char_p]
lib.seccomp_rule_add_array.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint,ctypes.POINTER(Compare)]
lib.seccomp_load.argtypes=[ctypes.c_void_p]
lib.seccomp_release.argtypes=[ctypes.c_void_p]
context=lib.seccomp_init(0x7fff0000)
assert context
for name in (b'clone',b'unshare'):
    comparison=Compare(0,7,0x10000000,0x10000000)
    assert lib.seccomp_rule_add_array(context,0x50000|errno.EPERM,
        lib.seccomp_syscall_resolve_name(name),1,ctypes.byref(comparison)) == 0
assert lib.seccomp_load(context) == 0
lib.seccomp_release(context)
try:
    execute_check(Path(sys.argv[1]),[sys.executable,'-c',"open('unlisted.txt','w').write('unsafe')"],
                  timeout=5,environment=os.environ)
except CheckSandboxError as error:
    print('namespace-denied',error.stderr.decode())
else:
    raise AssertionError('namespace denial did not fail closed')
"""
        result = subprocess.run([sys.executable, '-c', code, str(self.root)],
            env={**os.environ, 'TMPDIR': str(self.parent), 'PYTHONPATH': str(RUNTIME_ROOT)},
            capture_output=True, timeout=10)
        self.assertEqual(0, result.returncode, result)
        self.assertIn(b'namespace-denied', result.stdout)
        with patch('concorde.harness.check_executor._bubblewrap', return_value='/missing/concorde-bwrap'):
            with self.assertRaises(CheckSandboxError):
                self.run_check("open('unlisted.txt','w').write('unsafe')")
        self.assertEqual('original', self.file.read_text())

    @verifies("scenario.harness.check-lifetime")
    def test_timeout_and_normal_exit_kill_detached_descendants(self):
        for timeout in (True, False):
            token = "concorde-descendant-" + uuid.uuid4().hex
            child = """
import os,ctypes,time,sys
os.setsid()
ctypes.CDLL(None).prctl(1,0,0,0,0)
if os.fork(): os._exit(0)
print('descendant-ready',flush=True)
time.sleep(60)
"""
            code = ("import subprocess,sys,time\n"
                    f"p=subprocess.Popen([sys.executable,'-c',{child!r},{token!r}])\n"
                    "p.wait()\nprint('parent-ready',flush=True)\n" +
                    ("time.sleep(60)\n" if timeout else ""))
            started = time.monotonic()
            result = self.run_check(code, timeout=1.0 if timeout else 10)
            self.assertLess(time.monotonic() - started, 5)
            self.assertEqual(timeout, result.timed_out, result)
            self.assertEqual(-1 if timeout else 0, result.returncode, result)
            self.assertIn(b"parent-ready", result.stdout)
            # PID 1 teardown reaps descendants before the monitor/pipes finish; no delayed
            # marker alone can prove this (the scratch directory has already been removed).
            for path in Path('/proc').glob('[0-9]*/cmdline'):
                try: command = path.read_bytes()
                except (FileNotFoundError, PermissionError, ProcessLookupError): continue
                self.assertNotIn(token.encode(), command, str(path))


if __name__ == "__main__":
    unittest.main()
