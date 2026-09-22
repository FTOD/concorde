"""Canonical callable Pi Agent inventory. The user session is external, not a tenth Agent.

Domain Agent profiles use Harness WorkerProfile contracts; Task subagent profiles have task
grants instead. Rendering/registration belongs to Distribution, execution and admission to Harness.
"""

from pathlib import Path

from .task_subagent import PROFILES as DISTRIBUTED_TASK_SUBAGENT_PROFILES

DOMAIN_AGENTS = (
    "spec_reviewer",
    "context_assessor",
    "planner",
    "task_author",
    "programmer",
    "code_reviewer",
    "issue_solver",
)
# Source profiles are excluded from installed packages, not registered then hidden.
if Path(__file__).with_name("source").is_dir():
    from .source.maintenance_worker import PROFILE as _maintenance

    TASK_SUBAGENT_PROFILES = (*DISTRIBUTED_TASK_SUBAGENT_PROFILES, _maintenance)
else:
    TASK_SUBAGENT_PROFILES = DISTRIBUTED_TASK_SUBAGENT_PROFILES

TASK_SUBAGENTS = tuple(profile.name for profile in TASK_SUBAGENT_PROFILES)
AGENTS = (*tuple(name.replace("_", "-") for name in DOMAIN_AGENTS), *TASK_SUBAGENTS)


def external_name(module_name: str) -> str:
    """Preserved domain wire identity; Task subagent names have no concorde prefix."""
    return "concorde-" + module_name.replace("_", "-")
