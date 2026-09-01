"""Architecture-owned diagram declaration, presentation, and reference rules."""

from __future__ import annotations

import posixpath
import re
from pathlib import PurePosixPath
from typing import Any

from ..model import Finding


_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def _link_targets(text: str, source_dir: str) -> set[str]:
    targets: set[str] = set()
    for match in _LINK.finditer(text):
        target = match.group(1).split("#", 1)[0]
        if not target or "://" in target or target.startswith(("mailto:", "/")):
            continue
        targets.add(posixpath.normpath(posixpath.join(source_dir, target.removeprefix("./"))))
        targets.add(posixpath.normpath(target))
    return targets


def validate_diagrams(package: Any) -> list[Finding]:
    findings: list[Finding] = []
    for module in package.documents("module"):
        source_dir = PurePosixPath(module.path).parent.as_posix()
        linked = _link_targets(module.body, source_dir)
        declared = module.metadata.get("diagrams", [])
        declared_sources: set[str] = set()
        if isinstance(declared, list):
            for item in declared:
                if not isinstance(item, dict) or not isinstance(item.get("source"), str):
                    continue
                source = item["source"]
                candidate = PurePosixPath(source)
                if candidate.parent != PurePosixPath(source_dir) / "diagrams":
                    candidate = PurePosixPath(source_dir) / candidate
                declared_sources.add(candidate.as_posix())
                diagram = package.diagrams.get(candidate.as_posix())
                if diagram is not None and item.get("kind") and diagram.get("diagram_type") != item.get("kind"):
                    findings.append(Finding("CONCORDE-VIEW-008", "error", module.path, f"Diagram declaration kind for '{candidate}' disagrees with diagram_type.", "Make the architecture declaration and maintained JSON source agree.", subject_id=module.identifier))
        for path, diagram in package.module_diagrams(module).items():
            meta = diagram.get("meta") if isinstance(diagram, dict) else None
            legend = meta.get("legend") if isinstance(meta, dict) else None
            if not isinstance(legend, dict) or legend.get("mode") != "hidden":
                findings.append(Finding("CONCORDE-VIEW-007", "error", path, "Maintained Archify diagrams must explicitly hide the renderer-owned legend.", 'Set meta.legend to {"mode": "hidden"}.', subject_id=module.identifier))
            if path not in declared_sources:
                findings.append(Finding("CONCORDE-VIEW-009", "error", path, "Architecture diagram is not declared by its module front matter.", "Add source, kind, and output to architecture.md diagrams.", subject_id=module.identifier))
            if posixpath.normpath(path) not in linked:
                findings.append(Finding("CONCORDE-VIEW-006", "error", path, "Architecture diagram is not linked from its owning architecture.md.", "Add a textual link from the architecture document or remove the diagram.", subject_id=module.identifier))
    return findings
