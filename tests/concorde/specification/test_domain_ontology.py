"""Spec Protocol 1.2: main-document identity and diagram authoring are usable end to end."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from concorde.host.capability_host import CapabilityHost, run_capability
from concorde.host.typed_data import typed
from concorde.specification.context import resolve_context, recheck_context
from concorde.specification.initialize import project_proposal, apply_project_proposal, empty_target
from concorde.specification.repository import SpecError, SpecRepository
from concorde.specification.validation import validate_repository
from tests.concorde.specification.support import (
    CONFIGURATION, PACKAGE, ModelProcessDouble, project, update_document_declaration,
)


class DomainOntologyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.registry = project(self.root)
        self.main = "specs/bank/ontology.md"
        self.diagram = "specs/bank/diagrams/overview.json"

    def save(self):
        (self.root / ".concorde/specs.json").write_text(json.dumps(self.registry))

    def call(self, capability, data, callback=None):
        double = ModelProcessDouble(callback)
        return run_capability(capability, CONFIGURATION, typed(capability + "-request", data),
            host_context=CapabilityHost(self.root, PACKAGE, executor=double.executor,
                                        allow_primary_worktree=True))

    def test_main_document_does_not_depend_on_order_or_replace_full_context(self):
        topic = "specs/bank/routing.md"
        (self.root / topic).write_text('```concorde-document\n' + json.dumps({
            "id": "document.bank.routing", "targets": ["scope.bank"], "main_visible": True,
        }) + '\n```\n\n# Routing\nRead the registered banking responsibilities.\n')
        self.registry["targets"][0]["documents"].insert(0, topic)
        self.save()
        repository = SpecRepository(self.root)
        target = repository.select("scope.bank")
        self.assertEqual(self.main, target.primary_document)
        snapshot = resolve_context(repository, target.id).value
        self.assertEqual([topic, self.main], snapshot["document_order"])
        self.assertEqual([topic, self.main], [d["path"] for d in snapshot["target_spec"]])
        self.assertEqual([self.diagram], [d["path"] for d in snapshot["diagram_sources"]])
        self.assertEqual("success", validate_repository(self.root).status)

    def test_missing_duplicate_or_shared_domain_main_document_is_rejected(self):
        original = copy.deepcopy(self.registry)
        cases = [
            ["specs/bank/topic.md"],
            [self.main, "specs/another/ontology.md"],
        ]
        for members in cases:
            with self.subTest(members=members):
                self.registry = copy.deepcopy(original)
                self.registry["targets"][0]["documents"] = members
                self.save()
                with self.assertRaisesRegex(SpecError, "exactly one.*ontology.md"):
                    SpecRepository(self.root)
        self.registry = copy.deepcopy(original)
        self.registry["targets"][2]["documents"].append(self.main)
        self.save()
        with self.assertRaisesRegex(SpecError, "only its own Domain"):
            SpecRepository(self.root)

    def test_domain_main_is_visible_and_ontology_heading_must_be_outside_fences(self):
        update_document_declaration(self.root, self.main, main_visible=False)
        with self.assertRaisesRegex(SpecError, "main_visible"):
            resolve_context(SpecRepository(self.root), "scope.bank")
        update_document_declaration(self.root, self.main, main_visible=True)
        path = self.root / self.main
        body = path.read_text().replace("## Ontology", "## Vocabulary")
        for fence in ("```", "~~~~"):
            with self.subTest(fence=fence):
                path.write_text(body + f"\n{fence}markdown\n## Ontology\n{fence}\n")
                report = validate_repository(self.root)
                self.assertIn("CONCORDE-ONTOLOGY-001", {f.rule_id for f in report.findings})

    def test_domain_overview_is_exactly_one_architecture_recipe(self):
        declaration = copy.deepcopy(self.registry["targets"][0]["diagrams"][0])
        for diagrams in ([], [{**declaration, "kind": "workflow"}],
                         [declaration, {**declaration, "source": "specs/bank/another.json"}]):
            with self.subTest(diagrams=diagrams):
                self.registry["targets"][0]["diagrams"] = diagrams
                self.save()
                with self.assertRaises(SpecError):
                    SpecRepository(self.root)

    def test_declared_source_metadata_and_output_boundary_are_checked(self):
        path = self.root / self.diagram
        original = json.loads(path.read_text())
        for field, value in (("title", "Wrong"), ("quality_profile", "standard"),
                             ("output", "../../../generated/protocol/rules.html")):
            with self.subTest(field=field):
                candidate = copy.deepcopy(original)
                candidate["meta"][field] = value
                path.write_text(json.dumps(candidate))
                report = validate_repository(self.root)
                self.assertIn("CONCORDE-DIAGRAM-001", {f.rule_id for f in report.findings})

    def test_diagram_bytes_invalidate_an_existing_context(self):
        repository = SpecRepository(self.root)
        snapshot = resolve_context(repository, "scope.bank")
        path = self.root / self.diagram
        diagram = json.loads(path.read_text())
        diagram["components"][1]["sublabel"] = "A revised authoring promise"
        path.write_text(json.dumps(diagram))
        with self.assertRaisesRegex(SpecError, "bytes changed"):
            recheck_context(repository, snapshot)

    def test_diagram_declaration_alone_also_invalidates_context(self):
        repository = SpecRepository(self.root)
        snapshot = resolve_context(repository, "scope.bank")
        self.registry["targets"][0]["diagrams"][0]["title"] = "Revised banking overview"
        self.save()
        with self.assertRaisesRegex(SpecError, "declarations"):
            recheck_context(repository, snapshot)

    def test_spec_author_can_update_its_diagram_but_cannot_write_a_foreign_source(self):
        before = (self.root / self.diagram).read_text()
        replacement = json.loads(before)
        replacement["components"][1]["sublabel"] = "Banking rules awaiting authoring"
        after = json.dumps(replacement)

        def callback(stage, snapshot, result, cwd):
            if stage == "specify":
                self.assertEqual(self.diagram, snapshot["diagram_sources"][0]["path"])
                result["diagrams"] = [{"path": self.diagram, "content": after}]

        result = self.call("concorde-specify", {"target_id": "scope.bank", "task": "Clarify the banking overview"}, callback)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual(after, (self.root / self.diagram).read_text())
        foreign = "specs/audit/diagrams/overview.json"
        foreign_before = (self.root / foreign).read_bytes()

        def illegal(stage, snapshot, result, cwd):
            if stage == "specify":
                result["diagrams"] = [{"path": foreign, "content": after}]

        result = self.call("concorde-specify", {"target_id": "scope.bank", "task": "Clarify the banking overview"}, illegal)
        self.assertEqual("permission_denied", result["errors"][0]["code"], result)
        self.assertEqual(foreign_before, (self.root / foreign).read_bytes())

    def test_invalid_diagram_rolls_back_markdown_and_diagram_together(self):
        original = (self.root / self.main).read_bytes()
        diagram_before = (self.root / self.diagram).read_bytes()

        def callback(stage, snapshot, result, cwd):
            if stage == "specify":
                result["documents"] = [{"path": self.main, "content": original.decode() + "\nA proposed rule.\n"}]
                result["diagrams"] = [{"path": self.diagram, "content": "{}"}]

        result = self.call("concorde-specify", {"target_id": "scope.bank", "task": "Update overview and rules"}, callback)
        self.assertNotEqual("succeeded", result["status"], result)
        self.assertEqual(original, (self.root / self.main).read_bytes())
        self.assertEqual(diagram_before, (self.root / self.diagram).read_bytes())

    def test_new_domain_topology_authors_and_applies_ontology_and_diagram(self):
        def callback(stage, snapshot, result, cwd):
            if stage == "route" and snapshot["action"] == "design-topology":
                registry = copy.deepcopy(snapshot["topology"])
                target = empty_target("scope.risk", "domain", "Risk", ["specs/risk/ontology.md"])
                target["scope_parent"] = "scope.bank"
                target["diagrams"] = [{"source": "specs/risk/diagrams/overview.json", "kind": "architecture",
                                       "title": "Risk", "recipe": "system-overview"}]
                registry["targets"].append(target)
                design = typed("concorde-topology-design", {"summary": "Add a Risk Domain.",
                    "registry": registry, "spec_tasks": [
                        {"target_id": "scope.bank", "task": "Route risk modeling tasks to scope.risk."},
                        {"target_id": "scope.risk", "task": "Define the known authoring boundary and name missing risk rules."}],
                    "migration_constraints": [], "acceptance": ["Risk has an ontology.md and an architecture overview."]})
                result.update(outcome="topology_proposed", answer="Risk Domain proposed.",
                              routes=[], expand_targets=[], gaps=[], topology_design=design)

        result = self.call("concorde-main", {"action": "design-topology", "task": "Add the Risk Domain"}, callback)
        self.assertEqual("topology_proposed", result["output"]["data"]["outcome"], result)
        proposal = result["output"]["data"]["topology_proposal"]
        prepared = self.call("concorde-main", {"action": "accept-topology", "topology_proposal": proposal}, callback)
        self.assertIsNotNone(prepared["output"], prepared)
        self.assertEqual("topology_prepared", prepared["output"]["data"]["outcome"], prepared)
        self.assertFalse((self.root / "specs/risk/ontology.md").exists())
        application = prepared["output"]["data"]["application"]
        applied = self.call("concorde-main", {"action": "apply-topology", "application": application}, callback)
        self.assertEqual("topology_applied", applied["output"]["data"]["outcome"], applied)
        self.assertTrue((self.root / "specs/risk/ontology.md").is_file())
        self.assertTrue((self.root / "specs/risk/diagrams/overview.json").is_file())
        self.assertEqual("success", validate_repository(self.root).status)


class InitialOntologyTests(unittest.TestCase):
    def test_initialization_is_honest_and_rolls_back_a_bad_overview(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proposal = project_proposal(root, PACKAGE, "New project", CONFIGURATION)
            source = next(f for f in proposal["files"] if f["path"].endswith("overview.architecture.json"))
            before = source["content"]
            source["content"] = "{}"
            with self.assertRaises(SpecError):
                apply_project_proposal(root, PACKAGE, proposal)
            self.assertFalse((root / ".concorde/config.json").exists())
            self.assertFalse((root / "specs/project/ontology.md").exists())
            source["content"] = before
            apply_project_proposal(root, PACKAGE, proposal)
            repository = SpecRepository(root, PACKAGE)
            target = repository.select("domain.project")
            self.assertEqual("specs/project/ontology.md", target.primary_document)
            self.assertIn("not yet been supplied", repository.document(target.primary_document).body)
            self.assertEqual("success", validate_repository(root, package_root=PACKAGE).status)


if __name__ == "__main__":
    unittest.main()
