"""Task subagent profiles, not domain stage-schema or bounded-Module profiles."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskSubagentProfile:
    name: str
    prompt: str
    tools: tuple[str, ...]
    extensions: tuple[str, ...]
    source_only: bool
    acceptance_role: str | None = None


PROFILES = (
    TaskSubagentProfile(
        "tester",
        "prompts/task-subagent/tester.md",
        ("read", "grep", "find", "ls", "test_command"),
        ("concorde-tester.ts",),
        False,
        "read-only",
    ),
)
