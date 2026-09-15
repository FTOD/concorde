"""Worker definitions: profile validation, child definitions and reproducible build-bound bindings."""
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

from concorde.harness import agent_model  # noqa: E402
from concorde.harness.agent_model import (  # noqa: E402
    Child,
    agent_definition,
    binding_digest,
    binding_from_json,
    binding_json,
    child_definitions,
    profile_digest,
    resolve_agent,
    validate_agent,
)
from concorde.distribution.build import BuildError, load_agent, write_build  # noqa: E402
from concorde.spec.verification import verifies  # noqa: E402


def _package(root: Path) -> None:
    for directory in ("prompts", "protocol", "skills", "agents"):
        shutil.copytree(REPOSITORY_ROOT / directory, root / directory)


class ResolveAgentBuildTests(unittest.TestCase):
    """``resolve_agent``/``load_agent`` against a real freshly built package."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        _package(self.root)
        write_build(self.root, "all")

    @verifies("scenario.harness.agent-bind")
    def test_resolve_agent_succeeds_for_every_inventory_worker(self):
        manifest = json.loads((self.root / "generated/build-manifest.json").read_text(encoding="utf-8"))
        inventory = agent_model.load_agent_inventory()
        self.assertEqual(12, len(inventory.AGENTS))
        for name in inventory.AGENTS:
            with self.subTest(agent=name):
                agent = agent_definition(name)
                binding = resolve_agent(self.root, name)
                self.assertEqual(binding.agent, name)
                self.assertEqual(binding.spec_path, f"agents/{name}/spec.md")
                self.assertEqual(binding.spec_digest, manifest["sources"][binding.spec_path])
                for child in agent.children:
                    self.assertIn(child.definition, manifest["sources"])
                hyphenated = name.replace("_", "-")
                rendered = self.root / f"generated/agents/{hyphenated}.md"
                self.assertEqual(binding.instructions_path, f"generated/agents/{hyphenated}.md")
                self.assertEqual(binding.instructions_digest, "sha256:" + hashlib.sha256(rendered.read_bytes()).hexdigest())
                # One rendered view: the common worker rules, then this worker's own role Spec.
                text = rendered.read_text(encoding="utf-8")
                self.assertIn(f"# concorde-{hyphenated}", text)
                self.assertLess(text.index("submit_result"), text.index(f"# concorde-{hyphenated}"))
                self.assertEqual(binding.timeout_seconds, agent.timeout_seconds)
                self.assertEqual(binding.profile_digest, profile_digest(self.root, agent))
                self.assertEqual(binding.digest, binding_digest(binding))
                self.assertEqual(binding, binding_from_json(binding_json(binding)))

    @verifies("scenario.harness.agent-bind")
    def test_resolve_agent_accepts_external_hyphenated_and_underscored_names(self):
        by_external = resolve_agent(self.root, "concorde-code-reviewer")
        self.assertEqual(by_external, resolve_agent(self.root, "code-reviewer"))
        self.assertEqual(by_external, resolve_agent(self.root, "code_reviewer"))
        self.assertEqual("code_reviewer", by_external.agent)

    @verifies("scenario.harness.agent-bind")
    def test_load_agent_binding_and_effects_match_resolve_agent(self):
        prompt = load_agent(self.root, "concorde-planner")
        self.assertEqual(resolve_agent(self.root, "concorde-planner"), prompt.binding)
        self.assertEqual(agent_definition("planner").contract.effects, prompt.effects)
        self.assertTrue(prompt.body.strip())

    @verifies("scenario.harness.agent-bind")
    def test_a_changed_child_definition_changes_the_profile_and_stales_the_build(self):
        before = resolve_agent(self.root, "programmer")
        scout = self.root / "agents/programmer/children/scout.md"
        scout.write_text(scout.read_text(encoding="utf-8") + "\nPrefer exact file names.\n", encoding="utf-8")
        with self.assertRaises(BuildError) as failure:
            resolve_agent(self.root, "programmer")
        self.assertEqual("stale_build", failure.exception.code)
        write_build(self.root, "all")
        after = resolve_agent(self.root, "programmer")
        self.assertNotEqual(before.profile_digest, after.profile_digest)
        self.assertNotEqual(before.digest, after.digest)

    @verifies("scenario.harness.agent-bind-reject")
    def test_unknown_worker_name_fails_closed(self):
        for name in ("concorde-not-a-real-agent", "coordinator", "spec_engineer"):
            with self.subTest(name=name), self.assertRaises(BuildError) as failure:
                resolve_agent(self.root, name)
            self.assertEqual("unknown_agent", failure.exception.code)

    @verifies("scenario.harness.agent-bind-reject")
    def test_missing_rendered_instructions_is_stale_build(self):
        (self.root / "generated/agents/router.md").unlink()
        with self.assertRaises(BuildError) as failure:
            resolve_agent(self.root, "concorde-router")
        self.assertEqual("stale_build", failure.exception.code)


class ProfileValidationTests(unittest.TestCase):
    """Profiles and child definitions fail closed with ``invalid_agent_binding``."""

    def assertInvalid(self, agent) -> None:
        with self.assertRaises(BuildError) as failure:
            validate_agent(agent)
        self.assertEqual("invalid_agent_binding", failure.exception.code)

    @verifies("scenario.harness.agent-bind-reject", "scenario.harness.worker-contract")
    def test_profiles_cannot_exceed_their_contract_or_workspace(self):
        planner = agent_definition("planner")
        programmer = agent_definition("programmer")
        effects = planner.contract.effects
        contract = planner.contract
        for label, agent in {
            "edit without a write effect": dataclasses.replace(planner, tools=(*planner.tools, "edit")),
            "unknown tool": dataclasses.replace(planner, tools=(*planner.tools, "web_fetch")),
            "duplicate tool": dataclasses.replace(planner, tools=(*planner.tools, "read")),
            "no read tool": dataclasses.replace(planner, tools=("grep",)),
            "implementation in a capsule": dataclasses.replace(planner, contract=dataclasses.replace(
                contract, effects=dataclasses.replace(effects, reads=(*effects.reads, "implementation")))),
            "network": dataclasses.replace(planner, contract=dataclasses.replace(
                contract, effects=dataclasses.replace(effects, network=True))),
            "mismatched result": dataclasses.replace(planner, contract=dataclasses.replace(
                contract, result="concorde-review-stage-result")),
            "required input not admitted": dataclasses.replace(planner, contract=dataclasses.replace(
                contract, required_inputs=("concorde-implementation-task",))),
            "wrong spec path": dataclasses.replace(planner, spec="agents/other/spec.md"),
            "child outside its directory": dataclasses.replace(planner, children=(Child("scout", "agents/scout.md"),)),
            "child declared twice": dataclasses.replace(programmer, children=(*programmer.children, programmer.children[0])),
            "zero timeout": dataclasses.replace(planner, timeout_seconds=0),
            "unknown workspace": dataclasses.replace(planner, workspace="container"),
        }.items():
            with self.subTest(label):
                self.assertInvalid(agent)
        for name in agent_model.load_agent_inventory().AGENTS:
            validate_agent(agent_definition(name))

    @verifies("scenario.harness.agent-bind-reject")
    def test_child_definitions_are_checked_and_leave_model_selection_to_configuration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(REPOSITORY_ROOT / "agents", root / "agents")
            programmer = agent_definition("programmer")
            self.assertEqual({"scout", "planner", "verifier"}, {item.name for item in child_definitions(root, programmer)})
            verifier = root / "agents/programmer/children/verifier.md"
            original = verifier.read_text(encoding="utf-8")
            forged = {
                "a model": original.replace("---\n", "---\nmodel: openai-codex/gpt-6-astra\n", 1),
                "a thinking level": original.replace("---\n", "---\nthinking: high\n", 1),
                "a tool outside the child set": original.replace("run_checks", "run_checks, edit", 1),
                "inherited project context": original.replace("inheritProjectContext: false", "inheritProjectContext: true"),
                "another name": original.replace("name: verifier", "name: tester"),
                "no prompt": original[:original.index("---", 3) + 4],
            }
            for label, text in forged.items():
                with self.subTest(label):
                    self.assertNotEqual(original, text)
                    verifier.write_text(text, encoding="utf-8")
                    with self.assertRaises(BuildError) as failure:
                        child_definitions(root, programmer)
                    self.assertEqual("invalid_agent_binding", failure.exception.code)
            verifier.unlink()
            with self.assertRaises(BuildError):
                child_definitions(root, programmer)
            # A capsule worker's children cannot run host checks.
            scout = root / "agents/planner/children/scout.md"
            scout.write_text(scout.read_text(encoding="utf-8").replace("tools: read", "tools: run_checks, read", 1),
                             encoding="utf-8")
            with self.assertRaises(BuildError):
                child_definitions(root, agent_definition("planner"))

    @verifies("scenario.harness.agent-bind-reject")
    def test_resolve_agent_rejects_an_inconsistent_inventory_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _package(root)
            write_build(root, "all")
            modified = dict(agent_model.load_agents())
            modified["router"] = dataclasses.replace(modified["router"], tools=("read", "write"))
            with mock.patch.object(agent_model, "load_agents", return_value=modified):
                with self.assertRaises(BuildError) as failure:
                    resolve_agent(root, "router")
            self.assertEqual("invalid_agent_binding", failure.exception.code)


if __name__ == "__main__":
    unittest.main()
