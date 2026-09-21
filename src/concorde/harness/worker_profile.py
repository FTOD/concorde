"""Canonical native Agent profiles and their byte-bound context/result contracts.

The WorkerProfile class name is a compatibility spelling. Roles are Agents, not private model-backed
LangGraph Operation aliases. Native transports narrow the profile to exact invocation tools/inputs.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .effects import EffectDeclaration

WORKSPACES = ("capsule", "project")
# Only non-delegating tools can be granted; the host adds submit_result.
WORKER_TOOLS = frozenset(
    {"read", "grep", "find", "ls", "edit", "write", "bash", "run_checks"}
)
CONTEXT_RESULT_PAIRS = {
    f"concorde-{kind}-context": f"concorde-{kind}-result"
    for kind in ("agent-stage", "review-stage")
}
RESULT_FIELDS = (
    "documents",
    "plan",
    "tasks",
    "issue_decision",
)


class ContractError(ValueError):
    """A result violated its WorkerProfile's contract; ``code`` preserves the host rejection class."""

    def __init__(self, message: str, code: str = "invalid_completion"):
        super().__init__(message)
        self.code = code
        self.field = ""


@dataclass(frozen=True)
class Contract:
    """Execution constraints for a model node's State input/output: phase, effects and artifacts."""

    phase: str
    context: str
    result: str
    effects: EffectDeclaration
    stage_inputs: tuple[str, ...] = ()
    required_inputs: tuple[str, ...] = ()
    output_fields: tuple[str, ...] = ()
    outcomes: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkerProfile:
    """One worker profile: role Spec, task contract, workspace, tools and timeout."""

    name: str
    spec: str
    workspace: Literal["capsule", "project"]
    contract: Contract
    tools: tuple[str, ...]
    timeout_seconds: int = 1800


@dataclass(frozen=True)
class WorkerBinding:
    """The reproducible identity of one resolved WorkerProfile against the current build."""

    agent: str
    spec_path: str
    spec_digest: str
    instructions_path: str
    instructions_digest: str
    profile_digest: str
    build_manifest_digest: str
    timeout_seconds: int
    digest: str


