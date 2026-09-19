"""Installer-owned virtual environment lifecycle for paired Concorde operations."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

MARKER_NAME = ".concorde-runtime.json"
MARKER_SCHEMA = 2
_LOCK_LINE = re.compile(r"^langgraph==([0-9]+(?:\.[0-9]+){2})$")
_SEMVER = re.compile(r"^v?([0-9]+)\.([0-9]+)\.([0-9]+)(?:[-+].*)?$")
# The Pi worker extensions a worker with children loads, installed from the package's pinned lock.
PI_SOURCES = ("pi/package.json", "pi/package-lock.json", "pi/.npmrc")
PI_INSTALL_RELATIVE = "share/concorde/pi"
PI_SUBAGENTS = "pi-subagents"


class ManagedRuntimeError(ValueError):
    """A managed runtime cannot be planned or provisioned safely."""


@dataclass(frozen=True)
class ManagedRuntimeSpec:
    venv: str
    requirements: str
    launcher: str
    python: str
    requirements_sha256: str
    runtime_sha256: str
    langgraph_version: str
    concorde_version: str
    skills: tuple[str, ...]
    pi_lock_sha256: str
    pi_subagents_version: str


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _safe_relative(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ManagedRuntimeError(f"{field} must be a string")
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts or "\\" in value:
        raise ManagedRuntimeError(
            f"{field} must be a safe project-relative path: {value!r}"
        )
    return candidate.as_posix()


def _json_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    if path.is_symlink() or not path.is_file():
        raise ManagedRuntimeError(f"{label} must be one real file: {path}")
    content = path.read_bytes()
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ManagedRuntimeError(
            f"{label} must be valid UTF-8 JSON: {path}"
        ) from error
    if not isinstance(value, dict):
        raise ManagedRuntimeError(f"{label} must be one JSON object: {path}")
    return value, content


def load_runtime_spec(
    package_root: Path,
    manifest: Mapping[str, Any],
) -> ManagedRuntimeSpec:
    configuration = manifest.get("runtime")
    if not isinstance(configuration, Mapping):
        raise ManagedRuntimeError("runtime must be one manifest object")
    venv = _safe_relative(configuration.get("venv"), "runtime.venv")
    requirements = _safe_relative(
        configuration.get("requirements"), "runtime.requirements"
    )
    launcher = _safe_relative(configuration.get("launcher"), "runtime.launcher")
    python = configuration.get("python")
    if python != ">=3.11":
        raise ManagedRuntimeError("runtime.python must be '>=3.11'")
    if venv != ".concorde/.venv":
        raise ManagedRuntimeError("runtime.venv must be .concorde/.venv")
    from .build import SKILL_NAMES

    requirement_path = package_root / requirements
    launcher_path = package_root / launcher
    for label, path in (
        ("requirements", requirement_path),
        ("launcher", launcher_path),
    ):
        if path.is_symlink() or not path.is_file():
            raise ManagedRuntimeError(f"runtime {label} must be one real file: {path}")
    content = requirement_path.read_bytes()
    lines = [
        line.strip() for line in content.decode("utf-8").splitlines() if line.strip()
    ]
    if len(lines) != 1 or (match := _LOCK_LINE.fullmatch(lines[0])) is None:
        raise ManagedRuntimeError(
            "runtime requirements must contain exactly one pinned langgraph version"
        )
    version = manifest.get("version")
    if not isinstance(version, str) or not version:
        raise ManagedRuntimeError("manifest version must be a non-empty string")
    pi_contents = []
    for relative in PI_SOURCES:
        source = package_root.joinpath(*PurePosixPath(relative).parts)
        if source.is_symlink() or not source.is_file():
            raise ManagedRuntimeError(
                f"Pi worker package source must be one real file: {relative}"
            )
        pi_contents.append(source.read_bytes())
    pi_package, _ = _json_object(package_root / PI_SOURCES[0], "Pi worker package")
    pi_subagents_version = (pi_package.get("dependencies") or {}).get(PI_SUBAGENTS)
    if not isinstance(pi_subagents_version, str) or not _SEMVER.fullmatch(
        pi_subagents_version
    ):
        raise ManagedRuntimeError(
            f"Pi worker package must pin {PI_SUBAGENTS} to one exact version"
        )
    pi_lock_sha256 = _sha256(b"\0".join(pi_contents))
    requirements_sha256 = _sha256(content)
    runtime_sha256 = _sha256(
        (requirements_sha256 + "\n" + pi_lock_sha256).encode("utf-8")
    )
    return ManagedRuntimeSpec(
        venv=venv,
        requirements=requirements,
        launcher=launcher,
        python=python,
        requirements_sha256=requirements_sha256,
        runtime_sha256=runtime_sha256,
        langgraph_version=match.group(1),
        concorde_version=version,
        skills=SKILL_NAMES,
        pi_lock_sha256=pi_lock_sha256,
        pi_subagents_version=pi_subagents_version,
    )


def runtime_python(venv: Path) -> Path:
    relative = Path("Scripts/python.exe") if os.name == "nt" else Path("bin/python")
    return venv / relative


def _runtime_path(target: Path, spec: ManagedRuntimeSpec) -> Path:
    target = target.resolve()
    runtime = target.joinpath(*PurePosixPath(spec.venv).parts)
    expected = target / ".concorde/.venv"
    if runtime != expected:
        raise ManagedRuntimeError(
            f"managed runtime escaped its fixed boundary: {runtime}"
        )
    current = target
    for part in PurePosixPath(spec.venv).parts[:-1]:
        current /= part
        if current.is_symlink():
            raise ManagedRuntimeError(
                f"managed runtime path contains a symlink: {current.relative_to(target)}"
            )
        if current.exists() and not current.is_dir():
            raise ManagedRuntimeError(
                f"managed runtime parent is not a directory: {current.relative_to(target)}"
            )
    return runtime


def _read_marker(runtime: Path) -> dict[str, Any] | None:
    marker = runtime / MARKER_NAME
    if marker.is_symlink() or not marker.is_file():
        return None
    try:
        value = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict):
        return None
    if value.get("schema_version") != MARKER_SCHEMA or value.get("owner") != "concorde":
        return None
    return value


def _receipt_owns_runtime(receipt: Mapping[str, Any], spec: ManagedRuntimeSpec) -> bool:
    runtime = receipt.get("runtime")
    return isinstance(runtime, Mapping) and runtime.get("path") == spec.venv


def _marker_owns_runtime(
    marker: Mapping[str, Any] | None, spec: ManagedRuntimeSpec
) -> bool:
    return bool(marker and marker.get("path") == spec.venv)


def _offline_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_INDEX": "1",
            "PYTHONNOUSERSITE": "1",
            "UV_OFFLINE": "1",
            "NPM_CONFIG_AUDIT": "false",
            "NPM_CONFIG_FUND": "false",
            "NPM_CONFIG_OFFLINE": "true",
        }
    )
    return environment


def _run(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        env=dict(environment) if environment is not None else None,
        text=True,
        capture_output=True,
    )


def _tool_version(
    command: str, cwd: Path, label: str
) -> tuple[str, tuple[int, int, int]]:
    try:
        result = _run([command, "--version"], cwd=cwd, environment=os.environ)
    except OSError as error:
        raise ManagedRuntimeError(
            f"{label} is required to install the Pi worker extensions: {error}"
        ) from error
    value = _checked(result, f"{label} version check").strip()
    match = _SEMVER.fullmatch(value)
    if match is None:
        raise ManagedRuntimeError(f"{label} returned an unsupported version: {value!r}")
    return value, tuple(int(item) for item in match.groups())


def _install_pi(runtime: Path, framework: Path, cwd: Path) -> None:
    """Install the Pi worker extensions from the package's pinned lock into the managed runtime."""
    _tool_version("npm", cwd, "npm")
    root = runtime.joinpath(*PurePosixPath(PI_INSTALL_RELATIVE).parts)
    root.mkdir(parents=True, exist_ok=False)
    for relative in PI_SOURCES:
        source = framework.joinpath(*PurePosixPath(relative).parts)
        if source.is_symlink() or not source.is_file():
            raise ManagedRuntimeError(
                f"installed Pi worker package source is missing: {source}"
            )
        destination = root / PurePosixPath(relative).name
        shutil.copyfile(source, destination)
        destination.chmod(0o644)
    environment = os.environ.copy()
    environment.update(
        {
            "NPM_CONFIG_AUDIT": "false",
            "NPM_CONFIG_FUND": "false",
            "NPM_CONFIG_UPDATE_NOTIFIER": "false",
        }
    )
    result = _run(
        [
            "npm",
            "--prefix",
            str(root),
            "ci",
            "--ignore-scripts",
            "--no-audit",
            "--no-fund",
        ],
        cwd=cwd,
        environment=environment,
    )
    _checked(result, "Pi worker extension installation")


