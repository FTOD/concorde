"""The check service: run the configured checks of some Modules of a worktree, read-only.

The checks are read from the worktree's checks files, ``.concorde/checks/<module id>.json``,
Check execution's own format, whose Module identities are labels. Which Modules' checks run, which
files each Module's result depends on, which tests a selective check runs and which interpreter
``{python}`` stands for are the caller's to say: the service reads no Spec. Each check runs
through ``execute_check`` with the worktree as project root, so a check can read the worktree but
never change it. Before and after the run the service measures the check's input (the files the
caller named for its Module, its checks' definitions and inputs, and the policy); a difference
means the check vouched for input that changed, and the call fails. A selective check's measured
digest also covers the selected Modules and the tests it selected.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Iterable, Mapping
from pathlib import Path

from ...kernel.errors import evidence, link
from ...kernel.refusal import KernelError
from ...kernel.schema import checked_path, register, safe_path
from ...kernel.tracing import layout
from ...kernel.tracing.layout import primary_worktree
from ...kernel.tracing.node import Node
from .check_executor import CHECK_POLICY, CheckSandboxError, execute_check

# contract.checks.check-trace, version 1: the content of one check's trace node.
CHECK_TRACE = "concorde-check-trace"
register(
    CHECK_TRACE,
    1,
    {
        "type": "object",
        "additionalProperties": False,
        "required": ["status", "exit_code", "source_digest", "argv", "selected_tests"],
        "properties": {
            "status": {"enum": ["passed", "failed", "timeout", "refused"]},
            "exit_code": {"anyOf": [{"type": "null"}, {"type": "integer"}]},
            "source_digest": {"type": "string", "minLength": 1},
            "argv": {"type": "array", "items": {"type": "string"}},
            "selected_tests": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
            },
        },
    },
)

# The configured checks, one file per Module named by its identity.
CHECKS_DIR = ".concorde/checks"
# The fields of one checks file entry.
ENTRY_FIELDS = ("id", "argv", "env", "when", "timeout_seconds", "inputs")
# A Module identity, the name of a checks file without ``.json``.
IDENTITY = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9-]+)*$")


class CheckError(Exception):
    """A configured check that cannot be run or whose result cannot be trusted, with its
    location, reason, remediation and causes."""

    CODES = {
        "invalid_check": (
            "a checks file is a JSON object whose only field, checks, lists entries with the "
            "fields id, argv, env, when, timeout_seconds and inputs; a check needs a nonempty "
            "argv, a positive timeout_seconds and an id unique in the project",
            "correct the check's entry in .concorde/checks/<its module>.json",
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
        "project_python_missing": (
            "{python} in a check stands for the project's own interpreter, which the caller "
            "names (in Concorde `python` in .concorde/config.json), never Concorde's",
            "set `python` in .concorde/config.json to the project's interpreter, or create it "
            "where the configuration says",
        ),
        "system_error": (
            "the operating system refused an operation Check execution needed",
            "repair what the message names and run the checks again",
        ),
    }

    def __init__(
        self,
        message: str,
        code: str = "invalid_check",
        field: str = "",
        *,
        path: str | None = None,
        subject: str | None = None,
        reason: str | None = None,
        remediation: str | None = None,
        causes: Iterable["CheckError"] = (),
    ):
        super().__init__(message)
        self.code, self.field, self.message = code, field, message
        self.path, self.subject = path, subject
        known = self.CODES.get(code, ("", ""))
        self.reason = reason or known[0]
        self.remediation = remediation or known[1]
        self.causes = tuple(causes)

    def where(self) -> str:
        parts = [self.path or ""]
        if self.field:
            parts.append(f"field {self.field}" if self.path else self.field)
        if self.subject:
            parts.append(self.subject)
        return ", ".join(part for part in parts if part)

    def describe(self) -> str:
        where = self.where()
        return (
            f"{self.code}: {self}"
            + (f" (at {where})" if where else "")
            + f"; why: {self.reason}; to fix: {self.remediation}"
        )


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
                path=relative,
                subject=check["id"],
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
                f"input {relative} of check {check['id']} ({check['module']}) is not a "
                "regular file",
                "check_input_missing",
                path=relative,
                subject=check["id"],
            )
    return digests


def checks_files(worktree: Path) -> list[tuple[str, str]]:
    """The checks files of a worktree as ``(path, Module id)``, in the byte order of their
    names; none when the worktree has no checks directory."""
    try:
        directory = checked_path(Path(worktree), CHECKS_DIR)
    except KernelError as error:
        raise CheckError(
            f"{CHECKS_DIR} in {worktree} is reached through a symbolic link: {error}",
            path=CHECKS_DIR,
            reason="the configured checks are read only from the worktree's own files",
            remediation=f"replace the link with a real {CHECKS_DIR} directory",
        ) from error
    if not directory.exists():
        return []
    if not directory.is_dir():
        raise CheckError(
            f"{CHECKS_DIR} in {worktree} is not a directory",
            path=CHECKS_DIR,
            reason="the configured checks are one file per Module under this directory",
            remediation="move the file away and put each Module's checks in "
            f"{CHECKS_DIR}/<module id>.json",
        )
    result = []
    for name in sorted(os.listdir(directory)):
        relative = f"{CHECKS_DIR}/{name}"
        module = name.removesuffix(".json") if name.endswith(".json") else ""
        entry = directory / name
        if not IDENTITY.fullmatch(module) or entry.is_symlink() or not entry.is_file():
            state = (
                "a symbolic link"
                if entry.is_symlink()
                else "not a regular file"
                if not entry.is_file()
                else "not named <module id>.json"
            )
            raise CheckError(
                f"{relative} is {state}",
                path=relative,
                reason=f"{CHECKS_DIR} holds only the regular files <module id>.json, each "
                "with the configured checks of the Module it names",
                remediation="rename the file after its Module's identity or move it out of "
                f"{CHECKS_DIR}",
            )
        result.append((relative, module))
    return result


def configured_checks(worktree: Path) -> list[dict]:
    """The worktree's configured checks in configuration order, each carrying after its ``id``
    the ``module`` its file is named after; ``invalid_check`` for a checks file or entry that
    breaks the format. ``argv``, ``env``, ``when`` and ``timeout_seconds`` are checked when the
    check runs."""
    root = Path(worktree)
    result, seen = [], {}
    for path, module in checks_files(root):
        try:
            value = json.loads((root / path).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as error:
            raise CheckError(
                f"{path} cannot be read as JSON: {error}",
                path=path,
                remediation='write {"checks": [...]} with one entry per check',
            ) from error
        if not isinstance(value, dict) or set(value) != {"checks"}:
            raise CheckError(
                f"{path} must be a JSON object with exactly the field checks, not "
                f"{json.dumps(value)[:200]}",
                path=path,
                remediation='write {"checks": [...]} with one entry per check',
            )
        if not isinstance(value["checks"], list):
            raise CheckError(
                f"the checks of {path} must be an array, not a JSON "
                f"{type(value['checks']).__name__}",
                "invalid_check",
                "/checks",
                path=path,
            )
        for position, entry in enumerate(value["checks"]):
            result.append(_entry(path, module, position, entry, seen))
    return result


def _entry(path: str, module: str, position: int, entry, seen: dict) -> dict:
    pointer = f"/checks/{position}"
    if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
        raise CheckError(
            f"configured check {position} of {path} needs an id: {entry!r}"[:300],
            "invalid_check",
            pointer,
            path=path,
        )
    key = entry["id"]
    extra = sorted(set(entry) - set(ENTRY_FIELDS))
    if extra:
        raise CheckError(
            f"configured check {key!r} of {path} has the field(s) {', '.join(extra)}, "
            f"which a checks file entry does not have"
            + (
                f"; it belongs to {module}, the Module its file is named after"
                if "module" in extra
                else ""
            ),
            "invalid_check",
            f"{pointer}/{extra[0]}",
            path=path,
            remediation="remove the field"
            + (
                f", or move the check into {CHECKS_DIR}/<its module id>.json"
                if "module" in extra
                else ""
            ),
        )
    if not IDENTITY.fullmatch(key):
        raise CheckError(
            f"configured check id {key!r} of {path} is not an identity",
            "invalid_check",
            f"{pointer}/id",
            path=path,
        )
    if key in seen:
        raise CheckError(
            f"the configured check id {key} is used in {seen[key]} and again in {path}",
            "invalid_check",
            f"{pointer}/id",
            path=path,
            remediation="rename one of the two checks",
        )
    seen[key] = path
    inputs = entry.get("inputs", [])
    if (
        not isinstance(inputs, list)
        or any(not isinstance(item, str) for item in inputs)
        or len(set(inputs)) != len(inputs)
    ):
        raise CheckError(
            f"the inputs of configured check {key} must be an array of distinct strings, "
            f"not {inputs!r}"[:300],
            "invalid_check",
            f"{pointer}/inputs",
            path=path,
        )
    for relative in inputs:
        try:
            safe_path(relative, relative)
        except KernelError as error:
            raise CheckError(
                f"input {relative!r} of configured check {key} ({module}) is not a canonical "
                f"project-relative path inside the worktree: {error}",
                "invalid_check",
                f"{pointer}/inputs",
                path=path,
                subject=key,
            ) from error
    return {"id": key, "module": module} | entry


def validate_checks(worktree: Path) -> list[dict]:
    """Judge every checks file of ``worktree`` and every declared input before any check runs;
    the configured checks, or ``invalid_check`` and ``check_input_missing`` naming the file,
    the entry and the path."""
    checks = configured_checks(worktree)
    for check in checks:
        _inputs(Path(worktree), check)
    return checks


def check_revision(
    worktree: Path, checks: list[dict], module: str, files: Iterable[str] = ()
) -> str:
    """The digest a stored check result of ``module`` is current against: the ``files`` its
    caller names for the Module, each of the Module's checks with its inputs, and the policy."""
    root = Path(worktree)
    implementation = [(path, _file_digest(root / path)) for path in sorted(set(files))]
    own = [check for check in checks if check["module"] == module]
    value = {
        "implementation": implementation,
        "checks": [
            {"definition": check, "inputs": _inputs(root, check)} for check in own
        ],
        "policy": CHECK_POLICY,
    }
    return (
        "sha256:"
        + hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
    )


