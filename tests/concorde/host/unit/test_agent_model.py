"""``agent_model.resolve_agent`` is the runtime binding the host actually uses (A1, A4): it fails
closed against the current build manifest, the registered Harness catalog, and every declared
capability/context/result/effect/limit. This exercises that resolution directly, plus the
``harness.harness(...)`` digest it depends on and the ``build.load_agent`` wrapper around it.
"""
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

from concorde.host import agent_model  # noqa: E402
from concorde.host.agent_model import (  # noqa: E402
    agent_definition,
    binding_digest,
    resolve_agent,
)
from concorde.host.build import BuildError, load_agent, write_build  # noqa: E402
from concorde.host.effects import EffectDeclaration  # noqa: E402
from concorde.host.harness import (  # noqa: E402
    DISCOVERY_CAPSULE,
    HARNESSES,
    SPEC_CAPSULE,
    LoopPolicy,
)
from concorde.host.harness import harness as make_harness  # noqa: E402


class HarnessDigestTests(unittest.TestCase):
    """``harness.harness(...)`` digests: deterministic, order-independent, field-sensitive."""

    def _fixture(self, **overrides) -> object:
        fields = {
            "name": "digest-fixture",
            "workspace": "capsule",
            "effects": EffectDeclaration(("spec-context",), (), False, "none"),
            "contexts": ("concorde-agent-stage-context", "concorde-review-stage-context"),
            "results": ("concorde-agent-stage-result",),
            "loop": LoopPolicy(600),
        }
        fields.update(overrides)
        return make_harness(**fields)

    def test_building_the_same_harness_twice_yields_the_same_digest(self):
        first = self._fixture()
        second = self._fixture()
        self.assertEqual(first.digest, second.digest)

    def test_tuple_order_does_not_affect_the_digest(self):
        forward = self._fixture(contexts=("concorde-agent-stage-context", "concorde-review-stage-context"))
        reversed_order = self._fixture(contexts=("concorde-review-stage-context", "concorde-agent-stage-context"))
        self.assertEqual(forward.digest, reversed_order.digest)
        # Both are normalized to the same stored (sorted) tuple, not just an equal digest.
        self.assertEqual(forward.contexts, reversed_order.contexts)

    def test_digest_changes_when_the_loop_timeout_changes(self):
        base = self._fixture(loop=LoopPolicy(600))
        changed = self._fixture(loop=LoopPolicy(900))
        self.assertNotEqual(base.digest, changed.digest)

    def test_digest_changes_when_a_context_changes(self):
        base = self._fixture(contexts=("concorde-agent-stage-context",))
        changed = self._fixture(contexts=("concorde-agent-stage-context", "concorde-topology-author-context"))
        self.assertNotEqual(base.digest, changed.digest)

    def test_digest_changes_when_effects_change(self):
        base = self._fixture(effects=EffectDeclaration(("spec-context",), (), False, "none"))
        changed = self._fixture(effects=EffectDeclaration(("spec-context", "implementation"), (), False, "none"))
        self.assertNotEqual(base.digest, changed.digest)

    def test_the_three_registered_harnesses_have_distinct_digests(self):
        digests = {one.digest for one in HARNESSES.values()}
        self.assertEqual(len(digests), len(HARNESSES))


