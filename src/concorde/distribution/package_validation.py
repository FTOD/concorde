"""One package validator over prompts, capability modules, contracts, build outputs and Spec alignment.

Validates the single ``capabilities/`` inventory, its model profiles, public Skills and their
registered Spec declarations. Every finding carries a stable ``CONCORDE-…`` rule id.
"""

from __future__ import annotations

import ast
import importlib
import json
import re
from pathlib import Path
from types import ModuleType
from ..spec.frontmatter import FrontMatterError, parse_document
from ..spec.model import Finding
from . import build
from ..harness.worker_profile import WorkerProfile, child_definitions, validate_worker_profile
from ..harness.capability_state import StateContract
from .build import BuildError, check_build, verify_fresh
from .prompt_resolver import (
    PromptResolverError,
    find_unreachable_prompts,
    resolve_model_instructions,
    resolve_role_prompt,
    resolve_skill_source,
)
from ..spec.contracts import MODEL_CAPABILITIES, CAPABILITY_NAMES, exported_types, schemas

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
    return (tuple(build.SKILL_SOURCES.values()) + tuple(build.MODEL_ROOTS.values())
            + (build.WORKER_RULES, "prompts/protocol/principles.md")
            + tuple(f"prompts/protocol/kinds/{kind}.md" for kind in build.PROTOCOL_KINDS))


def _validate_prompts(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for relative in _prompt_roots():
        try:
            if relative.startswith("skills/"):
                resolve_skill_source(root, relative)
            elif relative.startswith("capabilities/"):
                resolve_model_instructions(root, relative)
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
            "No skill source, WorkerProfile Spec, or role root reaches this prompt file.",
            "Include it from a root, or delete the dead prompt text.",
        ))

    known = (
        frozenset(build.SKILL_NAMES)
        | frozenset(CAPABILITY_NAMES)
        | frozenset(MODEL_CAPABILITIES)
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
        for path in (root / "capabilities").rglob("spec.md")
        if path.is_file() and not path.is_symlink()
    ) if (root / "capabilities").is_dir() else [])
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
                    f"'{token}' names no skill, capability, WorkerProfile, or exported type.",
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


