"""Shared effect-declaration vocabulary for roles and permission compilation.

``EffectDeclaration`` names the exact path roles one launchable agent identity may read or write,
plus its network/credential posture. ``PATH_ROLES`` is the closed vocabulary those declarations draw
from. This module has no dependency on the old package-loading machinery: it is pure data shared by
``roles.py`` (role authority) and ``permissions.py`` (policy compilation).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CredentialPosture = Literal["none", "declared"]

PATH_ROLES = frozenset(
    {
        "discovery-context",
        "spec-context",
        "implementation",
        "selected-feature",
        "module-architecture",
        "module-ancestry",
        "related-summaries",
        "required-feature-specs",
        "owned-implementation",
        "task-authorized",
        "attempt",
        "checklists",
        "constitution",
        "reflections",
        "framework",
        "templates",
        "reflection-queue",
        "reflection-plans",
        "reflection-worktrees",
        "generated-projections",
    }
)


@dataclass(frozen=True)
class EffectDeclaration:
    """Integration-neutral authority owned by one canonical launchable agent identity."""

    reads: tuple[str, ...] = ()
    writes: tuple[str, ...] = ()
    network: bool = False
    credentials: CredentialPosture = "none"
