"""Shared lazy LangGraph runtime for ordered Concorde capability occurrences."""

from __future__ import annotations

import operator
import re
import hashlib
import json
from dataclasses import dataclass, is_dataclass, replace
from pathlib import Path
from typing import Annotated, Any, Callable, Protocol, TypedDict

from .skill_assets import SkillPrompt, load_skill_prompt


class OperationDependencyError(RuntimeError):
    """An optional Operation runtime dependency is unavailable."""


@dataclass(frozen=True)
class OperationBinding:
    """One exact direct capability occurrence and its narrowing agent binding."""

    stage: str
    occurrence: int
    capability: str
    agent: str
    read_roles: tuple[str, ...] | None = None
    write_roles: tuple[str, ...] | None = None
    network: bool | None = None
    credentials: str | None = None


@dataclass(frozen=True)
class OperationStage:
    """One graph stage containing ordered direct capabilities."""

    name: str
    capabilities: tuple[SkillPrompt, ...]


@dataclass(frozen=True)
class CapabilityResult:
    """One successful direct capability result retained in exact graph order."""

    operation: str
    stage: str
    occurrence: int
    capability: str
    output: str
    receipt: Any | None = None


@dataclass(frozen=True)
class OperationExecution:
    """Immutable input supplied to a host for one direct capability occurrence."""

    request: str
    operation: str
    stage: str
    occurrence: int
    capability: SkillPrompt
    binding: OperationBinding
    prior_results: tuple[CapabilityResult, ...]
    launch_specification: Any | None = None


class OperationExecutor(Protocol):
    def __call__(self, invocation: OperationExecution) -> str | Any: ...


class OperationState(TypedDict):
    request: str
    capability_results: Annotated[list[CapabilityResult], operator.add]


OperationDefinition = tuple[tuple[str, tuple[str, ...]], ...]
BindingDeclaration = tuple[Any, ...]
LaunchFactory = Callable[[OperationExecution], Any]
NestedOperationDispatcher = Callable[[OperationExecution], str | Any]

_STAGE_NAME = re.compile(r"^[a-z][a-z0-9-]*$")


@dataclass(frozen=True)
class PermissionRuntimeContext:
    project_root: str
    role_paths: dict[str, tuple[str, ...]]
    denied_paths: tuple[str, ...]
    source_digest: str


def resolve_permission_runtime_context(
    project_root: str | Path,
    feature_path: str | None = None,
) -> PermissionRuntimeContext:
    """Resolve safe broad phase roles for non-planner Operation leaves."""

    from ..understanding.feature_workspace import resolve_selected_workspace, workspace_role_paths

    project = Path(project_root).resolve()
    workspace = resolve_selected_workspace(project, feature_path)
    roles = workspace_role_paths(project, workspace)
    attempts = project / ".concorde/attempts"
    denied: list[str] = []
    if attempts.is_dir() and not attempts.is_symlink():
        for path in sorted(attempts.iterdir()):
            relative = path.relative_to(project).as_posix()
            if relative != workspace.attempt_dir:
                denied.append(relative)
    payload = {
        "workspace": workspace.to_dict(),
        "roles": {name: list(values) for name, values in sorted(roles.items())},
        "denied": denied,
    }
    digest = "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return PermissionRuntimeContext(
        project_root=project.as_posix(),
        role_paths=roles,
        denied_paths=tuple(denied),
        source_digest=digest,
    )


def permission_launch_factory(
    context: Any,
    integration: str,
    *,
    native_enforcement: bool = True,
    outer_sandbox: str | None = None,
) -> LaunchFactory:
    """Create one immutable normalized/native launch specification per leaf occurrence."""

    from .operation_permissions import (
        PolicyBinding,
        build_launch_specification,
        compile_policy,
        render_claude_configuration,
        render_codex_configuration,
    )

    if integration not in {"codex", "claude"}:
        raise ValueError(f"unsupported Operation integration: {integration!r}")

    def create(invocation: OperationExecution) -> Any:
        effects = invocation.capability.effects
        if effects is None:
            raise ValueError(
                f"Operation-composed leaf {invocation.capability.name!r} has no effects"
            )
        binding = PolicyBinding(
            operation=invocation.operation,
            stage=invocation.binding.stage,
            occurrence=invocation.binding.occurrence,
            capability=invocation.binding.capability,
            agent=invocation.binding.agent,
            read_roles=invocation.binding.read_roles,
            write_roles=invocation.binding.write_roles,
            network=invocation.binding.network,
            credentials=invocation.binding.credentials,
        )
        policy = compile_policy(
            effects,
            binding,
            context.role_paths,
            deny_paths=context.denied_paths,
            outer_sandbox_required=not native_enforcement,
        )
        native = (
            render_codex_configuration(
                policy,
                native_enforcement=native_enforcement,
                outer_sandbox=outer_sandbox,
            )
            if integration == "codex"
            else render_claude_configuration(
                policy,
                native_enforcement=native_enforcement,
                outer_sandbox=outer_sandbox,
            )
        )
        return build_launch_specification(
            operation=invocation.operation,
            stage=invocation.stage,
            occurrence=invocation.occurrence,
            capability=invocation.capability.name,
            integration=integration,
            agent=invocation.binding.agent,
            project_root=context.project_root,
            request=invocation.request,
            prompt=invocation.capability.body,
            prior_results=tuple(
                f"{item.capability}:{item.output}" for item in invocation.prior_results
            ),
            workspace_digest=context.source_digest,
            policy=policy,
            native_configuration=native,
        )

    return create


