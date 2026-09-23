"""The Agent binding: one Agent definition, as built, bound to one Agent call.

``AgentDefinition`` is the record format every ``agents/<name>/`` package exports as
``DEFINITION``. ``bind_agent`` checks a definition's consistency, reads the build manifest as
contract.distribution.build-manifest defines it, requires the definition's instruction source to be
recorded there and its rendered instructions ``generated/native/<name>.md`` to exist, and returns the
reproducible ``AgentBinding`` a context snapshot records.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from ..spec.repository import SpecError
from .effects import EFFECT_ROLES

WORKSPACES = ("capsule", "project")
# Only non-delegating tools can be listed; a call adds report_issue and structured_output.
AGENT_TOOLS = frozenset(
    {"read", "grep", "find", "ls", "edit", "write", "bash", "run_checks"}
)
CONTEXT_RESULT_PAIRS = {
    f"concorde-{kind}-context": f"concorde-{kind}-result"
    for kind in ("agent-stage", "review-stage")
}
RESULT_FIELDS = ("documents", "plan", "tasks", "issue_decision")


class ContractError(ValueError):
    """A result violated its Agent definition; ``code`` keeps the Host's rejection class."""

    def __init__(self, message: str, code: str = "invalid_completion"):
        super().__init__(message)
        self.code = code
        self.field = ""


@dataclass(frozen=True)
class AgentDefinition:
    """One Agent's definition, as the Agents Module declares it."""

    name: str
    instructions: str
    workspace: str
    phase: str
    context: str
    result: str
    reads: tuple[str, ...]
    tools: tuple[str, ...]
    hook: str
    writes: tuple[str, ...] = ()
    network: bool = False
    credentials: str = "none"
    stage_inputs: tuple[str, ...] = ()
    required_inputs: tuple[str, ...] = ()
    output_fields: tuple[str, ...] = ()
    outcomes: tuple[str, ...] = ()
    timeout_seconds: int = 1800

    @property
    def reads_implementation(self) -> bool:
        return "implementation" in self.reads

    @property
    def writes_implementation(self) -> bool:
        return "implementation" in self.writes

    @property
    def effects(self) -> dict:
        return {
            "reads": list(self.reads),
            "writes": list(self.writes),
            "network": self.network,
            "credentials": self.credentials,
        }


@dataclass(frozen=True)
class AgentBinding:
    """The reproducible identity of one Agent definition bound against the current build."""

    agent: str
    spec_path: str
    spec_digest: str
    instructions_path: str
    instructions_digest: str
    definition_digest: str
    build_manifest_digest: str
    tools: tuple[str, ...]
    effects: dict
    workspace: str
    timeout_seconds: int
    digest: str

    def record(self) -> dict:
        """The binding as the snapshot's ``agent_binding`` field."""
        value = dataclasses.asdict(self)
        value["tools"] = list(self.tools)
        return value


def _invalid(message: str) -> SpecError:
    return SpecError(message, "invalid_agent_binding")


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def agent_key(name: str) -> str:
    """Normalize a ``concorde-`` prefixed, hyphenated or underscored Agent name."""
    return name.removeprefix("concorde-").replace("-", "_")


