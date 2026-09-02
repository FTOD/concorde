#!/usr/bin/env python3
"""Deterministic queue, allocation, plan-state, and merged-removal helper for reflection-triage/v3."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

EXTENSION_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(EXTENSION_ROOT / "runtime"))

from concorde.frontmatter import FrontMatterError, parse_document  # noqa: E402
from concorde.reflections import (  # noqa: E402
    ParsedLog,
    ReflectionEntry,
    format_reflection_id,
    log_path,
    parse_reflection_log,
    reflection_number,
    strip_reference_suffix,
)


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


COMMIT_ID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


def _safe_relative(value: str, field: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or "\\" in value:
        raise QueueError(f"{field} must be a safe project-relative path: {value!r}")
    return path.as_posix()


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _reject_symlink_components(root: Path, path: Path, field: str, *, final_may_be_missing: bool = False) -> None:
    try:
        relative = path.relative_to(root)
    except ValueError as error:
        raise QueueError(f"{field} escapes project root: {path}") from error
    current = root
    for index, part in enumerate(relative.parts):
        current /= part
        final = index == len(relative.parts) - 1
        if current.is_symlink():
            raise QueueError(f"{field} may not contain a symlink: {current.relative_to(root)}")
        if not current.exists() and not (final and final_may_be_missing):
            raise QueueError(f"{field} is missing: {current.relative_to(root)}")


def _require_real_file(root: Path, path: Path, field: str) -> None:
    _reject_symlink_components(root, path, field)
    try:
        mode = path.stat().st_mode
    except OSError as error:
        raise QueueError(f"cannot inspect {field}: {error}") from error
    if not stat.S_ISREG(mode):
        raise QueueError(f"{field} must be one real file: {path.relative_to(root)}")


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
        _require_real_file(root, path, "reflection-triage config")
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
    return "\n".join(lines[entry.line - 1 : entry.end_line]).rstrip() + "\n"


def _load_log(root: Path, *, required: bool = False) -> tuple[Path, bytes, str, ParsedLog, dict[str, str]]:
    _, specification_root = _specification_root(root)
    path = root / log_path()
    documents = _document_map(specification_root, root)
    if not path.exists() and not path.is_symlink():
        if required:
            raise QueueError(f"reflection log is missing: {log_path()}")
        parsed = parse_reflection_log("")
        return path, b"", "", parsed, documents
    _require_real_file(root, path, "reflection log")
    try:
        data = path.read_bytes()
        text = data.decode("utf-8")
    except (OSError, UnicodeError) as error:
        raise QueueError(f"cannot read reflection log: {error}") from error
    parsed = parse_reflection_log(text)
    if parsed.problems:
        messages = "; ".join(problem.message for problem in parsed.problems)
        raise QueueError(f"reflection log is malformed: {messages}")
    return path, data, text, parsed, documents


def _load_entries(root: Path) -> tuple[list[ReflectionEntry], str, dict[str, str]]:
    _, _, text, parsed, documents = _load_log(root)
    return list(parsed.entries), text, documents


def _load_plans(root: Path, config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    directory = root / config["plans_dir"]
    result: dict[str, dict[str, Any]] = {}
    if not directory.exists() and not directory.is_symlink():
        return result
    _reject_symlink_components(root, directory, "reflection plan directory")
    if not directory.is_dir():
        raise QueueError(f"reflection plan directory must be one real directory: {config['plans_dir']}")
    for path in sorted(directory.glob("R-*.md")):
        _require_real_file(root, path, "reflection plan")
        try:
            metadata, _ = parse_document(path.read_text(encoding="utf-8"), path.as_posix())
        except (OSError, UnicodeError, FrontMatterError) as error:
            raise QueueError(f"invalid plan {path.relative_to(root)}: {error}") from error
        missing = [field for field in REQUIRED_PLAN_FIELDS if field not in metadata]
        if missing:
            raise QueueError(f"plan {path.name} is missing field(s): {', '.join(missing)}")
        raw_identifier = metadata["id"]
        if not isinstance(raw_identifier, str) or reflection_number(raw_identifier) is None:
            raise QueueError(f"plan {path.name} has noncanonical reflection id {raw_identifier!r}")
        identifier = raw_identifier
        if identifier in result:
            raise QueueError(f"duplicate plan identifier: {identifier}")
        if metadata["route"] not in ROUTES:
            raise QueueError(f"plan {identifier} has invalid route {metadata['route']!r}")
        if metadata["status"] not in PLAN_STATUSES:
            raise QueueError(f"plan {identifier} has invalid status {metadata['status']!r}")
        if reflection_number(path.stem) is None or path.stem != identifier:
            raise QueueError(f"plan filename {path.name} does not match id {identifier}")
        result[identifier] = {
            **metadata,
            "path": path.relative_to(root).as_posix(),
        }
    return result


def _validate_high_water(parsed: ParsedLog, plans: dict[str, dict[str, Any]]) -> int:
    if parsed.high_water is None:
        raise QueueError("reflection log has no tracked high-water marker")
    highest_entry = max((reflection_number(entry.identifier) or 0 for entry in parsed.entries), default=0)
    highest_plan = max((reflection_number(identifier) or 0 for identifier in plans), default=0)
    required = max(highest_entry, highest_plan)
    if parsed.high_water < required:
        raise QueueError(
            f"reflection high-water {format_reflection_id(parsed.high_water)} is below retained "
            f"entry/plan {format_reflection_id(required)}"
        )
    return parsed.high_water


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
        "feature_path": documents.get(feature_id),
        "concerns_path": concern_path,
        "plan": plans.get(entry.identifier),
    }


def queue_payload(root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    config = load_config(root)
    _, _, text, parsed, documents = _load_log(root, required=True)
    entries = list(parsed.entries)
    plans = _load_plans(root, config)
    _validate_high_water(parsed, plans)
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


def _line_ending(line: str) -> str:
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\n"):
        return "\n"
    if line.endswith("\r"):
        return "\r"
    return ""


def _render_high_water(text: str, parsed: ParsedLog, number: int) -> bytes:
    if parsed.high_water_line is None:
        raise QueueError("reflection log has no tracked high-water marker")
    lines = text.splitlines(keepends=True)
    index = parsed.high_water_line - 1
    ending = _line_ending(lines[index])
    lines[index] = f"<!-- concorde-reflection-high-water: {format_reflection_id(number)} -->{ending}"
    return "".join(lines).encode("utf-8")


def _render_without_entries(text: str, parsed: ParsedLog, identifiers: set[str]) -> bytes:
    lines = text.splitlines(keepends=True)
    remove: set[int] = set()
    for entry in parsed.entries:
        if entry.identifier in identifiers:
            remove.update(range(entry.line - 1, entry.end_line))
    rendered = "".join(line for index, line in enumerate(lines) if index not in remove).encode("utf-8")
    try:
        verified = parse_reflection_log(rendered.decode("utf-8"))
    except UnicodeError as error:
        raise QueueError(f"rendered reflection log is not UTF-8: {error}") from error
    if verified.problems:
        raise QueueError("rendered reflection log is malformed: " + "; ".join(item.message for item in verified.problems))
    observed = {entry.identifier for entry in verified.entries}
    expected = {entry.identifier for entry in parsed.entries} - identifiers
    if observed != expected:
        raise QueueError("rendered reflection log did not preserve the exact retained entry set")
    if verified.high_water != parsed.high_water:
        raise QueueError("reflection removal may not lower or change the high-water marker")
    return rendered


def _atomic_log_replace(path: Path, expected: bytes, replacement: bytes) -> None:
    root = path.parents[2]
    _require_real_file(root, path, "reflection log")
    try:
        current = path.read_bytes()
        mode = stat.S_IMODE(path.stat().st_mode)
    except OSError as error:
        raise QueueError(f"cannot inspect reflection log before write: {error}") from error
    if current != expected:
        raise QueueError("reflection log digest changed before atomic replacement")
    stage = path.with_name(f".{path.name}.reflection-triage-stage")
    _reject_symlink_components(root, stage.parent, "reflection log directory")
    if stage.exists() or stage.is_symlink():
        raise QueueError(f"stale reflection staging path exists: {stage.relative_to(root)}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor: int | None = None
    try:
        descriptor = os.open(stage, flags, mode)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            stream.write(replacement)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(stage, mode)
        _require_real_file(root, path, "reflection log")
        if path.read_bytes() != expected:
            raise QueueError("reflection log digest changed during atomic replacement")
        os.replace(stage, path)
    except QueueError:
        raise
    except OSError as error:
        raise QueueError(f"atomic reflection log replacement failed: {error}") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            stage.unlink(missing_ok=True)
        except OSError:
            pass


def _git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *arguments],
            text=True,
            capture_output=True,
        )
    except OSError as error:
        raise QueueError(f"cannot execute git: {error}") from error
    if check and completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        raise QueueError(detail)
    return completed


def _captured_head(root: Path) -> str:
    head = _git(root, "rev-parse", "--verify", "HEAD^{commit}").stdout.strip()
    if not COMMIT_ID.fullmatch(head):
        raise QueueError("Git HEAD did not resolve to one canonical commit ID")
    return head


def _validate_commit(root: Path, identifier: str, commit: Any, head: str) -> str:
    if not isinstance(commit, str) or not COMMIT_ID.fullmatch(commit):
        raise QueueError(f"plan {identifier} commit must be one full canonical Git object ID")
    resolved = _git(root, "rev-parse", "--verify", f"{commit}^{{commit}}").stdout.strip()
    if resolved != commit:
        raise QueueError(f"plan {identifier} commit is not canonical: {commit}")
    ancestor = _git(root, "merge-base", "--is-ancestor", commit, head, check=False)
    if ancestor.returncode == 1:
        raise QueueError(f"plan {identifier} commit is not an ancestor of captured HEAD")
    if ancestor.returncode != 0:
        raise QueueError(ancestor.stderr.strip() or f"cannot verify plan {identifier} commit ancestry")
    return commit


def allocate_id(root: Path) -> dict[str, Any]:
    config = load_config(root)
    path, before, text, parsed, _ = _load_log(root, required=True)
    plans = _load_plans(root, config)
    previous = _validate_high_water(parsed, plans)
    allocated = previous + 1
    replacement = _render_high_water(text, parsed, allocated)
    _atomic_log_replace(path, before, replacement)
    return {
        "operation": "allocate-reflection-id",
        "status": "allocated",
        "log_path": log_path(),
        "allocated_id": format_reflection_id(allocated),
        "previous_high_water": format_reflection_id(previous),
        "high_water": format_reflection_id(allocated),
        "before_sha256": _sha256(before),
        "after_sha256": _sha256(replacement),
    }


def remove_merged(root: Path, requested: list[str]) -> dict[str, Any]:
    if not requested:
        raise QueueError("remove-merged requires at least one reflection ID")
    identifiers: list[str] = []
    seen: set[str] = set()
    for value in requested:
        if reflection_number(value) is None:
            raise QueueError(f"remove-merged ID must be canonical: {value!r}")
        if value in seen:
            raise QueueError(f"remove-merged ID is repeated: {value}")
        seen.add(value)
        identifiers.append(value)
    identifiers.sort(key=lambda item: reflection_number(item) or 0)

    config = load_config(root)
    path, before, text, parsed, _ = _load_log(root, required=True)
    plans = _load_plans(root, config)
    _validate_high_water(parsed, plans)
    entries = {entry.identifier: entry for entry in parsed.entries}
    head = _captured_head(root)
    for identifier in identifiers:
        entry = entries.get(identifier)
        if entry is None:
            raise QueueError(f"reflection {identifier} has no matching open entry")
        if entry.status != "open":
            raise QueueError(f"reflection {identifier} is not open")
        plan = plans.get(identifier)
        if plan is None:
            raise QueueError(f"reflection {identifier} has no matching plan")
        if plan.get("recorded_under") != entry.feature:
            raise QueueError(f"plan {identifier} recorded_under does not match reflection Feature")
        if plan.get("route") != "fast-loop":
            raise QueueError(f"plan {identifier} route is not fast-loop")
        if plan.get("effort") != "small":
            raise QueueError(f"plan {identifier} effort is not small")
        if plan.get("status") != "merged":
            raise QueueError(f"plan {identifier} status is not merged")
        _validate_commit(root, identifier, plan.get("commit"), head)

    replacement = _render_without_entries(text, parsed, set(identifiers))
    if _captured_head(root) != head:
        raise QueueError("Git HEAD changed during merged-reflection validation")
    _atomic_log_replace(path, before, replacement)
    return {
        "operation": "remove-merged-reflections",
        "status": "removed",
        "log_path": log_path(),
        "removed": identifiers,
        "removed_count": len(identifiers),
        "remaining_count": len(parsed.entries) - len(identifiers),
        "head": head,
        "before_sha256": _sha256(before),
        "after_sha256": _sha256(replacement),
    }


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
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--json", action="store_true")
    actions.add_argument("--next", type=int, metavar="N")
    actions.add_argument("--entry", metavar="R-NNN")
    actions.add_argument("--plans", action="store_true")
    actions.add_argument("--set", nargs="+", metavar=("R-NNN", "key=value"))
    actions.add_argument("--allocate-id", action="store_true")
    actions.add_argument("--remove-merged", nargs="+", metavar="R-NNN")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        arguments = create_parser().parse_args(argv)
        root = find_root(arguments.root)
        if arguments.allocate_id:
            print(json.dumps(allocate_id(root), indent=2, sort_keys=True))
            return 0
        if arguments.remove_merged:
            print(json.dumps(remove_merged(root, arguments.remove_merged), indent=2, sort_keys=True))
            return 0
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
