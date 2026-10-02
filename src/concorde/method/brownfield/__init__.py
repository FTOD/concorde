"""Method's brownfield workflow: describe a project whose code came before its Specs.

Loading this module registers the workflow with Workflows' catalog: its procedure is
``brownfield.js`` beside it, and its last step is ``delivery``, so its workflow result is ``ok``
only when the delivery step ended ``ok``.
"""

from __future__ import annotations

from ...workflows import catalog

BROWNFIELD = catalog.Workflow(
    name="brownfield",
    description=(
        "Describe a project whose code came before its Specs: survey, scaffold, "
        "code_to_spec per Module, spec review, validation and delivery, in one task"
    ),
    when=(
        "After installing and initializing Concorde in an existing codebase, in the worktree "
        "of a task bound to the Module to describe, usually the root"
    ),
    phases=("Survey", "Scaffold", "Describe", "Review", "Deliver"),
    script="src/concorde/method/brownfield/brownfield.js",
    last_step="delivery",
    registered_in="src/concorde/method/brownfield/__init__.py",
)

catalog.register(BROWNFIELD)

__all__ = ["BROWNFIELD"]
