#!/usr/bin/env python3
"""Deterministic queue and plan-state helper for reflection-triage/v1."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

EXTENSION_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(EXTENSION_ROOT / "runtime"))

from concorde.frontmatter import FrontMatterError, parse_document  # noqa: E402
from concorde.reflections import ReflectionEntry, parse_reflection_log, strip_reference_suffix  # noqa: E402


ROUTES = frozenset({"fast-loop", "specify", "dismiss", "blocked"})
PLAN_STATUSES = frozenset(
    {"proposed", "approved", "hold", "rejected", "implemented", "ineligible", "failed", "merged"}
)
TRANSITIONS = {
    "proposed": frozenset({"approved", "hold", "rejected", "implemented", "ineligible", "failed"}),
    "approved": frozenset({"hold", "rejected", "implemented", "ineligible", "failed"}),
    "hold": frozenset({"approved", "rejected"}),
    "implemented": frozenset({"merged"}),
    "rejected": frozenset(),
    "ineligible": frozenset(),
    "failed": frozenset(),
    "merged": frozenset(),
}
SETTABLE_KEYS = frozenset({"status", "branch", "worktree", "commit"})
REQUIRED_PLAN_FIELDS = (
    "id",
    "title",
    "route",
    "status",
    "recorded_under",
    "implement_in",
    "implement_in_id",
    "touches_docsite",
    "effort",
    "files",
)


class QueueError(ValueError):
    pass


def _safe_relative(value: str, field: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or "\\" in value:
        raise QueueError(f"{field} must be a safe project-relative path: {value!r}")
    return path.as_posix()


def find_root(explicit: str | None) -> Path:
    if explicit:
        root = Path(explicit).resolve()
        if not (root / ".concorde/config.json").is_file():
            raise QueueError(f"not a Concorde project: {root}")
        return root
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / ".concorde/config.json").is_file():
            return candidate
    raise QueueError("cannot find .concorde/config.json; pass --root")


def load_config(root: Path) -> dict[str, Any]:
    path = root / ".concorde/reflections/config.json"
    legacy = root / ".claude/reflections.config.json"
    if not path.is_file():
        if legacy.is_file():
            raise QueueError(
                "legacy .claude/reflections.config.json exists; preview/adopt it through Concorde agent-asset sync"
            )
        raise QueueError("missing .concorde/reflections/config.json; run Concorde agent-asset sync")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise QueueError(f"invalid reflection-triage config: {error}") from error
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise QueueError("reflection-triage config must use schema_version 1")
    if value.get("order") not in {"newest-first", "oldest-first"}:
        raise QueueError("config order must be newest-first or oldest-first")
    for key in ("investigators", "implementers"):
        if not isinstance(value.get(key), int) or value[key] < 1:
            raise QueueError(f"config {key} must be a positive integer")
    if not isinstance(value.get("require_approval"), bool):
        raise QueueError("config require_approval must be boolean")
    skip = value.get("skip")
    if not isinstance(skip, list) or any(not isinstance(item, str) for item in skip) or len(skip) != len(set(skip)):
        raise QueueError("config skip must be a unique string list")
    for key in ("plans_dir", "worktrees_dir"):
        value[key] = _safe_relative(str(value.get(key, "")), key)
    return value


def _specification_root(root: Path) -> tuple[str, Path]:
    try:
        config = json.loads((root / ".concorde/config.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise QueueError(f"invalid .concorde/config.json: {error}") from error
    relative = _safe_relative(str(config.get("specification_root", "")), "specification_root")
    path = root / relative
    if not path.is_dir():
        raise QueueError(f"specification root does not exist: {relative}")
    return relative, path


def _document_map(specification_root: Path, root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(specification_root.rglob("*.md")):
        try:
            metadata, _ = parse_document(path.read_text(encoding="utf-8"), path.as_posix())
        except (OSError, UnicodeError, FrontMatterError):
            continue
        identifier = metadata.get("id")
        if isinstance(identifier, str) and identifier:
            result[identifier] = path.relative_to(root).as_posix()
    return result


def _entry_text(text: str, entry: ReflectionEntry) -> str:
    lines = text.splitlines()
    start = entry.line - 1
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("### ") or lines[index].startswith("## "):
            end = index
            break
    return "\n".join(lines[start:end]).rstrip() + "\n"


def _load_entries(root: Path) -> tuple[list[ReflectionEntry], str, dict[str, str]]:
    _, specification_root = _specification_root(root)
    path = specification_root / "reflections.md"
    if not path.is_file():
        return [], "", _document_map(specification_root, root)
    text = path.read_text(encoding="utf-8")
    parsed = parse_reflection_log(text)
    if parsed.problems:
        messages = "; ".join(problem.message for problem in parsed.problems)
        raise QueueError(f"reflection log is malformed: {messages}")
    return list(parsed.entries), text, _document_map(specification_root, root)


def _load_plans(root: Path, config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    directory = root / config["plans_dir"]
    result: dict[str, dict[str, Any]] = {}
    if not directory.is_dir():
        return result
    for path in sorted(directory.glob("R-*.md")):
        try:
            metadata, _ = parse_document(path.read_text(encoding="utf-8"), path.as_posix())
        except (OSError, UnicodeError, FrontMatterError) as error:
            raise QueueError(f"invalid plan {path.relative_to(root)}: {error}") from error
        missing = [field for field in REQUIRED_PLAN_FIELDS if field not in metadata]
        if missing:
            raise QueueError(f"plan {path.name} is missing field(s): {', '.join(missing)}")
        identifier = str(metadata["id"])
        if identifier in result:
            raise QueueError(f"duplicate plan identifier: {identifier}")
        if metadata["route"] not in ROUTES:
            raise QueueError(f"plan {identifier} has invalid route {metadata['route']!r}")
        if metadata["status"] not in PLAN_STATUSES:
            raise QueueError(f"plan {identifier} has invalid status {metadata['status']!r}")
        if path.stem != identifier:
            raise QueueError(f"plan filename {path.name} does not match id {identifier}")
        result[identifier] = {
            "path": path.relative_to(root).as_posix(),
            **metadata,
        }
    return result


def _enrich(
    entry: ReflectionEntry,
    text: str,
    documents: dict[str, str],
    plans: dict[str, dict[str, Any]],
    root: Path,
) -> dict[str, Any]:
    concern = strip_reference_suffix(entry.fields.get("Concerns", ""))
    concern_path = documents.get(concern)
    if concern_path is None and concern and (root / concern).exists():
        concern_path = concern
    feature_id = entry.fields.get("Feature", "")
    return {
        "id": entry.identifier,
        "title": entry.title,
        "text": _entry_text(text, entry),
        **{key.lower(): value for key, value in entry.fields.items()},
        "feature_directory": str(PurePosixPath(documents[feature_id]).parent) if feature_id in documents else None,
        "concerns_path": concern_path,
        "plan": plans.get(entry.identifier),
    }


def queue_payload(root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    config = load_config(root)
    entries, text, documents = _load_entries(root)
    plans = _load_plans(root, config)
    skip = set(config["skip"])
    selected = [entry for entry in entries if entry.status == "open" and entry.identifier not in skip]
    selected.sort(key=lambda item: int(item.identifier[2:]), reverse=config["order"] == "newest-first")
    enriched = [_enrich(entry, text, documents, plans, root) for entry in selected]
    return {
        "entries": enriched,
        "summary": {
            "open": len(enriched),
            "planned": sum(1 for item in enriched if item["plan"] is not None),
            "total": len(entries),
        },
        "config": config,
    }, plans


def _set_frontmatter(path: Path, updates: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as error:
        raise QueueError(f"plan {path.name} has no closing frontmatter fence") from error
    seen: set[str] = set()
    for index in range(1, end):
        match = re.match(r"^([A-Za-z_][\w-]*):", lines[index])
        if match and match.group(1) in updates:
            key = match.group(1)
            lines[index] = f"{key}: {updates[key]}"
            seen.add(key)
    for key, value in updates.items():
        if key not in seen:
            lines.insert(end, f"{key}: {value}")
            end += 1
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_plan(root: Path, identifier: str, assignments: list[str]) -> dict[str, str]:
    config = load_config(root)
    plans = _load_plans(root, config)
    plan = plans.get(identifier)
    if plan is None:
        raise QueueError(f"no plan for {identifier}")
    updates: dict[str, str] = {}
    for assignment in assignments:
        if "=" not in assignment:
            raise QueueError(f"plan update must be key=value: {assignment!r}")
        key, value = assignment.split("=", 1)
        if key not in SETTABLE_KEYS:
            raise QueueError(f"plan field {key!r} is not mutable")
        if not value:
            raise QueueError(f"plan field {key!r} cannot be empty")
        updates[key] = value
    if "status" in updates:
        before = str(plan["status"])
        after = updates["status"]
        if after not in PLAN_STATUSES or after not in TRANSITIONS[before]:
            raise QueueError(f"invalid plan status transition: {before} -> {after}")
    _set_frontmatter(root / str(plan["path"]), updates)
    return {"updated": str(plan["path"]), **updates}


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--next", type=int, metavar="N")
    parser.add_argument("--entry", metavar="R-NNN")
    parser.add_argument("--plans", action="store_true")
    parser.add_argument("--set", nargs="+", metavar=("R-NNN", "key=value"))
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        arguments = create_parser().parse_args(argv)
        root = find_root(arguments.root)
        if arguments.set:
            identifier, *updates = arguments.set
            print(json.dumps(update_plan(root, identifier, updates), indent=2, sort_keys=True))
            return 0
        payload, plans = queue_payload(root)
        if arguments.plans:
            print(json.dumps(plans, indent=2, sort_keys=True))
            return 0
        entries = payload["entries"]
        if arguments.entry:
            selected = next((item for item in entries if item["id"] == arguments.entry), None)
            if selected is None:
                raise QueueError(f"no open, unskipped entry {arguments.entry}")
            print(json.dumps(selected, indent=2, sort_keys=True))
            return 0
        if arguments.next is not None:
            if arguments.next < 0:
                raise QueueError("--next must be non-negative")
            print(json.dumps([item for item in entries if item["plan"] is None][: arguments.next], indent=2, sort_keys=True))
            return 0
        if arguments.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        print(f"{'ID':<7} {'ROUTE/STATUS':<24} CONCERNS")
        for item in entries:
            plan = item["plan"]
            state = f"{plan['route']}/{plan['status']}" if plan else "-"
            print(f"{item['id']:<7} {state:<24} {item.get('concerns', '')}")
        summary = payload["summary"]
        print(f"\n{summary['open']} open · {summary['planned']} planned · {summary['total']} total")
        return 0
    except QueueError as error:
        print(f"reflection triage: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
