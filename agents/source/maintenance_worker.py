"""Canonical source-only author profile."""

from ..task_subagent import TaskSubagentProfile

PROFILE = TaskSubagentProfile(
    "maintenance-worker",
    "prompts/task-subagent/source/maintenance-worker.md",
    ("read", "grep", "find", "ls", "bash", "edit", "write"),
    ("concorde-maintenance.ts", "concorde-brief-lifecycle.ts"),
    True,
)