def _verify_pi(runtime: Path, spec: ManagedRuntimeSpec) -> None:
    package_root = (
        runtime.joinpath(*PurePosixPath(PI_INSTALL_RELATIVE).parts)
        / "node_modules"
        / PI_SUBAGENTS
    )
    package, _ = _json_object(
        package_root / "package.json", "installed pi-subagents package"
    )
    if (
        package.get("name") != PI_SUBAGENTS
        or package.get("version") != spec.pi_subagents_version
    ):
        raise ManagedRuntimeError(
            "installed pi-subagents package identity is mismatched"
        )
    entry = package_root / "index.ts"
    if entry.is_symlink() or not entry.is_file():
        raise ManagedRuntimeError(
            f"installed pi-subagents entry point is missing: {entry}"
        )


def _healthy(runtime: Path, spec: ManagedRuntimeSpec) -> bool:
    python = runtime_python(runtime)
    if not python.is_file():
        return False
    code = (
        "import importlib.metadata,sys;"
        f"assert importlib.metadata.version('langgraph') == {spec.langgraph_version!r};"
        "assert sys.prefix"
    )
    try:
        result = _run(
            [str(python), "-I", "-c", code],
            cwd=runtime.parent,
            environment=_offline_environment(),
        )
    except OSError:
        return False
    return result.returncode == 0


