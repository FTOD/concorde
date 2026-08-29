"""Feature abstract (abstract.md) shape, structure link, requirement citation, and reading-budget rules."""

from __future__ import annotations

import posixpath
import re
from pathlib import PurePosixPath
from typing import Any

from ..model import Finding, SourceDocument
from ..projection import markdown_section
from .summary import _link_targets, body_words


REQUIRED_ABSTRACT_SECTIONS = ("Purpose", "Functionality", "Structure", "Logic", "Read Next")
ABSTRACT_BUDGET_WORDS = 3000

_FENCE = re.compile(r"^(```|~~~)")
_HREF = re.compile(r"href=\"([^\"]+)\"")
_REQUIREMENT_ID = re.compile(r"\bFR-\d{3}\b")
_DEFINED_REQUIREMENT = re.compile(r"\*\*(FR-\d{3})\*\*")
_TEXT_SKETCH = re.compile(r"^```text\s*$", re.MULTILINE)


def _finding(rule: str, path: str, feature: SourceDocument, message: str, remediation: str, severity: str = "error") -> Finding:
    return Finding(rule, severity, path, message, remediation, subject_id=feature.identifier)


def _h2_headings(body: str) -> list[str]:
    """Return the H2 headings in order, ignoring fenced code blocks."""
    headings: list[str] = []
    fenced = False
    for line in body.splitlines():
        if _FENCE.match(line.strip()):
            fenced = not fenced
            continue
        if not fenced and line.startswith("## "):
            headings.append(line[3:].strip())
    return headings


def _structure_is_linked(structure: str, source_dir: str, feature: SourceDocument, package: Any) -> bool:
    accepted: set[str] = set()
    for declaration in feature.metadata.get("diagrams", []) if isinstance(feature.metadata.get("diagrams"), list) else []:
        if isinstance(declaration, dict) and isinstance(declaration.get("source"), str):
            accepted.add(posixpath.normpath(declaration["source"]))
    accepted.update(posixpath.normpath(path) for path in package.views)
    accepted.update(posixpath.normpath(path) for path in package.diagrams)
    if accepted & _link_targets(structure, source_dir):
        return True
    for match in _HREF.finditer(structure):
        target = match.group(1)
        if target.startswith("/architecture/") and target.endswith(".html"):
            return True
    return bool(_TEXT_SKETCH.search(structure))


def validate_abstracts(package: Any) -> list[Finding]:
    findings: list[Finding] = []
    for feature in package.documents("feature"):
        source_dir = PurePosixPath(feature.path).parent.as_posix()
        path = f"{source_dir}/abstract.md"
        body = package.auxiliary.get(path)
        if body is None:
            continue  # absence is a layout finding (CONCORDE-LAYOUT-009)
        headings = _h2_headings(body)
        sections = {heading: markdown_section(body, heading) for heading in REQUIRED_ABSTRACT_SECTIONS}
        if headings != list(REQUIRED_ABSTRACT_SECTIONS) or any(not sections[heading].strip() for heading in REQUIRED_ABSTRACT_SECTIONS):
            findings.append(
                _finding(
                    "CONCORDE-ABSTRACT-001",
                    path,
                    feature,
                    "The feature abstract must consist of exactly the non-empty sections Purpose, Functionality, Structure, Logic, and Read Next, in that order"
                    + (f"; found: {', '.join(headings) or 'no H2 sections'}." if headings != list(REQUIRED_ABSTRACT_SECTIONS) else "; one of them is empty."),
                    "Rewrite abstract.md with the five required H2 sections in order and nothing else at H2 level; keep it self-contained and within the reading budget.",
                )
            )
        structure = sections["Structure"]
        if structure.strip() and not _structure_is_linked(structure, source_dir, feature, package):
            findings.append(
                _finding(
                    "CONCORDE-ABSTRACT-002",
                    path,
                    feature,
                    "The Structure section links no maintained diagram, level view, or delivered architecture view and contains no fenced text sketch.",
                    "Link the feature's declared core diagram (or the parent's core view or the level view), or add a ```text sketch of the participating parts.",
                )
            )
        logic = sections["Logic"]
        cited = set(_REQUIREMENT_ID.findall(logic))
        defined = set(_DEFINED_REQUIREMENT.findall(feature.body))
        unknown = sorted(cited - defined)
        if unknown:
            findings.append(
                _finding(
                    "CONCORDE-ABSTRACT-003",
                    path,
                    feature,
                    "The Logic section cites requirement IDs that the adjacent design.md does not define: " + ", ".join(unknown) + ".",
                    "Cite only **FR-NNN** identifiers defined in design.md, or add the missing requirement to design.md through design review.",
                )
            )
        elif defined and logic.strip() and not cited:
            findings.append(
                _finding(
                    "CONCORDE-ABSTRACT-003",
                    path,
                    feature,
                    "The Logic section states rules without citing any FR-NNN requirement defined in the adjacent design.md.",
                    "End each rule in Logic with the design.md requirement IDs it summarizes, for example (FR-003, FR-007).",
                )
            )
        words = body_words(body)
        if words > ABSTRACT_BUDGET_WORDS:
            findings.append(
                _finding(
                    "CONCORDE-ABSTRACT-004",
                    path,
                    feature,
                    f"Feature abstract body has {words} words, over the {ABSTRACT_BUDGET_WORDS}-word reading budget (about 15 minutes).",
                    "Move detail into design.md or implementation.md; keep the abstract to purpose, functionality, basic structure, and logic.",
                    severity="warning",
                )
            )
    return findings
