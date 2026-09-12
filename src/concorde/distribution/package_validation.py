"""One package validator over prompts, capability modules, contracts, build outputs and Spec alignment.

Validates the current ``agents/``, ``capabilities/`` and ``skills/`` inventories and their
registered Spec declarations. Every finding carries a stable ``CONCORDE-…`` rule id.
"""

from __future__ import annotations

import ast
import importlib
import json
import re
from pathlib import Path

from ..spec.frontmatter import FrontMatterError, parse_document
from ..spec.model import Finding
from . import build
from ..harness.agent_model import Agent
from .build import BuildError, check_build, verify_fresh
from ..harness.harness import HARNESSES
from ..spec.typed_data import json_schema
from .prompt_resolver import (
    PromptResolverError,
    find_unreachable_prompts,
    resolve_agent_spec,
    resolve_role_prompt,
    resolve_skill_source,
)
from ..spec.contracts import INTERNAL_SKILLS, CAPABILITY_NAMES, MAIN_ROUTED_CAPABILITIES, exported_types, schemas

_SUBJECT = "module.distribution"

_NAME_TOKEN = re.compile(r"concorde-[a-z][a-z0-9-]*")

# Wire/Protocol vocabulary that legitimately appears as inline `concorde-…` prose terms but is not
# a skill name, a capability external name, or a member of contracts.schemas(): the two
# envelope type_ids validated ad hoc (never through DATA_SCHEMAS/schemas()), and two Protocol
# structural terms (a document ID prefix, a machine-readable participant block name) defined only
# in protocol/principles.md prose, not in any Python registry.
_PROTOCOL_VOCABULARY = frozenset(
    {
        "concorde-capability-invocation",
        "concorde-capability-configuration",
        "concorde-capability-result",
        "concorde-document",
        "concorde-dependencies",
        "concorde-entities",
        "concorde-contract",
        "concorde-contract-binding",
    }
)


def _finding(rule: str, source: str, message: str, remediation: str, *, severity: str = "error") -> Finding:
    return Finding(rule, severity, source, message, remediation, subject_id=_SUBJECT)


def _prompt_roots() -> tuple[str, ...]:
    return (tuple(build.SKILL_SOURCES.values()) + tuple(build.AGENT_ROOTS.values())
            + tuple(m.instructions for a in build.load_agents().values() for m in a.modes)
            + ("prompts/protocol/principles.md",)
            + tuple(f"prompts/protocol/kinds/{kind}.md" for kind in build.PROTOCOL_KINDS))


