"""A report-only host service bound to one admitted worker invocation.

No file write grant is added to the worker. The source identity and scope are captured by trusted
host code before launch; worker arguments cannot select a project root or forge provenance.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock

from ..spec.repository import SpecError
from ..spec.typed_data import check_schema, decode
from ..spec.issue_shapes import PROVENANCE, REPORT
from .store import read_issue, report_issue, validate_report


@dataclass
class IssueReporter:
    root: Path
    source: dict
    admitted_owners: frozenset[str]
    evidence_paths: frozenset[str]
    selected_issues: frozenset[str] = frozenset()
    admitted_receipts: tuple[dict, ...] = ()
    receipts: list[dict] = field(default_factory=list, init=False)
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def __post_init__(self):
        check_schema(self.source, PROVENANCE)
        if self.source["target_id"] not in self.admitted_owners:
            raise SpecError("reporting target is outside the admitted context", "permission_denied")
        self.source = copy.deepcopy(self.source)
        self.root = self.root.resolve()

    @property
    def schema(self) -> dict:
        return copy.deepcopy(REPORT)

    def __call__(self, report: dict) -> dict:
        """Return an immutable receipt and the current revision for an admitted follow-up."""
        validate_report(report)
        if report["owner_target_id"] is not None and report["owner_target_id"] not in self.admitted_owners:
            raise SpecError("issue owner is outside the admitted context; report unknown ownership as null",
                            "permission_denied")
        if any(item["path"] not in self.evidence_paths for item in report["evidence"]):
            raise SpecError("issue evidence is outside the admitted file scope", "permission_denied")
        with self._lock:
            selected = self.selected_issues | {receipt["issue_id"] for receipt in self.receipts}
            if "issue_id" in report and report["issue_id"] not in selected:
                raise SpecError("issue was not admitted for this invocation", "permission_denied")
            receipt = report_issue(self.root, report, self.source)
            if receipt not in self.receipts:
                self.receipts.append(copy.deepcopy(receipt))
            _, revision = read_issue(self.root, receipt["issue_id"])
            return {"receipt": receipt, "revision": revision}


def reporter_for_invocation(root: Path, invocation, *, target_id: str | None, change_id: str | None):
    """Derive a service from the frozen context, not a worker-supplied path/target claim."""
    from ..harness.change_worktree import git

    value = decode(invocation.context_json)["data"]
    snapshot = value.get("snapshot", {}).get("data", value)
    resolutions = ([snapshot["spec_resolution"]] if "spec_resolution" in snapshot else
                   [target["spec_resolution"] for target in snapshot["targets"]])
    owners = {owner for resolution in resolutions for owner in
              [resolution["module_id"], *resolution["registration"]["uses"],
               *(source["owner"] for source in resolution["sources"])]}
    reporting_target = target_id or resolutions[0]["module_id"]
    paths = {source["path"] for resolution in resolutions for source in resolution["sources"]}
    paths.update(item["path"] for item in snapshot.get("implementation_artifacts", []))
    # Removed files present in the host's scoped review patch remain valid evidence locations.
    paths.update(item["path"] for item in value.get("review", {}).get("data", {}).get("changes", []))
    head = git(root, "rev-parse", "HEAD", check=False)
    source = {"invocation_id": invocation.invocation_id, "agent": invocation.agent,
        "capability": invocation.capability, "phase": invocation.stage, "target_id": reporting_target,
        "context_id": snapshot["context_id"], "change_id": change_id,
        "head": head.stdout.strip() if head.returncode == 0 else None}
    admitted = tuple(item["receipt"] for value in snapshot.get("stage_inputs", [])
                     if value["type_id"] == "concorde-issue-context" for item in value["data"]["observations"])
    selected = {item["issue_id"] for item in admitted}
    selected.update(value["data"]["issue_id"] for value in snapshot.get("stage_inputs", [])
                    if value["type_id"] == "concorde-issue-selection")
    return IssueReporter(root, source, frozenset(owners), frozenset(paths), frozenset(selected), admitted)
