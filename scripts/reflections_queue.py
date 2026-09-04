#!/usr/bin/env python3
"""Deterministic per-file queue, allocation, plan-state, relocation, and removal helper.

Reflection documents live in one of three tracked buckets that mirror triage state:
``pending/`` (``triage: pending``), ``planned/`` (``triage: complete`` and
``human_intervention: not-required``), and ``needs-comments/`` (``triage: complete`` and
``human_intervention: required``). ``--allocate-id`` always returns a ``pending/`` path and
``--relocate`` moves documents into the bucket their front matter now requires; every other action
refuses a misplaced collection so the layout never drifts silently; ``--validate-entry`` is the
exception, running a bounded, read-only, project-wide validation but reporting only the findings
attributable to one requested document. A closed document (``status: resolved`` or ``dismissed``
with a ``resolution_note``) is deleted by ``--remove-closed`` rather than retained; Git history
keeps the record. A plan records only the last verification of its problem (``verified`` date and
``verified_commit``); ``--json``/``--plans`` report each plan's ``verification`` as ``current``,
``stale``, ``unverified``, or ``unknown`` against the checkout HEAD, ``--set`` accepts those two
keys, a plan cannot become ``approved`` or ``implemented`` without them, and ``status=stale``
sends a plan back to investigation.
"""

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

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from concorde.frontmatter import FrontMatterError, parse_document  # noqa: E402
from concorde.reflections.reflections import (  # noqa: E402
    BUCKETS,
    PENDING_BUCKET,
    ParsedReflections,
    ReflectionEntry,
    bucket_path,
    format_reflection_id,
    index_path,
    parse_reflections,
    reflection_number,
    reflection_path,
    reflections_path,
    strip_reference_suffix,
)
from concorde.understanding.validate import validate_project  # noqa: E402


ROUTES = frozenset({"fast-loop", "specify", "dismiss", "blocked"})
PLAN_STATUSES = frozenset(
    {"proposed", "approved", "hold", "stale", "rejected", "implemented", "ineligible", "failed", "merged"}
)
TRANSITIONS = {
    "proposed": frozenset({"approved", "hold", "stale", "rejected", "implemented", "ineligible", "failed"}),
    "approved": frozenset({"hold", "stale", "rejected", "implemented", "ineligible", "failed"}),
    "hold": frozenset({"approved", "stale", "rejected"}),
    "stale": frozenset({"proposed", "rejected"}),
    "implemented": frozenset({"merged"}),
    "rejected": frozenset(),
    "ineligible": frozenset(),
    "failed": frozenset(),
    "merged": frozenset(),
}
# Statuses that assert the problem was verified at a known commit before work proceeds.
VERIFIED_STATUSES = frozenset({"approved", "implemented"})
SETTABLE_KEYS = frozenset({"status", "branch", "worktree", "commit", "verified", "verified_commit"})
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
COMMIT_ID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
VERIFIED_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class QueueError(ValueError):
    pass


