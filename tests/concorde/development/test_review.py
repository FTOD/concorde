"""Review mechanism tests. Process doubles do not measure semantic detection quality."""
import json
import subprocess
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch

from concorde.harness.change_worktree import ensure_change, read_change, save_change
from concorde.harness.permissions import PermissionPolicyError
from concorde.spec.typed_data import DATA_SCHEMAS, typed
from concorde.spec.verification import verifies
from concorde.development.capability_service import CapabilityHost, run_capability
from concorde.development.capability_host import Invocation
from concorde.development.review import current, inputs
from tests.concorde.spec.support import CONFIGURATION, PACKAGE, ModelProcessDouble, project, update_document_declaration


class ReviewTests(unittest.TestCase):
    @verifies("scenario.development.task-history-identities", "scenario.development.task-scope-repair")
    def test_replan_author_sees_all_retained_ids_and_collision_is_rejected_without_rewriting(self):
        from concorde.spec.repository import digest
        observed = []
        def author(stage, snapshot, data, cwd):
            if stage == "tasks":
                identity = next(v for v in snapshot["stage_inputs"]
                    if v["type_id"] == "concorde-task-identity-constraints")
                reserved = identity["data"]["reserved_task_ids"]
                self.assertEqual([f"task.round.{i}" for i in range(len(observed))], reserved)
                self.assertEqual([], snapshot["implementation_artifacts"])
                self.assertTrue(all("content" not in item for item in snapshot["implementation_files"]))
                observed.append(snapshot)
                data["tasks"][0]["id"] = f"task.round.{len(reserved)}"
            if stage == "implementation":
                for task in data["tasks"]:
                    task["complete"] = False
        self.call_capability("concorde-dev-loop", callback=author)
        for _ in range(2):
            tasks = read_change(self.root)["targets"]["service.transfer"]["tasks"]
            self.call_capability("concorde-dev-loop", {**self.task,
                "repair_task_scope": {"tasks_digest": digest(tasks)}}, callback=author)
        history = read_change(self.root)["targets"]["service.transfer"]["task_history"]
        self.assertEqual(2, len(history))
        self.assertEqual(3, len(observed))
        self.assertEqual(3, len({s["context_id"] for s in observed}))

        # A real Spec revision selects the normal replan edge. Current tasks are cleared,
        # but the two retained lists must still reach the fresh, Spec-only task author.
        document = self.root / "specs/transfer/module.md"
        document.write_text(document.read_text() + "\n")
        replanned = []
        def collide(stage, snapshot, data, cwd):
            if stage == "tasks":
                replanned.append(snapshot)
                values = {v["type_id"]: v["data"] for v in snapshot["stage_inputs"]}
                self.assertEqual(["task.round.0", "task.round.1"],
                    values["concorde-task-identity-constraints"]["reserved_task_ids"])
                self.assertNotIn("concorde-implementation-task", values)
                self.assertIn("reserved_task_ids", snapshot["instructions"])
                self.assertEqual([], snapshot["implementation_artifacts"])
                data["tasks"][0]["id"] = "task.round.0"
        rejected = self.call_capability("concorde-dev-loop", callback=collide)
        self.assertEqual("child_blocked", rejected["errors"][0]["code"], rejected)
        errors = json.loads(rejected["errors"][0]["message"].split("concorde-tasks blocked: ", 1)[1])
        self.assertEqual("invalid_completion", errors[0]["code"])
        self.assertIn("task.round.0", errors[0]["message"])
        self.assertEqual(1, len(replanned))
        self.assertIn("plan", [c["stage"] for c in self.model.calls])
        state = read_change(self.root)["targets"]["service.transfer"]
        self.assertEqual([], state["tasks"])
        self.assertEqual(history, state["task_history"])
        self.assertIsNone(state["implementation_digest"])
        self.assertNotIn("implementation", [c["stage"] for c in self.model.calls])

        def accept(stage, snapshot, data, cwd):
            if stage == "tasks":
                reserved = next(v["data"]["reserved_task_ids"] for v in snapshot["stage_inputs"]
                    if v["type_id"] == "concorde-task-identity-constraints")
                data["tasks"][0]["id"] = f"task.round.{len(reserved)}.replanned"
        accepted = self.call_capability("concorde-dev-loop", callback=accept)
        self.assertEqual("succeeded", accepted["status"], accepted)
        self.assertEqual("ready", accepted["output"]["data"]["outcome"])
        state = read_change(self.root)["targets"]["service.transfer"]
        self.assertEqual("task.round.2.replanned", state["tasks"][0]["id"])
        self.assertEqual(history, state["task_history"])

    @verifies("scenario.harness.node-runtime")
    def test_project_worker_pins_host_node_but_spec_capsule_does_not(self):
        import os
        import tomllib
        from concorde.harness.agent_executor import resolve_runtime_bootstrap

        model = self.double()
        node = Path(model.runtime_directory.name) / "node"
        node.write_bytes(b"\x7fELFfixture-node-runtime")
        node.chmod(0o755)
        # This process-double test covers projection of an admitted runtime, not
        # machine installation trust. In a configured check's user namespace,
        # host-root ancestors are unmapped, so the real Node resolver must reject
        # them. Keep that policy in the resolver tests and supply fixture admission
        # here, just as ModelProcessDouble does for Codex. File rechecks stay real.
        bootstrap = resolve_runtime_bootstrap("codex", str(node), str(self.root), {})
        self.configuration = typed("concorde-capability-configuration", {"integration": "codex", "enforcement": "native"})
        config_path = self.root / ".concorde/config.json"
        config = json.loads(config_path.read_text())
        config["capability_configuration"] = self.configuration
        config_path.write_text(json.dumps(config))
        with patch("concorde.harness.agent_executor.resolve_node_runtime", return_value=bootstrap) as resolver:
            result = self.call_capability("concorde-dev-loop", double=model)
        self.assertEqual("succeeded", result["status"], result)
        project_calls = [call for call in self.model.calls if call["stage"] in {"implementation", "code-review"}]
        self.assertEqual({"implementation", "code-review"}, {call["stage"] for call in project_calls})
        self.assertEqual(2 * len(project_calls), resolver.call_count)  # admission and pre-launch recheck
        for call in self.model.calls:
            settings = {}
            for i, arg in enumerate(call["argv"]):
                if arg == "-c":
                    settings.update(tomllib.loads(call["argv"][i + 1]))
            if call["stage"] in {"implementation", "code-review"}:
                self.assertFalse(settings["allow_login_shell"])
                self.assertEqual(str(node.parent), settings["shell_environment_policy"]["set"]["PATH"].split(os.pathsep)[0])
                profile = next(iter(settings["permissions"].values()))
                self.assertEqual("read", profile["filesystem"][str(node)])
            else:
                self.assertNotIn("shell_environment_policy", settings)
                self.assertNotIn(str(node), json.dumps(settings))

    @verifies("scenario.development.task-scope-repair")
    def test_invalid_scope_repair_cannot_replace_or_complete_original_tasks(self):
        from concorde.spec.repository import digest
        def incomplete(stage, snapshot, data, cwd):
            if stage == "implementation":
                for task in data["tasks"]:
                    task["complete"] = False
        self.call_capability("concorde-dev-loop", callback=incomplete)
        original = read_change(self.root)["targets"]["service.transfer"]["tasks"]
        request = {**self.task, "repair_task_scope": {"tasks_digest": digest(original)}}
        for invalid in ("completed", "reused_id"):
            def reject(stage, snapshot, data, cwd):
                if stage == "tasks" and invalid == "completed":
                    data["tasks"][0]["complete"] = True
            result = self.call_capability("concorde-dev-loop", request, callback=reject)
            self.assertNotEqual("succeeded", result["status"], result)
            state = read_change(self.root)["targets"]["service.transfer"]
            self.assertEqual(original, state["tasks"])
            self.assertEqual([], state.get("task_history", []))
            self.assertIsNone(state.get("implementation_digest"))

    @verifies("scenario.development.task-scope-repair")
    def test_incomplete_phase_tasks_repair_then_implementation_validation_review_ready(self):
        from concorde.spec.repository import digest
        def incomplete(stage, snapshot, data, cwd):
            if stage == "tasks":
                data["tasks"][0]["acceptance"] += " Host review and validation then commit must finish first."
            if stage == "implementation":
                for task in data["tasks"]:
                    task["complete"] = False
        first = self.call_capability("concorde-dev-loop", callback=incomplete)
        self.assertNotEqual("succeeded", first["status"])
        original = read_change(self.root)["targets"]["service.transfer"]["tasks"]
        # A new Framework binding also changes this revision. Exercise fresh review
        # and task revalidation with a meaning-preserving contract revision.
        document = self.root / "specs/transfer/module.md"
        document.write_text(document.read_text() + "\n")
        request = {**self.task, "repair_task_scope": {"tasks_digest": digest(original)}}
        def repair(stage, snapshot, data, cwd):
            if stage == "tasks":
                feedback = next(v for v in snapshot["stage_inputs"] if v["type_id"] == "concorde-task-scope-feedback")
                self.assertEqual("implementation_boundary", feedback["data"]["reason"])
                self.assertEqual([], snapshot["implementation_artifacts"])
                self.assertTrue(all("content" not in item for item in snapshot["implementation_files"]))
                data["tasks"][0]["id"] += ".scope-repair"
        repaired = self.call_capability("concorde-dev-loop", request, callback=repair)
        self.assertEqual("succeeded", repaired["status"], repaired)
        self.assertEqual("ready", repaired["output"]["data"]["outcome"])
        stages = [call["stage"] for call in self.model.calls]
        self.assertLess(stages.index("tasks"), stages.index("implementation"))
        self.assertLess(stages.index("implementation"), stages.index("code-review"))
        state = read_change(self.root)
        history = state["targets"]["service.transfer"]["task_history"]
        self.assertEqual(original, history[0]["tasks"])
        self.assertTrue(all(not t["complete"] for t in history[0]["tasks"]))
        self.assertTrue(state["review_requirements"]["service.transfer"]["spec"])
        self.assertTrue(state["review_requirements"]["service.transfer"]["code"])
        replay = self.call_capability("concorde-dev-loop", request)
        self.assertEqual("succeeded", replay["status"], replay)
        self.assertFalse(any(c["stage"] in {"tasks", "implementation"} for c in self.model.calls))
        stale = self.call_capability("concorde-dev-loop", {**request,
            "repair_task_scope": {"tasks_digest": "sha256:" + "0" * 64}})
        self.assertNotEqual("succeeded", stale["status"])

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

    def call_capability(self, capability, data=None, callback=None, *, mode="execute", double=None):
        self.model = double or self.double(callback)
        self.host = CapabilityHost(self.root, PACKAGE, executor=self.model.executor,
            allow_primary_worktree=True, mode=mode, routed_target=(data or self.task)["target_id"])
        return run_capability(capability, self.configuration, typed(capability + "-request", data or self.task),
                             host_context=self.host)

    def review(self, review_mode="spec", callback=None, **kwargs):
        return self.call_capability("concorde-review", {**self.task, "review_mode": review_mode}, callback, **kwargs)

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
                    "document": "specs/transfer/module.md", "contract": self.gap()["needed_contract"],
                    "location": {"path": "specs/transfer/module.md", "line": 12},
                    "problem": "A required daily-limit promise is absent.",
                    "affected_task": self.gap()["blocked_step"]}])
            else:
                data.update(outcome="spec_incomplete", gaps=[self.gap()])
        return callback

    @verifies("scenario.development.execute-capability")
    def test_modes_use_full_collection_fresh_sessions_and_no_write_grants(self):
        self.registry["targets"][3]["documents"].append("specs/transfer/promises.md")
        (self.root / ".concorde/specs.json").write_text(json.dumps(self.registry))
        update_document_declaration(self.root, "specs/transfer/promises.md",
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
            self.assertEqual(["specs/transfer/module.md", "specs/transfer/promises.md"], snapshot["document_order"])
            self.assertEqual(["specs/transfer/promises.md"], [x["path"] for x in snapshot["shared_specs"]])
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
                # The listed file names are Spec facts; only code review reads their bytes.
                self.assertEqual(["app/transfer.py", "checks/transfer_check.py"],
                                 [item["path"] for item in snapshot["implementation_files"]])
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

    def relist_checks_directory(self):
        """List the transfer check entity as the whole `checks/` directory instead of one file."""
        document = self.root / "specs/transfer/module.md"
        text = document.read_text()
        prefix, rest = text.split("```concorde-entities\n", 1)
        payload, suffix = rest.split("\n```", 1)
        entities = json.loads(payload)
        for entity in entities:
            if entity["id"] == "entity.transfer.check":
                entity["files"] = ["checks/"]
        document.write_text(prefix + "```concorde-entities\n" + json.dumps(entities, indent=2)
                            + "\n```" + suffix)
        self.registry["targets"][2]["files"] = ["app/transfer.py", "checks/"]
        (self.root / ".concorde/specs.json").write_text(json.dumps(self.registry))

    def test_a_directory_entry_scopes_history_and_grants_its_subtree(self):
        self.relist_checks_directory()
        (self.root / "checks/.tool.json").write_text('{"excluded": true}\n')
        self.commit_fixture()
        (self.root / "app/transfer.py").write_text("CHANGED_LOCAL_CODE\n")
        (self.root / "app/ledger.py").write_text("UNGRANTED_OTHER_CODE\n")
        # A file created below the listed directory needs no new declaration.
        (self.root / "checks/extra_check.py").write_text("NEW_LISTED_CHECK\n")
        (self.root / "checks/transfer_check.py").unlink()
        (self.root / "checks/__pycache__").mkdir()
        (self.root / "checks/__pycache__/transfer_check.pyc").write_bytes(b"cached")
        result = self.review("code")
        self.assertEqual("succeeded", result["status"], result)
        review = self.model.calls[0]["review"]
        # History is scoped by the directory root: the deleted listed file appears, the ungranted
        # peer file does not, and neither do the skipped dot file and cache the walk excludes.
        self.assertEqual({"app/transfer.py", "checks/extra_check.py", "checks/transfer_check.py"},
                         {item["path"] for item in review["changes"]})
        self.assertNotIn("UNGRANTED_OTHER_CODE", json.dumps(review))
        self.assertNotIn(".tool.json", json.dumps(review))
        policy = self.host.descriptions[0]
        self.assertIn("checks/extra_check.py", policy["read_paths"])
        self.assertNotIn("checks/.tool.json", policy["read_paths"])
        self.assertEqual([], policy["write_paths"])
        snapshot = self.model.calls[0]["snapshot"]
        self.assertEqual([("app/transfer.py", False), ("checks/", True)],
                         [(item["path"], item["directory"])
                          for item in snapshot["implementation_entries"]])
        self.assertEqual(["app/transfer.py", "checks/extra_check.py"],
                         [item["path"] for item in snapshot["implementation_files"]])

    @verifies("scenario.development.describe-policy")
    def test_describe_policy_is_not_a_completed_review(self):
        for mode in ("spec", "code"):
            result = self.review(mode, mode="describe-policy")
            self.assertEqual("described", result["status"])
            self.assertEqual("not_run", result["output"]["data"]["reviews"][0]["data"]["status"])
            self.assertEqual([], self.model.calls)
        self.assertFalse((self.root / ".concorde/runs").exists())

    @verifies("scenario.development.execute-blocked-launch")
    def test_failed_policy_preview_does_not_persist_artifacts_or_change_state(self):
        # Configuration admits native enforcement only, so an unenforceable compiled policy is
        # simulated at the renderer: the integration reports that it cannot enforce the grant.
        ensure_change(self.root, task=self.task, allow_primary=True)
        before = read_change(self.root)
        unenforceable = PermissionPolicyError("simulated: the integration cannot enforce the compiled policy")
        with patch("concorde.development.review.render_claude_configuration", side_effect=unenforceable):
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
            lambda d: d.update(documents=[{"path": "specs/transfer/module.md", "content": "replacement"}]),
        ]
        original = (self.root / "specs/transfer/module.md").read_bytes()
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                def callback(stage, snapshot, data, cwd):
                    mutate(data)
                result = self.review(callback=callback)
                self.assertEqual("failed", result["status"], result)
                self.assertEqual("incomplete", result["output"]["data"]["reviews"][0]["data"]["status"])
        self.assertEqual(original, (self.root / "specs/transfer/module.md").read_bytes())
        def foreign(stage, snapshot, data, cwd):
            self.missing("spec-review")(stage, snapshot, data, cwd)
            data["findings"][0]["document"] = "specs/ledger/module.md"
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
        from concorde.harness.agent_executor import CapabilityExecutionError
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
            path = self.root / "specs/transfer/module.md"
            path.write_text(path.read_text() + "\nChanged during review.\n")
        result = self.review(callback=change)
        self.assertEqual("failed", result["status"])
        self.assertIn("stale_context", result["output"]["data"]["answer"])
        def code_change(stage, snapshot, data, cwd):
            (self.root / "app/transfer.py").write_text("Modified by a deliberately invalid process double\n")
        result = self.review("code", callback=code_change)
        self.assertEqual("failed", result["status"])
        self.assertIn("stale_context", result["output"]["data"]["answer"])

    @verifies("scenario.development.dev-loop-ready")
    def test_required_reviews_surround_planning_and_follow_checks_before_ready(self):
        observed = []
        def inspect(stage, snapshot, data, cwd):
            if stage == "code-review":
                state = read_change(self.root)
                observed.append(state["status"])
                self.assertEqual("passed", state["targets"][self.task["target_id"]]["checks"][0]["status"])
        result = self.call_capability("concorde-dev-loop", callback=inspect)
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
        self.assertEqual("succeeded", self.call_capability("concorde-dev-loop")["status"])
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
        spec = self.root / "specs/transfer/module.md"
        spec.write_text(spec.read_text() + "\nChanged contract.\n")
        self.assertIsNone(current(self.invocation(), "spec"))

    @verifies("scenario.development.dev-loop-spec-gap")
    def test_changed_review_instructions_reassess_without_erasing_gaps_on_failure(self):
        import hashlib
        from contextlib import contextmanager
        from concorde.harness import agent_model
        from concorde.harness.agent_model import binding_digest
        from concorde.development.review import load_role_prompt
        first = self.call_capability("concorde-dev-loop", callback=self.missing("spec-review"))
        self.assertEqual("blocked", first["status"], first)
        original = read_change(self.root)["gap_history"][0]
        self.call_capability("concorde-dev-loop")
        self.assertFalse(any(c["stage"] == "spec-review" for c in self.model.calls))

        def revised(suffix, *args, **kwargs):
            prompt = load_role_prompt(*args, **kwargs)
            if prompt.binding.mode != "spec-review":
                return prompt
            body = prompt.body + suffix
            binding = replace(prompt.binding,
                instructions_digest="sha256:" + hashlib.sha256(body.encode()).hexdigest())
            return replace(prompt, body=body, binding=replace(binding, digest=binding_digest(binding)))

        def changed(*args, **kwargs):
            return revised("\nClarified task relevance.\n", *args, **kwargs)

        @contextmanager
        def instructions(loader):
            # Admit the test's new instruction binding through the same preflight
            # as a rebuilt package; all effects and mode contracts stay intact.
            resolve = agent_model.resolve_agent
            from concorde.distribution.build import render_agent
            prompt = loader(PACKAGE, "spec-engineer", "spec-review")
            def binding(package, name, mode=None):
                return prompt.binding if mode == "spec-review" else resolve(package, name, mode)
            def rendered(package, name, mode=None):
                output = render_agent(package, name, mode)
                return replace(output, content=prompt.body.encode()) if mode == "spec-review" else output
            with patch("concorde.development.review.load_role_prompt", side_effect=loader), \
                    patch("concorde.harness.agent_model.resolve_agent", side_effect=binding), \
                    patch("concorde.distribution.build.render_agent", side_effect=rendered):
                yield

        def incomplete(stage, snapshot, data, cwd):
            if stage == "spec-review":
                data.update(status="incomplete", answer="Coverage could not be completed.")
        with instructions(changed):
            result = self.call_capability("concorde-dev-loop", callback=incomplete)
            self.assertEqual("failed", result["status"], result)
            self.assertTrue(any(c["stage"] == "spec-review" for c in self.model.calls))
            self.assertEqual(original, read_change(self.root)["gap_history"][0])

        # Another actual instruction revision permits a completed reassessment.
        # The Host preserves the reviewer's independent finding and old history.
        def changed_again(*args, **kwargs):
            return revised("\nReassess coverage.\n", *args, **kwargs)
        def advisory(stage, snapshot, data, cwd):
            if stage == "spec-review":
                self.missing(stage)(stage, snapshot, data, cwd)
                data["findings"][0]["severity"] = "advisory"
                data["gaps"] = []
        with instructions(changed_again):
            result = self.call_capability("concorde-dev-loop", callback=advisory)
        self.assertEqual("succeeded", result["status"], result)
        state = read_change(self.root)
        self.assertEqual("resolved", state["gap_history"][0]["status"])
        self.assertEqual(original["gap"], state["gap_history"][0]["gap"])
        self.assertEqual([], state["gaps"])

    @verifies("scenario.development.dev-loop-spec-gap")
    def test_gap_persists_deduplicates_and_requires_spec_repair_before_resume(self):
        result = self.call_capability("concorde-dev-loop", callback=self.missing("spec-review"))
        self.assertEqual("blocked", result["status"], result)
        self.assertNotIn("plan", [x["stage"] for x in self.model.calls])
        before = read_change(self.root)
        self.assertEqual(1, len(before["gap_history"]))
        retry = self.call_capability("concorde-dev-loop")
        self.assertEqual("blocked", retry["status"], retry)
        self.assertEqual(1, len(read_change(self.root)["gap_history"]))
        self.assertEqual(1, len(read_change(self.root)["gaps"]))
        self.assertEqual(before["gaps"][0]["context_id"], retry["output"]["data"]["gaps"][0]["context_id"])
        self.assertNotIn("plan", [x["stage"] for x in self.model.calls])
        spec = self.root / "specs/transfer/module.md"
        spec.write_text(spec.read_text() + "\nThe transfer capability owns a daily limit of 1000 units.\n")
        resumed = self.call_capability("concorde-dev-loop")
        self.assertEqual("succeeded", resumed["status"], resumed)
        state = read_change(self.root)
        self.assertEqual([], state["gaps"])
        self.assertEqual("resolved", state["gap_history"][0]["status"])
        self.assertEqual("ready", state["status"])
        self.assertNotIn("specify", [x["stage"] for x in self.model.calls])

    @verifies("scenario.development.dev-loop-spec-gap")
    def test_real_task_phases_preserve_gaps_and_resume_after_repair(self):
        for phase in ("context-solve", "plan", "tasks", "implementation"):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as temporary:
                original_root = self.root
                self.root = Path(temporary)
                project(self.root)
                result = self.call_capability("concorde-dev-loop", callback=self.missing(phase))
                self.assertEqual("blocked", result["status"], result)
                self.assertEqual(phase, read_change(self.root)["gap_history"][0]["phase"])
                spec = self.root / "specs/transfer/module.md"
                spec.write_text(spec.read_text() + "\nThe transfer capability owns the necessary daily limit.\n")
                resumed = self.call_capability("concorde-dev-loop")
                self.assertEqual("succeeded", resumed["status"], resumed)
                self.assertEqual([], read_change(self.root)["gaps"])
                self.root = original_root

    def test_fast_loop_records_skips_and_cannot_downgrade_required_review(self):
        result = self.call_capability("concorde-dev-loop", {**self.task, "specify": False, "run_reviews": False})
        self.assertEqual("succeeded", result["status"], result)
        state = read_change(self.root)
        self.assertEqual({"skipped"}, {x["status"] for x in state["reviews"][self.task["target_id"]].values()})
        self.assertIn("spec=skipped", result["output"]["data"]["answer"])
        self.assertIn("code=skipped", result["output"]["data"]["answer"])
        self.assertEqual(2, len(result["output"]["data"]["artifacts"]))
        self.assertFalse(any("review" in x["stage"] for x in self.model.calls))
        result = self.call_capability("concorde-dev-loop", {**self.task, "specify": False, "run_reviews": True}, callback=self.missing("spec-review"))
        self.assertEqual("blocked", result["status"], result)
        retried = self.call_capability("concorde-dev-loop", {**self.task, "specify": False, "run_reviews": False})
        self.assertEqual("blocked", retried["status"], retried)
        self.assertTrue(read_change(self.root)["review_requirements"][self.task["target_id"]]["spec"])

    @verifies("scenario.development.standalone-review")
    def test_independent_contract_findings_remain_visible_without_claiming_completeness(self):
        # Process doubles verify result retention and gates, not semantic relevance.
        for mode in ("spec", "code"):
            with self.subTest(mode=mode):
                def independent(stage, snapshot, data, cwd):
                    if stage == mode + "-review":
                        data.update(status="findings", gaps=[], findings=[{
                            "id": "independent-contract", "severity": "advisory",
                            "target_id": snapshot["target_id"],
                            "document": "specs/transfer/module.md", "contract": "Independent export",
                            "location": {"path": "specs/transfer/module.md", "line": 1},
                            "problem": "Export collision behavior is unspecified. The admitted pure transfer task "
                                       "does not use or change export; this finding does not establish export completeness.",
                            "affected_task": "Export colliding identifiers"}])
                result = self.review(mode, callback=independent)
                self.assertEqual("succeeded", result["status"], result)
                report = result["output"]["data"]["reviews"][0]["data"]
                self.assertEqual("findings", report["status"])
                self.assertEqual("not_proven", report["semantic_completeness"])
                self.assertEqual("independent-contract", report["findings"][0]["id"])
                reference = result["output"]["data"]["artifacts"][0]
                self.assertEqual(report, json.loads((self.root / reference["path"]).read_text())["data"])

    def test_advisory_findings_do_not_block_but_required_incomplete_review_does(self):
        def advisory(stage, snapshot, data, cwd):
            if stage == "code-review":
                data.update(status="findings", findings=[{"id": "clarity", "severity": "advisory",
                    "target_id": "service.transfer", "document": "specs/transfer/module.md", "contract": "Pure transfer",
                    "location": {"path": "app/transfer.py", "line": 1}, "problem": "An example could be clearer.",
                    "affected_task": "Read the implementation"}])
        self.assertEqual("succeeded", self.call_capability("concorde-dev-loop", callback=advisory)["status"])
        state = read_change(self.root)
        state["reviews"][self.task["target_id"]].pop("code")
        save_change(self.root, state)
        def incomplete(stage, snapshot, data, cwd):
            if stage == "code-review":
                data.update(status="incomplete", answer="Required review could not complete.")
        result = self.call_capability("concorde-dev-loop", {**self.task, "specify": False, "run_reviews": False}, callback=incomplete)
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
        self.assertEqual("succeeded", self.call_capability("concorde-dev-loop")["status"])
        before = read_change(self.root)
        result = self.call_capability("concorde-review", {**self.task, "task": "Inspect a separate possible use",
            "review_mode": "spec"}, callback=self.missing("spec-review"))
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual(before, read_change(self.root))
        self.assertIsNotNone(current(self.invocation(), "spec"))

    def test_standalone_dependent_steps_cannot_bypass_a_failed_required_spec_review(self):
        self.assertEqual("succeeded", self.call_capability("concorde-dev-loop")["status"])
        blocked = self.review(callback=self.missing("spec-review"))
        self.assertEqual("blocked", blocked["status"], blocked)
        tasks = read_change(self.root)["targets"][self.task["target_id"]]["tasks"]
        for capability in ("concorde-tasks", "concorde-implement"):
            result = self.call_capability(capability)
            self.assertEqual("blocked", result["status"], result)
            self.assertEqual("review_required", result["errors"][0]["code"])
            self.assertEqual([], self.model.calls)
            self.assertEqual(tasks, read_change(self.root)["targets"][self.task["target_id"]]["tasks"])

    @verifies("scenario.development.dev-loop-spec-gap")
    def test_upstream_task_gaps_block_standalone_dependents_but_allow_independent_queries(self):
        for phase in ("context-solve", "plan"):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                previous_root = self.root
                self.root = Path(directory)
                try:
                    project(self.root)
                    self.assertEqual("succeeded", self.call_capability("concorde-dev-loop")["status"])
                    self.assertEqual("blocked", self.call_capability("concorde-plan", callback=self.missing(phase))["status"])
                    gap = read_change(self.root)["gaps"][0]
                    for capability in ("concorde-tasks", "concorde-implement"):
                        result = self.call_capability(capability)
                        self.assertEqual("blocked", result["status"], result)
                        self.assertEqual([gap], result["output"]["data"]["gaps"])
                        self.assertEqual([], self.model.calls)
                    self.assertEqual("succeeded", self.call_capability("concorde-context-solve")["status"])
                    self.assertEqual("open", read_change(self.root)["gap_history"][0]["status"])
                    spec = self.root / "specs/transfer/module.md"
                    spec.write_text(spec.read_text() + "\nThe daily-limit owner is transfer.\n")
                    self.assertEqual("succeeded", self.call_capability("concorde-dev-loop")["status"])
                    self.assertEqual("resolved", read_change(self.root)["gap_history"][0]["status"])
                finally:
                    self.root = previous_root

    @verifies("scenario.development.resume-bound")
    def test_review_binds_actual_worktree_even_with_identical_unversioned_bytes(self):
        original = inputs(self.invocation(), "spec")[0]["input_digest"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project(root)
            peer = Invocation("concorde-review", self.configuration, self.task, CapabilityHost(root, PACKAGE))
            self.assertNotEqual(original, inputs(peer, "spec")[0]["input_digest"])
        rejected = self.call_capability("concorde-review", {**self.task, "review_mode": "spec", "change_id": "change.foreign"})
        self.assertEqual("missing_change", rejected["errors"][0]["code"])
        self.assertEqual([], self.model.calls)

    @verifies("scenario.development.dev-loop-coordinated")
    def test_domain_review_aggregates_only_separate_recorded_component_contexts(self):
        task = {"target_id": "scope.bank", "task": "Implement the transfer and ledger promises"}
        def components(stage, snapshot, data, cwd):
            if stage == "tasks" and snapshot["target_id"] == "scope.bank":
                data["tasks"].append({"id": "task.ledger", "target_id": "module.ledger",
                    "description": "Implement the ledger read promise.", "acceptance": "Read known balances and reject unknown accounts.",
                    "complete": False})
        result = self.call_capability("concorde-dev-loop", task, callback=components)
        self.assertEqual("succeeded", result["status"], result)
        references = {ref["id"] for ref in result["output"]["data"]["artifacts"]}
        self.assertIn("review.module.ledger.code", references)
        self.assertIn("review.service.transfer.code", references)
        result = self.call_capability("concorde-review", {**task, "review_mode": "code"})
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

    @verifies("scenario.development.dev-loop-coordinated")
    def test_domain_resume_upgrades_component_reviews_before_reusing_completed_work(self):
        task = {"target_id": "scope.bank", "task": "Implement the transfer promise"}
        self.assertEqual("succeeded", self.call_capability("concorde-dev-loop", {**task, "specify": False, "run_reviews": False})["status"])
        def component_gap(stage, snapshot, data, cwd):
            if snapshot["target_id"] == "service.transfer":
                self.missing("spec-review")(stage, snapshot, data, cwd)
        result = self.call_capability("concorde-dev-loop", {**task, "specify": False, "run_reviews": True}, callback=component_gap)
        self.assertEqual("blocked", result["status"], result)
        state = read_change(self.root)
        self.assertTrue(state["review_requirements"]["service.transfer"]["spec"])
        self.assertNotEqual("ready", state["status"])
        spec = self.root / "specs/transfer/module.md"
        spec.write_text(spec.read_text() + "\nThe transfer daily-limit owner supplies the required rule.\n")
        resumed = self.call_capability("concorde-dev-loop", {**task, "specify": False, "run_reviews": False})
        self.assertEqual("succeeded", resumed["status"], resumed)
        self.assertIn(("service.transfer", "code-review"),
            [(call["snapshot"]["target_id"], call["stage"]) for call in self.model.calls])

    def test_standalone_review_does_not_substitute_for_standard_loop_authoring(self):
        ensure_change(self.root, task=self.task, allow_primary=True)
        self.assertEqual("succeeded", self.call_capability("concorde-review", {
            **self.task, "task": "Inspect a separate possible use", "review_mode": "spec"})["status"])
        result = self.call_capability("concorde-dev-loop")
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("specify", self.model.calls[0]["stage"])

    @verifies("scenario.development.dev-loop-spec-gap")
    def test_rejected_authoring_preserves_gaps_until_the_host_accepts_the_repair(self):
        result = self.call_capability("concorde-specify", callback=self.missing("specify"))
        self.assertEqual("blocked", result["status"], result)
        original = (self.root / "specs/transfer/module.md").read_bytes()
        gap = read_change(self.root)["gap_history"][0]
        def invalid(stage, snapshot, data, cwd):
            data["documents"] = [{"path": "specs/transfer/module.md", "content": "Missing document declaration"}]
        result = self.call_capability("concorde-specify", callback=invalid)
        self.assertNotEqual("succeeded", result["status"], result)
        state = read_change(self.root)
        self.assertEqual(gap, state["gap_history"][0])
        self.assertEqual([gap["gap"]], state["gaps"])
        self.assertEqual(original, (self.root / "specs/transfer/module.md").read_bytes())
        def repair(stage, snapshot, data, cwd):
            data["documents"] = [{"path": "specs/transfer/module.md", "content": original.decode() + "\nThe daily-limit owner is transfer.\n"}]
        self.assertEqual("succeeded", self.call_capability("concorde-specify", callback=repair)["status"])
        self.assertEqual("resolved", read_change(self.root)["gap_history"][0]["status"])

    @verifies("scenario.development.dev-loop-spec-gap")
    def test_rejected_plan_tasks_and_implementation_cannot_resolve_previous_gaps(self):
        for phase in ("plan", "tasks", "implementation"):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                previous_root = self.root
                self.root = Path(directory)
                try:
                    project(self.root)
                    self.assertEqual("blocked", self.call_capability("concorde-dev-loop",
                        callback=self.missing(phase))["status"])
                    spec = self.root / "specs/transfer/module.md"
                    spec.write_text(spec.read_text() + "\nThe daily-limit owner is transfer.\n")
                    def invalid(stage, snapshot, data, cwd):
                        if stage == phase:
                            data["plan" if phase == "plan" else "tasks"] = "" if phase == "plan" else []
                    result = self.call_capability("concorde-dev-loop", callback=invalid)
                    self.assertNotEqual("succeeded", result["status"], result)
                    self.assertEqual("open", read_change(self.root)["gap_history"][0]["status"])
                    self.assertTrue(read_change(self.root)["gaps"])
                    self.assertEqual("succeeded", self.call_capability("concorde-dev-loop")["status"])
                    self.assertEqual("resolved", read_change(self.root)["gap_history"][0]["status"])
                finally:
                    self.root = previous_root

    @verifies("scenario.development.dev-loop-spec-gap")
    def test_failed_plan_artifact_write_can_resume_and_resolve_the_planning_gap(self):
        from concorde.development import capability_host
        self.assertEqual("blocked", self.call_capability("concorde-dev-loop",
            callback=self.missing("plan"))["status"])
        spec = self.root / "specs/transfer/module.md"
        spec.write_text(spec.read_text() + "\nThe daily-limit owner is transfer.\n")
        original_apply = capability_host.apply_files
        def reject_plan(root, changes, allowed, **kwargs):
            if any(item["path"].endswith("/plan.md") for item in changes):
                raise OSError("fixture plan directory cannot be written")
            return original_apply(root, changes, allowed, **kwargs)
        with patch.object(capability_host, "apply_files", side_effect=reject_plan):
            self.assertNotEqual("succeeded", self.call_capability("concorde-dev-loop")["status"])
        self.assertEqual("open", read_change(self.root)["gap_history"][0]["status"])
        resumed = self.call_capability("concorde-dev-loop")
        self.assertEqual("succeeded", resumed["status"], resumed)
        self.assertIn("plan", [call["stage"] for call in self.model.calls])
        self.assertEqual("resolved", read_change(self.root)["gap_history"][0]["status"])

    def test_gap_capture_is_explicit_deduplicated_and_keeps_owner_and_blocker(self):
        result = self.call_capability("concorde-plan", callback=self.missing("context-solve"))
        self.assertEqual("blocked", result["status"])
        status = self.call_capability("concorde-reflections-triage", {**self.task, "action": "status", "reflection_ids": []})
        self.assertEqual("succeeded", status["status"], status)
        gap = status["output"]["data"]["gap_records"][0]
        self.assertEqual("open", gap["status"])
        self.assertIsNone(gap["reflection_id"])
        request = {**self.task, "action": "record-gaps", "reflection_ids": [], "gap_ids": [gap["id"]]}
        result = self.call_capability("concorde-reflections-triage", request)
        self.assertEqual("succeeded", result["status"], result)
        reflection = result["output"]["data"]["reflections"][0]
        self.assertEqual("service.transfer", reflection["target_id"])
        self.assertEqual("open", read_change(self.root)["gap_history"][0]["status"])
        self.assertEqual([], self.model.calls)
        repeated = self.call_capability("concorde-reflections-triage", request)
        self.assertEqual(reflection["id"], repeated["output"]["data"]["reflections"][0]["id"])
        self.assertEqual(1, len(list((self.root / ".concorde/reflections/pending").glob("R-*.md"))))
        rejected = self.call_capability("concorde-reflections-triage", {**request, "target_id": "module.ledger"})
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

    def call_capability(self, capability, data=None, callback=None, *, mode="execute", double=None):
        self.model = double or self.double(callback)
        self.host = CapabilityHost(self.root, PACKAGE, executor=self.model.executor,
            allow_primary_worktree=True, mode=mode, routed_target=(data or self.task)["target_id"])
        return run_capability(capability, self.configuration, typed(capability + "-request", data or self.task),
                             host_context=self.host)

    @staticmethod
    def finding(problem="A required daily-limit check is missing.", finding_id="daily-limit-check"):
        return {"id": finding_id, "severity": "blocking", "target_id": "service.transfer",
                "document": "specs/transfer/module.md", "contract": "Pure transfer",
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

    @verifies("scenario.development.task-history-identities", "scenario.development.dev-loop-repair")
    def test_code_review_repair_reserves_current_ids_before_archiving_them(self):
        def callback(stage, snapshot, data, cwd):
            if stage == "code-review":
                data.update(status="findings", findings=[self.finding()], gaps=[])
            if stage == "tasks":
                values = {v["type_id"]: v["data"] for v in snapshot["stage_inputs"]}
                reserved = values["concorde-task-identity-constraints"]["reserved_task_ids"]
                self.assertEqual(["task.transfer"] if "concorde-review-result" in values else [], reserved)
                # The unchanged process-double result deliberately reuses task.transfer.
        rejected = self.call_capability("concorde-dev-loop", callback=callback)
        self.assertEqual("child_blocked", rejected["errors"][0]["code"], rejected)
        errors = json.loads(rejected["errors"][0]["message"].split("concorde-tasks blocked: ", 1)[1])
        self.assertEqual("invalid_completion", errors[0]["code"])
        self.assertIn("task.transfer", errors[0]["message"])
        change = read_change(self.root)
        state = change["targets"]["service.transfer"]
        self.assertEqual([], state.get("task_history", []))
        self.assertTrue(all(t["complete"] for t in state["tasks"]))
        self.assertIsNotNone(change["graph"]["service.transfer"]["repair"])
        self.assertEqual(1, [c["stage"] for c in self.model.calls].count("implementation"))

    @verifies("scenario.development.dev-loop-repair")
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
        result = self.call_capability("concorde-dev-loop", callback=callback)
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
        self.assertEqual("model-driven", repairs[0]["source"])
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
        result = self.call_capability("concorde-dev-loop", callback=callback)
        self.assertEqual("blocked", result["status"], result)
        return result

    @verifies("scenario.development.dev-loop-repair-exhausted")
    def test_unchanged_blocking_feedback_stops_waiting_after_one_repair(self):
        result = self._reach_unchanged_feedback_waiting()
        self.assertEqual("conflicting", result["output"]["data"]["outcome"])
        self.assertEqual("waiting", read_change(self.root)["status"])
        stages = [c["stage"] for c in self.model.calls]
        self.assertEqual(2, stages.count("implementation"))
        self.assertEqual(2, stages.count("code-review"))

    @verifies("scenario.development.dev-loop-repair", "scenario.development.dev-loop-repair-exhausted")
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
        result = self.call_capability("concorde-dev-loop", callback=callback)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("conflicting", result["output"]["data"]["outcome"])
        state = read_change(self.root)
        self.assertEqual("limit_exhausted", state["status"])
        stages = [c["stage"] for c in self.model.calls]
        self.assertEqual(3, stages.count("implementation"))
        self.assertEqual(3, stages.count("code-review"))
        self.assertEqual(2, state["graph"]["service.transfer"]["repair_iteration"])
        self.assertEqual(2, state["graph"]["service.transfer"]["policy"]["max_repair_iterations"])

    @verifies("scenario.development.dev-loop-spec-gap")
    def test_spec_gap_in_spec_review_stops_waiting_before_planning(self):
        def callback(stage, snapshot, data, cwd):
            if stage == "spec-review":
                data.update(status="findings", gaps=[{
                    "question": "Who owns the daily limit?", "blocked_step": "Decide daily-limit admission",
                    "needed_contract": "The transfer daily-limit owner and admission rule"}],
                    findings=[{"id": "missing-limit", "severity": "blocking", "target_id": snapshot["target_id"],
                        "document": "specs/transfer/module.md",
                        "contract": "The transfer daily-limit owner and admission rule",
                        "location": {"path": "specs/transfer/module.md", "line": 12},
                        "problem": "A required daily-limit promise is absent.",
                        "affected_task": "Decide daily-limit admission"}])
        result = self.call_capability("concorde-dev-loop", callback=callback)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("spec_incomplete", result["output"]["data"]["outcome"])
        self.assertEqual("waiting", read_change(self.root)["status"])
        self.assertNotIn("plan", [c["stage"] for c in self.model.calls])

    def test_admitted_specify_spec_change_does_not_spuriously_reset_the_graph_record(self):
        def callback(stage, snapshot, data, cwd):
            if stage == "specify" and snapshot["target_id"] == "service.transfer":
                document = next(d for d in snapshot["target_spec"] if d["path"] == "specs/transfer/module.md")
                data["documents"] = [{"path": "specs/transfer/module.md",
                    "content": document["content"] + "\nThe transfer capability documents an additional promise.\n"}]
        result = self.call_capability("concorde-dev-loop", callback=callback)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        self.assertIn("The transfer capability documents an additional promise.",
                      (self.root / "specs/transfer/module.md").read_text())
        self.assertEqual([], read_change(self.root)["graph"]["service.transfer"]["transitions"])
        # A second dev-loop resumes without re-authoring; the first run's own admitted Spec change
        # must not be mistaken for an out-of-band human edit and spuriously reset the record.
        second = self.call_capability("concorde-dev-loop")
        self.assertEqual("succeeded", second["status"], second)
        self.assertNotIn("specify", [c["stage"] for c in self.model.calls])
        record = read_change(self.root)["graph"]["service.transfer"]
        self.assertEqual([], [t for t in record["transitions"] if t["trigger"] == "human"])
        # A genuinely human Spec edit between runs still resets the record.
        spec = self.root / "specs/transfer/module.md"
        spec.write_text(spec.read_text() + "\nA human directly edited this Spec.\n")
        third = self.call_capability("concorde-dev-loop")
        self.assertEqual("succeeded", third["status"], third)
        record = read_change(self.root)["graph"]["service.transfer"]
        human_transitions = [t for t in record["transitions"] if t["trigger"] == "human"]
        self.assertEqual(1, len(human_transitions))
        self.assertEqual("spec_changed", human_transitions[0]["outcome"])

    @verifies("scenario.development.dev-loop-repair-exhausted")
    def test_human_implementation_edit_resets_the_repair_record(self):
        self._reach_unchanged_feedback_waiting()
        before = read_change(self.root)
        self.assertEqual(1, before["graph"]["service.transfer"]["repair_iteration"])
        code = self.root / "app/transfer.py"
        code.write_text(code.read_text() + "\n# a human edited this directly\n")
        result = self.call_capability("concorde-dev-loop")
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        record = read_change(self.root)["graph"]["service.transfer"]
        self.assertEqual(0, record["repair_iteration"])
        human_transitions = [t for t in record["transitions"] if t["trigger"] == "human"]
        self.assertEqual(1, len(human_transitions))
        self.assertEqual("implementation_changed", human_transitions[0]["outcome"])

    def test_capability_execution_error_during_standalone_code_review_maps_to_execution_limit(self):
        from concorde.harness.agent_executor import CapabilityExecutionError
        from concorde.harness.change_worktree import ensure_change
        ensure_change(self.root, task=self.task, allow_primary=True)
        double = self.double()
        def fail(launch):
            raise CapabilityExecutionError(
                "codex process exceeded the Harness loop limit of 10s", None, outcome="limit_exhausted")
        double.executor = fail
        result = self.call_capability("concorde-review", {**self.task, "review_mode": "code"}, double=double)
        self.assertEqual("failed", result["status"], result)
        reviewed = result["output"]["data"]["reviews"][0]["data"]
        self.assertEqual("incomplete", reviewed["status"])
        reference = result["output"]["data"]["artifacts"][0]
        private = json.loads((self.root / reference["path"]).with_suffix(".execution.json").read_text())
        self.assertEqual("execution_limit", private["failure"]["code"])
        self.assertIsNone(private["execution"])
        self.assertEqual("limit_exhausted", read_change(self.root)["status"])
