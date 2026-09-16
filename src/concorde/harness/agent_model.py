"""Concorde's Agent model: one Pi worker per task contract.

An Agent is one worker the host launches as a Pi process for one bounded task. Its definition is
the worker profile (workflow/agents-and-harnesses.md): the authored role Spec (``spec.md``), the
task contract it fulfils (the phase it runs in, the typed context it admits, the typed result it
submits, its effects on the project, the stage artifacts it admits and the result fields and
outcomes it may produce), its workspace kind, its Pi tools, its lightweight child agents and its
timeout. One Python module under the top-level ``agents/`` package declares each Agent. Children
are pi-subagents Markdown definitions under ``agents/<name>/children/``; they are not Agents and
carry no Concorde contract.

``resolve_agent`` binds an Agent to the current build into an ``AgentBinding``, the reproducible
identity a launch carries. This module never imports ``build`` at module scope, because ``build``
imports the Agent inventory from here; every function that needs it imports it lazily.
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
# The Pi tools a worker profile may grant. submit_result is granted to every worker and subagent to
# every worker with children; the host adds both, so a profile never lists them.
WORKER_TOOLS = frozenset({"read", "grep", "find", "ls", "edit", "write", "bash", "run_checks"})
# Children are read, search and check helpers: they never edit or write.
CHILD_TOOLS = frozenset({"read", "grep", "find", "ls", "bash", "run_checks"})
CONTEXT_RESULT_PAIRS = {f"concorde-{kind}-context": f"concorde-{kind}-result"
                        for kind in ("agent-stage", "review-stage", "main-stage", "topology-author")}
RESULT_FIELDS = ("documents", "plan", "tasks", "issue_decision", "routes", "topology_design")
_CHILD_SETTINGS = {"systemPromptMode": "replace", "inheritProjectContext": False,
                   "inheritGlobalContext": False, "inheritSkills": False}


class ContractError(ValueError):
    """A result violated its Agent's contract; ``code`` preserves the host rejection class."""

    def __init__(self, message: str, code: str = "invalid_completion"):
        super().__init__(message)
        self.code = code
        self.field = ""


@dataclass(frozen=True)
class Contract:
    """The one task an Agent fulfils: its phase, typed context and result, effects and artifacts."""

    phase: str
    context: str
    result: str
    effects: EffectDeclaration
    action: str | None = None
    stage_inputs: tuple[str, ...] = ()
    required_inputs: tuple[str, ...] = ()
    output_fields: tuple[str, ...] = ()
    outcomes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Child:
    """One lightweight child agent the worker may delegate to, defined by a Markdown file."""

    name: str
    definition: str


@dataclass(frozen=True)
class Agent:
    """One worker profile: role Spec, task contract, workspace, tools, children and timeout."""

    name: str
    spec: str
    workspace: Literal["capsule", "project"]
    contract: Contract
    tools: tuple[str, ...]
    children: tuple[Child, ...] = ()
    timeout_seconds: int = 1800


@dataclass(frozen=True)
class ChildDefinition:
    name: str
    description: str
    tools: tuple[str, ...]
    text: str


