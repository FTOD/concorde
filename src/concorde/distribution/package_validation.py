"""One package validator over prompts, operation modules, contracts, build outputs and Spec alignment.

Validates compatibility adapters in ``operations/``, canonical Agents in ``agents/``, public
guidance and their separately owned registered Spec declarations. Every finding carries a stable ``CONCORDE-…`` rule id.
"""

from __future__ import annotations

import ast
import importlib
import json
import re
from pathlib import Path
from types import ModuleType

from ..harness.worker_profile import AgentDefinition, validate_definition
from ..operations.catalog import (
    OPERATION_NAMES,
    CatalogError,
    load_catalog,
    mirror,
    register_types,
)
from ..spec.model import Finding
from . import build
from .build import BuildError, check_build, verify_fresh
from .prompt_resolver import (
    GUIDANCE_ROOT,
    PromptResolverError,
    find_unreachable_prompts,
    resolve_model_instructions,
    resolve_operation_guidance,
    resolve_role_prompt,
)

_SUBJECT = "module.distribution"


def exported_types() -> tuple[str, ...]:
    """Every registered type identity, after the catalog loaded every owner."""
    from ..spec.typed_data import registered_types

    register_types()
    return registered_types()


def schemas() -> dict[str, dict]:
    """Every registered type's ``data`` schema, keyed by type identity."""
    from ..spec.typed_data import data_schema

    return {name: data_schema(name) for name in exported_types()}


_NAME_TOKEN = re.compile(r"concorde-[a-z][a-z0-9-]*")

# Wire/Protocol vocabulary that legitimately appears as inline `concorde-…` prose terms but is not
# an operation external name, or a registered type: the two
# envelope type_ids validated ad hoc (never registered), and two Protocol
# structural terms (a document ID prefix, a machine-readable participant block name) defined only
# in protocol/principles.md prose, not in any Python registry.
_PROTOCOL_VOCABULARY = frozenset(
    {
        "concorde-operation-invocation",
        "concorde-operation-configuration",
        "concorde-operation-result",
        "concorde-document",
        "concorde-dependencies",
        "concorde-entities",
        "concorde-contract",
        "concorde-contract-binding",
    }
)


def _finding(
    rule: str, source: str, message: str, remediation: str, *, severity: str = "error"
) -> Finding:
    return Finding(rule, severity, source, message, remediation, subject_id=_SUBJECT)


def _prompt_roots(root: Path) -> tuple[str, ...]:
    return (
        build.task_subagents.prompt_roots(root)
        + tuple(build.guidance_sources().values())
        + tuple(build.MODEL_ROOTS.values())
        + tuple(f"prompts/native/{name}.md" for name in build.MODEL_ROOTS)
        + ("prompts/protocol/principles.md",)
        + tuple(f"prompts/protocol/kinds/{kind}.md" for kind in build.PROTOCOL_KINDS)
    )


