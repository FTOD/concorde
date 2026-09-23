"""Agent bindings: definition consistency and reproducible build-bound bindings."""

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

import agents  # noqa: E402
from concorde.distribution.build import write_build  # noqa: E402
from concorde.harness.worker_profile import (  # noqa: E402
    agent_definition,
    agent_names,
    bind_agent,
    load_instructions,
    validate_definition,
)
from concorde.spec.repository import SpecError  # noqa: E402
from concorde.spec.verification import verifies  # noqa: E402


def _package(root: Path) -> None:
    for directory in ("agents", "prompts", "protocol", "operations"):
        shutil.copytree(REPOSITORY_ROOT / directory, root / directory)


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


class BindAgentBuildTests(unittest.TestCase):
    """``bind_agent`` against a real freshly built package."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        _package(self.root)
        write_build(self.root)

    @verifies("scenario.context.agent-bind")
    def test_every_agent_binds_to_its_rendered_instructions(self):
        manifest_bytes = (self.root / "generated/build-manifest.json").read_bytes()
        manifest = json.loads(manifest_bytes)
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
            set(agent_names()),
        )
        for name in agent_names():
            with self.subTest(agent=name):
                definition = agent_definition(name)
                binding = bind_agent(self.root, name)
                self.assertEqual(binding.agent, name)
                self.assertEqual(binding.spec_path, f"agents/{name}/spec.md")
                self.assertEqual(
                    binding.spec_digest, manifest["sources"][binding.spec_path]
                )
                hyphenated = name.replace("_", "-")
                rendered = self.root / f"generated/native/{hyphenated}.md"
                self.assertEqual(
                    binding.instructions_path, f"generated/native/{hyphenated}.md"
                )
                self.assertEqual(
                    binding.instructions_digest, _sha256(rendered.read_bytes())
                )
                self.assertEqual(
                    rendered.read_text(), load_instructions(self.root, binding)
                )
                # One rendered view: the native rules, then the Agent's own instructions.
                text = rendered.read_text(encoding="utf-8")
                self.assertIn(f"# concorde-{hyphenated}", text)
                self.assertLess(
                    text.index("structured_output"),
                    text.index(f"# concorde-{hyphenated}"),
                )
                self.assertEqual(binding.tools, definition.tools)
                self.assertEqual(binding.effects, definition.effects)
                self.assertEqual(binding.workspace, definition.workspace)
                self.assertEqual(binding.timeout_seconds, definition.timeout_seconds)
                self.assertEqual(_sha256(manifest_bytes), binding.build_manifest_digest)
                fields = binding.record()
                fields.pop("digest")
                self.assertEqual(
                    _sha256(
                        json.dumps(
                            fields, sort_keys=True, separators=(",", ":")
                        ).encode()
                    ),
                    binding.digest,
                )

    @verifies("scenario.context.agent-bind")
    def test_bind_accepts_external_hyphenated_and_underscored_names(self):
        by_external = bind_agent(self.root, "concorde-code-reviewer")
        self.assertEqual(by_external, bind_agent(self.root, "code-reviewer"))
        self.assertEqual(by_external, bind_agent(self.root, "code_reviewer"))
        self.assertEqual("code_reviewer", by_external.agent)

    @verifies("scenario.context.agent-bind", "scenario.context.agent-bind-stale-build")
    def test_changed_instructions_stale_the_build(self):
        before = bind_agent(self.root, "programmer")
        role = self.root / "agents/programmer/spec.md"
        role.write_text(role.read_text() + "\nUse precise evidence.\n")
        with self.assertRaises(SpecError) as failure:
            bind_agent(self.root, "programmer")
        self.assertEqual("stale_build", failure.exception.code)
        write_build(self.root)
        self.assertNotEqual(before.digest, bind_agent(self.root, "programmer").digest)

    @verifies("scenario.context.unknown-agent")
    def test_unknown_agent_name_fails_closed(self):
        for name in (
            "concorde-not-a-real-agent",
            "coordinator",
            "tester",
            "concorde-plan",
        ):
            with self.subTest(name=name), self.assertRaises(SpecError) as failure:
                bind_agent(self.root, name)
            self.assertEqual("unknown_agent", failure.exception.code)

    @verifies("scenario.context.agent-bind-stale-build")
    def test_missing_rendered_instructions_is_stale_build(self):
        (self.root / "generated/native/planner.md").unlink()
        with self.assertRaises(SpecError) as failure:
            bind_agent(self.root, "concorde-planner")
        self.assertEqual("stale_build", failure.exception.code)


class DefinitionValidationTests(unittest.TestCase):
    """Definitions fail closed with ``invalid_agent_binding``."""

    def assertInvalid(self, definition) -> None:
        with self.assertRaises(SpecError) as failure:
            validate_definition(definition)
        self.assertEqual("invalid_agent_binding", failure.exception.code)

    @verifies("scenario.context.definition-inconsistent")
    def test_definitions_cannot_exceed_their_effects_or_workspace(self):
        planner = agent_definition("planner")
        replace = dataclasses.replace
        for label, definition in {
            "edit without a write effect": replace(
                planner, tools=(*planner.tools, "edit")
            ),
            "bash without a write effect": replace(
                planner, tools=(*planner.tools, "bash")
            ),
            "unknown tool": replace(planner, tools=(*planner.tools, "web_fetch")),
            "duplicate tool": replace(planner, tools=(*planner.tools, "read")),
            "no read tool": replace(planner, tools=("grep",)),
            "implementation in a capsule": replace(
                planner, reads=(*planner.reads, "implementation")
            ),
            "unknown effect role": replace(planner, reads=(*planner.reads, "secrets")),
            "writes what it cannot read": replace(planner, writes=("implementation",)),
            "network": replace(planner, network=True),
            "credentials": replace(planner, credentials="declared"),
            "mismatched result": replace(
                planner, result="concorde-review-stage-result"
            ),
            "required input not admitted": replace(
                planner, required_inputs=("concorde-implementation-task",)
            ),
            "wrong instructions": replace(planner, instructions="operations/x/spec.md"),
            "zero timeout": replace(planner, timeout_seconds=0),
            "unknown workspace": replace(planner, workspace="container"),
            "no hook": replace(planner, hook="concorde.planning.hooks"),
        }.items():
            with self.subTest(label):
                self.assertInvalid(definition)
        for name in agent_names():
            validate_definition(agent_definition(name))

    @verifies("scenario.context.definition-inconsistent")
    def test_a_definition_rejects_delegation_tools(self):
        planner = agent_definition("planner")
        for tool in ("subagent", "concorde", "run_operation"):
            self.assertInvalid(
                dataclasses.replace(planner, tools=(*planner.tools, tool))
            )

    @verifies("scenario.context.definition-inconsistent")
    def test_bind_rejects_an_inconsistent_inventory_definition(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _package(root)
            write_build(root)
            planner = agents.definition("planner")
            inconsistent = dataclasses.replace(planner, tools=("read", "write"))
            with (
                mock.patch.object(agents, "definition", return_value=inconsistent),
                self.assertRaises(SpecError) as failure,
            ):
                bind_agent(root, "planner")
            self.assertEqual("invalid_agent_binding", failure.exception.code)


if __name__ == "__main__":
    unittest.main()