def _safe_relative(value: str, field: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or "\\" in value:
        raise QueueError(f"{field} must be a safe project-relative path: {value!r}")
    return path.as_posix()


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _collection_digest(documents: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for path, data in sorted(documents.items()):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(data)
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def _reject_symlink_components(
    root: Path, path: Path, field: str, *, final_may_be_missing: bool = False
) -> None:
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


def _bucket_directory(root: Path, bucket: str, *, create: bool = False) -> Path:
    """Return one real bucket directory, optionally creating it, never following symlinks."""
    directory = root / bucket_path(bucket)
    _reject_symlink_components(root, directory, "reflection bucket", final_may_be_missing=True)
    if directory.exists() and not directory.is_dir():
        raise QueueError(f"reflection bucket must be one real directory: {bucket_path(bucket)}")
    if create and not directory.exists():
        try:
            directory.mkdir(mode=0o755)
        except OSError as error:
            raise QueueError(f"cannot create reflection bucket {bucket_path(bucket)}: {error}") from error
    return directory


def _load_reflections(
    root: Path, *, required: bool = False, allow_misplaced: bool = False
) -> tuple[Path, bytes, ParsedReflections, dict[str, str], dict[str, bytes]]:
    _, specification_root = _specification_root(root)
    documents_by_id = _document_map(specification_root, root)
    directory = root / reflections_path()
    index = root / index_path()
    if not directory.exists() and not directory.is_symlink():
        if required:
            raise QueueError(f"reflection directory is missing: {reflections_path()}")
        return index, b"", parse_reflections({}, None), documents_by_id, {}
    _reject_symlink_components(root, directory, "reflection directory")
    if not directory.is_dir():
        raise QueueError(f"reflection directory must be real: {reflections_path()}")
    if not index.exists() and not index.is_symlink():
        if required:
            raise QueueError(f"reflection allocation index is missing: {index_path()}")
        index_bytes = b""
        index_text = None
    else:
        _require_real_file(root, index, "reflection allocation index")
        try:
            index_bytes = index.read_bytes()
            index_text = index_bytes.decode("utf-8")
        except (OSError, UnicodeError) as error:
            raise QueueError(f"cannot read reflection allocation index: {error}") from error
    texts: dict[str, str] = {}
    raw: dict[str, bytes] = {}
    # Flat documents directly under the collection root are legacy/misplaced; they are loaded so
    # they can be diagnosed (or relocated) rather than silently dropped.
    candidates = list(directory.glob("R-*.md"))
    for bucket in BUCKETS:
        bucket_directory = _bucket_directory(root, bucket)
        if bucket_directory.is_dir():
            candidates.extend(bucket_directory.glob("R-*.md"))
    for path in sorted(candidates):
        _require_real_file(root, path, "reflection document")
        relative = path.relative_to(root).as_posix()
        try:
            data = path.read_bytes()
            texts[relative] = data.decode("utf-8")
            raw[relative] = data
        except (OSError, UnicodeError) as error:
            raise QueueError(f"cannot read reflection document {relative}: {error}") from error
    parsed = parse_reflections(texts, index_text)
    problems = [
        problem for problem in parsed.problems if not (allow_misplaced and problem.code == "placement")
    ]
    if problems:
        detail = "; ".join(f"{problem.path}: {problem.message}" for problem in problems)
        if any(problem.code == "placement" for problem in problems):
            detail += "; run reflections_queue.py --relocate to file misplaced documents by triage state"
        raise QueueError(f"reflection collection is malformed: {detail}")
    return index, index_bytes, parsed, documents_by_id, raw


def _validate_verification_fields(identifier: str, fields: dict[str, Any]) -> None:
    """A plan carries both ``verified`` and ``verified_commit`` or neither, each well-formed."""
    verified, commit = fields.get("verified"), fields.get("verified_commit")
    if (verified is None) != (commit is None):
        raise QueueError(f"plan {identifier} must carry both verified and verified_commit or neither")
    if verified is not None and not VERIFIED_DATE.fullmatch(str(verified)):
        raise QueueError(f"plan {identifier} verified must be one YYYY-MM-DD date")
    if commit is not None and not (isinstance(commit, str) and COMMIT_ID.fullmatch(commit)):
        raise QueueError(f"plan {identifier} verified_commit must be one full canonical Git object ID")


def _head_or_none(root: Path) -> str | None:
    try:
        return _captured_head(root)
    except QueueError:
        return None


def _verification_state(plan: dict[str, Any], head: str | None) -> str:
    """Whether the plan's recorded verification still applies to the current checkout.

    ``unverified``: nothing recorded; ``current``: verified at the current HEAD; ``stale``: verified
    at another commit, so the problem must be re-verified before any further attempt; ``unknown``:
    no Git HEAD is available to compare against. The state is derived on every read and never stored.
    """
    commit = plan.get("verified_commit")
    if commit is None:
        return "unverified"
    if head is None:
        return "unknown"
    return "current" if commit == head else "stale"


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
        _validate_verification_fields(identifier, metadata)
        if reflection_number(path.stem) is None or path.stem != identifier:
            raise QueueError(f"plan filename {path.name} does not match id {identifier}")
        result[identifier] = {**metadata, "path": path.relative_to(root).as_posix()}
    return result


def _validate_high_water(parsed: ParsedReflections, plans: dict[str, dict[str, Any]]) -> int:
    if parsed.high_water is None:
        raise QueueError("reflection collection has no tracked high_water index")
    highest_entry = max((reflection_number(entry.identifier) or 0 for entry in parsed.entries), default=0)
    highest_plan = max((reflection_number(identifier) or 0 for identifier in plans), default=0)
    required = max(highest_entry, highest_plan)
    if parsed.high_water < required:
        raise QueueError(
            f"reflection high_water {format_reflection_id(parsed.high_water)} is below retained "
            f"document/plan {format_reflection_id(required)}"
        )
    return parsed.high_water


def _enrich(
    entry: ReflectionEntry,
    raw: dict[str, bytes],
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
        "path": entry.path,
        "bucket": entry.bucket,
        "text": raw[entry.path].decode("utf-8"),
        **{key.lower().replace(" ", "_"): value for key, value in entry.fields.items()},
        "feature_path": documents.get(feature_id),
        "concerns_path": concern_path,
        "plan": plans.get(entry.identifier),
    }


def queue_payload(root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    config = load_config(root)
    _, _, parsed, documents, raw = _load_reflections(root, required=True)
    plans = _load_plans(root, config)
    _validate_high_water(parsed, plans)
    head = _head_or_none(root)
    for plan in plans.values():
        plan["verification"] = _verification_state(plan, head)
    skip = set(config["skip"])
    selected = [entry for entry in parsed.entries if entry.status == "open" and entry.identifier not in skip]
    selected.sort(
        key=lambda item: reflection_number(item.identifier) or 0,
        reverse=config["order"] == "newest-first",
    )
    enriched = [_enrich(entry, raw, documents, plans, root) for entry in selected]
    return {
        "entries": enriched,
        "summary": {
            "open": len(enriched),
            "pending_triage": sum(1 for entry in selected if entry.triage == "pending"),
            "planned": sum(1 for item in enriched if item["plan"] is not None),
            "closed": len(parsed.closed()),
            "total": len(parsed.entries),
            "buckets": parsed.bucket_counts(),
        },
        "config": config,
    }, plans


def _atomic_file_replace(root: Path, path: Path, expected: bytes, replacement: bytes, field: str) -> None:
    _require_real_file(root, path, field)
    try:
        current = path.read_bytes()
        mode = stat.S_IMODE(path.stat().st_mode)
    except OSError as error:
        raise QueueError(f"cannot inspect {field} before write: {error}") from error
    if current != expected:
        raise QueueError(f"{field} digest changed before atomic replacement")
    stage = path.with_name(f".{path.name}.reflection-stage")
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
        _require_real_file(root, path, field)
        if path.read_bytes() != expected:
            raise QueueError(f"{field} digest changed during atomic replacement")
        os.replace(stage, path)
    except QueueError:
        raise
    except OSError as error:
        raise QueueError(f"atomic {field} replacement failed: {error}") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            stage.unlink(missing_ok=True)
        except OSError:
            pass


def _git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(["git", "-C", str(root), *arguments], text=True, capture_output=True)
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
    path, before, parsed, _, _ = _load_reflections(root, required=True)
    plans = _load_plans(root, config)
    previous = _validate_high_water(parsed, plans)
    allocated = previous + 1
    _bucket_directory(root, PENDING_BUCKET, create=True)
    replacement = (
        json.dumps({"high_water": format_reflection_id(allocated), "schema_version": 1}, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")
    _atomic_file_replace(root, path, before, replacement, "reflection allocation index")
    return {
        "tool": "allocate-reflection-id",
        "status": "allocated",
        "index_path": index_path(),
        "reflection_path": reflection_path(format_reflection_id(allocated), PENDING_BUCKET),
        "bucket": PENDING_BUCKET,
        "allocated_id": format_reflection_id(allocated),
        "previous_high_water": format_reflection_id(previous),
        "high_water": format_reflection_id(allocated),
        "before_sha256": _sha256(before),
        "after_sha256": _sha256(replacement),
    }


def _remove_documents(root: Path, paths: list[Path], expected: dict[str, bytes]) -> None:
    directory = root / reflections_path()
    stage = directory / ".remove-stage"
    if stage.exists() or stage.is_symlink():
        raise QueueError(f"stale reflection removal staging path exists: {stage.relative_to(root)}")
    moved: list[tuple[Path, Path]] = []
    try:
        stage.mkdir(mode=0o700)
        for path in paths:
            _require_real_file(root, path, "reflection document")
            relative = path.relative_to(root).as_posix()
            if path.read_bytes() != expected[relative]:
                raise QueueError(f"reflection document changed before removal: {relative}")
            staged = stage / path.name
            os.replace(path, staged)
            moved.append((path, staged))
    except (OSError, QueueError) as error:
        for original, staged in reversed(moved):
            if staged.exists() and not original.exists():
                os.replace(staged, original)
        try:
            stage.rmdir()
        except OSError:
            pass
        if isinstance(error, QueueError):
            raise
        raise QueueError(f"atomic reflection removal failed: {error}") from error
    # All canonical paths are absent: removal is committed. Tombstone cleanup is best-effort and
    # cannot make a completed removal look failed after rollback is no longer possible.
    for _, staged in moved:
        try:
            staged.unlink()
        except OSError:
            pass
    try:
        stage.rmdir()
    except OSError:
        pass


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
    _, _, parsed, _, raw = _load_reflections(root, required=True)
    plans = _load_plans(root, config)
    _validate_high_water(parsed, plans)
    entries = {entry.identifier: entry for entry in parsed.entries}
    head = _captured_head(root)
    for identifier in identifiers:
        entry = entries.get(identifier)
        if entry is None:
            raise QueueError(f"reflection {identifier} has no matching open document")
        if entry.status != "open":
            raise QueueError(f"reflection {identifier} is not open")
        plan = plans.get(identifier)
        if plan is None:
            raise QueueError(f"reflection {identifier} has no matching plan")
        if plan.get("recorded_under") != entry.feature:
            raise QueueError(f"plan {identifier} recorded_under does not match reflection feature")
        if plan.get("route") != "fast-loop":
            raise QueueError(f"plan {identifier} route is not fast-loop")
        if plan.get("effort") != "small":
            raise QueueError(f"plan {identifier} effort is not small")
        if plan.get("status") != "merged":
            raise QueueError(f"plan {identifier} status is not merged")
        _validate_commit(root, identifier, plan.get("commit"), head)
    if _captured_head(root) != head:
        raise QueueError("Git HEAD changed during merged-reflection validation")
    before_digest = _collection_digest(raw)
    paths = [root / entries[identifier].path for identifier in identifiers]
    _remove_documents(root, paths, raw)
    remaining = {path: data for path, data in raw.items() if path not in {entry.path for entry in (entries[item] for item in identifiers)}}
    return {
        "tool": "remove-merged-reflections",
        "status": "removed",
        "removed": identifiers,
        "removed_paths": [entries[identifier].path for identifier in identifiers],
        "removed_count": len(identifiers),
        "remaining_count": len(parsed.entries) - len(identifiers),
        "head": head,
        "before_sha256": before_digest,
        "after_sha256": _collection_digest(remaining),
    }


def _bucket_counts_excluding(parsed: ParsedReflections, excluded: set[str]) -> dict[str, int]:
    counts = {bucket: 0 for bucket in BUCKETS}
    for entry in parsed.entries:
        if entry.identifier in excluded:
            continue
        bucket = entry.bucket
        if bucket is not None:
            counts[bucket] += 1
    return counts


def remove_closed(root: Path, requested: list[str]) -> dict[str, Any]:
    """Remove every requested (or, with none named, every) closed reflection document.

    A closed reflection has ``status: resolved`` or ``status: dismissed``. The maintainer's
    disposition and ``resolution_note`` are preserved in Git history; only the working-tree document
    is deleted. ``index.json``, plans, and every other document are left untouched.
    """
    identifiers: list[str] = []
    seen: set[str] = set()
    for value in requested:
        if reflection_number(value) is None:
            raise QueueError(f"remove-closed ID must be canonical: {value!r}")
        if value in seen:
            raise QueueError(f"remove-closed ID is repeated: {value}")
        seen.add(value)
        identifiers.append(value)
    identifiers.sort(key=lambda item: reflection_number(item) or 0)

    config = load_config(root)
    _, _, parsed, _, raw = _load_reflections(root, required=True)
    plans = _load_plans(root, config)
    _validate_high_water(parsed, plans)
    entries = {entry.identifier: entry for entry in parsed.entries}

    if identifiers:
        selected = identifiers
        for identifier in selected:
            entry = entries.get(identifier)
            if entry is None:
                raise QueueError(f"reflection {identifier} has no matching document")
            if entry.status not in {"resolved", "dismissed"}:
                raise QueueError(
                    f"reflection {identifier} is still open; record status resolved or dismissed "
                    "with a resolution_note before removal"
                )
    else:
        selected = [entry.identifier for entry in parsed.closed()]

    for identifier in selected:
        if not entries[identifier].fields.get("Note", "").strip():
            raise QueueError(f"reflection {identifier} is closed without a resolution_note")

    before_digest = _collection_digest(raw)
    if not selected:
        return {
            "tool": "remove-closed-reflections",
            "status": "unchanged",
            "removed": [],
            "removed_count": 0,
            "remaining_count": len(parsed.entries),
            "buckets": _bucket_counts_excluding(parsed, set()),
            "before_sha256": before_digest,
            "after_sha256": before_digest,
        }

    removed_set = set(selected)
    paths = [root / entries[identifier].path for identifier in selected]
    _remove_documents(root, paths, raw)
    removed_paths = {entries[identifier].path for identifier in selected}
    remaining = {path: data for path, data in raw.items() if path not in removed_paths}
    removed = sorted(
        (
            {
                "id": identifier,
                "status": entries[identifier].status,
                "path": entries[identifier].path,
                "title": entries[identifier].title,
                "resolution_note": entries[identifier].fields.get("Note", ""),
            }
            for identifier in selected
        ),
        key=lambda item: reflection_number(item["id"]) or 0,
    )
    return {
        "tool": "remove-closed-reflections",
        "status": "removed",
        "removed": removed,
        "removed_count": len(selected),
        "remaining_count": len(parsed.entries) - len(selected),
        "buckets": _bucket_counts_excluding(parsed, removed_set),
        "before_sha256": before_digest,
        "after_sha256": _collection_digest(remaining),
    }


def _move_documents(root: Path, moves: list[tuple[str, str, str]], expected: dict[str, bytes]) -> None:
    """Move documents between buckets, rolling every completed move back on any failure."""
    done: list[tuple[Path, Path]] = []
    try:
        for identifier, source_relative, target_relative in moves:
            source = root / source_relative
            target = root / target_relative
            _require_real_file(root, source, "reflection document")
            if source.read_bytes() != expected[source_relative]:
                raise QueueError(f"reflection document changed before relocation: {source_relative}")
            _bucket_directory(root, target.parent.name, create=True)
            if target.exists() or target.is_symlink():
                raise QueueError(f"relocation target for {identifier} already exists: {target_relative}")
            os.replace(source, target)
            done.append((source, target))
    except (OSError, QueueError) as error:
        for source, target in reversed(done):
            if target.exists() and not source.exists():
                os.replace(target, source)
        if isinstance(error, QueueError):
            raise
        raise QueueError(f"reflection relocation failed: {error}") from error


def relocate(root: Path, requested: list[str]) -> dict[str, Any]:
    """Move reflection documents into the bucket their triage state requires.

    With no identifiers every misplaced document is relocated. The bucket is derived only from
    ``triage`` and ``human_intervention``; the document text is never changed.
    """
    identifiers: list[str] = []
    seen: set[str] = set()
    for value in requested:
        if reflection_number(value) is None:
            raise QueueError(f"relocate ID must be canonical: {value!r}")
        if value in seen:
            raise QueueError(f"relocate ID is repeated: {value}")
        seen.add(value)
        identifiers.append(value)
    identifiers.sort(key=lambda item: reflection_number(item) or 0)

    config = load_config(root)
    _, _, parsed, _, raw = _load_reflections(root, required=True, allow_misplaced=True)
    plans = _load_plans(root, config)
    _validate_high_water(parsed, plans)
    entries = {entry.identifier: entry for entry in parsed.entries}
    selected = identifiers or [entry.identifier for entry in parsed.entries]
    moves: list[tuple[str, str, str]] = []
    for identifier in selected:
        entry = entries.get(identifier)
        if entry is None:
            raise QueueError(f"reflection {identifier} has no matching document")
        expected = entry.expected_path
        if expected is None:
            raise QueueError(f"reflection {identifier} has no decidable bucket; complete its triage first")
        if entry.path != expected:
            moves.append((identifier, entry.path, expected))
    before_digest = _collection_digest(raw)
    _move_documents(root, moves, raw)
    moved = {source: target for _, source, target in moves}
    after = {moved.get(path, path): data for path, data in raw.items()}
    return {
        "tool": "relocate-reflections",
        "status": "relocated" if moves else "unchanged",
        "moved": [
            {
                "id": identifier,
                "from": source,
                "to": target,
                "bucket": entries[identifier].bucket,
            }
            for identifier, source, target in moves
        ],
        "moved_count": len(moves),
        "unchanged_count": len(selected) - len(moves),
        "buckets": parsed.bucket_counts(),
        "before_sha256": before_digest,
        "after_sha256": _collection_digest(after),
    }


def _locate_reflection_document(root: Path, identifier: str) -> tuple[Path, str, str | None]:
    """Return ``(absolute path, project-relative path, bucket)`` for one reflection ID's document.

    Every tracked bucket is tried first; the legacy flat ``.concorde/reflections/R-NNN.md`` path is
    tried last with bucket ``None``. Raises :class:`QueueError` if no such file exists.
    """
    candidates: list[tuple[Path, str | None]] = [
        (root / reflection_path(identifier, bucket), bucket) for bucket in BUCKETS
    ]
    candidates.append((root / reflections_path() / f"{identifier}.md", None))
    for candidate, bucket in candidates:
        if candidate.exists() or candidate.is_symlink():
            _require_real_file(root, candidate, "reflection document")
            return candidate, candidate.relative_to(root).as_posix(), bucket
    raise QueueError(f"no reflection document for {identifier}")


def validate_entry(root: Path, identifier: str) -> dict[str, Any]:
    """Run bounded, read-only, attributable validation for one reflection document.

    Full project validation runs (nothing here bypasses any rule), but the report separates
    findings attributable to the requested document (by ``source`` path or ``subject_id``) from
    every other finding, which is counted and summarized by rule only. This intentionally does not
    use ``_load_reflections``: other malformed or misplaced documents must never block validating
    one entry.
    """
    if reflection_number(identifier) is None:
        raise QueueError(f"validate-entry ID must be canonical: {identifier!r}")
    path, relative, bucket = _locate_reflection_document(root, identifier)
    data = path.read_bytes()
    result = validate_project(root)
    attributable: list[Any] = []
    unrelated: list[Any] = []
    for finding in result.findings:
        if finding.source == relative or finding.subject_id == identifier:
            attributable.append(finding)
        else:
            unrelated.append(finding)
    attributable.sort(key=lambda finding: (finding.rule_id, finding.line if finding.line is not None else -1))
    return {
        "tool": "validate-reflection-entry",
        "id": identifier,
        "path": relative,
        "bucket": bucket,
        "status": "invalid" if attributable else "valid",
        "sha256": _sha256(data),
        "findings": [
            {
                "rule_id": finding.rule_id,
                "severity": finding.severity,
                "source": finding.source,
                "line": finding.line,
                "message": finding.message,
                "remediation": finding.remediation,
            }
            for finding in attributable
        ],
        "unrelated": {
            "count": len(unrelated),
            "rules": sorted({finding.rule_id for finding in unrelated}),
        },
        "project_status": result.status,
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
    merged = {**plan, **updates}
    _validate_verification_fields(identifier, merged)
    if "status" in updates:
        before = str(plan["status"])
        after = updates["status"]
        if after not in PLAN_STATUSES or after not in TRANSITIONS[before]:
            raise QueueError(f"invalid plan status transition: {before} -> {after}")
        if after in VERIFIED_STATUSES and merged.get("verified_commit") is None:
            raise QueueError(f"plan status {after} requires verified and verified_commit")
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
    actions.add_argument(
        "--remove-closed",
        nargs="*",
        metavar="R-NNN",
        help="remove the named (default: every closed) resolved/dismissed reflection document",
    )
    actions.add_argument(
        "--relocate",
        nargs="*",
        metavar="R-NNN",
        help="move the named (default: every misplaced) reflection into the bucket its triage state requires",
    )
    actions.add_argument(
        "--validate-entry",
        metavar="R-NNN",
        help="run bounded, read-only validation attributable to one reflection document",
    )
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
        if arguments.remove_closed is not None:
            print(json.dumps(remove_closed(root, arguments.remove_closed), indent=2, sort_keys=True))
            return 0
        if arguments.relocate is not None:
            print(json.dumps(relocate(root, arguments.relocate), indent=2, sort_keys=True))
            return 0
        if arguments.validate_entry:
            payload = validate_entry(root, arguments.validate_entry)
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0 if payload["status"] == "valid" else 1
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
                raise QueueError(f"no open, unskipped reflection {arguments.entry}")
            print(json.dumps(selected, indent=2, sort_keys=True))
            return 0
        if arguments.next is not None:
            if arguments.next < 0:
                raise QueueError("--next must be non-negative")
            print(json.dumps(entries[: arguments.next], indent=2, sort_keys=True))
            return 0
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except (OSError, QueueError, UnicodeError, ValueError) as error:
        print(f"reflection queue error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