def _validate_prompts(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for relative in _prompt_roots(root):
        try:
            if relative.startswith(GUIDANCE_ROOT):
                resolve_operation_guidance(root, relative)
            elif relative.startswith("agents/"):
                resolve_model_instructions(root, relative)
            else:
                resolve_role_prompt(root, relative)
        except PromptResolverError as error:
            findings.append(
                _finding(
                    error.rule_id,
                    relative,
                    str(error),
                    "Repair the prompt source or its @path.md references.",
                )
            )
    try:
        unreachable = find_unreachable_prompts(root, _prompt_roots(root))
    except PromptResolverError:
        # Already reported above as a resolver error against the same broken root; reachability
        # over a root that cannot even resolve would only duplicate that finding.
        unreachable = ()
    for relative in unreachable:
        findings.append(
            _finding(
                "CONCORDE-PROMPT-UNREACHABLE-001",
                relative,
                "No operation guidance source, Agent instructions, or Agent prompt root reaches this prompt file.",
                "Include it from a root, or delete the dead prompt text.",
            )
        )

    known = (
        frozenset(OPERATION_NAMES)
        | frozenset(
            "concorde-" + name.replace("_", "-") for name in _agent_modules(root)
        )
        | frozenset(schemas())
        | _PROTOCOL_VOCABULARY
    )
    sources: list[str] = (
        sorted(
            path.relative_to(root).as_posix()
            for path in (root / "prompts").rglob("*.md")
            if path.is_file() and not path.is_symlink()
        )
        if (root / "prompts").is_dir()
        else []
    )
    sources.extend(
        sorted(
            path.relative_to(root).as_posix()
            for path in (root / "agents").rglob("spec.md")
            if path.is_file() and not path.is_symlink()
        )
        if (root / "agents").is_dir()
        else []
    )
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
                findings.append(
                    _finding(
                        "CONCORDE-PROMPT-NAME-001",
                        relative,
                        f"'{token}' names no operation, Agent, or exported type.",
                        "Correct the identifier, or export/declare it if it is genuinely new.",
                    )
                )
    return findings


def _load_operations_package(root: Path, directory: str = "operations"):
    """Load ``<root>/operations/__init__.py`` under a fresh private module name.

    Root-parametrized, unlike ``catalog.load_operation_inventory()`` (which always
    loads the actual running checkout's package): this lets the validator check a temporary
    fixture package. A fresh unique name per call avoids any ``sys.modules`` collision between
    successive validations of different roots within one process, such as this module's own tests.
    """

    import sys
    import uuid
    from importlib.util import module_from_spec, spec_from_file_location

    init_path = root / directory / "__init__.py"
    if init_path.is_symlink() or not init_path.is_file():
        return None
    module_name = f"_concorde_package_validation_inventory_{uuid.uuid4().hex}"
    spec = spec_from_file_location(
        module_name, init_path, submodule_search_locations=[str(root / directory)]
    )
    if spec is None or spec.loader is None:
        return None
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _agent_modules(root: Path) -> dict[str, ModuleType | None]:
    """The Agent modules of ``root``'s ``agents`` package, None for one that cannot load."""
    inventory = _load_operations_package(root, "agents")
    modules: dict[str, ModuleType | None] = {}
    if inventory is None:
        return modules
    for name in inventory.AGENTS:
        try:
            modules[name] = importlib.import_module(f"{inventory.__name__}.{name}")
        except Exception:  # noqa: BLE001 - reported as a finding, not a crash
            modules[name] = None
    return modules


def _catalog(root: Path):
    """The Operation catalog of ``root``, or the loader's refusal."""
    try:
        return load_catalog(root), None
    except CatalogError as error:
        return None, error


def _validate_operation_modules(root: Path) -> list[Finding]:
    """The catalog loads, and each public Operation has exactly its own guidance source.

    The declaration rules are the catalog loader's; its refusal is reported, not repeated.
    """
    catalog, error = _catalog(root)
    if catalog is None:
        return [
            _finding(
                "CONCORDE-OPERATION-INVENTORY-001",
                f"operations/{error.declaration}.py",
                str(error),
                "Repair the declaration so the Operation catalog loads.",
            )
        ]
    findings: list[Finding] = []
    guidance_root = root / GUIDANCE_ROOT
    guidance = (
        {
            path.stem
            for path in guidance_root.glob("*.md")
            if path.is_file() and not path.is_symlink()
        }
        if guidance_root.is_dir() and not guidance_root.is_symlink()
        else set()
    )
    public = {name for name, item in catalog.items() if item.public}
    for name in sorted(public - guidance):
        findings.append(
            _finding(
                "CONCORDE-OPERATION-GUIDANCE-001",
                f"{GUIDANCE_ROOT}{name}.md",
                f"public operation {name!r} has no guidance source.",
                "Add prompts/operation-guidance/<public name>.md.",
            )
        )
    for name in sorted(guidance - public):
        findings.append(
            _finding(
                "CONCORDE-OPERATION-GUIDANCE-001",
                f"{GUIDANCE_ROOT}{name}.md",
                f"guidance source {name!r} names no public operation.",
                "Remove the guidance source or declare its Operation.",
            )
        )
    return findings


_AGENT_SPEC_HEADINGS: tuple[str, ...] = (
    "Responsibilities",
    "Goals",
    "Accepted input and feedback",
    "Expected results",
    "Completion conditions",
    "Missing information, failure and human decisions",
)


def _validate_agent_definition(
    root: Path, agent: AgentDefinition, source: str
) -> list[Finding]:
    """Validate one Agent definition and the types it names."""

    findings: list[Finding] = []
    try:
        validate_definition(agent)
    except ValueError as error:
        findings.append(
            _finding(
                "CONCORDE-AGENT-PROFILE-001",
                source,
                str(error),
                "Declare a consistent Agent definition: phase, types, effects, tools and hook.",
            )
        )
    exported = frozenset(exported_types())
    unknown = sorted({agent.context, agent.result} - exported)
    if unknown:
        findings.append(
            _finding(
                "CONCORDE-AGENT-PROFILE-001",
                source,
                f"agent {agent.name!r} names unexported types: {unknown}.",
                "Reference only registered types.",
            )
        )
    return findings


def _validate_worker_profiles(root: Path) -> list[Finding]:
    """Rules CONCORDE-AGENT-INVENTORY-001, CONCORDE-AGENT-SPEC-001, CONCORDE-AGENT-HARNESS-001."""

    agents = _load_operations_package(root, "agents")
    if agents is None:
        return [
            _finding(
                "CONCORDE-OPERATION-INVENTORY-001",
                "agents/__init__.py",
                "Missing Agents inventory.",
                "Declare the single AGENTS inventory.",
            )
        ]
    modules = _agent_modules(root)
    findings: list[Finding] = []
    if agents is not None and len(agents.AGENTS) != len(set(agents.AGENTS)):
        findings.append(
            _finding(
                "CONCORDE-OPERATION-INVENTORY-001",
                "agents/__init__.py",
                "Duplicate Agent identity.",
                "Declare each Agent once.",
            )
        )
    for name, module in modules.items():
        if module is None:
            findings.append(
                _finding(
                    "CONCORDE-OPERATION-INVENTORY-001",
                    f"agents/{name}/__init__.py",
                    f"Cannot load Agent {name!r}.",
                    "Repair the Agent definition.",
                )
            )
            continue
        agent = getattr(module, "DEFINITION", None)
        source = f"agents/{name}/__init__.py"
        spec_source = f"agents/{name}/spec.md"
        if not isinstance(agent, AgentDefinition) or agent.name != name:
            findings.append(
                _finding(
                    "CONCORDE-AGENT-SPEC-001",
                    source,
                    f"DEFINITION must be the AgentDefinition of {name!r}.",
                    "Export exactly this Agent's DEFINITION.",
                )
            )
            continue
        expected_spec = f"agents/{name}/spec.md"
        if agent.instructions != expected_spec:
            findings.append(
                _finding(
                    "CONCORDE-AGENT-SPEC-001",
                    source,
                    f"agent {name!r} names instructions {agent.instructions!r}, expected {expected_spec!r}.",
                    "Point the definition's instructions at agents/<name>/spec.md.",
                )
            )
        else:
            spec_path = root / expected_spec
            if spec_path.is_symlink() or not spec_path.is_file():
                findings.append(
                    _finding(
                        "CONCORDE-AGENT-SPEC-001",
                        spec_source,
                        f"agent {name!r} spec is missing: {expected_spec}.",
                        "Author agents/<name>/spec.md.",
                    )
                )
            else:
                try:
                    resolve_model_instructions(root, expected_spec)
                except PromptResolverError as error:
                    findings.append(
                        _finding(
                            error.rule_id,
                            spec_source,
                            str(error),
                            "Repair the Agent instructions or their @path.md references.",
                        )
                    )
                else:
                    try:
                        text = spec_path.read_text(encoding="utf-8")
                    except (OSError, UnicodeError) as error:
                        findings.append(
                            _finding(
                                "CONCORDE-AGENT-SPEC-001",
                                spec_source,
                                f"cannot read {expected_spec}: {error}",
                                "Repair the Agent instructions.",
                            )
                        )
                    else:
                        hyphenated = name.replace("_", "-")
                        lines = text.splitlines()
                        if not lines or lines[0].strip() != f"# concorde-{hyphenated}":
                            findings.append(
                                _finding(
                                    "CONCORDE-AGENT-SPEC-001",
                                    spec_source,
                                    f"agent {name!r} spec must begin with '# concorde-{hyphenated}'.",
                                    "Set the H1 heading to the exact concorde-<hyphenated> identity.",
                                )
                            )
                        found_headings = tuple(
                            line[3:].strip() for line in lines if line.startswith("## ")
                        )
                        if found_headings != _AGENT_SPEC_HEADINGS:
                            findings.append(
                                _finding(
                                    "CONCORDE-AGENT-SPEC-001",
                                    spec_source,
                                    f"agent {name!r} spec headings are {list(found_headings)}, "
                                    f"expected {list(_AGENT_SPEC_HEADINGS)}.",
                                    "Use exactly the six required `## ` headings, in order.",
                                )
                            )

        findings.extend(_validate_agent_definition(root, agent, source))
    return findings


def _validate_contracts(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    # Expect exactly what the build exports: every type the running package registers.
    from ..spec.typed_data import TypedDataError
    from .build import SCHEMAS_PATH, BuildError, registered_schemas

    try:
        register_types()
    except TypedDataError as error:
        findings.append(
            _finding(
                "CONCORDE-CONTRACT-UNIQUE-001"
                if error.code == "duplicate_type"
                else "CONCORDE-CONTRACT-SCHEMA-001",
                SCHEMAS_PATH,
                f"{error.field}: {error}",
                "Register every type identity once, with one version and schema.",
            )
        )
        return findings
    try:
        expected, _ = registered_schemas(root)
    except BuildError as error:
        findings.append(
            _finding(
                "CONCORDE-CONTRACT-SCHEMA-001",
                SCHEMAS_PATH,
                f"cannot export the registered schemas: {error}",
                "Repair the registered schema, then run `python -m concorde build`.",
            )
        )
        return findings
    schemas_path = root / SCHEMAS_PATH
    try:
        documented = json.loads(schemas_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        findings.append(
            _finding(
                "CONCORDE-CONTRACT-SCHEMA-001",
                SCHEMAS_PATH,
                f"cannot read rendered schema export: {error}",
                f"Run `python -m concorde build` to render {SCHEMAS_PATH}.",
            )
        )
        return findings
    if documented != expected:
        findings.append(
            _finding(
                "CONCORDE-CONTRACT-SCHEMA-001",
                SCHEMAS_PATH,
                f"rendered {SCHEMAS_PATH} differs from the registered types.",
                f"Run `python -m concorde build` to re-render {SCHEMAS_PATH}.",
            )
        )
    return findings


_SPEC_TYPE_TOKEN = re.compile(r"concorde-[a-z][a-z0-9-]*@[0-9]+")
_ERROR_TABLE_ROW = re.compile(r"^\|\s*`([a-z][a-z0-9_]*)`\s*\|", re.MULTILINE)
_CODE_SHAPE = re.compile(r"^[a-z][a-z0-9_]*$")

# The wire envelope types are validated ad hoc (never registered,
# see _PROTOCOL_VOCABULARY above) but are still real versioned identities the boundary document must
# describe; their versions are not derivable from schemas() the way every other type's is.
# The two envelopes of a capability request carry a type_id and schema_version but are checked
# against their contracts, not registered as typed values; the entry module validates them.
_ENVELOPE_VERSIONS = {
    "concorde-operation-invocation": 3,
    "concorde-operation-result": 3,
}
_ENVELOPE_MODULE = "concorde.harness.entry"

_OPERATION_HOST_BOUNDARY_ID = "document.admission.contracts"


def _registered_documents(root: Path) -> dict[str, str] | None:
    """``{relative_path: text}`` for every reading path any registry record ``owns``.

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
    if not isinstance(registry, dict) or not isinstance(registry.get("modules"), list):
        return None
    paths: set[str] = set()
    for record in registry["modules"]:
        if isinstance(record, dict) and isinstance(record.get("owns"), list):
            paths.update(path for path in record["owns"] if isinstance(path, str))
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


def _find_boundary_document(
    root: Path, documents: dict[str, str]
) -> tuple[str, str] | None:
    for path, text in documents.items():
        if _document_header_id(root, path) == _OPERATION_HOST_BOUNDARY_ID:
            return path, text
    return None


def _metadata_inventories(
    root: Path, documents: dict[str, str], key: str
) -> list[tuple[str, str]]:
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


def _operation_code_inventory(root: Path) -> dict | None:
    """The ``concorde.operations`` records the loaded catalog of ``root`` yields, by identity."""
    catalog, _ = _catalog(root)
    if catalog is None:
        return None
    return {
        record["id"]: {key: value for key, value in record.items() if key != "id"}
        for record in mirror(catalog)
    }


def _validate_spec_operations_block(
    root: Path, documents: dict[str, str]
) -> list[Finding]:
    """Exactly one metadata inventory covers every Operation and its optional profile."""
    rule = "CONCORDE-SPEC-OPERATIONS-001"
    findings = []
    matches = _metadata_inventories(root, documents, "concorde.operations")
    if len(matches) != 1:
        return [
            _finding(
                rule,
                ".concorde/specs.json",
                "Exactly one concorde.operations inventory is required.",
                "Register one complete inventory.",
            )
        ]
    path, raw = matches[0]
    try:
        entries = json.loads(raw)
    except ValueError:
        entries = None
    fields = {
        "id",
        "public_name",
        "kind",
        "public",
        "deterministic",
        "owner",
        "agents",
        "uses",
    }
    if not isinstance(entries, list) or any(
        not isinstance(item, dict)
        or set(item) != fields
        or not isinstance(item["id"], str)
        or not isinstance(item["public_name"], str)
        or not isinstance(item["kind"], str)
        or type(item["public"]) is not bool
        or type(item["deterministic"]) is not bool
        or not isinstance(item["owner"], str)
        or not isinstance(item["agents"], list)
        or not isinstance(item["uses"], list)
        for item in entries
    ):
        return [
            _finding(
                rule,
                path,
                "Malformed Operation catalog mirror.",
                "Declare id/public_name/kind/public/deterministic/owner/agents/uses.",
            )
        ]
    declared = {
        item["id"]: {k: v for k, v in item.items() if k != "id"} for item in entries
    }
    if len(declared) != len(entries):
        findings.append(
            _finding(
                rule,
                path,
                "Duplicate operation identity.",
                "Declare each identity once.",
            )
        )
    expected = _operation_code_inventory(root)
    if expected is None:
        return [
            _finding(
                rule,
                path,
                "The Operation catalog does not load.",
                "Repair the declarations so the catalog loads.",
            )
        ]
    for name in sorted(set(expected) - set(declared)):
        findings.append(
            _finding(
                rule,
                path,
                f"missing operation {name!r}.",
                "Add its complete declaration.",
            )
        )
    for name in sorted(set(declared) - set(expected)):
        findings.append(
            _finding(
                rule,
                path,
                f"unknown operation {name!r}.",
                "Remove the unimplemented declaration.",
            )
        )
    for name in sorted(set(expected) & set(declared)):
        if declared[name] != expected[name]:
            findings.append(
                _finding(
                    rule,
                    path,
                    f"Operation {name!r} differs from its code declaration.",
                    "Make the mirror record equal the fields its declaration states.",
                )
            )
    return findings


def _validate_spec_agents_block(root: Path, documents: dict[str, str]) -> list[Finding]:
    """Agents-owned metadata is checked against the actual Agent authority, not adapters."""
    rule = "CONCORDE-SPEC-AGENTS-001"
    inventory = _load_operations_package(root, "agents")
    matches = _metadata_inventories(root, documents, "concorde.agents")
    if inventory is None or len(matches) != 1:
        return [
            _finding(
                rule,
                "agents/__init__.py",
                "Exactly one Agents inventory and paired metadata declaration are required.",
                "Restore canonical Agents registration.",
            )
        ]
    expected = []
    for name in inventory.AGENTS:
        try:
            definition = importlib.import_module(
                f"{inventory.__name__}.{name}"
            ).DEFINITION
            validate_definition(definition)
        except (ImportError, AttributeError, ValueError) as error:
            return [
                _finding(
                    rule,
                    f"agents/{name}/__init__.py",
                    str(error),
                    "Restore the Agent definition.",
                )
            ]
        expected.append(
            {
                "id": name.replace("_", "-"),
                "source": definition.instructions,
                "hook": definition.hook,
            }
        )
    path, raw = matches[0]
    entries = json.loads(raw)
    fields = {"id", "source", "hook"}
    if not isinstance(entries, list) or any(
        not isinstance(e, dict)
        or set(e) != fields
        or not all(isinstance(v, str) for v in e.values())
        for e in entries
    ):
        return [
            _finding(
                rule,
                path,
                "Malformed Agents inventory.",
                "Use the exact Agent inventory fields.",
            )
        ]
    if len({e["id"] for e in entries}) != len(entries) or sorted(
        entries, key=lambda e: e["id"]
    ) != sorted(expected, key=lambda e: e["id"]):
        return [
            _finding(
                rule,
                path,
                "Agents metadata differs from the Agent definitions.",
                "Reconcile every Agent identity, instruction source and hook.",
            )
        ]
    declared = set(inventory.AGENTS)
    # An Agent package holds its instructions ``spec.md``; the Task subagent definitions under
    # ``agents/`` are Pi session's and have none.
    actual = {p.parent.name for p in (root / "agents").glob("*/spec.md")}
    if declared != actual or len(inventory.AGENTS) != len(set(inventory.AGENTS)):
        return [
            _finding(
                rule,
                "agents/__init__.py",
                "Agent source membership or identity is inconsistent.",
                "Declare each actual Agent once.",
            )
        ]
    return []


def _module_records(root: Path) -> dict[str, list[str]]:
    """The reading paths every registered Module owns, by Module identity."""
    try:
        registry = json.loads(
            (root / ".concorde/specs.json").read_text(encoding="utf-8")
        )
        return {
            record["id"]: [path for path in record["owns"] if isinstance(path, str)]
            for record in registry["modules"]
        }
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        return {}


def _binding_modules(root: Path, documents: dict[str, str]) -> list[tuple[str, str]]:
    """Every ``(module, realization entry)`` the registered documents' metadata declares."""
    from ..spec.repository_base import read_file

    bindings = []
    for path in documents:
        try:
            metadata = json.loads(read_file(root, path + ".json").decode())
            owner = metadata["document"]["owner"]
            for item in metadata.get("defines", []):
                if item.get("type") == "realization":
                    bindings.extend((owner, entry) for entry in item["entries"])
        except (ValueError, OSError, KeyError, TypeError, AttributeError):
            continue  # The document-unit validator reports invalid metadata.
    return bindings


def _type_owners(root: Path, documents: dict[str, str]) -> dict[str, set[str]]:
    """The owner Modules of every exported type identity and envelope.

    A capability's request and response belong to the Module its declaration names as owner;
    every other type belongs to the Modules that bind the file of the Python module that
    registered it.
    """
    import sys

    from ..operations.catalog import CATALOG, PACKAGE_ROOT
    from ..spec.repository_base import bound_by
    from ..spec.typed_data import registration_module

    bindings = _binding_modules(root, documents)

    def binders(module_name: str) -> set[str]:
        try:
            module = sys.modules.get(module_name) or importlib.import_module(
                module_name
            )
        except ImportError:
            return set()
        location = getattr(module, "__file__", None)
        if location is None:
            return set()
        try:
            relative = Path(location).resolve().relative_to(PACKAGE_ROOT).as_posix()
        except ValueError:
            return set()
        return {owner for owner, entry in bindings if bound_by(entry, relative)}

    declared = {}
    for operation in CATALOG.values():
        declared[operation.request_type] = operation.owner
        declared[operation.response_type] = operation.owner
    owners = {}
    for name in exported_types():
        owners[name] = (
            {declared[name]} if name in declared else binders(registration_module(name))
        )
    for name in _ENVELOPE_VERSIONS:
        owners.setdefault(name, binders(_ENVELOPE_MODULE))
    return owners


def _validate_spec_types(root: Path, documents: dict[str, str]) -> list[Finding]:
    """Every ``concorde-…@N`` token in a registered document names an exported identity at that
    exact version, and every exported identity appears at its version in a document its owner
    Module owns."""

    rule = "CONCORDE-SPEC-TYPES-001"
    findings: list[Finding] = []
    from ..spec.typed_data import type_version

    expected: dict[str, int] = {name: type_version(name) for name in exported_types()}
    expected.update(_ENVELOPE_VERSIONS)
    for path, text in documents.items():
        for token in sorted(set(_SPEC_TYPE_TOKEN.findall(text))):
            name, _, version_text = token.rpartition("@")
            version = int(version_text)
            if name not in expected:
                findings.append(
                    _finding(
                        rule,
                        path,
                        f"{name}@{version} names no exported identity.",
                        "Correct the identifier, or register the type in its owner's code.",
                    )
                )
            elif version != expected[name]:
                findings.append(
                    _finding(
                        rule,
                        path,
                        f"{name}@{version} does not match its exported version @{expected[name]}.",
                        f"Use {name}@{expected[name]}, the version the host actually exports.",
                    )
                )
    modules = _module_records(root)
    for name, owners in sorted(_type_owners(root, documents).items()):
        token = f"{name}@{expected[name]}"
        if not owners:
            findings.append(
                _finding(
                    rule,
                    ".concorde/specs.json",
                    f"exported identity {token} has no owner Module: no Module binds the code "
                    "that registers it.",
                    "Bind the registering file to the Module that owns the type.",
                )
            )
            continue
        owned = [path for owner in sorted(owners) for path in modules.get(owner, [])]
        if not any(token in documents.get(path, "") for path in owned):
            findings.append(
                _finding(
                    rule,
                    owned[0] if owned else ".concorde/specs.json",
                    f"exported identity {token} is not described in a document of its owner "
                    f"{', '.join(sorted(owners))}.",
                    "Describe the type at its exported version in its owner Module's Spec.",
                )
            )
    return findings


def _raised_error_codes(root: Path) -> set[str]:
    """Collect literal error codes, not diagnostic field names or message text.

    Package errors conventionally take (message, code); TypedDataError instead takes
    (code, field, message), and OperationExecutionError takes (message, outcome, code).
    Explicit code keywords and inline code records are also supported. This advisory
    scanner does not execute constructors or infer codes from arbitrary arguments.
    """

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
                name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else (
                        node.func.attr if isinstance(node.func, ast.Attribute) else None
                    )
                )
                if not name or not name.endswith("Error"):
                    continue
                position = {"TypedDataError": 0, "OperationExecutionError": 2}.get(
                    name, 1
                )
                positional = node.args[position : position + 1]
                for argument in (
                    *positional,
                    *(
                        keyword.value
                        for keyword in node.keywords
                        if keyword.arg == "code"
                    ),
                ):
                    if (
                        isinstance(argument, ast.Constant)
                        and isinstance(argument.value, str)
                        and _CODE_SHAPE.fullmatch(argument.value)
                    ):
                        codes.add(argument.value)
            elif isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values, strict=True):
                    if (
                        isinstance(key, ast.Constant)
                        and key.value == "code"
                        and isinstance(value, ast.Constant)
                        and isinstance(value.value, str)
                        and _CODE_SHAPE.fullmatch(value.value)
                    ):
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
        _finding(
            "CONCORDE-SPEC-ERRORS-001",
            path,
            f"error code {code!r} is raised under src/concorde but missing from the error table.",
            "Add a row describing this error code's meaning.",
            severity="advisory",
        )
        for code in missing
    ]


