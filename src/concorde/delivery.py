"""Digest-bound Delivery Proposal 9: validate and remove one complete attempt only."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, Iterable

from .diagnostics import digest_sources
from .feature_workspace import WorkspaceError, _read_persisted_selection, _resolve_feature, resolve_phase_paths
from .model import Finding, SourceDocument, ToolResult
from .reflections import log_path, parse_reflection_log
from .repository import ProjectRepository, RepositoryError, safe_relative_path


TASK_LINE = re.compile(r"^\s*-\s+\[([ xX])\]\s+(T\d{3,})\b")
TASK_REFERENCE = re.compile(r"\bT\d{3,}\b")
CHECKLIST_LINE = re.compile(r"^\s*-\s+\[([ xX])\](?:\s+.*)?$")
CHECKBOX_LIKE_LINE = re.compile(r"^\s*-\s+\[[^\]]*\]")
EVIDENCE_HEADING = re.compile(r"^###\s+(T\d{3,})\b.*$", re.MULTILINE)
PASSED_OUTCOME = re.compile(r"\*\*Outcome\*\*:\s*passed\b", re.IGNORECASE)
DELIVERY_PROPOSAL_KEYS = frozenset({"proposal_version", "tool", "target", "source_digest", "remove"})


def _finding(rule: str, source: str, message: str, remediation: str) -> Finding:
    return Finding(rule, "error", source, message, remediation)


def _resolve_target(project: Path, package: Any, target: str | None) -> tuple[SourceDocument, Any]:
    resolved_target = target or _read_persisted_selection(project)
    feature = _resolve_feature(package, resolved_target)
    if feature is None:
        raise WorkspaceError(f"feature target '{resolved_target}' does not resolve exactly once")
    return feature, resolve_phase_paths(project, feature.path)


def _attempt_files(project: Path, attempt_dir: str, ignored: str | None = None) -> list[str]:
    attempt = project / attempt_dir
    if not attempt.is_dir() or attempt.is_symlink():
        raise WorkspaceError("delivery requires one real stable-ID project-control attempt directory")
    files: list[str] = []
    for path in sorted(attempt.rglob("*")):
        relative = path.relative_to(project).as_posix()
        if path.is_symlink():
            raise WorkspaceError(f"delivery input may not be a symlink: {relative}")
        if path.is_file() and relative != ignored:
            files.append(relative)
    return files


def _delivery_digest(project: Path, package: Any, paths: Any, ignored: str | None = None) -> str:
    sources = [source.path for source in package.sources]
    sources.extend(package.diagrams)
    if (project / paths.reflections).is_file() and not (project / paths.reflections).is_symlink():
        sources.append(paths.reflections)
    sources.extend(_executable_files(project, paths))
    sources.extend(_attempt_files(project, paths.attempt_dir, ignored))
    return digest_sources(project, sources)


def _task_state(project: Path, tasks_path: str) -> tuple[list[str], list[str], list[str]]:
    path = project / tasks_path
    if not path.is_file() or path.is_symlink():
        return [], [], ["tasks.md is missing or is not a real file"]
    complete: list[str] = []
    incomplete: list[str] = []
    malformed: list[str] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = TASK_LINE.match(line)
        if match:
            (complete if match.group(1).lower() == "x" else incomplete).append(match.group(2))
        elif TASK_REFERENCE.search(line) and CHECKBOX_LIKE_LINE.match(line):
            malformed.append(f"line {number}")
    if not complete and not incomplete:
        malformed.append("no recognizable task items")
    return complete, incomplete, malformed


def _checklist_state(project: Path, checklists_dir: str) -> tuple[int, list[str], list[str], list[str]]:
    directory = project / checklists_dir
    if directory.is_symlink():
        raise WorkspaceError(f"delivery checklist directory may not be a symlink: {checklists_dir}")
    if not directory.exists():
        return 0, [], [], []
    if not directory.is_dir():
        raise WorkspaceError(f"delivery checklist path is not a directory: {checklists_dir}")
    complete: list[str] = []
    incomplete: list[str] = []
    malformed: list[str] = []
    files = 0
    for path in sorted(directory.glob("*.md")):
        relative = path.relative_to(project).as_posix()
        if path.is_symlink():
            raise WorkspaceError(f"delivery checklist input may not be a symlink: {relative}")
        if not path.is_file():
            continue
        files += 1
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            match = CHECKLIST_LINE.match(line)
            reference = f"{relative}:line {number}"
            if match:
                (complete if match.group(1).lower() == "x" else incomplete).append(reference)
            elif CHECKBOX_LIKE_LINE.match(line):
                malformed.append(reference)
    return files, complete, incomplete, malformed


def _validation_state(project: Path, validation_path: str, task_ids: Iterable[str]) -> tuple[list[str], list[str]]:
    path = project / validation_path
    if not path.is_file() or path.is_symlink():
        return [], ["validation.md is missing or is not a real file"]
    body = path.read_text(encoding="utf-8")
    matches = list(EVIDENCE_HEADING.finditer(body))
    passed: list[str] = []
    for index, match in enumerate(matches):
        block = body[match.end() : matches[index + 1].start() if index + 1 < len(matches) else len(body)]
        if PASSED_OUTCOME.search(block):
            passed.append(match.group(1))
    missing = sorted(set(task_ids) - set(passed))
    return sorted(set(passed)), missing


def _authority_paths(project: Path, package: Any, paths: Any) -> list[str]:
    result = [paths.feature_path, paths.module_architecture]
    result.extend(item["architecture"] for item in paths.module_ancestry)
    result.extend(item["feature_path"] for item in paths.related_features)
    if (project / paths.reflections).is_file():
        result.append(paths.reflections)
    return sorted(set(result))


def _executable_files(project: Path, paths: Any) -> list[str]:
    result: list[str] = []
    for roots in paths.executable_context.values():
        for root in roots:
            directory = project / root
            for path in sorted(directory.rglob("*")):
                if path.is_file() and not path.is_symlink():
                    relative = path.relative_to(project).as_posix()
                    if not relative.startswith(paths.attempt_dir + "/"):
                        result.append(relative)
    return sorted(set(result))


def _retained_digests(project: Path, package: Any, paths: Any) -> dict[str, str]:
    result = {
        path: digest_sources(project, [path])
        for path in _authority_paths(project, package, paths)
    }
    executable = _executable_files(project, paths)
    result["executable_context"] = digest_sources(project, executable) if executable else "sha256:" + "0" * 64
    return dict(sorted(result.items()))


def _relative_file_bytes(directory: Path) -> dict[str, bytes]:
    if directory.is_symlink() or not directory.is_dir():
        raise WorkspaceError("delivery rollback tree must be one real directory")
    files: dict[str, bytes] = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise WorkspaceError("delivery rollback tree may not contain symlinks")
        if path.is_file():
            files[path.relative_to(directory).as_posix()] = path.read_bytes()
    return files


def propose_delivery(project_root: str | Path, target: str | None = None, ignored_proposal: str | None = None) -> ToolResult:
    project = Path(project_root).resolve()
    try:
        package = ProjectRepository(project).load()
        feature, paths = _resolve_target(project, package, target)
        complete, incomplete, malformed = _task_state(project, paths.tasks)
        checklist_files, checklist_complete, checklist_incomplete, checklist_malformed = _checklist_state(project, paths.checklists_dir)
        evidence_passed, evidence_missing = _validation_state(project, paths.validation, complete)
        source_digest = _delivery_digest(project, package, paths, ignored_proposal)
        retained_digests = _retained_digests(project, package, paths)
    except (RepositoryError, WorkspaceError, OSError, UnicodeError) as error:
        return ToolResult("deliver", target or ".", "invalid", findings=(_finding("CONCORDE-DELIVER-001", ".concorde/feature.json", str(error), "Select a valid direct feature with one active real .concorde/attempts/<stable-feature-id> directory."),))

    findings: list[Finding] = []
    if incomplete:
        findings.append(_finding("CONCORDE-DELIVER-002", paths.tasks, "Unchecked tasks block delivery: " + ", ".join(incomplete), "Complete or deliberately remove blocking work through task review."))
    if malformed:
        findings.append(_finding("CONCORDE-DELIVER-003", paths.tasks, "Task completion cannot be proven: " + ", ".join(malformed), "Use canonical '- [ ] T###' or '- [X] T###' task items."))
    if checklist_incomplete:
        findings.append(_finding("CONCORDE-DELIVER-009", paths.checklists_dir, "Unchecked checklist items block delivery: " + ", ".join(checklist_incomplete), "Resolve every existing checklist item."))
    if checklist_malformed:
        findings.append(_finding("CONCORDE-DELIVER-010", paths.checklists_dir, "Checklist completion cannot be proven: " + ", ".join(checklist_malformed), "Use canonical checklist markers."))
    if evidence_missing:
        findings.append(_finding("CONCORDE-DELIVER-013", paths.validation, "Passing Attempt Evidence is missing for: " + ", ".join(evidence_missing), "Record one current **Outcome**: passed evidence block for every completed task."))

    reflection_summary = {"entries": 0, "open": 0, "resolved": 0, "dismissed": 0}
    reflections_body = package.auxiliary.get(log_path())
    if reflections_body is not None:
        parsed = parse_reflection_log(reflections_body)
        if parsed.problems:
            findings.append(_finding("CONCORDE-DELIVER-011", paths.reflections, "The project reflection log is malformed: " + "; ".join(problem.message for problem in parsed.problems), "Repair the centralized log and re-propose."))
        reflection_summary = parsed.summary(feature.identifier)
    result = {
        "proposal_version": 9,
        "workspace": paths.protocol_paths(),
        "changes": [{"path": paths.attempt_dir, "action": "delete", "meaning": "Remove the complete temporal attempt; retain every durable and executable authority."}],
        "source_digest": source_digest,
        "task_summary": {"complete": len(complete), "incomplete": len(incomplete), "malformed": len(malformed)},
        "checklist_summary": {"files": checklist_files, "complete": len(checklist_complete), "incomplete": len(checklist_incomplete), "malformed": len(checklist_malformed)},
        "evidence_summary": {"passed": len(evidence_passed), "missing": len(evidence_missing)},
        "proposal_path": f"{paths.attempt_dir}/deliver-proposal.json",
        "retained_digests": retained_digests,
        "reflection_summary": reflection_summary,
    }
    artifacts = [paths.feature_path, paths.module_architecture, paths.tasks, paths.validation]
    if reflections_body is not None:
        artifacts.append(paths.reflections)
    return ToolResult("deliver", feature.identifier, "eligible" if not findings else "invalid", tuple(artifacts), tuple(findings), result)


def _load_proposal(project: Path, proposal_path: str) -> tuple[str, dict[str, Any]]:
    relative = safe_relative_path(proposal_path)
    path = ProjectRepository(project).resolve(relative)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WorkspaceError(f"cannot read delivery proposal: {error}") from error
    if not isinstance(value, dict):
        raise WorkspaceError("delivery proposal must be a JSON object")
    return relative, value


def apply_delivery(project_root: str | Path, proposal_path: str) -> ToolResult:
    project = Path(project_root).resolve()
    try:
        relative_proposal, proposal = _load_proposal(project, proposal_path)
        if "operation" in proposal:
            raise WorkspaceError("legacy delivery proposal operation discriminator is unsupported; use tool")
        unexpected = sorted(set(proposal) - DELIVERY_PROPOSAL_KEYS)
        if unexpected:
            raise WorkspaceError("delivery proposal contains unexpected fields: " + ", ".join(unexpected))
        if proposal.get("proposal_version") != 9 or proposal.get("tool") != "deliver":
            raise WorkspaceError("unsupported delivery proposal; proposal_version 9 with tool deliver is required")
        target = proposal.get("target")
        if not isinstance(target, str) or not target:
            raise WorkspaceError("delivery proposal target is required")
        eligibility = propose_delivery(project, target, relative_proposal)
        if eligibility.status != "eligible":
            return eligibility
        paths = eligibility.result["workspace"]
        if relative_proposal != eligibility.result["proposal_path"]:
            raise WorkspaceError(f"proposal must be stored at {eligibility.result['proposal_path']}")
        if proposal.get("source_digest") != eligibility.result["source_digest"]:
            return ToolResult("deliver", target, "conflict", findings=(_finding("CONCORDE-DELIVER-004", relative_proposal, "Delivery inputs changed after proposal.", "Regenerate the proposal against the current complete attempt."),), result={"workspace": paths, "changes": [], "source_digest": eligibility.result["source_digest"]})
        if proposal.get("remove") != [paths["attempt_dir"]]:
            raise WorkspaceError("proposal removal set must contain exactly the selected feature's stable-ID project-control attempt directory")
        repository = ProjectRepository(project)
        package = repository.load()
        attempt = repository.resolve(paths["attempt_dir"])
        if attempt.is_symlink() or not attempt.is_dir():
            raise WorkspaceError("delivery target must be one real attempt directory")
        tombstone = attempt.with_name(f".{attempt.name}.concorde-remove")
        if tombstone.exists():
            raise WorkspaceError("stale delivery recovery artifact exists")
        removed_artifacts = _attempt_files(project, paths["attempt_dir"])
        retained_before = _retained_digests(project, package, resolve_phase_paths(project, paths["feature_path"]))
    except (RepositoryError, WorkspaceError, OSError, UnicodeError) as error:
        return ToolResult("deliver", ".", "invalid", findings=(_finding("CONCORDE-DELIVER-005", proposal_path, str(error), "Correct and regenerate the cleanup-only proposal before applying it."),))

    backup_complete = False
    moved = False
    with tempfile.TemporaryDirectory(prefix="concorde-delivery-") as temporary:
        backup = Path(temporary) / attempt.name
        try:
            shutil.copytree(attempt, backup)
            backup_complete = True
            attempt.replace(tombstone)
            moved = True
            shutil.rmtree(tombstone)
            current_package = ProjectRepository(project).load()
            current_paths = resolve_phase_paths(project, paths["feature_path"])
            retained_after = _retained_digests(project, current_package, current_paths)
            if retained_after != retained_before:
                raise WorkspaceError("a retained durable or executable authority changed during cleanup")
        except (OSError, WorkspaceError) as error:
            try:
                if moved and tombstone.exists() and not attempt.exists():
                    tombstone.replace(attempt)
                if backup_complete:
                    shutil.copytree(backup, attempt, dirs_exist_ok=True)
                if tombstone.exists():
                    shutil.rmtree(tombstone)
                if backup_complete and _relative_file_bytes(attempt) != _relative_file_bytes(backup):
                    raise WorkspaceError("restored attempt does not match the complete delivery backup")
            except (OSError, WorkspaceError) as rollback_error:
                error = WorkspaceError(f"{error}; rollback also failed: {rollback_error}")
            return ToolResult("deliver", target, "failed", findings=(_finding("CONCORDE-DELIVER-006", paths["feature_path"], f"Attempt cleanup failed: {error}", "Resolve the filesystem failure; the complete attempt was restored when possible."),), result={"workspace": paths, "changes": [], "source_digest": eligibility.result["source_digest"]})

    return ToolResult(
        "deliver",
        target,
        "delivered",
        tuple(_authority_paths(project, ProjectRepository(project).load(), resolve_phase_paths(project, paths["feature_path"]))),
        result={
            "workspace": {**paths, "attempt_state": "absent"},
            "changes": eligibility.result["changes"],
            "source_digest": eligibility.result["source_digest"],
            "removed_artifacts": removed_artifacts,
            "retained_artifacts": sorted(path for path in retained_before if path != "executable_context"),
            "retained_digests": retained_before,
            "reflection_summary": eligibility.result["reflection_summary"],
        },
    )