def plan_runtime(
    target: Path,
    spec: ManagedRuntimeSpec,
    receipt: Mapping[str, Any],
) -> dict[str, str]:
    item = {
        "path": spec.venv,
        "role": "runtime",
        "sha256": spec.runtime_sha256,
    }
    try:
        runtime = _runtime_path(target, spec)
    except ManagedRuntimeError as error:
        return {**item, "action": "conflict", "reason": str(error)}
    if runtime.is_symlink():
        return {
            **item,
            "action": "conflict",
            "reason": f"managed runtime must not be a symlink: {spec.venv}",
        }
    if not runtime.exists():
        return {**item, "action": "create"}
    if not runtime.is_dir():
        return {
            **item,
            "action": "conflict",
            "reason": f"managed runtime must be a real directory: {spec.venv}",
        }
    marker = _read_marker(runtime)
    if not (_receipt_owns_runtime(receipt, spec) or _marker_owns_runtime(marker, spec)):
        return {
            **item,
            "action": "conflict",
            "reason": f"existing managed runtime path is not owned by Concorde: {spec.venv}",
        }
    matches = bool(
        marker
        and marker.get("requirements_sha256") == spec.requirements_sha256
        and marker.get("pi_lock_sha256") == spec.pi_lock_sha256
        and marker.get("verified_skills") == list(spec.skills)
    )
    if matches and _healthy(runtime, spec):
        return {**item, "action": "unchanged"}
    return {
        **item,
        "action": "rebuild",
        "reason": "managed runtime lock or health differs from the desired package",
    }


def _checked(result: subprocess.CompletedProcess[str], label: str) -> str:
    if result.returncode == 0:
        return result.stdout
    detail = (result.stderr or result.stdout).strip()
    if len(detail) > 1200:
        detail = detail[-1200:]
    raise ManagedRuntimeError(f"{label} failed with exit {result.returncode}: {detail}")


def _verify_skills(
    target: Path,
    framework: Path,
    spec: ManagedRuntimeSpec,
    runtime: Path,
) -> tuple[str, ...]:
    """Run every public Skill's launcher runtime check inside the managed runtime itself.

    The check must exercise the environment being verified, not the interpreter that runs the
    installer: it is started with the runtime's own interpreter and must report that runtime as
    its prefix, so a launcher that ended up in another environment fails verification."""
    launcher = framework.joinpath(*PurePosixPath(spec.launcher).parts)
    python = runtime_python(runtime)
    environment = _offline_environment()
    observed_python: str | None = None
    verified: list[str] = []
    for skill in spec.skills:
        result = _run(
            [str(python), str(launcher), skill, "--runtime-check"],
            cwd=target,
            environment=environment,
        )
        output = _checked(result, f"operation runtime check for {skill}")
        try:
            payload = json.loads(output)
        except json.JSONDecodeError as error:
            raise ManagedRuntimeError(
                f"operation runtime check for {skill} returned invalid JSON"
            ) from error
        if not isinstance(payload, dict) or payload.get("operation") != skill:
            raise ManagedRuntimeError(
                f"operation runtime check for {skill} returned mismatched identity"
            )
        if payload.get("langgraph") != spec.langgraph_version:
            raise ManagedRuntimeError(
                f"operation runtime check for {skill} returned mismatched LangGraph version"
            )
        prefix = payload.get("prefix")
        if (
            not isinstance(prefix, str)
            or not prefix
            or Path(prefix).resolve() != runtime.resolve()
        ):
            raise ManagedRuntimeError(
                f"operation runtime check for {skill} ran outside the managed runtime: {prefix!r}"
            )
        observed_python = payload.get("python_version")
        if not isinstance(observed_python, str) or not observed_python:
            raise ManagedRuntimeError(
                f"operation runtime check for {skill} omitted its Python version"
            )
        verified.append(skill)
    if observed_python is None:
        raise ManagedRuntimeError("managed runtime verified no skills")
    return tuple(verified)


