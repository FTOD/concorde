"""OS-enforced read-only configured checks; no unsandboxed execution fallback.

The backend is a trusted host interface, never a registry/task-selected command. Linux exposes
the host tree recursively read-only, with one fresh writable scratch mount. PID namespaces,
closed descriptors and a host-held pidfd keep filesystem and process authority inside that tree.
This is not a read, network or credential policy.
"""
from __future__ import annotations

import json
import ctypes
import math
import os
import select
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from typing import Mapping, Protocol, Sequence


CHECK_POLICY = "project-read-only-v1"


@dataclass(frozen=True)
class CheckResult:
    stdout: bytes
    stderr: bytes
    returncode: int
    timed_out: bool = False


class CheckSandboxError(RuntimeError):
    """Enforcement unavailable; diagnostics stay with the calling host."""

    def __init__(self, message: str, *, stdout: bytes = b"", stderr: bytes = b""):
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr


class CheckBackend(Protocol):
    def run(self, project: Path, argv: Sequence[str], scratch: Path,
            environment: Mapping[str, str], timeout: float) -> CheckResult: ...


def _pidfd_call(name: str, *args: int) -> int:
    # Some portable CPython builds omit the Python wrappers despite kernel/libc support.
    # Use libc's named interface there; never fall back to signalling a reusable numeric PID.
    if name == "pidfd_open" and hasattr(os, name):
        return os.pidfd_open(*args)
    if name == "pidfd_send_signal" and hasattr(signal, name):
        signal.pidfd_send_signal(args[0], args[1], None, args[3])
        return 0
    try:
        function = getattr(ctypes.CDLL(None, use_errno=True), name)
    except AttributeError as error:
        raise CheckSandboxError("Linux libc pidfd support is required for check cleanup") from error
    function.restype = ctypes.c_int
    function.argtypes = ([ctypes.c_int, ctypes.c_uint] if name == "pidfd_open"
                         else [ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint])
    result = function(*args)
    if result < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    return result


def _bubblewrap() -> str:
    # Never execute a project-provided bwrap, PATH shim or loader override outside the sandbox.
    mappings = [tuple(map(int, line.split())) for line in Path('/proc/self/uid_map').read_text().splitlines()]
    overflow_uid = int(Path('/proc/sys/kernel/overflowuid').read_text())
    overflow_mapped = any(start <= overflow_uid < start + count for start, _, count in mappings)
    def trusted(path: Path) -> bool:
        metadata = path.stat()
        # Inside a parent check's user namespace, system root is unmapped. Admit that owner
        # only on an already read-only system mount; the mapped checking user is never trusted.
        owner = metadata.st_uid == 0 or (
            not overflow_mapped and metadata.st_uid == overflow_uid and
            os.statvfs(path).f_flag & os.ST_RDONLY)
        return bool(owner and not metadata.st_mode & 0o022)
    for candidate in (Path("/usr/bin/bwrap"), Path("/bin/bwrap")):
        executable = candidate.resolve()
        if not executable.is_file():
            continue
        paths = (executable, *executable.parents)
        if all(trusted(p) for p in paths):
            return str(executable)
    raise CheckSandboxError("a root-owned system bubblewrap installation is required")


def _read_info(descriptor: int, deadline: float) -> dict:
    data = b""
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not select.select([descriptor], [], [], remaining)[0]:
            raise subprocess.TimeoutExpired("bubblewrap setup", 0)
        chunk = os.read(descriptor, 4096)
        if not chunk:
            try:
                value = json.loads(data)
                if type(value.get("child-pid")) is int and value["child-pid"] > 0:
                    return value
            except (ValueError, AttributeError):
                pass
            raise CheckSandboxError("bubblewrap did not create a sandbox process")
        data += chunk
        if len(data) > 65536:
            raise CheckSandboxError("invalid bubblewrap setup metadata")


@contextmanager
def _pipe():
    read, write = os.pipe()
    with os.fdopen(read, "rb", buffering=0) as source, os.fdopen(write, "wb", buffering=0) as sink:
        yield source, sink


