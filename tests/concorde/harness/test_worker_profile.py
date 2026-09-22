"""Worker definitions: terminal profile validation and reproducible build-bound bindings."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.distribution.build import (  # noqa: E402
    BuildError,
    load_model_instructions,
    write_build,
)
from concorde.harness import worker_profile as profiles  # noqa: E402
from concorde.harness.worker_profile import (  # noqa: E402
    binding_digest,
    binding_from_json,
    binding_json,
    profile_digest,
    resolve_worker,
    validate_worker_profile,
    worker_profile,
)
from concorde.spec.verification import verifies  # noqa: E402


def _package(root: Path) -> None:
    for directory in ("agents", "prompts", "protocol", "operations"):
        shutil.copytree(REPOSITORY_ROOT / directory, root / directory)


class ResolveAgentBuildTests(unittest.TestCase):
    """``resolve_worker``/``load_model_instructions`` against a real freshly built package."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        _package(self.root)
        write_build(self.root)

    @verifies("scenario.harness.agent-bind")
    def test_resolve_agent_succeeds_for_every_inventory_worker(self):
        manifest = json.loads(
            (self.root / "generated/build-manifest.json").read_text(encoding="utf-8")
        )
        inventory = profiles.load_worker_profiles()
        self.assertEqual(
            {
                "context_assessor",
                "planner",
                "task_author",
                "programmer",
                "spec_reviewer",
                "code_reviewer",
                "issue_solver",
            },
            set(inventory),
        )
        for name in inventory:
            with self.subTest(agent=name):
                agent = worker_profile(name)
                binding = resolve_worker(self.root, name)
                self.assertEqual(binding.agent, name)
                self.assertEqual(binding.spec_path, f"agents/{name}/spec.md")
                self.assertEqual(
                    binding.spec_digest, manifest["sources"][binding.spec_path]
                )
                self.assertNotIn("children", dataclasses.asdict(agent))
                hyphenated = name.replace("_", "-")
                rendered = self.root / f"generated/agents/{hyphenated}.md"
                self.assertEqual(
                    binding.instructions_path, f"generated/agents/{hyphenated}.md"
                )
                self.assertEqual(
                    binding.instructions_digest,
                    "sha256:" + hashlib.sha256(rendered.read_bytes()).hexdigest(),
                )
                # One rendered view: native terminal rules, then the canonical Agent role Spec.
                text = rendered.read_text(encoding="utf-8")
                self.assertIn(f"# concorde-{hyphenated}", text)
                self.assertLess(
                    text.index("structured_output"),
                    text.index(f"# concorde-{hyphenated}"),
                )
                self.assertEqual(binding.timeout_seconds, agent.timeout_seconds)
                self.assertEqual(
                    binding.profile_digest, profile_digest(self.root, agent)
                )
                self.assertEqual(binding.digest, binding_digest(binding))
                self.assertEqual(binding, binding_from_json(binding_json(binding)))

    @verifies("scenario.harness.agent-bind")
    def test_resolve_agent_accepts_external_hyphenated_and_underscored_names(self):
        by_external = resolve_worker(self.root, "concorde-code-reviewer")
        self.assertEqual(by_external, resolve_worker(self.root, "code-reviewer"))
        self.assertEqual(by_external, resolve_worker(self.root, "code_reviewer"))
        self.assertEqual("code_reviewer", by_external.agent)

    @verifies("scenario.harness.agent-bind")
    def test_load_agent_binding_and_effects_match_resolve_agent(self):
        prompt = load_model_instructions(self.root, "concorde-planner")
        self.assertEqual(resolve_worker(self.root, "concorde-planner"), prompt.binding)
        self.assertEqual(worker_profile("planner").contract.effects, prompt.effects)
        self.assertTrue(prompt.body.strip())

    @verifies("scenario.harness.agent-bind")
    def test_changed_role_instructions_stale_the_build(self):
        before = resolve_worker(self.root, "programmer")
        role = self.root / "agents/programmer/spec.md"
        role.write_text(role.read_text() + "\nUse precise evidence.\n")
        with self.assertRaises(BuildError) as failure:
            resolve_worker(self.root, "programmer")
        self.assertEqual("stale_build", failure.exception.code)
        write_build(self.root)
        self.assertNotEqual(
            before.digest, resolve_worker(self.root, "programmer").digest
        )

    @verifies("scenario.harness.agent-bind-reject")
    def test_unknown_worker_name_fails_closed(self):
        for name in ("concorde-not-a-real-agent", "coordinator", "spec_engineer"):
            with self.subTest(name=name), self.assertRaises(BuildError) as failure:
                resolve_worker(self.root, name)
            self.assertEqual("unknown_agent", failure.exception.code)

    @verifies("scenario.harness.agent-bind-reject")
    def test_missing_rendered_instructions_is_stale_build(self):
        (self.root / "generated/agents/planner.md").unlink()
        with self.assertRaises(BuildError) as failure:
            resolve_worker(self.root, "concorde-planner")
        self.assertEqual("stale_build", failure.exception.code)


