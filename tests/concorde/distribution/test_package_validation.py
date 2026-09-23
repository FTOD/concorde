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

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.distribution import package_validation  # noqa: E402
from concorde.distribution.build import write_build  # noqa: E402
from concorde.spec.verification import verifies  # noqa: E402

VALID_OPERATION_INIT = """OPERATIONS = ("alpha",)


def external_name(name):
    return "concorde-" + name.replace("_", "-")
"""

VALID_ALPHA = """from concorde.spec import contract_shapes as shapes
from agents import planner
from . import external_name
from concorde.harness.operation_state import StateContract

KIND = "operation"
PUBLIC = False
CONTEXT_SELECTION = "bound"
DETERMINISTIC = False
PROFILE = planner.PROFILE
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])
REQUEST = shapes.obj({})
RESPONSE = shapes.obj({})
STATE = StateContract("concorde-agent-stage-context", "concorde-agent-stage-result")


def run(state, runtime):
    return {}
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


def _guidance(root: Path, *, operation: str = "alpha") -> None:
    guidance = root / "prompts/operation-guidance/concorde-alpha.md"
    guidance.parent.mkdir(parents=True, exist_ok=True)
    guidance.write_text(
        f"---\nname: concorde-alpha\ndescription: Fixture guidance.\noperation: {operation}\n---\n\n# concorde-alpha\n",
        encoding="utf-8",
    )


VALID_AGENT_INIT = """DOMAIN_AGENTS = ("alpha",)


def external_name(name):
    return "concorde-" + name.replace("_", "-")
"""

VALID_AGENT_ALPHA_MODULE = """from concorde.harness.worker_profile import WorkerProfile, Contract
from concorde.harness.effects import EffectDeclaration

PROFILE = WorkerProfile(
    name="alpha",
    spec="agents/alpha/spec.md",
    workspace="capsule",
    contract=Contract(
        phase="plan",
        context="concorde-agent-stage-context",
        result="concorde-agent-stage-result",
        effects=EffectDeclaration(("spec-context",), (), False, "none"),
        output_fields=("plan",),
    ),
    tools=("read", "grep", "find", "ls"),
)
"""

VALID_AGENT_ALPHA_SPEC = """# concorde-alpha

