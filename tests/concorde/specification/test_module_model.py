"""Behavioral regression tests for the Module/Implementation model, without model calls."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from concorde.host.capability_host import Invocation, _implementation_digest, _target_revision
from concorde.specification.context import resolve_context, recheck_context
from concorde.specification.repository import SpecError, SpecRepository, digest


PACKAGE = Path(__file__).resolve().parents[3]


class ModuleImplementationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.configuration = {"type_id": "concorde-capability-configuration", "schema_version": 1,
                              "data": {"integration": "claude", "enforcement": "native"}}
        manifest = (PACKAGE / "protocol/manifest.json").read_bytes()
        self.write(".concorde/config.json", json.dumps({"profile_version": 9,
            "registry": ".concorde/specs.json", "protocol": {
                "version": "2.0.0", "digest": digest(manifest)},
            "capability_configuration": self.configuration}))
        targets = []
        for name in ("root", "a", "b"):
            key = "module." + name
            path = f"specs/{name}/module.md"
            target = {"id": key, "kind": "module", "title": name, "documents": [path],
                "parent": None if name == "root" else "module.root", "uses": [],
                "implementations": [] if name == "root" else ["implementation.shared"],
                "features": [{"id": f"feature.{name}.value", "title": "Read value", "document": path}],
                "interfaces": [{"id": f"interface.{name}.value", "title": "value()", "document": path}],
                "checks": [], "diagrams": []}
            body = (f"# {name}\n\n## feature.{name}.value\nReturn the promised value.\n"
                    f"## interface.{name}.value\nvalue() returns an integer.\n\n## Architecture\n"
                    + ("B_PRIVATE_SPEC" if name == "b" else name.upper() + "_MODULE_CONTRACT"))
            if name == "root":
                body += "\n```concorde-dependencies\n" + json.dumps([{
                    "target_id": "module." + peer, "responsibility": "Return its value.",
                    "selection_condition": "Select for " + peer, "relied_upon_promises": ["value returns an integer."]}
                    for peer in ("a", "b")]) + "\n```\n"
            self.document(path, key, body)
            targets.append(target)
        targets[1]["documents"].append("specs/a/details.md")
        self.document("specs/a/details.md", "module.a", "# Local details\nA_OWN_ADDITIONAL_CONTRACT")
        targets[1]["implementations"].append("implementation.only-a")
        self.document("specs/implementations/shared.md", "implementation.shared",
                      "# Shared implementation\nIMPLEMENTATION_SECRET_SHARED")
        self.document("specs/implementations/a.md", "implementation.only-a",
                      "# A implementation\nIMPLEMENTATION_SECRET_A")
        self.write("source/shared.py", "def value():\n    return 42\n# PRIVATE_SOURCE_MARKER\n")
        self.write("source/a.py", "def adapt(value):\n    return value\n")
        self.registry = {"schema_version": 2, "project_id": "project.test", "entry_target": "module.root",
            "targets": targets, "implementations": [
                {"id": "implementation.shared", "title": "Shared implementation",
                 "documents": ["specs/implementations/shared.md"], "files": ["source/shared.py"]},
                {"id": "implementation.only-a", "title": "A implementation",
                 "documents": ["specs/implementations/a.md"], "files": ["source/a.py"]}], "checks": []}
        self.save_registry()

    def write(self, path, content):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content)

    def document(self, path, owner, content):
        declaration = {"id": "document." + path.replace("/", ".").removesuffix(".md"),
                       "targets": [owner], "main_visible": not owner.startswith("implementation.")}
        self.write(path, "```concorde-document\n" + json.dumps(declaration) + "\n```\n\n" + content)

    def save_registry(self):
        self.write(".concorde/specs.json", json.dumps(self.registry))

    def repository(self):
        return SpecRepository(self.root, PACKAGE)

    def test_non_code_agents_receive_the_whole_module_and_no_implementation(self):
        for phase in ("ask", "specify", "plan", "tasks", "context-solve", "spec-review"):
            with self.subTest(phase=phase):
                snapshot = resolve_context(self.repository(), "module.a", phase=phase,
                                           focus_id="feature.a.value")
                self.assertIn("A_MODULE_CONTRACT", snapshot.serialized)
                self.assertIn("A_OWN_ADDITIONAL_CONTRACT", snapshot.serialized)
                self.assertNotIn("B_PRIVATE_SPEC", snapshot.serialized)
                self.assertNotIn("IMPLEMENTATION_SECRET", snapshot.serialized)
                self.assertNotIn("source/shared.py", snapshot.serialized)
                self.assertEqual([], snapshot.value["implementation_specs"])
                self.assertEqual([], snapshot.value["implementation_artifacts"])

    def test_only_code_writing_appends_implementation_specs_and_exact_files(self):
        snapshot = resolve_context(self.repository(), "module.a", phase="implementation")
        self.assertIn("IMPLEMENTATION_SECRET_SHARED", snapshot.serialized)
        self.assertIn("IMPLEMENTATION_SECRET_A", snapshot.serialized)
        self.assertNotIn("B_PRIVATE_SPEC", snapshot.serialized)
        self.assertNotIn("PRIVATE_SOURCE_MARKER", snapshot.serialized)
        self.assertEqual({"source/shared.py", "source/a.py"},
                         {item["path"] for item in snapshot.value["implementation_artifacts"]})
        review = resolve_context(self.repository(), "module.a", phase="code-review")
        self.assertEqual([], review.value["implementation_specs"])
        self.assertTrue(review.value["implementation_artifacts"])

    def test_shared_implementation_has_one_identity_and_all_users(self):
        repository = self.repository()
        self.assertEqual(("module.a", "module.b"), repository.implementation_users["implementation.shared"])
        self.assertEqual("implementation.shared", repository.file_implementations["source/shared.py"])
        self.assertEqual(("module.a", "module.b"), tuple(t.id for t in repository.affected_modules(["source/shared.py"])))
        self.assertEqual(("module.a", "module.b"), tuple(t.id for t in repository.affected_modules(["specs/implementations/shared.md"])))
        self.assertEqual(("module.a",), tuple(t.id for t in repository.affected_modules(["source/a.py"])))

    def test_two_specs_cannot_own_the_same_file(self):
        self.registry["implementations"][1]["files"] = ["source/shared.py"]
        self.save_registry()
        with self.assertRaisesRegex(SpecError, "multiple owners"):
            self.repository()

    def test_directory_is_not_an_implementation_binding(self):
        self.registry["implementations"][0]["files"] = ["source"]
        self.save_registry()
        with self.assertRaisesRegex(SpecError, "explicit files"):
            self.repository()

    def test_implementation_document_cannot_leak_through_module_membership(self):
        self.registry["targets"][1]["documents"].append("specs/implementations/shared.md")
        self.save_registry()
        with self.assertRaisesRegex(SpecError, "cannot be Module context"):
            self.repository()

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

    def test_implementation_only_change_invalidates_writers_not_planner_context(self):
        repository = self.repository()
        planned = resolve_context(repository, "module.a", phase="plan")
        coding = resolve_context(repository, "module.a", phase="implementation")
        self.document("specs/implementations/shared.md", "implementation.shared", "# Revised implementation\nNew internal constraints.")
        recheck_context(repository, planned)
        with self.assertRaisesRegex(SpecError, "Implementation Spec"):
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

    def test_new_shared_user_invalidates_code_context_without_importing_its_spec(self):
        snapshot = resolve_context(self.repository(), "module.a", phase="implementation")
        self.registry["targets"][0]["implementations"] = ["implementation.shared"]
        self.save_registry()
        with self.assertRaisesRegex(SpecError, "using Modules"):
            recheck_context(self.repository(), snapshot)

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

    def test_new_implementation_binding_gets_an_honest_private_stub(self):
        from concorde.host.capability_host import _implementation_document_proposals
        repository = self.repository()
        self.registry["implementations"].append({"id": "implementation.new", "title": "New realization",
            "documents": ["specs/implementations/new.md"], "files": ["source/new.py"]})
        self.registry["targets"][1]["implementations"].append("implementation.new")
        proposed = _implementation_document_proposals(repository, self.registry)
        self.assertEqual({"specs/implementations/new.md"}, set(proposed))
        self.assertIn("not yet been authored", proposed["specs/implementations/new.md"])
        self.assertIn("source/new.py", proposed["specs/implementations/new.md"])
        self.write("specs/implementations/new.md", proposed["specs/implementations/new.md"])
        self.save_registry()
        repository = self.repository()
        planned = resolve_context(repository, "module.a", phase="plan")
        coding = resolve_context(repository, "module.a", phase="implementation")
        self.assertNotIn("New realization", planned.serialized)
        self.assertIn("New realization", coding.serialized)
        self.assertIn("source/new.py", repository.implementation_paths(repository.select("module.a")))
        self.assertNotIn("source/new.py", repository.implementation_files(repository.select("module.a")))

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
        from concorde.host.capability_host import CapabilityHost
        from concorde.host.review import review_scope
        from tests.concorde.specification.support import ModelProcessDouble
        self.write("source/shared.py", "def value():\n    return 43\n")
        self.document("specs/b/module.md", "module.b", "# B\n## feature.b.value\nReturn 42.\n"
            "## interface.b.value\nvalue() must return 42.\n## Architecture\nB_PRIVATE_SPEC")
        seen = []
        def inspect(stage, snapshot, result, cwd):
            if stage != "code-review":
                return
            seen.append(snapshot["target_id"])
            self.assertEqual([], snapshot["implementation_specs"])
            text = json.dumps(snapshot)
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

    def test_composite_keeps_its_plan_and_verifies_shared_code_after_all_writers(self):
        import re
        from concorde.host.capability_host import CapabilityHost, run_capability
        from concorde.host.typed_data import typed
        from tests.concorde.specification.support import project, ModelProcessDouble
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
                    path = root / bank["documents"][0]
                    content = path.read_text()
                    block = re.search(r"^```concorde-dependencies\s*\n(.*?)^```\s*$", content, re.M | re.S)
                    dependencies = [item for item in json.loads(block.group(1)) if item["target_id"] != "module.ledger"]
                    path.write_text(content[:block.start()] + "```concorde-dependencies\n" + json.dumps(dependencies) + "\n```\n")
                else:
                    transfer["uses"] = []
                for target in ((audit,) if nested else (audit, transfer)):
                    path = root / target["documents"][0]
                    content = re.sub(r"^```concorde-dependencies\s*\n.*?^```\s*$", "", path.read_text(), flags=re.M | re.S)
                    path.write_text(content)
                bank["features"] = [{"id": "feature.bank.result", "title": "Compute result", "document": bank["documents"][0]}]
                bank["interfaces"] = [{"id": "interface.bank.result", "title": "result()", "document": bank["documents"][0]}]
                path = root / bank["documents"][0]
                path.write_text(path.read_text() + "\n## feature.bank.result\nCompute transfer(100, 20).\n"
                    "## interface.bank.result\nresult() returns 80 through the private transfer Module.\n")
                bank["implementations"] = ["implementation.bank"]
                implementation_path = "specs/implementations/bank.md"
                (root / implementation_path).write_text("```concorde-document\n" + json.dumps({
                    "id": "document.implementation.bank", "targets": ["implementation.bank"], "main_visible": False})
                    + "\n```\n\n# Bank code\napp/bank.py implements result() using app.transfer.transfer.\n")
                (root / "app/bank.py").write_text("from app.transfer import transfer\ndef result():\n    return 0\n")
                registry["implementations"].append({"id": "implementation.bank", "title": "Bank code",
                    "documents": [implementation_path], "files": ["app/bank.py"]})
                if shared:
                    transfer["implementations"].append("implementation.bank")
                bank["checks"] = ["check.bank"]
                registry["checks"].append({"id": "check.bank", "target_id": "scope.bank",
                    "argv": ["{python}", "-c", "from app.bank import result; assert result()==80"], "timeout_seconds": 10})
                (root / ".concorde/specs.json").write_text(json.dumps(registry))
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
                            self.assertNotIn("INTERNAL_TRANSFER_IMPLEMENTATION_SPEC", json.dumps(snapshot))
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

    def test_peer_review_failure_does_not_repair_against_the_wrong_module_context(self):
        from concorde.host.capability_host import CapabilityHost, run_capability
        from concorde.host.typed_data import typed
        from tests.concorde.specification.support import project, ModelProcessDouble
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = project(root)
            registry["targets"][1]["implementations"] = ["implementation.transfer"]
            (root / ".concorde/specs.json").write_text(json.dumps(registry))
            def review_peer(stage, snapshot, result, cwd):
                if stage == "code-review" and snapshot["target_id"] == "scope.audit":
                    result.update(status="findings", findings=[{"id": "finding.audit.compatibility", "severity": "blocking",
                        "target_id": "scope.audit", "document": "specs/audit/module.md", "contract": "Audit completion promise",
                        "location": {"path": "app/transfer.py", "line": 2}, "problem": "The shared result violates the audit contract.",
                        "affected_task": snapshot["task"]}])
            double = ModelProcessDouble(review_peer)
            self.addCleanup(double.runtime_directory.cleanup)
            result = run_capability("concorde-dev-loop", self.configuration,
                typed("concorde-dev-loop-request", {"target_id": "service.transfer", "task": "Refactor transfer"}),
                host_context=CapabilityHost(root, PACKAGE, executor=double.executor, allow_primary_worktree=True))
            self.assertEqual("blocked", result["status"], result)
            self.assertEqual("conflicting", result["output"]["data"]["outcome"])
            reviews = [index for index, call in enumerate(double.calls) if call["stage"] == "code-review"]
            self.assertTrue(reviews)
            self.assertFalse(any(call["stage"] == "tasks" for call in double.calls[min(reviews):]))


if __name__ == "__main__":
    unittest.main()