def _validate_spec_alignment(root: Path) -> list[Finding]:
    """Rule 4: the operation registry and wire promises agree with the executable code."""

    documents = _registered_documents(root)
    if documents is None:
        return [
            _finding(
                "CONCORDE-SPEC-OPERATIONS-001",
                ".concorde/specs.json",
                "no readable Spec registry was found.",
                "Register the operation registry and Harness admission documents.",
            )
        ]
    findings: list[Finding] = []
    findings.extend(_validate_spec_operations_block(root, documents))
    findings.extend(_validate_spec_agents_block(root, documents))
    findings.extend(_validate_spec_types(root, documents))
    findings.extend(_validate_spec_errors(root, documents))
    return findings


def _validate_build_outputs(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        verify_fresh(root)
    except BuildError as error:
        findings.append(
            _finding(
                "CONCORDE-BUILD-FRESH-001",
                "generated/build-manifest.json",
                str(error),
                "Run `python -m concorde build` to refresh generated/ outputs.",
            )
        )
        return findings
    try:
        current, differences = check_build(root)
    except BuildError as error:
        findings.append(
            _finding(
                "CONCORDE-BUILD-FRESH-001",
                "generated/build-manifest.json",
                str(error),
                "Run `python -m concorde build` to refresh generated/ outputs.",
            )
        )
        return findings
    if not current:
        findings.append(
            _finding(
                "CONCORDE-BUILD-DRIFT-001",
                "generated/",
                f"a pure rebuild differs from recorded outputs: {list(differences)}.",
                "Run `python -m concorde build` for the private Pi catalog and runtime projections.",
            )
        )
    return findings


def validate_package(root: Path) -> list[Finding]:
    """Validate the Concorde package: prompts, Operations, model profiles, contracts, Spec
    alignment, build outputs."""

    root = Path(root)
    findings: list[Finding] = []
    findings.extend(_validate_prompts(root))
    findings.extend(_validate_operation_modules(root))
    findings.extend(_validate_worker_profiles(root))
    findings.extend(_validate_contracts(root))
    findings.extend(_validate_spec_alignment(root))
    findings.extend(_validate_build_outputs(root))
    return findings