def _capability_modules(root: Path) -> tuple[ModuleType | None, dict[str, ModuleType | None]]:
    inventory = _load_capabilities_package(root)
    if inventory is None or not isinstance(getattr(inventory, "CAPABILITIES", None), tuple):
        return None, {}
    modules: dict[str, ModuleType | None] = {}
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
    actual = {path.stem for path in (root / "capabilities").glob("*.py") if path.stem != "__init__"}
    actual.update(path.parent.name for path in (root / "capabilities").glob("*/__init__.py"))
    if len(inventory.CAPABILITIES) != len(declared):
        findings.append(_finding("CONCORDE-CAPABILITY-INVENTORY-001", "capabilities/__init__.py",
            "CAPABILITIES must not contain duplicates.", "Declare each capability exactly once."))
    if declared != actual:
        findings.append(_finding(
            "CONCORDE-CAPABILITY-INVENTORY-001", "capabilities/__init__.py",
            f"Declared CAPABILITIES {sorted(declared)} differs from module files {sorted(actual)}.",
            "List exactly the capability module files in CAPABILITIES, one entry each.",
        ))

    skill_capabilities = _skill_capabilities(root)
    valid_modules: dict[str, ModuleType] = {}
    for name in sorted(declared):
        module = modules.get(name)
        source = f"capabilities/{name}.py"
        if module is None:
            findings.append(_finding("CONCORDE-CAPABILITY-CONSTANTS-001", source,
                f"capability module {name!r} could not be imported.",
                "Fix the import error in the capability module."))
            continue
        missing = [attribute for attribute in ("PUBLIC", "CONTEXT_SELECTION", "DETERMINISTIC", "PROFILE", "USES", "EXTERNAL_NAME", "STATE", "run")
                   if not hasattr(module, attribute)]
        if missing:
            findings.append(_finding("CONCORDE-CAPABILITY-CONSTANTS-001", source,
                f"capability module {name!r} is missing mandatory constants: {missing}.",
                "Declare PUBLIC, CONTEXT_SELECTION, DETERMINISTIC, PROFILE, USES, EXTERNAL_NAME, STATE and run(state, runtime)."))
            continue
        if (type(module.PUBLIC) is not bool or not isinstance(module.CONTEXT_SELECTION, str)
                or type(module.DETERMINISTIC) is not bool
                or module.PROFILE is not None and not isinstance(module.PROFILE, WorkerProfile)
                or not isinstance(module.USES, tuple)
                or not all(isinstance(used, str) for used in module.USES)
                or not isinstance(module.EXTERNAL_NAME, str)
                or not isinstance(module.STATE, StateContract)
                or not callable(module.run)):
            findings.append(_finding("CONCORDE-CAPABILITY-CONSTANTS-001", source,
                f"capability module {name!r} declares a mandatory constant with the wrong type.",
                "Use booleans, a WorkerProfile or None, a USES tuple, a StateContract and a callable run."))
            continue
        valid_modules[name] = module
        if hasattr(module, "CLASS") or hasattr(module, "AGENTS"):
            findings.append(_finding("CONCORDE-CAPABILITY-CONSTANTS-001", source,
                f"capability {name!r} retains a removed CLASS or AGENTS declaration.",
                "Use one Capability inventory and one USES composition relation."))
        if module.CONTEXT_SELECTION not in {"discover", "bound", "none"}:
            findings.append(_finding("CONCORDE-CAPABILITY-CONTEXT-001", source,
                f"capability {name!r} declares CONTEXT_SELECTION {module.CONTEXT_SELECTION!r}.",
                "CONTEXT_SELECTION must be discover, bound or none."))
        unknown_uses = sorted(set(module.USES) - declared)
        if unknown_uses:
            findings.append(_finding("CONCORDE-CAPABILITY-USES-001", source,
                f"capability {name!r} USES unknown capabilities: {unknown_uses}.",
                "Name only capabilities listed in capabilities.CAPABILITIES."))
        if module.PROFILE is not None and (
                module.STATE.input_type != module.PROFILE.contract.context
                or module.STATE.output_type != module.PROFILE.contract.result):
            findings.append(_finding("CONCORDE-CAPABILITY-STATE-001", source,
                "State contract differs from the model execution profile.",
                "Use the profile's admitted input and output types."))
        if len(module.USES) != len(set(module.USES)):
            findings.append(_finding("CONCORDE-CAPABILITY-USES-001", source,
                "USES contains duplicate Capability identities.", "Declare each direct dependency once."))
        known_types = schemas()
        if (not isinstance(module.STATE.input_type, str) or module.STATE.input_type not in known_types
                or module.STATE.output_type is not None and (
                    not isinstance(module.STATE.output_type, str) or module.STATE.output_type not in known_types)):
            findings.append(_finding("CONCORDE-CAPABILITY-STATE-001", source,
                "State contract references an unknown type.", "Declare registered input and output schemas."))
        if (module.PUBLIC or hasattr(module, "REQUEST") or hasattr(module, "RESPONSE")) and (
                not isinstance(getattr(module, "REQUEST", None), dict)
                or not isinstance(getattr(module, "RESPONSE", None), dict)):
            findings.append(_finding("CONCORDE-CAPABILITY-CONSTANTS-001", source,
                "Public/host adapters must retain both wire schemas.",
                "Declare REQUEST and RESPONSE; private State-only nodes need neither."))
        expected_external = "concorde-" + name.replace("_", "-")
        if module.EXTERNAL_NAME != expected_external:
            findings.append(_finding("CONCORDE-CAPABILITY-EXTERNALNAME-001", source,
                f"capability {name!r} EXTERNAL_NAME is {module.EXTERNAL_NAME!r}, expected {expected_external!r}.",
                "EXTERNAL_NAME is always 'concorde-' plus the module name with underscores hyphenated."))
        skills = skill_capabilities.get(name, [])
        should_have_skill = module.PUBLIC
        if should_have_skill and len(skills) != 1:
            findings.append(_finding("CONCORDE-CAPABILITY-SKILL-001", source,
                f"public capability {name!r} must have exactly one skill naming it; found {skills}.",
                "Add or deduplicate the skills/<name>/SKILL.md declaring capability: " + name + "."))
        if not should_have_skill and skills:
            findings.append(_finding("CONCORDE-CAPABILITY-SKILL-001", source,
                f"non-public capability {name!r} must have no skill; found {skills}.",
                "Only PUBLIC=True capabilities are projected as Skills; remove the skill source."))

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
        calls_model = module.PROFILE is not None or module.CONTEXT_SELECTION == "discover" or any(children)
        resolved = all(child is not None for child in children)
        if resolved and module.DETERMINISTIC != (not calls_model):
            findings.append(_finding("CONCORDE-CAPABILITY-DETERMINISTIC-001", f"capabilities/{name}.py",
                f"capability {name!r} declares DETERMINISTIC={module.DETERMINISTIC}, "
                f"but its WorkerProfile, routing and transitive USES declarations imply model_calls={calls_model}.",
                "Set DETERMINISTIC to true exactly when no supported path calls a model."))
        if resolved and module.CONTEXT_SELECTION == "none" and calls_model:
            findings.append(_finding("CONCORDE-CAPABILITY-CONTEXT-001", f"capabilities/{name}.py",
                f"capability {name!r} selects no WorkerProfile context but its composition calls a model.",
                "Model-backed capabilities must declare discover or bound context selection."))
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