def _validate_prompts(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for relative in _prompt_roots():
        try:
            if relative.startswith("skills/"):
                resolve_skill_source(root, relative)
            elif relative.startswith("agents/"):
                resolve_agent_spec(root, relative)
            else:
                resolve_role_prompt(root, relative)
        except PromptResolverError as error:
            findings.append(_finding(error.rule_id, relative, str(error),
                "Repair the prompt source or its @include directives."))
    try:
        unreachable = find_unreachable_prompts(root, _prompt_roots())
    except PromptResolverError:
        # Already reported above as a resolver error against the same broken root; reachability
        # over a root that cannot even resolve would only duplicate that finding.
        unreachable = ()
    for relative in unreachable:
        findings.append(_finding(
            "CONCORDE-PROMPT-UNREACHABLE-001", relative,
            "No skill source, Agent Spec, or role root reaches this prompt file.",
            "Include it from a root, or delete the dead prompt text.",
        ))

    known = (
        frozenset(build.SKILL_NAMES)
        | frozenset(CAPABILITY_NAMES)
        | frozenset(INTERNAL_SKILLS)
        | frozenset(schemas())
        | _PROTOCOL_VOCABULARY
    )
    sources: list[str] = sorted(
        path.relative_to(root).as_posix()
        for path in (root / "prompts").rglob("*.md")
        if path.is_file() and not path.is_symlink()
    ) if (root / "prompts").is_dir() else []
    sources.extend(sorted(build.SKILL_SOURCES.values()))
    sources.extend(sorted(
        path.relative_to(root).as_posix()
        for path in (root / "agents").rglob("spec.md")
        if path.is_file() and not path.is_symlink()
    ) if (root / "agents").is_dir() else [])
    for relative in sources:
        path = root / relative
        if path.is_symlink() or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        for token in sorted(set(_NAME_TOKEN.findall(text))):
            if token not in known:
                findings.append(_finding(
                    "CONCORDE-PROMPT-NAME-001", relative,
                    f"'{token}' names no skill, capability, Agent, or exported type.",
                    "Correct the identifier, or export/declare it if it is genuinely new.",
                ))
    return findings


def _load_capabilities_package(root: Path):
    """Load ``<root>/capabilities/__init__.py`` under a fresh private module name.

    Root-parametrized, unlike ``contracts.load_capability_inventory()`` (which always
    loads the actual running checkout's package): this lets the validator check a temporary
    fixture package. A fresh unique name per call avoids any ``sys.modules`` collision between
    successive validations of different roots within one process, such as this module's own tests.
    """

    import sys
    import uuid
    from importlib.util import module_from_spec, spec_from_file_location

    init_path = root / "capabilities" / "__init__.py"
    if init_path.is_symlink() or not init_path.is_file():
        return None
    module_name = f"_concorde_package_validation_inventory_{uuid.uuid4().hex}"
    spec = spec_from_file_location(module_name, init_path, submodule_search_locations=[str(root / "capabilities")])
    if spec is None or spec.loader is None:
        return None
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _capability_modules(root: Path) -> tuple[object | None, dict[str, object]]:
    inventory = _load_capabilities_package(root)
    if inventory is None or not isinstance(getattr(inventory, "CAPABILITIES", None), tuple):
        return None, {}
    modules: dict[str, object] = {}
    for name in inventory.CAPABILITIES:
        try:
            modules[name] = importlib.import_module(f"{inventory.__name__}.{name}")
        except Exception:  # noqa: BLE001 - reported as a finding, not a crash
            modules[name] = None
    return inventory, modules


def _skill_capabilities(root: Path) -> dict[str, list[str]]:
    """Return {capability_module_name: [skill_name, ...]} from every skills/*/SKILL.md.

    Discovers whatever skill directories actually exist at ``root`` rather than assuming the
    real package's fixed public names, so a temporary fixture package with its own skill set is
    validated on its own terms.
    """

    result: dict[str, list[str]] = {}
    skills_root = root / "skills"
    if skills_root.is_symlink() or not skills_root.is_dir():
        return result
    for directory in sorted(skills_root.iterdir()):
        if directory.is_symlink() or not directory.is_dir():
            continue
        path = directory / "SKILL.md"
        if path.is_symlink() or not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        try:
            metadata, _ = parse_document(path.read_text(encoding="utf-8"), relative)
        except (OSError, UnicodeError, FrontMatterError):
            continue
        capability = metadata.get("capability")
        if isinstance(capability, str) and capability.strip():
            result.setdefault(capability.strip(), []).append(directory.name)
    return result


def _validate_capability_modules(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    inventory, modules = _capability_modules(root)
    if inventory is None:
        return [_finding("CONCORDE-CAPABILITY-INVENTORY-001", "capabilities/__init__.py",
            "capabilities/__init__.py is missing, unsafe, or declares no CAPABILITIES tuple.",
            "Add capabilities/__init__.py with an explicit CAPABILITIES inventory.")]

    declared = set(inventory.CAPABILITIES)
    actual = {
        path.stem
        for path in (Path(inventory.__file__).parent).glob("*.py")
        if path.stem != "__init__"
    }
    if declared != actual:
        findings.append(_finding(
            "CONCORDE-CAPABILITY-INVENTORY-001", "capabilities/__init__.py",
            f"Declared CAPABILITIES {sorted(declared)} differs from module files {sorted(actual)}.",
            "List exactly the capability module files in CAPABILITIES, one entry each.",
        ))

    skill_capabilities = _skill_capabilities(root)
    valid_modules: dict[str, object] = {}
    for name in sorted(declared):
        module = modules.get(name)
        source = f"capabilities/{name}.py"
        if module is None:
            findings.append(_finding("CONCORDE-CAPABILITY-CONSTANTS-001", source,
                f"capability module {name!r} could not be imported.",
                "Fix the import error in the capability module."))
            continue
        missing = [attribute for attribute in ("CLASS", "DETERMINISTIC", "AGENTS", "USES", "EXTERNAL_NAME", "REQUEST", "RESPONSE", "run")
                   if not hasattr(module, attribute)]
        if missing:
            findings.append(_finding("CONCORDE-CAPABILITY-CONSTANTS-001", source,
                f"capability module {name!r} is missing mandatory constants: {missing}.",
                "Declare CLASS, DETERMINISTIC, AGENTS, USES, EXTERNAL_NAME, REQUEST, RESPONSE and run()."))
            continue
        if (not isinstance(module.CLASS, str) or type(module.DETERMINISTIC) is not bool
                or not isinstance(module.AGENTS, tuple) or not isinstance(module.USES, tuple)
                or not all(isinstance(used, str) for used in module.USES)
                or not isinstance(module.EXTERNAL_NAME, str)
                or not isinstance(module.REQUEST, dict) or not isinstance(module.RESPONSE, dict)
                or not callable(module.run)):
            findings.append(_finding("CONCORDE-CAPABILITY-CONSTANTS-001", source,
                f"capability module {name!r} declares a mandatory constant with the wrong type.",
                "CLASS/EXTERNAL_NAME are str; DETERMINISTIC is bool; AGENTS is a tuple; USES is a tuple of str; REQUEST/RESPONSE are dict; run is callable."))
            continue
        valid_modules[name] = module
        if module.CLASS not in {"global", "lifecycle", "stage"}:
            findings.append(_finding("CONCORDE-CAPABILITY-CLASS-001", source,
                f"capability {name!r} declares CLASS {module.CLASS!r}.",
                "CLASS must be one of global, lifecycle, stage."))
        unknown_uses = sorted(set(module.USES) - declared)
        if unknown_uses:
            findings.append(_finding("CONCORDE-CAPABILITY-USES-001", source,
                f"capability {name!r} USES unknown capabilities: {unknown_uses}.",
                "Name only capabilities listed in capabilities.CAPABILITIES."))
        if not all(isinstance(agent, Agent) for agent in module.AGENTS):
            findings.append(_finding("CONCORDE-CAPABILITY-AGENTS-001", source,
                f"capability {name!r} AGENTS must contain only agent_model.Agent objects.",
                "Reference Agents by their AGENT constant, e.g. coordinator.AGENT."))
        expected_external = "concorde-" + name.replace("_", "-")
        if module.EXTERNAL_NAME != expected_external:
            findings.append(_finding("CONCORDE-CAPABILITY-EXTERNALNAME-001", source,
                f"capability {name!r} EXTERNAL_NAME is {module.EXTERNAL_NAME!r}, expected {expected_external!r}.",
                "EXTERNAL_NAME is always 'concorde-' plus the module name with underscores hyphenated."))
        skills = skill_capabilities.get(name, [])
        should_have_skill = module.CLASS in {"global", "lifecycle"}
        if should_have_skill and len(skills) != 1:
            findings.append(_finding("CONCORDE-CAPABILITY-SKILL-001", source,
                f"{module.CLASS} capability {name!r} must have exactly one skill naming it; found {skills}.",
                "Add or deduplicate the skills/<name>/SKILL.md declaring capability: " + name + "."))
        if not should_have_skill and skills:
            findings.append(_finding("CONCORDE-CAPABILITY-SKILL-001", source,
                f"stage capability {name!r} must have no skill; found {skills}.",
                "Stage capabilities are never projected as a skill; remove the skill source."))

    visiting: set[str] = set()
    visited: set[str] = set()
    model_calls: dict[str, bool | None] = {}

    def visit(name: str, chain: tuple[str, ...]) -> bool | None:
        module = valid_modules.get(name)
        if module is None:
            return None
        if name in visited:
            return model_calls[name]
        if name in visiting:
            findings.append(_finding("CONCORDE-CAPABILITY-USES-001", f"capabilities/{name}.py",
                "capability USES graph is cyclic: " + " -> ".join((*chain, name)),
                "Remove one nested USES edge so the composition graph is acyclic."))
            return None
        visiting.add(name)
        children = [visit(used, (*chain, name)) for used in module.USES]
        # Routing may call the coordinator even when it is not in this module's AGENTS.
        calls_model = bool(module.AGENTS) or module.EXTERNAL_NAME in MAIN_ROUTED_CAPABILITIES or any(children)
        resolved = all(child is not None for child in children) and all(
            isinstance(agent, Agent) for agent in module.AGENTS)
        if resolved and (module.DETERMINISTIC != (not calls_model)
                         or (module.CLASS == "lifecycle" and not module.DETERMINISTIC)):
            findings.append(_finding("CONCORDE-CAPABILITY-DETERMINISTIC-001", f"capabilities/{name}.py",
                f"capability {name!r} declares DETERMINISTIC={module.DETERMINISTIC}, "
                f"but its Agent, routing and transitive USES declarations imply model_calls={calls_model}.",
                "Set DETERMINISTIC to true exactly when no supported path calls a model; lifecycle capabilities must remain deterministic."))
        visiting.discard(name)
        visited.add(name)
        model_calls[name] = calls_model if resolved else None
        return model_calls[name]

    for name in sorted(declared):
        visit(name, ())
    return findings


_AGENT_SPEC_HEADINGS: tuple[str, ...] = (
    "Responsibilities",
    "Goals",
    "Accepted input and feedback",
    "Expected results",
    "Completion conditions",
    "Missing information, failure and human decisions",
)


def _load_agents_package(root: Path):
    """Load ``<root>/agents/__init__.py`` under a fresh private module name.

    Root-parametrized, unlike ``agent_model.load_agent_inventory()`` (which always loads the
    actual running checkout's package): this lets the validator check a temporary fixture
    package, mirroring ``_load_capabilities_package``.
    """

    import sys
    import uuid
    from importlib.util import module_from_spec, spec_from_file_location

    init_path = root / "agents" / "__init__.py"
    if init_path.is_symlink() or not init_path.is_file():
        return None
    module_name = f"_concorde_package_validation_agents_{uuid.uuid4().hex}"
    spec = spec_from_file_location(module_name, init_path, submodule_search_locations=[str(root / "agents")])
    if spec is None or spec.loader is None:
        return None
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _agent_modules(root: Path) -> tuple[object | None, dict[str, object]]:
    inventory = _load_agents_package(root)
    if inventory is None or not isinstance(getattr(inventory, "AGENTS", None), tuple):
        return None, {}
    modules: dict[str, object] = {}
    for name in inventory.AGENTS:
        try:
            modules[name] = importlib.import_module(f"{inventory.__name__}.{name}")
        except Exception:  # noqa: BLE001 - reported as a finding, not a crash
            modules[name] = None
    return inventory, modules


def _validate_agent_harness(agent: Agent, source: str) -> list[Finding]:
    """Rule CONCORDE-AGENT-HARNESS-001: the bound Harness is registered and every declared
    capability/context/result/effect/limit is a subset of what it admits."""

    findings: list[Finding] = []
    declared_harness = agent.harness
    registered = HARNESSES.get(declared_harness.name)
    if registered is None or registered.digest != declared_harness.digest:
        return [_finding("CONCORDE-AGENT-HARNESS-001", source,
            f"agent {agent.name!r} references an unregistered harness: {declared_harness.name!r}.",
            "Reference one of the registered harness.HARNESSES constants unchanged.")]

    unknown_capabilities = sorted(set(agent.constraints.capabilities) - frozenset(CAPABILITY_NAMES))
    if unknown_capabilities:
        findings.append(_finding("CONCORDE-AGENT-HARNESS-001", source,
            f"agent {agent.name!r} references unknown capabilities: {unknown_capabilities}.",
            "Reference only capabilities in contracts.CAPABILITY_NAMES."))

    exported = frozenset(exported_types())
    for field_name, declared_values in (("contexts", agent.constraints.contexts), ("results", agent.constraints.results)):
        unknown_types = sorted(set(declared_values) - exported)
        if unknown_types:
            findings.append(_finding("CONCORDE-AGENT-HARNESS-001", source,
                f"agent {agent.name!r} {field_name} reference unexported types: {unknown_types}.",
                "Reference only types in contracts.exported_types()."))
        outside_harness = sorted(set(declared_values) - set(getattr(declared_harness, field_name)))
        if outside_harness:
            findings.append(_finding("CONCORDE-AGENT-HARNESS-001", source,
                f"agent {agent.name!r} {field_name} exceed its harness {declared_harness.name!r}: {outside_harness}.",
                "Declare only contexts/results the bound harness itself admits."))

    effects = agent.constraints.effects
    harness_effects = declared_harness.effects
    if (
        set(effects.reads) - set(harness_effects.reads)
        or set(effects.writes) - set(harness_effects.writes)
        or (effects.network and not harness_effects.network)
        or (effects.credentials == "declared" and harness_effects.credentials != "declared")
    ):
        findings.append(_finding("CONCORDE-AGENT-HARNESS-001", source,
            f"agent {agent.name!r} constraints widen its harness {declared_harness.name!r} effects.",
            "Keep Constraints.effects a subset of the bound Harness effects."))

    from ..harness.agent_model import mode_definition
    for mode in agent.modes:
        try:
            mode_definition(agent, mode.name)
        except ValueError as error:
            findings.append(_finding("CONCORDE-AGENT-MODE-001", source, str(error),
                "Declare unique modes that narrow the Agent context, result and authority ceiling."))

    limits = agent.constraints.limits
    if limits is not None:
        if limits.timeout_seconds > declared_harness.loop.timeout_seconds:
            findings.append(_finding("CONCORDE-AGENT-HARNESS-001", source,
                f"agent {agent.name!r} limits exceed its harness {declared_harness.name!r} loop timeout.",
                "Keep Constraints.limits.timeout_seconds <= the harness loop timeout."))
        if (limits.max_turns is not None and declared_harness.loop.max_turns is not None
                and limits.max_turns > declared_harness.loop.max_turns):
            findings.append(_finding("CONCORDE-AGENT-HARNESS-001", source,
                f"agent {agent.name!r} limits exceed its harness {declared_harness.name!r} loop max_turns.",
                "Keep Constraints.limits.max_turns <= the harness loop max_turns when attested."))
    return findings


def _validate_agents(root: Path) -> list[Finding]:
    """Rules CONCORDE-AGENT-INVENTORY-001, CONCORDE-AGENT-SPEC-001, CONCORDE-AGENT-HARNESS-001."""

    inventory, modules = _agent_modules(root)
    if inventory is None:
        return [_finding("CONCORDE-AGENT-INVENTORY-001", "agents/__init__.py",
            "agents/__init__.py is missing, unsafe, or declares no AGENTS tuple.",
            "Add agents/__init__.py with an explicit AGENTS inventory.")]

    findings: list[Finding] = []
    declared = tuple(inventory.AGENTS)
    if len(declared) != len(set(declared)):
        findings.append(_finding("CONCORDE-AGENT-INVENTORY-001", "agents/__init__.py",
            f"AGENTS {list(declared)} must not contain duplicates.",
            "List each agents/<name>/ directory exactly once."))
    declared_set = set(declared)
    actual = {path.parent.name for path in (Path(inventory.__file__).parent).glob("*/__init__.py")}
    if declared_set != actual:
        findings.append(_finding("CONCORDE-AGENT-INVENTORY-001", "agents/__init__.py",
            f"Declared AGENTS {sorted(declared_set)} differs from agent directories {sorted(actual)}.",
            "List exactly the agents/<name>/ directories in AGENTS, one entry each."))

    for name in sorted(declared_set):
        source = f"agents/{name}/__init__.py"
        spec_source = f"agents/{name}/spec.md"
        module = modules.get(name)
        if module is None or not hasattr(module, "AGENT"):
            findings.append(_finding("CONCORDE-AGENT-SPEC-001", source,
                f"agent module {name!r} could not be imported, or declares no AGENT.",
                "Fix the import error, or declare AGENT = Agent(...)."))
            continue
        agent = module.AGENT
        if not isinstance(agent, Agent) or agent.name != name:
            findings.append(_finding("CONCORDE-AGENT-SPEC-001", source,
                f"agent module {name!r} must declare AGENT with name={name!r}.",
                "Declare AGENT = Agent(name=..., spec=..., harness=..., constraints=...)."))
            continue

        expected_spec = f"agents/{name}/spec.md"
        if agent.spec != expected_spec:
            findings.append(_finding("CONCORDE-AGENT-SPEC-001", source,
                f"agent {name!r} declares spec {agent.spec!r}, expected {expected_spec!r}.",
                "Point Agent.spec at agents/<name>/spec.md."))
        else:
            spec_path = root / expected_spec
            if spec_path.is_symlink() or not spec_path.is_file():
                findings.append(_finding("CONCORDE-AGENT-SPEC-001", spec_source,
                    f"agent {name!r} spec is missing: {expected_spec}.",
                    "Author agents/<name>/spec.md."))
            else:
                try:
                    resolve_agent_spec(root, expected_spec)
                except PromptResolverError as error:
                    findings.append(_finding(error.rule_id, spec_source, str(error),
                        "Repair the Agent Spec source or its @include directives."))
                else:
                    try:
                        text = spec_path.read_text(encoding="utf-8")
                    except (OSError, UnicodeError) as error:
                        findings.append(_finding("CONCORDE-AGENT-SPEC-001", spec_source,
                            f"cannot read {expected_spec}: {error}",
                            "Repair the Agent Spec source."))
                    else:
                        hyphenated = name.replace("_", "-")
                        lines = text.splitlines()
                        if not lines or lines[0].strip() != f"# concorde-{hyphenated}":
                            findings.append(_finding("CONCORDE-AGENT-SPEC-001", spec_source,
                                f"agent {name!r} spec must begin with '# concorde-{hyphenated}'.",
                                "Set the H1 heading to the exact concorde-<hyphenated> identity."))
                        found_headings = tuple(line[3:].strip() for line in lines if line.startswith("## "))
                        if found_headings != _AGENT_SPEC_HEADINGS:
                            findings.append(_finding("CONCORDE-AGENT-SPEC-001", spec_source,
                                f"agent {name!r} spec headings are {list(found_headings)}, "
                                f"expected {list(_AGENT_SPEC_HEADINGS)}.",
                                "Use exactly the six required `## ` headings, in order."))

        findings.extend(_validate_agent_harness(agent, source))
        declared_modes = {mode.instructions for mode in agent.modes}
        actual_modes = {path.relative_to(root).as_posix()
                        for path in (root / "agents" / name / "modes").glob("*.md")}
        if declared_modes != actual_modes:
            findings.append(_finding("CONCORDE-AGENT-MODE-001", source,
                "Mode instruction files differ from the declared mode inventory.",
                "Keep exactly the declared modes/<mode>.md authoring sources."))
        for mode in agent.modes:
            try:
                resolve_agent_spec(root, mode.instructions)
            except PromptResolverError as error:
                findings.append(_finding("CONCORDE-AGENT-MODE-001", mode.instructions, str(error),
                    "Repair the selected mode instruction source."))
    return findings


def _validate_contracts(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    names = list(exported_types())
    if len(names) != len(set(names)):
        duplicates = sorted({name for name in names if names.count(name) > 1})
        findings.append(_finding("CONCORDE-CONTRACT-UNIQUE-001", "src/concorde/spec/contracts.py",
            f"exported type identities contain duplicates: {duplicates}.",
            "Keep every exported type identity globally unique."))
    schemas_path = root / "generated/protocol/schemas.json"
    try:
        documented = json.loads(schemas_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        findings.append(_finding("CONCORDE-CONTRACT-SCHEMA-001", "generated/protocol/schemas.json",
            f"cannot read rendered schema export: {error}",
            "Run `python -m concorde build` to render generated/protocol/schemas.json."))
        return findings
    expected = {name: json_schema(name) for name in names}
    if documented != expected:
        findings.append(_finding("CONCORDE-CONTRACT-SCHEMA-001", "generated/protocol/schemas.json",
            "rendered generated/protocol/schemas.json differs from the executable exported contracts.",
            "Run `python -m concorde build` to re-render generated/protocol/schemas.json from concorde.spec.contracts.exported_types()."))
    return findings


_CAPABILITIES_BLOCK = re.compile(r"^```concorde-capabilities\s*\n(.*?)^```\s*$", re.M | re.S)
_AGENTS_BLOCK = re.compile(r"^```concorde-agents\s*\n(.*?)^```\s*$", re.M | re.S)
_DOCUMENT_HEADER_BLOCK = re.compile(r"^```concorde-document\s*\n(.*?)^```\s*$", re.M | re.S)
_SPEC_TYPE_TOKEN = re.compile(r"concorde-[a-z][a-z0-9-]*@[0-9]+")
_ERROR_TABLE_ROW = re.compile(r"^\|\s*`([a-z][a-z0-9_]*)`\s*\|", re.M)
_CODE_SHAPE = re.compile(r"^[a-z][a-z0-9_]*$")

# The wire envelope types are validated ad hoc (never through contracts.schemas()/exported_types(),
# see _PROTOCOL_VOCABULARY above) but are still real versioned identities the boundary document must
# describe; their versions are not derivable from schemas() the way every other type's is.
_ENVELOPE_VERSIONS = {
    "concorde-capability-invocation": 3,
    "concorde-capability-configuration": 1,
    "concorde-capability-result": 3,
}

_WORKFLOW_HOST_BOUNDARY_ID = "document.development.interfaces"


def _registered_documents(root: Path) -> dict[str, str] | None:
    """``{relative_path: text}`` for every unique Markdown path any registry target declares.

    Returns ``None`` when no readable registry exists at the conventional ``.concorde/specs.json``
    path, distinguishing "no registry" from "registry exists but is otherwise invalid" (already
    reported by the deterministic Spec/registry validator, not this module).
    """

    registry_path = root / ".concorde/specs.json"
    if registry_path.is_symlink() or not registry_path.is_file():
        return None
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(registry, dict) or not isinstance(registry.get("targets"), list):
        return None
    paths: set[str] = set()
    for target in registry["targets"]:
        if isinstance(target, dict) and isinstance(target.get("documents"), list):
            paths.update(path for path in target["documents"] if isinstance(path, str))
    documents: dict[str, str] = {}
    for relative in sorted(paths):
        path = root / relative
        if path.is_symlink() or not path.is_file():
            continue
        try:
            documents[relative] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
    return documents


def _document_header_id(text: str) -> str | None:
    match = _DOCUMENT_HEADER_BLOCK.search(text)
    if not match:
        return None
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return value.get("id") if isinstance(value, dict) else None


def _find_boundary_document(documents: dict[str, str]) -> tuple[str, str] | None:
    for path, text in documents.items():
        if _document_header_id(text) == _WORKFLOW_HOST_BOUNDARY_ID:
            return path, text
    return None


def _capability_code_inventory(root: Path) -> dict[str, dict[str, object]] | None:
    """``{external-id-without-prefix: {"class": ..., "deterministic": ..., "skill": ...}}`` from code.

    Mirrors ``_validate_capability_modules``'s own reads of the capability package and the skill
    sources, so this rule and rule 2 agree on what "the code" declares without a second inventory
    concept.
    """

    inventory, modules = _capability_modules(root)
    if inventory is None:
        return None
    skill_capabilities = _skill_capabilities(root)
    result: dict[str, dict[str, object]] = {}
    for name in inventory.CAPABILITIES:
        module = modules.get(name)
        if module is None or not hasattr(module, "CLASS"):
            continue
        skills = skill_capabilities.get(name, [])
        result[name.replace("_", "-")] = {
            "class": module.CLASS,
            "deterministic": getattr(module, "DETERMINISTIC", None),
            "skill": skills[0] if len(skills) == 1 else None,
        }
    return result


def _validate_spec_capabilities_block(root: Path, documents: dict[str, str]) -> list[Finding]:
    """Rule 4a: exactly one registered ``concorde-capabilities`` block, equal to the code inventory."""

    findings: list[Finding] = []
    matches = [(path, match.group(1)) for path, text in documents.items()
               for match in _CAPABILITIES_BLOCK.finditer(text)]
    if len(matches) != 1:
        findings.append(_finding("CONCORDE-SPEC-CAPABILITIES-001", ".concorde/specs.json",
            f"exactly one registered document must contain a concorde-capabilities block; found {len(matches)}.",
            "Keep the machine-readable capability inventory in exactly one registered Spec document."))
        return findings
    path, raw = matches[0]
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError as error:
        findings.append(_finding("CONCORDE-SPEC-CAPABILITIES-001", path,
            f"concorde-capabilities block is not valid JSON: {error}",
            "Fix the JSON array of {id, class, deterministic, skill} entries."))
        return findings
    valid_shape = (isinstance(entries, list)
        and all(isinstance(item, dict) and set(item) == {"id", "class", "deterministic", "skill"}
                and isinstance(item["id"], str) and isinstance(item["class"], str)
                and type(item["deterministic"]) is bool
                and (item["skill"] is None or isinstance(item["skill"], str)) for item in entries))
    if not valid_shape:
        findings.append(_finding("CONCORDE-SPEC-CAPABILITIES-001", path,
            "concorde-capabilities block must be a JSON array of {id, class, deterministic, skill} objects.",
            "Match exactly id/class/deterministic/skill for every entry, with a boolean deterministic value."))
        return findings
    declared: dict[str, tuple[object, object, object]] = {}
    for entry in entries:
        declared[entry["id"]] = (entry["class"], entry["deterministic"], entry["skill"])
    if len(declared) != len(entries):
        findings.append(_finding("CONCORDE-SPEC-CAPABILITIES-001", path,
            "concorde-capabilities entries must have unique id values.",
            "Remove the duplicate capability id."))
    code = _capability_code_inventory(root)
    if code is None:
        findings.append(_finding("CONCORDE-CAPABILITY-INVENTORY-001", "capabilities/__init__.py",
            "capabilities/__init__.py is missing, unsafe, or declares no CAPABILITIES tuple.",
            "Add capabilities/__init__.py with an explicit CAPABILITIES inventory."))
        return findings
    expected = {capability_id: (data["class"], data["deterministic"], data["skill"]) for capability_id, data in code.items()}
    for capability_id in sorted(set(expected) - set(declared)):
        findings.append(_finding("CONCORDE-SPEC-CAPABILITIES-001", path,
            f"concorde-capabilities block is missing capability {capability_id!r}.",
            "Add its {id, class, deterministic, skill} entry to the block."))
    for capability_id in sorted(set(declared) - set(expected)):
        findings.append(_finding("CONCORDE-SPEC-CAPABILITIES-001", path,
            f"concorde-capabilities block declares unknown capability {capability_id!r}.",
            "Remove the entry, or add the matching capabilities/<name>.py module."))
    for capability_id in sorted(set(declared) & set(expected)):
        if declared[capability_id] != expected[capability_id]:
            findings.append(_finding("CONCORDE-SPEC-CAPABILITIES-001", path,
                f"concorde-capabilities entry {capability_id!r} is {declared[capability_id]!r}, "
                f"code declares {expected[capability_id]!r}.",
                "Match class, deterministic and skill exactly to the capability module and its skill."))
    return findings


def _agent_code_inventory(root: Path) -> dict[str, dict[str, object]] | None:
    """``{hyphenated-agent-id: {"harness": ..., "capabilities": [...]}}`` from the actual code.

    Mirrors ``_validate_agents``'s own reads of the Agent package, and ``_capability_modules``'s
    read of the capability package, so this rule agrees with those rules on what "the code"
    declares without a second inventory concept. ``capabilities`` lists the sorted hyphenated
    names of every capability module whose ``AGENTS`` includes this Agent.
    """

    inventory, modules = _agent_modules(root)
    if inventory is None:
        return None
    capability_inventory, capability_modules = _capability_modules(root)
    result: dict[str, dict[str, object]] = {}
    for name in inventory.AGENTS:
        module = modules.get(name)
        if module is None or not hasattr(module, "AGENT"):
            continue
        agent = module.AGENT
        capability_names: list[str] = []
        if capability_inventory is not None:
            for capability_name in capability_inventory.CAPABILITIES:
                capability_module = capability_modules.get(capability_name)
                if capability_module is None:
                    continue
                declared_agents = getattr(capability_module, "AGENTS", ())
                if any(getattr(declared, "name", None) == name for declared in declared_agents):
                    capability_names.append(capability_name.replace("_", "-"))
        result[name.replace("_", "-")] = {
            "harness": agent.harness.name,
            "capabilities": sorted(capability_names),
            "modes": sorted(mode.name for mode in agent.modes),
        }
    return result


def _validate_spec_agents_block(root: Path, documents: dict[str, str]) -> list[Finding]:
    """New rule CONCORDE-SPEC-AGENTS-001: exactly one registered ``concorde-agents`` block, equal
    to the code inventory (mirrors ``_validate_spec_capabilities_block``)."""

    findings: list[Finding] = []
    matches = [(path, match.group(1)) for path, text in documents.items()
               for match in _AGENTS_BLOCK.finditer(text)]
    if len(matches) != 1:
        findings.append(_finding("CONCORDE-SPEC-AGENTS-001", ".concorde/specs.json",
            f"exactly one registered document must contain a concorde-agents block; found {len(matches)}.",
            "Keep the machine-readable Agent inventory in exactly one registered Spec document."))
        return findings
    path, raw = matches[0]
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError as error:
        findings.append(_finding("CONCORDE-SPEC-AGENTS-001", path,
            f"concorde-agents block is not valid JSON: {error}",
            "Fix the JSON array of {id, harness, capabilities, modes} entries."))
        return findings
    valid_shape = (isinstance(entries, list)
        and all(isinstance(item, dict) and set(item) == {"id", "harness", "capabilities", "modes"}
                and isinstance(item.get("capabilities"), list)
                and isinstance(item.get("modes"), list) for item in entries))
    if not valid_shape:
        findings.append(_finding("CONCORDE-SPEC-AGENTS-001", path,
            "concorde-agents block must be a JSON array of {id, harness, capabilities, modes} objects.",
            "Match exactly the four fields id/harness/capabilities/modes for every entry."))
        return findings
    declared: dict[str, tuple[object, tuple]] = {}
    for entry in entries:
        declared[entry["id"]] = (entry["harness"], tuple(entry["capabilities"]), tuple(entry["modes"]))
    if len(declared) != len(entries):
        findings.append(_finding("CONCORDE-SPEC-AGENTS-001", path,
            "concorde-agents entries must have unique id values.",
            "Remove the duplicate agent id."))
    code = _agent_code_inventory(root)
    if code is None:
        findings.append(_finding("CONCORDE-AGENT-INVENTORY-001", "agents/__init__.py",
            "agents/__init__.py is missing, unsafe, or declares no AGENTS tuple.",
            "Add agents/__init__.py with an explicit AGENTS inventory."))
        return findings
    expected = {agent_id: (data["harness"], tuple(data["capabilities"]), tuple(data["modes"])) for agent_id, data in code.items()}
    for agent_id in sorted(set(expected) - set(declared)):
        findings.append(_finding("CONCORDE-SPEC-AGENTS-001", path,
            f"concorde-agents block is missing agent {agent_id!r}.",
            "Add its {id, harness, capabilities, modes} entry to the block."))
    for agent_id in sorted(set(declared) - set(expected)):
        findings.append(_finding("CONCORDE-SPEC-AGENTS-001", path,
            f"concorde-agents block declares unknown agent {agent_id!r}.",
            "Remove the entry, or add the matching agents/<name>/ package."))
    for agent_id in sorted(set(declared) & set(expected)):
        if declared[agent_id] != expected[agent_id]:
            findings.append(_finding("CONCORDE-SPEC-AGENTS-001", path,
                f"concorde-agents entry {agent_id!r} is {declared[agent_id]!r}, "
                f"code declares {expected[agent_id]!r}.",
                "Match harness and capabilities exactly to the Agent module and its capability callers."))
    return findings


def _validate_spec_types(root: Path, documents: dict[str, str]) -> list[Finding]:
    """Rule 4b: every ``concorde-…@N`` token in the boundary document is an exported identity with
    that exact version, and every exported identity appears there at least once."""

    boundary = _find_boundary_document(documents)
    if boundary is None:
        return [_finding("CONCORDE-SPEC-TYPES-001", ".concorde/specs.json",
            f"no registered document declares id {_WORKFLOW_HOST_BOUNDARY_ID}.",
            "Register the Development interfaces document with that document id.")]
    path, text = boundary
    findings: list[Finding] = []
    from ..spec.wire_shapes import type_version
    expected: dict[str, int] = {name: type_version(name) for name in schemas()}
    expected.update(_ENVELOPE_VERSIONS)
    found: dict[str, set[int]] = {}
    for token in _SPEC_TYPE_TOKEN.findall(text):
        name, _, version_text = token.rpartition("@")
        found.setdefault(name, set()).add(int(version_text))
    for name in sorted(found):
        for version in sorted(found[name]):
            if name not in expected:
                findings.append(_finding("CONCORDE-SPEC-TYPES-001", path,
                    f"{name}@{version} names no exported identity.",
                    "Correct the identifier, or export it from the wire contracts."))
            elif version != expected[name]:
                findings.append(_finding("CONCORDE-SPEC-TYPES-001", path,
                    f"{name}@{version} does not match its exported version @{expected[name]}.",
                    f"Use {name}@{expected[name]}, the version the host actually exports."))
    for name in sorted(set(expected) - set(found)):
        findings.append(_finding("CONCORDE-SPEC-TYPES-001", path,
            f"exported identity {name}@{expected[name]} does not appear in this document.",
            "Describe every exported identity's promise in the Wire contracts section."))
    return findings


def _raised_error_codes(root: Path) -> set[str]:
    """Every ``code``-shaped literal passed to a ``*Error(...)`` call or an inline ``{"code": ...}``
    dict under ``src/concorde``, using the AST so message text (which always contains spaces
    or interpolation) is never mistaken for a code."""

    codes: set[str] = set()
    package_dir = root / "src/concorde"
    if not package_dir.is_dir():
        return codes
    for path in sorted(package_dir.rglob("*.py")):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = (node.func.id if isinstance(node.func, ast.Name)
                       else node.func.attr if isinstance(node.func, ast.Attribute) else None)
                if not name or not name.endswith("Error"):
                    continue
                for argument in (*node.args, *(keyword.value for keyword in node.keywords)):
                    if (isinstance(argument, ast.Constant) and isinstance(argument.value, str)
                            and _CODE_SHAPE.fullmatch(argument.value)):
                        codes.add(argument.value)
            elif isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values):
                    if (isinstance(key, ast.Constant) and key.value == "code"
                            and isinstance(value, ast.Constant) and isinstance(value.value, str)
                            and _CODE_SHAPE.fullmatch(value.value)):
                        codes.add(value.value)
    return codes


def _validate_spec_errors(root: Path, documents: dict[str, str]) -> list[Finding]:
    """Advisory rule 4c: every package error code literal appears in the boundary's error table."""

    boundary = _find_boundary_document(documents)
    if boundary is None:
        return []
    path, text = boundary
    documented = set(_ERROR_TABLE_ROW.findall(text))
    missing = sorted(_raised_error_codes(root) - documented)
    return [
        _finding("CONCORDE-SPEC-ERRORS-001", path,
            f"error code {code!r} is raised under src/concorde but missing from the error table.",
            "Add a row describing this error code's meaning.", severity="advisory")
        for code in missing
    ]


def _validate_spec_alignment(root: Path) -> list[Finding]:
    """Rule 4: the capability registry and wire promises agree with the executable code."""

    documents = _registered_documents(root)
    if documents is None:
        return [_finding("CONCORDE-SPEC-CAPABILITIES-001", ".concorde/specs.json",
            "no readable Spec registry was found.",
            "Register the capability registry and Development interfaces documents.")]
    findings: list[Finding] = []
    findings.extend(_validate_spec_capabilities_block(root, documents))
    findings.extend(_validate_spec_agents_block(root, documents))
    findings.extend(_validate_spec_types(root, documents))
    findings.extend(_validate_spec_errors(root, documents))
    return findings


def _validate_build_outputs(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        verify_fresh(root)
    except BuildError as error:
        findings.append(_finding("CONCORDE-BUILD-FRESH-001", "generated/build-manifest.json",
            str(error), "Run `python -m concorde build` to refresh generated/ outputs."))
        return findings
    try:
        current, differences = check_build(root, "all")
    except BuildError as error:
        findings.append(_finding("CONCORDE-BUILD-FRESH-001", "generated/build-manifest.json",
            str(error), "Run `python -m concorde build` to refresh generated/ outputs."))
        return findings
    if not current:
        findings.append(_finding("CONCORDE-BUILD-DRIFT-001", "generated/",
            f"rebuilding into a temporary directory differs from recorded outputs: {list(differences)}.",
            "Run `python -m concorde build` and commit no rendered output; it is derived."))
    return findings


def validate_package(root: Path) -> list[Finding]:
    """Validate the Concorde package: prompts, capability modules, Agents, contracts, Spec
    alignment, build outputs."""

    root = Path(root)
    findings: list[Finding] = []
    findings.extend(_validate_prompts(root))
    findings.extend(_validate_capability_modules(root))
    findings.extend(_validate_agents(root))
    findings.extend(_validate_contracts(root))
    findings.extend(_validate_spec_alignment(root))
    findings.extend(_validate_build_outputs(root))
    return findings