Fixture WorkerProfile summary.

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
    """Rule 2: operation module inventory, mandatory properties, context selection, USES, model profiles, Operation guidance."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_clean_minimal_package_has_no_findings(self) -> None:
        _operations_package(self.root)
        findings = package_validation._validate_operation_modules(self.root)
        self.assertEqual([], findings)

    def test_inventory_mismatch_is_reported(self) -> None:
        init = VALID_OPERATION_INIT.replace(
            'OPERATIONS = ("alpha",)', 'OPERATIONS = ("alpha", "missing")'
        )
        _operations_package(self.root, init_source=init)
        findings = package_validation._validate_operation_modules(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-OPERATION-INVENTORY-001" for f in findings),
            findings,
        )

    def test_missing_mandatory_constant_is_reported(self) -> None:
        broken = VALID_ALPHA.replace(
            'STATE = StateContract("concorde-agent-stage-context", "concorde-agent-stage-result")\n',
            "",
        )
        _operations_package(self.root, alpha_source=broken)
        findings = package_validation._validate_operation_modules(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-OPERATION-CONSTANTS-001" for f in findings),
            findings,
        )

    def test_wrong_constant_type_is_reported(self) -> None:
        broken = VALID_ALPHA.replace("USES = ()", "USES = []")
        _operations_package(self.root, alpha_source=broken)
        findings = package_validation._validate_operation_modules(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-OPERATION-CONSTANTS-001" for f in findings),
            findings,
        )

    def test_invalid_context_selection_is_reported(self) -> None:
        broken = VALID_ALPHA.replace(
            'CONTEXT_SELECTION = "bound"', 'CONTEXT_SELECTION = "bogus"'
        )
        _operations_package(self.root, alpha_source=broken)
        findings = package_validation._validate_operation_modules(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-OPERATION-CONTEXT-001" for f in findings),
            findings,
        )

    def test_public_requires_an_explicit_boolean(self) -> None:
        for declaration in (
            "",
            'PUBLIC = "false"\n',
            "PUBLIC = 0\n",
            "PUBLIC = None\n",
        ):
            with self.subTest(declaration=declaration):
                _operations_package(
                    self.root,
                    alpha_source=VALID_ALPHA.replace("PUBLIC = False\n", declaration),
                )
                findings = package_validation._validate_operation_modules(self.root)
                self.assertTrue(
                    any(
                        f.rule_id == "CONCORDE-OPERATION-CONSTANTS-001"
                        for f in findings
                    ),
                    findings,
                )

    def test_unknown_uses_name_is_reported(self) -> None:
        broken = VALID_ALPHA.replace("USES = ()", 'USES = ("unknown",)')
        _operations_package(self.root, alpha_source=broken)
        findings = package_validation._validate_operation_modules(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-OPERATION-USES-001" for f in findings), findings
        )

    def test_uses_cycle_is_reported(self) -> None:
        init = VALID_OPERATION_INIT.replace(
            'OPERATIONS = ("alpha",)', 'OPERATIONS = ("alpha", "beta")'
        )
        alpha = VALID_ALPHA.replace("USES = ()", 'USES = ("beta",)')
        beta = VALID_ALPHA.replace("USES = ()", 'USES = ("alpha",)')
        _operations_package(self.root, alpha_source=alpha, init_source=init)
        (self.root / "operations/beta.py").write_text(beta, encoding="utf-8")
        findings = package_validation._validate_operation_modules(self.root)
        self.assertTrue(any("cyclic" in f.message for f in findings), findings)

    def test_private_deterministic_state_node_needs_no_wire_wrapper(self) -> None:
        source = VALID_ALPHA.replace("PROFILE = planner.PROFILE", "PROFILE = None")
        source = source.replace("DETERMINISTIC = False", "DETERMINISTIC = True")
        source = source.replace("REQUEST = shapes.obj({})\n", "").replace(
            "RESPONSE = shapes.obj({})\n", ""
        )
        _operations_package(self.root, alpha_source=source)
        self.assertEqual([], package_validation._validate_operation_modules(self.root))

    def test_state_types_and_profile_must_agree(self) -> None:
        for replacement in (
            'StateContract("not-registered", None)',
            'StateContract("concorde-main-stage-context", "concorde-main-stage-result")',
        ):
            source = VALID_ALPHA.replace(
                'StateContract("concorde-agent-stage-context", "concorde-agent-stage-result")',
                replacement,
            )
            _operations_package(self.root, alpha_source=source)
            findings = package_validation._validate_operation_modules(self.root)
            self.assertTrue(
                any(f.rule_id == "CONCORDE-OPERATION-STATE-001" for f in findings),
                findings,
            )

    def test_duplicate_uses_is_rejected(self) -> None:
        _operations_package(
            self.root,
            alpha_source=VALID_ALPHA.replace("USES = ()", 'USES = ("alpha", "alpha")'),
        )
        findings = package_validation._validate_operation_modules(self.root)
        self.assertTrue(
            any("duplicate Operation" in f.message for f in findings), findings
        )

    def test_profiles_must_be_worker_profile_objects(self) -> None:
        broken = VALID_ALPHA.replace(
            "PROFILE = planner.PROFILE", 'PROFILE = "not-a-profile"'
        )
        _operations_package(self.root, alpha_source=broken)
        findings = package_validation._validate_operation_modules(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-OPERATION-CONSTANTS-001" for f in findings),
            findings,
        )

    def test_public_operation_without_a_guidance_is_reported(self) -> None:
        broken = VALID_ALPHA.replace("PUBLIC = False", "PUBLIC = True")
        _operations_package(self.root, alpha_source=broken)
        findings = package_validation._validate_operation_modules(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-OPERATION-GUIDANCE-001" for f in findings),
            findings,
        )

    def test_nonpublic_operation_with_a_guidance_is_reported(self) -> None:
        _operations_package(self.root)
        _guidance(self.root)
        findings = package_validation._validate_operation_modules(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-OPERATION-GUIDANCE-001" for f in findings),
            findings,
        )

    def test_public_operation_with_exactly_one_guidance_has_no_guidance_finding(
        self,
    ) -> None:
        broken = VALID_ALPHA.replace("PUBLIC = False", "PUBLIC = True")
        _operations_package(self.root, alpha_source=broken)
        _guidance(self.root)
        findings = package_validation._validate_operation_modules(self.root)
        self.assertFalse(
            any(f.rule_id == "CONCORDE-OPERATION-GUIDANCE-001" for f in findings),
            findings,
        )

    @verifies("scenario.distribution.build-pi-session")
    def test_public_guidance_filename_must_match_external_name(self) -> None:
        _operations_package(
            self.root,
            alpha_source=VALID_ALPHA.replace("PUBLIC = False", "PUBLIC = True"),
        )
        _guidance(self.root)
        source = self.root / "prompts/operation-guidance/concorde-alpha.md"
        source.rename(source.with_name("concorde-wrong.md"))
        findings = package_validation._validate_operation_modules(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-OPERATION-GUIDANCE-001" for f in findings),
            findings,
        )

    def test_external_name_mismatch_is_reported(self) -> None:
        broken = VALID_ALPHA.replace(
            'EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])',
            'EXTERNAL_NAME = "concorde-wrong-name"',
        )
        _operations_package(self.root, alpha_source=broken)
        findings = package_validation._validate_operation_modules(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-OPERATION-EXTERNALNAME-001" for f in findings),
            findings,
        )

    def test_missing_operations_package_is_reported(self) -> None:
        findings = package_validation._validate_operation_modules(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-OPERATION-INVENTORY-001" for f in findings),
            findings,
        )

    @verifies("scenario.operations.invalid-declaration")
    def test_deterministic_requires_an_explicit_boolean(self) -> None:
        for declaration in (
            "",
            'DETERMINISTIC = "false"\n',
            "DETERMINISTIC = 0\n",
            "DETERMINISTIC = 1\n",
            "DETERMINISTIC = None\n",
        ):
            with self.subTest(declaration=declaration):
                source = VALID_ALPHA.replace("DETERMINISTIC = False\n", declaration)
                _operations_package(self.root, alpha_source=source)
                findings = package_validation._validate_operation_modules(self.root)
                self.assertTrue(
                    any(
                        f.rule_id == "CONCORDE-OPERATION-CONSTANTS-001"
                        for f in findings
                    ),
                    findings,
                )

    @verifies("scenario.operations.invalid-declaration")
    def test_deterministic_matches_direct_model_calls_from_direct_model_calls(
        self,
    ) -> None:
        for profile in ("None", "planner.PROFILE"):
            for deterministic in (True, False):
                with self.subTest(profile=profile, deterministic=deterministic):
                    source = VALID_ALPHA.replace(
                        "PROFILE = planner.PROFILE", f"PROFILE = {profile}"
                    )
                    source = source.replace(
                        "DETERMINISTIC = False", f"DETERMINISTIC = {deterministic}"
                    )
                    _operations_package(self.root, alpha_source=source)
                    findings = package_validation._validate_operation_modules(self.root)
                    invalid = any(
                        f.rule_id == "CONCORDE-OPERATION-DETERMINISTIC-001"
                        for f in findings
                    )
                    self.assertEqual(
                        invalid, deterministic != (profile == "None"), findings
                    )

    @verifies("scenario.operations.invalid-declaration")
    def test_transitive_model_calls_do_not_trust_a_childs_false_deterministic_claim(
        self,
    ) -> None:
        init = VALID_OPERATION_INIT.replace('("alpha",)', '("alpha", "beta", "gamma")')
        pure = VALID_ALPHA.replace("PROFILE = planner.PROFILE", "PROFILE = None")
        pure = pure.replace("DETERMINISTIC = False", "DETERMINISTIC = True")
        _operations_package(
            self.root,
            alpha_source=pure.replace("USES = ()", 'USES = ("beta",)'),
            init_source=init,
        )
        (self.root / "operations/beta.py").write_text(
            pure.replace("USES = ()", 'USES = ("gamma",)'), encoding="utf-8"
        )
        # All three incorrectly claim determinism; gamma launches an WorkerProfile.
        (self.root / "operations/gamma.py").write_text(
            VALID_ALPHA.replace("DETERMINISTIC = False", "DETERMINISTIC = True"),
            encoding="utf-8",
        )
        findings = package_validation._validate_operation_modules(self.root)
        self.assertEqual(
            {
                f.source
                for f in findings
                if f.rule_id == "CONCORDE-OPERATION-DETERMINISTIC-001"
            },
            {f"operations/{name}.py" for name in ("alpha", "beta", "gamma")},
            findings,
        )

    @verifies("scenario.operations.invalid-declaration")
    def test_deterministic_composition_without_agents_is_valid(self) -> None:
        init = VALID_OPERATION_INIT.replace('("alpha",)', '("alpha", "beta")')
        pure = VALID_ALPHA.replace("PROFILE = planner.PROFILE", "PROFILE = None")
        pure = pure.replace("DETERMINISTIC = False", "DETERMINISTIC = True")
        _operations_package(
            self.root,
            alpha_source=pure.replace("USES = ()", 'USES = ("beta",)'),
            init_source=init,
        )
        (self.root / "operations/beta.py").write_text(pure, encoding="utf-8")
        self.assertEqual([], package_validation._validate_operation_modules(self.root))

    @verifies("scenario.operations.invalid-declaration")
    def test_removed_discovery_selection_is_rejected(self) -> None:
        pure = VALID_ALPHA.replace("PROFILE = planner.PROFILE", "PROFILE = None")
        pure = pure.replace("DETERMINISTIC = False", "DETERMINISTIC = True")
        _operations_package(self.root, alpha_source=pure)
        pure = pure.replace(
            'CONTEXT_SELECTION = "bound"', 'CONTEXT_SELECTION = "discover"'
        )
        _operations_package(self.root, alpha_source=pure)
        findings = package_validation._validate_operation_modules(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-OPERATION-CONTEXT-001" for f in findings),
            findings,
        )

    @verifies("scenario.operations.invalid-declaration")
    def test_no_context_selection_cannot_admit_model_calls(self) -> None:
        source = VALID_ALPHA.replace(
            'CONTEXT_SELECTION = "bound"', 'CONTEXT_SELECTION = "none"'
        ).replace("PUBLIC = False", "PUBLIC = True")
        _operations_package(self.root, alpha_source=source)
        _guidance(self.root)
        findings = package_validation._validate_operation_modules(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-OPERATION-CONTEXT-001" for f in findings),
            findings,
        )


class AgentRuleTests(unittest.TestCase):
    """New rules: WorkerProfile inventory, WorkerProfile Spec structure, worker profile and child definitions."""

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
            'DOMAIN_AGENTS = ("alpha",)', 'DOMAIN_AGENTS = ("alpha", "missing")'
        )
        _agents_package(self.root, init_source=init)
        findings = package_validation._validate_worker_profiles(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-OPERATION-INVENTORY-001" for f in findings),
            findings,
        )

    def test_duplicate_agent_name_is_reported(self) -> None:
        init = VALID_AGENT_INIT.replace(
            'DOMAIN_AGENTS = ("alpha",)', 'DOMAIN_AGENTS = ("alpha", "alpha")'
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
            'spec="agents/alpha/spec.md",', 'spec="agents/alpha/wrong.md",'
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
            'effects=EffectDeclaration(("spec-context",), (), False, "none"),',
            'effects=EffectDeclaration(("spec-context",), (), True, "none"),',
        )
        _agents_package(self.root, module_source=broken_module)
        findings = package_validation._validate_worker_profiles(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-AGENT-PROFILE-001" for f in findings), findings
        )

    def test_write_effect_outside_read_effect_is_an_invalid_profile(self) -> None:
        broken_module = VALID_AGENT_ALPHA_MODULE.replace(
            'effects=EffectDeclaration(("spec-context",), (), False, "none"),',
            'effects=EffectDeclaration(("spec-context",), ("implementation",), False, "none"),',
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
    """Rule 3: exported type identities are unique; generated/protocol/schemas.json matches json_schema."""

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
        (self.root / "generated/protocol").mkdir(parents=True)
        (self.root / "generated/protocol/schemas.json").write_text(
            "{}", encoding="utf-8"
        )
        findings = package_validation._validate_contracts(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-CONTRACT-SCHEMA-001" for f in findings), findings
        )

    def test_current_schemas_file_has_no_findings(self) -> None:
        (self.root / "generated/protocol").mkdir(parents=True)
        shutil.copy2(
            REPOSITORY_ROOT / "generated/protocol/schemas.json",
            self.root / "generated/protocol/schemas.json",
        )
        self.assertEqual([], package_validation._validate_contracts(self.root))

    def test_broken_schema_source_is_reported_without_raising(self) -> None:
        (self.root / "generated/protocol").mkdir(parents=True)
        shutil.copy2(
            REPOSITORY_ROOT / "generated/protocol/schemas.json",
            self.root / "generated/protocol/schemas.json",
        )
        shutil.copytree(
            REPOSITORY_ROOT / "src/concorde/spec",
            self.root / "src/concorde/spec",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        helper = self.root / "src/concorde/spec/wire_shapes.py"
        helper.write_text(
            helper.read_text(encoding="utf-8") + "\nSTRING = {\n", encoding="utf-8"
        )
        findings = package_validation._validate_contracts(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-CONTRACT-SCHEMA-001" for f in findings), findings
        )
        self.assertIn("wire_shapes.py", str(findings))

    def test_duplicate_exported_type_identity_is_reported(self) -> None:
        # The duplicate lives in the named root's own contracts, which the rendered schema
        # dictionary would otherwise collapse silently.
        (self.root / "generated/protocol").mkdir(parents=True)
        shutil.copy2(
            REPOSITORY_ROOT / "generated/protocol/schemas.json",
            self.root / "generated/protocol/schemas.json",
        )
        shutil.copytree(
            REPOSITORY_ROOT / "src/concorde/spec",
            self.root / "src/concorde/spec",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        contracts = self.root / "src/concorde/spec/contracts.py"
        contracts.write_text(
            contracts.read_text(encoding="utf-8")
            + (
                "\n_ORIGINAL_EXPORTED_TYPES = exported_types\n"
                "def exported_types():\n"
                "    return (*_ORIGINAL_EXPORTED_TYPES(), 'concorde-context-solve-request')\n"
            ),
            encoding="utf-8",
        )
        findings = package_validation._validate_contracts(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-CONTRACT-UNIQUE-001" for f in findings), findings
        )
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
        target = self.root / "generated/agents/planner.md"
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
        (self.root / "generated/agents/extra.md").write_text(
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
                            for field in ("kind", "uses", "state", "profile"):
                                entry.setdefault(field, base.get(field))
            except ValueError:
                value = match.group(
                    1
                )  # Invalid inventory shape must still reach the rule under test.
            metadata.setdefault("extensions", {})[key] = value
        body = pattern.sub("Machine inventory is in the associated metadata.", body)
    path.write_text("# Fixture\n\n" + body + "\n")
    (root / (relative + ".json")).write_text(json.dumps(metadata))


class SpecAlignmentOperationsRuleTests(unittest.TestCase):
    """Rule 4a: exactly one registered concorde-operations block, equal to the code inventory."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_missing_registry_is_reported(self) -> None:
        findings = package_validation._validate_spec_alignment(self.root)
        self.assertTrue(
            any(f.rule_id == "CONCORDE-SPEC-OPERATIONS-001" for f in findings),
            findings,
        )

    @verifies("scenario.operations.invalid-declaration")
    def test_spec_deterministic_must_be_a_matching_boolean(self) -> None:
        _operations_package(self.root)
        for value in (False, True, "false", 0, 1, None, "missing"):
            with self.subTest(value=value):
                entry = {
                    "id": "alpha",
                    "public": False,
                    "context_selection": "bound",
                    "public_name": None,
                }
                if value != "missing":
                    entry["deterministic"] = value
                body = "```concorde-operations\n" + json.dumps([entry]) + "\n```"
                _document(self.root, "specs/one.md", "document.one", body)
                findings = package_validation._validate_spec_operations_block(
                    self.root, {"specs/one.md": body}
                )
                if value is False:
                    self.assertEqual([], findings)
                else:
                    self.assertTrue(
                        any(
                            f.rule_id == "CONCORDE-SPEC-OPERATIONS-001"
                            for f in findings
                        ),
                        findings,
                    )

    def test_no_operations_block_is_reported(self) -> None:
        _operations_package(self.root)
        _document(self.root, "specs/doc.md", "document.doc", "No block here.")
        _registry(self.root, documents=["specs/doc.md"])
        findings = package_validation._validate_spec_operations_block(
            self.root, _required_documents(self.root)
        )
        self.assertTrue(
            any(f.rule_id == "CONCORDE-SPEC-OPERATIONS-001" for f in findings),
            findings,
        )

    def test_two_operations_blocks_is_reported(self) -> None:
        _operations_package(self.root)
        block = '```concorde-operations\n[{"id": "alpha", "public": false, "context_selection": "bound", "deterministic": false, "public_name": null}]\n```'
        _document(self.root, "specs/one.md", "document.one", block)
        _document(self.root, "specs/two.md", "document.two", block)
        _registry(self.root, documents=["specs/one.md", "specs/two.md"])
        findings = package_validation._validate_spec_operations_block(
            self.root, _required_documents(self.root)
        )
        self.assertTrue(
            any(f.rule_id == "CONCORDE-SPEC-OPERATIONS-001" for f in findings),
            findings,
        )

    def test_malformed_json_is_reported(self) -> None:
        _operations_package(self.root)
        _document(
            self.root,
            "specs/one.md",
            "document.one",
            "```concorde-operations\nnot json\n```",
        )
        _registry(self.root, documents=["specs/one.md"])
        findings = package_validation._validate_spec_operations_block(
            self.root, _required_documents(self.root)
        )
        self.assertTrue(
            any(f.rule_id == "CONCORDE-SPEC-OPERATIONS-001" for f in findings),
            findings,
        )

    def test_matching_operations_block_has_no_findings(self) -> None:
        public_alpha = VALID_ALPHA.replace("PUBLIC = False", "PUBLIC = True")
        _operations_package(self.root, alpha_source=public_alpha)
        _guidance(self.root)
        block = (
            "```concorde-operations\n"
            + json.dumps(
                [
                    {
                        "id": "alpha",
                        "public": True,
                        "context_selection": "bound",
                        "deterministic": False,
                        "public_name": "concorde-alpha",
                    }
                ]
            )
            + "\n```"
        )
        _document(self.root, "specs/one.md", "document.one", block)
        _registry(self.root, documents=["specs/one.md"])
        findings = package_validation._validate_spec_operations_block(
            self.root, _required_documents(self.root)
        )
        self.assertEqual([], findings)

    @verifies("scenario.operations.invalid-declaration")
    def test_public_name_is_code_identity_not_a_skill_prerequisite(self) -> None:
        _operations_package(
            self.root,
            alpha_source=VALID_ALPHA.replace("PUBLIC = False", "PUBLIC = True"),
        )
        inventory = package_validation._operation_code_inventory(self.root)
        self.assertEqual("concorde-alpha", inventory["alpha"]["public_name"])
        self.assertNotIn("skill", inventory["alpha"])
        # Missing ordinary guidance is independently invalid, not a null executable name.
        self.assertTrue(
            any(
                f.rule_id == "CONCORDE-OPERATION-GUIDANCE-001"
                for f in package_validation._validate_operation_modules(self.root)
            )
        )

    @verifies("scenario.operations.invalid-declaration")
    def test_retired_skill_metadata_and_wrong_public_names_are_rejected(self) -> None:
        _operations_package(
            self.root,
            alpha_source=VALID_ALPHA.replace("PUBLIC = False", "PUBLIC = True"),
        )
        _guidance(self.root)
        expected = package_validation._operation_code_inventory(self.root)["alpha"]
        legacy = {"id": "alpha", **expected}
        legacy["skill"] = legacy.pop("public_name")
        entries = [legacy, {"id": "alpha", **expected, "skill": "concorde-alpha"}]
        entries.extend(
            {"id": "alpha", **expected, "public_name": value}
            for value in (None, False, 1, "concorde-wrong", ["concorde-alpha"])
        )
        for entry in entries:
            with self.subTest(entry=entry):
                body = "```concorde-operations\\n" + json.dumps([entry]) + "\\n```"
                _document(self.root, "specs/one.md", "document.one", body)
                findings = package_validation._validate_spec_operations_block(
                    self.root, {"specs/one.md": body}
                )
                self.assertTrue(
                    any(f.rule_id == "CONCORDE-SPEC-OPERATIONS-001" for f in findings),
                    findings,
                )

    @verifies("scenario.operations.invalid-declaration")
    def test_private_operation_has_no_public_name(self) -> None:
        _operations_package(self.root)
        expected = package_validation._operation_code_inventory(self.root)["alpha"]
        self.assertIsNone(expected["public_name"])
        entry = {"id": "alpha", **expected, "public_name": "concorde-alpha"}
        body = "```concorde-operations\\n" + json.dumps([entry]) + "\\n```"
        _document(self.root, "specs/one.md", "document.one", body)
        findings = package_validation._validate_spec_operations_block(
            self.root, {"specs/one.md": body}
        )
        self.assertTrue(
            any(f.rule_id == "CONCORDE-SPEC-OPERATIONS-001" for f in findings), findings
        )

    def test_mismatched_context_selection_is_reported(self) -> None:
        public_alpha = VALID_ALPHA.replace("PUBLIC = False", "PUBLIC = True")
        _operations_package(self.root, alpha_source=public_alpha)
        _guidance(self.root)
        block = (
            "```concorde-operations\n"
            + json.dumps(
                [
                    {
                        "id": "alpha",
                        "public": True,
                        "context_selection": "none",
                        "deterministic": False,
                        "public_name": "concorde-alpha",
                    }
                ]
            )
            + "\n```"
        )
        _document(self.root, "specs/one.md", "document.one", block)
        _registry(self.root, documents=["specs/one.md"])
        findings = package_validation._validate_spec_operations_block(
            self.root, _required_documents(self.root)
        )
        self.assertTrue(
            any(f.rule_id == "CONCORDE-SPEC-OPERATIONS-001" for f in findings),
            findings,
        )

    def test_missing_operation_entry_is_reported(self) -> None:
        _operations_package(self.root)
        _document(
            self.root,
            "specs/one.md",
            "document.one",
            "```concorde-operations\n[]\n```",
        )
        _registry(self.root, documents=["specs/one.md"])
        findings = package_validation._validate_spec_operations_block(
            self.root, _required_documents(self.root)
        )
        self.assertTrue(
            any("missing operation" in f.message for f in findings), findings
        )

    def test_extra_operation_entry_is_reported(self) -> None:
        _operations_package(self.root)
        block = (
            "```concorde-operations\n"
            + json.dumps(
                [
                    {
                        "id": "alpha",
                        "public": False,
                        "context_selection": "bound",
                        "deterministic": False,
                        "public_name": None,
                    },
                    {
                        "id": "ghost",
                        "public": False,
                        "context_selection": "bound",
                        "deterministic": False,
                        "public_name": None,
                    },
                ]
            )
            + "\n```"
        )
        _document(self.root, "specs/one.md", "document.one", block)
        _registry(self.root, documents=["specs/one.md"])
        findings = package_validation._validate_spec_operations_block(
            self.root, _required_documents(self.root)
        )
        self.assertTrue(
            any("unknown operation" in f.message for f in findings), findings
        )