def _validate_agent_profile(root: Path, agent: WorkerProfile, source: str) -> list[Finding]:
    """Rules CONCORDE-AGENT-PROFILE-001 and CONCORDE-AGENT-CHILD-001: a consistent worker profile
    whose contract types are exported and whose declared children are exactly its child files."""

    findings: list[Finding] = []
    try:
        validate_worker_profile(agent)
    except ValueError as error:
        findings.append(_finding("CONCORDE-AGENT-PROFILE-001", source, str(error),
            "Declare a consistent worker profile: contract, workspace, tools, children and timeout."))
    exported = frozenset(exported_types())
    unknown = sorted({agent.contract.context, agent.contract.result} - exported)
    if unknown:
        findings.append(_finding("CONCORDE-AGENT-PROFILE-001", source,
            f"agent {agent.name!r} contract references unexported types: {unknown}.",
            "Reference only types in contracts.exported_types()."))
    declared = {child.definition for child in agent.children}
    directory = root / "capabilities" / agent.name / "children"
    actual = {path.relative_to(root).as_posix() for path in directory.glob("*.md")} if directory.is_dir() else set()
    if declared != actual:
        findings.append(_finding("CONCORDE-AGENT-CHILD-001", source,
            f"agent {agent.name!r} declares children {sorted(declared)} but has child files {sorted(actual)}.",
            "Declare exactly the capabilities/<name>/children/<child>.md definitions as Child entries."))
    try:
        child_definitions(root, agent)
    except ValueError as error:
        findings.append(_finding("CONCORDE-AGENT-CHILD-001", source, str(error),
            "Author each child as a pi-subagents definition with its name, description, read or check tools "
            "and replaced, context-free prompt settings."))
    return findings


