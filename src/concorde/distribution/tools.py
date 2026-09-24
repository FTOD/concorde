"""Pinned third-party programs that the installer places under ``.concorde/tools/``.

``d2`` (github.com/d2lang/d2) renders the Specs' diagrams for the docsite. ``concorde.json`` pins
its release and the SHA-256 of the archive for each platform; the installer downloads that archive,
refuses any byte that does not match the pin, and writes only the program itself.

The pi runtime is the sandbox engine pi workers run their commands in,
``@anthropic-ai/sandbox-runtime``. The package ships its ``package.json`` and ``package-lock.json``
under ``src/concorde/distribution/pi_runtime/``; the installer copies both to
``.concorde/tools/pi-runtime/`` and runs ``npm ci``, which installs exactly the locked versions and
checks each package's integrity hash, without running install scripts.

A later install with the same pin or lockfile keeps what it already placed.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import platform
import shutil
import subprocess
import tarfile
import urllib.request
from collections.abc import Callable
from pathlib import Path

TOOLS = ".concorde/tools"
D2_RECORD = f"{TOOLS}/d2.json"
PI_RUNTIME = f"{TOOLS}/pi-runtime"
PI_RUNTIME_RECORD = f"{TOOLS}/pi-runtime.json"
PI_RUNTIME_SOURCE = "src/concorde/distribution/pi_runtime"
PI_RUNTIME_ENTRY = "node_modules/@anthropic-ai/sandbox-runtime/dist/index.js"
_SYSTEMS = {"linux": "linux", "darwin": "macos", "windows": "windows"}
_MACHINES = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}


class ToolError(RuntimeError):
    """A pinned program could not be placed, with the reason and what to do about it."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def platform_key(system: str | None = None, machine: str | None = None) -> str:
    """The release platform name of this machine, such as ``linux-amd64``."""
    system = (system or platform.system()).lower()
    machine = (machine or platform.machine()).lower()
    if system not in _SYSTEMS or machine not in _MACHINES:
        raise ToolError(
            "unsupported_platform",
            f"d2 has no pinned release for {system}/{machine}; install d2 from "
            "https://github.com/d2lang/d2/releases yourself and put it on PATH, or set "
            "CONCORDE_D2 to its path",
        )
    return f"{_SYSTEMS[system]}-{_MACHINES[machine]}"


def _download(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def d2_path(project: Path, key: str) -> Path:
    return project / TOOLS / ("d2.exe" if key.startswith("windows-") else "d2")


def install_d2(
    project: Path,
    descriptor: dict,
    *,
    fetch: Callable[[str], bytes] = _download,
    key: str | None = None,
) -> dict:
    """Place the pinned ``d2`` under ``.concorde/tools/`` and return what was placed."""
    pin = descriptor.get("tools", {}).get("d2")
    if not isinstance(pin, dict):
        raise ToolError(
            "invalid_descriptor", "concorde.json pins no d2 release under tools.d2"
        )
    key = key or platform_key()
    version = pin["version"]
    expected = pin["sha256"].get(key)
    if expected is None:
        raise ToolError(
            "unsupported_platform",
            f"concorde.json pins no d2 {version} archive for {key}; install d2 from "
            "https://github.com/d2lang/d2/releases yourself and put it on PATH, or set "
            "CONCORDE_D2 to its path",
        )
    target = d2_path(project, key)
    record_path = project / D2_RECORD
    placed = {
        "version": version,
        "platform": key,
        "sha256": expected,
        "path": target.relative_to(project).as_posix(),
    }
    try:
        if target.is_file() and json.loads(record_path.read_text()) == placed:
            return placed
    except (OSError, ValueError):
        pass
    url = pin["url"].format(version=version, platform=key)
    try:
        archive = fetch(url)
    except Exception as error:  # every download failure is reported the same way
        raise ToolError(
            "d2_unavailable",
            f"downloading d2 {version} for {key} from {url} failed: {error}; check the network "
            "and install again, or install without d2 and put d2 on PATH yourself",
        ) from error
    actual = hashlib.sha256(archive).hexdigest()
    if actual != expected:
        raise ToolError(
            "d2_digest_mismatch",
            f"{url} has SHA-256 {actual}, but concorde.json pins {expected} for {key}; "
            "nothing was installed",
        )
    member = f"d2-{version}/bin/{target.name}"
    try:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as bundle:
            source = bundle.extractfile(member)
            program = source.read() if source is not None else None
    except (tarfile.TarError, KeyError, OSError) as error:
        raise ToolError(
            "d2_archive_invalid", f"{url} holds no readable {member}: {error}"
        ) from error
    if program is None:
        raise ToolError("d2_archive_invalid", f"{url} holds no regular file {member}")
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".partial")
    partial.write_bytes(program)
    partial.chmod(0o755)
    os.replace(partial, target)
    record_path.write_text(json.dumps(placed, indent=2) + "\n")
    return placed


def install_pi_runtime(
    project: Path,
    package: Path,
    *,
    run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> dict:
    """Place the locked pi runtime under ``.concorde/tools/pi-runtime/``; return what was placed."""
    source = package / PI_RUNTIME_SOURCE
    lock = source / "package-lock.json"
    try:
        locked = json.loads(lock.read_text())
        version = locked["packages"]["node_modules/@anthropic-ai/sandbox-runtime"][
            "version"
        ]
    except (OSError, ValueError, KeyError) as error:
        raise ToolError(
            "invalid_descriptor",
            f"{lock} is missing or pins no @anthropic-ai/sandbox-runtime: {error}",
        ) from error
    target = project / PI_RUNTIME
    record_path = project / PI_RUNTIME_RECORD
    placed = {
        "package": "@anthropic-ai/sandbox-runtime",
        "version": version,
        "lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(),
        "path": PI_RUNTIME,
    }
    try:
        if (target / PI_RUNTIME_ENTRY).is_file() and json.loads(
            record_path.read_text()
        ) == placed:
            return placed
    except (OSError, ValueError):
        pass
    npm = shutil.which("npm")
    if npm is None:
        raise ToolError(
            "npm_missing",
            "the pi runtime is installed with npm, which is not on PATH; install Node.js and "
            "npm, or install without --pi",
        )
    target.mkdir(parents=True, exist_ok=True)
    for name in ("package.json", "package-lock.json"):
        shutil.copy2(source / name, target / name)
    command = [npm, "ci", "--ignore-scripts", "--no-audit", "--no-fund", "--omit=dev"]
    try:
        completed = run(
            command, cwd=target, capture_output=True, text=True, timeout=600
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ToolError(
            "pi_runtime_failed", f"`{' '.join(command)}` in {target} failed: {error}"
        ) from error
    if completed.returncode != 0 or not (target / PI_RUNTIME_ENTRY).is_file():
        output = ((completed.stdout or "") + (completed.stderr or ""))[-2000:]
        raise ToolError(
            "pi_runtime_failed",
            f"`{' '.join(command)}` in {target} exited with {completed.returncode} and left no "
            f"{PI_RUNTIME_ENTRY}; its output ends with: {output.strip() or '(empty)'}",
        )
    record_path.write_text(json.dumps(placed, indent=2) + "\n")
    return placed


__all__ = [
    "D2_RECORD",
    "PI_RUNTIME",
    "TOOLS",
    "ToolError",
    "d2_path",
    "install_d2",
    "install_pi_runtime",
    "platform_key",
]
