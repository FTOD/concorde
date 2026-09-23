"""Task subagent profiles, not domain stage-schema or bounded-Module profiles."""

from dataclasses import dataclass
from pathlib import Path


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

# Source profiles are excluded from installed packages, not registered then hidden.
if (Path(__file__).parent / "source").is_dir():
    from .source.maintenance_worker import PROFILE as _maintenance

    TASK_SUBAGENT_PROFILES = (*PROFILES, _maintenance)
else:
    TASK_SUBAGENT_PROFILES = PROFILES

TASK_SUBAGENTS = tuple(profile.name for profile in TASK_SUBAGENT_PROFILES)
