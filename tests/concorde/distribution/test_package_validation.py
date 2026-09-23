"""One package validator over prompts, operation modules, contracts, Spec alignment and build
outputs (proposal §11). One test class per rule, using temporary fixture packages, plus an
end-to-end run against the real package.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.distribution import package_validation  # noqa: E402
from concorde.distribution.build import write_build  # noqa: E402
from concorde.spec.verification import verifies  # noqa: E402

VALID_OPERATION_INIT = 'OPERATIONS = ("alpha",)\n'

VALID_ALPHA = """from concorde.operations import shapes

KIND = "host"
PUBLIC = True
DETERMINISTIC = True
OWNER = "module.fixture"
AGENTS = ()
USES = ()
REQUEST = shapes.obj({})
RESPONSE = shapes.obj({})
REQUEST_VERSION = 1
RESPONSE_VERSION = 1
MUTATION = {"policy": "never", "actions": []}
WORKSPACE = "none"
TARGET = {"selection": "none", "hook": None}
DEFAULT_TASK = None
CONFIGURATION = "stored"
ENTRY_POINT = "concorde.validation.validate:run"
"""


def _operations_package(
    root: Path,
    *,
    alpha_source: str = VALID_ALPHA,
    init_source: str = VALID_OPERATION_INIT,
) -> None:
    package = root / "operations"
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").write_text(init_source, encoding="utf-8")
    (package / "alpha.py").write_text(alpha_source, encoding="utf-8")


def _guidance(root: Path, *, name: str = "concorde-alpha") -> None:
    guidance = root / f"prompts/operation-guidance/{name}.md"
    guidance.parent.mkdir(parents=True, exist_ok=True)
    guidance.write_text(
        f"---\nname: {name}\ndescription: Fixture guidance.\n---\n\n# {name}\n",
        encoding="utf-8",
    )


VALID_AGENT_INIT = """AGENTS = ("alpha",)


def external_name(name):
    return "concorde-" + name.replace("_", "-")
"""

VALID_AGENT_ALPHA_MODULE = """from concorde.harness.worker_profile import AgentDefinition

DEFINITION = AgentDefinition(
    name="alpha",
    instructions="agents/alpha/spec.md",
    workspace="capsule",
    phase="plan",
    context="concorde-agent-stage-context",
    result="concorde-agent-stage-result",
    reads=("spec-context",),
    writes=(),
    network=False,
    output_fields=("plan",),
    tools=("read", "grep", "find", "ls"),
    hook="fixture.hooks:alpha",
)
"""

VALID_AGENT_ALPHA_SPEC = """# concorde-alpha

Fixture Agent summary.

## Responsibilities

Fixture responsibilities.

## Goals

Fixture goals.

## Accepted input and feedback

Fixture input.

## Expected results

Fixture results.

## Completion conditions

Fixture completion.

## Missing information, failure and human decisions