class ProfileValidationTests(unittest.TestCase):
    """Profiles fail closed with ``invalid_agent_binding``."""

    def assertInvalid(self, agent) -> None:
        with self.assertRaises(BuildError) as failure:
            validate_worker_profile(agent)
        self.assertEqual("invalid_agent_binding", failure.exception.code)

    @verifies("scenario.harness.agent-bind-reject", "scenario.harness.worker-contract")
    def test_profiles_cannot_exceed_their_contract_or_workspace(self):
        planner = worker_profile("planner")
        effects = planner.contract.effects
        contract = planner.contract
        for label, agent in {
            "edit without a write effect": dataclasses.replace(
                planner, tools=(*planner.tools, "edit")
            ),
            "unknown tool": dataclasses.replace(
                planner, tools=(*planner.tools, "web_fetch")
            ),
            "duplicate tool": dataclasses.replace(
                planner, tools=(*planner.tools, "read")
            ),
            "no read tool": dataclasses.replace(planner, tools=("grep",)),
            "implementation in a capsule": dataclasses.replace(
                planner,
                contract=dataclasses.replace(
                    contract,
                    effects=dataclasses.replace(
                        effects, reads=(*effects.reads, "implementation")
                    ),
                ),
            ),
            "network": dataclasses.replace(
                planner,
                contract=dataclasses.replace(
                    contract, effects=dataclasses.replace(effects, network=True)
                ),
            ),
            "mismatched result": dataclasses.replace(
                planner,
                contract=dataclasses.replace(
                    contract, result="concorde-review-stage-result"
                ),
            ),
            "required input not admitted": dataclasses.replace(
                planner,
                contract=dataclasses.replace(
                    contract, required_inputs=("concorde-implementation-task",)
                ),
            ),
            "wrong spec path": dataclasses.replace(
                planner, spec="operations/other/spec.md"
            ),
            "zero timeout": dataclasses.replace(planner, timeout_seconds=0),
            "unknown workspace": dataclasses.replace(planner, workspace="container"),
        }.items():
            with self.subTest(label):
                self.assertInvalid(agent)
        for name in profiles.load_worker_profiles():
            validate_worker_profile(worker_profile(name))

    @verifies(
        "scenario.harness.agent-bind-reject", "scenario.harness.pi-worker-delegation"
    )
    def test_terminal_profile_rejects_child_definitions_and_delegation_tools(self):
        planner = worker_profile("planner")
        with self.assertRaises(TypeError):
            dataclasses.replace(planner, children=())
        for tool in ("subagent", "concorde", "run_operation"):
            self.assertInvalid(
                dataclasses.replace(planner, tools=(*planner.tools, tool))
            )

    @verifies("scenario.harness.agent-bind-reject")
    def test_resolve_agent_rejects_an_inconsistent_inventory_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _package(root)
            write_build(root)
            modified = dict(profiles.load_worker_profiles())
            modified["planner"] = dataclasses.replace(
                modified["planner"], tools=("read", "write")
            )
            with (
                mock.patch.object(
                    profiles, "load_worker_profiles", return_value=modified
                ),
                self.assertRaises(BuildError) as failure,
            ):
                resolve_worker(root, "planner")
            self.assertEqual("invalid_agent_binding", failure.exception.code)


if __name__ == "__main__":
    unittest.main()