@dataclass(frozen=True)
class AgentBinding:
    """The reproducible identity of one resolved Agent against the current build."""

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
    return _sha256_bytes(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def agent_key(name: str) -> str:
    """Normalize an external (``concorde-code-reviewer``), hyphenated or underscored Agent name."""
    key = name[len("concorde-"):] if name.startswith("concorde-") else name
    return key.replace("-", "_")


def external_agent_name(name: str) -> str:
    """The ``concorde-<hyphenated>`` identity of one bare Agent name."""
    return "concorde-" + name.replace("_", "-")


def validate_agent(agent: Agent) -> None:
    """Reject a profile whose contract, workspace, tools or children are inconsistent."""
    contract = agent.contract
    if agent.spec != f"agents/{agent.name}/spec.md":
        raise _invalid(f"agent {agent.name!r} must declare spec agents/{agent.name}/spec.md")
    if agent.workspace not in WORKSPACES:
        raise _invalid(f"agent {agent.name!r} has an unknown workspace {agent.workspace!r}")
    if CONTEXT_RESULT_PAIRS.get(contract.context) != contract.result:
        raise _invalid(f"agent {agent.name!r} pairs context {contract.context} with result {contract.result}")
    if set(contract.required_inputs) - set(contract.stage_inputs):
        raise _invalid(f"agent {agent.name!r} requires stage inputs it does not admit")
    if set(contract.output_fields) - set(RESULT_FIELDS):
        raise _invalid(f"agent {agent.name!r} names unknown result fields")
    effects = contract.effects
    if set(effects.writes) - set(effects.reads):
        raise _invalid(f"agent {agent.name!r} writes a role it cannot read")
    if effects.network or effects.credentials != "none":
        raise _invalid(f"agent {agent.name!r} may not declare network or credential effects")
    if "implementation" in effects.reads and agent.workspace != "project":
        raise _invalid(f"agent {agent.name!r} reads implementation files outside a project workspace")
    if ("discovery-context" in effects.reads) != (contract.context == "concorde-main-stage-context"):
        raise _invalid(f"agent {agent.name!r} must read discovery context exactly for main-stage contexts")
    tools = set(agent.tools)
    if len(tools) != len(agent.tools) or tools - WORKER_TOOLS:
        raise _invalid(f"agent {agent.name!r} declares duplicate or unknown tools")
    if tools & {"edit", "write"} and not effects.writes:
        raise _invalid(f"agent {agent.name!r} grants edit or write without a write effect")
    if not {"read"} <= tools:
        raise _invalid(f"agent {agent.name!r} must be able to read its context")
    names = [child.name for child in agent.children]
    if len(names) != len(set(names)):
        raise _invalid(f"agent {agent.name!r} declares a child twice")
    for child in agent.children:
        if child.definition != f"agents/{agent.name}/children/{child.name}.md":
            raise _invalid(f"child {child.name!r} of {agent.name!r} must be defined at "
                           f"agents/{agent.name}/children/{child.name}.md")
    if type(agent.timeout_seconds) is not int or agent.timeout_seconds <= 0:
        raise _invalid(f"agent {agent.name!r} needs a positive integer timeout")


def child_definition(package_root: str | Path, agent: Agent, child: Child) -> ChildDefinition:
    """Parse and check one child's pi-subagents Markdown definition."""
    from ..spec.frontmatter import FrontMatterError, parse_document

    path = Path(package_root) / child.definition
    if path.is_symlink() or not path.is_file():
        raise _invalid(f"child definition is missing: {child.definition}")
    text = path.read_text(encoding="utf-8")
    try:
        metadata, body = parse_document(text, child.definition)
    except FrontMatterError as error:
        raise _invalid(str(error)) from error
    tools = tuple(item.strip() for item in str(metadata.get("tools") or "").split(",") if item.strip())
    if metadata.get("name") != child.name or not str(metadata.get("description") or "").strip() or not body.strip():
        raise _invalid(f"{child.definition} must declare name {child.name!r}, a description and a prompt")
    if not tools or len(set(tools)) != len(tools) or set(tools) - CHILD_TOOLS:
        raise _invalid(f"{child.definition} must list distinct tools from {sorted(CHILD_TOOLS)}")
    if "run_checks" in tools and agent.workspace != "project":
        raise _invalid(f"{child.definition} runs checks for a worker without a project workspace")
    if any(metadata.get(key) != value for key, value in _CHILD_SETTINGS.items()):
        raise _invalid(f"{child.definition} must set {_CHILD_SETTINGS}")
    if "model" in metadata or "thinking" in metadata:
        raise _invalid(f"{child.definition} leaves model and thinking to project configuration")
    return ChildDefinition(child.name, str(metadata["description"]), tools, text)


def child_definitions(package_root: str | Path, agent: Agent) -> tuple[ChildDefinition, ...]:
    return tuple(child_definition(package_root, agent, child) for child in agent.children)


def load_agent_inventory():
    """Import the package-root ``agents`` package by its real name."""
    import sys

    package_root = Path(__file__).resolve().parents[3]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
    import agents

    return agents


def load_agents() -> dict[str, Agent]:
    """``{name: Agent}`` for every module named in ``agents.AGENTS``."""
    import importlib

    inventory = load_agent_inventory()
    result: dict[str, Agent] = {}
    for name in inventory.AGENTS:
        agent = importlib.import_module(f"{inventory.__name__}.{name}").AGENT
        if not isinstance(agent, Agent) or agent.name != name:
            raise _invalid(f"agents.{name} does not declare AGENT with name={name!r}")
        result[name] = agent
    return result


def agent_definition(name: str) -> Agent:
    """Look up one Agent by its external, hyphenated or underscored name."""
    agent = load_agents().get(agent_key(name))
    if agent is None:
        from ..distribution.build import BuildError
        raise BuildError(f"unknown agent: {name!r}", "unknown_agent")
    return agent


def validate_agent_artifacts(agent: Agent, inputs, *, require_all: bool = True) -> None:
    contract = agent.contract
    types = [item["type_id"] for item in inputs]
    allowed = set(contract.stage_inputs) | {"concorde-issue-intent"}
    if "concorde-review-result" in types:
        allowed.add("concorde-issue-context")
    if (len(types) != len(set(types)) or set(types) - allowed
            or require_all and (set(contract.required_inputs) - set(types)
                or "concorde-task-scope-feedback" in types
                    and "concorde-implementation-task" not in types)):
        raise ValueError(f"stage inputs do not match the {agent.name} contract")


def validate_agent_input(agent: Agent, value: dict, *, phase: str) -> None:
    """Check an admitted context against the Agent's contract, independently of prompt text."""
    from ..spec.typed_data import validate_typed

    contract = agent.contract
    validate_typed(value, contract.context)
    if phase != contract.phase:
        raise ValueError(f"launch phase does not match the {agent.name} contract")
    data = value["data"]
    snapshot = data.get("snapshot", {}).get("data", data)
    if snapshot.get("phase", phase) != phase:
        raise ValueError("snapshot phase does not match the contract")
    if contract.action is not None and snapshot.get("action") != contract.action:
        raise ValueError("discovery action does not match the contract")
    validate_agent_artifacts(agent, snapshot.get("stage_inputs", []))
    if "implementation" not in contract.effects.reads and snapshot.get("implementation_artifacts"):
        raise ValueError("this Agent cannot admit implementation contents")
    if contract.context == "concorde-review-stage-context":
        review = data["review"]["data"]
        if review["review_mode"] != contract.phase.split("-")[0]:
            raise ValueError("review input does not match the contract")
        if contract.phase == "spec-review" and any(
                change["path"] not in [source["path"] for source in snapshot["spec_resolution"]["sources"]]
                for change in review["changes"]):
            raise ValueError("a Spec review cannot admit implementation patches")
    if data.get("expected_artifacts"):
        raise ValueError("no Agent admits extra expected artifact paths")


def validate_agent_output(agent: Agent, value: dict) -> None:
    from ..spec.typed_data import validate_typed

    contract = agent.contract
    data = validate_typed(value, contract.result)["data"]
    if contract.outcomes and data.get("outcome") not in contract.outcomes:
        raise ContractError(f"result outcome does not match the {agent.name} contract")
    for field in RESULT_FIELDS:
        if field not in contract.output_fields and data.get(field):
            message = ("this Agent cannot author Spec documents" if field == "documents"
                       else f"this Agent cannot return {field}")
            raise ContractError(message, "permission_denied")
    if contract.context == "concorde-review-stage-context" and data["review_mode"] != contract.phase.split("-")[0]:
        raise ContractError("review result does not match the contract")


def validate_agent_policy(agent: Agent, value: dict, policy, receipt: dict) -> None:
    """Recompile the concrete grant against the contract's effects, including code path membership."""
    from .context import context_grants
    from .permissions import PolicyBinding, compile_policy, verify_effective_subset

    contract = agent.contract
    role_paths = {key: tuple(paths) for key, paths in receipt["role_paths"].items()}
    context_role = "discovery-context" if contract.action is not None else "spec-context"
    capsule_paths = role_paths.get(context_role, ())
    snapshot = value["data"].get("snapshot", {}).get("data", value["data"])
    indexes = [path for path in capsule_paths if Path(path).name == "context.json"]
    if len(indexes) != 1 or set(capsule_paths) - {indexes[0]} != set(context_grants(snapshot)):
        raise ValueError("a launch requires one frozen context index and the grant of exactly its listed files")
    entries = [item["path"].rstrip("/") for item in snapshot.get("implementation_entries", [])]
    names = [item["path"] for item in snapshot.get("implementation_files", [])]
    directories = [item["path"] for item in snapshot.get("implementation_entries", []) if item["directory"]]
    artifacts = {item["path"] for item in snapshot.get("implementation_artifacts", [])}
    for path in role_paths.get("implementation", ()):
        if "implementation" not in contract.effects.reads:
            raise ValueError("this Agent cannot be granted implementation reads")
        if not contract.effects.writes and path not in artifacts:
            raise ValueError("a read-only grant exceeds the frozen implementation files")
        if path not in entries + names and not any(path.startswith(directory) for directory in directories):
            raise ValueError("implementation grant is outside the selected Module")
    references = {item["path"].rstrip("/") for item in snapshot.get("external_references", [])}
    for path in role_paths.get("references", ()):
        if "references" not in contract.effects.reads:
            raise ValueError("this Agent cannot be granted external reference reads")
        if path not in references:
            raise ValueError("reference grant exceeds the snapshot's external references")
    bound = PolicyBinding(policy.capability, policy.stage, policy.occurrence, policy.role, policy.agent)
    verify_effective_subset(compile_policy(contract.effects, bound, role_paths), policy)


def profile_digest(package_root: str | Path, agent: Agent) -> str:
    """Identity of the complete worker profile, including each child definition's bytes."""
    return _sha256_json({"agent": dataclasses.asdict(agent),
                         "children": {child.name: _sha256_bytes((Path(package_root) / child.definition).read_bytes())
                                      for child in agent.children}})


def canonical_binding(binding: AgentBinding) -> str:
    """Canonical JSON of the binding without its own digest, the digest's input."""
    payload = dataclasses.asdict(binding)
    payload.pop("digest", None)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def binding_digest(binding: AgentBinding) -> str:
    return _sha256_bytes(canonical_binding(binding).encode("utf-8"))


def binding_json(binding: AgentBinding) -> str:
    """Canonical JSON of the complete binding, digest included: the wire form a launch carries."""
    return json.dumps(dataclasses.asdict(binding), sort_keys=True, separators=(",", ":"))


def binding_from_json(text: str) -> AgentBinding:
    try:
        return AgentBinding(**json.loads(text))
    except (ValueError, TypeError) as error:
        raise ValueError("malformed Agent binding JSON") from error


def resolve_agent(package_root: str | Path, name: str) -> AgentBinding:
    """Bind one Agent to the current build, failing closed with ``BuildError``.

    ``stale_build`` when sources drifted since the last build or the rendered instructions are
    missing, ``unknown_agent`` for an unrecognized name, ``invalid_agent_binding`` for an
    inconsistent profile or child definition.
    """
    from ..distribution.build import BuildError, verify_fresh

    root = Path(package_root)
    verify_fresh(root)
    agent = agent_definition(name)
    validate_agent(agent)
    child_definitions(root, agent)
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
        raise _invalid(f"agent {agent.name!r} spec is not recorded in the build manifest: {agent.spec}")
    for child in agent.children:
        if sources.get(child.definition) != _sha256_bytes((root / child.definition).read_bytes()):
            raise BuildError(f"child definition is stale: {child.definition}", "stale_build")
    instructions_path = f"generated/agents/{agent.name.replace('_', '-')}.md"
    rendered = root / instructions_path
    if rendered.is_symlink() or not rendered.is_file():
        raise BuildError(f"no rendered instructions found for agent {agent.name!r}; run the build", "stale_build")
    binding = AgentBinding(agent=agent.name, spec_path=agent.spec, spec_digest=spec_digest,
                           instructions_path=instructions_path,
                           instructions_digest=_sha256_bytes(rendered.read_bytes()),
                           profile_digest=profile_digest(root, agent),
                           build_manifest_digest=_sha256_bytes(manifest_bytes),
                           timeout_seconds=agent.timeout_seconds, digest="")
    return dataclasses.replace(binding, digest=binding_digest(binding))