def _invalid(message: str):
    from ..distribution.build import BuildError

    return BuildError(message, "invalid_agent_binding")


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _sha256_json(payload: object) -> str:
    return _sha256_bytes(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def worker_key(name: str) -> str:
    """Normalize an external (``concorde-code-reviewer``), hyphenated or underscored WorkerProfile name."""
    key = name.removeprefix("concorde-")
    return key.replace("-", "_")


def external_worker_name(name: str) -> str:
    """The ``concorde-<hyphenated>`` identity of one bare WorkerProfile name."""
    return "concorde-" + name.replace("_", "-")


def validate_worker_profile(agent: WorkerProfile) -> None:
    """Reject a profile whose contract, workspace or tools are inconsistent."""
    contract = agent.contract
    if agent.spec != f"operations/{agent.name}/spec.md":
        raise _invalid(
            f"agent {agent.name!r} must declare spec operations/{agent.name}/spec.md"
        )
    if agent.workspace not in WORKSPACES:
        raise _invalid(
            f"agent {agent.name!r} has an unknown workspace {agent.workspace!r}"
        )
    if CONTEXT_RESULT_PAIRS.get(contract.context) != contract.result:
        raise _invalid(
            f"agent {agent.name!r} pairs context {contract.context} with result {contract.result}"
        )
    if set(contract.required_inputs) - set(contract.stage_inputs):
        raise _invalid(f"agent {agent.name!r} requires stage inputs it does not admit")
    if set(contract.output_fields) - set(RESULT_FIELDS):
        raise _invalid(f"agent {agent.name!r} names unknown result fields")
    effects = contract.effects
    if set(effects.writes) - set(effects.reads):
        raise _invalid(f"agent {agent.name!r} writes a role it cannot read")
    if effects.network or effects.credentials != "none":
        raise _invalid(
            f"agent {agent.name!r} may not declare network or credential effects"
        )
    if "implementation" in effects.reads and agent.workspace != "project":
        raise _invalid(
            f"agent {agent.name!r} reads implementation files outside a project workspace"
        )
    tools = set(agent.tools)
    if len(tools) != len(agent.tools) or tools - WORKER_TOOLS:
        raise _invalid(f"agent {agent.name!r} declares duplicate or unknown tools")
    if tools & {"edit", "write"} and not effects.writes:
        raise _invalid(
            f"agent {agent.name!r} grants edit or write without a write effect"
        )
    if not {"read"} <= tools:
        raise _invalid(f"agent {agent.name!r} must be able to read its context")
    if type(agent.timeout_seconds) is not int or agent.timeout_seconds <= 0:
        raise _invalid(f"agent {agent.name!r} needs a positive integer timeout")


def load_worker_profiles() -> dict[str, WorkerProfile]:
    """Derive optional worker execution profiles from the single Operation inventory."""
    import importlib

    import operations

    result: dict[str, WorkerProfile] = {}
    for name in operations.AGENTS:
        profile = importlib.import_module(f"operations.{name}").PROFILE
        if profile is None:
            continue
        if not isinstance(profile, WorkerProfile) or profile.name != name:
            raise _invalid(
                f"operations.{name} does not declare PROFILE with name={name!r}"
            )
        result[name] = profile
    return result


def worker_profile(name: str) -> WorkerProfile:
    """Look up one WorkerProfile by its external, hyphenated or underscored name."""
    agent = load_worker_profiles().get(worker_key(name))
    if agent is None:
        from ..distribution.build import BuildError

        raise BuildError(f"unknown agent: {name!r}", "unknown_agent")
    return agent


def validate_worker_artifacts(
    agent: WorkerProfile, inputs, *, require_all: bool = True
) -> None:
    contract = agent.contract
    types = [item["type_id"] for item in inputs]
    allowed = set(contract.stage_inputs) | {"concorde-issue-intent"}
    if "concorde-review-result" in types:
        allowed.add("concorde-issue-context")
    if (
        len(types) != len(set(types))
        or set(types) - allowed
        or require_all
        and (
            set(contract.required_inputs) - set(types)
            or "concorde-task-scope-feedback" in types
            and "concorde-implementation-task" not in types
        )
    ):
        raise ValueError(f"stage inputs do not match the {agent.name} contract")


def validate_worker_input(agent: WorkerProfile, value: dict, *, phase: str) -> None:
    """Check an admitted context against the WorkerProfile's contract, independently of prompt text."""
    from ..spec.typed_data import validate_typed

    contract = agent.contract
    validate_typed(value, contract.context)
    if phase != contract.phase:
        raise ValueError(f"launch phase does not match the {agent.name} contract")
    data = value["data"]
    snapshot = data.get("snapshot", {}).get("data", data)
    if snapshot.get("phase", phase) != phase:
        raise ValueError("snapshot phase does not match the contract")
    validate_worker_artifacts(agent, snapshot.get("stage_inputs", []))
    if "implementation" not in contract.effects.reads and snapshot.get(
        "implementation_artifacts"
    ):
        raise ValueError("this WorkerProfile cannot admit implementation contents")
    if contract.context == "concorde-review-stage-context":
        review = data["review"]["data"]
        if review["review_mode"] != contract.phase.split("-")[0]:
            raise ValueError("review input does not match the contract")
        if contract.phase == "spec-review" and any(
            change["path"]
            not in [source["path"] for source in snapshot["spec_resolution"]["sources"]]
            for change in review["changes"]
        ):
            raise ValueError("a Spec review cannot admit implementation patches")
    if data.get("expected_artifacts"):
        raise ValueError("no WorkerProfile admits extra expected artifact paths")


def validate_worker_output(agent: WorkerProfile, value: dict) -> None:
    from ..spec.typed_data import validate_typed

    contract = agent.contract
    data = validate_typed(value, contract.result)["data"]
    if contract.outcomes and data.get("outcome") not in contract.outcomes:
        raise ContractError(f"result outcome does not match the {agent.name} contract")
    for field in RESULT_FIELDS:
        if field not in contract.output_fields and data.get(field):
            message = (
                "this WorkerProfile cannot author Spec documents"
                if field == "documents"
                else f"this WorkerProfile cannot return {field}"
            )
            raise ContractError(message, "permission_denied")
    if (
        contract.context == "concorde-review-stage-context"
        and data["review_mode"] != contract.phase.split("-")[0]
    ):
        raise ContractError("review result does not match the contract")


def context_role(agent: WorkerProfile) -> str:
    """The read role that carries a worker's frozen context index and granted documents."""
    return "spec-context"


def validate_worker_policy(
    agent: WorkerProfile, value: dict, policy, receipt: dict
) -> None:
    """Recompile the concrete grant against the contract's effects, including code path membership."""
    from .context import context_grants
    from .permissions import PolicyBinding, compile_policy, verify_effective_subset

    contract = agent.contract
    role_paths = {key: tuple(paths) for key, paths in receipt["role_paths"].items()}
    capsule_paths = role_paths.get(context_role(agent), ())
    snapshot = value["data"].get("snapshot", {}).get("data", value["data"])
    indexes = [path for path in capsule_paths if Path(path).name == "context.json"]
    if len(indexes) != 1 or set(capsule_paths) - {indexes[0]} != set(
        context_grants(snapshot)
    ):
        raise ValueError(
            "a launch requires one frozen context index and the grant of exactly its listed files"
        )
    entries = [
        item["path"].rstrip("/") for item in snapshot.get("implementation_entries", [])
    ]
    names = [item["path"] for item in snapshot.get("implementation_files", [])]
    directories = [
        item["path"]
        for item in snapshot.get("implementation_entries", [])
        if item["directory"]
    ]
    artifacts = {item["path"] for item in snapshot.get("implementation_artifacts", [])}
    for path in role_paths.get("implementation", ()):
        if "implementation" not in contract.effects.reads:
            raise ValueError(
                "this WorkerProfile cannot be granted implementation reads"
            )
        if not contract.effects.writes and path not in artifacts:
            raise ValueError(
                "a read-only grant exceeds the frozen implementation files"
            )
        if path not in entries + names and not any(
            path.startswith(directory) for directory in directories
        ):
            raise ValueError("implementation grant is outside the selected Module")
    references = {
        item["path"].rstrip("/") for item in snapshot.get("external_references", [])
    }
    for path in role_paths.get("references", ()):
        if "references" not in contract.effects.reads:
            raise ValueError(
                "this WorkerProfile cannot be granted external reference reads"
            )
        if path not in references:
            raise ValueError(
                "reference grant exceeds the snapshot's external references"
            )
    bound = PolicyBinding(
        policy.operation, policy.stage, policy.occurrence, policy.role, policy.agent
    )
    verify_effective_subset(compile_policy(contract.effects, bound, role_paths), policy)


def profile_digest(package_root: str | Path, agent: WorkerProfile) -> str:
    """Identity of the terminal worker profile."""
    return _sha256_json({"agent": dataclasses.asdict(agent)})


def canonical_binding(binding: WorkerBinding) -> str:
    """Canonical JSON of the binding without its own digest, the digest's input."""
    payload = dataclasses.asdict(binding)
    payload.pop("digest", None)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def binding_digest(binding: WorkerBinding) -> str:
    return _sha256_bytes(canonical_binding(binding).encode("utf-8"))


def binding_json(binding: WorkerBinding) -> str:
    """Canonical JSON of the complete binding, digest included: the wire form a launch carries."""
    return json.dumps(
        dataclasses.asdict(binding), sort_keys=True, separators=(",", ":")
    )


def binding_from_json(text: str) -> WorkerBinding:
    try:
        return WorkerBinding(**json.loads(text))
    except (ValueError, TypeError) as error:
        raise ValueError("malformed WorkerProfile binding JSON") from error


def resolve_worker(package_root: str | Path, name: str) -> WorkerBinding:
    """Bind one WorkerProfile to the current build, failing closed with ``BuildError``.

    ``stale_build`` when sources drifted since the last build or the rendered instructions are
    missing, ``unknown_agent`` for an unrecognized name, ``invalid_agent_binding`` for an
    inconsistent profile.
    """
    from ..distribution.build import BuildError, verify_fresh

    root = Path(package_root)
    verify_fresh(root)
    agent = worker_profile(name)
    validate_worker_profile(agent)
    spec_path = root / agent.spec
    if spec_path.is_symlink() or not spec_path.is_file():
        raise _invalid(f"agent {agent.name!r} spec is missing: {agent.spec}")
    spec_digest = _sha256_bytes(spec_path.read_bytes())
    manifest_bytes = (root / "generated/build-manifest.json").read_bytes()
    try:
        sources = json.loads(manifest_bytes.decode("utf-8")).get("sources", {})
    except (ValueError, AttributeError) as error:
        raise BuildError("malformed build manifest", "stale_build") from error
    if sources.get(agent.spec) != spec_digest:
        raise _invalid(
            f"agent {agent.name!r} spec is not recorded in the build manifest: {agent.spec}"
        )
    instructions_path = f"generated/agents/{agent.name.replace('_', '-')}.md"
    rendered = root / instructions_path
    if rendered.is_symlink() or not rendered.is_file():
        raise BuildError(
            f"no rendered instructions found for agent {agent.name!r}; run the build",
            "stale_build",
        )
    binding = WorkerBinding(
        agent=agent.name,
        spec_path=agent.spec,
        spec_digest=spec_digest,
        instructions_path=instructions_path,
        instructions_digest=_sha256_bytes(rendered.read_bytes()),
        profile_digest=profile_digest(root, agent),
        build_manifest_digest=_sha256_bytes(manifest_bytes),
        timeout_seconds=agent.timeout_seconds,
        digest="",
    )
    return dataclasses.replace(binding, digest=binding_digest(binding))
