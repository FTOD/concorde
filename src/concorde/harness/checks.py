"""Host execution of a Module's configured checks inside their read-only sandbox."""

from __future__ import annotations

import os
import sys

from ..spec.repository import (
    SpecError,
    SpecRepository,
    check_input_error,
    check_input_members,
    digest,
    read_file,
)
from ..spec.typed_data import TypedDataError, checked_path
from .check_executor import CHECK_POLICY, CheckSandboxError, execute_check
from .revisions import implementation_digest
from .status_store import run_path, write_run


def check_service(repository: SpecRepository, target, invocation_id: str):
    """The host's run_checks answer: every configured check's status and the tail of its log."""

    def run_checks() -> dict:
        current = SpecRepository(repository.root, repository.package_root)
        results = configured_checks(current, current.module(target.id), invocation_id)
        for item in results:
            log = run_path(
                current.root, f".concorde/runs/{invocation_id}/{item['check_id']}.log"
            )
            item["output_tail"] = (
                log.read_bytes()[-20000:].decode("utf-8", "replace")
                if log.is_file()
                else ""
            )
        return {"checks": results}

    return run_checks


def check_revision(repository: SpecRepository, target) -> str:
    inputs = []
    for check_id in target.checks:
        check = repository.checks[check_id]
        inputs.append((check_id, check))
        for relative in check.get("inputs", []):
            try:
                members = check_input_members(repository.root, relative)
                inputs.extend(
                    (member, digest(read_file(repository.root, member)))
                    for member in members
                )
            except (SpecError, TypedDataError, OSError) as error:
                raise check_input_error(check, relative, error) from error
    return digest(
        {
            "implementation": implementation_digest(repository, target),
            "check_inputs": inputs,
            "execution_policy": CHECK_POLICY,
        }
    )


def configured_checks(
    repository: SpecRepository, target, invocation_id: str
) -> list[dict]:
    """Only the host executes configured argv. Never send stdout/stderr to a Spec-only agent."""
    before = check_revision(repository, target)
    results = []
    for check_id in target.checks:
        configured = repository.checks[check_id]
        argv = list(configured["argv"])
        if argv[0] == "{python}":
            argv[0] = sys.executable
        failure = None
        status, code = "failed", -1
        try:
            result = execute_check(
                repository.root,
                argv,
                timeout=configured["timeout_seconds"],
                environment={
                    **os.environ,
                    "PYTHONPATH": str(repository.package_root / "src"),
                },
            )
            log = result.stdout + b"\n" + result.stderr
            status = (
                "timeout"
                if result.timed_out
                else ("passed" if result.returncode == 0 else "failed")
            )
            code = result.returncode
        except CheckSandboxError as error:
            log = error.stdout + b"\n" + error.stderr + b"\n" + str(error).encode()
            failure = error
        path = f".concorde/runs/{invocation_id}/{check_id}.log"
        # Logs are host/implementation evidence, absent from non-implementation context manifests.
        write_run(repository.root, path, log)
        if failure is not None:
            raise SpecError(
                f"configured check {check_id} requires an enforceable read-only sandbox; "
                f"see host log {path}",
                "check_sandbox_unavailable",
            ) from failure
        results.append(
            {
                "check_id": check_id,
                "target_id": target.id,
                "status": status,
                "exit_code": code,
                "source_digest": before,
                "log_digest": digest(log),
            }
        )
    if check_revision(repository, target) != before:
        raise SpecError(
            "configured validation changed the implementation it measured",
            "stale_evidence",
        )
    return results
