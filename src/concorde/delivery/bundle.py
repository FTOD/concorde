"""The evidence bundle committed with a delivery, the delivery commit message, and reading the
earlier delivery commits back from Git.

The bundle records the workspace, the readiness the delivery consumed and every run of the
workspace since the previous delivery, by identity and digest; the results, run records and
transcripts themselves stay in the run store of the workspace's records directory.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

SHA256 = {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
COMMIT = {"type": "string", "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"}
TEXT = {"type": "string", "minLength": 1}
TEXTS = {"type": "array", "items": TEXT}

BUNDLE_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "workspace",
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
        "workspace": TEXT,
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
                    "kind",
                    "name",
                    "modules",
                    "status",
                    "summary",
                    "worker_runs",
                    "result_digest",
                ],
                "properties": {
                    "run_id": TEXT,
                    "kind": {"enum": ["operation", "command"]},
                    "name": TEXT,
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

SUBJECT = "concorde: deliver {workspace}"
TRAILERS = ("Concorde-Workspace", "Concorde-Evidence", "Concorde-Readiness")


def bundle_path(workspace: str, sequence: int) -> str:
    return f".concorde/evidence/{workspace}/{sequence}.json"


def sequence_of(bundle: str) -> int | None:
    name = Path(bundle).name
    return int(name[:-5]) if name.endswith(".json") and name[:-5].isdigit() else None


def commit_message(workspace: dict, bundle: str, readiness_run: str) -> str:
    return (
        f"{SUBJECT.format(workspace=workspace['workspace'])}\n\n{workspace['goal'].strip()}\n\n"
        f"Concorde-Workspace: {workspace['workspace']}\n"
        f"Concorde-Evidence: {bundle}\n"
        f"Concorde-Readiness: {readiness_run}\n"
    )


def delivery_commits(
    worktree: Path, base: str | None, head: str, workspace: str | None
) -> list[dict]:
    """The delivery commits of ``workspace`` between ``base`` and ``head``, oldest first.

    A delivery commit has the delivery subject and names the workspace, its evidence bundle and
    the run that decided its readiness in its trailers; it is the only record of a delivery.
    """
    if not workspace:
        return []
    separator = "\x1f"
    fields = separator.join(
        [
            "%H",
            "%s",
            *(f"%(trailers:key={key},valueonly,separator=%x20)" for key in TRAILERS),
        ]
    )
    span = f"{base}..{head}" if base else head
    result = subprocess.run(
        ["git", "log", "--first-parent", "--reverse", f"--format={fields}%x1e", span],
        cwd=worktree,
        capture_output=True,
        text=True,
        check=False,
    )
    found = []
    for entry in result.stdout.split("\x1e"):
        parts = entry.strip("\n").split(separator)
        if len(parts) != 2 + len(TRAILERS):
            continue
        commit, subject, named, bundle, readiness = (part.strip() for part in parts)
        if subject != SUBJECT.format(workspace=workspace) or named != workspace:
            continue
        if not bundle or not readiness or sequence_of(bundle) is None:
            continue
        found.append({"commit": commit, "bundle": bundle, "readiness_run": readiness})
    return found


def _run_entry(records: Path, run: dict) -> dict:
    path = records / "runs" / run["run_id"] / "result.json"
    entry = {
        "run_id": run["run_id"],
        "kind": run.get("kind") or "operation",
        "name": run.get("name") or "unknown",
        "modules": list(run.get("modules") or []),
    }
    try:
        data = path.read_bytes()
        result = json.loads(data)
    except (OSError, ValueError):
        return {
            **entry,
            "status": "interrupted",
            "summary": "",
            "worker_runs": [],
            "result_digest": None,
        }
    return {
        **entry,
        "status": result.get("status", "interrupted"),
        "summary": result.get("summary", ""),
        "worker_runs": list(result.get("worker_runs") or []),
        "result_digest": "sha256:" + hashlib.sha256(data).hexdigest(),
    }


def runs_since(runs: list[dict], since: str | None, current_run: str) -> list[dict]:
    """The runs after ``since`` (the previous delivery's run) and before ``current_run``."""
    start = 0
    if since:
        for index, run in enumerate(runs):
            if run["run_id"] == since:
                start = index + 1
    selected = []
    for run in runs[start:]:
        if run["run_id"] == current_run:
            break
        selected.append(run)
    return selected


def build_bundle(
    workspace: dict,
    records: Path,
    runs: list[dict],
    *,
    since: str | None,
    run_id: str,
    sequence: int,
    parent: str,
    readiness_run: str,
    readiness: dict,
    confirmations: list[dict],
) -> dict:
    return {
        "workspace": workspace["workspace"],
        "goal": workspace["goal"],
        "modules": list(workspace["modules"]),
        "sequence": sequence,
        "base_commit": workspace["base_commit"],
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
        "runs": [_run_entry(records, run) for run in runs_since(runs, since, run_id)],
        "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


__all__ = [
    "BUNDLE_SCHEMA",
    "OUTPUT_SCHEMA",
    "SUBJECT",
    "TRAILERS",
    "build_bundle",
    "bundle_path",
    "commit_message",
    "delivery_commits",
    "runs_since",
    "sequence_of",
]
