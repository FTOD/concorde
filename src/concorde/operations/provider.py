"""What an Operation provider declares, and the context and outcomes its steps work with.

A provider is a fixed list of steps. Each step receives the run's ``RunContext`` and returns
``Continue`` (with any output and host evidence it produced) or ``Stop`` (with a status, a summary,
host evidence and, unless the status is ``ok``, an escalation). ``RunContext.run_worker`` is the
standard worker sequence: it computes the grant from the task worktree's Specs, runs one worker
through Workers and maps its outcome to a step outcome.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


@dataclass
class Continue:
    output: dict | None = None
    evidence: list[dict] = field(default_factory=list)


@dataclass
class Stop:
    status: str
    summary: str
    evidence: list[dict] = field(default_factory=list)
    escalation: dict | None = None


@dataclass(frozen=True)
class Provider:
    name: str
    task_type: str | None
    writes: bool
    steps: tuple[Callable, ...]
    output_schema: dict | None = None
    add_arguments: Callable[[argparse.ArgumentParser], None] | None = None
    # False for a provider that diagnoses the task worktree's Specs itself, such as validate:
    # the host then begins the run even when those Specs cannot be loaded.
    requires_loaded_specs: bool = True


PACKAGE_ROOT = Path(__file__).resolve().parents[3]


def load_prompt(name: str) -> str:
    """The rendered worker prompt ``generated/workers/<name>.md`` of this package."""
    path = PACKAGE_ROOT / "generated/workers" / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} is missing; run the build (python3 scripts/concorde.py build)"
        )
    return path.read_text(encoding="utf-8")


def evidence(kind: str, ref: str = "", detail: str = "") -> dict:
    return {"kind": kind, "ref": ref, "detail": detail}


def host_escalation(
    problem: str, *, options=(), recommendation: str = "", impact: str = ""
) -> dict:
    return {
        "source": "host",
        "problem": problem,
        "attempts": [],
        "options": list(options),
        "recommendation": recommendation,
        "blocking": True,
        "impact": impact,
    }


@dataclass
class RunContext:
    operation: str
    primary: Path
    task: dict
    worktree: Path
    modules: list[str]
    run_id: str
    run_dir: Path
    arguments: argparse.Namespace
    inputs: dict[str, dict] = field(default_factory=dict)
    output: dict | None = None
    worker: dict | None = None
    worker_runs: list[str] = field(default_factory=list)
    evidence: list[dict] = field(default_factory=list)
    # Provider-owned values shared between the steps of one run.
    state: dict = field(default_factory=dict)
    # The run record of the latest worker launch, as Workers wrote it.
    last_record: dict | None = None

    def workers_config(self) -> dict:
        config = json.loads((self.worktree / ".concorde/config.json").read_text())
        return config.get("workers") or {}

    def run_worker(
        self,
        instructions: str,
        *,
        task_type: str,
        output_schema: dict | None = None,
        checks: bool = False,
        rounds: int | None = None,
        modules: list[str] | None = None,
    ):
        """The standard worker sequence; returns ``Continue`` or ``Stop``."""
        from ..harness.workers import WorkerRequest, run_worker
        from ..spec.grants import grant
        from ..spec.repository import SpecRepository
        from ..spec.repository_base import SpecError

        bound = modules or self.modules
        try:
            frozen = grant(SpecRepository(self.worktree), bound, task_type).value
        except (SpecError, OSError, ValueError) as error:
            code = getattr(error, "code", "grant_unavailable")
            return Stop(
                "failed",
                f"The {task_type} grant for {', '.join(bound)} could not be computed ({code}).",
                [evidence("grant", ", ".join(bound), str(error))],
                host_escalation(
                    f"no {task_type} grant for {', '.join(bound)}: {error}",
                    options=[
                        "bind every Module that binds the shared file",
                        "repair the Specs",
                    ],
                ),
            )
        config = self.workers_config()
        runtime = tuple(
            Path(path) if os.path.isabs(path) else self.worktree / path
            for path in config.get("runtime", [".venv", "node_modules"])
            if (Path(path) if os.path.isabs(path) else self.worktree / path).exists()
        )
        record = run_worker(
            WorkerRequest(
                worktree=self.worktree,
                task_type=task_type,
                grant=frozen,
                instructions=instructions,
                check_modules=bound if checks else None,
                runtime=runtime,
                output_schema=output_schema,
                rounds=rounds if rounds is not None else int(config.get("rounds", 3)),
                timeout=float(config.get("timeout_seconds", 1800)),
                max_turns=int(config.get("max_turns", 200)),
                max_budget_usd=config.get("max_budget_usd"),
                model=config.get("model"),
            )
        )
        return self.absorb(record)

    def absorb(self, record: dict):
        """Map one worker run record to a step outcome, adding host evidence."""
        self.worker_runs.append(record["run_id"])
        self.last_record = record
        self.worker = record.get("worker_result")
        found = [
            evidence(
                "grant",
                record.get("grant_digest") or "",
                f"{record['task_type']} grant",
            ),
            evidence("context-identity", record.get("context_identity") or "", ""),
        ]
        rounds = record.get("rounds") or []
        for item in rounds:
            audit = item.get("audit")
            if audit:
                found.append(
                    evidence(
                        "audit",
                        str(item["round"]),
                        f"{len(audit['changed'])} changed, violations: {', '.join(audit['violations']) or 'none'}",
                    )
                )
            for check in item.get("checks") or []:
                found.append(
                    evidence(
                        "check",
                        check["check_id"],
                        f"{check['status']}, exit {check['exit_code']}; log {check['log']}",
                    )
                )
        found.append(evidence("rounds", "", f"{len(rounds)} round(s)"))
        if record.get("transcript"):
            found.append(evidence("transcript", record["transcript"], ""))
        if record.get("stderr_tail"):
            found.append(
                evidence("stderr", record["run_id"], record["stderr_tail"][-2000:])
            )
        errors = record.get("errors") or []
        status = record["status"]
        if status == "ok":
            return Continue(output=(self.worker or {}).get("output"), evidence=found)
        if errors:
            error = errors[0]
            return Stop(
                "failed",
                f"The worker run {record['run_id']} failed: {error['code']}.",
                found
                + [evidence(error["code"], record["run_id"], error.get("detail", ""))],
                host_escalation(
                    f"{error['code']}: {error.get('detail', '')}",
                    options=[
                        "inspect the run record",
                        "run the Operation again with a narrower goal",
                    ],
                ),
            )
        worker = self.worker or {}
        return Stop(
            status,
            f"The worker ended {status}; the audit was clean.",
            found,
            {
                "source": "worker",
                "problem": worker.get("problem") or worker.get("summary", ""),
                "attempts": worker.get("attempts", []),
                "options": worker.get("options", []),
                "recommendation": worker.get("recommendation", ""),
                "blocking": bool(worker.get("blocking", True)),
                "impact": worker.get("impact", ""),
            },
        )


__all__ = [
    "Continue",
    "Provider",
    "RunContext",
    "Stop",
    "evidence",
    "host_escalation",
    "load_prompt",
]
