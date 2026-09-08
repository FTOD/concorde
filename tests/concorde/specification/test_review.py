"""Review mechanism tests. Process doubles do not measure semantic detection quality."""
import json
import subprocess
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch

from concorde.host.change_worktree import ensure_change, read_change, save_change
from concorde.host.typed_data import DATA_SCHEMAS, typed
from concorde.host.capability_service import CapabilityHost, run_capability
from concorde.host.capability_host import Invocation
from concorde.host.review import current, inputs
from .support import CONFIGURATION, PACKAGE, ModelProcessDouble, project, update_document_declaration


class ReviewTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.registry = project(self.root)
        self.configuration = CONFIGURATION
        self.task = {"target_id": "service.transfer", "task": "Implement the pure transfer contract"}

    def double(self, callback=None):
        double = ModelProcessDouble(callback)
        self.addCleanup(double.runtime_directory.cleanup)
        return double

    def run_op(self, operation, data=None, callback=None, *, mode="execute", double=None):
        self.model = double or self.double(callback)
        self.host = CapabilityHost(self.root, PACKAGE, executor=self.model.executor,
            allow_primary_worktree=True, mode=mode, routed_target=(data or self.task)["target_id"])
        return run_capability(operation, self.configuration, typed(operation + "-request", data or self.task),
                             host_context=self.host)

    def review(self, review_mode="spec", callback=None, **kwargs):
        return self.run_op("concorde-review", {**self.task, "review_mode": review_mode}, callback, **kwargs)

    def invocation(self):
        return Invocation("concorde-review", self.configuration, self.task,
            CapabilityHost(self.root, PACKAGE, routed_target=self.task["target_id"]))

    def commit_fixture(self):
        for args in [("init",), ("add", "."), ("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                "commit", "-m", "Fixture baseline")]:
            subprocess.run(("git", *args), cwd=self.root, capture_output=True, check=True)

    @staticmethod
    def gap():
        return {"question": "Who owns the necessary daily limit?", "blocked_step": "Decide daily-limit admission",
                "needed_contract": "The transfer daily-limit owner and admission rule"}

    def missing(self, phase):
        def callback(stage, snapshot, data, cwd):
            if stage != phase:
                return
            if phase.endswith("review"):
                data.update(status="findings", gaps=[self.gap()], findings=[{
                    "id": "missing-limit", "severity": "blocking", "target_id": snapshot["target_id"],
                    "document": "specs/send-money.md", "contract": self.gap()["needed_contract"],
                    "location": {"path": "specs/send-money.md", "line": 12},
                    "problem": "A required daily-limit promise is absent.",
                    "affected_task": self.gap()["blocked_step"]}])
            else:
                data.update(outcome="spec_incomplete", gaps=[self.gap()])
        return callback

    def test_modes_use_full_collection_fresh_sessions_and_no_write_grants(self):
        self.registry["targets"][3]["documents"].append("specs/transfer-promises.md")
        (self.root / ".concorde/specs.json").write_text(json.dumps(self.registry))
        update_document_declaration(self.root, "specs/transfer-promises.md",
            targets=["service.transfer", "module.ledger"])
        calls, identities = [], []
        for mode in ("code", "spec"):
            result = self.review(mode)
            self.assertEqual("succeeded", result["status"], result)
            calls.append(self.model.calls[0])
            identities.append(self.host.evidence[0].completion.invocation_id)
            policy = self.host.descriptions[0]
            self.assertEqual([], policy["write_paths"])
            self.assertFalse(policy["network"])
            self.assertTrue(policy["fresh_session"])
            snapshot = calls[-1]["snapshot"]
            self.assertEqual(["specs/send-money.md", "specs/transfer-promises.md"], snapshot["document_order"])
            self.assertEqual(["specs/transfer-promises.md"], [x["path"] for x in snapshot["shared_specs"]])
            self.assertNotIn("# Ledger API", calls[-1]["prompt"])
            self.assertNotIn("PRIVATE_CODE", calls[-1]["prompt"])
            if mode == "code":
                self.assertEqual(self.root, calls[-1]["cwd"])
                self.assertIn("app/transfer.py", policy["read_paths"])
                self.assertNotIn("app/ledger.py", policy["read_paths"])
                self.assertNotIn("app", policy["read_paths"])
                self.assertIn("def transfer", calls[-1]["prompt"])
            else:
                self.assertNotEqual(self.root, calls[-1]["cwd"])
                self.assertEqual(["context.json"], policy["read_paths"])
                self.assertEqual([], snapshot["implementation_artifacts"])
                self.assertNotIn("def transfer", calls[-1]["prompt"])
                self.assertNotIn("app/transfer.py", calls[-1]["prompt"])
        self.assertEqual(2, len(set(identities)))

    def test_diff_admits_only_current_target_paths_and_includes_untracked_and_deleted(self):
        self.commit_fixture()
        (self.root / "app/transfer.py").write_text("CHANGED_LOCAL_CODE\n")
        (self.root / "app/ledger.py").write_text("UNGRANTED_OTHER_CODE\n")
        (self.root / "checks/transfer_check.py").unlink()
        result = self.review("code")
        self.assertEqual("succeeded", result["status"], result)
        patches = self.model.calls[0]["review"]["changes"]
        self.assertEqual({"app/transfer.py", "checks/transfer_check.py"}, {x["path"] for x in patches})
        self.assertNotIn("UNGRANTED_OTHER_CODE", json.dumps(patches))
        self.assertIn("/dev/null", patches[1]["patch"])
        self.assertNotIn("CHANGED_LOCAL_CODE", json.dumps(result))
        (self.root / "checks/transfer_check.py").write_text("NEW_LOCAL_CHECK\n")
        subprocess.run(("git", "rm", "--cached", "checks/transfer_check.py"), cwd=self.root, capture_output=True, check=True)
        result = self.review("code")
        self.assertEqual("succeeded", result["status"], result)
        self.assertIn("NEW_LOCAL_CHECK", json.dumps(self.model.calls[0]["review"]["changes"]))

    def test_describe_policy_is_not_a_completed_review(self):
        for mode in ("spec", "code"):
            result = self.review(mode, mode="describe-policy")
            self.assertEqual("described", result["status"])
            self.assertEqual("not_run", result["output"]["data"]["reviews"][0]["data"]["status"])
            self.assertEqual([], self.model.calls)
        self.assertFalse((self.root / ".concorde/runs").exists())

    def test_failed_policy_preview_does_not_persist_artifacts_or_change_state(self):
        self.configuration = typed("concorde-capability-configuration", {"integration": "claude", "enforcement": "outer"})
        path = self.root / ".concorde/config.json"
        config = json.loads(path.read_text())
        config["capability_configuration"] = self.configuration
        path.write_text(json.dumps(config))
        ensure_change(self.root, task=self.task, allow_primary=True)
        before = read_change(self.root)
        for mode in ("spec", "code"):
            result = self.review(mode, mode="describe-policy")
            self.assertNotEqual("described", result["status"], result)
            self.assertEqual([], self.model.calls)
            self.assertEqual(before, read_change(self.root))
            self.assertFalse((self.root / ".concorde/runs").exists())

    def test_result_validation_rejects_false_clean_cross_scope_and_replayed_identity(self):
        mutations = [
            lambda d: d.update(input_digest="sha256:" + "0" * 64),
            lambda d: d.update(review_mode="code"),
            lambda d: d.update(representative_tasks=[]),
            lambda d: d.update(representative_tasks=[" "]),
            lambda d: d.update(representative_tasks=["same", "same"]),
            lambda d: d.update(gaps=[self.gap()]),
            lambda d: d.update(documents=[{"path": "specs/send-money.md", "content": "replacement"}]),
        ]
        original = (self.root / "specs/send-money.md").read_bytes()
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                def callback(stage, snapshot, data, cwd):
                    mutate(data)
                result = self.review(callback=callback)
                self.assertEqual("failed", result["status"], result)
                self.assertEqual("incomplete", result["output"]["data"]["reviews"][0]["data"]["status"])
        self.assertEqual(original, (self.root / "specs/send-money.md").read_bytes())
        def foreign(stage, snapshot, data, cwd):
            self.missing("spec-review")(stage, snapshot, data, cwd)
            data["findings"][0]["document"] = "specs/ledger-api.md"
        result = self.review(callback=foreign)
        self.assertEqual("failed", result["status"])
        self.assertIn("permission_denied", result["output"]["data"]["answer"])

    def test_execution_failure_and_incomplete_coverage_are_not_no_findings(self):
        def fail(stage, snapshot, data, cwd):
            raise RuntimeError("private process failure diagnostics")
        for callback in (fail, lambda stage, snapshot, data, cwd: data.update(status="incomplete", representative_tasks=[])):
            result = self.review(callback=callback)
            self.assertEqual("failed", result["status"], result)
            self.assertEqual("incomplete", result["output"]["data"]["reviews"][0]["data"]["status"])
            self.assertNotIn("private process failure diagnostics", json.dumps(result))

    def test_failed_reviews_retain_available_native_attestation_privately(self):
        from concorde.host.agent_executor import CapabilityExecutionError
        double = self.double()
        executor = double.executor
        captured = []
        def fail(launch):
            executed = executor(launch)
            receipt = replace(executed.receipt, status="failed", exit_code=17, completion_status="failed")
            captured.append(receipt)
            raise CapabilityExecutionError("private failed completion diagnostics", receipt)
        double.executor = fail
        failed = self.review(double=double)
        self.assertEqual("failed", failed["status"], failed)
        def private(result):
            path = self.root / result["output"]["data"]["artifacts"][0]["path"]
            return json.loads(path.with_suffix(".execution.json").read_text())
        self.assertEqual(asdict(captured[0]), private(failed)["receipt"])
        self.assertIsNone(private(failed)["execution"])
        rejected = self.review(callback=lambda stage, snapshot, data, cwd:
            data.update(input_digest="sha256:" + "0" * 64))
        self.assertEqual("failed", rejected["status"], rejected)
        self.assertEqual("success", private(rejected)["execution"]["receipt"]["status"])
        for result in (failed, rejected):
            self.assertNotIn("private failed completion diagnostics", json.dumps(result))
            self.assertNotIn("client_version", json.dumps(result))

    def test_spec_query_returns_gaps_without_creating_a_change_or_reflection(self):
        before = {p.relative_to(self.root).as_posix(): p.read_bytes()
                  for p in (self.root / ".concorde/reflections").rglob("*") if p.is_file()}
        result = self.review(callback=self.missing("spec-review"))
        self.assertEqual("blocked", result["status"])
        gap = result["output"]["data"]["gaps"][0]
        self.assertEqual(self.task["target_id"], gap["target_id"])
        self.assertEqual(result["output"]["data"]["context_id"], gap["context_id"])
        self.assertIsNone(read_change(self.root))
        after = {p.relative_to(self.root).as_posix(): p.read_bytes()
                 for p in (self.root / ".concorde/reflections").rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_input_change_during_review_invalidates_the_completion(self):
        def change(stage, snapshot, data, cwd):
            path = self.root / "specs/send-money.md"
            path.write_text(path.read_text() + "\nChanged during review.\n")
        result = self.review(callback=change)
        self.assertEqual("failed", result["status"])
        self.assertIn("stale_context", result["output"]["data"]["answer"])
        def code_change(stage, snapshot, data, cwd):
            (self.root / "app/transfer.py").write_text("Modified by a deliberately invalid process double\n")
        result = self.review("code", callback=code_change)
        self.assertEqual("failed", result["status"])
        self.assertIn("stale_context", result["output"]["data"]["answer"])

    def test_required_reviews_surround_planning_and_follow_checks_before_ready(self):
        observed = []
        def inspect(stage, snapshot, data, cwd):
            if stage == "code-review":
                state = read_change(self.root)
                observed.append(state["status"])
                self.assertEqual("passed", state["targets"][self.task["target_id"]]["checks"][0]["status"])
        result = self.run_op("concorde-dev-loop", callback=inspect)
        self.assertEqual("succeeded", result["status"], result)
        stages = [x["stage"] for x in self.model.calls]
        self.assertLess(stages.index("specify"), stages.index("spec-review"))
        self.assertLess(stages.index("spec-review"), stages.index("plan"))
        self.assertLess(stages.index("implementation"), stages.index("code-review"))
        self.assertNotIn("ready", observed)
        self.assertEqual("ready", read_change(self.root)["status"])
        self.assertIsNotNone(current(self.invocation(), "spec"))
        self.assertIsNotNone(current(self.invocation(), "code"))

    def test_review_freshness_covers_spec_code_intent_and_artifact_integrity(self):
        self.assertEqual("succeeded", self.run_op("concorde-dev-loop")["status"])
        (self.root / "app/ledger.py").write_text("Unrelated implementation\n")
        self.assertIsNotNone(current(self.invocation(), "spec"))
        self.assertIsNotNone(current(self.invocation(), "code"))
        code = self.root / "app/transfer.py"
        code.write_text(code.read_text() + "\n# changed reviewed code\n")
        self.assertIsNotNone(current(self.invocation(), "spec"))
        self.assertIsNone(current(self.invocation(), "code"))
        state = read_change(self.root)
        reference = state["reviews"][self.task["target_id"]]["spec"]["artifact"]
        path = self.root / reference["path"]
        before = path.read_text()
        value = json.loads(before)
        value["data"]["answer"] = "tampered"
        path.write_text(json.dumps(value))
        self.assertIsNone(current(self.invocation(), "spec"))
        path.write_text(before)
        invocation = self.invocation()
        invocation.task = {**self.task, "constraints": ["Changed assessment constraint"]}
        self.assertIsNone(current(invocation, "spec"))
        spec = self.root / "specs/send-money.md"
        spec.write_text(spec.read_text() + "\nChanged contract.\n")
        self.assertIsNone(current(self.invocation(), "spec"))

    def test_gap_persists_deduplicates_and_requires_spec_repair_before_resume(self):
        result = self.run_op("concorde-dev-loop", callback=self.missing("spec-review"))
        self.assertEqual("blocked", result["status"], result)
        self.assertNotIn("plan", [x["stage"] for x in self.model.calls])
        before = read_change(self.root)
        self.assertEqual(1, len(before["gap_history"]))
        retry = self.run_op("concorde-dev-loop")
        self.assertEqual("blocked", retry["status"], retry)
        self.assertEqual(1, len(read_change(self.root)["gap_history"]))
        self.assertEqual(1, len(read_change(self.root)["gaps"]))
        self.assertEqual(before["gaps"][0]["context_id"], retry["output"]["data"]["gaps"][0]["context_id"])
        self.assertNotIn("plan", [x["stage"] for x in self.model.calls])
        spec = self.root / "specs/send-money.md"
        spec.write_text(spec.read_text() + "\nThe transfer capability owns a daily limit of 1000 units.\n")
        resumed = self.run_op("concorde-dev-loop")
        self.assertEqual("succeeded", resumed["status"], resumed)
        state = read_change(self.root)
        self.assertEqual([], state["gaps"])
        self.assertEqual("resolved", state["gap_history"][0]["status"])
        self.assertEqual("ready", state["status"])
        self.assertNotIn("specify", [x["stage"] for x in self.model.calls])

    def test_real_task_phases_preserve_gaps_and_resume_after_repair(self):
        for phase in ("context-solve", "plan", "tasks", "implementation"):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as temporary:
                original_root = self.root
                self.root = Path(temporary)
                project(self.root)
                result = self.run_op("concorde-dev-loop", callback=self.missing(phase))
                self.assertEqual("blocked", result["status"], result)
                self.assertEqual(phase, read_change(self.root)["gap_history"][0]["phase"])
                spec = self.root / "specs/send-money.md"
                spec.write_text(spec.read_text() + "\nThe transfer capability owns the necessary daily limit.\n")
                resumed = self.run_op("concorde-dev-loop")
                self.assertEqual("succeeded", resumed["status"], resumed)
                self.assertEqual([], read_change(self.root)["gaps"])
                self.root = original_root

    def test_fast_loop_records_skips_and_cannot_downgrade_required_review(self):
        result = self.run_op("concorde-dev-loop", {**self.task, "specify": False, "run_reviews": False})
        self.assertEqual("succeeded", result["status"], result)
        state = read_change(self.root)
        self.assertEqual({"skipped"}, {x["status"] for x in state["reviews"][self.task["target_id"]].values()})
        self.assertIn("spec=skipped", result["output"]["data"]["answer"])
        self.assertIn("code=skipped", result["output"]["data"]["answer"])
        self.assertEqual(2, len(result["output"]["data"]["artifacts"]))
        self.assertFalse(any("review" in x["stage"] for x in self.model.calls))
        result = self.run_op("concorde-dev-loop", {**self.task, "specify": False, "run_reviews": True}, callback=self.missing("spec-review"))
        self.assertEqual("blocked", result["status"], result)
        retried = self.run_op("concorde-dev-loop", {**self.task, "specify": False, "run_reviews": False})
        self.assertEqual("blocked", retried["status"], retried)
        self.assertTrue(read_change(self.root)["review_requirements"][self.task["target_id"]]["spec"])

    def test_advisory_findings_do_not_block_but_required_incomplete_review_does(self):
        def advisory(stage, snapshot, data, cwd):
            if stage == "code-review":
                data.update(status="findings", findings=[{"id": "clarity", "severity": "advisory",
                    "target_id": "service.transfer", "document": "specs/send-money.md", "contract": "Pure transfer",
                    "location": {"path": "app/transfer.py", "line": 1}, "problem": "An example could be clearer.",
                    "affected_task": "Read the implementation"}])
        self.assertEqual("succeeded", self.run_op("concorde-dev-loop", callback=advisory)["status"])
        state = read_change(self.root)
        state["reviews"][self.task["target_id"]].pop("code")
        save_change(self.root, state)
        def incomplete(stage, snapshot, data, cwd):
            if stage == "code-review":
                data.update(status="incomplete", answer="Required review could not complete.")
        result = self.run_op("concorde-dev-loop", {**self.task, "specify": False, "run_reviews": False}, callback=incomplete)
        self.assertEqual("failed", result["status"], result)
        self.assertNotEqual("ready", read_change(self.root)["status"])
        self.assertIsNone(read_change(self.root)["validated_tree"])

    def test_codex_generation_schema_is_strict_without_weakening_wire_validation(self):
        config_path = self.root / ".concorde/config.json"
        config = json.loads(config_path.read_text())
        self.configuration = typed("concorde-capability-configuration", {"integration": "codex", "enforcement": "native"})
        config["capability_configuration"] = self.configuration
        config_path.write_text(json.dumps(config))
        double = self.double()
        captured = []
        def runner(argv, **kwargs):
            captured.append(json.loads(Path(argv[argv.index("--output-schema") + 1]).read_text()))
            return double.run(argv, **kwargs)
        double.executor = replace(double.executor, runner=runner)
        result = self.review(double=double)
        self.assertEqual("succeeded", result["status"], result)
        def inspect(value):
            if isinstance(value, dict):
                self.assertNotIn("uniqueItems", value)
                if "properties" in value:
                    self.assertEqual(set(value["properties"]), set(value["required"]))
                if "const" in value or "enum" in value:
                    self.assertIn("type", value)
                for child in value.values():
                    inspect(child)
            elif isinstance(value, list):
                for child in value:
                    inspect(child)
        inspect(captured[0])
        wire = DATA_SCHEMAS["concorde-review-stage-result"]["properties"]
        self.assertTrue(wire["representative_tasks"]["uniqueItems"])
        self.assertNotIn("context_id", wire["gaps"]["items"]["required"])

    def test_unrelated_review_query_cannot_replace_required_lifecycle_evidence(self):
        self.assertEqual("succeeded", self.run_op("concorde-dev-loop")["status"])
        before = read_change(self.root)
        result = self.run_op("concorde-review", {**self.task, "task": "Inspect a separate possible use",
            "review_mode": "spec"}, callback=self.missing("spec-review"))
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual(before, read_change(self.root))
        self.assertIsNotNone(current(self.invocation(), "spec"))

    def test_standalone_dependent_steps_cannot_bypass_a_failed_required_spec_review(self):
        self.assertEqual("succeeded", self.run_op("concorde-dev-loop")["status"])
        blocked = self.review(callback=self.missing("spec-review"))
        self.assertEqual("blocked", blocked["status"], blocked)
        tasks = read_change(self.root)["targets"][self.task["target_id"]]["tasks"]
        for operation in ("concorde-tasks", "concorde-implement"):
            result = self.run_op(operation)
            self.assertEqual("blocked", result["status"], result)
            self.assertEqual("review_required", result["errors"][0]["code"])
            self.assertEqual([], self.model.calls)
            self.assertEqual(tasks, read_change(self.root)["targets"][self.task["target_id"]]["tasks"])

    def test_upstream_task_gaps_block_standalone_dependents_but_allow_independent_queries(self):
        for phase in ("context-solve", "plan"):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                previous_root = self.root
                self.root = Path(directory)
                try:
                    project(self.root)
                    self.assertEqual("succeeded", self.run_op("concorde-dev-loop")["status"])
                    self.assertEqual("blocked", self.run_op("concorde-plan", callback=self.missing(phase))["status"])
                    gap = read_change(self.root)["gaps"][0]
                    for operation in ("concorde-tasks", "concorde-implement"):
                        result = self.run_op(operation)
                        self.assertEqual("blocked", result["status"], result)
                        self.assertEqual([gap], result["output"]["data"]["gaps"])
                        self.assertEqual([], self.model.calls)
                    self.assertEqual("succeeded", self.run_op("concorde-context-solve")["status"])
                    self.assertEqual("open", read_change(self.root)["gap_history"][0]["status"])
                    spec = self.root / "specs/send-money.md"
                    spec.write_text(spec.read_text() + "\nThe daily-limit owner is transfer.\n")
                    self.assertEqual("succeeded", self.run_op("concorde-dev-loop")["status"])
                    self.assertEqual("resolved", read_change(self.root)["gap_history"][0]["status"])
                finally:
                    self.root = previous_root

    def test_review_binds_actual_worktree_even_with_identical_unversioned_bytes(self):
        original = inputs(self.invocation(), "spec")[0]["input_digest"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project(root)
            peer = Invocation("concorde-review", self.configuration, self.task, CapabilityHost(root, PACKAGE))
            self.assertNotEqual(original, inputs(peer, "spec")[0]["input_digest"])
        rejected = self.run_op("concorde-review", {**self.task, "review_mode": "spec", "change_id": "change.foreign"})
        self.assertEqual("incompatible_handoff", rejected["errors"][0]["code"])
        self.assertEqual([], self.model.calls)

    def test_domain_review_aggregates_only_separate_recorded_component_contexts(self):
        task = {"target_id": "scope.bank", "task": "Implement the transfer and ledger promises"}
        def components(stage, snapshot, data, cwd):
            if stage == "tasks" and snapshot["kind"] == "domain":
                data["tasks"].append({"id": "task.ledger", "target_id": "module.ledger",
                    "description": "Implement the ledger read promise.", "acceptance": "Read known balances and reject unknown accounts.",
                    "complete": False})
        result = self.run_op("concorde-dev-loop", task, callback=components)
        self.assertEqual("succeeded", result["status"], result)
        references = {ref["id"] for ref in result["output"]["data"]["artifacts"]}
        self.assertIn("review.module.ledger.code", references)
        self.assertIn("review.service.transfer.code", references)
        result = self.run_op("concorde-review", {**task, "review_mode": "code"})
        self.assertEqual("succeeded", result["status"], result)
        reviews = result["output"]["data"]["reviews"]
        self.assertEqual({"service.transfer", "module.ledger"}, {x["data"]["target_id"] for x in reviews})
        self.assertEqual(["code-review", "code-review"], [x["stage"] for x in self.model.calls])
        for call in self.model.calls:
            paths = {x["path"] for x in call["snapshot"]["implementation_artifacts"]}
            if call["snapshot"]["target_id"] == "service.transfer":
                self.assertNotIn("app/ledger.py", paths)
            else:
                self.assertNotIn("app/transfer.py", paths)
        self.assertNotIn("def transfer", json.dumps(result))

    def test_domain_resume_upgrades_component_reviews_before_reusing_completed_work(self):
        task = {"target_id": "scope.bank", "task": "Implement the transfer promise"}
        self.assertEqual("succeeded", self.run_op("concorde-dev-loop", {**task, "specify": False, "run_reviews": False})["status"])
        def component_gap(stage, snapshot, data, cwd):
            if snapshot["target_id"] == "service.transfer":
                self.missing("spec-review")(stage, snapshot, data, cwd)
        result = self.run_op("concorde-dev-loop", {**task, "specify": False, "run_reviews": True}, callback=component_gap)
        self.assertEqual("blocked", result["status"], result)
        state = read_change(self.root)
        self.assertTrue(state["review_requirements"]["service.transfer"]["spec"])
        self.assertNotEqual("ready", state["status"])
        spec = self.root / "specs/send-money.md"
        spec.write_text(spec.read_text() + "\nThe transfer daily-limit owner supplies the required rule.\n")
        resumed = self.run_op("concorde-dev-loop", {**task, "specify": False, "run_reviews": False})
        self.assertEqual("succeeded", resumed["status"], resumed)
        self.assertIn(("service.transfer", "code-review"),
            [(call["snapshot"]["target_id"], call["stage"]) for call in self.model.calls])

    def test_standalone_review_does_not_substitute_for_standard_loop_authoring(self):
        ensure_change(self.root, task=self.task, allow_primary=True)
        self.assertEqual("succeeded", self.run_op("concorde-review", {
            **self.task, "task": "Inspect a separate possible use", "review_mode": "spec"})["status"])
        result = self.run_op("concorde-dev-loop")
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("specify", self.model.calls[0]["stage"])

    def test_rejected_authoring_preserves_gaps_until_the_host_accepts_the_repair(self):
        result = self.run_op("concorde-specify", callback=self.missing("specify"))
        self.assertEqual("blocked", result["status"], result)
        original = (self.root / "specs/send-money.md").read_bytes()
        gap = read_change(self.root)["gap_history"][0]
        def invalid(stage, snapshot, data, cwd):
            data["documents"] = [{"path": "specs/send-money.md", "content": "Missing document declaration"}]
        result = self.run_op("concorde-specify", callback=invalid)
        self.assertNotEqual("succeeded", result["status"], result)
        state = read_change(self.root)
        self.assertEqual(gap, state["gap_history"][0])
        self.assertEqual([gap["gap"]], state["gaps"])
        self.assertEqual(original, (self.root / "specs/send-money.md").read_bytes())
        def repair(stage, snapshot, data, cwd):
            data["documents"] = [{"path": "specs/send-money.md", "content": original.decode() + "\nThe daily-limit owner is transfer.\n"}]
        self.assertEqual("succeeded", self.run_op("concorde-specify", callback=repair)["status"])
        self.assertEqual("resolved", read_change(self.root)["gap_history"][0]["status"])

    def test_rejected_plan_tasks_and_implementation_cannot_resolve_previous_gaps(self):
        for phase in ("plan", "tasks", "implementation"):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                previous_root = self.root
                self.root = Path(directory)
                try:
                    project(self.root)
                    self.assertEqual("blocked", self.run_op("concorde-dev-loop",
                        callback=self.missing(phase))["status"])
                    spec = self.root / "specs/send-money.md"
                    spec.write_text(spec.read_text() + "\nThe daily-limit owner is transfer.\n")
                    def invalid(stage, snapshot, data, cwd):
                        if stage == phase:
                            data["plan" if phase == "plan" else "tasks"] = "" if phase == "plan" else []
                    result = self.run_op("concorde-dev-loop", callback=invalid)
                    self.assertNotEqual("succeeded", result["status"], result)
                    self.assertEqual("open", read_change(self.root)["gap_history"][0]["status"])
                    self.assertTrue(read_change(self.root)["gaps"])
                    self.assertEqual("succeeded", self.run_op("concorde-dev-loop")["status"])
                    self.assertEqual("resolved", read_change(self.root)["gap_history"][0]["status"])
                finally:
                    self.root = previous_root

    def test_failed_plan_artifact_write_can_resume_and_resolve_the_planning_gap(self):
        from concorde.host import capability_host
        self.assertEqual("blocked", self.run_op("concorde-dev-loop",
            callback=self.missing("plan"))["status"])
        spec = self.root / "specs/send-money.md"
        spec.write_text(spec.read_text() + "\nThe daily-limit owner is transfer.\n")
        original_apply = capability_host.apply_files
        def reject_plan(root, changes, allowed, **kwargs):
            if any(item["path"].endswith("/plan.md") for item in changes):
                raise OSError("fixture plan directory cannot be written")
            return original_apply(root, changes, allowed, **kwargs)
        with patch.object(capability_host, "apply_files", side_effect=reject_plan):
            self.assertNotEqual("succeeded", self.run_op("concorde-dev-loop")["status"])
        self.assertEqual("open", read_change(self.root)["gap_history"][0]["status"])
        resumed = self.run_op("concorde-dev-loop")
        self.assertEqual("succeeded", resumed["status"], resumed)
        self.assertIn("plan", [call["stage"] for call in self.model.calls])
        self.assertEqual("resolved", read_change(self.root)["gap_history"][0]["status"])

    def test_gap_capture_is_explicit_deduplicated_and_keeps_owner_and_blocker(self):
        result = self.run_op("concorde-plan", callback=self.missing("context-solve"))
        self.assertEqual("blocked", result["status"])
        status = self.run_op("concorde-reflections-triage", {**self.task, "action": "status", "reflection_ids": []})
        self.assertEqual("succeeded", status["status"], status)
        gap = status["output"]["data"]["gap_records"][0]
        self.assertEqual("open", gap["status"])
        self.assertIsNone(gap["reflection_id"])
        request = {**self.task, "action": "record-gaps", "reflection_ids": [], "gap_ids": [gap["id"]]}
        result = self.run_op("concorde-reflections-triage", request)
        self.assertEqual("succeeded", result["status"], result)
        reflection = result["output"]["data"]["reflections"][0]
        self.assertEqual("service.transfer", reflection["target_id"])
        self.assertEqual("open", read_change(self.root)["gap_history"][0]["status"])
        self.assertEqual([], self.model.calls)
        repeated = self.run_op("concorde-reflections-triage", request)
        self.assertEqual(reflection["id"], repeated["output"]["data"]["reflections"][0]["id"])
        self.assertEqual(1, len(list((self.root / ".concorde/reflections/pending").glob("R-*.md"))))
        rejected = self.run_op("concorde-reflections-triage", {**request, "target_id": "module.ledger"})
        self.assertEqual("permission_denied", rejected["errors"][0]["code"])


class RepairLoopTests(unittest.TestCase):
    """R-069: the dev-loop's only automatic revision edge is review_code -> tasks, bounded by
    the declared max_repair_iterations policy (see capabilities/dev_loop.GRAPH)."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.registry = project(self.root)
        self.configuration = CONFIGURATION
        self.task = {"target_id": "service.transfer", "task": "Implement the pure transfer contract"}

    def double(self, callback=None):
        double = ModelProcessDouble(callback)
        self.addCleanup(double.runtime_directory.cleanup)
        return double

    def run_op(self, operation, data=None, callback=None, *, mode="execute", double=None):
        self.model = double or self.double(callback)
        self.host = CapabilityHost(self.root, PACKAGE, executor=self.model.executor,
            allow_primary_worktree=True, mode=mode, routed_target=(data or self.task)["target_id"])
        return run_capability(operation, self.configuration, typed(operation + "-request", data or self.task),
                             host_context=self.host)

    @staticmethod
    def finding(problem="A required daily-limit check is missing.", finding_id="daily-limit-check"):
        return {"id": finding_id, "severity": "blocking", "target_id": "service.transfer",
                "document": "specs/send-money.md", "contract": "Pure transfer",
                "location": {"path": "app/transfer.py", "line": 1},
                "problem": problem, "affected_task": "Reject invalid amounts"}

    @staticmethod
    def repair_tasks(counter, snapshot, data):
        """Give the repair round a task id that never repeats an earlier (historical) id."""
        if any(item["type_id"] == "concorde-review-result" for item in snapshot["stage_inputs"]):
            data["tasks"] = [{"id": f"task.transfer.repair.{counter[0]}", "target_id": snapshot["target_id"],
                "description": "Repair the reported daily-limit defect.",
                "acceptance": "Valid transfer subtracts; invalid amount or insufficient funds raises ValueError.",
                "complete": False}]

    def test_blocking_then_clean_repairs_once_and_reaches_ready(self):
        counter = [0]
        reviews = {"count": 0}
        def callback(stage, snapshot, data, cwd):
            if stage == "code-review":
                reviews["count"] += 1
                if reviews["count"] == 1:
                    data.update(status="findings", findings=[self.finding()], gaps=[])
            if stage == "tasks":
                counter[0] += 1
                self.repair_tasks(counter, snapshot, data)
        result = self.run_op("concorde-dev-loop", callback=callback)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        stages = [c["stage"] for c in self.model.calls]
        self.assertEqual(2, stages.count("implementation"))
        self.assertEqual(2, stages.count("code-review"))
        tasks_calls = [c for c in self.model.calls if c["stage"] == "tasks"]
        self.assertEqual(2, len(tasks_calls))
        second_inputs = tasks_calls[1]["snapshot"]["stage_inputs"]
        types = {item["type_id"] for item in second_inputs}
        self.assertIn("concorde-implementation-task", types)
        self.assertIn("concorde-review-result", types)
        implementation_task_input = next(item for item in second_inputs
            if item["type_id"] == "concorde-implementation-task")
        self.assertTrue(implementation_task_input["data"]["tasks"])
        self.assertTrue(all(t["complete"] for t in implementation_task_input["data"]["tasks"]))
        implement_calls = [c for c in self.model.calls if c["stage"] == "implementation"]
        self.assertEqual(2, len(implement_calls))
        repair_implement_types = {item["type_id"] for item in implement_calls[1]["snapshot"]["stage_inputs"]}
        self.assertIn("concorde-review-result", repair_implement_types)
        state = read_change(self.root)
        transitions = state["graph"]["service.transfer"]["transitions"]
        repairs = [t for t in transitions if t["trigger"] == "ai-review" and t["to"] == "tasks"]
        self.assertEqual(1, len(repairs))
        self.assertEqual(["daily-limit-check"], repairs[0]["finding_ids"])
        self.assertIsNotNone(repairs[0]["artifact"])
        self.assertEqual(1, len(state["targets"]["service.transfer"]["task_history"]))

    def _reach_unchanged_feedback_waiting(self):
        counter = [0]
        def callback(stage, snapshot, data, cwd):
            if stage == "code-review":
                data.update(status="findings", findings=[self.finding()], gaps=[])
            if stage == "tasks":
                counter[0] += 1
                self.repair_tasks(counter, snapshot, data)
        result = self.run_op("concorde-dev-loop", callback=callback)
        self.assertEqual("blocked", result["status"], result)
        return result

    def test_unchanged_blocking_feedback_stops_waiting_after_one_repair(self):
        result = self._reach_unchanged_feedback_waiting()
        self.assertEqual("conflicting", result["output"]["data"]["outcome"])
        self.assertEqual("waiting", read_change(self.root)["status"])
        stages = [c["stage"] for c in self.model.calls]
        self.assertEqual(2, stages.count("implementation"))
        self.assertEqual(2, stages.count("code-review"))

    def test_repeated_different_blocking_feedback_stops_at_the_declared_limit(self):
        review_counter = [0]
        counter = [0]
        def callback(stage, snapshot, data, cwd):
            if stage == "code-review":
                review_counter[0] += 1
                data.update(status="findings", gaps=[], findings=[self.finding(
                    problem=f"Distinct defect variant {review_counter[0]}.",
                    finding_id=f"defect-{review_counter[0]}")])
            if stage == "tasks":
                counter[0] += 1
                self.repair_tasks(counter, snapshot, data)
        result = self.run_op("concorde-dev-loop", callback=callback)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("conflicting", result["output"]["data"]["outcome"])
        state = read_change(self.root)
        self.assertEqual("limit_exhausted", state["status"])
        stages = [c["stage"] for c in self.model.calls]
        self.assertEqual(3, stages.count("implementation"))
        self.assertEqual(3, stages.count("code-review"))
        self.assertEqual(2, state["graph"]["service.transfer"]["repair_iteration"])
        self.assertEqual(2, state["graph"]["service.transfer"]["policy"]["max_repair_iterations"])

    def test_spec_gap_in_spec_review_stops_waiting_before_planning(self):
        def callback(stage, snapshot, data, cwd):
            if stage == "spec-review":
                data.update(status="findings", gaps=[{
                    "question": "Who owns the daily limit?", "blocked_step": "Decide daily-limit admission",
                    "needed_contract": "The transfer daily-limit owner and admission rule"}],
                    findings=[{"id": "missing-limit", "severity": "blocking", "target_id": snapshot["target_id"],
                        "document": "specs/send-money.md",
                        "contract": "The transfer daily-limit owner and admission rule",
                        "location": {"path": "specs/send-money.md", "line": 12},
                        "problem": "A required daily-limit promise is absent.",
                        "affected_task": "Decide daily-limit admission"}])
        result = self.run_op("concorde-dev-loop", callback=callback)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("spec_incomplete", result["output"]["data"]["outcome"])
        self.assertEqual("waiting", read_change(self.root)["status"])
        self.assertNotIn("plan", [c["stage"] for c in self.model.calls])

    def test_admitted_specify_spec_change_does_not_spuriously_reset_the_graph_record(self):
        def callback(stage, snapshot, data, cwd):
            if stage == "specify" and snapshot["target_id"] == "service.transfer":
                document = next(d for d in snapshot["target_spec"] if d["path"] == "specs/send-money.md")
                data["documents"] = [{"path": "specs/send-money.md",
                    "content": document["content"] + "\nThe transfer capability documents an additional promise.\n"}]
        result = self.run_op("concorde-dev-loop", callback=callback)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        self.assertIn("The transfer capability documents an additional promise.",
                      (self.root / "specs/send-money.md").read_text())
        self.assertEqual([], read_change(self.root)["graph"]["service.transfer"]["transitions"])
        # A second dev-loop resumes without re-authoring; the first run's own admitted Spec change
        # must not be mistaken for an out-of-band human edit and spuriously reset the record.
        second = self.run_op("concorde-dev-loop")
        self.assertEqual("succeeded", second["status"], second)
        self.assertNotIn("specify", [c["stage"] for c in self.model.calls])
        record = read_change(self.root)["graph"]["service.transfer"]
        self.assertEqual([], [t for t in record["transitions"] if t["trigger"] == "human"])
        # A genuinely human Spec edit between runs still resets the record.
        spec = self.root / "specs/send-money.md"
        spec.write_text(spec.read_text() + "\nA human directly edited this Spec.\n")
        third = self.run_op("concorde-dev-loop")
        self.assertEqual("succeeded", third["status"], third)
        record = read_change(self.root)["graph"]["service.transfer"]
        human_transitions = [t for t in record["transitions"] if t["trigger"] == "human"]
        self.assertEqual(1, len(human_transitions))
        self.assertEqual("spec_changed", human_transitions[0]["outcome"])

    def test_human_implementation_edit_resets_the_repair_record(self):
        self._reach_unchanged_feedback_waiting()
        before = read_change(self.root)
        self.assertEqual(1, before["graph"]["service.transfer"]["repair_iteration"])
        code = self.root / "app/transfer.py"
        code.write_text(code.read_text() + "\n# a human edited this directly\n")
        result = self.run_op("concorde-dev-loop")
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        record = read_change(self.root)["graph"]["service.transfer"]
        self.assertEqual(0, record["repair_iteration"])
        human_transitions = [t for t in record["transitions"] if t["trigger"] == "human"]
        self.assertEqual(1, len(human_transitions))
        self.assertEqual("implementation_changed", human_transitions[0]["outcome"])

    def test_capability_execution_error_during_standalone_code_review_maps_to_execution_limit(self):
        from concorde.host.agent_executor import CapabilityExecutionError
        from concorde.host.change_worktree import ensure_change
        ensure_change(self.root, task=self.task, allow_primary=True)
        double = self.double()
        def fail(launch):
            raise CapabilityExecutionError(
                "codex process exceeded the Harness loop limit of 10s", None, outcome="limit_exhausted")
        double.executor = fail
        result = self.run_op("concorde-review", {**self.task, "review_mode": "code"}, double=double)
        self.assertEqual("failed", result["status"], result)
        reviewed = result["output"]["data"]["reviews"][0]["data"]
        self.assertEqual("incomplete", reviewed["status"])
        reference = result["output"]["data"]["artifacts"][0]
        private = json.loads((self.root / reference["path"]).with_suffix(".execution.json").read_text())
        self.assertEqual("execution_limit", private["failure"]["code"])
        self.assertIsNone(private["execution"])
        self.assertEqual("limit_exhausted", read_change(self.root)["status"])