def _binding(value: BindingDeclaration) -> OperationBinding:
    if not isinstance(value, tuple) or len(value) not in {4, 8}:
        raise ValueError(
            "Operation binding must identify stage, occurrence, capability, and agent"
        )
    stage, occurrence, capability, agent = value[:4]
    if (
        not isinstance(stage, str)
        or not _STAGE_NAME.fullmatch(stage)
        or not isinstance(occurrence, int)
        or occurrence < 0
        or not isinstance(capability, str)
        or not capability
        or not isinstance(agent, str)
        or not agent
    ):
        raise ValueError(f"invalid Operation binding identity: {value!r}")
    optional = value[4:] if len(value) == 8 else (None, None, None, None)
    read_roles, write_roles, network, credentials = optional
    for roles, label in ((read_roles, "read"), (write_roles, "write")):
        if roles is not None and (
            not isinstance(roles, tuple)
            or len(roles) != len(set(roles))
            or not all(isinstance(role, str) for role in roles)
        ):
            raise ValueError(f"Operation binding {label} roles must be a unique literal tuple")
    if network is not None and not isinstance(network, bool):
        raise ValueError("Operation binding network must be a bool or None")
    if credentials not in {None, "none", "declared"}:
        raise ValueError("Operation binding credentials must be none, declared, or None")
    return OperationBinding(
        stage=stage,
        occurrence=occurrence,
        capability=capability,
        agent=agent,
        read_roles=read_roles,
        write_roles=write_roles,
        network=network,
        credentials=credentials,
    )


def load_operation_stages(
    package_root: str | Path,
    definition: OperationDefinition,
    *,
    framework_prefix: str = "",
) -> tuple[OperationStage, ...]:
    """Resolve an Operation definition into immutable direct-capability stages."""

    if not definition:
        raise ValueError("Operation requires at least one stage")
    stages: list[OperationStage] = []
    names: set[str] = set()
    for name, capability_names in definition:
        if not isinstance(name, str) or not _STAGE_NAME.fullmatch(name) or name in names:
            raise ValueError(f"Operation stage name must be safe and unique: {name!r}")
        if not isinstance(capability_names, tuple) or not capability_names:
            raise ValueError(f"Operation stage {name!r} requires at least one capability")
        capabilities = tuple(
            load_skill_prompt(package_root, capability_name, framework_prefix)
            for capability_name in capability_names
        )
        stages.append(OperationStage(name=name, capabilities=capabilities))
        names.add(name)
    return tuple(stages)


def load_operation_bindings(
    stages: tuple[OperationStage, ...],
    declarations: tuple[BindingDeclaration, ...],
) -> tuple[OperationBinding, ...]:
    """Validate exact binding coverage for resolved direct occurrences."""

    bindings = tuple(_binding(item) for item in declarations)
    expected = tuple(
        (stage.name, occurrence, capability.name)
        for stage in stages
        for occurrence, capability in enumerate(stage.capabilities)
    )
    observed = tuple(
        (binding.stage, binding.occurrence, binding.capability) for binding in bindings
    )
    if observed != expected:
        raise ValueError(
            "Operation bindings must cover every direct capability occurrence exactly in stage order"
        )
    return bindings


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


def _execution_output(value: Any, capability: str) -> tuple[str, Any | None]:
    if isinstance(value, str):
        return value, None
    output = getattr(value, "output", None)
    receipt = getattr(value, "receipt", None)
    if not isinstance(output, str):
        raise TypeError(f"Operation executor for {capability!r} must return a string result")
    if receipt is None:
        raise TypeError(
            f"structured Operation executor result for {capability!r} requires a receipt"
        )
    return output, receipt


