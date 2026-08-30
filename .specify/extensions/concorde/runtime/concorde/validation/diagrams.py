"""Maintained diagram presentation and module-reference rules.

Every Archify diagram beneath `<module>/architecture/diagrams/` is a maintained explanation of that
level. A diagram nobody links is unreachable from the hierarchy, so each one must be referenced from
the level's `module.md`, its `design.md`, or the project reflection log. Module- and feature-owned
diagrams hide Archify's renderer-owned legends because Concorde diagrams use domain-specific labels
and textual counterparts instead of the renderer's generic kind names.
"""

from __future__ import annotations

import posixpath
from pathlib import PurePosixPath
from typing import Any

from ..model import Finding
from ..reflections import log_path
from .summary import _link_targets


def validate_diagrams(package: Any) -> list[Finding]:
    findings: list[Finding] = []
    for path, diagram in sorted({**package.views, **package.diagrams}.items()):
        meta = diagram.get("meta") if isinstance(diagram, dict) else None
        legend = meta.get("legend") if isinstance(meta, dict) else None
        if not isinstance(legend, dict) or legend.get("mode") != "hidden":
            findings.append(
                Finding(
                    "CONCORDE-VIEW-007",
                    "error",
                    path,
                    "Maintained Archify diagrams must explicitly hide the renderer-owned legend.",
                    'Set meta.legend to {"mode": "hidden"}; rely on domain labels and the '
                    "diagram's textual counterpart.",
                )
            )
    reflections_path = log_path(package.specification_root)
    reflections_body = package.auxiliary.get(reflections_path)
    reflections_links = (
        _link_targets(reflections_body, PurePosixPath(reflections_path).parent.as_posix())
        if reflections_body is not None
        else set()
    )
    for module in package.documents("module"):
        diagrams = package.module_diagrams(module)
        if not diagrams:
            continue
        source_dir = PurePosixPath(module.path).parent.as_posix()
        linked = _link_targets(module.body, source_dir)
        design = package.auxiliary.get(f"{source_dir}/design.md")
        if design is not None:
            linked |= _link_targets(design, source_dir)
        linked |= reflections_links
        for path in diagrams:
            if posixpath.normpath(path) in linked:
                continue
            findings.append(
                Finding(
                    "CONCORDE-VIEW-006",
                    "error",
                    path,
                    f"Diagram '{PurePosixPath(path).name}' is not referenced from the level's module.md, design.md, or the project reflection log.",
                    "Link the diagram from ## Structure of module.md (a level view), from design.md (an explanatory view), or from reflections.md, or remove the file.",
                    subject_id=module.identifier,
                )
            )
    return findings
