"""Execute one host-built worker invocation as a Pi worker and admit its typed result.

The host freezes an invocation's context, compiles its policy, resolves its WorkerProfile binding and
selects its model; ``build_worker_invocation`` binds all of that into one immutable, digest-bound
``WorkerInvocation``. ``WorkerExecutor`` then refuses to run anything it cannot verify: the carried
binding must equal the current build's, the system prompt must be exactly the worker's rendered
instructions followed by the Protocol files the context lists, and the context and policy must fit
the WorkerProfile's contract. It launches the worker through the Pi worker runtime and admits the single
submitted result only when it validates against the contract's result type and permitted fields.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Literal

from . import worker_profile
from .model_selection import WorkerSelection
from .permissions import NormalizedPolicy
from .pi_worker import ChildAgent, PiWorkerRuntime, WorkerExecutionError, WorkerLaunch

PACKAGE_ROOT = Path(__file__).resolve().parents[3]

Outcome = Literal["failed", "cancelled", "limit_exhausted", "invalid_completion"]


class CapabilityExecutionError(RuntimeError):
    """A worker invocation was refused, failed, was cancelled, ran out of time or returned an invalid
    result. ``outcome`` classifies why; ``code`` preserves a contract rejection class. The host maps
    these to distinct result error codes, and none retries automatically."""

    def __init__(self, message: str, outcome: Outcome = "failed", code: str | None = None,
                 usage: "ExecutionUsage | None" = None):
        super().__init__(message)
        self.outcome: Outcome = outcome
        self.code = code
        self.usage = usage


@dataclass(frozen=True)
class ExecutionUsage:
    """What one worker consumed, as Pi reported it; ``None`` means Pi did not report that figure.

    Usage is diagnostic evidence about cost and never gates a result."""

    model: str | None = None
    thinking: str | None = None
    input_tokens: int | None = None
    cached_input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cost_usd: float | None = None
    turns: int | None = None
    wall_seconds: float | None = None
    prompt_bytes: int | None = None
    context_bytes: int | None = None

    def wire(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkerInvocation:
    capability: str
    stage: str
    agent: str
    invocation_id: str
    workspace: str
    context_json: str
    receipt_json: str
    policy: NormalizedPolicy
    binding_json: str
    instructions: str
    selection: WorkerSelection
    child_selections: tuple[tuple[str, WorkerSelection], ...]
    digest: str

    @property
    def context_id(self) -> str:
        from ..spec.typed_data import decode
        return decode(self.receipt_json)["source_digest"]


@dataclass(frozen=True)
class WorkerOutcome:
    value: dict[str, Any]
    usage: ExecutionUsage
    invocation_digest: str
    binding_digest: str


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def worker_instructions(rendered: str, protocol: list[tuple[str, bytes]]) -> str:
    """A worker's system prompt: its rendered instructions, then each listed Protocol file."""
    parts = [rendered.rstrip("\n")]
    for path, raw in protocol:
        parts.append(f"# Concorde Spec Protocol and Framework profile ({path})\n\n" + raw.decode("utf-8").rstrip("\n"))
    return "\n\n".join(parts) + "\n"


def result_parameters(type_id: str) -> dict[str, Any]:
    """The self-contained JSON schema of a result type's data: the worker's submit_result parameters."""
    from ..spec.typed_data import DATA_SCHEMAS

    def expand(value, seen):
        if isinstance(value, dict):
            if "$ref" in value:
                name = value["$ref"]
                if name in seen:
                    raise ValueError(f"recursive result schema: {name}")
                return expand(DATA_SCHEMAS[name], seen | {name})
            return {key: expand(item, seen) for key, item in value.items() if key != "format"}
        if isinstance(value, list):
            return [expand(item, seen) for item in value]
        return value

    result = expand(DATA_SCHEMAS[type_id], frozenset({type_id}))
    if not isinstance(result, dict):
        raise ValueError("worker result schema must be an object")
    return result


