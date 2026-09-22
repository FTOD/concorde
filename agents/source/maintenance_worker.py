"""Canonical source-only author profile."""

from ..outer import OuterProfile

PROFILE = OuterProfile(
    "maintenance-worker",
    "prompts/outer/source/maintenance-worker.md",
    ("read", "grep", "find", "ls", "bash", "edit", "write"),
    ("concorde-maintenance.ts", "concorde-outer-lifecycle.ts"),
    True,
)
