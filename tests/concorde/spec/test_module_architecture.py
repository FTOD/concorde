"""Spec Protocol 3.0: the reading entry, its inline architecture diagram and entity listings."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from concorde.development.capability_host import CapabilityHost, run_capability
from concorde.spec.typed_data import typed
from concorde.harness.context import resolve_context, recheck_context
from concorde.spec.initialize import project_proposal, apply_project_proposal, empty_target
from concorde.spec.repository import SpecError, SpecRepository
from concorde.spec.validation import validate_repository
from concorde.spec.verification import verifies
from tests.concorde.spec.support import (
    CONFIGURATION, PACKAGE, ModelProcessDouble, project, update_document_declaration,
)


def replace_entities(text, update):
    prefix, rest = text.split("```concorde-entities\n", 1)
    payload, suffix = rest.split("\n```", 1)
    value = update(json.loads(payload))
    return prefix + "```concorde-entities\n" + json.dumps(value, indent=2) + "\n```" + suffix


class ModuleArchitectureTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.registry = project(self.root)
        self.main = "specs/bank/module.md"

    def save(self):
        (self.root / ".concorde/specs.json").write_text(json.dumps(self.registry))

    def call(self, capability, data, callback=None):
        double = ModelProcessDouble(callback)
        return run_capability(capability, CONFIGURATION, typed(capability + "-request", data),
            host_context=CapabilityHost(self.root, PACKAGE, executor=double.executor,
                                        allow_primary_worktree=True))

    @verifies("scenario.spec.select-module")
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
        self.assertEqual("success", validate_repository(self.root).status)

    def test_missing_duplicate_or_shared_module_entry_is_rejected(self):
        original = copy.deepcopy(self.registry)
        cases = [
            ["specs/bank/topic.md"],
            [self.main, "specs/another/module.md"],
        ]
        for members in cases:
            with self.subTest(members=members):
                self.registry = copy.deepcopy(original)
                self.registry["targets"][0]["documents"] = members
                self.save()
                with self.assertRaisesRegex(SpecError, "exactly one.*module.md"):
                    SpecRepository(self.root)
        self.registry = copy.deepcopy(original)
        self.registry["targets"][2]["documents"].append(self.main)
        self.save()
        with self.assertRaisesRegex(SpecError, "exactly one.*module.md"):
            SpecRepository(self.root)

    @verifies("scenario.spec.query-files", "scenario.spec.validate-structural-errors")
    def test_complete_context_ignores_visibility_and_architecture_heading_is_outside_fences(self):
        update_document_declaration(self.root, self.main, main_visible=False)
        self.assertIn(self.main, resolve_context(SpecRepository(self.root), "scope.bank").value["document_order"])
        update_document_declaration(self.root, self.main, main_visible=True)
        path = self.root / self.main
        body = path.read_text().replace("### Relationships", "### Vocabulary")
        for fence in ("```", "~~~~"):
            with self.subTest(fence=fence):
                path.write_text(body + f"\n{fence}markdown\n### Relationships\n{fence}\n")
                report = validate_repository(self.root)
                self.assertIn("CONCORDE-MODULE-001", {f.rule_id for f in report.findings})

    @verifies("scenario.spec.validate-structural-errors")
    def test_the_reading_entry_requires_a_mermaid_flowchart_in_its_architecture_section(self):
        path = self.root / self.main
        original = path.read_text()
        start = original.index("```mermaid\n")
        end = original.index("\n```", start) + len("\n```\n")
        path.write_text(original[:start] + original[end:])
        report = validate_repository(self.root)
        self.assertEqual("invalid", report.status)
        self.assertIn("CONCORDE-MODULE-001", {f.rule_id for f in report.findings})
        self.assertTrue(any("Mermaid flowchart fence" in f.message for f in report.findings))

    @verifies("scenario.spec.validate-architecture-mismatch")
    def test_diagram_nodes_must_equal_entity_titles_and_every_edge_must_be_labeled(self):
        path = self.root / self.main
        original = path.read_text()
        path.write_text(original.replace("request -->|admitted by| transfer",
                                         "request --> transfer"))
        report = validate_repository(self.root)
        self.assertEqual("invalid", report.status)
        self.assertIn("CONCORDE-ARCHITECTURE-002", {f.rule_id for f in report.findings})
        path.write_text(original.replace('audit["Audit"]', 'audit["Auditing"]'))
        report = validate_repository(self.root)
        self.assertEqual("invalid", report.status)
        self.assertIn("CONCORDE-ARCHITECTURE-001", {f.rule_id for f in report.findings})
        path.write_text(original.replace('    request["Transfer request"]',
                                         '    request["Transfer request"'))
        report = validate_repository(self.root)
        self.assertEqual("invalid", report.status)
        self.assertIn("CONCORDE-ARCHITECTURE-002", {f.rule_id for f in report.findings})

    @verifies("scenario.spec.validate-structural-errors")
    def test_an_entity_can_only_stand_for_a_child_or_used_module(self):
        path = self.root / self.main
        path.write_text(replace_entities(path.read_text(), lambda values: [
            {**value, "target_id": "module.ledger"} if value["id"] == "entity.bank.audit" else value
            for value in values]))
        report = validate_repository(self.root)
        self.assertEqual("invalid", report.status)
        self.assertIn("CONCORDE-DEFINITION-001", {f.rule_id for f in report.findings})
        self.assertTrue(any("is represented by two entities" in f.message for f in report.findings))

    def test_inline_diagram_bytes_invalidate_an_existing_context(self):
        repository = SpecRepository(self.root)
        snapshot = resolve_context(repository, "scope.bank")
        path = self.root / self.main
        path.write_text(path.read_text().replace("accTitle: Banking coordination",
                                                 "accTitle: Banking settlement"))
        with self.assertRaisesRegex(SpecError, "bytes changed"):
            recheck_context(repository, snapshot)

    def test_entity_file_listings_invalidate_an_existing_context(self):
        repository = SpecRepository(self.root)
        snapshot = resolve_context(repository, "service.transfer", phase="plan")
        # A registry-only file listing change leaves every document byte untouched.
        self.registry["targets"][2]["files"] = ["app/extra.py", "app/transfer.py",
                                                "checks/transfer_check.py"]
        self.save()
        with self.assertRaisesRegex(SpecError, "listed implementation entries"):
            recheck_context(repository, snapshot)

    def test_spec_author_can_update_its_own_inline_diagram_but_not_a_foreign_document(self):
        path = self.root / self.main
        after = path.read_text().replace(
            "accDescr: A transfer request reaches the transfer service",
            "accDescr: One transfer request reaches the transfer service")

        def callback(stage, snapshot, result, cwd):
            if stage == "specify":
                result["documents"] = [{"path": self.main, "content": after}]

        result = self.call("concorde-specify", {"target_id": "scope.bank", "task": "Clarify the banking overview"}, callback)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual(after, path.read_text())
        foreign = "specs/audit/module.md"
        foreign_before = (self.root / foreign).read_bytes()

        def illegal(stage, snapshot, result, cwd):
            if stage == "specify":
                result["documents"] = [{"path": foreign, "content": after}]

        result = self.call("concorde-specify", {"target_id": "scope.bank", "task": "Clarify the banking overview"}, illegal)
        self.assertEqual("permission_denied", result["errors"][0]["code"], result)
        self.assertEqual(foreign_before, (self.root / foreign).read_bytes())

    def test_an_invalid_inline_diagram_rolls_the_whole_document_back(self):
        path = self.root / self.main
        original = path.read_bytes()
        broken = original.decode().replace("transfer -->|reports accepted changes to| audit",
                                           "transfer --> audit")

        def callback(stage, snapshot, result, cwd):
            if stage == "specify":
                result["documents"] = [{"path": self.main, "content": broken}]

        result = self.call("concorde-specify", {"target_id": "scope.bank", "task": "Update overview and rules"}, callback)
        self.assertNotEqual("succeeded", result["status"], result)
        self.assertEqual("invalid_spec", result["errors"][0]["code"], result)
        self.assertEqual(original, path.read_bytes())

    def test_new_module_topology_authors_and_applies_its_own_contract(self):
        def callback(stage, snapshot, result, cwd):
            if stage == "route" and snapshot["action"] == "design-topology":
                registry = copy.deepcopy(snapshot["topology"])
                target = empty_target("scope.risk", "module", "Risk", ["specs/risk/module.md"])
                target["parent"] = "scope.bank"
                registry["targets"].append(target)
                design = typed("concorde-topology-design", {"summary": "Add a Risk Module.",
                    "registry": registry, "spec_tasks": [
                        {"target_id": "scope.bank", "task": "Route risk modeling tasks to scope.risk."},
                        {"target_id": "scope.risk", "task": "Define the known authoring boundary and name missing risk rules."}],
                    "migration_constraints": [], "acceptance": ["Risk is registered and routable."]})
                result.update(outcome="topology_proposed", answer="Risk Module proposed.",
                              routes=[], expand_targets=[], gaps=[], topology_design=design)

            if stage == "topology-author" and snapshot["target"]["id"] == "scope.bank":
                import re
                item = next(item for item in result["documents"] if item["path"] == self.main)
                match = re.search(r"```concorde-dependencies\s*\n(.*?)^```", item["content"], re.M | re.S)
                entries = json.loads(match.group(1))
                entries.append({"target_id": "scope.risk",
                    "responsibility": "Describe risk modeling.", "selection_condition": "Select for risk rules.",
                    "relied_upon_promises": ["Unknown risk rules remain explicit rather than inferred from code."]})
                content = (item["content"][:match.start()] + "```concorde-dependencies\n"
                           + json.dumps(entries) + "\n```" + item["content"][match.end():])
                content = replace_entities(content, lambda values: [*values, {
                    "id": "entity.bank.risk", "title": "Risk", "kind": "module",
                    "responsibility": "Describes risk modeling for Banking.",
                    "target_id": "scope.risk"}])
                item["content"] = content.replace('    audit["Audit"]',
                    '    audit["Audit"]\n    risk["Risk"]').replace(
                    "    transfer -->|reports accepted changes to| audit",
                    "    transfer -->|reports accepted changes to| audit\n"
                    "    request -->|assessed by| risk")

        result = self.call("concorde-main", {"action": "design-topology", "task": "Add the Risk Module"}, callback)
        self.assertEqual("topology_proposed", result["output"]["data"]["outcome"], result)
        proposal = result["output"]["data"]["topology_proposal"]
        prepared = self.call("concorde-main", {"action": "accept-topology", "topology_proposal": proposal}, callback)
        self.assertIsNotNone(prepared["output"], prepared)
        self.assertEqual("topology_prepared", prepared["output"]["data"]["outcome"], prepared)
        self.assertFalse((self.root / "specs/risk/module.md").exists())
        application = prepared["output"]["data"]["application"]
        applied = self.call("concorde-main", {"action": "apply-topology", "application": application}, callback)
        self.assertEqual("topology_applied", applied["output"]["data"]["outcome"], applied)
        self.assertTrue((self.root / "specs/risk/module.md").is_file())
        report = validate_repository(self.root)
        self.assertEqual("success", report.status, [f.message for f in report.findings])
        repository = SpecRepository(self.root)
        risk = repository.select("scope.risk")
        self.assertEqual((), risk.files)
        self.assertTrue(repository.scenarios(risk))


class InitialModuleTests(unittest.TestCase):
    @verifies("scenario.spec.propose-initialization", "scenario.spec.apply-initialization", "scenario.spec.rollback-on-failure")
    def test_initialization_is_honest_and_rolls_back_a_bad_reading_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proposal = project_proposal(root, PACKAGE, "New project", CONFIGURATION)
            source = next(f for f in proposal["files"]
                          if f["path"] == "specs/project/module.md")
            before = source["content"]
            source["content"] = before.replace("### Relationships", "### Drawing")
            with self.assertRaises(SpecError):
                apply_project_proposal(root, PACKAGE, proposal)
            self.assertFalse((root / ".concorde/config.json").exists())
            self.assertFalse((root / "specs/project/module.md").exists())
            source["content"] = before
            apply_project_proposal(root, PACKAGE, proposal)
            repository = SpecRepository(root, PACKAGE)
            target = repository.select("module.project")
            self.assertEqual("specs/project/module.md", target.primary_document)
            body = repository.document(target.primary_document).body
            self.assertIn("not yet been supplied", body)
            self.assertEqual((), target.files)
            self.assertEqual({"Project Spec", "Developer", "Concorde Framework"},
                             {entity.title for entity in repository.entities(target)})
            self.assertEqual("success", validate_repository(root, package_root=PACKAGE).status)


if __name__ == "__main__":
    unittest.main()
