"""Stable Agent responsibilities, Harness ceilings and explicit per-task Mode contracts.

Binds one Python module per named Agent (the top-level ``agents/`` package) to its authored Spec,
Harness reference and effective Constraints, and resolves that binding against the current build
(spec.md digest recorded in the build manifest, rendered instructions under ``generated/agents/``,
registered Harness, and every declared capability/context/result/effect) into an ``AgentBinding`` --
the reproducible identity the host and reviewers can inspect (A1, A4). ``roles.py`` projects this
inventory for backward compatibility; new code should use ``load_agents``/``agent_definition``/
``resolve_agent`` directly.

This module never imports ``build`` at module scope: ``build.py`` imports ``roles.py``, and
``roles.py`` now derives ``ROLES`` from ``load_agents()`` here, so a module-level import of
``build`` from here would cycle. Every function that needs ``build.BuildError`` or
``build.verify_fresh`` imports ``build`` lazily inside its own body instead.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .effects import EffectDeclaration
from .harness import HARNESSES, Harness, LoopPolicy


class ModeContractError(ValueError):
    """A bounded result violated the selected mode, preserving Host rejection semantics."""

    def __init__(self, message: str, code: str = "invalid_completion"):
        super().__init__(message)
        self.code = code
        self.field = ""


@dataclass(frozen=True)
class Constraints:
    """An Agent ceiling or Mode restriction, always beneath the enclosing authority."""

    effects: EffectDeclaration
    capabilities: tuple[str, ...] = ()
    contexts: tuple[str, ...] = ()
    results: tuple[str, ...] = ()
    limits: LoopPolicy | None = None
    allow_delegation: bool = False


@dataclass(frozen=True)
class Mode:
    """One task contract; all authority is bounded by the owning Agent ceiling."""

    name: str
    instructions: str
    constraints: Constraints
    phase: str
    action: str | None = None
    stage_inputs: tuple[str, ...] = ()
    required_inputs: tuple[str, ...] = ()
    output_fields: tuple[str, ...] = ()
    outcomes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Agent:
    """One capability boundary: common responsibility, Harness, authority ceiling and modes."""

    name: str
    spec: str
    harness: Harness
    constraints: Constraints
    modes: tuple[Mode, ...] = ()


@dataclass(frozen=True)
class AgentBinding:
    """The reproducible identity of one resolved Agent definition (A1, A4)."""

    agent: str
    spec_path: str
    spec_digest: str
    instructions_path: str
    instructions_digest: str
    harness: str
    harness_digest: str
    constraints_digest: str
    build_manifest_digest: str
    effective_loop: LoopPolicy
    digest: str
    mode: str | None = None
    mode_digest: str | None = None


def mode_definition(agent: Agent, name: str) -> Mode:
    from ..distribution.build import BuildError

    matches = [mode for mode in agent.modes if mode.name == name]
    if len(matches) != 1:
        raise BuildError(f"unknown or ambiguous mode {agent.name}/{name}", "invalid_agent_binding")
    mode = matches[0]
    ceiling, actual = agent.constraints, mode.constraints
    for field in ("contexts", "results", "capabilities"):
        if set(getattr(actual, field)) - set(getattr(ceiling, field)):
            raise BuildError(f"mode widens Agent {field}", "invalid_agent_binding")
    if (set(actual.effects.reads) - set(ceiling.effects.reads)
            or set(actual.effects.writes) - set(ceiling.effects.writes)
            or actual.effects.network and not ceiling.effects.network
            or actual.effects.credentials == "declared" and ceiling.effects.credentials != "declared"
            or actual.allow_delegation and not ceiling.allow_delegation):
        raise BuildError("mode widens Agent authority", "invalid_agent_binding")
    limit = _narrow_loop(agent.harness.loop, ceiling.limits)
    if actual.limits and (actual.limits.timeout_seconds > limit.timeout_seconds
            or limit.max_turns is not None and actual.limits.max_turns is not None
                and actual.limits.max_turns > limit.max_turns):
        raise BuildError("mode widens Agent loop limits", "invalid_agent_binding")
    if (len(actual.contexts) != 1 or len(actual.results) != 1
            or set(mode.required_inputs) - set(mode.stage_inputs)
            or mode.instructions != f"agents/{agent.name}/modes/{mode.name}.md"):
        raise BuildError("invalid mode contract", "invalid_agent_binding")
    pairs = {f"concorde-{kind}-context": f"concorde-{kind}-result"
             for kind in ("agent-stage", "review-stage", "main-stage", "topology-author")}
    if pairs.get(actual.contexts[0]) != actual.results[0]:
        raise BuildError("mode context/result pair is incompatible", "invalid_agent_binding")
    return mode


def _narrow_loop(parent: LoopPolicy, limits: LoopPolicy | None) -> LoopPolicy:
    if limits is None:
        return parent
    turns = [value for value in (parent.max_turns, limits.max_turns) if value is not None]
    return LoopPolicy(min(parent.timeout_seconds, limits.timeout_seconds), min(turns) if turns else None)


def effective_mode_loop(agent: Agent, mode: Mode) -> LoopPolicy:
    return _narrow_loop(_narrow_loop(agent.harness.loop, agent.constraints.limits), mode.constraints.limits)


def validate_mode_input(agent: Agent, mode_name: str, value: dict, *, phase: str) -> Mode:
    """Validate admitted cognition independently of prompt text and caller policy."""
    from ..spec.typed_data import validate_typed
    mode = mode_definition(agent, mode_name)
    validate_typed(value, mode.constraints.contexts[0])
    if phase != mode.phase:
        raise ValueError("launch phase does not match mode")
    data = value["data"]
    snapshot = data.get("snapshot", {}).get("data", data)
    if snapshot.get("phase", phase) != phase:
        raise ValueError("snapshot phase does not match mode")
    if mode.action is not None and snapshot.get("action") != mode.action:
        raise ValueError("discovery action does not match mode")
    validate_mode_artifacts(mode, snapshot.get("stage_inputs", []))
    if "implementation" not in mode.constraints.effects.reads and snapshot.get("implementation_artifacts"):
        raise ValueError("mode cannot admit implementation contents")
    if mode.name.endswith("-review") and data["review"]["data"]["review_mode"] != mode.name.split("-")[0]:
        raise ValueError("review input does not match mode")
    if mode.name == "spec-review" and any(change["path"] not in [source["path"] for source in snapshot["spec_resolution"]["sources"]]
            for change in data["review"]["data"]["changes"]):
        raise ValueError("Spec review cannot admit implementation patches")
    if data.get("expected_artifacts"):
        raise ValueError("current modes do not admit extra expected artifact paths")
    return mode


def validate_mode_artifacts(mode: Mode, inputs, *, require_all: bool = True) -> None:
    types = [item["type_id"] for item in inputs]
    if (len(types) != len(set(types)) or set(types) - set(mode.stage_inputs)
            or require_all and (set(mode.required_inputs) - set(types)
                or "concorde-task-scope-feedback" in types
                    and "concorde-implementation-task" not in types)):
        raise ValueError("stage inputs do not match mode")


def validate_mode_output(agent: Agent, mode_name: str, value: dict) -> None:
    from ..spec.typed_data import validate_typed
    mode = mode_definition(agent, mode_name)
    data = validate_typed(value, mode.constraints.results[0])["data"]
    if mode.outcomes and data.get("outcome") not in mode.outcomes:
        raise ModeContractError("result outcome does not match mode")
    for field in ("documents", "plan", "tasks", "reflection_findings", "routes", "topology_design"):
        if field not in mode.output_fields and data.get(field):
            message = "this mode cannot author Spec documents" if field == "documents" else f"mode cannot return {field}"
            raise ModeContractError(message, "permission_denied")
    if mode.name.endswith("-review") and data["review_mode"] != mode.name.split("-")[0]:
        raise ModeContractError("review result does not match mode")


def validate_mode_policy(mode: Mode, value: dict, policy, receipt: dict) -> None:
    """Recompile the concrete grant against mode effects, including code path membership."""
    from .permissions import PolicyBinding, compile_policy, verify_effective_subset
    role_paths = {key: tuple(paths) for key, paths in receipt["role_paths"].items()}
    context_role = "discovery-context" if mode.action is not None else "spec-context"
    capsule_paths = role_paths.get(context_role, ())
    if len(capsule_paths) != 1 or Path(capsule_paths[0]).name != "context.json":
        raise ValueError("mode requires exactly one frozen context capsule")
    snapshot = value["data"].get("snapshot", {}).get("data", value["data"])
    entries = [item["path"].rstrip("/") for item in snapshot.get("implementation_entries", [])]
    names = [item["path"] for item in snapshot.get("implementation_files", [])]
    directories = [item["path"] for item in snapshot.get("implementation_entries", []) if item["directory"]]
    artifacts = {item["path"] for item in snapshot.get("implementation_artifacts", [])}
    for path in role_paths.get("implementation", ()):
        if "implementation" not in mode.constraints.effects.reads:
            raise ValueError("mode cannot grant implementation reads")
        if not mode.constraints.effects.writes and path not in artifacts:
            raise ValueError("read-only mode grant exceeds the frozen implementation files")
        if path not in entries + names and not any(path.startswith(directory) for directory in directories):
            raise ValueError("implementation grant is outside the selected Module")
    bound = PolicyBinding(policy.capability, policy.stage, policy.occurrence, policy.role, policy.agent)
    ceiling = compile_policy(mode.constraints.effects, bound, role_paths)
    verify_effective_subset(ceiling, policy)


def agent_key(name: str) -> str:
    """Normalize an external (``concorde-spec-engineer``) or bare Agent name."""

    key = name[len("concorde-"):] if name.startswith("concorde-") else name
    return key.replace("-", "_")


def external_agent_name(name: str) -> str:
    """Return the ``concorde-<hyphenated>`` external identity for one bare agent name."""

    return "concorde-" + name.replace("_", "-")


def load_agent_inventory():
    """Import the repository-root ``agents`` package normally.

    Mirrors ``contracts.load_capability_inventory()``: puts the package root on ``sys.path`` (if
    not already there) and imports the top-level ``agents`` package by its real name, so it is
    safe to call from anywhere without depending on the current working directory.
    """

    import sys

    package_root = Path(__file__).resolve().parents[3]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
    import agents

    return agents


def load_agents() -> dict[str, Agent]:
    """Return ``{name: Agent}`` for every module named in ``agents.AGENTS``."""

    import importlib

    from ..distribution.build import BuildError

    inventory = load_agent_inventory()
    result: dict[str, Agent] = {}
    for name in inventory.AGENTS:
        module = importlib.import_module(f"{inventory.__name__}.{name}")
        agent = module.AGENT
        if not isinstance(agent, Agent) or agent.name != name:
            raise BuildError(f"agents.{name} does not declare AGENT with name={name!r}", "invalid_agent_binding")
        result[name] = agent
    return result


def agent_definition(name: str) -> Agent:
    """Look up one Agent by its external, hyphenated or underscored name."""

    from ..distribution.build import BuildError

    key = agent_key(name)
    agent = load_agents().get(key)
    if agent is None:
        raise BuildError(f"unknown agent: {name!r}", "unknown_agent")
    return agent


def canonical_binding(binding: AgentBinding) -> str:
    """Canonical (sorted-key, compact) JSON of ``dataclasses.asdict(binding)``, excluding its own
    ``digest`` field -- the same self-referential-digest pattern as ``harness.Harness.digest``."""

    payload = dataclasses.asdict(binding)
    payload.pop("digest", None)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def binding_digest(binding: AgentBinding) -> str:
    return "sha256:" + hashlib.sha256(canonical_binding(binding).encode("utf-8")).hexdigest()


def binding_json(binding: AgentBinding) -> str:
    """Canonical (sorted-key, compact) JSON of the complete resolved binding, INCLUDING its own
    ``digest`` field -- for embedding one launch's Agent identity into ``LaunchSpecification``.
    Unlike ``canonical_binding`` (which excludes ``digest`` because it is the digest's own input),
    this is the wire form a launch carries and the executor independently reverifies."""

    payload = dataclasses.asdict(binding)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def binding_from_json(text: str) -> AgentBinding:
    """Reconstruct one ``AgentBinding`` (with its nested ``LoopPolicy``) from ``binding_json``
    output. Raises ``TypeError``/``KeyError`` for a malformed payload; callers verify
    ``binding_digest(binding) == binding.digest`` separately to detect tampering."""

    payload = json.loads(text)
    loop_payload = payload["effective_loop"]
    return AgentBinding(**{**payload, "effective_loop": LoopPolicy(**loop_payload)})


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _sha256_json(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def mode_digest(mode: Mode) -> str:
    return _sha256_json(dataclasses.asdict(mode))


def constraints_digest(constraints: Constraints) -> str:
    return _sha256_json(dataclasses.asdict(constraints))


def resolve_agent(package_root: str | Path, name: str, mode: str | None = None) -> AgentBinding:
    """Resolve one named Agent's complete binding against the current build.

    Fails closed with ``BuildError``: ``stale_build`` when sources drifted since the last build or
    the rendered instructions are missing; ``unknown_agent`` for an unrecognized name;
    ``invalid_agent_binding`` for every other inconsistency between the Agent definition, its
    Harness, and the build manifest.
    """

    from ..spec import contracts
    from ..distribution.build import BuildError, verify_fresh

    root = Path(package_root)
    verify_fresh(root)

    agent = agent_definition(name)
    selected = mode_definition(agent, mode) if mode is not None else None
    for declared_mode in agent.modes:
        mode_definition(agent, declared_mode.name)

    expected_spec = f"agents/{agent.name}/spec.md"
    if agent.spec != expected_spec:
        raise BuildError(
            f"agent {agent.name!r} declares spec {agent.spec!r}, expected {expected_spec!r}",
            "invalid_agent_binding",
        )
    spec_path = root / agent.spec
    if spec_path.is_symlink() or not spec_path.is_file():
        raise BuildError(f"agent {agent.name!r} spec is missing: {agent.spec}", "invalid_agent_binding")
    spec_bytes = spec_path.read_bytes()
    spec_digest = _sha256_bytes(spec_bytes)

    manifest_path = root / "generated/build-manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    recorded_digest = manifest.get("sources", {}).get(agent.spec)
    if recorded_digest is None or recorded_digest != spec_digest:
        raise BuildError(
            f"agent {agent.name!r} spec is not recorded in the build manifest: {agent.spec}",
            "invalid_agent_binding",
        )
    build_manifest_digest = _sha256_bytes(manifest_bytes)

    declared_harness = agent.harness
    registered_harness = HARNESSES.get(declared_harness.name)
    if registered_harness is None or registered_harness.digest != declared_harness.digest:
        raise BuildError(
            f"agent {agent.name!r} references an unregistered harness: {declared_harness.name!r}",
            "invalid_agent_binding",
        )

    capability_names = {
        "concorde-" + module_name.replace("_", "-")
        for module_name in contracts.load_capability_inventory().CAPABILITIES
    }
    unknown_capabilities = sorted(set(agent.constraints.capabilities) - capability_names)
    if unknown_capabilities:
        raise BuildError(
            f"agent {agent.name!r} references unknown capabilities: {unknown_capabilities}",
            "invalid_agent_binding",
        )

    exported = set(contracts.exported_types())
    if type(agent.constraints.allow_delegation) is not bool or (agent.constraints.allow_delegation and (
            "concorde-agent-loop-context" not in agent.constraints.contexts
            or "concorde-agent-loop-step" not in agent.constraints.results)):
        raise BuildError("delegation requires the explicit host-loop contracts", "invalid_agent_binding")
    for field_name, declared_values in (
        ("contexts", agent.constraints.contexts),
        ("results", agent.constraints.results),
    ):
        unknown_types = sorted(set(declared_values) - exported)
        if unknown_types:
            raise BuildError(
                f"agent {agent.name!r} {field_name} reference unexported types: {unknown_types}",
                "invalid_agent_binding",
            )
        outside_harness = sorted(set(declared_values) - set(getattr(declared_harness, field_name)))
        if outside_harness:
            raise BuildError(
                f"agent {agent.name!r} {field_name} exceed its harness {declared_harness.name!r}: {outside_harness}",
                "invalid_agent_binding",
            )

    effects = agent.constraints.effects
    harness_effects = declared_harness.effects
    if (
        set(effects.reads) - set(harness_effects.reads)
        or set(effects.writes) - set(harness_effects.writes)
        or (effects.network and not harness_effects.network)
        or (effects.credentials == "declared" and harness_effects.credentials != "declared")
    ):
        raise BuildError(
            f"agent {agent.name!r} constraints widen its harness {declared_harness.name!r} effects",
            "invalid_agent_binding",
        )

    limits = agent.constraints.limits
    if limits is not None:
        if limits.timeout_seconds > declared_harness.loop.timeout_seconds:
            raise BuildError(
                f"agent {agent.name!r} limits exceed its harness {declared_harness.name!r} loop timeout",
                "invalid_agent_binding",
            )
        if (
            limits.max_turns is not None
            and declared_harness.loop.max_turns is not None
            and limits.max_turns > declared_harness.loop.max_turns
        ):
            raise BuildError(
                f"agent {agent.name!r} limits exceed its harness {declared_harness.name!r} loop max_turns",
                "invalid_agent_binding",
            )
        if declared_harness.loop.max_turns is None:
            effective_max_turns = limits.max_turns
        elif limits.max_turns is None:
            effective_max_turns = declared_harness.loop.max_turns
        else:
            effective_max_turns = min(limits.max_turns, declared_harness.loop.max_turns)
        effective_loop = LoopPolicy(
            timeout_seconds=min(limits.timeout_seconds, declared_harness.loop.timeout_seconds),
            max_turns=effective_max_turns,
        )
    else:
        effective_loop = declared_harness.loop

    hyphenated = agent.name.replace("_", "-")
    instructions_path = f"generated/agents/{hyphenated}.md"
    if selected:
        instructions_path = f"generated/agents/{hyphenated}/{selected.name}.md"
        if manifest.get("sources", {}).get(selected.instructions) != _sha256_bytes((root / selected.instructions).read_bytes()):
            raise BuildError("mode instructions are stale", "stale_build")
        effective_loop = effective_mode_loop(agent, selected)
    rendered_path = root / instructions_path
    if rendered_path.is_symlink() or not rendered_path.is_file():
        raise BuildError(
            f"no rendered instructions found for agent {agent.name!r}; run the build", "stale_build"
        )
    instructions_digest = _sha256_bytes(rendered_path.read_bytes())

    constraint_hash = constraints_digest(agent.constraints)

    binding = AgentBinding(
        agent=agent.name,
        spec_path=agent.spec,
        spec_digest=spec_digest,
        instructions_path=instructions_path,
        instructions_digest=instructions_digest,
        harness=declared_harness.name,
        harness_digest=declared_harness.digest,
        constraints_digest=constraint_hash,
        build_manifest_digest=build_manifest_digest,
        effective_loop=effective_loop,
        digest="",
        mode=mode,
        mode_digest=mode_digest(selected) if selected else None,
    )
    return dataclasses.replace(binding, digest=binding_digest(binding))
