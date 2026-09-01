"""Invocation-authorized delivery of a completed attempt into implementation.md,
optionally amending the providing module's design reference in the same atomic apply."""

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
from .reflections import log_path, parse_reflection_log
from .repository import ProjectRepository, RepositoryError, safe_relative_path


TASK_LINE = re.compile(r"^\s*-\s+\[([ xX])\]\s+(T\d{3,})\b")
TASK_REFERENCE = re.compile(r"\bT\d{3,}\b")
CHECKLIST_LINE = re.compile(r"^\s*-\s+\[([ xX])\](?:\s+.*)?$")
CHECKBOX_LIKE_LINE = re.compile(r"^\s*-\s+\[[^\]]*\]")
REFLECTION_IDENTIFIER = re.compile(r"\bR-\d{3,}\b")
PLACEHOLDER_MARKER = "No implementation realization has been accepted yet."
REQUIRED_IMPLEMENTATION_HEADINGS = (
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


def _attempt_files(project: Path, attempt_dir: str, ignored: str | None = None) -> list[str]:
    attempt = project / attempt_dir
    if not attempt.is_dir() or attempt.is_symlink():
        raise WorkspaceError("delivery requires one real attempt/ directory")
    files: list[str] = []
    for path in sorted(attempt.rglob("*")):
        if path.is_symlink():
            raise WorkspaceError(f"delivery input may not be a symlink: {path.relative_to(project).as_posix()}")
        if path.is_file():
            relative = path.relative_to(project).as_posix()
            if relative != ignored:
                files.append(relative)
    return files


def _delivery_digest(project: Path, package: Any, paths: Any, ignored: str | None = None) -> str:
    sources = [item.path for item in package.sources]
    sources.extend(package.views)
    sources.extend(package.diagrams)
    for durable in (paths.feature_abstract, paths.feature_implementation, paths.module_design, paths.reflections):
        candidate = project / durable
        if candidate.is_file() and not candidate.is_symlink():
            sources.append(durable)
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


def _checklist_state(
    project: Path,
    checklists_dir: str,
) -> tuple[int, list[str], list[str], list[str]]:
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


def propose_delivery(
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
        source_digest = _delivery_digest(project, package, paths, ignored_proposal)
    except (RepositoryError, WorkspaceError, OSError, UnicodeError) as error:
        return OperationResult(
            "deliver",
            target or ".",
            "invalid",
            findings=(_finding("CONCORDE-DELIVER-001", ".specify/feature.json", str(error), "Select a valid feature with real durable abstract.md, design.md, and implementation.md files and an active attempt."),),
        )
    findings: list[Finding] = []
    if incomplete:
        findings.append(_finding("CONCORDE-DELIVER-002", paths.tasks, "Unchecked tasks block delivery: " + ", ".join(incomplete), "Complete or deliberately remove the blocking work through the normal task workflow."))
    if malformed:
        findings.append(_finding("CONCORDE-DELIVER-003", paths.tasks, "Task completion cannot be proven: " + ", ".join(malformed), "Use canonical '- [ ] T###' or '- [X] T###' task items and complete every task."))
    if checklist_incomplete:
        findings.append(_finding("CONCORDE-DELIVER-009", paths.checklists_dir, "Unchecked checklist items block delivery: " + ", ".join(checklist_incomplete), "Resolve every existing checklist item through the normal specification and implementation workflow."))
    if checklist_malformed:
        findings.append(_finding("CONCORDE-DELIVER-010", paths.checklists_dir, "Checklist completion cannot be proven: " + ", ".join(checklist_malformed), "Use canonical '- [ ]' or '- [X]' checklist markers and resolve every item."))
    reflection_summary = {"entries": 0, "open": 0, "resolved": 0, "dismissed": 0}
    reflections_body = package.auxiliary.get(log_path(package.specification_root))
    if reflections_body is not None:
        parsed = parse_reflection_log(reflections_body)
        if parsed.problems:
            findings.append(_finding("CONCORDE-DELIVER-011", paths.reflections, "The project reflection log is malformed: " + "; ".join(problem.message for problem in parsed.problems), "Repair the log per the reflection-log contract (speckit.concorde.validate reports each CONCORDE-REFLECT finding) and re-propose."))
        reflection_summary = parsed.summary(feature.identifier)
    changes = [
        {"path": paths.feature_implementation, "action": "update", "meaning": "Replace the feature's durable implementation with the invocation-authorized candidate."},
        {"path": paths.attempt_dir, "action": "delete", "meaning": "Remove the complete temporal attempt after the implementation is promoted."},
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
        "proposal_path": f"{paths.attempt_dir}/deliver-proposal.json",
        "reflection_summary": reflection_summary,
    }
    artifacts = [paths.feature_design, paths.feature_implementation, paths.tasks]
    if reflections_body is not None:
        artifacts.append(paths.reflections)
    if (project / paths.feature_abstract).is_file():
        artifacts.append(paths.feature_abstract)
    if (project / paths.module_design).is_file():
        artifacts.append(paths.module_design)
    return OperationResult(
        "deliver",
        feature.identifier,
        "eligible" if not findings else "invalid",
        tuple(artifacts),
        tuple(findings),
        result,
    )


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


def _sha256_text(content: str | None) -> str | None:
    if content is None:
        return None
    return "sha256:" + hashlib.sha256(content.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def _validate_implementation(content: Any) -> str:
    if not isinstance(content, str) or not content.strip():
        raise WorkspaceError("candidate implementation.md content must be non-empty UTF-8 Markdown")
    missing = [heading for heading in REQUIRED_IMPLEMENTATION_HEADINGS if heading not in content]
    if missing:
        raise WorkspaceError("candidate implementation.md is missing required sections: " + ", ".join(missing))
    if "[NEEDS CLARIFICATION" in content or "[TODO" in content or PLACEHOLDER_MARKER in content:
        raise WorkspaceError("candidate implementation.md still contains unresolved or placeholder content")
    return content.rstrip() + "\n"


def _validate_module_design(content: Any) -> str:
    if not isinstance(content, str) or not content.strip():
        raise WorkspaceError("module design.md amendment must be non-empty UTF-8 Markdown")
    lines = content.splitlines()
    if not any(line.startswith("# ") for line in lines) or not any(line.startswith("## ") for line in lines):
        raise WorkspaceError("module design.md amendment must contain an H1 title and at least one H2 section")
    if "[NEEDS CLARIFICATION" in content or "[TODO" in content:
        raise WorkspaceError("module design.md amendment still contains unresolved proposal placeholders")
    return content.rstrip() + "\n"


def _amendment_target(paths: dict[str, Any], amendment: Any) -> str:
    if not isinstance(amendment, dict):
        raise WorkspaceError("module_design must be an object with path and content")
    path = amendment.get("path")
    if not isinstance(path, str) or not path:
        raise WorkspaceError("module_design.path is required")
    if path.endswith("/module.md") or path == "module.md":
        raise WorkspaceError("delivery may not edit a module summary (module.md); amend the module design.md instead")
    if path != paths["module_design"]:
        if path.startswith(paths["feature_directory"] + "/"):
            raise WorkspaceError("module_design must name the providing module's design.md, not a path inside the feature root")
        raise WorkspaceError(f"module_design.path must be the providing module's design reference {paths['module_design']}")
    return path


def _persisted_reflection_identifiers(*contents: str | None) -> list[str]:
    """Reflection identifiers copied into delivery-managed durable documents."""
    return sorted({match.group(0) for content in contents if content for match in REFLECTION_IDENTIFIER.finditer(content)})


def apply_delivery(project_root: str | Path, proposal_path: str) -> OperationResult:
    project = Path(project_root).resolve()
    try:
        relative_proposal, proposal = _load_proposal(project, proposal_path)
        if proposal.get("proposal_version") != 7 or proposal.get("operation") != "deliver":
            raise WorkspaceError("unsupported delivery proposal; proposal_version 7 with operation deliver is required")
        if "design" in proposal:
            raise WorkspaceError("proposal v7 names the durable implementation under 'implementation'; 'design' is not accepted")
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
            return OperationResult(
                "deliver",
                target,
                "conflict",
                findings=(_finding("CONCORDE-DELIVER-004", relative_proposal, "Delivery inputs changed after proposal.", "Regenerate the proposal against the current completed attempt."),),
                result={"workspace": paths, "changes": [], "source_digest": eligibility.result["source_digest"]},
            )
        realization = proposal.get("implementation")
        if not isinstance(realization, dict):
            raise WorkspaceError("proposal implementation must be an object with path and content")
        realization_path = realization.get("path")
        if realization_path != paths["feature_implementation"]:
            if isinstance(realization_path, str) and realization_path.rsplit("/", 1)[-1] in {"abstract.md", "design.md", "module.md", "spec.md", "tldr.md"}:
                raise WorkspaceError("delivery writes only feature implementation.md; it never writes abstract.md, design.md, module.md, spec.md, or tldr.md")
            raise WorkspaceError("proposal implementation path must be the selected feature's root implementation.md")
        if proposal.get("remove") != [paths["attempt_dir"]]:
            raise WorkspaceError("proposal removal set must contain exactly the selected feature's attempt/ directory")
        content = _validate_implementation(realization.get("content"))
        repository = ProjectRepository(project)
        implementation_path = repository.resolve(paths["feature_implementation"])
        attempt_path = repository.resolve(paths["attempt_dir"])
        amendment = proposal.get("module_design")
        module_design_path: Path | None = None
        module_design_content: str | None = None
        if amendment is not None:
            module_design_path = repository.resolve(_amendment_target(paths, amendment))
            module_design_content = _validate_module_design(amendment.get("content"))
        persisted_reflections = _persisted_reflection_identifiers(content, module_design_content)
        if persisted_reflections:
            source = paths["feature_implementation"] if REFLECTION_IDENTIFIER.search(content) else paths["module_design"]
            return OperationResult(
                "deliver",
                target,
                "invalid",
                findings=(_finding("CONCORDE-DELIVER-012", source, "Delivery-managed durable documents must not persist reflection identifiers: " + ", ".join(persisted_reflections), "Keep reflection entries, identifiers, statuses, notes, and occurrences only in the project reflections.md; describe independently true implementation facts without reflection identity."),),
                result={"workspace": paths, "changes": [], "source_digest": eligibility.result["source_digest"], "reflection_summary": eligibility.result["reflection_summary"]},
            )
        if implementation_path.is_symlink() or attempt_path.is_symlink() or (module_design_path is not None and module_design_path.is_symlink()):
            raise WorkspaceError("delivery targets may not be symlinks")
        old_content = implementation_path.read_text(encoding="utf-8") if implementation_path.is_file() else None
        old_module_design = (
            module_design_path.read_text(encoding="utf-8")
            if module_design_path is not None and module_design_path.is_file()
            else None
        )
        removed_artifacts = _attempt_files(project, paths["attempt_dir"])
    except (RepositoryError, WorkspaceError, OSError, UnicodeError) as error:
        return OperationResult(
            "deliver",
            ".",
            "invalid",
            findings=(_finding("CONCORDE-DELIVER-005", proposal_path, str(error), "Correct and regenerate the delivery proposal before applying it."),),
        )

    # Ordered file set promoted atomically with the attempt removal: all succeed or all are restored.
    updates: list[tuple[Path, str]] = [(implementation_path, content)]
    if module_design_path is not None and module_design_content is not None:
        updates.append((module_design_path, module_design_content))
    stages = [(target_path, target_path.with_name(f".{target_path.name}.concorde-stage"), target_path.with_name(f".{target_path.name}.concorde-backup")) for target_path, _ in updates]
    attempt_backup = attempt_path.with_name(".attempt.concorde-backup")
    moved_attempt = False
    try:
        for _, staged, backup in stages:
            if staged.exists() or backup.exists():
                raise WorkspaceError("stale delivery stage or recovery artifact exists")
        if attempt_backup.exists():
            raise WorkspaceError("stale delivery stage or recovery artifact exists")
        for (target_path, new_content), (_, staged, _) in zip(updates, stages):
            staged.write_text(new_content, encoding="utf-8", newline="\n")
        for target_path, _, backup in stages:
            if target_path.exists():
                target_path.replace(backup)
        attempt_path.replace(attempt_backup)
        moved_attempt = True
        for target_path, staged, _ in stages:
            staged.replace(target_path)
    except (OSError, WorkspaceError) as error:
        for target_path, staged, backup in stages:
            staged.unlink(missing_ok=True)
        if moved_attempt and attempt_backup.exists() and not attempt_path.exists():
            attempt_backup.replace(attempt_path)
        for target_path, _, backup in stages:
            if backup.exists():
                target_path.unlink(missing_ok=True)
                backup.replace(target_path)
        return OperationResult(
            "deliver",
            target,
            "failed",
            findings=(_finding("CONCORDE-DELIVER-006", paths["feature_directory"], f"Delivery commit failed: {error}", "Resolve the filesystem failure; the prior feature implementation.md, module design.md, and attempt were restored."),),
            result={"workspace": paths, "changes": [], "source_digest": eligibility.result["source_digest"]},
        )

    cleanup_findings: list[Finding] = []
    try:
        shutil.rmtree(attempt_backup)
        for _, _, backup in stages:
            backup.unlink(missing_ok=True)
    except OSError as error:
        cleanup_findings.append(Finding("CONCORDE-DELIVER-007", "warning", paths["feature_directory"], f"Delivery committed but recovery cleanup is pending: {error}", "Remove the hidden Concorde backup after confirming the durable realization and version-control recovery."))
    retained_artifacts = [paths["feature_abstract"], paths["feature_design"], paths["module_summary"]]
    if (project / paths["reflections"]).is_file():
        retained_artifacts.append(paths["reflections"])
    if module_design_path is None and (project / paths["module_design"]).is_file():
        retained_artifacts.append(paths["module_design"])
    parent_context = paths.get("parent_context")
    if isinstance(parent_context, dict):
        retained_artifacts.extend(
            item for item in (parent_context.get("feature_abstract"), parent_context.get("feature_design"), parent_context.get("feature_implementation"))
            if isinstance(item, str)
        )
    for sibling in paths.get("siblings", []):
        sibling_root = sibling.get("feature_directory") if isinstance(sibling, dict) else None
        if isinstance(sibling_root, str):
            for name in ("abstract.md", "design.md", "implementation.md"):
                candidate = f"{sibling_root}/{name}"
                if (project / candidate).is_file():
                    retained_artifacts.append(candidate)
    changes = list(eligibility.result["changes"])
    result_artifacts = [paths["feature_implementation"]]
    if module_design_path is not None:
        changes.insert(1, {"path": paths["module_design"], "action": "update", "meaning": "Amend the module design reference with invocation-authorized implementation detail and rationale."})
        result_artifacts.append(paths["module_design"])
    return OperationResult(
        "deliver",
        target,
        "delivered",
        tuple(result_artifacts),
        tuple(cleanup_findings),
        {
            "workspace": {**paths, "attempt_state": "absent"},
            "changes": changes,
            "source_digest": eligibility.result["source_digest"],
            "implementation_digest_before": _sha256_text(old_content),
            "implementation_digest_after": _sha256_text(content),
            "module_design_digest_before": _sha256_text(old_module_design) if module_design_path is not None else None,
            "module_design_digest_after": _sha256_text(module_design_content) if module_design_path is not None else None,
            "removed_artifacts": removed_artifacts,
            "retained_artifacts": sorted(set(retained_artifacts)),
            "reflection_summary": eligibility.result["reflection_summary"],
        },
    )