def project_python(worktree: Path, configured: str | None, check_id: str) -> str:
    """The project's interpreter the caller names: an absolute path as it is, a relative one in
    the worktree the check runs in or, when that has none (a task worktree rarely has an
    environment of its own), in the primary worktree."""
    if not isinstance(configured, str) or not configured.strip():
        raise CheckError(
            f"check {check_id} uses {{python}}, but no project interpreter is named (in "
            "Concorde, `python` in .concorde/config.json)",
            "project_python_missing",
            subject=check_id,
        )
    if os.path.isabs(configured):
        candidates = [Path(configured)]
    else:
        candidates = [worktree / configured]
        primary = primary_worktree(worktree)
        if primary is not None and primary != worktree.resolve():
            candidates.append(primary / configured)
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.as_posix()
    raise CheckError(
        f"check {check_id} uses {{python}}, the project interpreter {configured!r}, which is "
        "not an executable file at "
        + " or at ".join(candidate.as_posix() for candidate in candidates),
        "project_python_missing",
        subject=check_id,
    )


# A check whose argv holds {tests} is selective: it runs the tests its caller names for the
# Modules being checked, those that declare they verify one of their scenarios.
TESTS = "{tests}"
# When a check runs: in every round that runs checks, or only when readiness is decided
# (validate and delivery), for a full suite too slow to run every round.
WHEN = ("always", "readiness")


