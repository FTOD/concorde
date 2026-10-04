"""Which configured checks Method's steps run, chosen from the workspace's Specs.

Check execution runs the checks of the Modules it is given, as labels, and reads no Spec. Method
says which: the Modules a change concerns (their Spec scope or implementation scope holds a changed
path), every Module that uses one of them, directly or through further uses, since its code runs
against the change, the implementation files each Module's result depends on, the tests whose
verification declarations name a scenario of the selected Modules, which a selective check runs,
and the project's interpreter, ``python`` of the project configuration. ``run_module_checks`` is
the one call every Method step and round validation runs checks through.
"""

from __future__ import annotations

from pathlib import Path

from ..execution.checks.checks import configured_checks, run_checks, selective
from ..spec.repository import SpecRepository
from ..spec.repository_base import bound_by


def affected_modules(repository: SpecRepository, changed) -> list[str]:
    """Every Module whose SpecScope or ImplementationScope contains a changed path."""
    result = []
    for identity in repository.modules:
        scope = set(repository.spec_scope(identity))
        entries = repository.implementation_scope(identity)
        if any(
            path in scope or any(bound_by(entry, path) for entry in entries)
            for path in changed
        ):
            result.append(identity)
    return result


def checked_modules(repository: SpecRepository, modules) -> list[str]:
    """The Modules whose checks a change of ``modules`` runs: those Modules and every Module that
    uses one of them, directly or through further uses, since their code runs against the change
    (the Protocol's impact of a written file). A full test suite checked by the Module that uses
    everything therefore runs whichever Module changes."""
    selected = list(dict.fromkeys(modules))
    reached = set(selected)
    changed = True
    while changed:
        changed = False
        for identity, module in repository.modules.items():
            if identity not in reached and reached & set(module.uses):
                reached.add(identity)
                selected.append(identity)
                changed = True
    return selected


def verified_tests(repository: SpecRepository, modules) -> list[str]:
    """The tests declaring that they verify a scenario of ``modules``: a Python test as
    ``path::Class::name``, a TypeScript test by its file."""
    from ..spec.verification import TYPESCRIPT_SUFFIXES, scan_declarations

    listed = sorted(
        {
            path
            for identity in repository.modules
            for path in repository.bound_files(identity)
        }
    )
    wanted = set(modules)
    scenarios = repository.scenario_nodes
    tests: dict[str, None] = {}
    for declaration in scan_declarations(repository.root, listed, []):
        scenario = scenarios.get(declaration.scenario_id)
        if scenario is None or scenario.owner not in wanted:
            continue
        if declaration.path.endswith(TYPESCRIPT_SUFFIXES):
            tests[declaration.path] = None
        else:
            tests[f"{declaration.path}::{declaration.name.replace('.', '::')}"] = None
    return sorted(tests)


def measured_files(repository: SpecRepository, modules) -> dict[str, tuple[str, ...]]:
    """The implementation files each of ``modules`` binds: what its check results depend on."""
    return {
        identity: tuple(repository.bound_files(identity))
        for identity in modules
        if identity in repository.modules
    }


def run_module_checks(
    worktree: Path,
    modules,
    *,
    trace_directory: Path,
    stage: str = "work",
    kinds: str = "all",
    repository: SpecRepository | None = None,
) -> list[dict]:
    """Run the configured checks of ``modules``, as Check execution's ``run_checks`` does, with
    what the workspace's Specs say about them: each Module's implementation files, the tests
    verifying their scenarios and the project's interpreter. Spec core's errors and Check
    execution's ``CheckError`` pass through."""
    repository = repository or SpecRepository(worktree)
    selected = list(dict.fromkeys(modules))
    # The tests are looked for only when some configured check selects tests.
    selects = kinds != "module" and any(
        selective(check) for check in configured_checks(worktree)
    )
    return run_checks(
        worktree,
        modules=selected,
        trace_directory=trace_directory,
        measured=measured_files(repository, selected),
        tests=verified_tests(repository, selected) if selects else (),
        python=repository.config.get("python"),
        stage=stage,
        kinds=kinds,
    )


__all__ = [
    "affected_modules",
    "checked_modules",
    "measured_files",
    "run_module_checks",
    "verified_tests",
]
