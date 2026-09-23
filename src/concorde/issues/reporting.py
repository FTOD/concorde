"""The reporting service: a report-only Host service bound to one reporter.

No file write grant is added to the reporter. Its caller supplies the provenance and limits
before the reporter starts; reporter arguments cannot select a project root or forge provenance.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock

from .shapes import PROVENANCE, REPORT
from ..spec.repository import SpecError
from ..spec.typed_data import check_schema
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
            raise SpecError(
                "reporting target is outside the admitted context", "permission_denied"
            )
        self.source = copy.deepcopy(self.source)
        self.root = self.root.resolve()

    @property
    def schema(self) -> dict:
        return copy.deepcopy(REPORT)

    def __call__(self, report: dict) -> dict:
        """Return an immutable receipt and the current revision for an admitted follow-up."""
        validate_report(report)
        if (
            report["owner_target_id"] is not None
            and report["owner_target_id"] not in self.admitted_owners
        ):
            raise SpecError(
                "issue owner is outside the admitted context; report unknown ownership as null",
                "permission_denied",
            )
        if any(item["path"] not in self.evidence_paths for item in report["evidence"]):
            raise SpecError(
                "issue evidence is outside the admitted file scope", "permission_denied"
            )
        with self._lock:
            selected = self.selected_issues | {
                receipt["issue_id"] for receipt in self.receipts
            }
            if "issue_id" in report and report["issue_id"] not in selected:
                raise SpecError(
                    "issue was not admitted for this invocation", "permission_denied"
                )
            receipt = report_issue(self.root, report, self.source)
            if receipt not in self.receipts:
                self.receipts.append(copy.deepcopy(receipt))
            _, revision = read_issue(self.root, receipt["issue_id"])
            return {"receipt": receipt, "revision": revision}
