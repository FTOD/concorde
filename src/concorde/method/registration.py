"""Method registers its Operations and execution commands with Execution's catalogs.

Loading this module registers every definition of Concorde's way of working, as a part registers
what it provides when its code loads; registering it again changes nothing. Whoever runs the
definitions loads it first: Distribution's ``concorde`` command before it dispatches ``run``, an
execution command or ``workflow``.
"""

from __future__ import annotations

from ..execution.commands.catalog import COMMANDS
from ..execution.operations.catalog import OPERATIONS
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
DEFINED_OPERATIONS = (
    UNDERSTAND,
    PLAN_REVIEW,
    SPECIFY,
    IMPLEMENT,
    TEST,
    SPEC_REVIEW,
    SPEC_PANEL,
    CODE_REVIEW,
    SURVEY,
    CODE_TO_SPEC,
)
DEFINED_COMMANDS = (TASK_VALIDATION, DELIVERY, SCAFFOLD)

for _definition in DEFINED_OPERATIONS:
    OPERATIONS.register(PART, _definition)
for _definition in DEFINED_COMMANDS:
    COMMANDS.register(PART, _definition)

__all__ = ["DEFINED_COMMANDS", "DEFINED_OPERATIONS", "PART"]