def build_worker_invocation(*, capability: str, stage: str, agent: str, invocation_id: str, workspace: str,
                            context_json: str, receipt_json: str, policy: NormalizedPolicy,
                            binding_json: str, instructions: str, selection: WorkerSelection,
                            child_selections: tuple[tuple[str, WorkerSelection], ...] = ()) -> WorkerInvocation:
    """Bind one invocation's identities, refusing an inconsistent or non-canonical combination."""
    from ..spec.typed_data import canonical, decode, validate_typed

    name = worker_profile.worker_key(agent)
    external = worker_profile.external_worker_name(name)
    if (policy.capability, policy.stage, policy.role, policy.agent) != (capability, stage, external, external):
        raise CapabilityExecutionError("invocation identity differs from its compiled policy")
    context = validate_typed(decode(context_json))
    receipt = decode(receipt_json)
    if context_json != canonical(context) or receipt_json != canonical(receipt):
        raise CapabilityExecutionError("invocation context and receipt must use canonical serialization")
    if not isinstance(receipt, dict) or not isinstance(receipt.get("role_paths"), dict) or not receipt.get("source_digest"):
        raise CapabilityExecutionError("invocation receipt must name its context identity and role paths")
    if not invocation_id or not Path(workspace).is_absolute():
        raise CapabilityExecutionError("an invocation needs a host-issued identity and an absolute workspace")
    payload = {"capability": capability, "stage": stage, "agent": name, "invocation_id": invocation_id,
               "workspace": workspace, "context": context, "receipt": receipt, "policy_digest": policy.digest,
               "binding": decode(binding_json), "instructions_digest": _digest(instructions),
               "selection": selection.wire(),
               "child_selections": [[child, value.wire()] for child, value in child_selections]}
    return WorkerInvocation(capability=capability, stage=stage, agent=name, invocation_id=invocation_id,
                            workspace=workspace, context_json=context_json, receipt_json=receipt_json,
                            policy=policy, binding_json=binding_json, instructions=instructions,
                            selection=selection, child_selections=tuple(child_selections), digest=_digest(payload))


def _child_text(definition: worker_profile.ChildDefinition, selection: WorkerSelection | None) -> str:
    extra = "".join(f"{key}: {value}\n" for key, value in (("model", selection and selection.model),
                                                           ("thinking", selection and selection.thinking)) if value)
    return definition.text.replace("---\n", "---\n" + extra, 1) if extra else definition.text