def measured_digest(
    worktree: Path,
    check: dict,
    modules,
    *,
    checks: list[dict] | None = None,
    measured: Mapping[str, Iterable[str]] | None = None,
    tests: Iterable[str] = (),
) -> str:
    """The digest a result of ``check`` run for the selected ``modules`` is current against.

    For an ordinary check it is its Module's ``check_revision`` over the files ``measured``
    names for that Module. A selective check also measures the selected Modules, the ``tests``
    it selected and the digest of every file holding one of them, since another selection runs
    other tests."""
    root = Path(worktree)
    checks = configured_checks(root) if checks is None else checks
    revision = check_revision(
        root, checks, check["module"], (measured or {}).get(check["module"], ())
    )
    if TESTS not in (check.get("argv") or []):
        return revision
    tests = list(tests)
    files = sorted({test.split("::", 1)[0] for test in tests})
    value = {
        "check_revision": revision,
        "modules": sorted(set(modules)),
        "tests": tests,
        "test_files": [(path, _file_digest(root / path)) for path in files],
    }
    return (
        "sha256:"
        + hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
    )


def _argv(check: dict, python, tests=()) -> list[str]:
    """The check's command; ``python`` gives the project interpreter for ``{python}`` and
    ``tests`` the test identities ``{tests}`` stands for."""
    argv = check.get("argv")
    if (
        not isinstance(argv, list)
        or not argv
        or any(not isinstance(item, str) or not item for item in argv)
    ):
        raise CheckError(
            f"check {check['id']} needs a nonempty argv",
            "invalid_check",
            subject=check["id"],
        )
    result: list[str] = []
    for item in argv:
        if item == "{python}":
            result.append(python())
        elif item == TESTS:
            result.extend(tests)
        else:
            result.append(item)
    return result


