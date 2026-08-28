"""Module summary (module.md) shape, structure link, inventory, reachability, and reading-budget rules."""

from __future__ import annotations

import posixpath
import re
from pathlib import PurePosixPath
from typing import Any

from ..model import Finding, SourceDocument
from ..projection import markdown_section


REQUIRED_SUMMARY_SECTIONS = (
    "Responsibility",
    "Boundary",
    "Structure",
    "Features",
    "Contracts",
    "Submodules",
    "Representative Scenario",
    "Design Rationale",
)
INVENTORY_SECTIONS = ("Features", "Contracts", "Submodules")
READING_BUDGET_WORDS = 4000
EMPTY_INVENTORY = "None."

_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_TABLE_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
_FENCE = re.compile(r"^(```|~~~)")


def _finding(rule: str, source: SourceDocument, message: str, remediation: str, severity: str = "error") -> Finding:
    return Finding(rule, severity, source.path, message, remediation, subject_id=source.identifier)


def _link_targets(text: str, source_dir: str) -> set[str]:
    """Resolve every Markdown link target in `text` to a project-relative POSIX path."""
    targets: set[str] = set()
    for match in _LINK.finditer(text):
        target = match.group(1).split("#", 1)[0]
        if not target or "://" in target or target.startswith(("mailto:", "/")):
            continue
        if target.startswith("./"):
            target = target[2:]
        targets.add(posixpath.normpath(posixpath.join(source_dir, target)))
        targets.add(posixpath.normpath(target))
    return targets


def _has_table(section: str) -> bool:
    lines = [line for line in section.splitlines() if line.strip()]
    for index, line in enumerate(lines[:-1]):
        if line.lstrip().startswith("|") and _TABLE_SEPARATOR.match(lines[index + 1]):
            return True
    return False


def body_words(body: str) -> int:
    """Count whitespace-separated tokens outside fenced code blocks and HTML comments."""
    without_comments = re.sub(r"<!--.*?-->", " ", body, flags=re.DOTALL)
    count = 0
    fenced = False
    for line in without_comments.splitlines():
        if _FENCE.match(line.strip()):
            fenced = not fenced
            continue
        if fenced:
            continue
        count += len(line.split())
    return count


def validate_summaries(package: Any) -> list[Finding]:
    findings: list[Finding] = []
    for module in package.documents("module"):
        body = module.body
        source_dir = PurePosixPath(module.path).parent.as_posix()
        sections = {heading: markdown_section(body, heading) for heading in REQUIRED_SUMMARY_SECTIONS}
        for heading in REQUIRED_SUMMARY_SECTIONS:
            if not sections[heading]:
                findings.append(
                    _finding(
                        "CONCORDE-SUMMARY-001",
                        module,
                        f"Module summary section '{heading}' is missing or empty.",
                        f"Add a non-empty ## {heading} section; keep the summary within the reading budget.",
                    )
                )
        structure = sections["Structure"]
        view_path = module.metadata.get("view")
        if structure:
            if isinstance(view_path, str) and view_path:
                if view_path not in _link_targets(structure, source_dir):
                    findings.append(
                        _finding(
                            "CONCORDE-SUMMARY-002",
                            module,
                            f"The Structure section does not link the module's level view '{view_path}'.",
                            "Link the declared architecture.json view from ## Structure so the published page embeds it.",
                        )
                    )
            # A leaf without a view satisfies the rule with non-empty rationale prose (already non-empty).
        for heading in INVENTORY_SECTIONS:
            section = sections[heading]
            if section and not _has_table(section) and section.strip() != EMPTY_INVENTORY:
                findings.append(
                    _finding(
                        "CONCORDE-SUMMARY-003",
                        module,
                        f"The {heading} section has neither an inventory table nor the line '{EMPTY_INVENTORY}'.",
                        f"Add a Markdown table inventorying the module's {heading.lower()}, or write '{EMPTY_INVENTORY}'.",
                    )
                )
        reference = f"{source_dir}/design.md"
        if reference not in _link_targets(body, source_dir):
            findings.append(
                _finding(
                    "CONCORDE-SUMMARY-004",
                    module,
                    "No link in the module summary resolves to the adjacent design.md design reference.",
                    "Link design.md from ## Design Rationale so the reference is reachable from the summary.",
                )
            )
        words = body_words(body)
        if words > READING_BUDGET_WORDS:
            findings.append(
                _finding(
                    "CONCORDE-SUMMARY-005",
                    module,
                    f"Module summary body has {words} words, over the {READING_BUDGET_WORDS}-word reading budget (about 20 minutes).",
                    "Move narrative, implementation detail, and rationale into design.md; keep the summary to diagram, tables, and short prose.",
                    severity="warning",
                )
            )
    return findings
