"""One package validator over prompts, capability modules, contracts, build outputs (proposal §11,
Stage B2 item 5). One test class per rule, using temporary fixture packages, plus an end-to-end run
against the real package.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.capabilities import package_validation  # noqa: E402
from concorde.capabilities.build import write_build  # noqa: E402


VALID_CAPABILITY_INIT = '''CAPABILITIES = ("alpha",)


def external_name(name):
    return "concorde-" + name.replace("_", "-")
'''

VALID_ALPHA = '''from concorde.capabilities import contract_shapes as shapes
from concorde.capabilities.roles import COORDINATOR
from . import external_name

CLASS = "stage"
ROLES = (COORDINATOR,)
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])
REQUEST = shapes.obj({})
RESPONSE = shapes.obj({})


def run(host, configuration, request):
    return {}
'''


def _capabilities_package(root: Path, *, alpha_source: str = VALID_ALPHA, init_source: str = VALID_CAPABILITY_INIT) -> None:
    package = root / "capabilities"
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").write_text(init_source, encoding="utf-8")
    (package / "alpha.py").write_text(alpha_source, encoding="utf-8")


def _skill(root: Path, *, capability: str = "alpha") -> None:
    skill = root / "skills/concorde-alpha/SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text(
        f"---\nname: concorde-alpha\ndescription: Fixture skill.\ncapability: {capability}\n---\n\n# concorde-alpha\n",
        encoding="utf-8",
    )


class PromptRuleTests(unittest.TestCase):
    """Rule 1: prompt resolver errors, reachability, and the concorde-* name lint."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(REPOSITORY_ROOT / "prompts", self.root / "prompts")
        shutil.copytree(REPOSITORY_ROOT / "skills", self.root / "skills")

    def test_clean_prompts_tree_has_no_findings(self) -> None:
        self.assertEqual([], package_validation._validate_prompts(self.root))

    def test_resolver_error_is_reported_with_its_rule_id(self) -> None:
        edited = self.root / "skills/concorde-main/SKILL.md"
        edited.write_text(edited.read_text(encoding="utf-8") + "\nUnbound {SOMETHING}.\n", encoding="utf-8")
        findings = package_validation._validate_prompts(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-PROMPT-UNRESOLVED-001" for f in findings), findings)

    def test_unreachable_prompt_is_reported(self) -> None:
        dead = self.root / "prompts/workflow-host/dead-text.md"
        dead.write_text("---\naudience: worker\n---\n\nDead text nobody includes.\n", encoding="utf-8")
        findings = package_validation._validate_prompts(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-PROMPT-UNREACHABLE-001" and "dead-text.md" in f.source for f in findings),
            findings,
        )

    def test_name_lint_catches_an_unknown_concorde_token(self) -> None:
        edited = self.root / "prompts/workflow-host/coordinator.md"
        edited.write_text(edited.read_text(encoding="utf-8") + "\nSee concorde-not-a-real-identity.\n", encoding="utf-8")
        findings = package_validation._validate_prompts(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-PROMPT-NAME-001" for f in findings), findings)


class CapabilityModuleRuleTests(unittest.TestCase):
    """Rule 2: capability module inventory, mandatory constants, CLASS, USES, ROLES, skills."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_clean_minimal_package_has_no_findings(self) -> None:
        _capabilities_package(self.root)
        findings = package_validation._validate_capability_modules(self.root)
        self.assertEqual([], findings)

    def test_inventory_mismatch_is_reported(self) -> None:
        init = VALID_CAPABILITY_INIT.replace('CAPABILITIES = ("alpha",)', 'CAPABILITIES = ("alpha", "missing")')
        _capabilities_package(self.root, init_source=init)
        findings = package_validation._validate_capability_modules(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-CAPABILITY-INVENTORY-001" for f in findings), findings)

    def test_missing_mandatory_constant_is_reported(self) -> None:
        broken = VALID_ALPHA.replace("RESPONSE = shapes.obj({})\n", "")
        _capabilities_package(self.root, alpha_source=broken)
        findings = package_validation._validate_capability_modules(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-CAPABILITY-CONSTANTS-001" for f in findings), findings)

    def test_wrong_constant_type_is_reported(self) -> None:
        broken = VALID_ALPHA.replace("USES = ()", "USES = []")
        _capabilities_package(self.root, alpha_source=broken)
        findings = package_validation._validate_capability_modules(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-CAPABILITY-CONSTANTS-001" for f in findings), findings)

    def test_invalid_class_value_is_reported(self) -> None:
        broken = VALID_ALPHA.replace('CLASS = "stage"', 'CLASS = "bogus"')
        _capabilities_package(self.root, alpha_source=broken)
        findings = package_validation._validate_capability_modules(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-CAPABILITY-CLASS-001" for f in findings), findings)

    def test_unknown_uses_name_is_reported(self) -> None:
        broken = VALID_ALPHA.replace("USES = ()", 'USES = ("unknown",)')
        _capabilities_package(self.root, alpha_source=broken)
        findings = package_validation._validate_capability_modules(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-CAPABILITY-USES-001" for f in findings), findings)

    def test_uses_cycle_is_reported(self) -> None:
        init = VALID_CAPABILITY_INIT.replace('CAPABILITIES = ("alpha",)', 'CAPABILITIES = ("alpha", "beta")')
        alpha = VALID_ALPHA.replace("USES = ()", 'USES = ("beta",)')
        beta = VALID_ALPHA.replace("USES = ()", 'USES = ("alpha",)')
        _capabilities_package(self.root, alpha_source=alpha, init_source=init)
        (self.root / "capabilities/beta.py").write_text(beta, encoding="utf-8")
        findings = package_validation._validate_capability_modules(self.root)
        self.assertTrue(any("cyclic" in f.message for f in findings), findings)

    def test_roles_must_be_role_objects(self) -> None:
        broken = VALID_ALPHA.replace("ROLES = (COORDINATOR,)", 'ROLES = ("not-a-role",)')
        _capabilities_package(self.root, alpha_source=broken)
        findings = package_validation._validate_capability_modules(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-CAPABILITY-ROLES-001" for f in findings), findings)

    def test_global_capability_without_a_skill_is_reported(self) -> None:
        broken = VALID_ALPHA.replace('CLASS = "stage"', 'CLASS = "global"')
        _capabilities_package(self.root, alpha_source=broken)
        findings = package_validation._validate_capability_modules(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-CAPABILITY-SKILL-001" for f in findings), findings)

    def test_stage_capability_with_a_skill_is_reported(self) -> None:
        _capabilities_package(self.root)
        _skill(self.root)
        findings = package_validation._validate_capability_modules(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-CAPABILITY-SKILL-001" for f in findings), findings)

    def test_global_capability_with_exactly_one_skill_has_no_skill_finding(self) -> None:
        broken = VALID_ALPHA.replace('CLASS = "stage"', 'CLASS = "global"')
        _capabilities_package(self.root, alpha_source=broken)
        _skill(self.root)
        findings = package_validation._validate_capability_modules(self.root)
        self.assertFalse(any(f.rule_id == "CONCORDE-CAPABILITY-SKILL-001" for f in findings), findings)

    def test_external_name_mismatch_is_reported(self) -> None:
        broken = VALID_ALPHA.replace(
            'EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])',
            'EXTERNAL_NAME = "concorde-wrong-name"',
        )
        _capabilities_package(self.root, alpha_source=broken)
        findings = package_validation._validate_capability_modules(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-CAPABILITY-EXTERNALNAME-001" for f in findings), findings)

    def test_missing_capabilities_package_is_reported(self) -> None:
        findings = package_validation._validate_capability_modules(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-CAPABILITY-INVENTORY-001" for f in findings), findings)


class ContractRuleTests(unittest.TestCase):
    """Rule 3: exported type identities are unique; protocol/schemas.json matches json_schema."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_missing_schemas_file_is_reported(self) -> None:
        findings = package_validation._validate_contracts(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-CONTRACT-SCHEMA-001" for f in findings), findings)

    def test_stale_schemas_file_is_reported(self) -> None:
        (self.root / "protocol").mkdir(parents=True)
        (self.root / "protocol/schemas.json").write_text("{}", encoding="utf-8")
        findings = package_validation._validate_contracts(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-CONTRACT-SCHEMA-001" for f in findings), findings)

    def test_current_schemas_file_has_no_findings(self) -> None:
        (self.root / "protocol").mkdir(parents=True)
        shutil.copy2(REPOSITORY_ROOT / "protocol/schemas.json", self.root / "protocol/schemas.json")
        self.assertEqual([], package_validation._validate_contracts(self.root))

    def test_duplicate_exported_type_identity_is_reported(self) -> None:
        (self.root / "protocol").mkdir(parents=True)
        shutil.copy2(REPOSITORY_ROOT / "protocol/schemas.json", self.root / "protocol/schemas.json")
        with mock.patch.object(
            package_validation, "exported_types",
            return_value=("concorde-main-request", "concorde-main-request"),
        ):
            findings = package_validation._validate_contracts(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-CONTRACT-UNIQUE-001" for f in findings), findings)


class BuildOutputRuleTests(unittest.TestCase):
    """Rule 5: generated/build-manifest.json is present and fresh; a rebuild matches every output."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(REPOSITORY_ROOT / "prompts", self.root / "prompts")
        shutil.copytree(REPOSITORY_ROOT / "skills", self.root / "skills")

    def test_missing_manifest_is_reported(self) -> None:
        findings = package_validation._validate_build_outputs(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-BUILD-FRESH-001" for f in findings), findings)

    def test_stale_source_is_reported(self) -> None:
        write_build(self.root, "all")
        edited = self.root / "prompts/workflow-host/gap-reporting.md"
        edited.write_text(edited.read_text(encoding="utf-8") + "\nChanged.\n", encoding="utf-8")
        findings = package_validation._validate_build_outputs(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-BUILD-FRESH-001" for f in findings), findings)

    def test_drifted_output_is_reported(self) -> None:
        write_build(self.root, "all")
        target = self.root / "generated/roles/coordinator.md"
        target.write_text(target.read_text(encoding="utf-8") + "\ntampered\n", encoding="utf-8")
        findings = package_validation._validate_build_outputs(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-BUILD-DRIFT-001" for f in findings), findings)

    def test_fresh_build_has_no_findings(self) -> None:
        write_build(self.root, "all")
        self.assertEqual([], package_validation._validate_build_outputs(self.root))


class EndToEndPackageValidationTests(unittest.TestCase):
    def test_the_real_package_has_no_findings(self) -> None:
        self.assertEqual([], package_validation.validate_package(REPOSITORY_ROOT))


if __name__ == "__main__":
    unittest.main()
