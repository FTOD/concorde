"""The evidence bundle committed with a delivery, and the delivery commit message.

The bundle records the task, the readiness the delivery consumed and every Operation run of the
task since the previous delivery, by identity and digest; the results, run records and
transcripts themselves stay in the primary worktree's ``.concorde/runs/``.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

SHA256 = {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
COMMIT = {"type": "string", "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"}
TEXT = {"type": "string", "minLength": 1}
TEXTS = {"type": "array", "items": TEXT}

BUNDLE_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "task",
        "goal",
        "modules",
        "sequence",
        "base_commit",
        "parent_commit",
        "readiness",
        "confirmations",
        "runs",
        "created_at",
    ],
    "properties": {
        "task": TEXT,
        "goal": TEXT,
        "modules": TEXTS,
        "sequence": {"type": "integer", "minimum": 1},
        "base_commit": COMMIT,
        "parent_commit": COMMIT,
        "readiness": {
            "type": "object",
            "additionalProperties": False,
            "required": ["run_id", "input_digest", "modules", "checks", "warnings"],
            "properties": {
                "run_id": TEXT,
                "input_digest": SHA256,
                "modules": TEXTS,
                "checks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["check", "module", "status", "measured_digest"],
                        "properties": {
                            "check": TEXT,
                            "module": TEXT,
                            "status": {"const": "passed"},
                            "measured_digest": SHA256,
                        },
                    },
                },
                "warnings": {"type": "integer", "minimum": 0},
            },
        },
        "confirmations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["module", "realization", "entry"],
                "properties": {
                    "module": TEXT,
                    "realization": TEXT,
                    "entry": TEXT,
                },
            },
        },
        "runs": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "run_id",
                    "operation",
                    "modules",
                    "status",
                    "summary",
                    "worker_runs",
                    "result_digest",
                ],
                "properties": {
                    "run_id": TEXT,
                    "operation": TEXT,
                    "modules": TEXTS,
                    "status": {"enum": ["ok", "blocked", "failed", "interrupted"]},
                    "summary": {"type": "string"},
                    "worker_runs": TEXTS,
                    "result_digest": {"anyOf": [{"type": "null"}, SHA256]},
                },
            },
        },
        "created_at": TEXT,
    },
}

OUTPUT_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["commit", "branch", "bundle", "sequence", "confirmed", "recovered"],
    "properties": {
        "commit": COMMIT,
        "branch": TEXT,
        "bundle": TEXT,
        "sequence": {"type": "integer", "minimum": 1},
        "confirmed": TEXTS,
        "recovered": {"type": "boolean"},
    },
}

SUBJECT = "concorde: deliver {task}"
TRAILERS = ("Concorde-Task", "Concorde-Evidence", "Concorde-Readiness")


def bundle_path(task_id: str, sequence: int) -> str:
    return f".concorde/evidence/{task_id}/{sequence}.json"


def sequence_of(bundle: str) -> int | None:
    name = Path(bundle).name
    return int(name[:-5]) if name.endswith(".json") and name[:-5].isdigit() else None


def commit_message(task: dict, bundle: str, readiness_run: str) -> str:
    return (
        f"{SUBJECT.format(task=task['id'])}\n\n{task['goal'].strip()}\n\n"
        f"Concorde-Task: {task['id']}\n"
        f"Concorde-Evidence: {bundle}\n"
        f"Concorde-Readiness: {readiness_run}\n"
    )


def _run_entry(primary: Path, run: dict) -> dict:
    path = primary / ".concorde/runs" / run["run_id"] / "result.json"
    try:
        data = path.read_bytes()
        result = json.loads(data)
    except (OSError, ValueError):
        return {
            "run_id": run["run_id"],
            "operation": run["operation"],
            "modules": list(run["modules"]),
            "status": "interrupted",
            "summary": "",
            "worker_runs": [],
            "result_digest": None,
        }
    return {
        "run_id": run["run_id"],
        "operation": run["operation"],
        "modules": list(run["modules"]),
        "status": result.get("status", "interrupted"),
        "summary": result.get("summary", ""),
        "worker_runs": list(result.get("worker_runs") or []),
        "result_digest": "sha256:" + hashlib.sha256(data).hexdigest(),
    }


def runs_since_last_delivery(task: dict, current_run: str) -> list[dict]:
    """The task's runs after its previous delivery run and before ``current_run``."""
    runs = task["runs"]
    start = 0
    if task["deliveries"]:
        previous = task["deliveries"][-1]["run_id"]
        for index, run in enumerate(runs):
            if run["run_id"] == previous:
                start = index + 1
    selected = []
    for run in runs[start:]:
        if run["run_id"] == current_run:
            break
        selected.append(run)
    return selected


def build_bundle(
    primary: Path,
    task: dict,
    *,
    run_id: str,
    sequence: int,
    parent: str,
    readiness_run: str,
    readiness: dict,
    confirmations: list[dict],
) -> dict:
    return {
        "task": task["id"],
        "goal": task["goal"],
        "modules": list(task["modules"]),
        "sequence": sequence,
        "base_commit": task["base_commit"],
        "parent_commit": parent,
        "readiness": {
            "run_id": readiness_run,
            "input_digest": readiness["inputs"]["digest"],
            "modules": list(readiness["modules"]),
            "checks": [
                {
                    "check": item["check"],
                    "module": item["module"],
                    "status": item["status"],
                    "measured_digest": item["measured_digest"],
                }
                for item in readiness["checks"]
            ],
            "warnings": len(readiness["warnings"]),
        },
        "confirmations": [
            {
                "module": item["module"],
                "realization": item["realization"],
                "entry": item["entry"],
            }
            for item in confirmations
        ],
        "runs": [
            _run_entry(primary, run) for run in runs_since_last_delivery(task, run_id)
        ],
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


__all__ = [
    "BUNDLE_SCHEMA",
    "OUTPUT_SCHEMA",
    "SUBJECT",
    "TRAILERS",
    "build_bundle",
    "bundle_path",
    "commit_message",
    "runs_since_last_delivery",
    "sequence_of",
]
