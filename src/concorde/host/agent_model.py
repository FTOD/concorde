"""Agent = spec.md + Harness + Constraints/Permissions (workflow/agents-and-harnesses.md A1, A4).

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


@dataclass(frozen=True)
class Constraints:
    """Effective Constraints/Permissions for one Agent (A4): always a subset of its Harness."""

    effects: EffectDeclaration
    capabilities: tuple[str, ...] = ()
    contexts: tuple[str, ...] = ()
    results: tuple[str, ...] = ()
    limits: LoopPolicy | None = None


@dataclass(frozen=True)
class Agent:
    """One named Agent definition (A1): its authored Spec, Harness and effective Constraints."""

    name: str
    spec: str
    harness: Harness
    constraints: Constraints


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


def agent_key(name: str) -> str:
    """Normalize an external (``concorde-spec-author``) or bare (``spec-author``) agent name."""

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

    from .build import BuildError

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
    """Look up one Agent by its external (``concorde-spec-author``), hyphenated (``spec-author``)
    or underscored (``spec_author``) name."""

    from .build import BuildError

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


def resolve_agent(package_root: str | Path, name: str) -> AgentBinding:
    """Resolve one named Agent's complete binding against the current build.

    Fails closed with ``BuildError``: ``stale_build`` when sources drifted since the last build or
    the rendered instructions are missing; ``unknown_agent`` for an unrecognized name;
    ``invalid_agent_binding`` for every other inconsistency between the Agent definition, its
    Harness, and the build manifest.
    """

    from . import contracts
    from .build import BuildError, verify_fresh

    root = Path(package_root)
    verify_fresh(root)

    agent = agent_definition(name)

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
    rendered_path = root / instructions_path
    if rendered_path.is_symlink() or not rendered_path.is_file():
        raise BuildError(
            f"no rendered instructions found for agent {agent.name!r}; run the build", "stale_build"
        )
    instructions_digest = _sha256_bytes(rendered_path.read_bytes())

    constraints_digest = _sha256_json(dataclasses.asdict(agent.constraints))

    binding = AgentBinding(
        agent=agent.name,
        spec_path=agent.spec,
        spec_digest=spec_digest,
        instructions_path=instructions_path,
        instructions_digest=instructions_digest,
        harness=declared_harness.name,
        harness_digest=declared_harness.digest,
        constraints_digest=constraints_digest,
        build_manifest_digest=build_manifest_digest,
        effective_loop=effective_loop,
        digest="",
    )
    return dataclasses.replace(binding, digest=binding_digest(binding))
