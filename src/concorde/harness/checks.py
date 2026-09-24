"""The check service: run the configured checks of some Modules of a worktree, read-only.

Each check runs through ``execute_check`` with the worktree as project root, so a check can read
the worktree but never change it. Before and after the run the service measures the Module's
``check_revision`` (its implementation files, its checks' definitions and inputs, and the policy);
a difference means the check vouched for input that changed, and the call fails.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

from ..errors import evidence, link
from ..spec.repository import SpecRepository
from ..spec.repository_base import SpecError, bound_by
from .check_executor import CHECK_POLICY, CheckSandboxError, execute_check


class CheckError(SpecError):
    """A configured check that cannot be run or whose result cannot be trusted."""

    CODES = {
        "invalid_check": (
            "a configured check needs a nonempty argv and a positive timeout_seconds",
            "correct the check's entry in .concorde/config.json",
        ),
        "check_input_missing": (
            "every declared input of a configured check must exist as a regular file or "
            "directory, because its result is bound to the inputs' digest",
            "restore the input or correct the check's inputs",
        ),
        "check_sandbox_unavailable": (
            "configured checks run only inside the read-only bubblewrap boundary",
            "install a root-owned system bubblewrap, or run on a host that allows it",
        ),
        "stale_evidence": (
            "a check result vouches only for inputs that stayed the same while it ran",
            "let the worktree settle and run the checks again",
        ),
        "unknown_module": (
            "checks run only for Modules the registry registers",
            "name registered Modules",
        ),
    }


FRAMEWORK_SRC = Path(__file__).resolve().parents[2]


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inputs(root: Path, check: dict) -> list[tuple[str, str]]:
    digests = []
    for relative in check.get("inputs", []):
        path = root / relative
        if path.is_symlink() or not path.exists():
            raise CheckError(
                f"input {relative} of check {check['id']} ({check['module']}) is missing "
                "or a symbolic link",
                "check_input_missing",
            )
        if path.is_dir():
            for item in sorted(path.rglob("*")):
                if "__pycache__" in item.parts or item.is_symlink():
                    continue
                if item.is_file():
                    digests.append(
                        (item.relative_to(root).as_posix(), _file_digest(item))
                    )
        elif path.is_file():
            digests.append((relative, _file_digest(path)))
        else:
            raise CheckError(
                f"input {relative} of check {check['id']} is not a regular file",
                "check_input_missing",
            )
    return digests


def check_revision(repository: SpecRepository, module: str) -> str:
    """The digest a stored check result of ``module`` is current against."""
    root = repository.root
    implementation = [
        (path, _file_digest(root / path)) for path in repository.bound_files(module)
    ]
    checks = [
        check for check in repository.checks.values() if check["module"] == module
    ]
    value = {
        "implementation": implementation,
        "checks": [
            {"definition": check, "inputs": _inputs(root, check)} for check in checks
        ],
        "policy": CHECK_POLICY,
    }
    return (
        "sha256:"
        + hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
    )


def affected_modules(repository: SpecRepository, changed) -> list[str]:
    """Every Module whose SpecScope or ImplementationScope contains a changed path."""
    result = []
    for identity in repository.modules:
        scope = set(repository.spec_scope(identity))
        entries = repository.implementation_scope(identity)
        if any(
            path in scope or any(bound_by(entry, path) for entry in entries)
            for path in changed
        ):
            result.append(identity)
    return result


def _argv(check: dict) -> list[str]:
    argv = check.get("argv")
    if (
        not isinstance(argv, list)
        or not argv
        or any(not isinstance(item, str) or not item for item in argv)
    ):
        raise CheckError(f"check {check['id']} needs a nonempty argv", "invalid_check")
    return [sys.executable if item == "{python}" else item for item in argv]


def _timeout(check: dict) -> float:
    value = check.get("timeout_seconds")
    if type(value) not in (int, float) or value <= 0:
        raise CheckError(
            f"check {check['id']} needs a positive timeout_seconds", "invalid_check"
        )
    return float(value)


def environment() -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "PYTHONPATH": str(FRAMEWORK_SRC),
    }


def run_checks(
    worktree: Path,
    *,
    modules=None,
    changed=None,
    log_directory: Path,
) -> list[dict]:
    """Run the configured checks of the selected Modules; one result per check, in order."""
    worktree = Path(worktree)
    repository = SpecRepository(worktree)
    selected = (
        list(modules)
        if modules is not None
        else affected_modules(repository, changed or ())
    )
    for identity in selected:
        if identity not in repository.modules:
            raise CheckError(f"unregistered Module: {identity}", "unknown_module")
    log_directory = Path(log_directory)
    log_directory.mkdir(parents=True, exist_ok=True)
    results = []
    for check in repository.checks.values():
        if check["module"] not in selected:
            continue
        argv, timeout = _argv(check), _timeout(check)
        before = check_revision(repository, check["module"])
        log = log_directory / f"{check['id']}.log"
        try:
            outcome = execute_check(
                worktree, argv, timeout=timeout, environment=environment()
            )
        except CheckSandboxError as error:
            log.write_bytes(
                (error.stdout or b"")
                + b"\n"
                + (error.stderr or b"")
                + str(error).encode()
            )
            raise CheckError(
                f"check {check['id']} could not run in the read-only boundary: {error}",
                "check_sandbox_unavailable",
            ) from error
        log.write_bytes(outcome.stdout + b"\n" + outcome.stderr)
        if check_revision(SpecRepository(worktree), check["module"]) != before:
            raise CheckError(
                f"the input of check {check['id']} changed while it ran",
                "stale_evidence",
            )
        results.append(
            {
                "check_id": check["id"],
                "module": check["module"],
                "status": "timeout"
                if outcome.timed_out
                else ("passed" if outcome.returncode == 0 else "failed"),
                "exit_code": -1 if outcome.timed_out else outcome.returncode,
                "source_digest": before,
                "log": log.as_posix(),
                "log_digest": "sha256:" + _file_digest(log),
            }
        )
    return results


LOG_TAIL = 3000


def check_error(result: dict) -> dict:
    """The error link of one check result that did not pass, with the end of its log."""
    try:
        tail = Path(result["log"]).read_bytes()[-LOG_TAIL:].decode("utf-8", "replace")
    except OSError as error:
        tail = f"(the log cannot be read: {error})"
    timeout = result["status"] == "timeout"
    outcome = "timed out" if timeout else f"failed with exit code {result['exit_code']}"
    return link(
        "check",
        result["check_id"],
        "check_timed_out" if timeout else "check_failed",
        f"the configured check {result['check_id']} of {result['module']} {outcome}; its "
        f"log {result['log']} ends with:\n{tail.strip() or '(empty)'}",
        reason="capability",
        explanation="a configured check only measures the code it runs against",
        evidence=[evidence("log", result["log"], result.get("log_digest", ""))],
    )


__all__ = ["affected_modules", "check_error", "check_revision", "run_checks"]
