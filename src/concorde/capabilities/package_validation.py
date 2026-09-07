"""One package validator over prompts, capability modules, contracts and build outputs.

Replaces the former ``profile8_validation.py`` (deleted) and the capability-graph checks that used
to live in ``validation.py`` (also deleted): those validated the retired ``roles/``/``operations/``
package layout. This module implements proposal section 11 rules 1, 2, 3 and 5 (rule 4, Spec
alignment, is Stage C). Every finding carries a stable ``CONCORDE-…`` rule id.
"""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path

from ..frontmatter import FrontMatterError, parse_document
from ..model import Finding
from . import build
from .build import BuildError, check_build, verify_fresh
from .operation_data import json_schema
from .prompt_resolver import PromptResolverError, find_unreachable_prompts, resolve_role_prompt, resolve_skill_source
from .protocol_contracts import INTERNAL_SKILLS, OPERATIONS, exported_types, schemas
from .roles import ROLES, Role

_SUBJECT = "module.package-assets"

_NAME_TOKEN = re.compile(r"concorde-[a-z][a-z0-9-]*")

# Wire/Protocol vocabulary that legitimately appears as inline `concorde-…` prose terms but is not
# a skill name, a capability external name, or a member of protocol_contracts.schemas(): the two
# envelope type_ids validated ad hoc (never through DATA_SCHEMAS/schemas()), and two Protocol
# structural terms (a document ID prefix, a machine-readable participant block name) defined only
# in protocol/principles.md prose, not in any Python registry.
_PROTOCOL_VOCABULARY = frozenset(
    {
        "concorde-operation-invocation",
        "concorde-operation-configuration",
        "concorde-operation-result",
        "concorde-document",
        "concorde-participants",
    }
)


def _finding(rule: str, source: str, message: str, remediation: str) -> Finding:
    return Finding(rule, "error", source, message, remediation, subject_id=_SUBJECT)


def _prompt_roots() -> tuple[str, ...]:
    return tuple(build.SKILL_SOURCES.values()) + tuple(role.prompt for role in ROLES.values())


def _validate_prompts(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for relative in _prompt_roots():
        try:
            if relative.startswith("skills/"):
                resolve_skill_source(root, relative)
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
            "No skill source or role root reaches this prompt file.",
            "Include it from a root, or delete the dead prompt text.",
        ))

    known = (
        frozenset(build.SKILL_NAMES)
        | frozenset(OPERATIONS)
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
                    f"'{token}' names no skill, capability, role, or exported type.",
                    "Correct the identifier, or export/declare it if it is genuinely new.",
                ))
    return findings


def _load_capabilities_package(root: Path):
    """Load ``<root>/capabilities/__init__.py`` under a fresh private module name.

    Root-parametrized, unlike ``protocol_contracts.load_capability_inventory()`` (which always
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
    real package's fixed seven names, so a temporary fixture package with its own skill set is
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
    for name in sorted(declared):
        module = modules.get(name)
        source = f"capabilities/{name}.py"
        if module is None:
            findings.append(_finding("CONCORDE-CAPABILITY-CONSTANTS-001", source,
                f"capability module {name!r} could not be imported.",
                "Fix the import error in the capability module."))
            continue
        missing = [attribute for attribute in ("CLASS", "ROLES", "USES", "EXTERNAL_NAME", "REQUEST", "RESPONSE", "run")
                   if not hasattr(module, attribute)]
        if missing:
            findings.append(_finding("CONCORDE-CAPABILITY-CONSTANTS-001", source,
                f"capability module {name!r} is missing mandatory constants: {missing}.",
                "Declare CLASS, ROLES, USES, EXTERNAL_NAME, REQUEST, RESPONSE and run()."))
            continue
        if (not isinstance(module.CLASS, str) or not isinstance(module.ROLES, tuple)
                or not isinstance(module.USES, tuple) or not isinstance(module.EXTERNAL_NAME, str)
                or not isinstance(module.REQUEST, dict) or not isinstance(module.RESPONSE, dict)
                or not callable(module.run)):
            findings.append(_finding("CONCORDE-CAPABILITY-CONSTANTS-001", source,
                f"capability module {name!r} declares a mandatory constant with the wrong type.",
                "CLASS/EXTERNAL_NAME are str; ROLES/USES are tuples; REQUEST/RESPONSE are dict; run is callable."))
            continue
        if module.CLASS not in {"global", "lifecycle", "stage"}:
            findings.append(_finding("CONCORDE-CAPABILITY-CLASS-001", source,
                f"capability {name!r} declares CLASS {module.CLASS!r}.",
                "CLASS must be one of global, lifecycle, stage."))
        unknown_uses = sorted(set(module.USES) - declared)
        if unknown_uses:
            findings.append(_finding("CONCORDE-CAPABILITY-USES-001", source,
                f"capability {name!r} USES unknown capabilities: {unknown_uses}.",
                "Name only capabilities listed in capabilities.CAPABILITIES."))
        if not all(isinstance(role, Role) for role in module.ROLES):
            findings.append(_finding("CONCORDE-CAPABILITY-ROLES-001", source,
                f"capability {name!r} ROLES must contain only roles.Role objects.",
                "Reference roles by their Role constant, e.g. roles.COORDINATOR."))
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

    def visit(name: str, chain: tuple[str, ...]) -> None:
        module = modules.get(name)
        if module is None or name in visited:
            return
        if name in visiting:
            findings.append(_finding("CONCORDE-CAPABILITY-USES-001", f"capabilities/{name}.py",
                "capability USES graph is cyclic: " + " -> ".join((*chain, name)),
                "Remove one nested USES edge so the composition graph is acyclic."))
            return
        visiting.add(name)
        for used in module.USES:
            if used in declared:
                visit(used, (*chain, name))
        visiting.discard(name)
        visited.add(name)

    for name in sorted(declared):
        visit(name, ())
    return findings


def _validate_contracts(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    names = list(exported_types())
    if len(names) != len(set(names)):
        duplicates = sorted({name for name in names if names.count(name) > 1})
        findings.append(_finding("CONCORDE-CONTRACT-UNIQUE-001", "src/concorde/capabilities/protocol_contracts.py",
            f"exported type identities contain duplicates: {duplicates}.",
            "Keep every exported type identity globally unique."))
    schemas_path = root / "protocol/schemas.json"
    try:
        documented = json.loads(schemas_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        findings.append(_finding("CONCORDE-CONTRACT-SCHEMA-001", "protocol/schemas.json",
            f"cannot read tracked schema manifest: {error}",
            "Regenerate protocol/schemas.json from the exported contracts."))
        return findings
    expected = {name: json_schema(name) for name in names}
    if documented != expected:
        findings.append(_finding("CONCORDE-CONTRACT-SCHEMA-001", "protocol/schemas.json",
            "tracked protocol/schemas.json differs from the executable exported contracts.",
            "Regenerate protocol/schemas.json from concorde.capabilities.protocol_contracts.exported_types()."))
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
    """Validate the Concorde package: prompts, capability modules, contracts, build outputs."""

    root = Path(root)
    findings: list[Finding] = []
    findings.extend(_validate_prompts(root))
    findings.extend(_validate_capability_modules(root))
    findings.extend(_validate_contracts(root))
    findings.extend(_validate_build_outputs(root))
    return findings
