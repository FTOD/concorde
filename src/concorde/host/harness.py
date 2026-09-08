"""Harness identity and configuration for Concorde Agents (workflow/agents-and-harnesses.md A2).

A Harness is the organized execution environment supporting an Agent: its model integration,
available Capability references, Tool interfaces, admitted Skills, context assembly, control-loop
policy, state handling and required system environment (A2). This module owns the closed catalog
of Harnesses Concorde defines today (three) and the record shapes themselves. It imports only
``effects.py`` and the standard library, so it stays a leaf usable from ``agent_model.py``,
``build.py`` and ``roles.py`` without an import cycle.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass
from typing import Literal

from .effects import EffectDeclaration

SAFE_ENVIRONMENT: tuple[str, ...] = tuple(sorted(
    {
        "COMSPEC",
        "HOME",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "LOGNAME",
        "PATH",
        "PATHEXT",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "TMPDIR",
        "USER",
        "WINDIR",
    }
))


@dataclass(frozen=True)
class LoopPolicy:
    """Host-enforced control-loop limits for one invocation (A4).

    ``max_turns`` is a native turn limit only when attested by the integration; ``None`` means it
    is not attested. There is no retry field: failure never triggers an automatic retry, with the
    same or broader permissions (A4).
    """

    timeout_seconds: int
    max_turns: int | None = None

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("LoopPolicy.timeout_seconds must be > 0")
        if self.max_turns is not None and self.max_turns <= 0:
            raise ValueError("LoopPolicy.max_turns must be > 0 when attested")


@dataclass(frozen=True)
class Harness:
    """One named, inspectable execution environment (A2): identity plus exact configuration."""

    name: str
    model: Literal["project-configured"]
    integrations: tuple[str, ...]
    workspace: Literal["capsule", "project"]
    effects: EffectDeclaration
    capabilities: tuple[str, ...]
    tools: tuple[str, ...]
    skills: tuple[str, ...]
    contexts: tuple[str, ...]
    results: tuple[str, ...]
    loop: LoopPolicy
    state: str
    environment: tuple[str, ...]
    digest: str


def _canonical(value: object) -> object:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {key: _canonical(item) for key, item in dataclasses.asdict(value).items()}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, dict):
        return {key: _canonical(item) for key, item in value.items()}
    return value


def _sha256_json(payload: object) -> str:
    encoded = json.dumps(_canonical(payload), sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _sorted_unique(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if len(set(values)) != len(values):
        raise ValueError(f"Harness.{field_name} must not contain duplicates")
    return tuple(sorted(values))


def harness(
    *,
    name: str,
    workspace: Literal["capsule", "project"],
    effects: EffectDeclaration,
    contexts: tuple[str, ...],
    results: tuple[str, ...],
    loop: LoopPolicy,
    capabilities: tuple[str, ...] = (),
    tools: tuple[str, ...] = ("native.filesystem", "native.shell"),
    skills: tuple[str, ...] = (),
    integrations: tuple[str, ...] = ("codex", "claude"),
    state: str = "fresh-process; typed completion persisted by host",
    environment: tuple[str, ...] = SAFE_ENVIRONMENT,
) -> Harness:
    """Validate one Harness's fields (nonempty name, positive timeout, unique tuples) and compute
    its digest. Every tuple field is normalized to sorted order so the digest is deterministic
    regardless of call-site ordering."""

    if not name or not name.strip():
        raise ValueError("Harness.name must be non-empty")
    if workspace not in ("capsule", "project"):
        raise ValueError(f"Harness.workspace must be 'capsule' or 'project', got {workspace!r}")
    if not isinstance(loop, LoopPolicy):
        raise ValueError("Harness.loop must be a LoopPolicy")

    integrations = _sorted_unique(tuple(integrations), "integrations")
    capabilities = _sorted_unique(tuple(capabilities), "capabilities")
    tools = _sorted_unique(tuple(tools), "tools")
    skills = _sorted_unique(tuple(skills), "skills")
    contexts = _sorted_unique(tuple(contexts), "contexts")
    results = _sorted_unique(tuple(results), "results")
    environment = _sorted_unique(tuple(environment), "environment")

    digest = _sha256_json(
        {
            "name": name,
            "model": "project-configured",
            "integrations": integrations,
            "workspace": workspace,
            "effects": effects,
            "capabilities": capabilities,
            "tools": tools,
            "skills": skills,
            "contexts": contexts,
            "results": results,
            "loop": loop,
            "state": state,
            "environment": environment,
        }
    )
    return Harness(
        name=name,
        model="project-configured",
        integrations=integrations,
        workspace=workspace,
        effects=effects,
        capabilities=capabilities,
        tools=tools,
        skills=skills,
        contexts=contexts,
        results=results,
        loop=loop,
        state=state,
        environment=environment,
        digest=digest,
    )


DISCOVERY_CAPSULE = harness(
    name="discovery-capsule",
    workspace="capsule",
    effects=EffectDeclaration(("discovery-context",), (), False, "none"),
    contexts=("concorde-main-stage-context",),
    results=("concorde-main-stage-result",),
    loop=LoopPolicy(900),
)

SPEC_CAPSULE = harness(
    name="spec-capsule",
    workspace="capsule",
    effects=EffectDeclaration(("spec-context",), (), False, "none"),
    contexts=(
        "concorde-agent-stage-context",
        "concorde-review-stage-context",
        "concorde-topology-author-context",
    ),
    results=(
        "concorde-agent-stage-result",
        "concorde-review-stage-result",
        "concorde-topology-author-result",
    ),
    loop=LoopPolicy(1800),
)

IMPLEMENTATION_WORKSPACE = harness(
    name="implementation-workspace",
    workspace="project",
    effects=EffectDeclaration(("spec-context", "implementation"), ("implementation",), False, "none"),
    contexts=("concorde-agent-stage-context", "concorde-review-stage-context"),
    results=("concorde-agent-stage-result", "concorde-review-stage-result"),
    loop=LoopPolicy(3600),
)

HARNESSES: dict[str, Harness] = {
    one.name: one for one in (DISCOVERY_CAPSULE, SPEC_CAPSULE, IMPLEMENTATION_WORKSPACE)
}