def _write_marker(
    runtime: Path,
    spec: ManagedRuntimeSpec,
    python_version: str,
) -> None:
    value = {
        "schema_version": MARKER_SCHEMA,
        "owner": "concorde",
        "path": spec.venv,
        "concorde_version": spec.concorde_version,
        "requirements_sha256": spec.requirements_sha256,
        "runtime_sha256": spec.runtime_sha256,
        "python_version": python_version,
        "pi_lock_sha256": spec.pi_lock_sha256,
        "pi_subagents_version": spec.pi_subagents_version,
        "verified_skills": list(spec.skills),
    }
    content = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    marker = runtime / MARKER_NAME
    with tempfile.NamedTemporaryFile(
        dir=runtime, prefix=".concorde-runtime-", delete=False
    ) as handle:
        staged = Path(handle.name)
        handle.write(content)
    staged.replace(marker)
    marker.chmod(0o644)


def _python_version(python: Path, cwd: Path) -> str:
    result = _run(
        [str(python), "-I", "-c", "import platform;print(platform.python_version())"],
        cwd=cwd,
        environment=_offline_environment(),
    )
    return _checked(result, "managed Python version check").strip()


def provision_runtime(
    target: Path,
    framework: Path,
    spec: ManagedRuntimeSpec,
    action: Mapping[str, str],
    *,
    bootstrap_python: str | None = None,
) -> dict[str, Any]:
    target = target.resolve()
    runtime = _runtime_path(target, spec)
    selected = action.get("action")
    if selected not in {"create", "rebuild", "unchanged"}:
        raise ManagedRuntimeError(f"cannot provision runtime action: {selected!r}")
    changed = selected in {"create", "rebuild"}
    bootstrap = bootstrap_python or sys.executable
    try:
        if selected == "rebuild":
            if runtime.is_symlink() or not runtime.is_dir():
                raise ManagedRuntimeError(
                    f"obsolete managed runtime is no longer one real directory: {spec.venv}"
                )
            shutil.rmtree(runtime)
        if selected == "create" and (runtime.exists() or runtime.is_symlink()):
            raise ManagedRuntimeError(
                f"managed runtime appeared after preview and will not be overwritten: {spec.venv}"
            )
        if changed:
            runtime.parent.mkdir(parents=True, exist_ok=True)
            _checked(
                _run(
                    [bootstrap, "-m", "venv", str(runtime)],
                    cwd=target,
                    environment=os.environ,
                ),
                "managed virtual environment creation",
            )
            python = runtime_python(runtime)
            requirements = framework.joinpath(*PurePosixPath(spec.requirements).parts)
            _checked(
                _run(
                    [
                        str(python),
                        "-m",
                        "pip",
                        "install",
                        "--disable-pip-version-check",
                        "--no-input",
                        "--requirement",
                        str(requirements),
                    ],
                    cwd=target,
                    environment=os.environ,
                ),
                "managed runtime dependency installation",
            )
            _install_pi(runtime, framework, target)
        python = runtime_python(runtime)
        python_version = _python_version(python, target)
        verified = _verify_skills(target, framework, spec, runtime)
        if verified != spec.skills:
            raise ManagedRuntimeError("managed runtime did not verify every skill")
        _verify_pi(runtime, spec)
        _write_marker(runtime, spec, python_version)
    except Exception:
        if (
            changed
            and runtime.exists()
            and not runtime.is_symlink()
            and runtime.is_dir()
        ):
            shutil.rmtree(runtime)
        raise
    return {
        "path": spec.venv,
        "python": spec.python,
        "python_version": python_version,
        "requirements": spec.requirements,
        "requirements_sha256": spec.requirements_sha256,
        "runtime_sha256": spec.runtime_sha256,
        "launcher": spec.launcher,
        "verified_skills": list(verified),
        "pi": {
            "install_relative": PI_INSTALL_RELATIVE,
            "lock_sha256": spec.pi_lock_sha256,
            "pi_subagents": spec.pi_subagents_version,
        },
    }