def _timeout(check: dict) -> float:
    value = check.get("timeout_seconds")
    if type(value) not in (int, float) or value <= 0:
        raise CheckError(
            f"check {check['id']} needs a positive timeout_seconds",
            "invalid_check",
            subject=check["id"],
        )
    return float(value)


ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
# Transport configuration can be required by an enclosing sandbox. Keep this list exact:
# runtime injection variables (e.g. PYTHONPATH, NODE_OPTIONS) do not belong to a check.
TRANSPORT_ENV = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "no_proxy",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "REQUESTS_CA_BUNDLE",
    "CURL_CA_BUNDLE",
    "NODE_EXTRA_CA_CERTS",
)


def environment(check: dict | None = None) -> dict[str, str]:
    """Host PATH, LANG and explicit transport settings, overridden by the check's own env.

    Runtime settings stay excluded; execute_check supplies its own scratch/cache settings.
    """
    base = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        **{key: os.environ[key] for key in TRANSPORT_ENV if key in os.environ},
    }
    own = (check or {}).get("env", {})
    if not isinstance(own, dict) or any(
        not isinstance(key, str)
        or not ENV_NAME.match(key)
        or not isinstance(value, str)
        for key, value in own.items()
    ):
        raise CheckError(
            f"check {check['id']} has an env that is not an object of variable names to "
            "strings",
            "invalid_check",
            subject=check["id"],
        )
    return {**base, **own}


