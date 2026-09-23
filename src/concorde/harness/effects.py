"""Shared effect-declaration vocabulary of Agent profiles.

``EffectDeclaration`` names the exact path roles one launchable agent identity may read or write,
plus its network/credential posture. ``PATH_ROLES`` is the closed vocabulary those declarations draw
from. This module is pure data shared by the worker profiles and the build.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CredentialPosture = Literal["none", "declared"]

PATH_ROLES = frozenset(
    {
        "spec-context",
        "implementation",
        # The Module's external references (Protocol 5.1): vendored documentation and source it
        # reads but does not own, granted read-only as resource context, never written.
        "references",
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
        "framework",
        "templates",
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
