"""LangGraph workflow composition over complete canonical Concorde command prompts."""

from __future__ import annotations

import operator
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Protocol, TypedDict

from .command_assets import CommandPrompt, load_command_prompt


class WorkflowDependencyError(RuntimeError):
    """An optional workflow runtime dependency is unavailable."""


@dataclass(frozen=True)
class WorkflowStage:
    """One graph stage containing complete canonical prompts in execution order."""

    name: str
    prompts: tuple[CommandPrompt, ...]


@dataclass(frozen=True)
class StageResult:
    """One successful stage output retained in graph order."""

    stage: str
    output: str


@dataclass(frozen=True)
class StageExecution:
    """Immutable input supplied to a host-owned stage executor."""

    request: str
    stage: WorkflowStage
    prior_results: tuple[StageResult, ...]


class StageExecutor(Protocol):
    def __call__(self, invocation: StageExecution) -> str: ...


class StandardDevLoopState(TypedDict):
    request: str
    stage_results: Annotated[list[StageResult], operator.add]


WorkflowDefinition = tuple[tuple[str, tuple[str, ...]], ...]


STANDARD_DEV_LOOP: WorkflowDefinition = (
    ("specify", ("concorde.specify",)),
    ("plan", ("concorde.plan",)),
    ("tasks", ("concorde.tasks", "concorde.implement")),
    ("deliver", ("concorde.validate", "concorde.deliver")),
)

_STAGE_NAME = re.compile(r"^[a-z][a-z0-9-]*$")


def load_workflow_stages(
    package_root: str | Path,
    definition: WorkflowDefinition,
    *,
    framework_prefix: str = "",
) -> tuple[WorkflowStage, ...]:
    """Resolve a workflow definition into immutable whole-prompt stages."""

    if not definition:
        raise ValueError("workflow requires at least one stage")
    stages: list[WorkflowStage] = []
    names: set[str] = set()
    for name, command_ids in definition:
        if not isinstance(name, str) or not _STAGE_NAME.fullmatch(name) or name in names:
            raise ValueError(f"workflow stage name must be safe and unique: {name!r}")
        if not command_ids:
            raise ValueError(f"workflow stage {name!r} requires at least one command prompt")
        prompts = tuple(
            load_command_prompt(package_root, command_id, framework_prefix)
            for command_id in command_ids
        )
        stages.append(WorkflowStage(name=name, prompts=prompts))
        names.add(name)
    return tuple(stages)


def _langgraph_api() -> tuple[Any, Any, Any]:
    try:
        from langgraph.graph import END, START, StateGraph
    except ModuleNotFoundError as error:
        if error.name == "langgraph" or (error.name and error.name.startswith("langgraph.")):
            raise WorkflowDependencyError(
                "LangGraph workflow execution requires the optional dependency langgraph>=1.2,<2."
            ) from error
        raise
    return StateGraph, START, END


def build_prompt_workflow(
    stages: tuple[WorkflowStage, ...],
    executor: StageExecutor,
) -> Any:
    """Compile whole-prompt stages into a linear LangGraph workflow."""

    if not stages:
        raise ValueError("workflow requires at least one resolved stage")
    StateGraph, START, END = _langgraph_api()
    builder = StateGraph(StandardDevLoopState)

    for index, stage in enumerate(stages):
        def run_stage(
            state: StandardDevLoopState,
            *,
            current: WorkflowStage = stage,
            first: bool = index == 0,
        ) -> dict[str, list[StageResult]]:
            request = state.get("request")
            prior = tuple(state.get("stage_results", ()))
            if not isinstance(request, str):
                raise TypeError("workflow request must be a string")
            if first and prior:
                raise ValueError("standard workflow input must start with no stage results")
            output = executor(
                StageExecution(
                    request=request,
                    stage=current,
                    prior_results=prior,
                )
            )
            if not isinstance(output, str):
                raise TypeError(f"stage executor for {current.name!r} must return a string")
            return {"stage_results": [StageResult(stage=current.name, output=output)]}

        builder.add_node(stage.name, run_stage)

    builder.add_edge(START, stages[0].name)
    for current, following in zip(stages, stages[1:]):
        builder.add_edge(current.name, following.name)
    builder.add_edge(stages[-1].name, END)
    return builder.compile()


def build_standard_dev_loop(
    package_root: str | Path,
    executor: StageExecutor,
    *,
    framework_prefix: str = "",
) -> Any:
    """Compile the standard specify → plan → tasks → deliver workflow."""

    stages = load_workflow_stages(
        package_root,
        STANDARD_DEV_LOOP,
        framework_prefix=framework_prefix,
    )
    return build_prompt_workflow(stages, executor)