def run_checks(
    worktree: Path,
    *,
    modules,
    trace_directory: Path,
    measured: Mapping[str, Iterable[str]] | None = None,
    tests: Iterable[str] | None = None,
    python: str | None = None,
    stage: str = "work",
    kinds: str = "all",
) -> list[dict]:
    """Run the configured checks of ``modules``; one result per check, in configuration order.

    ``modules`` are labels that select checks files. ``measured`` names, for each Module, the
    files its results depend on besides its checks' inputs; ``tests`` the tests a selective check
    runs, which is skipped when there are none; ``python`` the project's interpreter ``{python}``
    stands for. ``stage`` is ``readiness`` when readiness is decided, which also runs the checks
    marked ``"when": "readiness"``. ``kinds`` narrows the call to the checks of the Modules
    (``module``) or to the selective checks (``selective``), which run once for the whole
    selection."""
    worktree = Path(worktree)
    checks = configured_checks(worktree)
    selected = list(dict.fromkeys(modules))
    tests = list(tests or ())
    trace_directory = Path(trace_directory)
    trace_directory.mkdir(parents=True, exist_ok=True)
    results = []
    for check in checks:
        when = check.get("when", "always")
        if when not in WHEN:
            raise CheckError(
                f"check {check['id']} has when {when!r}; expected one of "
                + ", ".join(WHEN),
                "invalid_check",
                subject=check["id"],
            )
        if when == "readiness" and stage != "readiness":
            continue
        selective = TESTS in (check.get("argv") or [])
        if selective:
            if kinds == "module" or not tests:
                continue
        elif kinds == "selective" or check["module"] not in selected:
            continue
        argv = _argv(
            check,
            lambda check=check: project_python(worktree, python, check["id"]),
            tests,
        )
        timeout = _timeout(check)

        def measure(check=check, checks=checks):
            return measured_digest(
                worktree, check, selected, checks=checks, measured=measured, tests=tests
            )

        before = measure()
        folder = layout.check_folder(trace_directory, check["id"])
        log = folder / "output.log"
        chosen = list(tests) if selective else []
        node = Node(
            folder,
            check["id"],
            "check",
            content_type=CHECK_TRACE,
            metadata={"check": check["id"], "module": check["module"]},
            content=_check_content("passed", None, before, argv, chosen),
        )
        node.keep("output", "output.log")
        node.start()
        try:
            outcome = execute_check(
                worktree, argv, timeout=timeout, environment=environment(check)
            )
        except CheckSandboxError as error:
            log.write_bytes(
                (error.stdout or b"")
                + b"\n"
                + (error.stderr or b"")
                + str(error).encode()
            )
            refusal = CheckError(
                f"check {check['id']} could not run in the read-only boundary: {error}",
                "check_sandbox_unavailable",
            )
            node.finish(
                "failed",
                outcome="refused",
                error=service_error(refusal),
                content=_check_content("refused", None, before, argv, chosen),
            )
            raise refusal from error
        header = (
            ("selected tests: " + " ".join(tests) + "\n\n").encode()
            if selective
            else b""
        )
        log.write_bytes(header + outcome.stdout + b"\n" + outcome.stderr)
        status = (
            "timeout"
            if outcome.timed_out
            else ("passed" if outcome.returncode == 0 else "failed")
        )
        exit_code = -1 if outcome.timed_out else outcome.returncode
        # The checks files are read again: a definition changed during the run is stale too.
        if measure(checks=None) != before:
            stale = CheckError(
                f"the input of check {check['id']} changed while it ran",
                "stale_evidence",
            )
            node.finish(
                "failed",
                outcome="stale_evidence",
                error=service_error(stale),
                content=_check_content(status, exit_code, before, argv, chosen),
            )
            raise stale
        result = {
            "check_id": check["id"],
            "module": check["module"],
            "status": status,
            "exit_code": exit_code,
            "source_digest": before,
            "log": log.as_posix(),
            "log_digest": "sha256:" + _file_digest(log),
        }
        node.finish(
            "ok" if status == "passed" else "failed",
            outcome=status,
            content=_check_content(status, exit_code, before, argv, chosen),
        )
        results.append(result)
    return results


def _check_content(status, exit_code, digest, argv, tests) -> dict:
    return {
        "status": status,
        "exit_code": exit_code,
        "source_digest": digest,
        "argv": [str(item) for item in argv],
        "selected_tests": list(tests),
    }


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


# Why a caller's Check execution link was not handled here, by the error's code; every other
# code is a configuration or request only its sender can correct.
SERVICE_REASONS = {
    "check_sandbox_unavailable": "environment",
    "stale_evidence": "environment",
    "system_error": "environment",
}


def service_error(error: BaseException) -> dict:
    """Check execution's own error link for an error ``run_checks`` raised, which the caller
    keeps as a cause under its own link."""
    if isinstance(error, OSError):
        return link(
            "component",
            "Check execution",
            "system_error",
            f"{type(error).__name__}: {error}",
            reason="environment",
            explanation="the operating system refused an operation Check execution needed",
        )
    if not isinstance(error, CheckError):
        return link(
            "component",
            "Check execution",
            "unexpected_error",
            f"{type(error).__name__}: {error}",
            reason="capability",
            explanation="Check execution raised an error it did not expect",
        )
    where = error.where()
    return link(
        "component",
        "Check execution",
        error.code,
        str(error) + (f" (at {where})" if where else ""),
        reason=SERVICE_REASONS.get(error.code, "input"),
        explanation=error.reason,
        evidence=[evidence("location", where, "")] if where else [],
        options=[error.remediation],
        recommendation=error.remediation,
        causes=[service_error(cause) for cause in error.causes],
    )


__all__ = [
    "CHECKS_DIR",
    "CheckError",
    "check_error",
    "check_revision",
    "checks_files",
    "configured_checks",
    "measured_digest",
    "project_python",
    "run_checks",
    "service_error",
    "validate_checks",
]
