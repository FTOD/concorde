"""Per-invocation token accounting for every native Agent launch.

Every Agent process the host launches reports what it consumed (see ``ExecutionUsage``). This
module records that figure once per launch, labelled with the capability, stage, target, Agent
and mode that spent it, so a whole Flow run can be read back per step. Records are diagnostics:
they live beside the run's other host records under ``.concorde/runs/<root invocation>/`` and
change no receipt, evidence or contract. Recording never turns a completed launch into a failure.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

USAGE_FILE = "usage.jsonl"
RUNS_PATH = ".concorde/runs"

_TOKEN_FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens", "total_tokens")
_SUM_FIELDS = (*_TOKEN_FIELDS, "cost_usd", "turns", "duration_ms", "wall_seconds",
               "prompt_bytes", "context_bytes")


def usage_path(root_invocation_id: str) -> str:
    return f"{RUNS_PATH}/{root_invocation_id}/{USAGE_FILE}"


def usage_record(host, *, capability: str, stage: str, target_id: str | None, agent: str,
                 mode: str | None, launch, result, change_id: str | None = None,
                 iteration: int | None = None) -> dict[str, Any]:
    """The labelled usage line for one launch; ``usage`` is null when the client reported none."""
    usage = getattr(result, "usage", None)
    return {
        "time": datetime.now(timezone.utc).isoformat(),
        "root_invocation_id": host.root_invocation_id or host.invocation_id,
        "invocation_id": host.invocation_id,
        "depth": host.depth,
        "capability": capability,
        "stage": stage,
        "target_id": target_id,
        "agent": agent,
        "mode": mode,
        "change_id": change_id,
        "iteration": iteration,
        "launch_invocation_id": getattr(launch, "invocation_id", None),
        "context_id": getattr(launch, "workspace_digest", None),
        "integration": getattr(launch, "integration", None),
        "usage": usage.wire() if usage is not None else None,
    }


def record_usage(host, **labels) -> dict[str, Any] | None:
    """Append one usage line to the run's file and announce it to the host observer.

    Observability must never fail a completed mutation, so persistence errors are swallowed;
    the observer still receives the record.
    """
    try:
        record = usage_record(host, **labels)
    except Exception:
        return None
    try:
        from ..spec.typed_data import checked_path
        destination = checked_path(host.project_root, usage_path(record["root_invocation_id"]))
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    except Exception:
        pass
    host.observe("agent_usage", **record)
    return record


def read_usage(project_root: str | Path, root_invocation_id: str | None = None) -> list[dict[str, Any]]:
    """Every recorded line, for one run or for all runs under the project."""
    root = Path(project_root)
    files = ([root / usage_path(root_invocation_id)] if root_invocation_id
             else sorted((root / RUNS_PATH).glob(f"*/{USAGE_FILE}")) if (root / RUNS_PATH).is_dir() else [])
    records: list[dict[str, Any]] = []
    for path in files:
        if not path.is_file() or path.is_symlink():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def _add(total: dict[str, Any], usage: dict[str, Any] | None) -> None:
    total["launches"] = total.get("launches", 0) + 1
    if usage is None:
        total["unreported"] = total.get("unreported", 0) + 1
        return
    for key in _SUM_FIELDS:
        value = usage.get(key)
        if value is not None:
            total[key] = round(total.get(key, 0) + value, 6)


def summarize_usage(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Totals plus per-step breakdowns, so the cost of each stage and target is visible.

    ``by_step`` groups by capability, stage and target: the granularity a Flow node has.
    ``by_stage``, ``by_target``, ``by_agent`` and ``by_run`` are coarser views of the same lines.
    """
    summary: dict[str, Any] = {"total": {}, "by_step": {}, "by_stage": {}, "by_target": {},
                               "by_agent": {}, "by_run": {}}
    for record in records:
        usage = record.get("usage")
        _add(summary["total"], usage)
        step = f"{record.get('capability')}/{record.get('stage')}/{record.get('target_id')}"
        for view, key in (("by_step", step), ("by_stage", record.get("stage")),
                          ("by_target", record.get("target_id")), ("by_agent", record.get("agent")),
                          ("by_run", record.get("root_invocation_id"))):
            _add(summary[view].setdefault(str(key), {}), usage)
    return summary
