"""Review-first compaction of a completed feature attempt into durable design."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

from .diagnostics import digest_sources
from .feature_workspace import (
    WorkspaceError,
    _read_persisted_selection,
    _resolve_feature,
    resolve_phase_paths,
)
from .model import Finding, OperationResult, SourceDocument
from .repository import ProjectRepository, RepositoryError, safe_relative_path


TASK_LINE = re.compile(r"^\s*-\s+\[([ xX])\]\s+(T\d{3,})\b")
TASK_REFERENCE = re.compile(r"\bT\d{3,}\b")
CHECKLIST_LINE = re.compile(r"^\s*-\s+\[([ xX])\](?:\s+.*)?$")
CHECKBOX_LIKE_LINE = re.compile(r"^\s*-\s+\[[^\]]*\]")
REQUIRED_DESIGN_HEADINGS = (
    "## Realization Overview",
    "## Module and Feature Collaboration",
    "## Scenario Realization",
    "## Durable Implementation Decisions",
    "## Traceability and Evidence",
    "## Known Limitations",
)


def _finding(rule: str, source: str, message: str, remediation: str) -> Finding:
    return Finding(rule, "error", source, message, remediation)


def _resolve_target(project: Path, package: Any, target: str | None) -> tuple[SourceDocument, Any]:
    resolved_target = target
    if not resolved_target:
        resolved_target = _read_persisted_selection(project)
    feature = _resolve_feature(package, resolved_target)
    if feature is None:
        raise WorkspaceError(f"feature target '{resolved_target}' does not resolve exactly once")
    paths = resolve_phase_paths(project, Path(feature.path).parent.as_posix())
    return feature, paths


def _attempt_files(project: Path, implementation_dir: str, ignored: str | None = None) -> list[str]:
    implementation = project / implementation_dir
    if not implementation.is_dir() or implementation.is_symlink():
        raise WorkspaceError("hardening requires one real implementation/ directory")
    files: list[str] = []
    for path in sorted(implementation.rglob("*")):
        if path.is_symlink():
            raise WorkspaceError(f"hardening input may not be a symlink: {path.relative_to(project).as_posix()}")
        if path.is_file():
            relative = path.relative_to(project).as_posix()
            if relative != ignored:
                files.append(relative)
    return files


def _hardening_digest(project: Path, package: Any, paths: Any, ignored: str | None = None) -> str:
    sources = [item.path for item in package.sources]
    sources.extend(package.views)
    sources.extend(package.diagrams)
    design = project / paths.feature_design
    if design.is_file() and not design.is_symlink():
        sources.append(paths.feature_design)
    sources.extend(_attempt_files(project, paths.implementation_dir, ignored))
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


def _checklist_state(
    project: Path,
    checklists_dir: str,
) -> tuple[int, list[str], list[str], list[str]]:
    directory = project / checklists_dir
    if directory.is_symlink():
        raise WorkspaceError(f"hardening checklist directory may not be a symlink: {checklists_dir}")
    if not directory.exists():
        return 0, [], [], []
    if not directory.is_dir():
        raise WorkspaceError(f"hardening checklist path is not a directory: {checklists_dir}")

    complete: list[str] = []
    incomplete: list[str] = []
    malformed: list[str] = []
    files = 0
    for path in sorted(directory.glob("*.md")):
        relative = path.relative_to(project).as_posix()
        if path.is_symlink():
            raise WorkspaceError(f"hardening checklist input may not be a symlink: {relative}")
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


def propose_hardening(
    project_root: str | Path,
    target: str | None = None,
    ignored_proposal: str | None = None,
) -> OperationResult:
    project = Path(project_root).resolve()
    try:
        package = ProjectRepository(project).load()
        feature, paths = _resolve_target(project, package, target)
        complete, incomplete, malformed = _task_state(project, paths.tasks)
        checklist_files, checklist_complete, checklist_incomplete, checklist_malformed = _checklist_state(
            project,
            paths.checklists_dir,
        )
        source_digest = _hardening_digest(project, package, paths, ignored_proposal)
    except (RepositoryError, WorkspaceError, OSError, UnicodeError) as error:
        return OperationResult(
            "feature.harden",
            target or ".",
            "invalid",
            findings=(_finding("CONCORDE-HARDEN-001", ".specify/feature.json", str(error), "Select a valid feature with a real durable design and implementation attempt."),),
        )
    findings: list[Finding] = []
    if incomplete:
        findings.append(_finding("CONCORDE-HARDEN-002", paths.tasks, "Unchecked tasks block hardening: " + ", ".join(incomplete), "Complete or deliberately remove the blocking work through the normal task workflow."))
    if malformed:
        findings.append(_finding("CONCORDE-HARDEN-003", paths.tasks, "Task completion cannot be proven: " + ", ".join(malformed), "Use canonical '- [ ] T###' or '- [X] T###' task items and complete every task."))
    if checklist_incomplete:
        findings.append(_finding("CONCORDE-HARDEN-009", paths.checklists_dir, "Unchecked checklist items block hardening: " + ", ".join(checklist_incomplete), "Resolve every existing checklist item through the normal specification and implementation workflow."))
    if checklist_malformed:
        findings.append(_finding("CONCORDE-HARDEN-010", paths.checklists_dir, "Checklist completion cannot be proven: " + ", ".join(checklist_malformed), "Use canonical '- [ ]' or '- [X]' checklist markers and resolve every item."))
    changes = [
        {"path": paths.feature_design, "action": "update", "meaning": "Replace the durable design with the reviewed accepted realization."},
        {"path": paths.implementation_dir, "action": "delete", "meaning": "Remove the complete temporal implementation attempt after design promotion."},
    ]
    result = {
        "workspace": paths.protocol_paths(),
        "changes": changes,
        "source_digest": source_digest,
        "task_summary": {"complete": len(complete), "incomplete": len(incomplete), "malformed": len(malformed)},
        "checklist_summary": {
            "files": checklist_files,
            "complete": len(checklist_complete),
            "incomplete": len(checklist_incomplete),
            "malformed": len(checklist_malformed),
        },
        "proposal_path": f"{paths.implementation_dir}/harden-proposal.json",
    }
    return OperationResult(
        "feature.harden",
        feature.identifier,
        "eligible" if not findings else "invalid",
        (paths.feature_spec, paths.feature_design, paths.tasks),
        tuple(findings),
        result,
    )


def _load_proposal(project: Path, proposal_path: str) -> tuple[str, dict[str, Any]]:
    relative = safe_relative_path(proposal_path)
    path = ProjectRepository(project).resolve(relative)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WorkspaceError(f"cannot read hardening proposal: {error}") from error
    if not isinstance(value, dict):
        raise WorkspaceError("hardening proposal must be a JSON object")
    return relative, value


def _sha256_text(content: str | None) -> str | None:
    if content is None:
        return None
    return "sha256:" + hashlib.sha256(content.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def _validate_design(content: Any) -> str:
    if not isinstance(content, str) or not content.strip():
        raise WorkspaceError("candidate design content must be non-empty UTF-8 Markdown")
    missing = [heading for heading in REQUIRED_DESIGN_HEADINGS if heading not in content]
    if missing:
        raise WorkspaceError("candidate design is missing required sections: " + ", ".join(missing))
    if "[NEEDS CLARIFICATION" in content or "[TODO" in content:
        raise WorkspaceError("candidate design still contains unresolved proposal placeholders")
    return content.rstrip() + "\n"


def apply_hardening(project_root: str | Path, proposal_path: str) -> OperationResult:
    project = Path(project_root).resolve()
    try:
        relative_proposal, proposal = _load_proposal(project, proposal_path)
        if proposal.get("proposal_version") != 1 or proposal.get("operation") != "feature.harden":
            raise WorkspaceError("unsupported hardening proposal")
        target = proposal.get("target")
        if not isinstance(target, str) or not target:
            raise WorkspaceError("hardening proposal target is required")
        eligibility = propose_hardening(project, target, relative_proposal)
        if eligibility.status != "eligible":
            return eligibility
        paths = eligibility.result["workspace"]
        if relative_proposal != eligibility.result["proposal_path"]:
            raise WorkspaceError(f"proposal must be stored at {eligibility.result['proposal_path']}")
        if proposal.get("source_digest") != eligibility.result["source_digest"]:
            return OperationResult(
                "feature.harden",
                target,
                "conflict",
                findings=(_finding("CONCORDE-HARDEN-004", relative_proposal, "Hardening inputs changed after proposal.", "Regenerate and review a proposal against the current completed attempt."),),
                result={"workspace": paths, "changes": [], "source_digest": eligibility.result["source_digest"]},
            )
        design = proposal.get("design")
        if not isinstance(design, dict) or design.get("path") != paths["feature_design"]:
            raise WorkspaceError("proposal design path must be the selected feature's root design.md")
        if proposal.get("remove") != [paths["implementation_dir"]]:
            raise WorkspaceError("proposal removal set must contain exactly the selected feature's implementation/ directory")
        content = _validate_design(design.get("content"))
        design_path = ProjectRepository(project).resolve(paths["feature_design"])
        implementation_path = ProjectRepository(project).resolve(paths["implementation_dir"])
        if design_path.is_symlink() or implementation_path.is_symlink():
            raise WorkspaceError("hardening targets may not be symlinks")
        old_content = design_path.read_text(encoding="utf-8") if design_path.is_file() else None
        removed_artifacts = _attempt_files(project, paths["implementation_dir"])
    except (RepositoryError, WorkspaceError, OSError, UnicodeError) as error:
        return OperationResult(
            "feature.harden",
            ".",
            "invalid",
            findings=(_finding("CONCORDE-HARDEN-005", proposal_path, str(error), "Correct and re-review the hardening proposal before applying it."),),
        )

    staged_design = design_path.with_name(".design.md.concorde-stage")
    design_backup = design_path.with_name(".design.md.concorde-backup")
    attempt_backup = implementation_path.with_name(".implementation.concorde-backup")
    try:
        if staged_design.exists() or design_backup.exists() or attempt_backup.exists():
            raise WorkspaceError("stale hardening stage or recovery artifact exists")
        staged_design.write_text(content, encoding="utf-8", newline="\n")
        if design_path.exists():
            design_path.replace(design_backup)
        implementation_path.replace(attempt_backup)
        staged_design.replace(design_path)
    except (OSError, WorkspaceError) as error:
        staged_design.unlink(missing_ok=True)
        if attempt_backup.exists() and not implementation_path.exists():
            attempt_backup.replace(implementation_path)
        if design_backup.exists():
            design_path.unlink(missing_ok=True)
            design_backup.replace(design_path)
        return OperationResult(
            "feature.harden",
            target,
            "failed",
            findings=(_finding("CONCORDE-HARDEN-006", paths["feature_directory"], f"Hardening commit failed: {error}", "Resolve the filesystem failure; the prior design and attempt were restored."),),
            result={"workspace": paths, "changes": [], "source_digest": eligibility.result["source_digest"]},
        )

    cleanup_findings: list[Finding] = []
    try:
        shutil.rmtree(attempt_backup)
        design_backup.unlink(missing_ok=True)
    except OSError as error:
        cleanup_findings.append(Finding("CONCORDE-HARDEN-007", "warning", paths["feature_directory"], f"Hardening committed but recovery cleanup is pending: {error}", "Remove the hidden Concorde backup after confirming the durable design and version-control recovery."))
    retained_artifacts = [paths["feature_spec"], paths["feature_design"]]
    parent_context = paths.get("parent_context")
    if isinstance(parent_context, dict):
        retained_artifacts.extend(
            item for item in (parent_context.get("feature_spec"), parent_context.get("feature_design"))
            if isinstance(item, str)
        )
    for sibling in paths.get("siblings", []):
        sibling_root = sibling.get("feature_directory") if isinstance(sibling, dict) else None
        if isinstance(sibling_root, str):
            for name in ("spec.md", "design.md"):
                candidate = f"{sibling_root}/{name}"
                if (project / candidate).is_file():
                    retained_artifacts.append(candidate)
    return OperationResult(
        "feature.harden",
        target,
        "hardened",
        (paths["feature_design"],),
        tuple(cleanup_findings),
        {
            "workspace": {**paths, "implementation_state": "absent"},
            "changes": eligibility.result["changes"],
            "source_digest": eligibility.result["source_digest"],
            "design_digest_before": _sha256_text(old_content),
            "design_digest_after": _sha256_text(content),
            "removed_artifacts": removed_artifacts,
            "retained_artifacts": sorted(set(retained_artifacts)),
        },
    )
