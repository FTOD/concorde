"""Shared LangGraph runtime for Operations composed from canonical leaf Skills."""

from __future__ import annotations

import operator
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Protocol, TypedDict

from .skill_assets import SkillPrompt, load_skill_prompt


class OperationDependencyError(RuntimeError):
    """An optional Operation runtime dependency is unavailable."""


@dataclass(frozen=True)
class OperationStage:
    """One graph stage containing complete leaf Skills in execution order."""

    name: str
    skills: tuple[SkillPrompt, ...]


@dataclass(frozen=True)
class StageResult:
    """One successful Operation stage output retained in graph order."""

    stage: str
    output: str


@dataclass(frozen=True)
class OperationExecution:
    """Immutable input supplied to a host-owned Operation executor."""

    request: str
    stage: OperationStage
    prior_results: tuple[StageResult, ...]


class OperationExecutor(Protocol):
    def __call__(self, invocation: OperationExecution) -> str: ...


class OperationState(TypedDict):
    request: str
    stage_results: Annotated[list[StageResult], operator.add]


OperationDefinition = tuple[tuple[str, tuple[str, ...]], ...]

_STAGE_NAME = re.compile(r"^[a-z][a-z0-9-]*$")


def load_operation_stages(
    package_root: str | Path,
    definition: OperationDefinition,
    *,
    framework_prefix: str = "",
) -> tuple[OperationStage, ...]:
    """Resolve an Operation definition into immutable whole-Skill stages."""

    if not definition:
        raise ValueError("Operation requires at least one stage")
    stages: list[OperationStage] = []
    names: set[str] = set()
    for name, skill_names in definition:
        if not isinstance(name, str) or not _STAGE_NAME.fullmatch(name) or name in names:
            raise ValueError(f"Operation stage name must be safe and unique: {name!r}")
        if not skill_names:
            raise ValueError(f"Operation stage {name!r} requires at least one Skill")
        skills = tuple(
            load_skill_prompt(package_root, skill_name, framework_prefix)
            for skill_name in skill_names
        )
        if any(skill.kind != "skill" for skill in skills):
            raise ValueError(f"Operation stage {name!r} may compose only leaf Skills")
        stages.append(OperationStage(name=name, skills=skills))
        names.add(name)
    return tuple(stages)


def _langgraph_api() -> tuple[Any, Any, Any]:
    try:
        from langgraph.graph import END, START, StateGraph
    except ModuleNotFoundError as error:
        if error.name == "langgraph" or (error.name and error.name.startswith("langgraph.")):
            raise OperationDependencyError(
                "Concorde Operations require the optional dependency langgraph>=1.2,<2."
            ) from error
        raise
    return StateGraph, START, END


def build_operation_graph(
    stages: tuple[OperationStage, ...],
    executor: OperationExecutor,
) -> Any:
    """Compile resolved Skill stages into a linear LangGraph Operation."""

    if not stages:
        raise ValueError("Operation requires at least one resolved stage")
    StateGraph, START, END = _langgraph_api()
    builder = StateGraph(OperationState)

    for index, stage in enumerate(stages):
        def run_stage(
            state: OperationState,
            *,
            current: OperationStage = stage,
            first: bool = index == 0,
        ) -> dict[str, list[StageResult]]:
            request = state.get("request")
            prior = tuple(state.get("stage_results", ()))
            if not isinstance(request, str):
                raise TypeError("Operation request must be a string")
            if first and prior:
                raise ValueError("Operation input must start with no stage results")
            output = executor(
                OperationExecution(request=request, stage=current, prior_results=prior)
            )
            if not isinstance(output, str):
                raise TypeError(f"Operation executor for {current.name!r} must return a string")
            return {"stage_results": [StageResult(stage=current.name, output=output)]}

        builder.add_node(stage.name, run_stage)

    builder.add_edge(START, stages[0].name)
    for current, following in zip(stages, stages[1:]):
        builder.add_edge(current.name, following.name)
    builder.add_edge(stages[-1].name, END)
    return builder.compile()


def build_operation(
    package_root: str | Path,
    definition: OperationDefinition,
    executor: OperationExecutor,
    *,
    framework_prefix: str = "",
) -> Any:
    """Resolve canonical Skills and compile one Operation."""

    return build_operation_graph(
        load_operation_stages(package_root, definition, framework_prefix=framework_prefix),
        executor,
    )