Fixture gaps.
"""


def _agents_package(
    root: Path,
    *,
    init_source: str = VALID_AGENT_INIT,
    module_source: str = VALID_AGENT_ALPHA_MODULE,
    spec_source: str = VALID_AGENT_ALPHA_SPEC,
) -> None:
    _operations_package(root, init_source="OPERATIONS = ()", alpha_source="")
    (root / "operations/alpha.py").unlink()
    package = root / "agents"
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").write_text(init_source, encoding="utf-8")
    alpha = package / "alpha"
    alpha.mkdir(parents=True, exist_ok=True)
    (alpha / "__init__.py").write_text(module_source, encoding="utf-8")
    (alpha / "spec.md").write_text(spec_source, encoding="utf-8")


class PromptRuleTests(unittest.TestCase):
    """Rule 1: prompt resolver errors, reachability, and the concorde-* name lint."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(REPOSITORY_ROOT / "prompts", self.root / "prompts")
        shutil.copytree(REPOSITORY_ROOT / "protocol", self.root / "protocol")
        shutil.copytree(REPOSITORY_ROOT / "agents", self.root / "agents")
        shutil.copytree(REPOSITORY_ROOT / "operations", self.root / "operations")

    def test_clean_prompts_tree_has_no_findings(self) -> None:
        self.assertEqual([], package_validation._validate_prompts(self.root))

    def test_resolver_error_is_reported_with_its_rule_id(self) -> None:
        edited = self.root / "prompts/operation-guidance/concorde-context-solve.md"
        edited.write_text(
            edited.read_text(encoding="utf-8") + "\nUnbound {SOMETHING}.\n",
            encoding="utf-8",
        )
        findings = package_validation._validate_prompts(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-PROMPT-UNRESOLVED-001" for f in findings),
            findings,
        )

    def test_unreachable_prompt_is_reported(self) -> None:
        dead = self.root / "prompts/workflow-host/dead-text.md"
        dead.write_text(
            "---\naudience: worker\n---\n\nDead text nobody includes.\n",
            encoding="utf-8",
        )
        findings = package_validation._validate_prompts(self.root)
        self.assertTrue(
            any(
                f.rule_id == "CONCORDE-PROMPT-UNREACHABLE-001"
                and "dead-text.md" in f.source
                for f in findings
            ),
            findings,
        )

    def test_name_lint_catches_an_unknown_concorde_token(self) -> None:
        edited = self.root / "prompts/native/context-assessor.md"
        edited.write_text(
            edited.read_text(encoding="utf-8")
            + "\nSee concorde-not-a-real-identity.\n",
            encoding="utf-8",
        )
        findings = package_validation._validate_prompts(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-PROMPT-NAME-001" for f in findings), findings
        )

    def test_name_lint_catches_an_unknown_token_in_an_agent_spec(self) -> None:
        edited = self.root / "agents/planner/spec.md"
        edited.write_text(
            edited.read_text(encoding="utf-8")
            + "\nSee concorde-not-a-real-identity.\n",
            encoding="utf-8",
        )
        findings = package_validation._validate_prompts(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-PROMPT-NAME-001" for f in findings), findings
        )


class OperationModuleRuleTests(unittest.TestCase):
    """Rule 2: the Operation catalog loads and each public Operation has its own guidance.

    The declaration rules themselves are the catalog loader's; the package check reports the
    loader's refusal instead of repeating them.
    """

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def rules(self) -> set[str]:
        return {
            f.rule_id for f in package_validation._validate_operation_modules(self.root)
        }

    def test_clean_minimal_package_has_no_findings(self) -> None:
        _operations_package(self.root)
        _guidance(self.root)
        self.assertEqual([], package_validation._validate_operation_modules(self.root))

    def test_missing_operations_package_is_reported(self) -> None:
        self.assertEqual({"CONCORDE-OPERATION-INVENTORY-001"}, self.rules())

    def test_inventory_mismatch_is_reported(self) -> None:
        for init in ('OPERATIONS = ("alpha", "missing")\n', "OPERATIONS = ()\n"):
            with self.subTest(init=init):
                _operations_package(self.root, init_source=init)
                _guidance(self.root)
                self.assertEqual({"CONCORDE-OPERATION-INVENTORY-001"}, self.rules())

    @verifies("scenario.operations.invalid-declaration")
    def test_a_declaration_the_loader_refuses_is_reported_with_its_source(self) -> None:
        for before, after in (
            ('KIND = "host"', 'KIND = "graph"'),
            ("DETERMINISTIC = True", "DETERMINISTIC = False"),
            ("AGENTS = ()", 'AGENTS = (("ghost", "plan"),)'),
            ("USES = ()", 'USES = ("concorde-ghost",)'),
            ('WORKSPACE = "none"', 'WORKSPACE = "elsewhere"'),
            ("DEFAULT_TASK = None\n", ""),
            (
                'ENTRY_POINT = "concorde.validation.validate:run"',
                'ENTRY_POINT = "concorde.validation.validate:missing"',
            ),
        ):
            with self.subTest(declaration=after):
                _operations_package(
                    self.root, alpha_source=VALID_ALPHA.replace(before, after)
                )
                _guidance(self.root)
                [finding] = package_validation._validate_operation_modules(self.root)
                self.assertEqual("CONCORDE-OPERATION-INVENTORY-001", finding.rule_id)
                self.assertEqual("operations/alpha.py", finding.source)

    def test_public_operation_without_a_guidance_is_reported(self) -> None:
        _operations_package(self.root)
        self.assertEqual({"CONCORDE-OPERATION-GUIDANCE-001"}, self.rules())

    def test_guidance_without_a_public_operation_is_reported(self) -> None:
        _operations_package(
            self.root,
            alpha_source=VALID_ALPHA.replace("PUBLIC = True", "PUBLIC = False"),
        )
        _guidance(self.root)
        self.assertEqual({"CONCORDE-OPERATION-GUIDANCE-001"}, self.rules())

    @verifies("scenario.distribution.build-pi-session")
    def test_public_guidance_filename_must_match_the_public_name(self) -> None:
        _operations_package(self.root)
        _guidance(self.root, name="concorde-wrong")
        findings = package_validation._validate_operation_modules(self.root)
        self.assertEqual(
            {
                "prompts/operation-guidance/concorde-alpha.md",
                "prompts/operation-guidance/concorde-wrong.md",
            },
            {f.source for f in findings},
        )