class UnifiedProfileMetadataTests(unittest.TestCase):
    """Profile drift is checked inside the one Operation inventory, not a parallel block."""

    @verifies("scenario.distribution.build-check")
    def test_model_profile_and_state_drift_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _operations_package(root)
            inventory = package_validation._operation_code_inventory(root)
            assert inventory is not None
            expected = inventory["alpha"]
            for key, value in (
                ("profile", {**expected["profile"], "tools": ["invented"]}),
                ("profile", {**expected["profile"], "workspace": "project"}),
                ("state", {"input": "unknown", "output": None}),
                ("uses", ["ghost"]),
            ):
                with self.subTest(key=key, value=value):
                    entry = {"id": "alpha", **expected, key: value}
                    block = "```concorde-operations\n" + json.dumps([entry]) + "\n```"
                    _document(root, "specs/one.md", "document.one", block)
                    _registry(root, documents=["specs/one.md"])
                    findings = package_validation._validate_spec_operations_block(
                        root, _required_documents(root)
                    )
                    self.assertTrue(
                        any(
                            f.rule_id == "CONCORDE-SPEC-OPERATIONS-001"
                            for f in findings
                        ),
                        findings,
                    )

    def test_single_inventory_matches_without_an_agent_metadata_block(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _operations_package(root)
            inventory = package_validation._operation_code_inventory(root)
            assert inventory is not None
            entry = {"id": "alpha", **inventory["alpha"]}
            _document(
                root,
                "specs/one.md",
                "document.one",
                "```concorde-operations\n" + json.dumps([entry]) + "\n```",
            )
            _registry(root, documents=["specs/one.md"])
            self.assertEqual(
                [],
                package_validation._validate_spec_operations_block(
                    root, _required_documents(root)
                ),
            )


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
        self.assertTrue(
            any("does not appear in this document" in f.message for f in findings),
            findings,
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
