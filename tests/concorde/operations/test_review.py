"""Review mechanism tests. Process doubles do not measure semantic detection quality."""

import json
import subprocess
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch

from concorde.harness.admission import run_operation
from concorde.harness.change_worktree import (
    WORK_PATH,
    ensure_change,
    bind_owner,
    read_change,
    save_change,
)
from tests.concorde.support.native_planning import OperationHost
from concorde.harness.invocation import Invocation
from concorde.harness.permissions import PermissionPolicyError
from concorde.review.review import current, inputs
from concorde.spec.typed_data import DATA_SCHEMAS, typed
from concorde.spec.verification import verifies
from tests.concorde.spec.support import (
    CONFIGURATION,
    PACKAGE,
    ModelProcessDouble,
    project,
    update_document_declaration,
)


def issue_observation(root, reference):
    from concorde.issues.references import receipt
    from concorde.issues.store import resolve_report

    return resolve_report(root, receipt(reference))


class ReviewTests(unittest.TestCase):
    @verifies("scenario.harness.graph-execution")
    def test_interrupted_review_reports_status_persistence_failure(self):
        from concorde.harness.worker_executor import OperationExecutionError

        ensure_change(self.root, task=self.task, allow_primary=True)
        bind_owner(self.root, self.task)
        before = read_change(self.root, required=True)
        double = self.double()
        execute = double.executor

        def interrupted(invocation, **options):
            if invocation.stage == "spec-review":
                raise OperationExecutionError(
                    "controlled interruption", outcome="cancelled"
                )
            return execute(invocation, **options)

        double.executor = interrupted
        with patch(
            "concorde.review.review.progress", side_effect=OSError("cannot save")
        ):
            result = self.review("spec", double=double)
        # The failed Review result and its incomplete report survive the lost status write,
        # which is reported beside them rather than replacing them.
        self.assertEqual("failed", result["status"], result)
        self.assertEqual("concorde-spec-review-response", result["output"]["type_id"])
        data = result["output"]["data"]
        self.assertEqual("failed", data["outcome"])
        self.assertEqual(
            ["incomplete"], [review["data"]["status"] for review in data["reviews"]]
        )
        self.assertIn("execution_cancelled", data["reviews"][0]["data"]["answer"])
        self.assertTrue(data["artifacts"])
        execution = json.loads(
            (self.root / data["artifacts"][0]["path"])
            .with_suffix(".execution.json")
            .read_text()
        )
        self.assertEqual("execution_cancelled", execution["failure"]["code"])
        self.assertIn("cannot save", execution["failure"]["persistence"])
        self.assertIn(
            "state_persistence_failed", [item["code"] for item in result["errors"]]
        )
        self.assertIn(
            "execution_cancelled", [item["code"] for item in result["errors"]]
        )
        self.assertEqual(
            before["status"], read_change(self.root, required=True)["status"]
        )

    @verifies("scenario.harness.graph-execution")
    def test_fresh_review_reconciles_removed_members_and_restores_required_currentness(
        self,
    ):
        from concorde.harness.worker_executor import OperationExecutionError
        from concorde.review.review import require_reviews, verify_required
        from concorde.spec.initialize import empty_target
        from concorde.spec.repository import SpecError
        from tests.concorde.spec.support import module_document, write_document

        for mode in ("code", "spec"):
            with self.subTest(mode=mode):
                fixture = ReviewTests()
                fixture.setUp()
                try:
                    path = fixture.root / ".concorde/specs.json"
                    registry = json.loads(path.read_text())
                    for name in ("first", "second"):
                        target_id = "module." + name
                        document = "specs/" + name + "/module.md"
                        peer = empty_target(target_id, "module", name, [document])
                        peer["files"] = ["app/transfer.py"]
                        if mode == "spec":
                            peer["references"] = [
                                {"kind": "module", "id": "service.transfer"}
                            ]
                        registry["targets"].append(peer)
                        file = fixture.root / document
                        file.parent.mkdir()
                        write_document(
                            fixture.root,
                            document,
                            module_document(
                                "document." + name,
                                target_id,
                                name,
                                "Observe the shared transfer calculation.",
                                "### scenario." + name + ".read — Read the result\n\n"
                                "- GIVEN a valid transfer\n- WHEN its result is read\n- THEN the remaining balance is returned\n",
                                (
                                    "The shared calculation supplies the result.",
                                    [
                                        {
                                            "id": "entity." + name + ".shared",
                                            "title": "Shared calculation",
                                            "kind": "function",
                                            "responsibility": "Compute the remaining balance.",
                                            "files": ["app/transfer.py"],
                                        }
                                    ],
                                ),
                                "",
                                'flowchart TB\n    shared["Shared calculation"]',
                            ),
                        )
                    path.write_text(json.dumps(registry))
                    planned = fixture.call_operation("concorde-plan")
                    self.assertEqual("succeeded", planned["status"], planned)
                    require_reviews(fixture.invocation(), True, modes=[mode])
                    first = fixture.review(mode)
                    self.assertEqual("succeeded", first["status"], first)
                    verify_required(fixture.invocation())
                    field = (
                        "shared_spec_reviews"
                        if mode == "spec"
                        else "shared_implementation_reviews"
                    )
                    original = read_change(fixture.root, required=True)[field][
                        "service.transfer"
                    ]
                    self.assertEqual({"module.first", "module.second"}, set(original))
                    artifacts = {
                        r["artifact"]["path"]: (
                            fixture.root / r["artifact"]["path"]
                        ).read_bytes()
                        for r in original.values()
                    }
                    # Change real fixture membership, first leaving one peer and then none.
                    # Spec removal removes the Module identity; live old-impact consumers
                    # must continue to be required when only a reference is removed.
                    for removed, remaining in (
                        ("first", {"module.second"}),
                        ("second", set()),
                    ):
                        registry = json.loads(path.read_text())
                        peer = next(
                            t
                            for t in registry["targets"]
                            if t["id"] == "module." + removed
                        )
                        document = fixture.root / peer["documents"][0]
                        if mode == "spec":
                            registry["targets"].remove(peer)
                            document.unlink()
                            Path(str(document) + ".json").unlink()
                        else:
                            peer["files"] = []
                            metadata_path = Path(str(document) + ".json")
                            metadata = json.loads(metadata_path.read_text())
                            for entity in metadata["entities"]:
                                entity.pop("files", None)
                                entity.pop("pending", None)
                            metadata_path.write_text(json.dumps(metadata))
                        path.write_text(json.dumps(registry))
                        with self.assertRaises(SpecError):
                            verify_required(fixture.invocation())
                        before = read_change(fixture.root, required=True)[field][
                            "service.transfer"
                        ]
                        double = fixture.double()
                        execute = double.executor

                        def interrupt(invocation, **options):
                            if invocation.stage == mode + "-review":
                                raise OperationExecutionError(
                                    "controlled stop", outcome="cancelled"
                                )
                            return execute(invocation, **options)

                        double.executor = interrupt
                        stopped = fixture.review(mode, double=double)
                        self.assertEqual("failed", stopped["status"], stopped)
                        retained = read_change(fixture.root, required=True)[field][
                            "service.transfer"
                        ]
                        self.assertEqual(remaining, set(retained))
                        for key in remaining:
                            self.assertEqual(before[key], retained[key])
                        with self.assertRaises(SpecError):
                            verify_required(fixture.invocation())
                        fresh = fixture.review(mode)
                        self.assertEqual("succeeded", fresh["status"], fresh)
                        verify_required(fixture.invocation())
                        self.assertEqual(
                            remaining,
                            set(
                                read_change(fixture.root, required=True)[field][
                                    "service.transfer"
                                ]
                            ),
                        )
                        self.assertTrue(
                            all(
                                (fixture.root / p).read_bytes() == data
                                for p, data in artifacts.items()
                            )
                        )
                finally:
                    fixture.doCleanups()

    @verifies("scenario.harness.graph-execution")
    def test_scope_scheduler_change_invalidates_accepted_review(self):
        from concorde.review import review
        from concorde.spec.repository import SpecError

        ensure_change(self.root, task=self.task, allow_primary=True)
        bind_owner(self.root, self.task)
        schedulers = (
            "src/concorde/review/review.py",
            "src/concorde/operations/dispatch.py",
            "src/concorde/operations/dispatch_graph.py",
        )
        for mode in ("spec", "code"):
            result = self.review(mode)
            self.assertEqual("succeeded", result["status"], result)
            run = self.invocation()
            # This consumer binds application code, not the Framework scheduler.
            self.assertTrue(
                set(schedulers).isdisjoint(
                    run.repository.implementation_files(run.target)
                )
            )
            before, _ = inputs(run, mode)
            accepted = current(run, mode, required=True)
            self.assertIsNotNone(accepted)
            original = review.read_file
            for scheduler in schedulers:
                with self.subTest(mode=mode, scheduler=scheduler):

                    def changed(root, path):
                        data = original(root, path)
                        return (
                            data + b"\n# scheduling revision\n"
                            if root == run.host.package_root and path == scheduler
                            else data
                        )

                    # Vary one runtime source's observed bytes without changing the
                    # package, its generated binding, or the consumer's sources.
                    with patch.object(review, "read_file", side_effect=changed):
                        after, _ = inputs(run, mode)
                        self.assertNotEqual(
                            before["input_digest"], after["input_digest"]
                        )
                        self.assertEqual(before["revision"], after["revision"])
                        self.assertEqual(before["changes"], after["changes"])
                        self.assertIsNone(current(run, mode))
                        with self.assertRaises(SpecError) as failure:
                            current(run, mode, required=True)
                        self.assertEqual("review_required", failure.exception.code)
                    # Rejection preserves the accepted artifact; identical inputs
                    # remain eligible for reuse after each independent variation.
                    self.assertEqual(before, inputs(run, mode)[0])
                    self.assertEqual(accepted, current(run, mode, required=True))

    @verifies("scenario.harness.graph-execution")
    def test_reviewer_interruptions_survive_enclosing_graphs_and_final_events(self):
        from concorde.harness.worker_executor import OperationExecutionError

        for mode in ("spec", "code"):
            for outcome in ("cancelled", "limit_exhausted", "failed"):
                with self.subTest(mode=mode, outcome=outcome):
                    ensure_change(self.root, task=self.task, allow_primary=True)
                    bind_owner(self.root, self.task)
                    before = read_change(self.root, required=True)
                    contents = {
                        p: p.read_bytes()
                        for p in (self.root / "specs").rglob("*")
                        if p.is_file()
                    }
                    double = self.double()

                    def interrupted(invocation, **options):
                        raise OperationExecutionError(
                            "controlled reviewer failure", outcome=outcome
                        )

                    double.executor = interrupted
                    events = []

                    def observe(host, event, **details):
                        events.append({"event": event, **details})

                    with patch.object(OperationHost, "observe", observe):
                        result = self.review(mode, double=double)
                    self.assertEqual("failed", result["status"], result)
                    self.assertEqual(
                        "incomplete",
                        result["output"]["data"]["reviews"][0]["data"]["status"],
                    )
                    after = read_change(self.root, required=True)
                    self.assertEqual(outcome, after["status"])
                    self.assertEqual(before["targets"], after["targets"])
                    self.assertEqual(contents, {p: p.read_bytes() for p in contents})
                    self.assertEqual(
                        outcome,
                        [e for e in events if e["event"] == "operation_finished"][-1][
                            "status"
                        ],
                    )
                    self.assertTrue(
                        after["review_requirements"][self.task["target_id"]][mode]
                    )

    @verifies(
        "scenario.issues.blocker-history",
        "scenario.review.standalone",
    )
    def test_lifecycle_only_standalone_review_cannot_resolve_a_required_gap(self):
        ensure_change(self.root, task=self.task, allow_primary=True)
        bind_owner(self.root, self.task)
        first = self.call_operation(
            "concorde-spec-review", callback=self.missing("spec-review")
        )
        self.assertEqual("blocked", first["status"], first)
        original = read_change(self.root, required=True)["issue_blockers"][0]
        self.assertIn("review_input_digest", original)
        reviewed = self.review()
        self.assertEqual("succeeded", reviewed["status"], reviewed)
        actual = reviewed["output"]["data"]["reviews"][0]["data"]
        self.assertEqual(original["review_input_digest"], actual["input_digest"])
        self.assertNotEqual(
            issue_observation(self.root, original["blocker"])["source"]["context_id"],
            actual["context_id"],
        )
        self.assertEqual(
            original, read_change(self.root, required=True)["issue_blockers"][0]
        )
        resumed = self.call_operation("concorde-plan")
        self.assertNotEqual("succeeded", resumed["status"], resumed)
        self.assertFalse(
            any(call["stage"] == "spec-review" for call in self.model.calls)
        )

    @verifies("scenario.issues.blocker-history")
    def test_legacy_gap_identity_is_not_inferred_from_a_later_review(self):
        ensure_change(self.root, task=self.task, allow_primary=True)
        bind_owner(self.root, self.task)
        self.call_operation(
            "concorde-spec-review", callback=self.missing("spec-review")
        )
        state = read_change(self.root, required=True)
        state["issue_blockers"][0].pop("review_input_digest")
        save_change(self.root, state)  # legacy fixture, not a production migration
        original = read_change(self.root, required=True)["issue_blockers"][0]
        self.review()
        self.assertEqual(
            original, read_change(self.root, required=True)["issue_blockers"][0]
        )
        document = self.root / "specs/transfer/module.md"
        document.write_text(
            document.read_text() + "\nTransfer owns the requested admission rule.\n"
        )
        self.assertEqual("succeeded", self.review()["status"])
        result = self.call_operation("concorde-plan")
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual(
            "resolved",
            read_change(self.root, required=True)["issue_blockers"][0]["status"],
        )

    @verifies("scenario.planning.task-history-identities")
    @verifies("scenario.planning.tasks-id-conflict")
    @verifies("scenario.planning.tasks-from-plan")
    def test_replan_author_sees_all_retained_ids_and_collision_is_rejected_without_rewriting(
        self,
    ):
        from concorde.spec.repository import digest

        self.assertEqual("succeeded", self.call_operation("concorde-plan")["status"])
        for index in range(3):
            state = read_change(self.root, required=True)["targets"][
                self.task["target_id"]
            ]
            request = dict(self.task)
            if index:
                request["repair_task_scope"] = {"tasks_digest": digest(state["tasks"])}

            def author(stage, snapshot, data, cwd):
                values = {v["type_id"]: v["data"] for v in snapshot["stage_inputs"]}
                self.assertEqual(
                    [f"task.round.{i}" for i in range(index)],
                    values["concorde-task-identity-constraints"]["reserved_task_ids"],
                )
                self.assertEqual([], snapshot["implementation_artifacts"])
                data["tasks"][0]["id"] = f"task.round.{index}"

            self.assertEqual(
                "succeeded",
                self.call_operation("concorde-tasks", request, callback=author)[
                    "status"
                ],
            )
        document = self.root / "specs/transfer/module.md"
        document.write_text(document.read_text() + "\n")
        self.assertEqual("succeeded", self.call_operation("concorde-plan")["status"])
        before = read_change(self.root, required=True)["targets"][
            self.task["target_id"]
        ]

        def collide(stage, snapshot, data, cwd):
            values = {v["type_id"]: v["data"] for v in snapshot["stage_inputs"]}
            self.assertEqual(
                ["task.round.0", "task.round.1", "task.round.2"],
                values["concorde-task-identity-constraints"]["reserved_task_ids"],
            )
            self.assertNotIn("concorde-implementation-task", values)
            data["tasks"][0]["id"] = "task.round.0"

        rejected = self.call_operation("concorde-tasks", callback=collide)
        self.assertEqual("invalid_completion", rejected["errors"][0]["code"], rejected)
        self.assertIn("task.round.0", rejected["errors"][0]["message"])
        self.assertEqual(
            before,
            read_change(self.root, required=True)["targets"][self.task["target_id"]],
        )

    @verifies("scenario.validation.blocked")
    def test_deferred_repository_verification_still_requires_passing_host_checks(self):
        # The programmer cannot read this repository-level dependency, but the Host must
        # still execute it after accepting the implementation's fulfilled tasks.
        (self.root / "host_regression.py").write_text(
            "raise AssertionError('repository regression')\n"
        )
        (self.root / "checks/transfer_check.py").write_text(
            "import runpy\nrunpy.run_path('host_regression.py')\n"
        )

        def deferred(stage, snapshot, data, cwd):
            if stage == "implementation":
                data["answer"] = (
                    "Implementation fulfilled; repository imports require deferred Host verification."
                )
                self.assertNotIn(
                    "host_regression.py",
                    [item["path"] for item in snapshot["implementation_files"]],
                )

        self.call_operation("concorde-plan")
        self.call_operation("concorde-tasks")
        self.call_operation("concorde-implement", callback=deferred)
        result = self.call_operation("concorde-validate")
        self.assertNotEqual("succeeded", result["status"], result)
        state = read_change(self.root, required=True)
        target = state["targets"]["service.transfer"]
        self.assertTrue(all(task["complete"] for task in target["tasks"]))
        self.assertIsNotNone(target["implementation_digest"])
        self.assertNotEqual("ready", state["status"])
        self.assertIsNone(state.get("validated_tree"))
        self.assertTrue(any(check["status"] == "failed" for check in target["checks"]))
        self.assertNotIn("code-review", [call["stage"] for call in self.model.calls])

    @verifies("scenario.harness.pi-worker-launch")
    def test_only_project_workers_receive_the_host_check_service(self):
        model = self.double()
        for operation in ("plan", "tasks", "implement", "spec-review", "code-review"):
            result = self.call_operation("concorde-" + operation, double=model)
            self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("succeeded", result["status"], result)
        for call in model.calls:
            with self.subTest(stage=call["stage"]):
                if call["stage"] in {"implementation", "code-review"}:
                    self.assertIn("run_checks", call["launch"].tools)
                    report = call["checks"]()
                    self.assertEqual(
                        ["check.transfer"],
                        [item["check_id"] for item in report["checks"]],
                    )
                    self.assertIn("output_tail", report["checks"][0])
                else:
                    self.assertIsNone(call["checks"])
                    self.assertNotIn("run_checks", call["launch"].tools)

    @verifies("scenario.harness.worker-selection")
    def test_each_worker_launches_on_its_own_model_and_thinking_level(self):
        self.configuration = typed(
            "concorde-operation-configuration",
            {
                "model": "openai-codex/gpt-6-astra",
                "thinking": "medium",
                "workers": {
                    "task_author": {"thinking": "high"},
                    "planner": {
                        "model": "anthropic/claude-sonnet-5",
                        "thinking": "low",
                    },
                    "programmer": {
                        "model": "openai-codex/gpt-5.6-sol",
                        "timeout_seconds": 5400,
                    },
                },
            },
        )
        config_path = self.root / ".concorde/config.json"
        config = json.loads(config_path.read_text())
        config["operation_configuration"] = self.configuration
        config_path.write_text(json.dumps(config))
        model = self.double()
        for operation in ("plan", "tasks", "implement", "code-review"):
            result = self.call_operation("concorde-" + operation, double=model)
            self.assertEqual("succeeded", result["status"], result)
        launched = {
            call["stage"]: (call["launch"].model, call["launch"].thinking)
            for call in self.model.calls
        }
        expected = {
            "plan": ("anthropic/claude-sonnet-5", "low"),
            "tasks": ("openai-codex/gpt-6-astra", "high"),
            "implementation": ("openai-codex/gpt-5.6-sol", "medium"),
            "code-review": ("openai-codex/gpt-6-astra", "medium"),
        }
        self.assertEqual(expected, {stage: launched[stage] for stage in expected})
        programmer = next(
            call["launch"]
            for call in self.model.calls
            if call["stage"] == "implementation"
        )
        self.assertEqual(5400, programmer.timeout_seconds)
        described = {
            item["phase"]: (item["model"], item["thinking"])
            for item in self.host.descriptions
        }
        self.assertEqual(
            {stage: expected[stage] for stage in described if stage in expected},
            {stage: described[stage] for stage in expected if stage in described},
        )

    @verifies("scenario.planning.scope-repair")
    def test_invalid_scope_repair_cannot_replace_or_complete_original_tasks(self):
        from concorde.spec.repository import digest

        self.call_operation("concorde-plan")
        self.call_operation("concorde-tasks")
        before = read_change(self.root, required=True)["targets"][
            self.task["target_id"]
        ]
        request = {
            **self.task,
            "repair_task_scope": {"tasks_digest": digest(before["tasks"])},
        }
        for invalid in ("completed", "reused_id", "digest", "stale_spec"):
            with self.subTest(invalid=invalid):
                selected = dict(request)
                if invalid == "digest":
                    selected["repair_task_scope"] = {
                        "tasks_digest": "sha256:" + "0" * 64
                    }
                if invalid == "stale_spec":
                    path = self.root / "specs/transfer/module.md.json"
                    path.write_text(path.read_text() + "\n")

                def reject(stage, snapshot, data, cwd):
                    if invalid == "completed":
                        data["tasks"][0].update(id="task.repair", complete=True)

                result = self.call_operation(
                    "concorde-tasks", selected, callback=reject
                )
                self.assertNotEqual("succeeded", result["status"], result)
                if invalid == "stale_spec":
                    self.assertEqual("stale_context", result["errors"][0]["code"])
                    self.assertEqual([], self.model.calls)
                self.assertEqual(
                    before,
                    read_change(self.root, required=True)["targets"][
                        self.task["target_id"]
                    ],
                )

    @verifies("scenario.planning.scope-repair")
    @verifies("scenario.validation.ready")
    def test_incomplete_phase_tasks_repair_then_implementation_validation_review_ready(
        self,
    ):
        from concorde.spec.repository import digest

        self.call_operation("concorde-plan")

        def bad_task(stage, snapshot, data, cwd):
            data["tasks"][0]["acceptance"] += (
                " Host review and commit must finish first."
            )

        self.call_operation("concorde-tasks", callback=bad_task)

        def incomplete(stage, snapshot, data, cwd):
            for task in data["tasks"]:
                task["complete"] = False

        first = self.call_operation("concorde-implement", callback=incomplete)
        self.assertEqual("incomplete_tasks", first["errors"][0]["code"], first)
        original = read_change(self.root, required=True)["targets"][
            self.task["target_id"]
        ]["tasks"]
        request = {**self.task, "repair_task_scope": {"tasks_digest": digest(original)}}

        def repair(stage, snapshot, data, cwd):
            values = {v["type_id"]: v["data"] for v in snapshot["stage_inputs"]}
            self.assertEqual(
                "implementation_boundary",
                values["concorde-task-scope-feedback"]["reason"],
            )
            self.assertEqual(original, values["concorde-implementation-task"]["tasks"])
            self.assertEqual([], snapshot["implementation_artifacts"])
            data["tasks"][0]["id"] += ".scope-repair"

        repaired = self.call_operation("concorde-tasks", request, callback=repair)
        self.assertEqual("succeeded", repaired["status"], repaired)
        for operation in (
            "concorde-implement",
            "concorde-spec-review",
            "concorde-code-review",
            "concorde-validate",
        ):
            result = self.call_operation(operation)
            self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        state = read_change(self.root, required=True)
        self.assertEqual(
            original,
            state["targets"][self.task["target_id"]]["task_history"][0]["tasks"],
        )
        self.assertEqual(
            {"spec": True, "code": True},
            state["review_requirements"][self.task["target_id"]],
        )
        replay = self.call_operation("concorde-tasks", request)
        self.assertEqual("incompatible_handoff", replay["errors"][0]["code"], replay)
        self.assertEqual([], self.model.calls)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.registry = project(self.root)
        self.configuration = CONFIGURATION
        self.task = {
            "target_id": "service.transfer",
            "task": "Implement the pure transfer contract",
        }

    def double(self, callback=None):
        double = ModelProcessDouble(callback)
        return double

    def call_operation(
        self, operation, data=None, callback=None, *, mode="execute", double=None
    ):
        self.model = double or self.double(callback)
        self.host = OperationHost(
            self.root,
            PACKAGE,
            executor=self.model.executor,
            allow_primary_worktree=True,
            mode=mode,
        )
        return run_operation(
            operation,
            self.configuration,
            typed(operation + "-request", data or self.task),
            host_context=self.host,
        )

    def review(self, review_mode="spec", callback=None, **kwargs):
        return self.call_operation(
            f"concorde-{review_mode}-review",
            dict(self.task),
            callback,
            **kwargs,
        )

    def invocation(self):
        return Invocation(
            "concorde-spec-review",
            self.configuration,
            self.task,
            OperationHost(self.root, PACKAGE),
        )

    def commit_fixture(self):
        for args in [
            ("init",),
            ("add", "."),
            (
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-m",
                "Fixture baseline",
            ),
        ]:
            subprocess.run(
                ("git", *args), cwd=self.root, capture_output=True, check=True
            )

    @staticmethod
    def gap():
        return {
            "question": "Who owns the necessary daily limit?",
            "blocked_step": "Decide daily-limit admission",
            "needed_contract": "The transfer daily-limit owner and admission rule",
        }

    def missing(self, phase):
        def callback(stage, snapshot, data, cwd):
            if stage != phase:
                return
            if phase.endswith("review"):
                data.update(
                    status="findings",
                    blockers=[self.gap()],
                    issues=[
                        {
                            "id": "missing-limit",
                            "severity": "blocking",
                            "target_id": snapshot["target_id"],
                            "document": "specs/transfer/module.md",
                            "contract": self.gap()["needed_contract"],
                            "location": {
                                "path": "specs/transfer/module.md",
                                "line": 12,
                            },
                            "problem": "A required daily-limit promise is absent.",
                            "affected_task": self.gap()["blocked_step"],
                        }
                    ],
                )
            else:
                data.update(outcome="spec_incomplete", blockers=[self.gap()])

        return callback

    @verifies("scenario.harness.execute-operation")
    def test_modes_use_full_collection_fresh_sessions_and_no_write_grants(self):
        self.registry["targets"][3]["references"].append(
            {"kind": "document", "id": "document.transfer.promises"}
        )
        (self.root / ".concorde/specs.json").write_text(json.dumps(self.registry))
        update_document_declaration(
            self.root, "specs/transfer/promises.md", owner="service.transfer"
        )
        calls, identities = [], []
        for mode in ("code", "spec"):
            result = self.review(mode)
            self.assertEqual("succeeded", result["status"], result)
            calls.append(self.model.calls[0])
            identities.append(self.host.evidence[0].invocation_digest)
            policy = self.host.descriptions[0]
            self.assertEqual([], policy["write_paths"])
            self.assertFalse(policy["network"])
            self.assertTrue(policy["fresh_session"])
            snapshot = calls[-1]["snapshot"]
            self.assertEqual(
                [
                    "specs/transfer/module.md",
                    "specs/transfer/module.md.json",
                    "specs/transfer/obligations.md",
                    "specs/transfer/obligations.md.json",
                    "specs/transfer/promises.md",
                    "specs/transfer/promises.md.json",
                ],
                [source["path"] for source in snapshot["spec_resolution"]["sources"]],
            )
            self.assertEqual(
                ["specs/transfer/promises.md"],
                [
                    x["path"]
                    for x in snapshot["spec_resolution"]["sources"]
                    if x["path"].endswith("promises.md")
                ],
            )
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
                # The index plus the granted Spec documents and Protocol files, never code.
                self.assertIn("context.json", policy["read_paths"])
                self.assertTrue(
                    all(
                        p == "context.json"
                        or p.startswith(("specs/", ".concorde/protocol/"))
                        for p in policy["read_paths"]
                    ),
                    policy["read_paths"],
                )
                self.assertEqual([], snapshot["implementation_artifacts"])
                self.assertNotIn("def transfer", calls[-1]["prompt"])
                # The listed file names are Spec facts; only code review reads their bytes.
                self.assertEqual(
                    ["app/transfer.py", "checks/transfer_check.py"],
                    [item["path"] for item in snapshot["implementation_files"]],
                )
        self.assertEqual(2, len(set(identities)))

    def test_diff_admits_only_current_target_paths_and_includes_untracked_and_deleted(
        self,
    ):
        self.commit_fixture()
        (self.root / "app/transfer.py").write_text("CHANGED_LOCAL_CODE\n")
        (self.root / "app/ledger.py").write_text("UNGRANTED_OTHER_CODE\n")
        (self.root / "checks/transfer_check.py").unlink()
        result = self.review("code")
        self.assertEqual("succeeded", result["status"], result)
        patches = self.model.calls[0]["review"]["changes"]
        self.assertEqual(
            {"app/transfer.py", "checks/transfer_check.py"},
            {x["path"] for x in patches},
        )
        self.assertNotIn("UNGRANTED_OTHER_CODE", json.dumps(patches))
        self.assertIn("/dev/null", patches[1]["patch"])
        self.assertNotIn("CHANGED_LOCAL_CODE", json.dumps(result))
        (self.root / "checks/transfer_check.py").write_text("NEW_LOCAL_CHECK\n")
        subprocess.run(
            ("git", "rm", "--cached", "checks/transfer_check.py"),
            cwd=self.root,
            capture_output=True,
            check=True,
        )
        result = self.review("code")
        self.assertEqual("succeeded", result["status"], result)
        self.assertIn(
            "NEW_LOCAL_CHECK", json.dumps(self.model.calls[0]["review"]["changes"])
        )

    def relist_checks_directory(self):
        """List the transfer check entity as the whole `checks/` directory instead of one file."""
        document = self.root / "specs/transfer/module.md.json"
        metadata = json.loads(document.read_text())
        for entity in metadata["entities"]:
            if entity["id"] == "entity.transfer.check":
                entity["files"] = ["checks/"]
        document.write_text(json.dumps(metadata, indent=2) + "\n")
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
        self.assertEqual(
            {"app/transfer.py", "checks/extra_check.py", "checks/transfer_check.py"},
            {item["path"] for item in review["changes"]},
        )
        self.assertNotIn("UNGRANTED_OTHER_CODE", json.dumps(review))
        self.assertNotIn(".tool.json", json.dumps(review))
        policy = self.host.descriptions[0]
        self.assertIn("checks/extra_check.py", policy["read_paths"])
        self.assertNotIn("checks/.tool.json", policy["read_paths"])
        self.assertEqual([], policy["write_paths"])
        snapshot = self.model.calls[0]["snapshot"]
        self.assertEqual(
            [("app/transfer.py", False), ("checks/", True)],
            [
                (item["path"], item["directory"])
                for item in snapshot["implementation_entries"]
            ],
        )
        self.assertEqual(
            ["app/transfer.py", "checks/extra_check.py"],
            [item["path"] for item in snapshot["implementation_files"]],
        )

    @verifies("scenario.harness.describe-policy")
    def test_describe_policy_is_not_a_completed_review(self):
        for mode in ("spec", "code"):
            result = self.review(mode, mode="describe-policy")
            self.assertEqual("described", result["status"])
            self.assertEqual(
                "not_run", result["output"]["data"]["reviews"][0]["data"]["status"]
            )
            self.assertEqual([], self.model.calls)
        self.assertFalse((self.root / ".concorde/runs").exists())

    @verifies("scenario.harness.execute-blocked-launch")
    def test_failed_policy_preview_does_not_persist_artifacts_or_change_state(self):
        # A reviewer grant the compiler refuses is simulated at policy compilation.
        ensure_change(self.root, task=self.task, allow_primary=True)
        bind_owner(self.root, self.task)
        before = read_change(self.root)
        refused = PermissionPolicyError(
            "simulated: the reviewer grant widens its declared effects"
        )
        with patch("concorde.harness.launch.compile_policy", side_effect=refused):
            for mode in ("spec", "code"):
                result = self.review(mode, mode="describe-policy")
                self.assertNotEqual("described", result["status"], result)
                self.assertEqual([], self.model.calls)
                self.assertEqual(before, read_change(self.root))
                self.assertFalse((self.root / ".concorde/runs").exists())

    def test_result_validation_rejects_false_clean_cross_scope_and_replayed_identity(
        self,
    ):
        mutations = [
            lambda d: d.update(input_digest="sha256:" + "0" * 64),
            lambda d: d.update(review_mode="code"),
            lambda d: d.update(representative_tasks=[]),
            lambda d: d.update(representative_tasks=[" "]),
            lambda d: d.update(representative_tasks=["same", "same"]),
            lambda d: d.update(blockers=[self.gap()]),
            lambda d: d.update(
                documents=[
                    {"path": "specs/transfer/module.md", "content": "replacement"}
                ]
            ),
        ]
        original = (self.root / "specs/transfer/module.md").read_bytes()
        for mutate in mutations:
            with self.subTest(mutation=mutate):

                def callback(stage, snapshot, data, cwd, mutate=mutate):
                    mutate(data)

                result = self.review(callback=callback)
                self.assertEqual("failed", result["status"], result)
                self.assertEqual(
                    "incomplete",
                    result["output"]["data"]["reviews"][0]["data"]["status"],
                )
        self.assertEqual(
            original, (self.root / "specs/transfer/module.md").read_bytes()
        )

        def foreign(stage, snapshot, data, cwd):
            self.missing("spec-review")(stage, snapshot, data, cwd)
            data["issues"][0]["document"] = "specs/ledger/module.md"

        result = self.review(callback=foreign)
        self.assertEqual("failed", result["status"])
        self.assertIn("permission_denied", result["output"]["data"]["answer"])

    def test_execution_failure_and_incomplete_coverage_are_not_no_findings(self):
        def fail(stage, snapshot, data, cwd):
            raise RuntimeError("private process failure diagnostics")

        for callback in (
            fail,
            lambda stage, snapshot, data, cwd: data.update(
                status="incomplete", representative_tasks=[]
            ),
        ):
            result = self.review(callback=callback)
            self.assertEqual("failed", result["status"], result)
            self.assertEqual(
                "incomplete", result["output"]["data"]["reviews"][0]["data"]["status"]
            )
            self.assertNotIn("private process failure diagnostics", json.dumps(result))

    def test_failed_reviews_retain_usage_and_failure_privately(self):
        from concorde.harness.worker_executor import OperationExecutionError

        double = self.double()
        executor = double.executor
        spent = []

        def fail(invocation, **options):
            outcome = executor(invocation, **options)
            spent.append(outcome.usage)
            raise OperationExecutionError(
                "private failed completion diagnostics",
                outcome="invalid_completion",
                usage=outcome.usage,
            )

        double.executor = fail
        failed = self.review(double=double)
        self.assertEqual("failed", failed["status"], failed)

        def private(result):
            path = self.root / result["output"]["data"]["artifacts"][0]["path"]
            return json.loads(path.with_suffix(".execution.json").read_text())

        self.assertEqual(asdict(spent[0]), private(failed)["usage"])
        self.assertEqual("execution_failed", private(failed)["failure"]["code"])
        rejected = self.review(
            callback=lambda stage, snapshot, data, cwd: data.update(
                input_digest="sha256:" + "0" * 64
            )
        )
        self.assertEqual("failed", rejected["status"], rejected)
        self.assertEqual(1200, private(rejected)["usage"]["input_tokens"])
        for result in (failed, rejected):
            self.assertNotIn(
                "private failed completion diagnostics", json.dumps(result)
            )
            self.assertNotIn("input_tokens", json.dumps(result))

    def test_spec_query_reports_issues_without_creating_a_change(self):
        from concorde.issues.store import list_issues

        self.assertEqual([], list_issues(self.root))
        result = self.review(callback=self.missing("spec-review"))
        self.assertEqual("blocked", result["status"])
        gap = result["output"]["data"]["blockers"][0]
        self.assertEqual(
            self.task["target_id"],
            issue_observation(self.root, gap)["source"]["target_id"],
        )
        self.assertEqual(
            result["output"]["data"]["context_id"],
            issue_observation(self.root, gap)["source"]["context_id"],
        )
        self.assertIsNone(read_change(self.root))
        self.assertEqual(1, len(list_issues(self.root)))
        self.assertEqual(gap["issue_id"], list_issues(self.root)[0]["id"])

    def test_input_change_during_review_invalidates_the_completion(self):
        def change(stage, snapshot, data, cwd):
            path = self.root / "specs/transfer/module.md"
            path.write_text(path.read_text() + "\nChanged during review.\n")

        result = self.review(callback=change)
        self.assertEqual("failed", result["status"])
        self.assertIn("stale_context", result["output"]["data"]["answer"])

        def code_change(stage, snapshot, data, cwd):
            (self.root / "app/transfer.py").write_text(
                "Modified by a deliberately invalid process double\n"
            )

        result = self.review("code", callback=code_change)
        self.assertEqual("failed", result["status"])
        self.assertIn("stale_context", result["output"]["data"]["answer"])

    @verifies("scenario.validation.ready")
    @verifies("scenario.validation.blocked")
    def test_required_reviews_surround_planning_and_follow_checks_before_ready(self):
        ensure_change(self.root, task=self.task, allow_primary=True)
        bind_owner(self.root, self.task)
        self.assertEqual("succeeded", self.review()["status"])
        for operation in ("concorde-plan", "concorde-tasks", "concorde-implement"):
            result = self.call_operation(operation)
            self.assertEqual("succeeded", result["status"], result)

        def incomplete(stage, snapshot, data, cwd):
            data.update(status="incomplete", answer="Review unfinished")

        self.assertEqual("failed", self.review("code", callback=incomplete)["status"])
        blocked = self.call_operation("concorde-validate")
        self.assertEqual("review_required", blocked["errors"][0]["code"], blocked)
        self.assertNotEqual("ready", read_change(self.root, required=True)["status"])
        self.assertEqual("succeeded", self.review("code")["status"])
        result = self.call_operation("concorde-validate")
        self.assertEqual("ready", result["output"]["data"]["outcome"], result)
        self.assertIsNotNone(current(self.invocation(), "spec"))
        self.assertIsNotNone(current(self.invocation(), "code"))

    def test_review_freshness_covers_spec_code_intent_and_artifact_integrity(self):
        self.assertEqual("succeeded", self.call_operation("concorde-plan")["status"])
        self.review("spec")
        self.review("code")
        (self.root / "app/ledger.py").write_text("Unrelated implementation\n")
        self.assertIsNotNone(current(self.invocation(), "spec"))
        self.assertIsNotNone(current(self.invocation(), "code"))
        code = self.root / "app/transfer.py"
        code.write_text(code.read_text() + "\n# changed reviewed code\n")
        self.assertIsNotNone(current(self.invocation(), "spec"))
        self.assertIsNone(current(self.invocation(), "code"))
        state = read_change(self.root, required=True)
        reference = state["reviews"][self.task["target_id"]]["spec"]["artifact"]
        path = self.root / reference["path"]
        before = path.read_text()
        value = json.loads(before)
        value["data"]["answer"] = "tampered"
        path.write_text(json.dumps(value))
        self.assertIsNone(current(self.invocation(), "spec"))
        path.write_text(before)
        invocation = self.invocation()
        invocation.task = {
            **self.task,
            "constraints": ["Changed assessment constraint"],
        }
        self.assertIsNone(current(invocation, "spec"))
        spec = self.root / "specs/transfer/module.md"
        spec.write_text(spec.read_text() + "\nChanged contract.\n")
        self.assertIsNone(current(self.invocation(), "spec"))

    @verifies("scenario.review.terminology-consistency")
    def test_spec_review_instructions_require_semantic_terminology_coverage(self):
        # This verifies the review contract and result handling, not a model's semantic accuracy.
        from concorde.distribution.build import load_model_instructions

        body = load_model_instructions(PACKAGE, "concorde-spec-reviewer").body
        for obligation in (
            "Terminology semantic consistency is a mandatory check",
            "including directly referenced documents",
            "text equality is not required",
            "scope, conditions, constraints, exceptions and obligation strength",
            "Record terminology coverage in representative_tasks",
            "If there are no imported restatements",
            "report incomplete rather than silently treating them as consistent",
        ):
            self.assertIn(obligation, body)
        self.assertIn("Allow different wording", body)
        self.assertIn("both source and local", body)
        self.assertIn("unresolved comparisons", body)

        def incomplete(stage, snapshot, data, cwd):
            if stage == "spec-review":
                data.update(
                    status="incomplete",
                    representative_tasks=["Terminology semantic consistency"],
                    answer="The canonical meaning is ambiguous; one terminology comparison is unresolved.",
                )

        result = self.review(callback=incomplete)
        self.assertEqual("failed", result["status"], result)
        self.assertEqual(
            "incomplete", result["output"]["data"]["reviews"][0]["data"]["status"]
        )

    @verifies("scenario.issues.blocker-history")
    def test_changed_review_instructions_reassess_without_erasing_gaps_on_failure(self):
        ensure_change(self.root, task=self.task, allow_primary=True)
        bind_owner(self.root, self.task)
        import hashlib
        from contextlib import contextmanager

        from concorde.distribution.build import load_model_instructions
        from concorde.harness import worker_profile
        from concorde.harness.worker_profile import binding_digest

        first = self.call_operation(
            "concorde-spec-review", callback=self.missing("spec-review")
        )
        self.assertEqual("blocked", first["status"], first)
        original = read_change(self.root, required=True)["issue_blockers"][0]
        self.call_operation("concorde-plan")
        self.assertFalse(any(c["stage"] == "spec-review" for c in self.model.calls))
        rendered = Path(tempfile.mkdtemp())
        self.addCleanup(
            lambda: __import__("shutil").rmtree(rendered, ignore_errors=True)
        )

        def revised(suffix, package_root, name):
            prompt = load_model_instructions(package_root, name)
            if prompt.binding.agent != "spec_reviewer":
                return prompt
            # A rebuilt package's instructions: the rendered file and its binding change together.
            body = prompt.body + suffix
            instructions = (
                rendered
                / f"spec-reviewer-{hashlib.sha256(body.encode()).hexdigest()}.md"
            )
            instructions.write_text(body, encoding="utf-8")
            binding = replace(
                prompt.binding,
                instructions_path=str(instructions),
                instructions_digest="sha256:"
                + hashlib.sha256(body.encode()).hexdigest(),
            )
            return replace(
                prompt,
                body=body,
                binding=replace(binding, digest=binding_digest(binding)),
            )

        def changed(package_root, name):
            return revised("\nClarified task relevance.\n", package_root, name)

        @contextmanager
        def instructions(loader):
            # Admit the test's new instruction binding through the same preflight as a rebuilt
            # package; the worker's effects and contract stay intact.
            resolve = worker_profile.resolve_worker
            prompt = loader(PACKAGE, "concorde-spec-reviewer")

            def binding(package, name):
                return (
                    prompt.binding
                    if worker_profile.worker_key(name) == "spec_reviewer"
                    else resolve(package, name)
                )

            with (
                patch(
                    "concorde.review.review.load_model_instructions",
                    side_effect=loader,
                ),
                patch(
                    "concorde.harness.worker_profile.resolve_worker",
                    side_effect=binding,
                ),
            ):
                yield

        def incomplete(stage, snapshot, data, cwd):
            if stage == "spec-review":
                data.update(
                    status="incomplete", answer="Coverage could not be completed."
                )

        with instructions(changed):
            result = self.call_operation("concorde-spec-review", callback=incomplete)
            self.assertEqual("failed", result["status"], result)
            self.assertTrue(any(c["stage"] == "spec-review" for c in self.model.calls))
            self.assertEqual(
                original, read_change(self.root, required=True)["issue_blockers"][0]
            )

        # Another actual instruction revision permits a completed reassessment.
        # The Host preserves the reviewer's independent finding and old history.
        def changed_again(package_root, name):
            return revised("\nReassess coverage.\n", package_root, name)

        def advisory(stage, snapshot, data, cwd):
            if stage == "spec-review":
                self.missing(stage)(stage, snapshot, data, cwd)
                data["issues"][0]["severity"] = "advisory"
                data["blockers"] = []

        with instructions(changed_again):
            result = self.call_operation("concorde-spec-review", callback=advisory)
        self.assertEqual("succeeded", result["status"], result)
        state = read_change(self.root, required=True)
        self.assertEqual("resolved", state["issue_blockers"][0]["status"])
        self.assertEqual(original["blocker"], state["issue_blockers"][0]["blocker"])
        self.assertEqual([], state["blockers"])

    @verifies("scenario.issues.blocker-history")
    def test_gap_persists_deduplicates_and_requires_spec_repair_before_resume(self):
        ensure_change(self.root, task=self.task, allow_primary=True)
        bind_owner(self.root, self.task)
        result = self.call_operation(
            "concorde-spec-review", callback=self.missing("spec-review")
        )
        self.assertEqual("blocked", result["status"], result)
        self.assertNotIn("plan", [x["stage"] for x in self.model.calls])
        before = read_change(self.root, required=True)
        self.assertEqual(1, len(before["issue_blockers"]))
        retry = self.call_operation("concorde-plan")
        self.assertEqual("blocked", retry["status"], retry)
        self.assertEqual(
            1, len(read_change(self.root, required=True)["issue_blockers"])
        )
        self.assertEqual(1, len(read_change(self.root, required=True)["blockers"]))
        self.assertEqual("review_required", retry["errors"][0]["code"], retry)
        self.assertEqual(
            before["blockers"], read_change(self.root, required=True)["blockers"]
        )
        self.assertNotIn("plan", [x["stage"] for x in self.model.calls])
        spec = self.root / "specs/transfer/module.md"
        spec.write_text(
            spec.read_text()
            + "\nThe transfer operation owns a daily limit of 1000 units.\n"
        )
        self.assertEqual("succeeded", self.review()["status"])
        resumed = self.call_operation("concorde-plan")
        self.assertEqual("succeeded", resumed["status"], resumed)
        state = read_change(self.root, required=True)
        self.assertEqual([], state["blockers"])
        self.assertEqual("resolved", state["issue_blockers"][0]["status"])
        self.assertEqual("active", state["status"])
        self.assertNotIn("specify", [x["stage"] for x in self.model.calls])

    @verifies("scenario.planning.assessment-gap", "scenario.concorde.develop-gap")
    @verifies("scenario.issues.blocker-history")
    def test_real_task_phases_preserve_gaps_and_resume_after_repair(self):
        for phase, operation in (
            ("context-solve", "concorde-context-solve"),
            ("plan", "concorde-plan"),
            ("tasks", "concorde-tasks"),
            ("implementation", "concorde-implement"),
        ):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                previous, self.root = self.root, Path(directory)
                try:
                    project(self.root)
                    ensure_change(self.root, task=self.task, allow_primary=True)
                    bind_owner(self.root, self.task)
                    if phase in {"tasks", "implementation"}:
                        self.call_operation("concorde-plan")
                    if phase == "implementation":
                        self.call_operation("concorde-tasks")
                    result = self.call_operation(
                        operation, callback=self.missing(phase)
                    )
                    self.assertEqual("blocked", result["status"], result)
                    history = read_change(self.root, required=True)["issue_blockers"]
                    self.assertEqual(phase, history[0]["phase"])
                    self.assertNotEqual(
                        "ready", read_change(self.root, required=True)["status"]
                    )
                    spec = self.root / "specs/transfer/module.md"
                    spec.write_text(
                        spec.read_text() + "\nTransfer owns the daily limit.\n"
                    )
                    self.assertEqual(
                        history, read_change(self.root, required=True)["issue_blockers"]
                    )
                    if phase in {"tasks", "implementation"}:
                        self.assertEqual(
                            "succeeded", self.call_operation("concorde-plan")["status"]
                        )
                    if phase == "implementation":

                        def new_tasks(stage, snapshot, data, cwd):
                            data["tasks"][0]["id"] += ".replanned"

                        self.assertEqual(
                            "succeeded",
                            self.call_operation("concorde-tasks", callback=new_tasks)[
                                "status"
                            ],
                        )
                    resumed = self.call_operation(operation)
                    self.assertEqual("succeeded", resumed["status"], resumed)
                    state = read_change(self.root, required=True)
                    self.assertEqual([], state["blockers"])
                    self.assertEqual("resolved", state["issue_blockers"][0]["status"])
                    self.assertEqual(
                        history[0]["contexts"], state["issue_blockers"][0]["contexts"]
                    )
                finally:
                    self.root = previous

    @verifies("scenario.validation.blocked")
    def test_explicit_review_requirement_cannot_be_downgraded(self):
        from concorde.review.review import require_reviews

        ensure_change(self.root, task=self.task, allow_primary=True)
        bind_owner(self.root, self.task)
        result = self.review(callback=self.missing("spec-review"))
        self.assertEqual("blocked", result["status"], result)
        require_reviews(self.invocation(), False, modes=["spec"])
        state = read_change(self.root, required=True)
        self.assertTrue(state["review_requirements"][self.task["target_id"]]["spec"])
        for operation in ("concorde-plan", "concorde-validate"):
            result = self.call_operation(
                operation,
                {
                    **self.task,
                    **(
                        {"run_checks": False}
                        if operation == "concorde-validate"
                        else {}
                    ),
                },
            )
            self.assertEqual("review_required", result["errors"][0]["code"], result)
            self.assertEqual([], self.model.calls)
        self.assertNotEqual("ready", read_change(self.root, required=True)["status"])

    @verifies("scenario.review.standalone")
    def test_independent_contract_findings_remain_visible_without_claiming_completeness(
        self,
    ):
        # Process doubles verify result retention and gates, not semantic relevance.
        for mode in ("spec", "code"):
            with self.subTest(mode=mode):

                def independent(stage, snapshot, data, cwd, mode=mode):
                    if stage == mode + "-review":
                        data.update(
                            status="findings",
                            blockers=[],
                            issues=[
                                {
                                    "id": "independent-contract",
                                    "severity": "advisory",
                                    "target_id": snapshot["target_id"],
                                    "document": "specs/transfer/module.md",
                                    "contract": "Independent export",
                                    "location": {
                                        "path": "specs/transfer/module.md",
                                        "line": 1,
                                    },
                                    "problem": "Export collision behavior is unspecified. The admitted pure transfer task "
                                    "does not use or change export; this finding does not establish export completeness.",
                                    "affected_task": "Export colliding identifiers",
                                }
                            ],
                        )

                result = self.review(mode, callback=independent)
                self.assertEqual("succeeded", result["status"], result)
                report = result["output"]["data"]["reviews"][0]["data"]
                self.assertEqual("findings", report["status"])
                self.assertEqual("not_proven", report["semantic_completeness"])
                self.assertEqual(
                    "independent-contract",
                    issue_observation(self.root, report["issues"][0])["report"][
                        "report_key"
                    ],
                )
                reference = result["output"]["data"]["artifacts"][0]
                self.assertEqual(
                    report,
                    json.loads((self.root / reference["path"]).read_text())["data"],
                )

    @verifies("scenario.validation.blocked")
    def test_advisory_findings_do_not_block_but_required_incomplete_review_does(self):
        for operation in ("concorde-plan", "concorde-tasks", "concorde-implement"):
            self.assertEqual("succeeded", self.call_operation(operation)["status"])

        def advisory(stage, snapshot, data, cwd):
            data.update(
                status="findings",
                issues=[{**ExplicitRepairTests.finding(), "severity": "advisory"}],
            )

        self.assertEqual("succeeded", self.review("code", callback=advisory)["status"])
        self.assertEqual(
            "ready",
            self.call_operation("concorde-validate")["output"]["data"]["outcome"],
        )

        def incomplete(stage, snapshot, data, cwd):
            data.update(status="incomplete", answer="Review could not complete.")

        self.assertEqual("failed", self.review("code", callback=incomplete)["status"])
        result = self.call_operation("concorde-validate")
        self.assertEqual("review_required", result["errors"][0]["code"], result)
        self.assertIsNone(read_change(self.root, required=True)["validated_tree"])

    @verifies("scenario.harness.execute-success")
    def test_reviewer_result_parameters_are_the_self_contained_wire_schema(self):
        from concorde.harness.worker_executor import result_parameters

        result = self.review()
        self.assertEqual("succeeded", result["status"], result)
        launch = self.model.calls[0]["launch"]
        self.assertEqual(
            result_parameters("concorde-review-stage-result"), launch.result_schema
        )
        self.assertNotIn("$ref", json.dumps(launch.result_schema))
        wire = DATA_SCHEMAS["concorde-review-stage-result"]["properties"]
        self.assertTrue(wire["representative_tasks"]["uniqueItems"])
        self.assertTrue(
            launch.result_schema["properties"]["representative_tasks"]["uniqueItems"]
        )
        self.assertNotIn("blockers", wire)
        self.assertEqual(
            {"issue_id", "report_id", "path", "severity", "affected_task"},
            set(wire["issues"]["items"]["required"]),
        )
        self.assertEqual(
            {"read", "grep", "find", "ls", "submit_result", "report_issue"},
            set(launch.tools),
        )
        self.assertIsNotNone(launch.report_schema)
        self.assertFalse(hasattr(launch, "child_tools"))

    def test_unrelated_review_query_cannot_replace_required_lifecycle_evidence(self):
        self.assertEqual("succeeded", self.call_operation("concorde-plan")["status"])
        self.review("spec")
        self.review("code")
        before = read_change(self.root)
        result = self.call_operation(
            "concorde-spec-review",
            {
                **self.task,
                "task": "Inspect a separate possible use",
            },
            callback=self.missing("spec-review"),
        )
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual(before, read_change(self.root))
        self.assertIsNotNone(current(self.invocation(), "spec"))

    def test_standalone_dependent_steps_cannot_bypass_a_failed_required_spec_review(
        self,
    ):
        self.assertEqual("succeeded", self.call_operation("concorde-plan")["status"])
        blocked = self.review(callback=self.missing("spec-review"))
        self.assertEqual("blocked", blocked["status"], blocked)
        tasks = read_change(self.root, required=True)["targets"][
            self.task["target_id"]
        ]["tasks"]
        for operation in ("concorde-tasks", "concorde-implement"):
            result = self.call_operation(operation)
            self.assertEqual("blocked", result["status"], result)
            self.assertEqual("review_required", result["errors"][0]["code"])
            self.assertEqual([], self.model.calls)
            self.assertEqual(
                tasks,
                read_change(self.root, required=True)["targets"][
                    self.task["target_id"]
                ]["tasks"],
            )

    @verifies(
        "scenario.planning.assessment-sufficient", "scenario.planning.plan-current"
    )
    def test_a_sufficient_assessment_admits_a_revision_bound_plan_and_no_task_list(
        self,
    ):
        from concorde.harness.revisions import target_revision
        from concorde.spec.repository import SpecRepository

        self.assertEqual("succeeded", self.call_operation("concorde-plan")["status"])
        documents = {
            path: path.read_bytes() for path in (self.root / "specs").rglob("*.md")
        }
        assessed = self.call_operation("concorde-context-solve")
        self.assertEqual("succeeded", assessed["status"], assessed)
        # A sufficient assessment concerns this task only: it authors nothing and admits planning.
        self.assertEqual("completed", assessed["output"]["data"]["outcome"])
        self.assertEqual([], assessed["output"]["data"]["blockers"])
        self.assertEqual(
            ["context-solve"], [call["stage"] for call in self.model.calls]
        )
        self.assertEqual(
            documents,
            {path: path.read_bytes() for path in (self.root / "specs").rglob("*.md")},
        )
        planned = self.call_operation("concorde-plan")
        self.assertEqual("succeeded", planned["status"], planned)
        reference = planned["output"]["data"]["artifacts"][0]
        state = read_change(self.root, required=True)["targets"][self.task["target_id"]]
        self.assertEqual((self.root / reference["path"]).read_text(), state["plan"])
        repository = SpecRepository(self.root, PACKAGE)
        self.assertEqual(
            target_revision(repository, repository.select(self.task["target_id"])),
            state["spec_digest"],
        )
        self.assertEqual(
            ([], [], None),
            (state["tasks"], state["checks"], state["implementation_digest"]),
        )
        self.assertEqual(
            documents,
            {path: path.read_bytes() for path in (self.root / "specs").rglob("*.md")},
        )

    @verifies("scenario.planning.plan-empty", "scenario.planning.plan-stale")
    def test_an_empty_or_stale_planner_result_preserves_the_accepted_plan(self):
        self.assertEqual("succeeded", self.call_operation("concorde-plan")["status"])
        self.assertEqual("succeeded", self.call_operation("concorde-plan")["status"])
        accepted = read_change(self.root, required=True)["targets"][
            self.task["target_id"]
        ]
        stored = (
            self.root / f"{WORK_PATH}/{self.task['target_id']}/plan.md"
        ).read_bytes()

        def empty(stage, snapshot, data, cwd):
            if stage == "plan":
                data["plan"] = ""

        def changed(stage, snapshot, data, cwd):
            if stage == "plan":
                spec = self.root / "specs/transfer/module.md"
                spec.write_text(
                    spec.read_text() + "\nThe daily-limit owner is transfer.\n"
                )

        for label, callback, code in (
            ("empty", empty, "invalid_completion"),
            ("stale", changed, "stale_context"),
        ):
            with self.subTest(plan=label):
                result = self.call_operation("concorde-plan", callback=callback)
                self.assertNotEqual("succeeded", result["status"], result)
                self.assertEqual(code, result["errors"][0]["code"], result)
                current_state = read_change(self.root, required=True)["targets"][
                    self.task["target_id"]
                ]
                self.assertEqual(accepted["plan"], current_state["plan"])
                self.assertEqual(
                    stored,
                    (
                        self.root / f"{WORK_PATH}/{self.task['target_id']}/plan.md"
                    ).read_bytes(),
                )
                self.assertEqual([], current_state["tasks"])

    @verifies(
        "scenario.planning.tasks-missing-plan", "scenario.implementation.missing-tasks"
    )
    def test_task_authoring_and_implementation_refuse_their_missing_prerequisite(self):
        self.assertEqual("succeeded", self.call_operation("concorde-plan")["status"])
        history = read_change(self.root, required=True)["targets"][
            self.task["target_id"]
        ].get("task_history", [])
        self.assertEqual("succeeded", self.call_operation("concorde-plan")["status"])
        # The accepted plan alone admits no implementation; without it, task authoring never starts.
        for operation, code in (
            ("concorde-implement", "missing_tasks"),
            ("concorde-tasks", "missing_plan"),
        ):
            with self.subTest(operation=operation):
                if operation == "concorde-tasks":
                    state = read_change(self.root, required=True)
                    state["targets"][self.task["target_id"]]["plan"] = ""
                    save_change(self.root, state)
                result = self.call_operation(operation)
                self.assertEqual("blocked", result["status"], result)
                self.assertEqual(code, result["errors"][0]["code"], result)
                self.assertEqual([], self.model.calls)
                current_state = read_change(self.root, required=True)["targets"][
                    self.task["target_id"]
                ]
                self.assertEqual([], current_state["tasks"])
                self.assertEqual(history, current_state.get("task_history", []))

    @verifies("scenario.implementation.incomplete-output")
    def test_an_incomplete_or_omitted_task_result_is_rejected_and_leaves_its_edits_inspectable(
        self,
    ):
        def incomplete(mode):
            def callback(stage, snapshot, data, cwd):
                if stage != "implementation" or not data["tasks"]:
                    return
                data["tasks"] = (
                    []
                    if mode == "omitted"
                    else [{**data["tasks"][0], "complete": False}]
                )

            return callback

        for mode in ("incomplete", "omitted"):
            with self.subTest(result=mode), tempfile.TemporaryDirectory() as directory:
                previous_root, self.root = self.root, Path(directory)
                try:
                    project(self.root)
                    self.assertEqual(
                        "succeeded", self.call_operation("concorde-plan")["status"]
                    )
                    for operation in ("concorde-plan", "concorde-tasks"):
                        self.assertEqual(
                            "succeeded", self.call_operation(operation)["status"]
                        )
                    result = self.call_operation(
                        "concorde-implement", callback=incomplete(mode)
                    )
                    self.assertEqual(
                        "incomplete_tasks", result["errors"][0]["code"], result
                    )
                    state = read_change(self.root, required=True)["targets"][
                        self.task["target_id"]
                    ]
                    self.assertIsNone(state["implementation_digest"])
                    self.assertEqual(
                        [False], [task["complete"] for task in state["tasks"]]
                    )
                    # The programmer's authorized edits stay in the candidate for the next attempt.
                    self.assertIn(
                        "TRANSFER_IMPLEMENTATION_CODE",
                        (self.root / "app/transfer.py").read_text(),
                    )
                finally:
                    self.root = previous_root

    @verifies("scenario.issues.blocker-history", "scenario.concorde.develop-gap")
    def test_upstream_task_gaps_block_standalone_dependents_but_allow_independent_queries(
        self,
    ):
        for phase in ("context-solve", "plan"):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                previous_root = self.root
                self.root = Path(directory)
                try:
                    project(self.root)
                    self.assertEqual(
                        "succeeded", self.call_operation("concorde-plan")["status"]
                    )
                    self.assertEqual(
                        "succeeded", self.call_operation("concorde-tasks")["status"]
                    )
                    self.assertEqual(
                        "blocked",
                        self.call_operation(
                            "concorde-plan", callback=self.missing(phase)
                        )["status"],
                    )
                    gap = read_change(self.root, required=True)["blockers"][0]
                    for operation in ("concorde-tasks", "concorde-implement"):
                        result = self.call_operation(operation)
                        self.assertEqual("blocked", result["status"], result)
                        self.assertEqual([gap], result["output"]["data"]["blockers"])
                        self.assertEqual([], self.model.calls)
                    self.assertEqual(
                        "succeeded",
                        self.call_operation("concorde-context-solve")["status"],
                    )
                    self.assertEqual(
                        "open",
                        read_change(self.root, required=True)["issue_blockers"][0][
                            "status"
                        ],
                    )
                    spec = self.root / "specs/transfer/module.md"
                    spec.write_text(
                        spec.read_text() + "\nThe daily-limit owner is transfer.\n"
                    )
                    self.assertEqual(
                        "succeeded", self.call_operation("concorde-plan")["status"]
                    )
                    self.assertEqual(
                        "resolved",
                        read_change(self.root, required=True)["issue_blockers"][0][
                            "status"
                        ],
                    )
                finally:
                    self.root = previous_root

    @verifies("scenario.harness.invocation-worktree-binding")
    def test_review_binds_actual_worktree_even_with_identical_unversioned_bytes(self):
        original = inputs(self.invocation(), "spec")[0]["input_digest"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project(root)
            peer = Invocation(
                "concorde-spec-review",
                self.configuration,
                self.task,
                OperationHost(root, PACKAGE),
            )
            self.assertNotEqual(original, inputs(peer, "spec")[0]["input_digest"])
        rejected = self.call_operation(
            "concorde-spec-review",
            {**self.task, "change_id": "change.foreign"},
        )
        self.assertEqual("missing_change", rejected["errors"][0]["code"])
        self.assertEqual([], self.model.calls)

    @verifies("scenario.review.standalone")
    def test_explicit_component_reviews_keep_separate_recorded_contexts(self):
        from concorde.implementation.implement import component_intent

        task = {
            "target_id": "scope.bank",
            "task": "Implement transfer and ledger promises",
        }

        def components(stage, snapshot, data, cwd):
            data["tasks"].append(
                {
                    "id": "task.ledger",
                    "target_id": "module.ledger",
                    "description": "Implement ledger reads.",
                    "acceptance": "Return known balances and reject unknown accounts.",
                    "complete": False,
                }
            )

        self.assertEqual(
            "succeeded", self.call_operation("concorde-plan", task)["status"]
        )
        self.assertEqual(
            "succeeded",
            self.call_operation("concorde-tasks", task, callback=components)["status"],
        )
        parent = read_change(self.root, required=True)["targets"]["scope.bank"]
        for target in ("service.transfer", "module.ledger"):
            selected = [t for t in parent["tasks"] if t["target_id"] == target]
            child = {"target_id": target, "task": component_intent(selected)}
            for operation in ("plan", "tasks", "implement", "validate"):
                result = self.call_operation("concorde-" + operation, child)
                self.assertEqual("succeeded", result["status"], result)
        self.assertEqual(
            "succeeded", self.call_operation("concorde-implement", task)["status"]
        )
        reviewed = []
        for target in ("service.transfer", "module.ledger"):
            selected = [t for t in parent["tasks"] if t["target_id"] == target]
            child = {"target_id": target, "task": component_intent(selected)}
            result = self.call_operation("concorde-code-review", child)
            self.assertEqual("succeeded", result["status"], result)
            reviewed.extend(
                r["data"]["target_id"] for r in result["output"]["data"]["reviews"]
            )
            for call in self.model.calls:
                paths = {
                    x["path"] for x in call["snapshot"]["implementation_artifacts"]
                }
                foreign = (
                    "app/ledger.py"
                    if target == "service.transfer"
                    else "app/transfer.py"
                )
                self.assertNotIn(foreign, paths)
        self.assertCountEqual(["service.transfer", "module.ledger"], reviewed)

    @verifies("scenario.issues.blocker-history")
    def test_rejected_plan_tasks_and_implementation_cannot_resolve_previous_gaps(self):
        for phase, operation in (
            ("plan", "concorde-plan"),
            ("tasks", "concorde-tasks"),
            ("implementation", "concorde-implement"),
        ):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                previous, self.root = self.root, Path(directory)
                try:
                    project(self.root)
                    if phase in {"tasks", "implementation"}:
                        self.call_operation("concorde-plan")
                    if phase == "implementation":
                        self.call_operation("concorde-tasks")
                    self.assertEqual(
                        "blocked",
                        self.call_operation(operation, callback=self.missing(phase))[
                            "status"
                        ],
                    )
                    spec = self.root / "specs/transfer/module.md"
                    spec.write_text(
                        spec.read_text() + "\nTransfer owns the daily limit.\n"
                    )
                    if phase in {"tasks", "implementation"}:
                        self.call_operation("concorde-plan")
                    if phase == "implementation":

                        def new_tasks(stage, snapshot, data, cwd):
                            data["tasks"][0]["id"] += ".replanned"

                        self.call_operation("concorde-tasks", callback=new_tasks)
                    before = read_change(self.root, required=True)["issue_blockers"]

                    def invalid(stage, snapshot, data, cwd):
                        if stage == phase:
                            data["plan" if phase == "plan" else "tasks"] = (
                                "" if phase == "plan" else []
                            )

                    result = self.call_operation(operation, callback=invalid)
                    self.assertNotEqual("succeeded", result["status"], result)
                    self.assertEqual(
                        before, read_change(self.root, required=True)["issue_blockers"]
                    )
                    self.assertEqual(
                        "succeeded", self.call_operation(operation)["status"]
                    )
                    self.assertEqual(
                        "resolved",
                        read_change(self.root, required=True)["issue_blockers"][0][
                            "status"
                        ],
                    )
                finally:
                    self.root = previous

    @verifies(
        "scenario.issues.blocker-history",
        "scenario.planning.plan-empty",
        "scenario.concorde.develop-failure",
    )
    def test_failed_plan_artifact_write_can_resume_and_resolve_the_planning_gap(self):
        from concorde.planning import plan as planning

        self.assertEqual(
            "blocked",
            self.call_operation("concorde-plan", callback=self.missing("plan"))[
                "status"
            ],
        )
        spec = self.root / "specs/transfer/module.md"
        spec.write_text(spec.read_text() + "\nThe daily-limit owner is transfer.\n")
        original_apply = planning.apply_files

        def reject_plan(root, changes, allowed, **kwargs):
            if any(item["path"].endswith("/plan.md") for item in changes):
                raise OSError("fixture plan directory cannot be written")
            return original_apply(root, changes, allowed, **kwargs)

        with patch.object(planning, "apply_files", side_effect=reject_plan):
            self.assertNotEqual(
                "succeeded", self.call_operation("concorde-plan")["status"]
            )
        failed_state = read_change(self.root, required=True)
        self.assertEqual("open", failed_state["issue_blockers"][0]["status"])
        self.assertNotEqual("ready", failed_state["status"])
        self.assertNotEqual("delivered", failed_state.get("outcome"))
        resumed = self.call_operation("concorde-plan")
        self.assertEqual("succeeded", resumed["status"], resumed)
        self.assertIn("plan", [call["stage"] for call in self.model.calls])
        self.assertEqual(
            "resolved",
            read_change(self.root, required=True)["issue_blockers"][0]["status"],
        )

    def test_reported_blocker_is_already_an_issue_without_capture(self):
        from concorde.issues.store import read_issue

        result = self.call_operation(
            "concorde-plan", callback=self.missing("context-solve")
        )
        self.assertEqual("blocked", result["status"], result)
        blocked = read_change(self.root, required=True)["issue_blockers"][0]
        reference = blocked["blocker"]
        record, _ = read_issue(self.root, reference["issue_id"])
        self.assertEqual("open", record["status"])
        self.assertEqual(
            "service.transfer", record["reports"][0]["source"]["target_id"]
        )
        result = self.call_operation(
            "concorde-issues",
            {
                "action": "show",
                "issue_id": record["id"],
                "target_id": self.task["target_id"],
            },
        )
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual([], self.model.calls)
        self.assertEqual(record, result["output"]["data"]["issues"][0])
        self.assertEqual(
            "open", read_change(self.root, required=True)["issue_blockers"][0]["status"]
        )

    @verifies(
        "scenario.planning.historical-author-gap", "scenario.issues.blocker-history"
    )
    def test_historical_author_gap_direct_edit_fresh_assessment_review_plan_tasks(self):
        from concorde.harness.change_worktree import record_task_gaps
        from concorde.issues.store import read_issue, report_issue
        from tests.concorde.issues.test_store import report, source

        ensure_change(self.root, task=self.task, allow_primary=True)
        bind_owner(self.root, self.task)
        self.assertEqual("succeeded", self.review()["status"])
        run = self.invocation()
        reference = report_issue(
            self.root,
            report(owner_target_id=self.task["target_id"], evidence=[]),
            source(
                agent="spec-author",
                operation="concorde-specify",
                phase="specify",
                target_id=self.task["target_id"],
                change_id=run.change_id,
            ),
        )
        record_task_gaps(
            self.root,
            self.task["target_id"],
            self.task["task"],
            "specify",
            [{**reference, "blocked_step": "Specify retry ownership"}],
            run.blocker_revision("specify"),
            spec_resolution=run.repository.spec_context(run.target.id).value,
        )
        original = read_change(self.root, required=True)["issue_blockers"]
        issue_before = (self.root / reference["path"]).read_bytes()

        # An unsuccessful reassessment cannot retire the old prerequisite.
        def failed_assessment(stage, snapshot, data, cwd):
            data.update(outcome="failed", answer="No accepted assessment.")

        self.assertEqual(
            "blocked",
            self.call_operation("concorde-context-solve", callback=failed_assessment)[
                "status"
            ],
        )
        self.assertEqual(
            original, read_change(self.root, required=True)["issue_blockers"]
        )
        self.assertEqual(
            "blocked",
            self.call_operation(
                "concorde-validate", {**self.task, "run_checks": False}
            )["status"],
        )
        document = self.root / "specs/transfer/module.md"
        document.write_text(
            document.read_text()
            + "\nTransfer owns retry admission; callers never retry implicitly.\n"
        )
        metadata = Path(str(document) + ".json")
        body = json.loads(metadata.read_text())
        entity = next(e for e in body["entities"] if "files" in e)
        entity["files"].append("app/retry.py")
        metadata.write_text(json.dumps(body, indent=2) + "\n")
        (self.root / "app/retry.py").write_text(
            "# Retry admission belongs to transfer.\n"
        )
        registry_path = self.root / ".concorde/specs.json"
        registry = json.loads(registry_path.read_text())
        target = next(
            t for t in registry["targets"] if t["id"] == self.task["target_id"]
        )
        target["files"] = sorted([*target["files"], "app/retry.py"])
        registry_path.write_text(json.dumps(registry, indent=2) + "\n")
        self.assertEqual(
            original, read_change(self.root, required=True)["issue_blockers"]
        )
        self.assertIsNone(current(self.invocation(), "spec"))
        self.assertEqual(
            "blocked",
            self.call_operation(
                "concorde-validate", {**self.task, "run_checks": False}
            )["status"],
        )
        assessed = self.call_operation("concorde-context-solve")
        self.assertEqual("succeeded", assessed["status"], assessed)
        history = read_change(self.root, required=True)["issue_blockers"]
        self.assertEqual("superseded", history[0]["status"])
        self.assertEqual(
            original[0],
            {
                k: v
                for k, v in {**history[0], "status": "open"}.items()
                if k != "reassessment"
            },
        )
        self.assertEqual(
            assessed["output"]["data"]["context_id"],
            history[0]["reassessment"]["context_id"],
        )
        # Assessment is not an independent review and cannot refresh its requirement.
        self.assertEqual(
            "review_required", self.call_operation("concorde-plan")["errors"][0]["code"]
        )
        self.assertEqual("succeeded", self.review()["status"])
        for operation in ("concorde-plan", "concorde-tasks"):
            result = self.call_operation(operation)
            self.assertEqual("succeeded", result["status"], result)
        self.assertEqual(issue_before, (self.root / reference["path"]).read_bytes())
        self.assertEqual(
            "open", read_issue(self.root, reference["issue_id"])[0]["status"]
        )
        self.assertEqual(
            history, read_change(self.root, required=True)["issue_blockers"]
        )

    @verifies("scenario.planning.historical-author-gap")
    def test_historical_author_gap_rejects_stale_failed_and_unrelated_assessment(self):
        from concorde.harness.change_worktree import record_task_gaps
        from concorde.issues.store import report_issue
        from tests.concorde.issues.test_store import report, source

        ensure_change(self.root, task=self.task, allow_primary=True)
        bind_owner(self.root, self.task)
        run = self.invocation()
        reference = report_issue(
            self.root,
            report(owner_target_id=self.task["target_id"], evidence=[]),
            source(
                target_id=self.task["target_id"],
                phase="specify",
                operation="concorde-specify",
            ),
        )
        record_task_gaps(
            self.root,
            self.task["target_id"],
            self.task["task"],
            "specify",
            [{**reference, "blocked_step": "Specify retry ownership"}],
            run.blocker_revision("specify"),
        )
        before = read_change(self.root, required=True)["issue_blockers"]
        document = self.root / "specs/transfer/module.md"
        document.write_text(document.read_text() + "\nTransfer owns retries.\n")
        for selected in (
            {**self.task, "task": "An unrelated question"},
            {**self.task, "constraints": ["Assess only documentation spelling"]},
            {"target_id": "module.ledger", "task": self.task["task"]},
        ):
            result = self.call_operation("concorde-context-solve", selected)
            self.assertEqual("succeeded", result["status"], result)
            self.assertEqual(
                before, read_change(self.root, required=True)["issue_blockers"]
            )

        def fail(stage, snapshot, data, cwd):
            data.update(outcome="failed", answer="Assessment failed.")

        self.assertNotEqual(
            "succeeded",
            self.call_operation("concorde-context-solve", callback=fail)["status"],
        )

        def stale(stage, snapshot, data, cwd):
            document.write_text(document.read_text() + "\nConcurrent edit.\n")

        result = self.call_operation("concorde-context-solve", callback=stale)
        self.assertEqual("stale_context", result["errors"][0]["code"], result)
        self.assertEqual(
            before, read_change(self.root, required=True)["issue_blockers"]
        )
        # An accepted planner cannot bypass an unresolved historical blocker.
        self.assertEqual("succeeded", self.review()["status"])
        self.assertEqual(
            "blocked",
            self.call_operation(
                "concorde-validate", {**self.task, "run_checks": False}
            )["status"],
        )
        self.assertEqual(
            before, read_change(self.root, required=True)["issue_blockers"]
        )
        self.assertEqual(
            "succeeded", self.call_operation("concorde-context-solve")["status"]
        )
        self.assertEqual(
            "superseded",
            read_change(self.root, required=True)["issue_blockers"][0]["status"],
        )

    @verifies("scenario.planning.historical-author-gap")
    def test_obsolete_author_relations_supersede_without_inventing_past_success(self):
        from concorde.harness.change_worktree import record_task_gaps
        from concorde.issues.store import report_issue
        from tests.concorde.issues.test_store import report, source

        for original_revision, issue_type in (
            (None, "gap"),
            ("known", "bug"),
            ("known", "gap"),
        ):
            with self.subTest(revision=original_revision, issue_type=issue_type):
                fixture = ReviewTests()
                fixture.setUp()
                try:
                    ensure_change(fixture.root, task=fixture.task, allow_primary=True)
                    bind_owner(fixture.root, fixture.task)
                    run = fixture.invocation()
                    payload = report(owner_target_id=run.target.id, evidence=[])
                    payload["type"] = issue_type
                    if issue_type == "bug":
                        payload["subtype"] = None
                    reference = report_issue(
                        fixture.root,
                        payload,
                        source(
                            target_id=run.target.id,
                            phase="specify",
                            operation="concorde-specify",
                        ),
                    )
                    revision = (
                        run.blocker_revision("specify") if original_revision else None
                    )
                    record_task_gaps(
                        fixture.root,
                        run.target.id,
                        run.task["task"],
                        "specify",
                        [{**reference, "blocked_step": "Retired author failed"}],
                        revision,
                    )
                    before = read_change(fixture.root, required=True)["issue_blockers"][
                        0
                    ]
                    issue_bytes = (fixture.root / reference["path"]).read_bytes()
                    result = fixture.call_operation("concorde-context-solve")
                    self.assertEqual("succeeded", result["status"], result)
                    after = read_change(fixture.root, required=True)["issue_blockers"][
                        0
                    ]
                    self.assertEqual("superseded", after["status"])
                    self.assertEqual(
                        "retired_author_prerequisite", after["reassessment"]["reason"]
                    )
                    self.assertEqual(
                        before,
                        {
                            key: value
                            for key, value in {**after, "status": "open"}.items()
                            if key != "reassessment"
                        },
                    )
                    self.assertEqual(
                        issue_bytes, (fixture.root / reference["path"]).read_bytes()
                    )
                finally:
                    fixture.doCleanups()

    @verifies("scenario.planning.historical-author-gap")
    def test_insufficient_assessment_keeps_obsolete_relation_and_records_current_gap(
        self,
    ):
        from concorde.harness.change_worktree import record_task_gaps
        from concorde.issues.store import report_issue
        from tests.concorde.issues.test_store import report, source

        ensure_change(self.root, task=self.task, allow_primary=True)
        bind_owner(self.root, self.task)
        run = self.invocation()
        reference = report_issue(
            self.root,
            report(owner_target_id=run.target.id, evidence=[]),
            source(
                target_id=run.target.id, phase="specify", operation="concorde-specify"
            ),
        )
        record_task_gaps(
            self.root,
            run.target.id,
            run.task["task"],
            "specify",
            [{**reference, "blocked_step": "Old author dependency"}],
            None,
        )
        before = read_change(self.root, required=True)["issue_blockers"][0]
        result = self.call_operation(
            "concorde-context-solve", callback=self.missing("context-solve")
        )
        self.assertEqual("blocked", result["status"], result)
        relations = read_change(self.root, required=True)["issue_blockers"]
        self.assertEqual(before, relations[0])
        self.assertEqual("context-solve", relations[1]["phase"])
        self.assertEqual("open", relations[1]["status"])
        result = self.call_operation("concorde-context-solve")
        self.assertEqual("succeeded", result["status"], result)
        relations = read_change(self.root, required=True)["issue_blockers"]
        self.assertEqual("superseded", relations[0]["status"])
        # The retained assessment's own unchanged contract gap is still a prerequisite.
        self.assertEqual("open", relations[1]["status"])
        self.assertEqual("blocked", self.call_operation("concorde-plan")["status"])

    @verifies("scenario.planning.historical-author-gap")
    def test_obsolete_author_relation_rejects_ambiguous_attribution(self):
        from concorde.harness.change_worktree import record_task_gaps
        from concorde.issues.store import report_issue
        from tests.concorde.issues.test_store import report, source

        ensure_change(self.root, task=self.task, allow_primary=True)
        bind_owner(self.root, self.task)
        run = self.invocation()
        reference = report_issue(
            self.root,
            report(owner_target_id=run.target.id, evidence=[]),
            source(
                target_id=run.target.id,
                phase="implementation",
                operation="concorde-implement",
            ),
        )
        record_task_gaps(
            self.root,
            run.target.id,
            run.task["task"],
            "specify",
            [{**reference, "blocked_step": "Incorrectly attributed execution"}],
            None,
        )
        before = read_change(self.root, required=True)["issue_blockers"]
        result = self.call_operation("concorde-context-solve")
        self.assertEqual("invalid_worktree_state", result["errors"][0]["code"], result)
        self.assertEqual(
            before, read_change(self.root, required=True)["issue_blockers"]
        )


class ExplicitRepairTests(unittest.TestCase):
    """Caller-selected repair consumes current review evidence, not graph history."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.registry = project(self.root)
        self.configuration = CONFIGURATION
        self.task = {
            "target_id": "service.transfer",
            "task": "Implement the pure transfer contract",
        }

    def double(self, callback=None):
        double = ModelProcessDouble(callback)
        return double

    def call_operation(
        self, operation, data=None, callback=None, *, mode="execute", double=None
    ):
        self.model = double or self.double(callback)
        self.host = OperationHost(
            self.root,
            PACKAGE,
            executor=self.model.executor,
            allow_primary_worktree=True,
            mode=mode,
        )
        return run_operation(
            operation,
            self.configuration,
            typed(operation + "-request", data or self.task),
            host_context=self.host,
        )

    @staticmethod
    def finding(
        problem="A required daily-limit check is missing.",
        finding_id="daily-limit-check",
    ):
        return {
            "id": finding_id,
            "severity": "blocking",
            "target_id": "service.transfer",
            "document": "specs/transfer/module.md",
            "contract": "Pure transfer",
            "location": {"path": "app/transfer.py", "line": 1},
            "problem": problem,
            "affected_task": "Reject invalid amounts",
        }

    @staticmethod
    def repair_tasks(counter, snapshot, data):
        """Give the repair round a task id that never repeats an earlier (historical) id."""
        if any(
            item["type_id"] == "concorde-review-result"
            for item in snapshot["stage_inputs"]
        ):
            data["tasks"] = [
                {
                    "id": f"task.transfer.repair.{counter[0]}",
                    "target_id": snapshot["target_id"],
                    "description": "Repair the reported daily-limit defect.",
                    "acceptance": "Valid transfer subtracts; invalid amount or insufficient funds raises ValueError.",
                    "complete": False,
                }
            ]

    def prepare_review(self):
        for operation in ("plan", "tasks", "implement"):
            result = self.call_operation("concorde-" + operation)
            self.assertEqual("succeeded", result["status"], result)

        def finding(stage, snapshot, data, cwd):
            if stage == "code-review":
                data.update(status="findings", issues=[self.finding()], blockers=[])

        result = self.call_operation("concorde-code-review", callback=finding)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual(["code-review"], [c["stage"] for c in self.model.calls])
        return result["output"]["data"]["artifacts"][0]

    def target(self):
        return read_change(self.root, required=True)["targets"]["service.transfer"]

    def new_tasks(self, stage, snapshot, data, cwd):
        if stage == "tasks":
            data["tasks"][0]["id"] = "task.transfer.repaired"

    @verifies(
        "scenario.planning.task-history-identities",
        "scenario.planning.tasks-id-conflict",
    )
    def test_explicit_review_repair_reserves_current_ids_and_preserves_rejected_state(
        self,
    ):
        reference = self.prepare_review()
        before = self.target()
        result = self.call_operation(
            "concorde-tasks", {**self.task, "repair_review": reference}
        )
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("invalid_completion", result["errors"][0]["code"])
        self.assertIn("task.transfer", result["errors"][0]["message"])
        self.assertEqual(before, self.target())
        values = {
            v["type_id"]: v["data"]
            for v in self.model.calls[-1]["snapshot"]["stage_inputs"]
        }
        self.assertEqual(
            ["task.transfer"],
            values["concorde-task-identity-constraints"]["reserved_task_ids"],
        )
        self.assertTrue(values["concorde-review-result"]["issues"])

    @verifies(
        "scenario.planning.repair-current", "scenario.implementation.admitted-work"
    )
    def test_caller_orders_repair_implementation_review_and_validation(self):
        reference = self.prepare_review()
        before = self.target()
        repaired = self.call_operation(
            "concorde-tasks",
            {**self.task, "repair_review": reference},
            callback=self.new_tasks,
        )
        self.assertEqual("succeeded", repaired["status"], repaired)
        self.assertEqual(["tasks"], [c["stage"] for c in self.model.calls])
        self.assertEqual(before["tasks"], self.target()["task_history"][-1]["tasks"])
        feedback = next(
            v
            for v in self.model.calls[-1]["snapshot"]["stage_inputs"]
            if v["type_id"] == "concorde-review-result"
        )
        implemented = self.call_operation("concorde-implement")
        self.assertEqual("succeeded", implemented["status"], implemented)
        self.assertEqual(["implementation"], [c["stage"] for c in self.model.calls])
        self.assertIn(feedback, self.model.calls[-1]["snapshot"]["stage_inputs"])
        self.assertNotIn("repair_review", self.target())
        reviewed = self.call_operation("concorde-code-review")
        self.assertEqual("succeeded", reviewed["status"], reviewed)
        validated = self.call_operation("concorde-validate")
        self.assertEqual("succeeded", validated["status"], validated)
        self.assertEqual("ready", validated["output"]["data"]["outcome"])
        self.assertFalse(read_change(self.root, required=True).get("graph"))

    @verifies("scenario.planning.repair-current")
    def test_missing_corrupt_forged_and_replaced_reviews_fail_before_task_worker(self):
        from concorde.spec.typed_data import artifact, canonical

        reference = self.prepare_review()
        before = self.target()
        saved = (self.root / reference["path"]).read_bytes()
        cases = [
            {**reference, "path": ".concorde/runs/missing.json"},
            {**reference, "digest": "sha256:" + "0" * 64},
        ]
        forged = json.loads(saved)
        forged["data"]["input_digest"] = "sha256:" + "f" * 64
        path = ".concorde/runs/forged.json"
        (self.root / path).write_text(canonical(forged))
        cases.append(artifact(self.root, reference["id"], path))
        for selected in cases:
            with self.subTest(reference=selected):
                result = self.call_operation(
                    "concorde-tasks",
                    {**self.task, "repair_review": selected},
                    callback=self.new_tasks,
                )
                self.assertEqual("blocked", result["status"], result)
                self.assertEqual([], self.model.calls)
                self.assertEqual(before, self.target())
        # A newer clean review supersedes the old blocking report even at unchanged bytes.
        self.assertEqual(
            "succeeded", self.call_operation("concorde-code-review")["status"]
        )
        before = self.target()
        result = self.call_operation(
            "concorde-tasks",
            {**self.task, "repair_review": reference},
            callback=self.new_tasks,
        )
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual([], self.model.calls)
        self.assertEqual(before, self.target())

    @verifies("scenario.planning.repair-current")
    def test_changed_code_invalidates_explicit_repair_evidence(self):
        reference = self.prepare_review()
        before = self.target()
        code = self.root / "app/transfer.py"
        code.write_text(code.read_text() + "\n# directly edited\n")
        result = self.call_operation(
            "concorde-tasks",
            {**self.task, "repair_review": reference},
            callback=self.new_tasks,
        )
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("stale_evidence", result["errors"][0]["code"])
        self.assertEqual([], self.model.calls)
        self.assertEqual(before, self.target())

    @verifies(
        "scenario.planning.repair-replacement",
        "scenario.planning.task-history-identities",
    )
    def test_replacement_clears_old_feedback_but_preserves_ids_and_review_requirement(
        self,
    ):
        reference = self.prepare_review()
        result = self.call_operation(
            "concorde-tasks",
            {**self.task, "repair_review": reference},
            callback=self.new_tasks,
        )
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual(reference, self.target()["repair_review"])

        def replacement(stage, snapshot, data, cwd):
            if stage == "tasks":
                data["tasks"][0]["id"] = "task.transfer.replacement"

        result = self.call_operation("concorde-tasks", callback=replacement)
        self.assertEqual("succeeded", result["status"], result)
        self.assertNotIn("repair_review", self.target())
        self.assertEqual(2, len(self.target()["task_history"]))
        self.assertTrue(
            read_change(self.root, required=True)["review_requirements"][
                "service.transfer"
            ]["code"]
        )
        result = self.call_operation("concorde-plan")
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual(3, len(self.target()["task_history"]))
        result = self.call_operation("concorde-tasks")
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("invalid_completion", result["errors"][0]["code"])
        self.assertEqual([], self.target()["tasks"])

    @verifies(
        "scenario.planning.plan-current",
        "scenario.planning.plan-stale",
        "scenario.implementation.admitted-work",
    )
    def test_direct_paired_spec_and_registry_edits_then_explicit_operations(self):
        spec = self.root / "specs/transfer/module.md"
        metadata = self.root / "specs/transfer/module.md.json"
        registry = self.root / ".concorde/specs.json"
        spec.write_text(
            spec.read_text()
            + "\nThe calculation may share its pure arithmetic helpers.\n"
        )
        declaration = json.loads(metadata.read_text())
        entity = next(
            e
            for e in declaration["entities"]
            if e["id"] == "entity.transfer.calculation"
        )
        entity["files"].append("app/arithmetic.py")
        metadata.write_text(json.dumps(declaration, indent=2) + "\n")
        registration = json.loads(registry.read_text())
        target = next(
            t for t in registration["targets"] if t["id"] == self.task["target_id"]
        )
        target["files"].append("app/arithmetic.py")
        target["files"].sort()
        registry.write_text(json.dumps(registration, indent=2) + "\n")
        (self.root / "app/arithmetic.py").write_text(
            "def subtract(balance, amount):\n    return balance - amount\n"
        )
        from concorde.spec.validation import validate_repository

        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("success", report.status, [f.message for f in report.findings])
        for operation in (
            "plan",
            "tasks",
            "implement",
            "spec-review",
            "code-review",
            "validate",
        ):
            result = self.call_operation("concorde-" + operation)
            self.assertEqual("succeeded", result["status"], result)
            for call in self.model.calls:
                paths = {
                    source["path"]
                    for source in call["snapshot"]["spec_resolution"]["sources"]
                }
                self.assertIn("specs/transfer/module.md", paths)
                self.assertIn("specs/transfer/module.md.json", paths)
                self.assertNotIn(call["stage"], {"specify", "route", "topology-author"})
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        self.assertFalse(read_change(self.root, required=True).get("graph"))
        # Even a metadata-only byte change invalidates the accepted plan and selected reviews.
        before = self.target()
        metadata.write_text(metadata.read_text() + "\n")
        result = self.call_operation("concorde-tasks", callback=self.new_tasks)
        self.assertEqual("blocked", result["status"], result)
        self.assertIn(result["errors"][0]["code"], {"stale_context", "review_required"})
        self.assertEqual([], self.model.calls)
        self.assertEqual(before, self.target())

    def test_operation_execution_error_during_standalone_code_review_maps_to_execution_limit(
        self,
    ):
        from concorde.harness.change_worktree import ensure_change
        from concorde.harness.worker_executor import OperationExecutionError

        ensure_change(self.root, task=self.task, allow_primary=True)
        bind_owner(self.root, self.task)
        double = self.double()

        def fail(invocation, **options):
            raise OperationExecutionError(
                "the worker ran past its 10s timeout", outcome="limit_exhausted"
            )

        double.executor = fail
        result = self.call_operation(
            "concorde-code-review", dict(self.task), double=double
        )
        self.assertEqual("failed", result["status"], result)
        reviewed = result["output"]["data"]["reviews"][0]["data"]
        self.assertEqual("incomplete", reviewed["status"])
        reference = result["output"]["data"]["artifacts"][0]
        private = json.loads(
            (self.root / reference["path"]).with_suffix(".execution.json").read_text()
        )
        self.assertEqual("execution_limit", private["failure"]["code"])
        self.assertIsNone(private["usage"])
        self.assertEqual(
            "limit_exhausted", read_change(self.root, required=True)["status"]
        )


class ExplicitComponentTests(unittest.TestCase):
    """Components are explicit caller work, admitted only from current parent intent."""

    setUp = ReviewTests.setUp
    double = ReviewTests.double
    call_operation = ReviewTests.call_operation

    def prepare_parent(self):
        self.task = {
            "target_id": "scope.bank",
            "task": "Implement the transfer contract",
        }
        for operation in ("plan", "tasks"):
            result = self.call_operation("concorde-" + operation)
            self.assertEqual("succeeded", result["status"], result)
        change = read_change(self.root, required=True)
        from concorde.implementation.implement import component_intent

        selected = [
            t
            for t in change["targets"]["scope.bank"]["tasks"]
            if t["target_id"] == "service.transfer"
        ]
        self.assertTrue(selected)
        return {"target_id": "service.transfer", "task": component_intent(selected)}

    @verifies("scenario.implementation.caller-components")
    def test_component_work_returns_to_caller_and_preserves_root_owner(self):
        child = self.prepare_parent()
        result = self.call_operation("concorde-implement")
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("unsupported", result["output"]["data"]["outcome"])
        self.assertIn("service.transfer", result["output"]["data"]["answer"])
        self.assertEqual([], self.model.calls)
        self.assertNotIn(
            "service.transfer", read_change(self.root, required=True)["targets"]
        )
        for operation in ("plan", "tasks", "implement", "validate"):
            result = self.call_operation("concorde-" + operation, child)
            self.assertEqual("succeeded", result["status"], result)
            self.assertEqual(
                "scope.bank", read_change(self.root, required=True)["target_id"]
            )
        result = self.call_operation("concorde-implement")
        self.assertEqual("succeeded", result["status"], result)
        parent = read_change(self.root, required=True)["targets"]["scope.bank"]
        self.assertIn("service.transfer", parent["component_revisions"])
        self.assertTrue(all(t["complete"] for t in parent["tasks"]))
        result = self.call_operation("concorde-validate")
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        code = self.root / "app/transfer.py"
        code.write_text(code.read_text() + "\n# changed component\n")
        result = self.call_operation("concorde-implement")
        self.assertEqual("unsupported", result["output"]["data"]["outcome"])
        self.assertEqual([], self.model.calls)

    @verifies("scenario.review.explicit-components")
    def test_code_free_parent_aggregates_fresh_component_review_without_child_work(
        self,
    ):
        child = self.prepare_parent()
        for operation in ("plan", "tasks", "implement", "validate"):
            result = self.call_operation("concorde-" + operation, child)
            self.assertEqual("succeeded", result["status"], result)
        result = self.call_operation("concorde-implement")
        self.assertEqual("succeeded", result["status"], result)
        state = read_change(self.root, required=True)
        self.assertNotIn("coordination", state["targets"]["scope.bank"])
        result = self.call_operation("concorde-code-review")
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual(["code-review"], [c["stage"] for c in self.model.calls])
        self.assertEqual(
            ["service.transfer"],
            [r["data"]["target_id"] for r in result["output"]["data"]["reviews"]],
        )
        self.assertEqual(child["task"], self.model.calls[0]["snapshot"]["task"])
        state = read_change(self.root, required=True)
        self.assertNotIn("scope.bank", state.get("reviews", {}))
        self.assertTrue(state["review_requirements"]["scope.bank"]["code"])
        from concorde.review.review import current_code_scope, verify_required

        parent = Invocation(
            "concorde-code-review", self.configuration, self.task, self.host
        )
        references = current_code_scope(parent)
        self.assertTrue(references)
        verify_required(parent)
        # Neither a changed question nor corrupt persisted bytes can borrow the aggregate.
        changed = Invocation(
            "concorde-code-review",
            self.configuration,
            {**self.task, "constraints": ["Other intent"]},
            self.host,
        )
        self.assertIsNone(current_code_scope(changed))
        changed_task = Invocation(
            "concorde-code-review",
            self.configuration,
            {**self.task, "task": "Unrelated parent question"},
            self.host,
        )
        self.assertIsNone(current_code_scope(changed_task))
        parent_source = self.root / "specs/bank/module.md"
        original_parent = parent_source.read_bytes()
        parent_source.write_bytes(original_parent + b"\nChanged parent contract.\n")
        self.assertIsNone(current_code_scope(parent))
        parent_source.write_bytes(original_parent)
        self.assertIsNotNone(current_code_scope(parent))
        report = self.root / references[0]["path"]
        original = report.read_bytes()
        report.write_bytes(original + b"\n")
        self.assertIsNone(current_code_scope(parent))
        report.write_bytes(original)
        code = self.root / "app/transfer.py"
        code.write_text(code.read_text() + "\n# changed after review\n")
        self.assertIsNone(current_code_scope(parent))
        result = self.call_operation("concorde-code-review")
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual(["code-review"], [c["stage"] for c in self.model.calls])
        self.assertIsNotNone(current_code_scope(parent))
        # Current review is not fabricated completion of the changed implementation.
        result = self.call_operation("concorde-validate")
        self.assertEqual("blocked", result["status"], result)

        def concurrent_parent_edit(stage, snapshot, data, cwd):
            if stage == "code-review":
                parent_source.write_bytes(
                    original_parent + b"\nConcurrent parent contract edit.\n"
                )

        result = self.call_operation(
            "concorde-code-review", callback=concurrent_parent_edit
        )
        self.assertEqual("stale_context", result["errors"][0]["code"], result)
        self.assertIsNone(current_code_scope(parent))

    @verifies("scenario.implementation.component-stale-parent")
    def test_stale_parent_or_mismatched_component_request_is_rejected(self):
        child = self.prepare_parent()
        for request in (
            {**child, "task": "A different task"},
            {**child, "constraints": ["Unaccepted constraint"]},
        ):
            before = read_change(self.root, required=True)["targets"]
            result = self.call_operation("concorde-plan", request)
            self.assertEqual("blocked", result["status"], result)
            self.assertEqual([], self.model.calls)
            self.assertEqual(before, read_change(self.root, required=True)["targets"])
        spec = self.root / "specs/bank/module.md"
        spec.write_text(
            spec.read_text() + "\nThe calling agent changed this contract.\n"
        )
        before = read_change(self.root, required=True)["targets"]
        result = self.call_operation("concorde-plan", child)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual([], self.model.calls)
        self.assertEqual(before, read_change(self.root, required=True)["targets"])