class AgentRuleTests(unittest.TestCase):
    """Agent inventory, Agent instruction structure and Agent definition consistency."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_clean_minimal_package_has_no_findings(self) -> None:
        _agents_package(self.root)
        findings = package_validation._validate_worker_profiles(self.root)
        self.assertEqual([], findings)

    def test_missing_agents_package_is_reported(self) -> None:
        findings = package_validation._validate_worker_profiles(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-OPERATION-INVENTORY-001" for f in findings),
            findings,
        )

    def test_inventory_mismatch_is_reported(self) -> None:
        init = VALID_AGENT_INIT.replace(
            'AGENTS = ("alpha",)', 'AGENTS = ("alpha", "missing")'
        )
        _agents_package(self.root, init_source=init)
        findings = package_validation._validate_worker_profiles(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-OPERATION-INVENTORY-001" for f in findings),
            findings,
        )

    def test_duplicate_agent_name_is_reported(self) -> None:
        init = VALID_AGENT_INIT.replace(
            'AGENTS = ("alpha",)', 'AGENTS = ("alpha", "alpha")'
        )
        _agents_package(self.root, init_source=init)
        findings = package_validation._validate_worker_profiles(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-OPERATION-INVENTORY-001" for f in findings),
            findings,
        )

    def test_missing_spec_is_reported(self) -> None:
        _agents_package(self.root)
        (self.root / "agents/alpha/spec.md").unlink()
        findings = package_validation._validate_worker_profiles(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-AGENT-SPEC-001" for f in findings), findings
        )

    def test_wrong_spec_path_is_reported(self) -> None:
        broken_module = VALID_AGENT_ALPHA_MODULE.replace(
            'instructions="agents/alpha/spec.md",',
            'instructions="agents/alpha/wrong.md",',
        )
        _agents_package(self.root, module_source=broken_module)
        findings = package_validation._validate_worker_profiles(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-AGENT-SPEC-001" for f in findings), findings
        )

    def test_missing_heading_is_reported(self) -> None:
        broken_spec = VALID_AGENT_ALPHA_SPEC.replace(
            "## Goals\n\nFixture goals.\n\n", ""
        )
        _agents_package(self.root, spec_source=broken_spec)
        findings = package_validation._validate_worker_profiles(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-AGENT-SPEC-001" for f in findings), findings
        )

    def test_wrong_h1_is_reported(self) -> None:
        broken_spec = VALID_AGENT_ALPHA_SPEC.replace(
            "# concorde-alpha", "# concorde-wrong-name"
        )
        _agents_package(self.root, spec_source=broken_spec)
        findings = package_validation._validate_worker_profiles(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-AGENT-SPEC-001" for f in findings), findings
        )

    def test_network_effect_is_an_invalid_profile(self) -> None:
        broken_module = VALID_AGENT_ALPHA_MODULE.replace(
            "network=False,",
            "network=True,",
        )
        _agents_package(self.root, module_source=broken_module)
        findings = package_validation._validate_worker_profiles(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-AGENT-PROFILE-001" for f in findings), findings
        )

    def test_write_effect_outside_read_effect_is_an_invalid_profile(self) -> None:
        broken_module = VALID_AGENT_ALPHA_MODULE.replace(
            "writes=(),",
            'writes=("implementation",),',
        )
        _agents_package(self.root, module_source=broken_module)
        findings = package_validation._validate_worker_profiles(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-AGENT-PROFILE-001" for f in findings), findings
        )

    def test_non_positive_timeout_is_an_invalid_profile(self) -> None:
        broken_module = VALID_AGENT_ALPHA_MODULE.replace(
            'tools=("read", "grep", "find", "ls"),',
            'tools=("read", "grep", "find", "ls"),\n    timeout_seconds=0,',
        )
        _agents_package(self.root, module_source=broken_module)
        findings = package_validation._validate_worker_profiles(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-AGENT-PROFILE-001" for f in findings), findings
        )


class ContractRuleTests(unittest.TestCase):
    """Rule 3: every type is registered once; generated/schemas.json matches json_schema."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_missing_schemas_file_is_reported(self) -> None:
        findings = package_validation._validate_contracts(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-CONTRACT-SCHEMA-001" for f in findings), findings
        )

    def test_stale_schemas_file_is_reported(self) -> None:
        (self.root / "generated").mkdir(parents=True)
        (self.root / "generated/schemas.json").write_text("{}", encoding="utf-8")
        findings = package_validation._validate_contracts(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-CONTRACT-SCHEMA-001" for f in findings), findings
        )

    def test_current_schemas_file_has_no_findings(self) -> None:
        (self.root / "generated").mkdir(parents=True)
        shutil.copy2(
            REPOSITORY_ROOT / "generated/schemas.json",
            self.root / "generated/schemas.json",
        )
        self.assertEqual([], package_validation._validate_contracts(self.root))

    def test_a_conflicting_registration_is_reported_without_raising(self) -> None:
        from concorde.spec.typed_data import TypedDataError

        for code, rule in (
            ("duplicate_type", "CONCORDE-CONTRACT-UNIQUE-001"),
            ("invalid_schema", "CONCORDE-CONTRACT-SCHEMA-001"),
        ):
            with (
                self.subTest(code=code),
                patch.object(
                    package_validation,
                    "register_types",
                    side_effect=TypedDataError(
                        code, "concorde-context-solve-request", "conflict"
                    ),
                ),
            ):
                findings = package_validation._validate_contracts(self.root)
            self.assertEqual([rule], [f.rule_id for f in findings])
            self.assertIn("concorde-context-solve-request", str(findings))


