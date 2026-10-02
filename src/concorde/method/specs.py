"""How Method's definitions read the workspace's Specs before and around their steps.

Execution treats a run's Modules as names. Every definition Method registers admits them against
the workspace's registry itself, through Spec core: it leaves out, with ``removed-module``
evidence, each Module the binding names that the workspace no longer registers, refuses a run whose
binding names only such Modules (``modules_removed``), a run whose Specs cannot be loaded
(``specs_unloadable``) and a named Module the workspace does not register (``unknown_module``),
except that a definition that diagnoses the Specs itself, such as ``task-validation``, begins
even when they do not load. Spec tooling reports with its own error record, which ``spec_cause``
and ``spec_finding`` translate into links of the error chain.
"""

from __future__ import annotations

from typing import Callable

from ..execution.context import Refused, RunContext
from ..kernel.errors import evidence, link
from ..spec.errors import SpecError
from ..spec.repository import SpecRepository

ADMISSION = "Method (Module admission)"


def spec_cause(error: BaseException, actor: str = "Spec core") -> dict:
    """Spec tooling's own error as a component link: its message and location, its reason
    as the explanation, its remediation as the option, and its causes as nested links."""
    if not isinstance(error, SpecError):
        return link(
            "component",
            actor,
            "system_error",
            f"{type(error).__name__}: {error}",
            reason="environment",
            explanation="the operating system refused an operation Spec tooling needed",
        )
    where = error.where()
    return link(
        "component",
        actor,
        error.code,
        str(error) + (f" (at {where})" if where else ""),
        reason={"system_error": "environment", "unexpected_error": "capability"}.get(
            error.code, "input"
        ),
        explanation=error.reason,
        evidence=[evidence("location", where, "")] if where else [],
        options=[error.remediation],
        recommendation=error.remediation,
        causes=[spec_cause(cause, actor) for cause in error.causes],
    )


def spec_finding(rule_id: str, source: str, line, message: str, explanation: str):
    """The link of one Spec validation finding, as Spec core reported it."""
    location = (source or "-") + (f":{line}" if line else "")
    return link(
        "component",
        "Spec core validation",
        "spec_finding",
        f"{rule_id} at {location}: {message}",
        reason="capability",
        explanation=explanation,
        evidence=[evidence("finding", location, rule_id)],
    )


def _registered(context: RunContext) -> set[str]:
    """The Modules the worktree's Specs register; ``specs_unloadable`` when they do not load."""
    root = context.worktree
    try:
        return set(SpecRepository(root).modules)
    except (SpecError, OSError, ValueError) as error:
        detail = error.describe() if isinstance(error, SpecError) else str(error)
        raise Refused(
            "specs_unloadable",
            f"the Specs of {root} cannot be loaded: {detail}",
            actor=ADMISSION,
            reason="scope",
            explanation="the run needs the workspace's Specs to load and never repairs them",
            options=[
                "run concorde task-validation in the workspace to see why the Specs do not "
                "load",
                "repair the Specs by hand",
            ],
        ) from error


def admission(*, diagnoses_specs: bool = False) -> Callable[[RunContext], None]:
    """The admission of the run's Modules for a definition Method registers; with
    ``diagnoses_specs`` it begins even when the Specs do not load, keeping the binding's Modules
    whole then, and checks no named Module, since its own steps report the Specs."""

    def admit_modules(context: RunContext) -> None:
        known: set[str] | None = None
        if context.workspace is not None and not context.modules_named:
            try:
                known = _registered(context)
            except Refused:
                if not diagnoses_specs and context.modules:
                    raise
                return
            _leave_out_removed(context, known)
        if diagnoses_specs or not context.modules:
            return
        known = known if known is not None else _registered(context)
        unknown = sorted(item for item in context.modules if item not in known)
        if unknown:
            raise Refused(
                "unknown_module",
                f"{', '.join(unknown)} {'is' if len(unknown) == 1 else 'are'} not registered "
                f"in {context.worktree} (registered: {', '.join(sorted(known))})",
                actor=ADMISSION,
            )

    return admit_modules


def _leave_out_removed(context: RunContext, known: set[str]) -> None:
    kept = [item for item in context.modules if item in known]
    removed = [item for item in context.modules if item not in known]
    if removed and not kept:
        raise Refused(
            "modules_removed",
            f"every Module the binding of workspace {context.workspace_name} names "
            f"({', '.join(removed)}) is no longer registered in {context.worktree}: the "
            "workspace removed or renamed them, so the run has no Module to work on; name its "
            "current Modules with --modules",
            actor=ADMISSION,
            explanation="the binding names only Modules the workspace removed or renamed, and "
            "which of its current Modules the run works on is for the caller to name",
            options=[
                "run it again naming the workspace's current Modules with --modules"
            ],
        )
    for module in removed:
        context.evidence.append(
            evidence(
                "removed-module",
                module,
                f"the binding of workspace {context.workspace_name} names {module}, which the "
                f"workspace no longer registers, so {context.name} leaves it out",
            )
        )
    context.modules = kept


__all__ = ["ADMISSION", "admission", "spec_cause", "spec_finding"]
