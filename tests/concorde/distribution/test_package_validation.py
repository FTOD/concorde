"""One package validator over prompts, capability modules, contracts, Spec alignment and build
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
from unittest import mock

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.distribution import package_validation  # noqa: E402
from concorde.distribution.build import write_build  # noqa: E402
from concorde.spec.verification import verifies  # noqa: E402


VALID_CAPABILITY_INIT = '''CAPABILITIES = ("alpha",)


def external_name(name):
    return "concorde-" + name.replace("_", "-")
'''

VALID_ALPHA = '''from concorde.spec import contract_shapes as shapes
from agents import coordinator
from . import external_name

CLASS = "stage"
DETERMINISTIC = False
AGENTS = (coordinator.AGENT,)
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


VALID_AGENT_INIT = '''AGENTS = ("alpha",)


def external_name(name):
    return "concorde-" + name.replace("_", "-")
'''

VALID_AGENT_ALPHA_MODULE = '''from concorde.harness.agent_model import Agent, Constraints
from concorde.harness.effects import EffectDeclaration
from concorde.harness.harness import SPEC_CAPSULE

AGENT = Agent(
    name="alpha",
    spec="agents/alpha/spec.md",
    harness=SPEC_CAPSULE,
    constraints=Constraints(effects=EffectDeclaration(("spec-context",), (), False, "none")),
)
'''

VALID_AGENT_ALPHA_SPEC = '''# concorde-alpha

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
'''


def _agents_package(
    root: Path,
    *,
    init_source: str = VALID_AGENT_INIT,
    module_source: str = VALID_AGENT_ALPHA_MODULE,
    spec_source: str = VALID_AGENT_ALPHA_SPEC,
) -> None:
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
        shutil.copytree(REPOSITORY_ROOT / "skills", self.root / "skills")
        shutil.copytree(REPOSITORY_ROOT / "agents", self.root / "agents")

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
        edited = self.root / "prompts/workflow-host/gap-reporting.md"
        edited.write_text(edited.read_text(encoding="utf-8") + "\nSee concorde-not-a-real-identity.\n", encoding="utf-8")
        findings = package_validation._validate_prompts(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-PROMPT-NAME-001" for f in findings), findings)

    def test_name_lint_catches_an_unknown_token_in_an_agent_spec(self) -> None:
        edited = self.root / "agents/coordinator/spec.md"
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

    def test_agents_must_be_agent_objects(self) -> None:
        broken = VALID_ALPHA.replace("AGENTS = (coordinator.AGENT,)", 'AGENTS = ("not-an-agent",)')
        _capabilities_package(self.root, alpha_source=broken)
        findings = package_validation._validate_capability_modules(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-CAPABILITY-AGENTS-001" for f in findings), findings)

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

    @verifies("scenario.distribution.capability-determinism")
    def test_deterministic_requires_an_explicit_boolean(self) -> None:
        for declaration in ("", 'DETERMINISTIC = "false"\n', "DETERMINISTIC = 0\n",
                            "DETERMINISTIC = 1\n", "DETERMINISTIC = None\n"):
            with self.subTest(declaration=declaration):
                source = VALID_ALPHA.replace("DETERMINISTIC = False\n", declaration)
                _capabilities_package(self.root, alpha_source=source)
                findings = package_validation._validate_capability_modules(self.root)
                self.assertTrue(any(f.rule_id == "CONCORDE-CAPABILITY-CONSTANTS-001" for f in findings), findings)

    @verifies("scenario.distribution.capability-determinism")
    def test_deterministic_matches_direct_model_calls_independently_of_stage_class(self) -> None:
        for agents in ("()", "(coordinator.AGENT,)"):
            for deterministic in (True, False):
                with self.subTest(agents=agents, deterministic=deterministic):
                    source = VALID_ALPHA.replace("AGENTS = (coordinator.AGENT,)", f"AGENTS = {agents}")
                    source = source.replace("DETERMINISTIC = False", f"DETERMINISTIC = {deterministic}")
                    _capabilities_package(self.root, alpha_source=source)
                    findings = package_validation._validate_capability_modules(self.root)
                    invalid = any(f.rule_id == "CONCORDE-CAPABILITY-DETERMINISTIC-001" for f in findings)
                    self.assertEqual(invalid, deterministic != (agents == "()"), findings)

    @verifies("scenario.distribution.capability-determinism")
    def test_transitive_model_calls_do_not_trust_a_childs_false_deterministic_claim(self) -> None:
        init = VALID_CAPABILITY_INIT.replace('("alpha",)', '("alpha", "beta", "gamma")')
        pure = VALID_ALPHA.replace("AGENTS = (coordinator.AGENT,)", "AGENTS = ()")
        pure = pure.replace("DETERMINISTIC = False", "DETERMINISTIC = True")
        _capabilities_package(self.root, alpha_source=pure.replace("USES = ()", 'USES = ("beta",)'), init_source=init)
        (self.root / "capabilities/beta.py").write_text(pure.replace("USES = ()", 'USES = ("gamma",)'), encoding="utf-8")
        # All three incorrectly claim determinism; gamma launches an Agent.
        (self.root / "capabilities/gamma.py").write_text(
            VALID_ALPHA.replace("DETERMINISTIC = False", "DETERMINISTIC = True"), encoding="utf-8")
        findings = package_validation._validate_capability_modules(self.root)
        self.assertEqual(
            {f.source for f in findings if f.rule_id == "CONCORDE-CAPABILITY-DETERMINISTIC-001"},
            {f"capabilities/{name}.py" for name in ("alpha", "beta", "gamma")}, findings)

    @verifies("scenario.distribution.capability-determinism")
    def test_deterministic_composition_without_agents_is_valid(self) -> None:
        init = VALID_CAPABILITY_INIT.replace('("alpha",)', '("alpha", "beta")')
        pure = VALID_ALPHA.replace("AGENTS = (coordinator.AGENT,)", "AGENTS = ()")
        pure = pure.replace("DETERMINISTIC = False", "DETERMINISTIC = True")
        _capabilities_package(self.root, alpha_source=pure.replace("USES = ()", 'USES = ("beta",)'), init_source=init)
        (self.root / "capabilities/beta.py").write_text(pure, encoding="utf-8")
        self.assertEqual([], package_validation._validate_capability_modules(self.root))

    @verifies("scenario.distribution.capability-determinism")
    def test_host_routing_counts_as_a_model_call(self) -> None:
        pure = VALID_ALPHA.replace("AGENTS = (coordinator.AGENT,)", "AGENTS = ()")
        pure = pure.replace("DETERMINISTIC = False", "DETERMINISTIC = True")
        _capabilities_package(self.root, alpha_source=pure)
        with mock.patch.object(package_validation, "MAIN_ROUTED_CAPABILITIES", {"concorde-alpha"}):
            findings = package_validation._validate_capability_modules(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-CAPABILITY-DETERMINISTIC-001" for f in findings), findings)

    @verifies("scenario.distribution.capability-determinism")
    def test_lifecycle_cannot_admit_model_calls_even_when_flag_is_false(self) -> None:
        source = VALID_ALPHA.replace('CLASS = "stage"', 'CLASS = "lifecycle"')
        _capabilities_package(self.root, alpha_source=source)
        _skill(self.root)
        findings = package_validation._validate_capability_modules(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-CAPABILITY-DETERMINISTIC-001" for f in findings), findings)


class AgentRuleTests(unittest.TestCase):
    """New rules: Agent inventory, Agent Spec structure, Harness binding."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_clean_minimal_package_has_no_findings(self) -> None:
        _agents_package(self.root)
        findings = package_validation._validate_agents(self.root)
        self.assertEqual([], findings)

    def test_missing_agents_package_is_reported(self) -> None:
        findings = package_validation._validate_agents(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-AGENT-INVENTORY-001" for f in findings), findings)

    def test_inventory_mismatch_is_reported(self) -> None:
        init = VALID_AGENT_INIT.replace('AGENTS = ("alpha",)', 'AGENTS = ("alpha", "missing")')
        _agents_package(self.root, init_source=init)
        findings = package_validation._validate_agents(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-AGENT-INVENTORY-001" for f in findings), findings)

    def test_duplicate_agent_name_is_reported(self) -> None:
        init = VALID_AGENT_INIT.replace('AGENTS = ("alpha",)', 'AGENTS = ("alpha", "alpha")')
        _agents_package(self.root, init_source=init)
        findings = package_validation._validate_agents(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-AGENT-INVENTORY-001" for f in findings), findings)

    def test_missing_spec_is_reported(self) -> None:
        _agents_package(self.root)
        (self.root / "agents/alpha/spec.md").unlink()
        findings = package_validation._validate_agents(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-AGENT-SPEC-001" for f in findings), findings)

    def test_wrong_spec_path_is_reported(self) -> None:
        broken_module = VALID_AGENT_ALPHA_MODULE.replace(
            'spec="agents/alpha/spec.md",', 'spec="agents/alpha/wrong.md",'
        )
        _agents_package(self.root, module_source=broken_module)
        findings = package_validation._validate_agents(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-AGENT-SPEC-001" for f in findings), findings)

    def test_missing_heading_is_reported(self) -> None:
        broken_spec = VALID_AGENT_ALPHA_SPEC.replace("## Goals\n\nFixture goals.\n\n", "")
        _agents_package(self.root, spec_source=broken_spec)
        findings = package_validation._validate_agents(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-AGENT-SPEC-001" for f in findings), findings)

    def test_wrong_h1_is_reported(self) -> None:
        broken_spec = VALID_AGENT_ALPHA_SPEC.replace("# concorde-alpha", "# concorde-wrong-name")
        _agents_package(self.root, spec_source=broken_spec)
        findings = package_validation._validate_agents(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-AGENT-SPEC-001" for f in findings), findings)

    def test_unknown_harness_is_reported(self) -> None:
        broken_module = VALID_AGENT_ALPHA_MODULE.replace(
            "from concorde.harness.harness import SPEC_CAPSULE",
            "from concorde.harness.effects import EffectDeclaration as _E\n"
            "from concorde.harness.harness import LoopPolicy, harness\n"
            'SPEC_CAPSULE = harness(name="bogus-harness", workspace="capsule", '
            'effects=_E(("spec-context",), (), False, "none"), contexts=(), results=(), loop=LoopPolicy(60))',
        )
        _agents_package(self.root, module_source=broken_module)
        findings = package_validation._validate_agents(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-AGENT-HARNESS-001" for f in findings), findings)

    def test_unknown_capability_reference_is_reported(self) -> None:
        broken_module = VALID_AGENT_ALPHA_MODULE.replace(
            'constraints=Constraints(effects=EffectDeclaration(("spec-context",), (), False, "none")),',
            'constraints=Constraints(effects=EffectDeclaration(("spec-context",), (), False, "none"), '
            'capabilities=("concorde-not-real",)),',
        )
        _agents_package(self.root, module_source=broken_module)
        findings = package_validation._validate_agents(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-AGENT-HARNESS-001" for f in findings), findings)

    def test_context_outside_harness_is_reported(self) -> None:
        broken_module = VALID_AGENT_ALPHA_MODULE.replace(
            'constraints=Constraints(effects=EffectDeclaration(("spec-context",), (), False, "none")),',
            'constraints=Constraints(effects=EffectDeclaration(("spec-context",), (), False, "none"), '
            'contexts=("concorde-main-stage-context",)),',
        )
        _agents_package(self.root, module_source=broken_module)
        findings = package_validation._validate_agents(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-AGENT-HARNESS-001" for f in findings), findings)

    def test_widened_effects_is_reported(self) -> None:
        broken_module = VALID_AGENT_ALPHA_MODULE.replace(
            'constraints=Constraints(effects=EffectDeclaration(("spec-context",), (), False, "none")),',
            'constraints=Constraints(effects=EffectDeclaration(("spec-context", "implementation"), (), False, "none")),',
        )
        _agents_package(self.root, module_source=broken_module)
        findings = package_validation._validate_agents(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-AGENT-HARNESS-001" for f in findings), findings)

    def test_widened_limits_is_reported(self) -> None:
        broken_module = VALID_AGENT_ALPHA_MODULE.replace(
            'from concorde.harness.harness import SPEC_CAPSULE',
            'from concorde.harness.harness import LoopPolicy, SPEC_CAPSULE',
        ).replace(
            'constraints=Constraints(effects=EffectDeclaration(("spec-context",), (), False, "none")),',
            'constraints=Constraints(effects=EffectDeclaration(("spec-context",), (), False, "none"), '
            'limits=LoopPolicy(999999)),',
        )
        _agents_package(self.root, module_source=broken_module)
        findings = package_validation._validate_agents(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-AGENT-HARNESS-001" for f in findings), findings)


class ContractRuleTests(unittest.TestCase):
    """Rule 3: exported type identities are unique; generated/protocol/schemas.json matches json_schema."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_missing_schemas_file_is_reported(self) -> None:
        findings = package_validation._validate_contracts(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-CONTRACT-SCHEMA-001" for f in findings), findings)

    def test_stale_schemas_file_is_reported(self) -> None:
        (self.root / "generated/protocol").mkdir(parents=True)
        (self.root / "generated/protocol/schemas.json").write_text("{}", encoding="utf-8")
        findings = package_validation._validate_contracts(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-CONTRACT-SCHEMA-001" for f in findings), findings)

    def test_current_schemas_file_has_no_findings(self) -> None:
        (self.root / "generated/protocol").mkdir(parents=True)
        shutil.copy2(REPOSITORY_ROOT / "generated/protocol/schemas.json", self.root / "generated/protocol/schemas.json")
        self.assertEqual([], package_validation._validate_contracts(self.root))

    def test_duplicate_exported_type_identity_is_reported(self) -> None:
        (self.root / "generated/protocol").mkdir(parents=True)
        shutil.copy2(REPOSITORY_ROOT / "generated/protocol/schemas.json", self.root / "generated/protocol/schemas.json")
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
        shutil.copytree(REPOSITORY_ROOT / "protocol", self.root / "protocol")
        shutil.copytree(REPOSITORY_ROOT / "skills", self.root / "skills")
        shutil.copytree(REPOSITORY_ROOT / "agents", self.root / "agents")

    @verifies("scenario.distribution.build-check")
    def test_missing_manifest_is_reported(self) -> None:
        findings = package_validation._validate_build_outputs(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-BUILD-FRESH-001" for f in findings), findings)

    @verifies("scenario.distribution.build-check")
    def test_stale_source_is_reported(self) -> None:
        write_build(self.root, "all")
        edited = self.root / "prompts/workflow-host/gap-reporting.md"
        edited.write_text(edited.read_text(encoding="utf-8") + "\nChanged.\n", encoding="utf-8")
        findings = package_validation._validate_build_outputs(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-BUILD-FRESH-001" for f in findings), findings)

    @verifies("scenario.distribution.build-check")
    def test_drifted_output_is_reported(self) -> None:
        write_build(self.root, "all")
        target = self.root / "generated/agents/coordinator.md"
        target.write_text(target.read_text(encoding="utf-8") + "\ntampered\n", encoding="utf-8")
        findings = package_validation._validate_build_outputs(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-BUILD-DRIFT-001" for f in findings), findings)

    @verifies("scenario.distribution.build-check")
    def test_fresh_build_has_no_findings(self) -> None:
        write_build(self.root, "all")
        self.assertEqual([], package_validation._validate_build_outputs(self.root))

    @verifies("scenario.distribution.build-check")
    def test_unrelated_file_under_generated_has_no_findings(self) -> None:
        """`generated/` is a shared, ignored root; a file another tool writes there (for example
        the legacy initializer's diagram renders under `generated/architecture/`) must never be
        reported as drift."""
        write_build(self.root, "all")
        other = self.root / "generated/architecture"
        other.mkdir(parents=True)
        (other / "example.html").write_text("unrelated diagram render\n", encoding="utf-8")
        self.assertEqual([], package_validation._validate_build_outputs(self.root))

    @verifies("scenario.distribution.build-check")
    def test_unexpected_file_in_an_owned_directory_is_reported(self) -> None:
        write_build(self.root, "all")
        (self.root / "generated/agents/extra.md").write_text("not a build output\n", encoding="utf-8")
        findings = package_validation._validate_build_outputs(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-BUILD-DRIFT-001" for f in findings), findings)


def _registry(root: Path, *, documents: list[str]) -> None:
    registry = {
        "schema_version": 1, "project_id": "project.fixture", "entry_target": "service.alpha",
        "targets": [{
            "id": "service.alpha", "kind": "service", "title": "Alpha",
            "documents": documents, "scope_parent": None, "component_parent": None,
            "participates_in": [], "implementation": [], "features": [], "apis": [],
            "checks": [], "diagrams": [],
        }],
        "checks": [],
    }
    registry_path = root / ".concorde/specs.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry), encoding="utf-8")


def _document(root: Path, relative: str, document_id: str, body: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    header = json.dumps({"id": document_id, "targets": ["service.alpha"], "main_visible": True})
    path.write_text(f"```concorde-document\n{header}\n```\n\n# Fixture\n\n{body}\n", encoding="utf-8")


class SpecAlignmentCapabilitiesRuleTests(unittest.TestCase):
    """Rule 4a: exactly one registered concorde-capabilities block, equal to the code inventory."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_missing_registry_is_reported(self) -> None:
        findings = package_validation._validate_spec_alignment(self.root)
        self.assertTrue(any(f.rule_id == "CONCORDE-SPEC-CAPABILITIES-001" for f in findings), findings)

    @verifies("scenario.distribution.capability-determinism")
    def test_spec_deterministic_must_be_a_matching_boolean(self) -> None:
        _capabilities_package(self.root)
        for value in (False, True, "false", 0, 1, None, "missing"):
            with self.subTest(value=value):
                entry = {"id": "alpha", "class": "stage", "skill": None}
                if value != "missing":
                    entry["deterministic"] = value
                body = "```concorde-capabilities\n" + json.dumps([entry]) + "\n```"
                findings = package_validation._validate_spec_capabilities_block(self.root, {"specs/one.md": body})
                if value is False:
                    self.assertEqual([], findings)
                else:
                    self.assertTrue(any(f.rule_id == "CONCORDE-SPEC-CAPABILITIES-001" for f in findings), findings)

    def test_no_capabilities_block_is_reported(self) -> None:
        _capabilities_package(self.root)
        _document(self.root, "specs/doc.md", "document.doc", "No block here.")
        _registry(self.root, documents=["specs/doc.md"])
        findings = package_validation._validate_spec_capabilities_block(
            self.root, package_validation._registered_documents(self.root))
        self.assertTrue(any(f.rule_id == "CONCORDE-SPEC-CAPABILITIES-001" for f in findings), findings)

    def test_two_capabilities_blocks_is_reported(self) -> None:
        _capabilities_package(self.root)
        block = '```concorde-capabilities\n[{"id": "alpha", "class": "stage", "deterministic": false, "skill": null}]\n```'
        _document(self.root, "specs/one.md", "document.one", block)
        _document(self.root, "specs/two.md", "document.two", block)
        _registry(self.root, documents=["specs/one.md", "specs/two.md"])
        findings = package_validation._validate_spec_capabilities_block(
            self.root, package_validation._registered_documents(self.root))
        self.assertTrue(any(f.rule_id == "CONCORDE-SPEC-CAPABILITIES-001" for f in findings), findings)

    def test_malformed_json_is_reported(self) -> None:
        _capabilities_package(self.root)
        _document(self.root, "specs/one.md", "document.one", "```concorde-capabilities\nnot json\n```")
        _registry(self.root, documents=["specs/one.md"])
        findings = package_validation._validate_spec_capabilities_block(
            self.root, package_validation._registered_documents(self.root))
        self.assertTrue(any(f.rule_id == "CONCORDE-SPEC-CAPABILITIES-001" for f in findings), findings)

    def test_matching_capabilities_block_has_no_findings(self) -> None:
        global_alpha = VALID_ALPHA.replace('CLASS = "stage"', 'CLASS = "global"')
        _capabilities_package(self.root, alpha_source=global_alpha)
        _skill(self.root)
        block = "```concorde-capabilities\n" + json.dumps(
            [{"id": "alpha", "class": "global", "deterministic": False, "skill": "concorde-alpha"}]) + "\n```"
        _document(self.root, "specs/one.md", "document.one", block)
        _registry(self.root, documents=["specs/one.md"])
        findings = package_validation._validate_spec_capabilities_block(
            self.root, package_validation._registered_documents(self.root))
        self.assertEqual([], findings)

    def test_mismatched_class_is_reported(self) -> None:
        global_alpha = VALID_ALPHA.replace('CLASS = "stage"', 'CLASS = "global"')
        _capabilities_package(self.root, alpha_source=global_alpha)
        _skill(self.root)
        block = "```concorde-capabilities\n" + json.dumps(
            [{"id": "alpha", "class": "lifecycle", "deterministic": False, "skill": "concorde-alpha"}]) + "\n```"
        _document(self.root, "specs/one.md", "document.one", block)
        _registry(self.root, documents=["specs/one.md"])
        findings = package_validation._validate_spec_capabilities_block(
            self.root, package_validation._registered_documents(self.root))
        self.assertTrue(any(f.rule_id == "CONCORDE-SPEC-CAPABILITIES-001" for f in findings), findings)

    def test_missing_capability_entry_is_reported(self) -> None:
        _capabilities_package(self.root)
        _document(self.root, "specs/one.md", "document.one", "```concorde-capabilities\n[]\n```")
        _registry(self.root, documents=["specs/one.md"])
        findings = package_validation._validate_spec_capabilities_block(
            self.root, package_validation._registered_documents(self.root))
        self.assertTrue(any("missing capability" in f.message for f in findings), findings)

    def test_extra_capability_entry_is_reported(self) -> None:
        _capabilities_package(self.root)
        block = "```concorde-capabilities\n" + json.dumps([
            {"id": "alpha", "class": "stage", "deterministic": False, "skill": None},
            {"id": "ghost", "class": "stage", "deterministic": False, "skill": None},
        ]) + "\n```"
        _document(self.root, "specs/one.md", "document.one", block)
        _registry(self.root, documents=["specs/one.md"])
        findings = package_validation._validate_spec_capabilities_block(
            self.root, package_validation._registered_documents(self.root))
        self.assertTrue(any("unknown capability" in f.message for f in findings), findings)


class SpecAlignmentAgentsRuleTests(unittest.TestCase):
    """New rule: exactly one registered concorde-agents block, equal to the code inventory."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_no_agents_block_is_reported(self) -> None:
        _agents_package(self.root)
        _document(self.root, "specs/doc.md", "document.doc", "No block here.")
        _registry(self.root, documents=["specs/doc.md"])
        findings = package_validation._validate_spec_agents_block(
            self.root, package_validation._registered_documents(self.root))
        self.assertTrue(any(f.rule_id == "CONCORDE-SPEC-AGENTS-001" for f in findings), findings)

    def test_two_agents_blocks_is_reported(self) -> None:
        _agents_package(self.root)
        block = '```concorde-agents\n[{"id": "alpha", "harness": "spec-capsule", "capabilities": [], "modes": []}]\n```'
        _document(self.root, "specs/one.md", "document.one", block)
        _document(self.root, "specs/two.md", "document.two", block)
        _registry(self.root, documents=["specs/one.md", "specs/two.md"])
        findings = package_validation._validate_spec_agents_block(
            self.root, package_validation._registered_documents(self.root))
        self.assertTrue(any(f.rule_id == "CONCORDE-SPEC-AGENTS-001" for f in findings), findings)

    def test_malformed_json_is_reported(self) -> None:
        _agents_package(self.root)
        _document(self.root, "specs/one.md", "document.one", "```concorde-agents\nnot json\n```")
        _registry(self.root, documents=["specs/one.md"])
        findings = package_validation._validate_spec_agents_block(
            self.root, package_validation._registered_documents(self.root))
        self.assertTrue(any(f.rule_id == "CONCORDE-SPEC-AGENTS-001" for f in findings), findings)

    def test_matching_agents_block_has_no_findings(self) -> None:
        _agents_package(self.root)
        block = "```concorde-agents\n" + json.dumps(
            [{"id": "alpha", "harness": "spec-capsule", "capabilities": [], "modes": []}]) + "\n```"
        _document(self.root, "specs/one.md", "document.one", block)
        _registry(self.root, documents=["specs/one.md"])
        findings = package_validation._validate_spec_agents_block(
            self.root, package_validation._registered_documents(self.root))
        self.assertEqual([], findings)

    @verifies("scenario.distribution.build-check")
    def test_spec_mode_inventory_must_match_the_agent_definition(self) -> None:
        _agents_package(self.root)
        block = "```concorde-agents\n" + json.dumps([
            {"id": "alpha", "harness": "spec-capsule", "capabilities": [], "modes": ["invented"]}
        ]) + "\n```"
        findings = package_validation._validate_spec_agents_block(self.root, {"specs/one.md": block})
        self.assertTrue(any(f.rule_id == "CONCORDE-SPEC-AGENTS-001" for f in findings), findings)

    def test_mismatched_harness_is_reported(self) -> None:
        _agents_package(self.root)
        block = "```concorde-agents\n" + json.dumps(
            [{"id": "alpha", "harness": "discovery-capsule", "capabilities": [], "modes": []}]) + "\n```"
        _document(self.root, "specs/one.md", "document.one", block)
        _registry(self.root, documents=["specs/one.md"])
        findings = package_validation._validate_spec_agents_block(
            self.root, package_validation._registered_documents(self.root))
        self.assertTrue(any(f.rule_id == "CONCORDE-SPEC-AGENTS-001" for f in findings), findings)

    def test_missing_agent_entry_is_reported(self) -> None:
        _agents_package(self.root)
        _document(self.root, "specs/one.md", "document.one", "```concorde-agents\n[]\n```")
        _registry(self.root, documents=["specs/one.md"])
        findings = package_validation._validate_spec_agents_block(
            self.root, package_validation._registered_documents(self.root))
        self.assertTrue(any("missing agent" in f.message for f in findings), findings)

    def test_extra_agent_entry_is_reported(self) -> None:
        _agents_package(self.root)
        block = "```concorde-agents\n" + json.dumps([
            {"id": "alpha", "harness": "spec-capsule", "capabilities": [], "modes": []},
            {"id": "ghost", "harness": "spec-capsule", "capabilities": [], "modes": []},
        ]) + "\n```"
        _document(self.root, "specs/one.md", "document.one", block)
        _registry(self.root, documents=["specs/one.md"])
        findings = package_validation._validate_spec_agents_block(
            self.root, package_validation._registered_documents(self.root))
        self.assertTrue(any("unknown agent" in f.message for f in findings), findings)


class SpecAlignmentTypesRuleTests(unittest.TestCase):
    """Rule 4b: every concorde-...@N token in the workflow-host boundary document is an exported
    identity with that exact version, and every exported identity appears there at least once."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_missing_boundary_document_is_reported(self) -> None:
        _document(self.root, "specs/other.md", "document.other", "Nothing relevant.")
        _registry(self.root, documents=["specs/other.md"])
        findings = package_validation._validate_spec_types(
            self.root, package_validation._registered_documents(self.root))
        self.assertTrue(any(f.rule_id == "CONCORDE-SPEC-TYPES-001" for f in findings), findings)

    def test_unknown_type_token_is_reported(self) -> None:
        _document(self.root, "specs/boundary.md", "document.development.interfaces",
            "Mentions `concorde-not-a-real-type@1` here.")
        _registry(self.root, documents=["specs/boundary.md"])
        findings = package_validation._validate_spec_types(
            self.root, package_validation._registered_documents(self.root))
        self.assertTrue(any("names no exported identity" in f.message for f in findings), findings)

    def test_wrong_version_is_reported(self) -> None:
        _document(self.root, "specs/boundary.md", "document.development.interfaces",
            "Mentions `concorde-capability-invocation@2` here.")
        _registry(self.root, documents=["specs/boundary.md"])
        findings = package_validation._validate_spec_types(
            self.root, package_validation._registered_documents(self.root))
        self.assertTrue(any("does not match its exported version" in f.message for f in findings), findings)

    def test_missing_exported_identity_is_reported(self) -> None:
        _document(self.root, "specs/boundary.md", "document.development.interfaces", "Nothing about types here.")
        _registry(self.root, documents=["specs/boundary.md"])
        findings = package_validation._validate_spec_types(
            self.root, package_validation._registered_documents(self.root))
        self.assertTrue(any("does not appear in this document" in f.message for f in findings), findings)

    def test_the_real_boundary_document_has_no_findings(self) -> None:
        findings = package_validation._validate_spec_types(
            REPOSITORY_ROOT, package_validation._registered_documents(REPOSITORY_ROOT))
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
        self._package_module("fixture.py",
            'class FixtureError(ValueError):\n    pass\n\n\n'
            'def raise_it():\n    raise FixtureError("something went wrong", "fixture_missing_code")\n')
        _document(self.root, "specs/boundary.md", "document.development.interfaces", "No error table here.")
        _registry(self.root, documents=["specs/boundary.md"])
        findings = package_validation._validate_spec_errors(
            self.root, package_validation._registered_documents(self.root))
        self.assertTrue(any(f.rule_id == "CONCORDE-SPEC-ERRORS-001" and "fixture_missing_code" in f.message
                            and f.severity == "advisory" for f in findings), findings)

    def test_message_text_is_never_mistaken_for_a_code(self) -> None:
        self._package_module("fixture.py",
            'class FixtureError(ValueError):\n    pass\n\n\n'
            'def raise_it():\n    raise FixtureError("a plain message with spaces")\n')
        _document(self.root, "specs/boundary.md", "document.development.interfaces", "No error table here.")
        _registry(self.root, documents=["specs/boundary.md"])
        findings = package_validation._validate_spec_errors(
            self.root, package_validation._registered_documents(self.root))
        self.assertEqual([], findings)

    def test_documented_error_code_has_no_findings(self) -> None:
        self._package_module("fixture.py",
            'class FixtureError(ValueError):\n    pass\n\n\n'
            'def raise_it():\n    raise FixtureError("something went wrong", "fixture_code")\n')
        _document(self.root, "specs/boundary.md", "document.development.interfaces",
            "| Error code | Meaning |\n| --- | --- |\n| `fixture_code` | Something. |")
        _registry(self.root, documents=["specs/boundary.md"])
        findings = package_validation._validate_spec_errors(
            self.root, package_validation._registered_documents(self.root))
        self.assertEqual([], findings)

    def test_missing_boundary_document_has_no_findings(self) -> None:
        _document(self.root, "specs/other.md", "document.other", "Nothing relevant.")
        _registry(self.root, documents=["specs/other.md"])
        findings = package_validation._validate_spec_errors(
            self.root, package_validation._registered_documents(self.root))
        self.assertEqual([], findings)


class EndToEndPackageValidationTests(unittest.TestCase):
    def test_the_real_package_has_no_findings(self) -> None:
        self.assertEqual([], package_validation.validate_package(REPOSITORY_ROOT))


if __name__ == "__main__":
    unittest.main()
