"""The public reading and real Agent discovery share one authority, not a link-only catalog."""

import importlib
import json
import tempfile
import unittest
from pathlib import Path

import agents
import operations
from concorde.distribution.build import build, load_model_instructions
from concorde.distribution.installation import Package, _package_files
from concorde.distribution.package_validation import _validate_spec_agents_block
from concorde.harness.worker_profile import WorkerProfile, load_worker_profiles
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
        self.assertEqual(9, len(agents.AGENTS))
        self.assertEqual(7, len(load_worker_profiles()))
        self.assertNotIn("main", agents.AGENTS)
        self.assertNotIn("user-session", agents.AGENTS)
        for name in ("planner", "task_author"):
            readme = (REPOSITORY_ROOT / "agents" / name / "README.md").read_text()
            self.assertIn("distributed with `agents/`", readme)
            self.assertNotIn("worker Operation", readme)
        for name in ("context_assessor", "task_author"):
            spec_text = (REPOSITORY_ROOT / "agents" / name / "spec.md").read_text()
            self.assertNotIn("`concorde-dependencies`", spec_text)
            self.assertIn("`uses`", spec_text)
        self.assertFalse(set(agents.DOMAIN_AGENTS) & set(operations.OPERATIONS))
        for name in agents.DOMAIN_AGENTS:
            module = importlib.import_module("agents." + name)
            self.assertIsInstance(module.PROFILE, WorkerProfile)
            self.assertFalse((REPOSITORY_ROOT / "operations" / name).exists())
            self.assertFalse(hasattr(module, "STATE"))
            self.assertFalse(hasattr(module, "run"))
        package = Package(
            REPOSITORY_ROOT, json.loads((REPOSITORY_ROOT / "concorde.json").read_text())
        )
        installed_files = _package_files(package)
        self.assertFalse(any("/agents/source/" in p for p in installed_files))
        self.assertTrue(
            any(p.endswith("/agents/task_subagent.py") for p in installed_files)
        )
        for profile in agents.TASK_SUBAGENT_PROFILES:
            self.assertNotIsInstance(profile, WorkerProfile)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            build_package_copy(root)
            for name in agents.DOMAIN_AGENTS:
                admitted = load_model_instructions(root, name)
                self.assertEqual(f"agents/{name}/spec.md", admitted.source_path)
                self.assertEqual(name, admitted.binding.agent)
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

    @verifies("scenario.agents.inventory")
    def test_metadata_drift_refuses_instead_of_creating_another_authority(self):
        path = "specs/concorde/agents/contracts.md"
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

    @verifies("scenario.agents.inventory")
    def test_missing_agent_and_malformed_metadata_are_findings(self):
        path = "specs/concorde/agents/contracts.md"
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
