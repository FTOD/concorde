"""Canonical callable Pi role inventory. Main is an external session, not a tenth role.

Domain profiles use Harness WorkerProfile contracts; outer profiles have task grants instead.
Rendering/registration belongs to Distribution, execution and admission to Harness.
"""

from pathlib import Path

from .outer import PROFILES as DISTRIBUTED_OUTER_PROFILES

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

    OUTER_PROFILES = (*DISTRIBUTED_OUTER_PROFILES, _maintenance)
else:
    OUTER_PROFILES = DISTRIBUTED_OUTER_PROFILES

OUTER_AGENTS = tuple(profile.name for profile in OUTER_PROFILES)
AGENTS = (*tuple(name.replace("_", "-") for name in DOMAIN_AGENTS), *OUTER_AGENTS)


def external_name(module_name: str) -> str:
    """Preserved domain wire identity; outer names have no concorde prefix."""
    return "concorde-" + module_name.replace("_", "-")
