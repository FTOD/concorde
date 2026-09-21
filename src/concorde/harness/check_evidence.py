"""Host-only, bounded tester evidence export through the canonical primary run store.

No task-selected destination, directory archive, environment dump or lifecycle mutation.
The sandbox has stopped before report files are opened; scratch is removed after collection.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
import uuid
from pathlib import Path

from .status_store import primary_root, run_path, write_run
from ..spec.typed_data import safe_path

MAX_REPORTS = 16
MAX_REPORT_BYTES = 2 * 1024 * 1024
MAX_REPORT_TOTAL = 8 * 1024 * 1024


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def report_names(value) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) > MAX_REPORTS:
        raise ValueError("reports must be a list of at most 16 relative file names")
    for name in value:
        safe_path(name)
        if len(name) > 240:
            raise ValueError("report name exceeds 240 characters")
    if len(set(value)) != len(value):
        raise ValueError("duplicate report name")
    return tuple(value)


def _report(scratch: Path, name: str, limit: int) -> tuple[bytes, int]:
    """Walk only real directories and open a single regular, non-hardlinked file."""
    descriptor = os.open(scratch, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        parts = ("reports", *name.split("/"))
        for part in parts[:-1]:
            child = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor
            )
            os.close(descriptor)
            descriptor = child
        child = os.open(
            parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor
        )
        with os.fdopen(child, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                raise ValueError("report must be a regular non-hardlinked file")
            data = stream.read(limit)
            after = os.fstat(stream.fileno())
            if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            ):
                raise ValueError("report changed during capture")
            return data, before.st_size
    finally:
        os.close(descriptor)


class CheckEvidence:
    def __init__(
        self,
        project: Path,
        names: tuple[str, ...],
        *,
        command: str,
        timeout: float,
        selection: dict | None = None,
        tool_call_id: str | None = None,
    ):
        from .change_worktree import git_value, snapshot_tree, workspace_identity

        self.project = project
        self.names = names
        self.execution_id = "tester-" + uuid.uuid4().hex
        self.relative = f".concorde/runs/{self.execution_id}"
        self.archive = None
        self.reference = None
        self.records: list[dict] = []
        self.errors: list[str] = []
        self.collected = False
        self.manifest = {
            "schema_version": 1,
            "execution_id": self.execution_id,
            "tool_call_id": tool_call_id,
            "source_worktree": str(project),
            # Commands can contain credentials; bind exact input without archiving it.
            "command_digest": digest(command.encode()),
            "timeout": timeout,
            "reports_requested": list(names),
            "python": sys.executable,
            "runtime_root": str(Path(__file__).resolve().parents[3]),
            "selection": None
            if selection is None
            else {
                "build_digest": selection["build_digest"],
                "runtime": selection["runtime"],
                "pi_entry": {
                    "path": selection["pi_entry"]["path"],
                    "digest": selection["pi_entry"]["digest"],
                    "catalog_digest": selection["pi_entry"]["catalog"]["digest"],
                },
            },
        }
        try:
            self.archive = primary_root(project)
            _, current = workspace_identity(project)
            tree = snapshot_tree(project, {}) if current else None
            self.manifest.update(
                branch=current["branch"] if current else None,
                commit=current["head"] if current else None,
                input_tree=tree,
                dirty=tree != git_value(project, "rev-parse", "HEAD^{tree}")
                if current
                else None,
            )
        except (OSError, ValueError, RuntimeError) as error:
            self.errors.append(f"evidence authority/provenance: {error}")

    def _save(self, name: str, data: bytes) -> dict:
        if self.archive is None:
            raise ValueError(
                "primary evidence authority unavailable; no local fallback"
            )
        relative = f"{self.relative}/{name}"
        # Reuse candidate-local-ledger refusal and primary authority checks as well
        # as the writer; binding an archive must not bypass source provenance checks.
        if primary_root(self.project) != self.archive:
            raise ValueError("primary evidence authority changed during execution")
        write_run(self.project, relative, data)
        # Existing atomic primary writer supplies mode 0600 and repository locking.
        return {
            "path": str(run_path(self.archive, relative)),
            "digest": digest(data),
            "bytes": len(data),
        }

    def _capture(self, name: str, data: bytes, total: int, *, portion: str):
        record = {
            "name": name,
            "available_bytes": total,
            "captured_bytes": len(data),
            "truncated": len(data) != total,
            "portion": portion,
            "artifact": None,
        }
        try:
            record["artifact"] = self._save(name, data)
        except (OSError, ValueError, RuntimeError) as error:
            record["error"] = str(error)
            self.errors.append(f"export {name}: {error}")
        self.records.append(record)

    def collect(self, scratch: Path | None, result, error=None):
        self.collected = True
        for name in ("stdout", "stderr"):
            data = getattr(result if result is not None else error, name, b"")
            total = getattr(
                result if result is not None else error, name + "_bytes", None
            )
            self._capture(
                name + ".bin",
                data,
                len(data) if total is None else total,
                portion="tail",
            )
        remaining = MAX_REPORT_TOTAL
        for name in self.names:
            try:
                if scratch is None:
                    raise ValueError("scratch/report unavailable before execution")
                data, total = _report(scratch, name, min(MAX_REPORT_BYTES, remaining))
                remaining -= len(data)
                self._capture("reports/" + name, data, total, portion="prefix")
            except (OSError, ValueError) as failure:
                self.records.append(
                    {"name": "reports/" + name, "artifact": None, "error": str(failure)}
                )
                self.errors.append(f"capture {name}: {failure}")
        self.manifest.update(
            returncode=result.returncode if result else None,
            timed_out=result.timed_out if result else False,
            cancelled=isinstance(error, KeyboardInterrupt),
            error=str(error) if error is not None else None,
        )
        self._finish()

    def _finish(self):
        artifacts_complete = not self.errors and not any(
            r.get("truncated") for r in self.records
        )
        self.manifest.update(
            artifacts=self.records,
            errors=self.errors,
            artifacts_complete=artifacts_complete,
            complete=artifacts_complete
            and not self.manifest.get("cancelled")
            and not self.manifest.get("timed_out")
            and self.manifest.get("error") is None,
        )
        try:
            self.reference = self._save(
                "manifest.json",
                (json.dumps(self.manifest, sort_keys=True) + "\n").encode(),
            )
        except (OSError, ValueError, RuntimeError) as error:
            self.errors.append(f"export manifest: {error}")
            self.manifest.update(complete=False, artifacts_complete=False)

    def summary(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "manifest": self.reference,
            "complete": self.manifest.get("complete", False),
            "artifacts_complete": self.manifest.get("artifacts_complete", False),
            "artifact_count": len(self.records),
            "truncated_artifacts": [
                r["name"] for r in self.records if r.get("truncated")
            ],
            # A failed manifest save must not hide artifacts that did export.
            "artifacts": self.records if self.reference is None else [],
            "errors": self.errors,
        }
