"""The public reading and real Agent discovery share one authority, not a link-only catalog."""

import importlib
import json
import tempfile
import unittest
from pathlib import Path

import agents
import operations
from concorde.distribution.build import build
from concorde.distribution.installation import Package, _package_files
from concorde.distribution.package_validation import _validate_spec_agents_block
from agents.task_subagent import TASK_SUBAGENT_PROFILES
from concorde.harness.worker_profile import AgentDefinition, bind_agent
from concorde.spec.repository import SpecRepository
from concorde.spec.verification import verifies
from tests.concorde.support.build_fixture import build_package_copy
from tests.concorde.support.paths import REPOSITORY_ROOT


class AgentInventoryTests(unittest.TestCase):
    @verifies("scenario.agents.inventory")
    def test_peer_discovery_and_real_render_admission(self):
        repository = SpecRepository(REPOSITORY_ROOT)
        target = repository.module("module.agents")
        self.assertEqual("module.concorde", target.parent)
        self.assertEqual("specs/concorde/agents/module.md", target.primary_document)
        resolution = repository.spec_context(target.id).value
        scenario = repository.spec_context("scenario.agents.inventory").value
        self.assertEqual(resolution["sources"], scenario["sources"])
        sources = {source["path"]: source for source in resolution["sources"]}
        self.assertEqual(len(sources), len(resolution["sources"]))
        for path, source in sources.items():
            if source["role"] == "reading":
                paired = sources[path + ".json"]
                self.assertEqual(source["document_id"], paired["document_id"])
                self.assertEqual(source["owner"], paired["owner"])
                self.assertEqual(source["reasons"], paired["reasons"])
        # Every selected document is explained by a declaration of this Module alone.
        declaration = repository.module_declaration(target.id)
        selected = set(target.documents)
        for relation in (*declaration.contains, *declaration.uses):
            selected.update(repository.selection({**relation, "kind": "module"}))
        for relation in declaration.includes:
            selected.update(repository.selection(relation))
        self.assertEqual(
            {path for path, source in sources.items() if source["role"] == "reading"},
            selected,
        )
        self.assertEqual(7, len(agents.AGENTS))
        self.assertNotIn("main", agents.AGENTS)
        self.assertNotIn("user-session", agents.AGENTS)
        for name in ("context_assessor", "task_author"):
            spec_text = (REPOSITORY_ROOT / "agents" / name / "spec.md").read_text()
            self.assertNotIn("`concorde-dependencies`", spec_text)
            self.assertIn("`uses`", spec_text)
        self.assertFalse(set(agents.AGENTS) & set(operations.OPERATIONS))
        for name in agents.AGENTS:
            module = importlib.import_module("agents." + name)
            self.assertIsInstance(module.DEFINITION, AgentDefinition)
            self.assertEqual(
                ["DEFINITION"],
                [
                    key
                    for key in vars(module)
                    if key.isupper() and not key.startswith("_")
                ],
            )
            self.assertFalse((REPOSITORY_ROOT / "operations" / name).exists())
        package = Package(
            REPOSITORY_ROOT, json.loads((REPOSITORY_ROOT / "concorde.json").read_text())
        )
        installed_files = _package_files(package)
        self.assertFalse(any("/agents/source/" in p for p in installed_files))
        self.assertTrue(
            any(p.endswith("/agents/task_subagent.py") for p in installed_files)
        )
        for profile in TASK_SUBAGENT_PROFILES:
            self.assertNotIsInstance(profile, AgentDefinition)
            self.assertNotIn(profile.name, agents.AGENTS)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            build_package_copy(root)
            for name in agents.AGENTS:
                binding = bind_agent(root, name)
                self.assertEqual(f"agents/{name}/spec.md", binding.spec_path)
                self.assertEqual(name, binding.agent)
                self.assertEqual(
                    agents.definition(name).hook,
                    agents.definition("concorde-" + name.replace("_", "-")).hook,
                )
            source = {o.path: o.content for o in build(root).outputs}
            consumer = {
                o.path: o.content
                for o in build(root, framework_prefix=".concorde/framework").outputs
            }
            self.assertIn(".pi/agents/maintenance-worker.md", source)
            self.assertIn(".pi/agents/tester.md", source)
            self.assertIn(".pi/agents/tester.md", consumer)
            self.assertNotIn(".pi/agents/maintenance-worker.md", consumer)
            self.assertNotIn(".pi/extensions/concorde-coordinator.ts", consumer)

    @verifies("scenario.agents.inventory-drift")
    def test_metadata_drift_refuses_instead_of_creating_another_authority(self):
        path = "specs/concorde/agents/definitions.md"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            build_package_copy(root)
            metadata = json.loads((REPOSITORY_ROOT / (path + ".json")).read_text())
            output = root / (path + ".json")
            output.parent.mkdir(parents=True)
            output.write_text(json.dumps(metadata))
            self.assertEqual([], _validate_spec_agents_block(root, {path: "reading"}))
            metadata["extensions"]["concorde.agents"].append(
                metadata["extensions"]["concorde.agents"][0]
            )
            output.write_text(json.dumps(metadata))
            self.assertTrue(_validate_spec_agents_block(root, {path: "reading"}))

    @verifies("scenario.agents.inventory-drift")
    def test_missing_agent_and_malformed_metadata_are_findings(self):
        path = "specs/concorde/agents/definitions.md"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            build_package_copy(root)
            output = root / (path + ".json")
            output.parent.mkdir(parents=True)
            metadata = json.loads((REPOSITORY_ROOT / (path + ".json")).read_text())
            metadata["extensions"]["concorde.agents"] = [None]
            output.write_text(json.dumps(metadata))
            self.assertTrue(_validate_spec_agents_block(root, {path: "reading"}))
            (root / "agents/planner/__init__.py").unlink()
            self.assertTrue(_validate_spec_agents_block(root, {path: "reading"}))

    @verifies("scenario.agents.inventory-drift")
    def test_each_inventory_difference_is_a_finding_without_a_second_definition(self):
        path = "specs/concorde/agents/definitions.md"
        metadata = json.loads((REPOSITORY_ROOT / (path + ".json")).read_text())
        entries = metadata["extensions"]["concorde.agents"]

        def drifted(**change):
            value = json.loads(json.dumps(metadata))
            value["extensions"]["concorde.agents"] = change["entries"]
            return value

        missing = entries[1:]
        duplicated = [*entries, entries[0]]
        other_hook = [
            {**entries[0], "hook": "concorde.planning.hooks:other"},
            *entries[1:],
        ]
        other_source = [{**entries[0], "source": "agents/other/spec.md"}, *entries[1:]]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            build_package_copy(root)
            output = root / (path + ".json")
            output.parent.mkdir(parents=True)
            for label, value in {
                "missing Agent": drifted(entries=missing),
                "duplicated Agent": drifted(entries=duplicated),
                "different hook": drifted(entries=other_hook),
                "different source": drifted(entries=other_source),
            }.items():
                with self.subTest(label):
                    output.write_text(json.dumps(value))
                    findings = _validate_spec_agents_block(root, {path: "reading"})
                    self.assertEqual(
                        ["CONCORDE-SPEC-AGENTS-001"], [f.rule_id for f in findings]
                    )
            output.write_text(json.dumps(metadata))
            self.assertEqual([], _validate_spec_agents_block(root, {path: "reading"}))
            # An unlisted Agent directory is a finding, never a second definition in use.
            extra = root / "agents/extra_reviewer"
            extra.mkdir()
            (extra / "spec.md").write_text("# Extra reviewer\n")
            (extra / "__init__.py").write_text(
                (root / "agents/planner/__init__.py").read_text()
            )
            findings = _validate_spec_agents_block(root, {path: "reading"})
            self.assertEqual(
                ["CONCORDE-SPEC-AGENTS-001"], [f.rule_id for f in findings]
            )
            self.assertEqual("agents/__init__.py", findings[0].source)
        self.assertNotIn("extra_reviewer", agents.AGENTS)
        with self.assertRaises(KeyError):
            agents.definition("extra_reviewer")

    @verifies("scenario.agents.invalid-definition")
    def test_a_definition_outside_the_rules_refuses_loading(self):
        import dataclasses
        from unittest import mock

        planner = importlib.import_module("agents.planner").DEFINITION
        for label, definition in {
            "delegating tool": dataclasses.replace(
                planner, tools=(*planner.tools, "subagent")
            ),
            "unknown tool": dataclasses.replace(planner, tools=(*planner.tools, "web")),
            "bash without writes": dataclasses.replace(
                planner, tools=(*planner.tools, "bash")
            ),
            "no hook": dataclasses.replace(planner, hook=""),
        }.items():
            with (
                self.subTest(label),
                mock.patch.object(
                    importlib.import_module("agents.planner"), "DEFINITION", definition
                ),
                self.assertRaises(ValueError) as failure,
            ):
                agents.definition("planner")
            self.assertIn("planner", str(failure.exception))
