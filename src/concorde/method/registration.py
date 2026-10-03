"""Method registers its Operations and execution commands with Execution's catalogs.

Loading this module registers every definition of Concorde's way of working, as a part registers
what it provides when its code loads; registering it again changes nothing. The method part's
registration names it among the modules Distribution loads before it routes a command or a tool,
and names its execution commands' entries here.
"""

from __future__ import annotations

from dataclasses import replace

from ..execution.commands.catalog import COMMANDS
from ..execution.operations.catalog import OPERATIONS
from ..execution.runner import run_main
from .adoption.code_to_spec import CODE_TO_SPEC
from .adoption.survey import SURVEY
from .code_review.operation import CODE_REVIEW
from .delivery.command import DELIVERY
from .implementation.operation import IMPLEMENT, TEST
from .scaffold.command import SCAFFOLD
from .spec_review.operation import SPEC_REVIEW
from .spec_review.panel import SPEC_PANEL
from .specification.operation import SPECIFY
from .understanding.operation import UNDERSTAND
from .understanding.plan_review import PLAN_REVIEW
from .validation.command import TASK_VALIDATION

PART = "method"
# Each definition with the Module of the method part that provides it.
DEFINED_OPERATIONS = tuple(
    replace(definition, module=module)
    for definition, module in (
        (UNDERSTAND, "module.understanding"),
        (PLAN_REVIEW, "module.understanding"),
        (SPECIFY, "module.specification"),
        (IMPLEMENT, "module.implementation"),
        (TEST, "module.implementation"),
        (SPEC_REVIEW, "module.spec-review"),
        (SPEC_PANEL, "module.spec-review"),
        (CODE_REVIEW, "module.code-review"),
        (SURVEY, "module.adoption"),
        (CODE_TO_SPEC, "module.adoption"),
    )
)
DEFINED_COMMANDS = tuple(
    replace(definition, module=module)
    for definition, module in (
        (TASK_VALIDATION, "module.validation"),
        (DELIVERY, "module.delivery"),
        (SCAFFOLD, "module.scaffold"),
    )
)

for _definition in DEFINED_OPERATIONS:
    OPERATIONS.register(PART, _definition)
for _definition in DEFINED_COMMANDS:
    COMMANDS.register(PART, _definition)


def _command(name: str):
    def main(words, root=None) -> int:
        return run_main("command", name, words)

    main.__doc__ = (
        f"``concorde {name}``, as the method part's registration names it: the execution "
        "command run by Execution's runner in the workspace of the current worktree."
    )
    return main


task_validation = _command("task-validation")
delivery = _command("delivery")
scaffold = _command("scaffold")

__all__ = [
    "DEFINED_COMMANDS",
    "DEFINED_OPERATIONS",
    "PART",
    "delivery",
    "scaffold",
    "task_validation",
]