def build_operation_graph(
    operation: str,
    stages: tuple[OperationStage, ...],
    bindings: tuple[OperationBinding, ...],
    executor: OperationExecutor,
    *,
    launch_factory: LaunchFactory | None = None,
    nested_dispatcher: NestedOperationDispatcher | None = None,
) -> Any:
    """Compile resolved stages into a fail-fast graph with one handoff per occurrence."""

    if not operation:
        raise ValueError("Operation identity is required")
    if not stages:
        raise ValueError("Operation requires at least one resolved stage")
    expected_count = sum(len(stage.capabilities) for stage in stages)
    if len(bindings) != expected_count:
        raise ValueError("Operation binding count differs from direct capability occurrences")
    direct = tuple(capability for stage in stages for capability in stage.capabilities)
    leaf_names = tuple(capability.name for capability in direct if capability.kind == "skill")
    nested_names = tuple(capability.name for capability in direct if capability.kind == "operation")
    if leaf_names and launch_factory is None:
        raise ValueError(
            "Operation direct leaves require a non-null enforcement launch factory: "
            + ", ".join(leaf_names)
        )
    if nested_names and nested_dispatcher is None:
        raise ValueError(
            "Nested Operations require an explicit enforcing dispatcher: "
            + ", ".join(nested_names)
        )
    StateGraph, START, END = _langgraph_api()
    builder = StateGraph(OperationState)
    binding_offset = 0

    for stage_index, stage in enumerate(stages):
        stage_bindings = bindings[binding_offset : binding_offset + len(stage.capabilities)]
        binding_offset += len(stage.capabilities)

        def run_stage(
            state: OperationState,
            *,
            current: OperationStage = stage,
            current_bindings: tuple[OperationBinding, ...] = stage_bindings,
            first: bool = stage_index == 0,
        ) -> dict[str, list[CapabilityResult]]:
            request = state.get("request")
            prior = tuple(state.get("capability_results", ()))
            if not isinstance(request, str):
                raise TypeError("Operation request must be a string")
            if first and prior:
                raise ValueError("Operation input must start with no capability results")
            completed: list[CapabilityResult] = []
            for occurrence, (capability, binding) in enumerate(
                zip(current.capabilities, current_bindings)
            ):
                invocation = OperationExecution(
                    request=request,
                    operation=operation,
                    stage=current.name,
                    occurrence=occurrence,
                    capability=capability,
                    binding=binding,
                    prior_results=(*prior, *completed),
                )
                if capability.kind == "skill":
                    if capability.effects is None:
                        raise ValueError(
                            f"Operation-composed leaf {capability.name!r} has no effects"
                        )
                    specification = launch_factory(invocation)  # type: ignore[misc]
                    parameters = getattr(specification, "__dataclass_params__", None)
                    if (
                        specification is None
                        or not is_dataclass(specification)
                        or parameters is None
                        or not parameters.frozen
                    ):
                        raise TypeError(
                            f"Operation leaf {capability.name!r} requires a frozen immutable launch specification"
                        )
                    invocation = replace(
                        invocation,
                        launch_specification=specification,
                    )
                    value = executor(invocation)
                else:
                    value = nested_dispatcher(invocation)  # type: ignore[misc]
                output, receipt = _execution_output(value, capability.name)
                completed.append(
                    CapabilityResult(
                        operation=operation,
                        stage=current.name,
                        occurrence=occurrence,
                        capability=capability.name,
                        output=output,
                        receipt=receipt,
                    )
                )
            return {"capability_results": completed}

        builder.add_node(stage.name, run_stage)

    builder.add_edge(START, stages[0].name)
    for current, following in zip(stages, stages[1:]):
        builder.add_edge(current.name, following.name)
    builder.add_edge(stages[-1].name, END)
    return builder.compile()


def build_operation(
    package_root: str | Path,
    operation: str,
    definition: OperationDefinition,
    binding_declarations: tuple[BindingDeclaration, ...],
    executor: OperationExecutor,
    *,
    framework_prefix: str = "",
    launch_factory: LaunchFactory | None = None,
    nested_dispatcher: NestedOperationDispatcher | None = None,
) -> Any:
    """Resolve canonical direct capabilities and compile one Operation."""

    stages = load_operation_stages(
        package_root,
        definition,
        framework_prefix=framework_prefix,
    )
    bindings = load_operation_bindings(stages, binding_declarations)
    return build_operation_graph(
        operation,
        stages,
        bindings,
        executor,
        launch_factory=launch_factory,
        nested_dispatcher=nested_dispatcher,
    )