def validate_definition(definition: AgentDefinition) -> None:
    """Refuse a definition whose fields are inconsistent with each other."""
    name = definition.name
    if not isinstance(definition, AgentDefinition):
        raise _invalid(f"agent {name!r} does not export an AgentDefinition")
    if definition.instructions != f"agents/{name}/spec.md":
        raise _invalid(f"agent {name!r} must name instructions agents/{name}/spec.md")
    if definition.workspace not in WORKSPACES:
        raise _invalid(
            f"agent {name!r} has an unknown workspace {definition.workspace!r}"
        )
    if CONTEXT_RESULT_PAIRS.get(definition.context) != definition.result:
        raise _invalid(
            f"agent {name!r} pairs context {definition.context} with result {definition.result}"
        )
    if not definition.phase:
        raise _invalid(f"agent {name!r} names no phase")
    if set(definition.required_inputs) - set(definition.stage_inputs):
        raise _invalid(f"agent {name!r} requires stage inputs it does not admit")
    if len(set(definition.stage_inputs)) != len(definition.stage_inputs):
        raise _invalid(f"agent {name!r} lists a stage input twice")
    if set(definition.output_fields) - set(RESULT_FIELDS):
        raise _invalid(f"agent {name!r} names unknown result fields")
    if set(definition.reads) - EFFECT_ROLES or set(definition.writes) - EFFECT_ROLES:
        raise _invalid(f"agent {name!r} declares an unknown effect role")
    if set(definition.writes) - set(definition.reads):
        raise _invalid(f"agent {name!r} writes a role it cannot read")
    if definition.network or definition.credentials != "none":
        raise _invalid(f"agent {name!r} may not declare network or credential effects")
    if definition.reads_implementation and definition.workspace != "project":
        raise _invalid(
            f"agent {name!r} reads implementation files outside a project workspace"
        )
    tools = set(definition.tools)
    if len(tools) != len(definition.tools) or tools - AGENT_TOOLS:
        raise _invalid(f"agent {name!r} declares duplicate or unknown tools")
    if tools & {"edit", "write", "bash"} and not definition.writes:
        raise _invalid(
            f"agent {name!r} lists edit, write or bash without implementation writes"
        )
    if "read" not in tools:
        raise _invalid(f"agent {name!r} must be able to read its context")
    if type(definition.timeout_seconds) is not int or definition.timeout_seconds <= 0:
        raise _invalid(f"agent {name!r} needs a positive integer timeout")
    module_name, separator, attribute = definition.hook.partition(":")
    if not separator or not module_name or not attribute:
        raise _invalid(f"agent {name!r} names no module:attribute hook")


def _inventory():
    """The ``agents`` package of the package root this module belongs to."""
    import sys

    root = str(Path(__file__).resolve().parents[3])
    if root not in sys.path:
        sys.path.append(root)
    import agents

    return agents


def agent_names() -> tuple[str, ...]:
    """The Agents of the Agents inventory."""
    return tuple(_inventory().AGENTS)


def agent_definition(name: str) -> AgentDefinition:
    """The checked definition of one Agent, or ``unknown_agent``."""
    agents = _inventory()
    key = agent_key(name)
    if key not in agents.AGENTS:
        raise SpecError(f"unknown agent: {name!r}", "unknown_agent")
    definition = agents.definition(key)
    validate_definition(definition)
    return definition


def phase_agent(phase: str) -> AgentDefinition:
    """The Agent whose definition names ``phase``, or ``invalid_phase``."""
    for name in agent_names():
        definition = agent_definition(name)
        if definition.phase == phase:
            return definition
    raise SpecError(f"no Agent performs phase {phase!r}", "invalid_phase")


def phases() -> frozenset[str]:
    """Every phase an Agent definition names."""
    return frozenset(agent_definition(name).phase for name in agent_names())


def rendered_instructions(name: str) -> str:
    """The project-relative path of an Agent's rendered instructions."""
    return f"generated/native/{agent_key(name).replace('_', '-')}.md"


def bind_agent(package_root: str | Path, name: str) -> AgentBinding:
    """Bind one Agent definition to the current build, failing closed.

    ``stale_build`` when the build manifest says the build is not fresh or the rendered
    instructions are missing, ``unknown_agent`` for an unrecognized name, and
    ``invalid_agent_binding`` for an inconsistent definition or an instruction source the manifest
    does not record.
    """
    from .admission import verify_build

    root = Path(package_root)
    definition = agent_definition(name)
    manifest, manifest_digest = verify_build(root)
    source = root / definition.instructions
    if source.is_symlink() or not source.is_file():
        raise _invalid(f"agent {definition.name!r} instructions are missing")
    spec_digest = _sha256(source.read_bytes())
    if manifest["sources"].get(definition.instructions) != spec_digest:
        raise _invalid(
            f"agent {definition.name!r} instructions are not recorded in the build manifest"
        )
    instructions_path = rendered_instructions(definition.name)
    rendered = root / instructions_path
    if rendered.is_symlink() or not rendered.is_file():
        raise SpecError(
            f"no rendered instructions for agent {definition.name!r}; run the build",
            "stale_build",
        )
    fields = {
        "agent": definition.name,
        "spec_path": definition.instructions,
        "spec_digest": spec_digest,
        "instructions_path": instructions_path,
        "instructions_digest": _sha256(rendered.read_bytes()),
        "definition_digest": _sha256(_canonical(dataclasses.asdict(definition))),
        "build_manifest_digest": manifest_digest,
        "tools": list(definition.tools),
        "effects": definition.effects,
        "workspace": definition.workspace,
        "timeout_seconds": definition.timeout_seconds,
    }
    return AgentBinding(
        **{**fields, "tools": tuple(definition.tools)},
        digest=_sha256(_canonical(fields)),
    )