class BubblewrapBackend:
    """Linux backend. The gate prevents command execution until its PID namespace is pinned."""

    def run(self, project: Path, argv: Sequence[str], scratch: Path,
            environment: Mapping[str, str], timeout: float) -> CheckResult:
        executable = _bubblewrap()
        deadline = time.monotonic() + timeout
        pidfd = None
        process = None
        stdout = stderr = b""
        timed_out = False
        failure = None
        reader = None
        output = None
        # The status descriptor belongs only to bubblewrap's outside monitor; bubblewrap closes
        # it in the sandbox. It is anonymous and cannot be reopened through a project log path.
        with _pipe() as (info_read, info_write), _pipe() as (gate_read, gate_write), \
             tempfile.TemporaryFile(dir=scratch.parent) as status, \
             tempfile.TemporaryFile(dir=scratch.parent) as arguments:
            command = [executable, "--unshare-user", "--unshare-pid", "--unshare-ipc",
                       "--die-with-parent", "--new-session", "--cap-drop", "ALL",
                       "--ro-bind", "/", "/", "--proc", "/proc", "--dev", "/dev",
                       "--bind", str(scratch), str(scratch),
                       "--bind", str(scratch / "shm"), "/dev/shm",
                       "--remount-ro", "/dev", "--chdir", str(project),
                       "--info-fd", str(info_write.fileno()), "--block-fd", str(gate_read.fileno()),
                       "--json-status-fd", str(status.fileno()), "--clearenv"]
            for key, value in environment.items():
                command.extend(("--setenv", key, value))
            # Preserve the check environment without making its values visible in the monitor's
            # public command line. bubblewrap consumes and closes this anonymous options fd.
            if any("\0" in argument for argument in command):
                raise CheckSandboxError("sandbox options cannot contain NUL bytes")
            arguments.write(b"\0".join(os.fsencode(argument) for argument in command[1:]) + b"\0")
            arguments.seek(0)
            command = [executable, "--args", str(arguments.fileno()), "--", *argv]
            try:
                process = subprocess.Popen(command, cwd="/", stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True,
                    pass_fds=(info_write.fileno(), gate_read.fileno(), status.fileno(), arguments.fileno()),
                    start_new_session=True,
                    env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"})
                info_write.close()
                gate_read.close()
                info = _read_info(info_read.fileno(), deadline)
                # Pin namespace PID 1 before allowing the check to start. A numeric PID alone
                # could be reused by an unrelated process before timeout/cleanup.
                pidfd = _pidfd_call("pidfd_open", info["child-pid"], 0)
                _pidfd_call("pidfd_send_signal", pidfd, 0, 0, 0)
                gate_write.write(b"1")
                # Drain both pipes while waiting for the monitor, rather than waiting for pipe
                # EOF: a daemon can retain stdout after the initial command has already exited.
                reader = ThreadPoolExecutor(max_workers=1)
                output = reader.submit(process.communicate)
                process.wait(timeout=max(0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                timed_out = True
            except (OSError, CheckSandboxError) as error:
                failure = error
            finally:
                # Killing PID 1 makes the kernel terminate *all* descendants, including setsid,
                # double forks, nested PID namespaces and processes that reset parent-death signals.
                # Do this on normal exit too: a background child must not outlive its check.
                if pidfd is not None:
                    try:
                        _pidfd_call("pidfd_send_signal", pidfd, signal.SIGKILL, 0, 0)
                    except ProcessLookupError:
                        pass
                    except OSError as error:
                        # Still stop the monitor below: its trusted init also uses parent-death
                        # termination. A cleanup error must never bypass the remaining cleanup.
                        failure = error
                if process is not None:
                    if process.poll() is None:
                        process.kill()
                if pidfd is not None:
                    try:
                        # pidfd readability means namespace PID 1 has exited, after the kernel
                        # has terminated and reaped its descendants, even with closed stdio.
                        select.select([pidfd], [], [])
                    finally:
                        os.close(pidfd)
                if process is not None:
                    stdout, stderr = output.result() if output is not None else process.communicate()
                if reader is not None:
                    reader.shutdown()
            if failure is not None:
                raise CheckSandboxError(str(failure), stdout=stdout, stderr=stderr) from failure
            if timed_out:
                return CheckResult(stdout, stderr, -1, True)
            status.seek(0)
            records = [json.loads(line) for line in status if line.strip()]
            # bubblewrap emits exit-code only after setup and successful exec. Never infer that
            # boundary from exit 0, or mistake an unavailable namespace for an ordinary check.
            exits = [r["exit-code"] for r in records if "exit-code" in r]
            if not exits or process is None or exits[-1] != process.returncode:
                raise CheckSandboxError("bubblewrap could not execute the isolated check",
                                        stdout=stdout, stderr=stderr)
            return CheckResult(stdout, stderr, process.returncode)


def execute_check(project_root: Path, argv: Sequence[str], *, timeout: float,
                  environment: Mapping[str, str]) -> CheckResult:
    """Run one check with a fresh external scratch directory, removing it after process cleanup."""
    project = project_root.resolve(strict=True)
    if not project.is_dir() or not argv or not math.isfinite(timeout) or timeout <= 0:
        raise CheckSandboxError("a project directory, command and positive finite timeout are required")
    if sys.platform != "linux":
        raise CheckSandboxError(f"no read-only check backend is available for {sys.platform}")
    # Replacing these synthetic filesystems cannot preserve a project located within them.
    if project == Path("/") or any(project.is_relative_to(p) for p in ("/proc", "/dev", "/sys")):
        raise CheckSandboxError("project location cannot be isolated by the Linux check backend")
    backend: CheckBackend = BubblewrapBackend()
    # An ambient TMPDIR inside the project must never create a writable project mount. Nested
    # checks may use their parent's scratch, provided it is outside their own project.
    candidates = dict.fromkeys((tempfile.gettempdir(), os.environ.get("CONCORDE_CHECK_TMPDIR"),
                                "/tmp", "/var/tmp"))
    for candidate in candidates:
        if candidate is None:
            continue
        base = Path(candidate).resolve()
        if base.is_relative_to(project):
            continue
        try:
            temporary = tempfile.TemporaryDirectory(prefix="concorde-check-", dir=base)
        except OSError:
            continue
        with temporary:
            scratch = Path(temporary.name)
            for name in ("tmp", "cache", "reports", "shm"):
                (scratch / name).mkdir(mode=0o700)
            env = {**environment, "PYTHONDONTWRITEBYTECODE": "1",
                   "TMPDIR": str(scratch / "tmp"), "TMP": str(scratch / "tmp"),
                   "TEMP": str(scratch / "tmp"), "XDG_CACHE_HOME": str(scratch / "cache"),
                   "npm_config_cache": str(scratch / "cache" / "npm"),
                   "CONCORDE_CHECK_TMPDIR": str(scratch),
                   "CONCORDE_CHECK_REPORT_DIR": str(scratch / "reports")}
            return backend.run(project, argv, scratch, env, timeout)
    raise CheckSandboxError("no writable host temporary directory outside the project is available")