def _validate_worker_profiles(root: Path) -> list[Finding]:
    """Rules CONCORDE-AGENT-INVENTORY-001, CONCORDE-AGENT-SPEC-001, CONCORDE-AGENT-HARNESS-001."""

    inventory, modules = _capability_modules(root)
    if inventory is None:
        return [_finding("CONCORDE-CAPABILITY-INVENTORY-001", "capabilities/__init__.py",
            "Missing Capability inventory.", "Declare the single CAPABILITIES inventory.")]
    findings: list[Finding] = []
    for name, module in modules.items():
        if module is None:
            findings.append(_finding("CONCORDE-CAPABILITY-INVENTORY-001", "capabilities/__init__.py",
                f"Cannot load capability {name!r}.", "Repair the capability declaration."))
            continue
        agent = getattr(module, "PROFILE", None)
        if agent is None:
            continue
        source = f"capabilities/{name}/__init__.py"
        spec_source = f"capabilities/{name}/spec.md"
        if not isinstance(agent, WorkerProfile) or agent.name != name:
            findings.append(_finding("CONCORDE-AGENT-SPEC-001", source,
                f"PROFILE must belong to capability {name!r}.", "Use this capability's identity."))
            continue
        expected_spec = f"capabilities/{name}/spec.md"
        if agent.spec != expected_spec:
            findings.append(_finding("CONCORDE-AGENT-SPEC-001", source,
                f"agent {name!r} declares spec {agent.spec!r}, expected {expected_spec!r}.",
                "Point WorkerProfile.spec at capabilities/<name>/spec.md."))
        else:
            spec_path = root / expected_spec
            if spec_path.is_symlink() or not spec_path.is_file():
                findings.append(_finding("CONCORDE-AGENT-SPEC-001", spec_source,
                    f"agent {name!r} spec is missing: {expected_spec}.",
                    "Author capabilities/<name>/spec.md."))
            else:
                try:
                    resolve_model_instructions(root, expected_spec)
                except PromptResolverError as error:
                    findings.append(_finding(error.rule_id, spec_source, str(error),
                        "Repair the WorkerProfile Spec source or its @include directives."))
                else:
                    try:
                        text = spec_path.read_text(encoding="utf-8")
                    except (OSError, UnicodeError) as error:
                        findings.append(_finding("CONCORDE-AGENT-SPEC-001", spec_source,
                            f"cannot read {expected_spec}: {error}",
                            "Repair the WorkerProfile Spec source."))
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

        findings.extend(_validate_agent_profile(root, agent, source))
    return findings


