"""Behavioral regression tests for the four-part Module model, without model calls."""
from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from concorde.development.capability_host import Invocation, _implementation_digest, _target_revision
from concorde.spec.changes import confirm_pending_files
from concorde.harness.context import resolve_context, recheck_context
from concorde.spec.repository import SpecError, SpecRepository, digest
from concorde.spec.validation import validate_repository


PACKAGE = Path(__file__).resolve().parents[3]


def reading_entry(target_id, title, purpose, scenario, entities, diagram, dependencies=None):
    """One valid four-part reading entry for the small composition fixture."""
    declaration = {"id": "document." + target_id, "targets": [target_id], "main_visible": True}
    text = ("```concorde-document\n" + json.dumps(declaration, indent=2) + "\n```\n\n"
        f"# {title}\n\n## Purpose\n\n{purpose}\n\n## Scenarios\n\n{scenario}\n"
        "\n## Entities\n\nEvery entity below is declared locally.\n\n"
        "```concorde-entities\n" + json.dumps(entities, indent=2) + "\n```\n"
        f"\n## Architecture\n\nThe declared entities relate as the diagram states.\n\n"
        "```mermaid\n" + diagram + "\n```\n")
    if dependencies:
        text += ("\n## Collaborators\n\nEach collaborator is described locally.\n\n"
                 "```concorde-dependencies\n" + json.dumps(dependencies, indent=2) + "\n```\n")
    return text


class ModuleImplementationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.configuration = {"type_id": "concorde-capability-configuration", "schema_version": 1,
                              "data": {"integration": "claude", "enforcement": "native"}}
        manifest = (PACKAGE / "protocol/manifest.json").read_bytes()
        self.write(".concorde/config.json", json.dumps({"profile_version": 10,
            "registry": ".concorde/specs.json", "protocol": {
                "version": "3.0.0", "digest": digest(manifest)},
            "capability_configuration": self.configuration}))
        self.write("source/shared.py", "def value():\n    return 42\n# PRIVATE_SOURCE_MARKER\n")
        self.write("source/a.py", "def adapt(value):\n    return value\n")
        self.write("specs/root/module.md", reading_entry("module.root", "root",
            "ROOT_MODULE_CONTRACT: the root composes its two submodules and owns no code.",
            "### scenario.root.value — The root reports a composed value\n\n"
            "- GIVEN both submodules answer\n- WHEN the root is asked for its value\n"
            "- THEN it reports the composed integer\n",
            [{"id": "entity.root.a", "title": "A", "kind": "module",
              "responsibility": "Adapts the shared value.", "target_id": "module.a"},
             {"id": "entity.root.b", "title": "B", "kind": "module",
              "responsibility": "Reads the shared value.", "target_id": "module.b"}],
            "flowchart TB\n    accTitle: root composition\n"
            "    accDescr: A and B are the root's two submodules and both answer with an integer.\n"
            '    a["A"]\n    b["B"]\n    a -->|answers beside| b',
            [{"target_id": "module." + peer, "responsibility": "Return its value.",
              "selection_condition": "Select for " + peer,
              "relied_upon_promises": ["value returns an integer."]} for peer in ("a", "b")]))
        self.write("specs/a/module.md", reading_entry("module.a", "a",
            "A_MODULE_CONTRACT: A adapts the shared integer for its own consumers.",
            "### scenario.a.value — A adapts the shared value\n\n"
            "- GIVEN the shared value function\n- WHEN A adapts it\n- THEN it returns the same integer\n"
            "- req.a.pure: A SHALL NOT change the shared value.\n",
            [{"id": "entity.a.adapter", "title": "Adapter", "kind": "function",
              "responsibility": "Adapts the shared integer.", "files": ["source/a.py"]},
             {"id": "entity.a.shared", "title": "Shared value", "kind": "function",
              "responsibility": "Answers with the shared integer.", "files": ["source/shared.py"]}],
            "flowchart TB\n    accTitle: A\n"
            "    accDescr: The adapter reads the shared value function.\n"
            '    adapter["Adapter"]\n    shared["Shared value"]\n    adapter -->|reads| shared'))
        self.write("specs/a/details.md", "```concorde-document\n" + json.dumps(
            {"id": "document.a.details", "targets": ["module.a"], "main_visible": True}, indent=2)
            + "\n```\n\n# Local details\n\nA_OWN_ADDITIONAL_CONTRACT: the adapted integer is never negative.\n")
        self.write("specs/b/module.md", reading_entry("module.b", "b",
            "B_PRIVATE_SPEC: B reads the shared integer and promises exactly 42.",
            "### scenario.b.value — B reports the shared value\n\n"
            "- GIVEN the shared value function\n- WHEN B is asked for its value\n- THEN it returns 42\n",
            [{"id": "entity.b.shared", "title": "Shared value", "kind": "function",
              "responsibility": "Answers with the shared integer.", "files": ["source/shared.py"]}],
            "flowchart TB\n    accTitle: B\n"
            "    accDescr: B holds only the shared value function.\n"
            '    shared["Shared value"]'))
        targets = [
            {"id": "module.root", "kind": "module", "title": "root",
             "documents": ["specs/root/module.md"], "parent": None, "uses": [],
             "files": [], "checks": []},
            {"id": "module.a", "kind": "module", "title": "a",
             "documents": ["specs/a/module.md", "specs/a/details.md"], "parent": "module.root",
             "uses": [], "files": ["source/a.py", "source/shared.py"], "checks": []},
            {"id": "module.b", "kind": "module", "title": "b",
             "documents": ["specs/b/module.md"], "parent": "module.root", "uses": [],
             "files": ["source/shared.py"], "checks": []}]
        self.registry = {"schema_version": 3, "project_id": "project.test",
                         "entry_target": "module.root", "targets": targets, "checks": []}
        self.save_registry()

    def write(self, path, content):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content)

    def save_registry(self):
        self.write(".concorde/specs.json", json.dumps(self.registry))

    def repository(self):
        return SpecRepository(self.root, PACKAGE)

    def entity_block(self, path):
        text = (self.root / path).read_text()
        prefix, rest = text.split("```concorde-entities\n", 1)
        payload, suffix = rest.split("\n```", 1)
        return json.loads(payload), (lambda value: self.write(
            path, prefix + "```concorde-entities\n" + json.dumps(value, indent=2) + "\n```" + suffix))

    def test_the_fixture_is_a_valid_four_part_project(self):
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("success", report.status, [f.message for f in report.findings])

    def test_non_code_agents_receive_the_whole_module_and_only_file_names(self):
        for phase in ("ask", "specify", "plan", "tasks", "context-solve", "spec-review"):
            with self.subTest(phase=phase):
                snapshot = resolve_context(self.repository(), "module.a", phase=phase,
                                           focus_id="scenario.a.value")
                self.assertIn("A_MODULE_CONTRACT", snapshot.serialized)
                self.assertIn("A_OWN_ADDITIONAL_CONTRACT", snapshot.serialized)
                self.assertNotIn("B_PRIVATE_SPEC", snapshot.serialized)
                self.assertNotIn("PRIVATE_SOURCE_MARKER", snapshot.serialized)
                # The listed file names are Spec facts; their contents never are.
                self.assertEqual([("source/a.py", "entity.a.adapter", False),
                                  ("source/shared.py", "entity.a.shared", False)],
                                 [(item["path"], item["entity_id"], item["pending"])
                                  for item in snapshot.value["implementation_files"]])
                self.assertEqual([], snapshot.value["implementation_artifacts"])

    def test_only_code_phases_receive_the_exact_file_artifacts(self):
        for phase in ("implementation", "code-review"):
            with self.subTest(phase=phase):
                snapshot = resolve_context(self.repository(), "module.a", phase=phase)
                self.assertEqual({"source/shared.py", "source/a.py"},
                                 {item["path"] for item in snapshot.value["implementation_artifacts"]})
                self.assertNotIn("B_PRIVATE_SPEC", snapshot.serialized)
                # Artifacts identify bytes by digest; the snapshot never carries source text.
                self.assertNotIn("PRIVATE_SOURCE_MARKER", snapshot.serialized)

    def test_a_shared_file_has_one_identity_and_every_listing_module(self):
        repository = self.repository()
        self.assertEqual(("module.a", "module.b"), repository.file_users["source/shared.py"])
        self.assertEqual(("module.a",), repository.file_users["source/a.py"])
        self.assertEqual(("module.a", "module.b"),
                         tuple(t.id for t in repository.affected_modules(["source/shared.py"])))
        self.assertEqual(("module.a",),
                         tuple(t.id for t in repository.affected_modules(["source/a.py"])))
        self.assertEqual(("source/a.py", "source/shared.py"),
                         repository.implementation_paths(repository.select("module.a")))

    def test_two_entities_of_one_module_cannot_list_the_same_file(self):
        entities, save = self.entity_block("specs/a/module.md")
        entities[1]["files"] = ["source/a.py"]
        save(entities)
        with self.assertRaisesRegex(SpecError, "listed by two entities"):
            self.repository().entities(self.repository().select("module.a"))

    def test_directory_is_not_a_file_listing(self):
        self.registry["targets"][1]["files"] = ["source"]
        self.save_registry()
        with self.assertRaisesRegex(SpecError, "explicit files"):
            self.repository()

    def test_a_spec_document_cannot_be_listed_as_an_implementation_file(self):
        self.registry["targets"][2]["files"] = ["source/shared.py", "specs/a/details.md"]
        self.save_registry()
        with self.assertRaisesRegex(SpecError, "project Spec file"):
            self.repository()

    def test_registry_files_must_equal_the_union_of_entity_files(self):
        self.registry["targets"][1]["files"] = ["source/a.py"]
        self.save_registry()
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("invalid", report.status)
        self.assertIn("CONCORDE-ENTITY-003", {finding.rule_id for finding in report.findings})

    def test_module_composition_rejects_cycles_and_shared_private_children(self):
        self.registry["targets"][0]["parent"] = "module.a"
        self.save_registry()
        with self.assertRaisesRegex(SpecError, "cycle"):
            self.repository()
        self.registry["targets"][0]["parent"] = None
        self.registry["targets"][0]["uses"] = ["module.b"]
        self.registry["targets"][1]["uses"] = ["module.b"]
        self.registry["targets"][2]["parent"] = None
        self.save_registry()
        with self.assertRaisesRegex(SpecError, "siblings"):
            self.repository()

    def test_file_only_change_invalidates_writers_not_planner_context(self):
        repository = self.repository()
        planned = resolve_context(repository, "module.a", phase="plan")
        coding = resolve_context(repository, "module.a", phase="implementation")
        self.write("source/shared.py", "def value():\n    return 43\n")
        recheck_context(repository, planned)
        with self.assertRaisesRegex(SpecError, "implementation input"):
            recheck_context(repository, coding)

    def test_shared_change_invalidates_each_implementation_revision(self):
        before = self.repository()
        old = {key: _implementation_digest(before, before.select(key)) for key in ("module.a", "module.b")}
        module_revision = _target_revision(before, before.select("module.a"))
        self.write("source/shared.py", "def value():\n    return 43\n")
        after = self.repository()
        for key in old:
            self.assertNotEqual(old[key], _implementation_digest(after, after.select(key)))
        self.assertEqual(module_revision, _target_revision(after, after.select("module.a")))

    def test_a_new_listing_module_joins_the_reverse_index_without_entering_the_context(self):
        from concorde.development.capability_host import _implementation_users
        snapshot = resolve_context(self.repository(), "module.a", phase="implementation")
        entities, save = self.entity_block("specs/root/module.md")
        entities.append({"id": "entity.root.shared", "title": "Shared value", "kind": "function",
                         "responsibility": "Answers with the shared integer.",
                         "files": ["source/shared.py"]})
        save(entities)
        path = self.root / "specs/root/module.md"
        path.write_text(path.read_text().replace('    a["A"]', '    shared["Shared value"]\n    a["A"]')
                        .replace("    a -->|answers beside| b",
                                 "    a -->|answers beside| b\n    a -->|reads| shared"))
        self.registry["targets"][0]["files"] = ["source/shared.py"]
        self.save_registry()
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("success", report.status, [f.message for f in report.findings])
        repository = self.repository()
        # A's own bounded context is unchanged: the peer Spec is never imported by a file listing.
        recheck_context(repository, snapshot)
        self.assertNotIn("ROOT_MODULE_CONTRACT", snapshot.serialized)
        self.assertEqual(("module.root", "module.a", "module.b"),
                         tuple(t.id for t in repository.affected_modules(["source/shared.py"])))
        self.assertEqual(("module.root", "module.a", "module.b"),
                         tuple(t.id for t in _implementation_users(repository, repository.select("module.a"))))

    def test_pending_files_stay_valid_until_delivery_confirms_them(self):
        entities, save = self.entity_block("specs/a/module.md")
        entities[0]["files"] = ["source/a.py", "source/new.py"]
        entities[0]["pending"] = ["source/new.py"]
        save(entities)
        self.registry["targets"][1]["files"] = ["source/a.py", "source/new.py", "source/shared.py"]
        self.save_registry()
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("success", report.status, [f.message for f in report.findings])
        repository = self.repository()
        target = repository.select("module.a")
        self.assertIn("source/new.py", repository.implementation_paths(target))
        self.assertNotIn("source/new.py", repository.implementation_files(target))
        self.assertEqual(("source/new.py",), repository.missing_files(target))
        snapshot = resolve_context(repository, "module.a", phase="plan")
        self.assertEqual([("source/a.py", False), ("source/new.py", True), ("source/shared.py", False)],
            [(item["path"], item["pending"]) for item in snapshot.value["implementation_files"]])
        self.write("source/new.py", "def added():\n    return 1\n")
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("success", report.status)
        self.assertEqual({"CONCORDE-ENTITY-005"},
                         {f.rule_id for f in report.findings if f.severity == "warning"
                          and f.rule_id == "CONCORDE-ENTITY-005"})
        confirmed, still_pending = confirm_pending_files(self.root, PACKAGE)
        self.assertEqual([{"module": "module.a", "entity": "entity.a.adapter",
                           "path": "source/new.py"}], confirmed)
        self.assertEqual([], still_pending)
        self.assertNotIn("pending", (self.root / "specs/a/module.md").read_text())
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("success", report.status)
        self.assertEqual([], [f for f in report.findings if f.rule_id == "CONCORDE-ENTITY-005"])

    def test_a_missing_file_that_is_not_pending_is_an_error(self):
        entities, save = self.entity_block("specs/a/module.md")
        entities[0]["files"] = ["source/a.py", "source/new.py"]
        save(entities)
        self.registry["targets"][1]["files"] = ["source/a.py", "source/new.py", "source/shared.py"]
        self.save_registry()
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("invalid", report.status)
        self.assertIn("CONCORDE-ENTITY-002", {finding.rule_id for finding in report.findings})
        confirmed, still_pending = confirm_pending_files(self.root, PACKAGE)
        self.assertEqual(([], []), (confirmed, still_pending))

    def test_validation_runs_both_consumers_checks_and_surfaces_peer_failure(self):
        for target in self.registry["targets"][1:]:
            key = "check." + target["id"]
            target["checks"] = [key]
            expectation = "value() >= 0" if target["id"] == "module.a" else "value() == 42"
            self.registry["checks"].append({"id": key, "target_id": target["id"],
                "argv": ["{python}", "-c", "from source.shared import value; assert " + expectation],
                "timeout_seconds": 10})
        self.save_registry()
        def validate():
            repository = self.repository()
            run = SimpleNamespace(repository=repository, target=repository.select("module.a"),
                host=SimpleNamespace(coordinated=True, package_root=PACKAGE, invocation_id="test-impact"),
                work_directory=None, completed=[],
                response=lambda outcome="completed", answer="", **kwargs: {"outcome": outcome, **kwargs})
            return Invocation.validate(run)
        result = validate()
        self.assertEqual("completed", result["outcome"])
        self.assertEqual({"module.a", "module.b"}, {item["target_id"] for item in result["checks"]})
        self.write("source/shared.py", "def value():\n    return 43\n")
        result = validate()
        self.assertEqual("failed", result["outcome"])
        self.assertEqual({"module.b"}, {item["target_id"] for item in result["checks"] if item["status"] == "failed"})

    def test_check_cannot_change_a_using_module_contract_and_claim_fresh_evidence(self):
        self.registry["targets"][1]["checks"] = ["check.mutates-peer"]
        self.registry["checks"] = [{"id": "check.mutates-peer", "target_id": "module.a",
            "argv": ["{python}", "-c", "from pathlib import Path; p=Path('specs/b/module.md'); p.write_text(p.read_text()+'\\nChanged peer promise.')"],
            "timeout_seconds": 10}]
        self.save_registry()
        repository = self.repository()
        run = SimpleNamespace(repository=repository, target=repository.select("module.a"),
            host=SimpleNamespace(coordinated=True, package_root=PACKAGE, invocation_id="mutating-check"),
            work_directory=None, completed=[],
            response=lambda outcome="completed", answer="", **kwargs: {"outcome": outcome, **kwargs})
        with self.assertRaisesRegex(SpecError, "using Module"):
            Invocation.validate(run)

    def test_shared_code_review_preserves_separate_module_contexts_and_peer_findings(self):
        from concorde.development.capability_host import CapabilityHost
        from concorde.development.review import review_scope
        from tests.concorde.spec.support import ModelProcessDouble
        self.write("source/shared.py", "def value():\n    return 43\n")
        seen = []
        def inspect(stage, snapshot, result, cwd):
            if stage != "code-review":
                return
            seen.append(snapshot["target_id"])
            text = json.dumps(snapshot)
            self.assertNotIn("PRIVATE_SOURCE_MARKER", text)
            if snapshot["target_id"] == "module.a":
                self.assertNotIn("B_PRIVATE_SPEC", text)
            else:
                self.assertNotIn("A_OWN_ADDITIONAL_CONTRACT", text)
                self.assertIn("return 43", (cwd / "source/shared.py").read_text())
                result.update(status="findings", findings=[{"id": "finding.b.value", "severity": "blocking",
                    "target_id": "module.b", "document": "specs/b/module.md", "contract": "value() returns 42",
                    "location": {"path": "source/shared.py", "line": 2},
                    "problem": "The shared implementation returns 43.", "affected_task": snapshot["task"]}])
        double = ModelProcessDouble(inspect)
        self.addCleanup(double.runtime_directory.cleanup)
        host = CapabilityHost(self.root, PACKAGE, executor=double.executor, allow_primary_worktree=True,
                              invocation_id="shared-consumer-review")
        run = Invocation("concorde-review", self.configuration,
            {"target_id": "module.a", "task": "Review the shared value change", "review_mode": "code"}, host)
        result = review_scope(run, "code")["data"]
        self.assertEqual(["module.a", "module.b"], seen)
        self.assertEqual("conflicting", result["outcome"])
        self.assertEqual({"module.a", "module.b"}, {value["data"]["target_id"] for value in result["reviews"]})

    def test_code_writer_cannot_author_spec_documents(self):
        from concorde.development.capability_host import CapabilityHost, run_capability
        from concorde.spec.typed_data import typed
        from tests.concorde.spec.support import project, ModelProcessDouble
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project(root)
            def author(stage, snapshot, data, cwd):
                if stage == "implementation":
                    data["documents"] = [{"path": "specs/transfer/module.md",
                                          "content": "```concorde-document\n{}\n```\n"}]
            double = ModelProcessDouble(author)
            self.addCleanup(double.runtime_directory.cleanup)
            result = run_capability("concorde-dev-loop", self.configuration,
                typed("concorde-dev-loop-request", {"target_id": "service.transfer",
                    "task": "Implement transfer", "run_reviews": False}),
                host_context=CapabilityHost(root, PACKAGE, executor=double.executor,
                                            allow_primary_worktree=True))
            self.assertEqual("blocked", result["status"], result)
            self.assertEqual("child_blocked", result["errors"][0]["code"])
            self.assertIn("permission_denied", result["errors"][0]["message"])
            self.assertIn("cannot author Spec documents", result["errors"][0]["message"])
            # The refused proposal never reached the registered Spec document.
            self.assertIn("# Transfer money", (root / "specs/transfer/module.md").read_text())

    def test_composite_keeps_its_plan_and_verifies_shared_code_after_all_writers(self):
        from concorde.development.capability_host import CapabilityHost, run_capability
        from concorde.spec.typed_data import typed
        from tests.concorde.spec.support import project, ModelProcessDouble
        for shared, nested in ((False, False), (True, False), (False, True), (True, True)):
            with self.subTest(shared=shared, nested=nested), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                registry = project(root)
                bank, audit, transfer, ledger = registry["targets"]
                bank["uses"].remove("service.transfer")
                transfer["parent"] = "scope.bank"
                audit["uses"] = []
                if nested:
                    ledger["parent"] = "service.transfer"
                    bank["uses"].remove("module.ledger")
                else:
                    transfer["uses"] = []
                # Every declared collaborator and every entity that stands for a Module must match
                # the Module's actual children and dependencies after the topology is rearranged.
                keep = {"scope.audit", "service.transfer", *(() if nested else ("module.ledger",))}
                self.retain_dependencies(root / bank["documents"][0], keep)
                self.retain_dependencies(root / audit["documents"][0], set())
                self.retain_dependencies(root / transfer["documents"][0],
                                         {"module.ledger"} if nested else set())
                self.drop_entity(root / audit["documents"][0], "entity.audit.transfer")
                if nested:
                    self.drop_entity(root / bank["documents"][0], "entity.bank.ledger")
                else:
                    self.drop_entity(root / transfer["documents"][0], "entity.transfer.ledger")
                # Bank owns coordination code of its own, in a file the transfer Module may share.
                self.add_entity(root / bank["documents"][0], {"id": "entity.bank.result",
                    "title": "Bank result", "kind": "function",
                    "responsibility": "Computes the settled result through the private transfer Module.",
                    "files": ["app/bank.py"]}, "    request -->|computed by| result")
                bank["files"] = ["app/bank.py"]
                (root / "app/bank.py").write_text("from app.transfer import transfer\ndef result():\n    return 0\n")
                if shared:
                    self.add_entity(root / transfer["documents"][0], {"id": "entity.transfer.bank",
                        "title": "Bank result", "kind": "function",
                        "responsibility": "Calls the transfer calculation from the Banking Module.",
                        "files": ["app/bank.py"]}, "    calculation -->|called by| bank")
                    transfer["files"] = sorted([*transfer["files"], "app/bank.py"])
                bank["checks"] = ["check.bank"]
                registry["checks"].append({"id": "check.bank", "target_id": "scope.bank",
                    "argv": ["{python}", "-c", "from app.bank import result; assert result()==80"], "timeout_seconds": 10})
                (root / ".concorde/specs.json").write_text(json.dumps(registry))
                self.assertEqual("success", validate_repository(root, package_root=PACKAGE).status,
                    [f.message for f in validate_repository(root, package_root=PACKAGE).findings])
                coding_targets = []
                def implement(stage, snapshot, result, cwd):
                    if nested and stage == "tasks" and snapshot["target_id"] == "service.transfer":
                        result["tasks"].append({"id": "task.ledger-read", "target_id": "module.ledger",
                            "description": "Implement the private ledger read interface.",
                            "acceptance": "read returns an integer or raises KeyError.", "complete": False})
                    if stage == "tasks" and snapshot["target_id"] == "scope.bank":
                        result["tasks"].append({"id": "task.bank-result", "target_id": "scope.bank",
                            "description": "Implement the bank result interface.", "acceptance": "result() returns 80.", "complete": False})
                    if stage == "implementation":
                        coding_targets.append(snapshot["target_id"])
                        if snapshot["target_id"] == "scope.bank":
                            self.assertNotIn("TRANSFER_IMPLEMENTATION_CODE", json.dumps(snapshot))
                            self.assertEqual({"app/bank.py"}, {item["path"] for item in snapshot["implementation_artifacts"]})
                            (cwd / "app/bank.py").write_text("from app.transfer import transfer\ndef result():\n    return transfer(100,20)\n")
                double = ModelProcessDouble(implement)
                self.addCleanup(double.runtime_directory.cleanup)
                task = "Implement the bank result using its private transfer Module"
                result = run_capability("concorde-dev-loop", self.configuration,
                    typed("concorde-dev-loop-request", {"target_id": "scope.bank", "task": task}),
                    host_context=CapabilityHost(root, PACKAGE, executor=double.executor, allow_primary_worktree=True))
                self.assertEqual("succeeded", result["status"], result)
                self.assertEqual("ready", result["output"]["data"]["outcome"])
                self.assertEqual((["module.ledger"] if nested else []) + ["service.transfer", "scope.bank"], coding_targets)
                state = json.loads((root / ".concorde/worktree.json").read_text())["targets"]["scope.bank"]
                self.assertEqual(task, state["task"])
                self.assertEqual(2, len(state["tasks"]))
                self.assertNotIn("scope.bank", state["coordination"])
                self.assertTrue(all(item["complete"] for item in state["tasks"]))

    def retain_dependencies(self, path, keep):
        """Keep only the named collaborator declarations, or remove the block entirely."""
        import re
        content = path.read_text()
        match = re.search(r"^```concorde-dependencies\s*\n(.*?)^```\s*$", content, re.M | re.S)
        if match is None:
            self.assertFalse(keep, f"{path} has no collaborator declarations")
            return
        retained = [item for item in json.loads(match.group(1)) if item["target_id"] in keep]
        replacement = ("```concorde-dependencies\n" + json.dumps(retained, indent=2) + "\n```"
                       if retained else "")
        path.write_text(content[:match.start()] + replacement + content[match.end():])

    def drop_entity(self, path, entity_id):
        """Remove one local entity, its diagram node and every edge that referenced it."""
        content = path.read_text()
        prefix, rest = content.split("```concorde-entities\n", 1)
        payload, suffix = rest.split("\n```", 1)
        entities = [item for item in json.loads(payload) if item["id"] != entity_id]
        content = prefix + "```concorde-entities\n" + json.dumps(entities, indent=2) + "\n```" + suffix
        node = entity_id.split(".")[-1]
        marker = "```mermaid\n"
        start = content.index(marker) + len(marker)
        end = content.index("\n```", start)
        kept = [line for line in content[start:end].split("\n")
                if line.strip().startswith(("accTitle", "accDescr", "flowchart"))
                or not re.search(r"\b" + re.escape(node) + r"\b", line)]
        path.write_text(content[:start] + "\n".join(kept) + content[end:])

    def add_entity(self, path, entity, edge):
        """Declare one more local entity and give it a labeled node in the same diagram."""
        content = path.read_text()
        prefix, rest = content.split("```concorde-entities\n", 1)
        payload, suffix = rest.split("\n```", 1)
        entities = [*json.loads(payload), entity]
        content = prefix + "```concorde-entities\n" + json.dumps(entities, indent=2) + "\n```" + suffix
        node = "    " + entity["id"].split(".")[-1] + '["' + entity["title"] + '"]'
        # Insert the node and its labeled edge just before the closing mermaid fence.
        marker = "```mermaid\n"
        start = content.index(marker) + len(marker)
        end = content.index("\n```", start)
        content = content[:end] + "\n" + node + "\n" + edge + content[end:]
        path.write_text(content)


if __name__ == "__main__":
    unittest.main()