def binding_from_record(record: dict) -> AgentBinding:
    """The ``AgentBinding`` a snapshot's ``agent_binding`` field records."""
    return AgentBinding(**{**record, "tools": tuple(record["tools"])})


def load_instructions(package_root: str | Path, binding: AgentBinding) -> str:
    """The rendered instructions of a binding, refused when their bytes no longer match."""
    raw = (Path(package_root) / binding.instructions_path).read_bytes()
    if _sha256(raw) != binding.instructions_digest:
        raise SpecError("rendered Agent instructions changed", "stale_context")
    return raw.decode("utf-8")


def validate_stage_inputs(
    definition: AgentDefinition, inputs, *, require_all: bool = True
) -> None:
    """Admit only the stage input types the definition lists, one per type."""
    types = [item.get("type_id") for item in inputs]
    if len(types) != len(set(types)) or set(types) - set(definition.stage_inputs):
        raise SpecError(
            f"stage inputs do not match the {definition.name} definition",
            "incompatible_handoff",
        )
    if require_all and set(definition.required_inputs) - set(types):
        raise SpecError(
            f"stage inputs miss a type the {definition.name} definition requires",
            "incompatible_handoff",
        )


def validate_agent_input(definition: AgentDefinition, value: dict) -> None:
    """Check an Agent's typed input against its definition, independently of prompt text."""
    from ..spec.typed_data import validate_typed

    validate_typed(value, definition.context)
    data = value["data"]
    snapshot = data.get("snapshot", {}).get("data", data)
    if snapshot.get("phase") != definition.phase:
        raise ValueError("snapshot phase does not match the definition")
    try:
        validate_stage_inputs(definition, snapshot.get("stage_inputs", []))
    except SpecError as error:
        raise ValueError(str(error)) from error
    if not definition.reads_implementation and snapshot.get("implementation_artifacts"):
        raise ValueError(f"{definition.name} cannot admit implementation contents")
    if definition.context == "concorde-review-stage-context":
        review = data["review"]["data"]
        if review["review_mode"] != definition.phase.split("-")[0]:
            raise ValueError("review input does not match the definition")
        if definition.phase == "spec-review" and any(
            change["path"]
            not in [source["path"] for source in snapshot["spec_resolution"]["sources"]]
            for change in review["changes"]
        ):
            raise ValueError("a Spec review cannot admit implementation patches")
    if data.get("expected_artifacts"):
        raise ValueError("no Agent admits extra expected artifact paths")


def validate_agent_result(definition: AgentDefinition, value: dict) -> None:
    """Check an Agent's typed result against the fields and outcomes its definition permits."""
    from ..spec.typed_data import validate_typed

    data = validate_typed(value, definition.result)["data"]
    if definition.outcomes and data.get("outcome") not in definition.outcomes:
        raise ContractError(
            f"result outcome does not match the {definition.name} definition"
        )
    for field in RESULT_FIELDS:
        if field not in definition.output_fields and data.get(field):
            message = (
                f"{definition.name} cannot author Spec documents"
                if field == "documents"
                else f"{definition.name} cannot return {field}"
            )
            raise ContractError(message, "permission_denied")
    if (
        definition.context == "concorde-review-stage-context"
        and data["review_mode"] != definition.phase.split("-")[0]
    ):
        raise ContractError("review result does not match the definition")