class BuildOutputRuleTests(unittest.TestCase):
    """Rule 5: generated/build-manifest.json is present and fresh; a rebuild matches every output."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(REPOSITORY_ROOT / "prompts", self.root / "prompts")
        shutil.copytree(REPOSITORY_ROOT / "protocol", self.root / "protocol")
        shutil.copytree(REPOSITORY_ROOT / "agents", self.root / "agents")
        shutil.copytree(REPOSITORY_ROOT / "operations", self.root / "operations")

    @verifies("scenario.distribution.build-check")
    def test_missing_manifest_is_reported(self) -> None:
        findings = package_validation._validate_build_outputs(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-BUILD-FRESH-001" for f in findings), findings
        )

    @verifies("scenario.distribution.build-check")
    def test_stale_source_is_reported(self) -> None:
        write_build(self.root)
        edited = self.root / "prompts/native/context-assessor.md"
        edited.write_text(
            edited.read_text(encoding="utf-8") + "\nChanged.\n", encoding="utf-8"
        )
        findings = package_validation._validate_build_outputs(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-BUILD-FRESH-001" for f in findings), findings
        )

    @verifies("scenario.distribution.build-check")
    def test_drifted_output_is_reported(self) -> None:
        write_build(self.root)
        target = self.root / "generated/native/planner.md"
        target.write_text(
            target.read_text(encoding="utf-8") + "\ntampered\n", encoding="utf-8"
        )
        findings = package_validation._validate_build_outputs(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-BUILD-DRIFT-001" for f in findings), findings
        )

    @verifies("scenario.distribution.build-check")
    def test_fresh_build_has_no_findings(self) -> None:
        write_build(self.root)
        self.assertEqual([], package_validation._validate_build_outputs(self.root))

    @verifies("scenario.distribution.build-check")
    def test_unrelated_file_under_generated_has_no_findings(self) -> None:
        """`generated/` is a shared, ignored root; a file another tool writes there (for example
        the legacy initializer's diagram renders under `generated/architecture/`) must never be
        reported as drift."""
        write_build(self.root)
        other = self.root / "generated/architecture"
        other.mkdir(parents=True)
        (other / "example.html").write_text(
            "unrelated diagram render\n", encoding="utf-8"
        )
        self.assertEqual([], package_validation._validate_build_outputs(self.root))

    @verifies("scenario.distribution.build-check")
    def test_unexpected_file_in_an_owned_directory_is_reported(self) -> None:
        write_build(self.root)
        (self.root / "generated/native/extra.md").write_text(
            "not a build output\n", encoding="utf-8"
        )
        findings = package_validation._validate_build_outputs(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-BUILD-DRIFT-001" for f in findings), findings
        )


def _required_documents(root: Path) -> dict[str, str]:
    documents = package_validation._registered_documents(root)
    assert documents is not None, "fixture must have an explicit registry"
    return documents


def _registry(root: Path, *, documents: list[str]) -> None:
    registry = {
        "schema_version": 3,
        "modules": [
            {
                "id": "service.alpha",
                "title": "Alpha",
                "entry": "specs/alpha/module.md",
                "owns": documents,
                "contains": [],
                "uses": [],
                "includes": [],
                "participates": [],
            }
        ],
    }
    path = root / ".concorde/specs.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry))


def _document(root: Path, relative: str, document_id: str, body: str) -> None:
    """Create a native paired unit for isolated package-inventory tests."""
    import re

    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "schema_version": 3,
        "document": {"id": document_id, "owner": "service.alpha", "role": "module"},
        "defines": [],
        "relations": [],
    }
    for language, key in [
        ("concorde-operations", "concorde.operations"),
        ("concorde-agents", "concorde.agents"),
    ]:
        pattern = re.compile(r"```" + language + r"\n(.*?)\n```", re.S)
        for match in pattern.finditer(body):
            try:
                value = json.loads(match.group(1))
                if language == "concorde-operations" and isinstance(value, list):
                    expected = package_validation._operation_code_inventory(root) or {}
                    for entry in value:
                        if isinstance(entry, dict):
                            base = expected.get(
                                entry.get("id"), next(iter(expected.values()), {})
                            )
                            for field in ("kind", "owner", "agents", "uses"):
                                entry.setdefault(field, base.get(field))
            except ValueError:
                value = match.group(
                    1
                )  # Invalid inventory shape must still reach the rule under test.
            metadata.setdefault("extensions", {})[key] = value
        body = pattern.sub("Machine inventory is in the associated metadata.", body)
    path.write_text("# Fixture\n\n" + body + "\n")
    (root / (relative + ".json")).write_text(json.dumps(metadata))


def _mirror_entry(**changes) -> dict:
    return {
        "id": "alpha",
        "public_name": "concorde-alpha",
        "kind": "host",
        "public": True,
        "deterministic": True,
        "owner": "module.fixture",
        "agents": [],
        "uses": [],
        **changes,
    }


class SpecAlignmentOperationsRuleTests(unittest.TestCase):
    """Rule 4a: exactly one ``concorde.operations`` mirror, equal to the loaded catalog."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        _operations_package(self.root)
        _guidance(self.root)

    def findings(self, entries) -> list:
        block = "```concorde-operations\n" + json.dumps(entries) + "\n```"
        _document(self.root, "specs/one.md", "document.one", block)
        _registry(self.root, documents=["specs/one.md"])
        return package_validation._validate_spec_operations_block(
            self.root, _required_documents(self.root)
        )

    def test_missing_registry_is_reported(self) -> None:
        findings = package_validation._validate_spec_alignment(Path(tempfile.mkdtemp()))
        self.assertTrue(
            any(f.rule_id == "CONCORDE-SPEC-OPERATIONS-001" for f in findings),
            findings,
        )

    def test_matching_mirror_has_no_findings(self) -> None:
        self.assertEqual(
            {"alpha": {k: v for k, v in _mirror_entry().items() if k != "id"}},
            package_validation._operation_code_inventory(self.root),
        )
        self.assertEqual([], self.findings([_mirror_entry()]))

    @verifies("scenario.operations.invalid-declaration")
    def test_a_mirror_record_differing_from_its_declaration_is_reported(self) -> None:
        for changes in (
            {"deterministic": False},
            {"public": False},
            {"kind": "agent-call"},
            {"owner": "module.other"},
            {"agents": [{"agent": "planner", "phase": "plan"}]},
            {"uses": ["concorde-ghost"]},
            {"public_name": "concorde-wrong"},
        ):
            with self.subTest(changes=changes):
                findings = self.findings([_mirror_entry(**changes)])
                self.assertTrue(
                    any(f.rule_id == "CONCORDE-SPEC-OPERATIONS-001" for f in findings),
                    findings,
                )

    def test_a_malformed_mirror_is_reported(self) -> None:
        entry = _mirror_entry()
        for bad in (
            {**entry, "state": None},
            {**entry, "agents": "none"},
            {**entry, "deterministic": "true"},
        ):
            with self.subTest(entry=bad):
                findings = self.findings([bad])
                self.assertTrue(
                    any("Malformed" in f.message for f in findings), findings
                )

    def test_no_or_two_mirrors_are_reported(self) -> None:
        _document(self.root, "specs/doc.md", "document.doc", "No block here.")
        _registry(self.root, documents=["specs/doc.md"])
        findings = package_validation._validate_spec_operations_block(
            self.root, _required_documents(self.root)
        )
        self.assertTrue(any("Exactly one" in f.message for f in findings), findings)
        block = "```concorde-operations\n" + json.dumps([_mirror_entry()]) + "\n```"
        _document(self.root, "specs/one.md", "document.one", block)
        _document(self.root, "specs/two.md", "document.two", block)
        _registry(self.root, documents=["specs/one.md", "specs/two.md"])
        findings = package_validation._validate_spec_operations_block(
            self.root, _required_documents(self.root)
        )
        self.assertTrue(any("Exactly one" in f.message for f in findings), findings)

    def test_missing_and_extra_records_are_reported(self) -> None:
        self.assertTrue(
            any("missing operation" in f.message for f in self.findings([]))
        )
        findings = self.findings([_mirror_entry(), _mirror_entry(id="ghost")])
        self.assertTrue(any("unknown operation" in f.message for f in findings))


class SpecAlignmentTypesRuleTests(unittest.TestCase):
    """Every concorde-...@N token in a registered document is an exported identity with that exact
    version, and every exported identity appears at its version in a document of its owner."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_types_without_owner_documents_are_reported(self) -> None:
        _document(self.root, "specs/other.md", "document.other", "Nothing relevant.")
        _registry(self.root, documents=["specs/other.md"])
        findings = package_validation._validate_spec_types(
            self.root, _required_documents(self.root)
        )
        self.assertTrue(
            any(f.rule_id == "CONCORDE-SPEC-TYPES-001" for f in findings), findings
        )

    def test_unknown_type_token_is_reported(self) -> None:
        _document(
            self.root,
            "specs/boundary.md",
            "document.admission.contracts",
            "Mentions `concorde-not-a-real-type@1` here.",
        )
        _registry(self.root, documents=["specs/boundary.md"])
        findings = package_validation._validate_spec_types(
            self.root, _required_documents(self.root)
        )
        self.assertTrue(
            any("names no exported identity" in f.message for f in findings), findings
        )

    def test_wrong_version_is_reported(self) -> None:
        _document(
            self.root,
            "specs/boundary.md",
            "document.admission.contracts",
            "Mentions `concorde-operation-invocation@2` here.",
        )
        _registry(self.root, documents=["specs/boundary.md"])
        findings = package_validation._validate_spec_types(
            self.root, _required_documents(self.root)
        )
        self.assertTrue(
            any("does not match its exported version" in f.message for f in findings),
            findings,
        )

    def test_missing_exported_identity_is_reported(self) -> None:
        _document(
            self.root,
            "specs/boundary.md",
            "document.admission.contracts",
            "Nothing about types here.",
        )
        _registry(self.root, documents=["specs/boundary.md"])
        findings = package_validation._validate_spec_types(
            self.root, _required_documents(self.root)
        )
        # The fixture registers none of the owners: a capability's request names its declared
        # owner, a record type the Module binding its registering file (here none).
        self.assertTrue(
            any(
                "concorde-plan-request@1 is not described in a document of its owner "
                "module.planning" in f.message
                for f in findings
            ),
            findings,
        )
        self.assertTrue(
            any("has no owner Module" in f.message for f in findings), findings
        )

    def test_the_real_boundary_document_has_no_findings(self) -> None:
        findings = package_validation._validate_spec_types(
            REPOSITORY_ROOT, _required_documents(REPOSITORY_ROOT)
        )
        self.assertEqual([], findings)


class SpecAlignmentErrorsRuleTests(unittest.TestCase):
    """Advisory rule 4c: every error code literal raised under src/concorde appears in the
    workflow-host boundary document's error table."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def _package_module(self, filename: str, source: str) -> None:
        path = self.root / "src/concorde/harness" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")

    def test_missing_error_code_is_reported_as_advisory(self) -> None:
        self._package_module(
            "fixture.py",
            "class FixtureError(ValueError):\n    pass\n\n\n"
            'def raise_it():\n    raise FixtureError("something went wrong", "fixture_missing_code")\n',
        )
        _document(
            self.root,
            "specs/boundary.md",
            "document.admission.contracts",
            "No error table here.",
        )
        _registry(self.root, documents=["specs/boundary.md"])
        findings = package_validation._validate_spec_errors(
            self.root, _required_documents(self.root)
        )
        self.assertTrue(
            any(
                f.rule_id == "CONCORDE-SPEC-ERRORS-001"
                and "fixture_missing_code" in f.message
                and f.severity == "advisory"
                for f in findings
            ),
            findings,
        )

    def test_message_text_is_never_mistaken_for_a_code(self) -> None:
        self._package_module(
            "fixture.py",
            "class FixtureError(ValueError):\n    pass\n\n\n"
            'def raise_it():\n    raise FixtureError("a plain message with spaces")\n',
        )
        _document(
            self.root,
            "specs/boundary.md",
            "document.admission.contracts",
            "No error table here.",
        )
        _registry(self.root, documents=["specs/boundary.md"])
        findings = package_validation._validate_spec_errors(
            self.root, _required_documents(self.root)
        )
        self.assertEqual([], findings)

    @verifies("scenario.distribution.build-check")
    def test_error_scanner_distinguishes_code_from_diagnostic_fields(self) -> None:
        self._package_module(
            "fixture.py",
            'SpecError("message_token", "invalid_target", field="target_id")\n'
            'TypedDataError("invalid_field", "target_id", "message_token")\n'
            'OperationExecutionError("message_token", "failed", "execution_failed")\n'
            'FixtureError("message_token", code="fixture_code", field="focus_id")\n'
            'ValueError("message_token")\n'
            'record = {"code": "record_code", "field": "target_id"}\n',
        )
        self.assertEqual(
            {
                "invalid_target",
                "invalid_field",
                "execution_failed",
                "fixture_code",
                "record_code",
            },
            package_validation._raised_error_codes(self.root),
        )

    def test_documented_error_code_has_no_findings(self) -> None:
        self._package_module(
            "fixture.py",
            "class FixtureError(ValueError):\n    pass\n\n\n"
            'def raise_it():\n    raise FixtureError("something went wrong", "fixture_code")\n',
        )
        _document(
            self.root,
            "specs/boundary.md",
            "document.admission.contracts",
            "| Error code | Meaning |\n| --- | --- |\n| `fixture_code` | Something. |",
        )
        _registry(self.root, documents=["specs/boundary.md"])
        findings = package_validation._validate_spec_errors(
            self.root, _required_documents(self.root)
        )
        self.assertEqual([], findings)

    def test_missing_boundary_document_has_no_findings(self) -> None:
        _document(self.root, "specs/other.md", "document.other", "Nothing relevant.")
        _registry(self.root, documents=["specs/other.md"])
        findings = package_validation._validate_spec_errors(
            self.root, _required_documents(self.root)
        )
        self.assertEqual([], findings)


class EndToEndPackageValidationTests(unittest.TestCase):
    def test_the_real_package_has_no_findings(self) -> None:
        self.assertEqual([], package_validation.validate_package(REPOSITORY_ROOT))


if __name__ == "__main__":
    unittest.main()