def _validate_contracts(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    # Expect exactly what the build renders for this root: its own schema sources, evaluated
    # afresh, so a root-local helper change never disagrees with a correctly rebuilt export.
    from .build import BuildError, _root_schemas
    try:
        expected, _, names = _root_schemas(root)
    except BuildError as error:
        findings.append(_finding("CONCORDE-CONTRACT-SCHEMA-001", "generated/protocol/schemas.json",
            f"cannot evaluate this root's schema sources: {error}",
            "Repair the schema sources under src/concorde/spec, then run `python -m concorde build`."))
        return findings
    names = list(names)
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
    if documented != expected:
        findings.append(_finding("CONCORDE-CONTRACT-SCHEMA-001", "generated/protocol/schemas.json",
            "rendered generated/protocol/schemas.json differs from the executable exported contracts.",
            "Run `python -m concorde build` to re-render generated/protocol/schemas.json from concorde.spec.contracts.exported_types()."))
    return findings


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


def _document_header_id(root: Path, path: str) -> str | None:
    from ..spec.repository_base import read_file
    try:
        return json.loads(read_file(root, path + ".json").decode())["document"]["id"]
    except (ValueError, OSError, KeyError, TypeError):
        return None


def _find_boundary_document(root: Path, documents: dict[str, str]) -> tuple[str, str] | None:
    for path, text in documents.items():
        if _document_header_id(root, path) == _WORKFLOW_HOST_BOUNDARY_ID:
            return path, text
    return None


def _metadata_inventories(root: Path, documents: dict[str, str], key: str) -> list[tuple[str, str]]:
    from ..spec.repository_base import read_file
    from ..spec.typed_data import decode
    result = []
    for path in documents:
        try:
            value = decode(read_file(root, path + ".json").decode())
        except (ValueError, OSError):
            continue  # The document-unit validator reports invalid/missing metadata.
        if not isinstance(value, dict):
            continue
        extensions = value.get("extensions", {})
        if not isinstance(extensions, dict):
            continue
        if key in extensions:
            result.append((path + ".json", json.dumps(extensions[key])))
    return result


def _capability_code_inventory(root: Path) -> dict | None:
    inventory, modules = _capability_modules(root)
    if inventory is None:
        return None
    skills = _skill_capabilities(root)
    result = {}
    for name, module in modules.items():
        if module is None or not hasattr(module, "PUBLIC"):
            continue
        profile = getattr(module, "PROFILE", None)
        state = getattr(module, "STATE", None)
        result[name.replace("_", "-")] = {
            "public": module.PUBLIC,
            "context_selection": getattr(module, "CONTEXT_SELECTION", None),
            "deterministic": getattr(module, "DETERMINISTIC", None),
            "skill": skills.get(name, [None])[0],
            "uses": list(getattr(module, "USES", ())),
            "state": {"input": state.input_type, "output": state.output_type} if state else None,
            "profile": {"workspace": profile.workspace, "tools": sorted(profile.tools),
                        "children": sorted(child.name for child in profile.children)} if profile else None,
        }
    return result



def _validate_spec_capabilities_block(root: Path, documents: dict[str, str]) -> list[Finding]:
    """Exactly one metadata inventory covers every Capability and its optional profile."""
    rule = "CONCORDE-SPEC-CAPABILITIES-001"
    findings = []
    matches = _metadata_inventories(root, documents, "concorde.capabilities")
    if len(matches) != 1:
        return [_finding(rule, ".concorde/specs.json",
            "Exactly one concorde.capabilities inventory is required.", "Register one complete inventory.")]
    path, raw = matches[0]
    try:
        entries = json.loads(raw)
    except ValueError:
        entries = None
    fields = {"id", "public", "context_selection", "deterministic", "skill", "uses", "state", "profile"}
    if not isinstance(entries, list) or any(
        not isinstance(item, dict) or set(item) != fields
        or not isinstance(item["id"], str) or type(item["public"]) is not bool
        or type(item["deterministic"]) is not bool
        or item["context_selection"] not in ("discover", "bound", "none")
        or not isinstance(item["uses"], list) or not isinstance(item["state"], dict)
        or item["profile"] is not None and not isinstance(item["profile"], dict)
        for item in entries
    ):
        return [_finding(rule, path, "Malformed Capability State/profile inventory.",
                         "Declare id/public/context_selection/deterministic/skill/uses/state/profile.")]
    declared = {item["id"]: {k: v for k, v in item.items() if k != "id"} for item in entries}
    if len(declared) != len(entries):
        findings.append(_finding(rule, path, "Duplicate capability identity.", "Declare each identity once."))
    expected = _capability_code_inventory(root)
    if expected is None:
        return [_finding(rule, path, "Missing capability code inventory.", "Restore capabilities/__init__.py.")]
    for name in sorted(set(expected) - set(declared)):
        findings.append(_finding(rule, path, f"missing capability {name!r}.", "Add its complete declaration."))
    for name in sorted(set(declared) - set(expected)):
        findings.append(_finding(rule, path, f"unknown capability {name!r}.", "Remove the unimplemented declaration."))
    for name in sorted(set(expected) & set(declared)):
        if declared[name] != expected[name]:
            findings.append(_finding(rule, path, f"Capability {name!r} differs from its code declaration.",
                "Reconcile exposure, USES, State and the optional execution profile."))
    return findings









def _validate_spec_types(root: Path, documents: dict[str, str]) -> list[Finding]:
    """Rule 4b: every ``concorde-…@N`` token in the boundary document is an exported identity with
    that exact version, and every exported identity appears there at least once."""

    boundary = _find_boundary_document(root, documents)
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
        try:
            version = int(version_text)
        except ValueError:
            findings.append(_finding("CONCORDE-SPEC-TYPES-001", path,
                "type version exceeds the supported integer representation", "Use the exported type version."))
            continue
        found.setdefault(name, set()).add(version)
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

    boundary = _find_boundary_document(root, documents)
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
    """Validate the Concorde package: prompts, Capabilities, model profiles, contracts, Spec
    alignment, build outputs."""

    root = Path(root)
    findings: list[Finding] = []
    findings.extend(_validate_prompts(root))
    findings.extend(_validate_capability_modules(root))
    findings.extend(_validate_worker_profiles(root))
    findings.extend(_validate_contracts(root))
    findings.extend(_validate_spec_alignment(root))
    findings.extend(_validate_build_outputs(root))
    return findings
