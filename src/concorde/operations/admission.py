"""The step every Operation's run begins with: all its workers checked against the model map."""

from __future__ import annotations

from ..errors import evidence
from ..execution.context import Continue, component
from ..harness.models import HANDLING, ModelConfigError, check_mapped, config_path, load


def check_worker_models(context):
    """Check every worker the Operation may launch against the machine's model map at once, when
    its run is admitted, so that the run never stops at a later worker after earlier ones ran;
    stop ``failed`` with ``worker_model_unavailable`` before any worker launches otherwise."""
    try:
        check_mapped(load(context.worktree), operation=context.name)
    except ModelConfigError as error:
        path = config_path(context.worktree).as_posix()
        reason = HANDLING.get(error.code, ("input",))[0]
        return context.fail(
            "failed",
            "worker_model_unavailable",
            f"The workers of {context.name} could not be configured ({error.code}).",
            f"the models of the workers {context.name} may launch in {context.worktree} cannot "
            f"all be settled: {error.code}: {error} (configuration file {path}); the run checks "
            "them all when it is admitted, so no worker launched",
            reason=reason,
            explanation="an Operation runs each worker on the program and model the worker "
            "configuration chooses for it, through the machine's model map, and never guesses, "
            "repairs or falls back from any of them",
            evidence=[evidence("worker_configuration", path, f"{error.code}: {error}")],
            causes=[
                component(
                    "Workers (worker configuration)",
                    error.code,
                    str(error),
                    reason,
                    "Workers reads the worker configuration and the model map and changes "
                    "neither",
                )
            ],
            options=(
                [
                    "write or correct this machine's model map as the error says, giving each "
                    "project model name it names its local id on that backend; the map is the "
                    "user's and is never committed"
                ]
                if error.code
                in ("model_map_missing", "model_map_invalid", "model_unmapped")
                else [
                    f"correct {path} as the error says and commit it; an unbound run reads the "
                    "committed file of its checkout"
                ]
            ),
        )
    return Continue()


__all__ = ["check_worker_models"]