@dataclass(frozen=True)
class WorkerExecutor:
    """Runs verified worker invocations; ``runtime`` is the trusted Pi worker runtime or a test double."""

    package_root: Path = PACKAGE_ROOT
    runtime: Callable[..., Any] | None = None

    def preflight(self, invocation: WorkerInvocation) -> tuple[worker_profile.WorkerProfile, worker_profile.WorkerBinding, dict]:
        from ..spec.typed_data import decode

        try:
            binding = worker_profile.binding_from_json(invocation.binding_json)
        except (TypeError, ValueError, KeyError) as error:
            raise CapabilityExecutionError(f"invocation carries a malformed WorkerProfile binding: {error}") from error
        if worker_profile.binding_digest(binding) != binding.digest or binding.agent != invocation.agent:
            raise CapabilityExecutionError("invocation WorkerProfile binding does not match its own digest or WorkerProfile")
        try:
            current = worker_profile.resolve_worker(self.package_root, binding.agent)
        except ValueError as error:
            raise CapabilityExecutionError(f"WorkerProfile binding cannot be resolved: {error}", code=getattr(error, "code", None)) from error
        if current != binding:
            raise CapabilityExecutionError("WorkerProfile binding differs from the current build")
        agent = worker_profile.worker_profile(binding.agent)
        context = decode(invocation.context_json)
        data = context["data"]
        snapshot = data.get("snapshot", {}).get("data", data)
        rendered = (Path(self.package_root) / binding.instructions_path).read_text(encoding="utf-8")
        protocol = []
        for record in snapshot["protocol"]:
            path = Path(invocation.workspace) / record["path"]
            raw = path.read_bytes() if path.is_file() and not path.is_symlink() else b""
            if "sha256:" + hashlib.sha256(raw).hexdigest() != record["digest"]:
                raise CapabilityExecutionError(f"granted Protocol file is missing or changed: {record['path']}")
            protocol.append((record["path"], raw))
        if invocation.instructions != worker_instructions(rendered, protocol):
            raise CapabilityExecutionError("worker instructions differ from the rendered worker and its Protocol files")
        if snapshot.get("instructions") != rendered:
            raise CapabilityExecutionError("context instructions differ from the rendered worker instructions")
        try:
            worker_profile.validate_worker_input(agent, context, phase=invocation.stage)
            worker_profile.validate_worker_policy(agent, context, invocation.policy, json.loads(invocation.receipt_json))
        except (ValueError, KeyError, TypeError) as error:
            raise CapabilityExecutionError(f"contract admission failed: {error}") from error
        effects = agent.contract.effects
        if invocation.policy.write_paths and not effects.writes:
            raise CapabilityExecutionError("invocation grants writes the WorkerProfile contract does not declare")
        if invocation.policy.network_enabled or invocation.policy.credentials != "none":
            raise CapabilityExecutionError("worker invocations never grant network or credential effects")
        return agent, binding, context

    def __call__(self, invocation: WorkerInvocation, *, checks: Callable[[], Any] | None = None,
                 report_issue=None) -> WorkerOutcome:
        from ..spec.typed_data import TypedDataError, typed

        agent, binding, _ = self.preflight(invocation)
        definitions = worker_profile.child_definitions(self.package_root, agent)
        selections = dict(invocation.child_selections)
        children = tuple(ChildAgent(item.name, _child_text(item, selections.get(item.name))) for item in definitions)
        child_tools = tuple(sorted({tool for item in definitions for tool in item.tools}))
        tools = (*agent.tools, "submit_result", *(("report_issue",) if report_issue is not None else ()),
                 *(("subagent",) if agent.children else ()))
        read_paths = invocation.policy.read_paths + (("." ,) if agent.workspace == "capsule" else ())
        launch = WorkerLaunch(
            worker=agent.name, workspace=invocation.workspace, system_prompt=invocation.instructions,
            message=invocation.context_json, result_schema=result_parameters(agent.contract.result),
            tools=tools, read_paths=read_paths, write_paths=invocation.policy.write_paths,
            children=children, child_tools=child_tools, model=invocation.selection.model,
            thinking=invocation.selection.thinking,
            timeout_seconds=invocation.selection.timeout_seconds or binding.timeout_seconds,
            report_schema=report_issue.schema if report_issue is not None else None)
        runtime = self.runtime or PiWorkerRuntime(Path(self.package_root))
        # The host check service is served only to a worker or child granted run_checks.
        if "run_checks" not in (*launch.tools, *launch.child_tools):
            checks = None
        try:
            services = {"report_issue": report_issue} if report_issue is not None else {}
            result = runtime(launch, checks=checks, **services)
        except WorkerExecutionError as error:
            raise CapabilityExecutionError(str(error), outcome=error.outcome) from error
        reported = result.usage
        usage = ExecutionUsage(model=invocation.selection.model, thinking=invocation.selection.thinking,
                               input_tokens=reported.get("input_tokens"),
                               cached_input_tokens=reported.get("cached_input_tokens"),
                               output_tokens=reported.get("output_tokens"), total_tokens=reported.get("total_tokens"),
                               cost_usd=reported.get("cost_usd"), turns=reported.get("turns"),
                               wall_seconds=reported.get("wall_seconds"),
                               prompt_bytes=len(invocation.instructions.encode("utf-8")),
                               context_bytes=len(invocation.context_json.encode("utf-8")))
        try:
            value = typed(agent.contract.result, result.value)
            worker_profile.validate_worker_output(agent, value)
        except worker_profile.ContractError as error:
            raise CapabilityExecutionError(f"invalid worker result: {error}", outcome=_INVALID,
                                           code=error.code, usage=usage) from error
        except TypedDataError as error:
            raise CapabilityExecutionError(f"invalid worker result: {error}", outcome=_INVALID, usage=usage) from error
        return WorkerOutcome(value=value, usage=usage, invocation_digest=invocation.digest, binding_digest=binding.digest)


_INVALID: Outcome = "invalid_completion"