class ResolveAgentBuildTests(unittest.TestCase):
    """``resolve_agent``/``load_agent`` against a real freshly built package."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(REPOSITORY_ROOT / "prompts", self.root / "prompts")
        shutil.copytree(REPOSITORY_ROOT / "skills", self.root / "skills")
        shutil.copytree(REPOSITORY_ROOT / "agents", self.root / "agents")

    def test_resolve_agent_succeeds_for_every_inventory_agent_after_write_build(self):
        write_build(self.root, "all")
        manifest = json.loads((self.root / "generated/build-manifest.json").read_text(encoding="utf-8"))
        inventory = agent_model.load_agent_inventory()
        self.assertTrue(inventory.AGENTS)
        for name in inventory.AGENTS:
            with self.subTest(agent=name):
                binding = resolve_agent(self.root, name)
                self.assertEqual(binding.agent, name)
                self.assertEqual(binding.spec_path, f"agents/{name}/spec.md")
                self.assertEqual(binding.spec_digest, manifest["sources"][binding.spec_path])

                hyphenated = name.replace("_", "-")
                rendered_path = self.root / f"generated/agents/{hyphenated}.md"
                expected_instructions_digest = "sha256:" + hashlib.sha256(rendered_path.read_bytes()).hexdigest()
                self.assertEqual(binding.instructions_path, f"generated/agents/{hyphenated}.md")
                self.assertEqual(binding.instructions_digest, expected_instructions_digest)

                self.assertEqual(binding.harness_digest, HARNESSES[binding.harness].digest)
                self.assertEqual(binding.digest, binding_digest(binding))

    def test_resolve_agent_accepts_external_hyphenated_and_underscored_names(self):
        write_build(self.root, "all")
        by_external = resolve_agent(self.root, "concorde-context-assessor")
        by_hyphenated = resolve_agent(self.root, "context-assessor")
        by_underscore = resolve_agent(self.root, "context_assessor")
        self.assertEqual(by_external, by_hyphenated)
        self.assertEqual(by_external, by_underscore)
        self.assertEqual(by_external.agent, "context_assessor")

    def test_unknown_agent_name_fails_closed(self):
        write_build(self.root, "all")
        with self.assertRaises(BuildError) as failure:
            resolve_agent(self.root, "concorde-not-a-real-agent")
        self.assertEqual(failure.exception.code, "unknown_agent")

    def test_missing_rendered_instructions_is_stale_build(self):
        write_build(self.root, "all")
        (self.root / "generated/agents/coordinator.md").unlink()
        with self.assertRaises(BuildError) as failure:
            resolve_agent(self.root, "concorde-coordinator")
        self.assertEqual(failure.exception.code, "stale_build")

    def test_effective_loop_is_the_harness_loop_when_limits_is_none(self):
        write_build(self.root, "all")
        self.assertIsNone(agent_definition("coordinator").constraints.limits)
        binding = resolve_agent(self.root, "coordinator")
        self.assertEqual(binding.effective_loop, DISCOVERY_CAPSULE.loop)

    def test_load_agent_binding_and_effects_match_resolve_agent(self):
        write_build(self.root, "all")
        prompt = load_agent(self.root, "concorde-spec-author")
        binding = resolve_agent(self.root, "concorde-spec-author")
        self.assertEqual(prompt.binding, binding)
        self.assertEqual(prompt.effects, agent_definition("spec_author").constraints.effects)
        self.assertTrue(prompt.body.strip())


def _with_one_agent_replaced(name: str, replacement) -> dict:
    """A copy of the real Agent inventory with ``name`` swapped for ``replacement``."""

    modified = dict(agent_model.load_agents())
    modified[name] = replacement
    return modified


class ResolveAgentInvalidBindingTests(unittest.TestCase):
    """``resolve_agent`` fails closed with ``invalid_agent_binding`` for every inconsistency
    between an Agent definition and its bound Harness, via a patched inventory."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(REPOSITORY_ROOT / "prompts", self.root / "prompts")
        shutil.copytree(REPOSITORY_ROOT / "skills", self.root / "skills")
        shutil.copytree(REPOSITORY_ROOT / "agents", self.root / "agents")
        write_build(self.root, "all")

    def _resolve_with(self, name: str, replacement) -> None:
        modified = _with_one_agent_replaced(name, replacement)
        with mock.patch.object(agent_model, "load_agents", return_value=modified):
            with self.assertRaises(BuildError) as failure:
                resolve_agent(self.root, name)
        self.assertEqual(failure.exception.code, "invalid_agent_binding")

    def test_constraints_that_widen_effects_beyond_the_harness_are_invalid(self):
        base = agent_model.load_agents()["reader"]
        self.assertEqual(base.harness.name, SPEC_CAPSULE.name)
        widened_effects = dataclasses.replace(base.constraints.effects, writes=("implementation",))
        widened = dataclasses.replace(base, constraints=dataclasses.replace(base.constraints, effects=widened_effects))
        self._resolve_with("reader", widened)

    def test_unregistered_harness_is_invalid(self):
        base = agent_model.load_agents()["reader"]
        bogus = make_harness(
            name="fixture-bogus-harness",
            workspace="capsule",
            effects=EffectDeclaration(("spec-context",), (), False, "none"),
            contexts=(),
            results=(),
            loop=LoopPolicy(60),
        )
        self.assertNotIn(bogus.name, HARNESSES)
        broken = dataclasses.replace(base, harness=bogus)
        self._resolve_with("reader", broken)

    def test_unknown_capability_reference_is_invalid(self):
        base = agent_model.load_agents()["reader"]
        broken = dataclasses.replace(
            base, constraints=dataclasses.replace(base.constraints, capabilities=("concorde-not-a-real-capability",))
        )
        self._resolve_with("reader", broken)

    def test_context_not_admitted_by_the_harness_is_invalid(self):
        base = agent_model.load_agents()["reader"]
        self.assertNotIn("concorde-main-stage-context", base.harness.contexts)
        broken = dataclasses.replace(
            base, constraints=dataclasses.replace(base.constraints, contexts=("concorde-main-stage-context",))
        )
        self._resolve_with("reader", broken)

    def test_wrong_spec_path_is_invalid(self):
        base = agent_model.load_agents()["reader"]
        broken = dataclasses.replace(base, spec="agents/reader/wrong.md")
        self._resolve_with("reader", broken)

    def test_limits_that_widen_the_harness_timeout_are_invalid(self):
        base = agent_model.load_agents()["reader"]
        widened = dataclasses.replace(
            base, constraints=dataclasses.replace(base.constraints, limits=LoopPolicy(999999))
        )
        self.assertGreater(widened.constraints.limits.timeout_seconds, widened.harness.loop.timeout_seconds)
        self._resolve_with("reader", widened)

    def test_effective_loop_is_the_tighter_timeout_when_limits_is_given(self):
        base = agent_model.load_agents()["reader"]
        self.assertLess(300, base.harness.loop.timeout_seconds)
        tightened = dataclasses.replace(
            base, constraints=dataclasses.replace(base.constraints, limits=LoopPolicy(300))
        )
        modified = _with_one_agent_replaced("reader", tightened)
        with mock.patch.object(agent_model, "load_agents", return_value=modified):
            binding = resolve_agent(self.root, "reader")
        self.assertEqual(binding.effective_loop, LoopPolicy(300))


if __name__ == "__main__":
    unittest.main()
