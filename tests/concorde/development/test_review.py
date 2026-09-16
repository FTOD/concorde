"""Review mechanism tests. Process doubles do not measure semantic detection quality."""
import json
import subprocess
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch

from concorde.harness.change_worktree import WORK_PATH, ensure_change, read_change, save_change
from concorde.harness.permissions import PermissionPolicyError
from concorde.spec.typed_data import DATA_SCHEMAS, typed
from concorde.spec.verification import verifies
from concorde.development.capability_service import CapabilityHost, run_capability
from concorde.development.capability_host import Invocation
from concorde.development.review import current, inputs
from tests.concorde.spec.support import CONFIGURATION, PACKAGE, ModelProcessDouble, project, update_document_declaration


class ReviewTests(unittest.TestCase):
    @verifies("scenario.development.flow-execution")
    def test_interrupted_review_reports_status_persistence_failure(self):
        from concorde.harness.worker_executor import CapabilityExecutionError

        ensure_change(self.root, task=self.task, allow_primary=True)
        before = read_change(self.root, required=True)
        double = self.double()
        execute = double.executor

        def interrupted(invocation, **options):
            if invocation.stage == "spec-review":
                raise CapabilityExecutionError("controlled interruption", outcome="cancelled")
            return execute(invocation, **options)

        double.executor = interrupted
        with patch("concorde.development.review.progress", side_effect=OSError("cannot save")):
            result = self.review("spec", double=double)
        # The failed Review result and its incomplete report survive the lost status write,
        # which is reported beside them rather than replacing them.
        self.assertEqual("failed", result["status"], result)
        self.assertEqual("concorde-review-response", result["output"]["type_id"])
        data = result["output"]["data"]
        self.assertEqual("failed", data["outcome"])
        self.assertEqual(["incomplete"], [review["data"]["status"] for review in data["reviews"]])
        self.assertIn("execution_cancelled", data["reviews"][0]["data"]["answer"])
        self.assertTrue(data["artifacts"])
        execution = json.loads((self.root / data["artifacts"][0]["path"]).with_suffix(".execution.json").read_text())
        self.assertEqual("execution_cancelled", execution["failure"]["code"])
        self.assertIn("cannot save", execution["failure"]["persistence"])
        self.assertIn("state_persistence_failed", [item["code"] for item in result["errors"]])
        self.assertIn("execution_cancelled", [item["code"] for item in result["errors"]])
        self.assertEqual(before["status"], read_change(self.root, required=True)["status"])

    @verifies("scenario.development.flow-execution")
    def test_fresh_review_reconciles_removed_members_and_restores_required_currentness(self):
        from concorde.development.review import require_reviews, verify_required
        from concorde.harness.worker_executor import CapabilityExecutionError
        from concorde.spec.initialize import empty_target
        from concorde.spec.repository import SpecError
        from tests.concorde.spec.support import module_document, write_document
        for mode in ("code", "spec"):
            with self.subTest(mode=mode):
                fixture = ReviewTests()
                fixture.setUp()
                try:
                    path = fixture.root / '.concorde/specs.json'
                    registry = json.loads(path.read_text())
                    for name in ('first', 'second'):
                        target_id = 'module.' + name
                        document = 'specs/' + name + '/module.md'
                        peer = empty_target(target_id, 'module', name, [document])
                        peer['files'] = ['app/transfer.py']
                        if mode == 'spec':
                            peer['references'] = [{'kind': 'module', 'id': 'service.transfer'}]
                        registry['targets'].append(peer)
                        file = fixture.root / document
                        file.parent.mkdir()
                        write_document(fixture.root, document, module_document('document.' + name, target_id, name,
                            'Observe the shared transfer calculation.',
                            '### scenario.' + name + '.read — Read the result\n\n'
                            '- GIVEN a valid transfer\n- WHEN its result is read\n- THEN the remaining balance is returned\n',
                            ('The shared calculation supplies the result.', [{
                                'id': 'entity.' + name + '.shared', 'title': 'Shared calculation',
                                'kind': 'function', 'responsibility': 'Compute the remaining balance.',
                                'files': ['app/transfer.py']}]), '',
                            'flowchart TB\n    shared["Shared calculation"]'))
                    path.write_text(json.dumps(registry))
                    planned = fixture.call_capability('concorde-plan')
                    self.assertEqual('succeeded', planned['status'], planned)
                    require_reviews(fixture.invocation(), True, modes=[mode])
                    first = fixture.review(mode)
                    self.assertEqual('succeeded', first['status'], first)
                    verify_required(fixture.invocation())
                    field = 'shared_spec_reviews' if mode == 'spec' else 'shared_implementation_reviews'
                    original = read_change(fixture.root, required=True)[field]['service.transfer']
                    self.assertEqual({'module.first', 'module.second'}, set(original))
                    artifacts = {r['artifact']['path']: (fixture.root / r['artifact']['path']).read_bytes()
                                 for r in original.values()}
                    # Change real fixture membership, first leaving one peer and then none.
                    # Spec removal removes the Module identity; live old-impact consumers
                    # must continue to be required when only a reference is removed.
                    for removed, remaining in (('first', {'module.second'}), ('second', set())):
                        registry = json.loads(path.read_text())
                        peer = next(t for t in registry['targets'] if t['id'] == 'module.' + removed)
                        document = fixture.root / peer['documents'][0]
                        if mode == 'spec':
                            registry['targets'].remove(peer)
                            document.unlink()
                            Path(str(document) + ".json").unlink()
                        else:
                            peer['files'] = []
                            metadata_path = Path(str(document) + '.json')
                            metadata = json.loads(metadata_path.read_text())
                            for entity in metadata['entities']:
                                entity.pop('files', None)
                                entity.pop('pending', None)
                            metadata_path.write_text(json.dumps(metadata))
                        path.write_text(json.dumps(registry))
                        with self.assertRaises(SpecError):
                            verify_required(fixture.invocation())
                        before = read_change(fixture.root, required=True)[field]['service.transfer']
                        double = fixture.double()
                        execute = double.executor
                        def interrupt(invocation, **options):
                            if invocation.stage == mode + '-review':
                                raise CapabilityExecutionError('controlled stop', outcome='cancelled')
                            return execute(invocation, **options)
                        double.executor = interrupt
                        stopped = fixture.review(mode, double=double)
                        self.assertEqual('failed', stopped['status'], stopped)
                        retained = read_change(fixture.root, required=True)[field]['service.transfer']
                        self.assertEqual(remaining, set(retained))
                        for key in remaining:
                            self.assertEqual(before[key], retained[key])
                        with self.assertRaises(SpecError):
                            verify_required(fixture.invocation())
                        fresh = fixture.review(mode)
                        self.assertEqual('succeeded', fresh['status'], fresh)
                        verify_required(fixture.invocation())
                        self.assertEqual(remaining, set(read_change(fixture.root, required=True)[field]['service.transfer']))
                        self.assertTrue(all((fixture.root / p).read_bytes() == data for p, data in artifacts.items()))
                finally:
                    fixture.doCleanups()

    @verifies("scenario.development.flow-execution")
    def test_scope_scheduler_change_invalidates_accepted_review(self):
        from concorde.development import review
        from concorde.spec.repository import SpecError
        ensure_change(self.root, task=self.task, allow_primary=True)
        schedulers = (
            "src/concorde/development/review.py",
            "src/concorde/development/coordination_flow.py",
            "src/concorde/development/loop_flow.py",
            "src/concorde/development/specify_flow.py",
        )
        for mode in ("spec", "code"):
            result = self.review(mode)
            self.assertEqual("succeeded", result["status"], result)
            run = self.invocation()
            # This consumer binds application code, not the Framework scheduler.
            self.assertTrue(set(schedulers).isdisjoint(
                run.repository.implementation_files(run.target)))
            before, _ = inputs(run, mode)
            accepted = current(run, mode, required=True)
            self.assertIsNotNone(accepted)
            original = review.read_file
            for scheduler in schedulers:
                with self.subTest(mode=mode, scheduler=scheduler):
                    def changed(root, path):
                        data = original(root, path)
                        return (data + b"\n# scheduling revision\n"
                                if root == run.host.package_root and path == scheduler else data)
                    # Vary one runtime source's observed bytes without changing the
                    # package, its generated binding, or the consumer's sources.
                    with patch.object(review, "read_file", side_effect=changed):
                        after, _ = inputs(run, mode)
                        self.assertNotEqual(before["input_digest"], after["input_digest"])
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

    @verifies("scenario.development.flow-execution")
    def test_reviewer_interruptions_survive_enclosing_flows_and_final_events(self):
        from concorde.harness.worker_executor import CapabilityExecutionError
        from typing import Literal
        outcomes: tuple[Literal['cancelled', 'limit_exhausted', 'failed'], ...] = ('cancelled', 'limit_exhausted', 'failed')
        outcome: Literal['cancelled', 'limit_exhausted', 'failed']
        for capability, review_stage in (("concorde-specify-loop", "spec-review"),
                                         ("concorde-dev-loop", "spec-review"),
                                         ("concorde-dev-loop", "code-review")):
            for outcome in outcomes:
                with self.subTest(capability=capability, review_stage=review_stage, outcome=outcome):
                    fixture = ReviewTests()
                    fixture.setUp()
                    try:
                        unrelated = fixture.root / "unrelated-note.txt"
                        unrelated.write_text("Preserve this local edit.\n")
                        double = fixture.double()
                        execute = double.executor
                        stages, events, prior = [], [], {}
                        candidate_bytes, review_outputs = {}, []
                        from concorde.development import review as review_module
                        original_review = review_module.review
                        def capture_review(*args, **kwargs):
                            output = original_review(*args, **kwargs)
                            review_outputs.append(output["data"])
                            return output
                        def interrupted(invocation, **options):
                            stages.append(invocation.stage)
                            if invocation.stage == review_stage:
                                prior.update(read_change(fixture.root, required=True))
                                for relative in ("app/transfer.py", "specs/transfer/module.md"):
                                    candidate_bytes[relative] = (fixture.root / relative).read_bytes()
                                raise CapabilityExecutionError("controlled reviewer failure", outcome=outcome)
                            return execute(invocation, **options)
                        double.executor = interrupted
                        def observe(host, event, **details):
                            events.append({"event": event, **details})
                        with patch.object(CapabilityHost, "observe", observe), \
                             patch.object(review_module, "review", side_effect=capture_review):
                            result = fixture.call_capability(capability,
                                {**fixture.task, "specify": False, "run_reviews": True}, double=double)
                        self.assertEqual("failed", result["status"], result)
                        self.assertEqual("failed", result["output"]["data"]["outcome"])
                        state = read_change(fixture.root, required=True)
                        self.assertEqual(outcome, state["status"])
                        self.assertEqual("failed", review_outputs[-1]["outcome"])
                        self.assertEqual("incomplete", review_outputs[-1]["reviews"][0]["data"]["status"])
                        for relative, before_bytes in candidate_bytes.items():
                            self.assertEqual(before_bytes, (fixture.root / relative).read_bytes())
                        self.assertEqual(prior["targets"], state["targets"])
                        self.assertEqual(prior.get("authored_specs"), state.get("authored_specs"))
                        self.assertEqual(prior.get("gap_history"), state.get("gap_history"))
                        self.assertEqual("Preserve this local edit.\n", unrelated.read_text())
                        self.assertEqual(prior["review_requirements"], state["review_requirements"])
                        if outcome != "failed":
                            self.assertEqual("execution_cancelled" if outcome == "cancelled" else "execution_limit",
                                             result["errors"][0]["code"])
                        self.assertEqual(review_stage, stages[-1])
                        flow_stages = [event["stage"] for event in events
                                       if event["event"] == "stage_started"]
                        stopping_stage = "review_spec" if review_stage == "spec-review" else "review_code"
                        self.assertEqual(stopping_stage, flow_stages[-1])
                        if review_stage == "spec-review":
                            self.assertFalse(set(stages) & {"plan", "tasks", "implementation", "code-review"})
                        else:
                            self.assertEqual(1, stages.count("tasks"))
                            self.assertEqual(1, stages.count("implementation"))
                            self.assertTrue(all(t["complete"] for t in state["targets"]
                                                [fixture.task["target_id"]]["tasks"]))
                        reviews = state["reviews"][fixture.task["target_id"]]
                        self.assertEqual("incomplete", reviews[review_stage.split("-")[0]]["status"])
                        report = json.loads((fixture.root / reviews[review_stage.split("-")[0]]
                                             ["artifact"]["path"]).read_text())["data"]
                        self.assertEqual("incomplete", report["status"])
                        self.assertEqual([], report["findings"])
                        self.assertIn("execution_cancelled" if outcome == "cancelled" else
                                      "execution_limit" if outcome == "limit_exhausted" else "execution_failed",
                                      report["answer"])
                        self.assertFalse(any(event.get("stage") == "ready" for event in events))
                        self.assertTrue(result["output"]["data"]["artifacts"])
                        finished = [event for event in events if event["event"] == "capability_finished"
                                    and event["capability"] == capability]
                        self.assertEqual(outcome, finished[-1]["status"])
                        review_finished = [event for event in events
                                           if event["event"] == "capability_finished"
                                           and event["capability"] == "concorde-review"]
                        self.assertTrue(review_finished)
                        self.assertEqual(outcome, review_finished[-1]["status"])
                        if capability == "concorde-dev-loop":
                            graph = state["graph"][fixture.task["target_id"]]
                            self.assertEqual(0, graph["repair_iteration"])
                            self.assertEqual(outcome, graph["transitions"][-1]["status"])
                            self.assertEqual("END", graph["transitions"][-1]["to"])
                    finally:
                        fixture.doCleanups()

    @verifies("scenario.development.task-scope-repair", "scenario.development.dev-loop-coordinated",
              "scenario.development.dev-loop-spec-gap")
    def test_nested_scope_repair_requires_resolved_gap_from_recorded_component_intent(self):
        from copy import deepcopy
        from concorde.spec.repository import digest

        task = {"target_id": "scope.bank", "task": "Implement the audited transfer contract"}
        def coordinate(stage, snapshot, data, cwd):
            if stage == "tasks" and snapshot["target_id"] == "scope.bank":
                data["tasks"][0].update(target_id="scope.audit", description="Implement audited transfers.")
        def initial(stage, snapshot, data, cwd):
            coordinate(stage, snapshot, data, cwd)
            if stage == "tasks" and snapshot["target_id"] == "scope.bank":
                data["tasks"][0]["acceptance"] += " Host validation must finish first."
            if snapshot["target_id"] == "service.transfer":
                self.missing("spec-review")(stage, snapshot, data, cwd)
        first = self.call_capability("concorde-dev-loop", task, callback=initial)
        self.assertEqual("blocked", first["status"], first)
        state = read_change(self.root, required=True)
        before = state["targets"]["scope.bank"]
        cached = before["coordination"]["scope.audit"]
        child = state["targets"]["scope.audit"]
        nested = child["coordination"]["service.transfer"]
        self.assertEqual(cached["task"], child["task"])
        self.assertEqual(nested["gaps"], cached["gaps"])
        self.assertEqual("service.transfer", cached["gaps"][0]["target_id"])
        self.assertTrue(all(item["target_id"] == "service.transfer" and item["task"] == nested["task"]
                            for item in state["gap_history"]))
        request = {**task, "repair_task_scope": {"tasks_digest": digest(before["tasks"])}}
        def repair(stage, snapshot, data, cwd):
            coordinate(stage, snapshot, data, cwd)
            if stage == "tasks" and snapshot["target_id"] == "scope.bank":
                data["tasks"][0]["id"] = "task.audit.scope-repair"
        def rejected():
            prior = read_change(self.root, required=True)
            result = self.call_capability("concorde-dev-loop", request, callback=repair)
            self.assertNotEqual("succeeded", result["status"], result)
            self.assertIn("contract gaps before repairing its task boundary", str(result))
            after = read_change(self.root, required=True)
            for target_id in ("scope.bank", "scope.audit"):
                for field in ("tasks", "task_history", "coordination"):
                    self.assertEqual(prior["targets"][target_id].get(field),
                                     after["targets"][target_id].get(field))
            self.assertEqual(prior["gap_history"], after["gap_history"])
        rejected()

        document = self.root / "specs/transfer/module.md"
        document.write_text(document.read_text() + "\nTransfer owns the daily-limit admission rule.\n")
        reviewed = self.call_capability("concorde-review", {
            "target_id": "service.transfer", "task": nested["task"], "review_mode": "spec"})
        self.assertEqual("succeeded", reviewed["status"], reviewed)
        resolved = read_change(self.root, required=True)["gap_history"]
        self.assertTrue(resolved)
        self.assertTrue(all(item["status"] == "resolved" for item in resolved))
        self.assertEqual(cached["gaps"],
                         read_change(self.root, required=True)["targets"]["scope.bank"]["coordination"]["scope.audit"]["gaps"])
        # Alter only isolated fixture evidence; neither unrelated history nor a broken
        # coordination chain can authorize replacement of the parent's accepted tasks.
        for mismatch in ("missing", "target_id", "task", "context", "reopened",
                         "child-intent", "nested-intent", "missing-coordination", "legacy-cache"):
            with self.subTest(provenance=mismatch):
                state = read_change(self.root, required=True)
                state["gap_history"] = deepcopy(resolved)
                state["targets"]["scope.audit"] = deepcopy(child)
                state["targets"]["scope.bank"]["coordination"] = deepcopy(before["coordination"])
                if mismatch == "missing":
                    state["gap_history"] = []
                elif mismatch in {"target_id", "task"}:
                    state["gap_history"][0][mismatch] = "unrelated"
                elif mismatch == "context":
                    state["gap_history"][0]["contexts"] = ["sha256:" + "f" * 64]
                elif mismatch == "reopened":
                    state["gap_history"][0]["status"] = "open"
                elif mismatch == "child-intent":
                    state["targets"]["scope.audit"]["task"] = "Unrelated audit task"
                elif mismatch == "nested-intent":
                    state["targets"]["scope.audit"]["coordination"]["service.transfer"]["task"] = "Unrelated transfer task"
                elif mismatch == "missing-coordination":
                    state["targets"]["scope.audit"]["coordination"] = {}
                else:
                    state["targets"]["scope.bank"]["coordination"]["scope.audit"]["gaps"][0].pop("context_id")
                save_change(self.root, state)
                rejected()
        state = read_change(self.root, required=True)
        state["gap_history"] = resolved
        state["targets"]["scope.audit"] = child
        state["targets"]["scope.bank"]["coordination"] = before["coordination"]
        save_change(self.root, state)
        result = self.call_capability("concorde-dev-loop", request, callback=repair)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        state = read_change(self.root, required=True)
        parent = state["targets"]["scope.bank"]
        self.assertEqual(before["tasks"], parent["task_history"][-1]["tasks"])
        self.assertEqual(before["coordination"], parent["task_history"][-1]["coordination"])
        self.assertEqual(resolved, state["gap_history"])
        self.assertNotEqual(cached["task"], parent["coordination"]["scope.audit"]["task"])
        self.assertTrue(all(item["complete"] for item in parent["tasks"]))

    @verifies("scenario.development.task-scope-repair", "scenario.development.dev-loop-coordinated",
              "scenario.development.dev-loop-spec-gap", "scenario.development.standalone-review")
    def test_scope_repair_accepts_cached_component_gap_only_after_attributed_resolution(self):
        from copy import deepcopy
        from concorde.spec.repository import digest

        task = {"target_id": "scope.bank", "task": "Implement the transfer contract"}
        def initial(stage, snapshot, data, cwd):
            if stage == "tasks" and snapshot["target_id"] == "scope.bank":
                data["tasks"][0]["acceptance"] += " Host validation must finish first."
            if snapshot["target_id"] == "service.transfer":
                self.missing("spec-review")(stage, snapshot, data, cwd)
        first = self.call_capability("concorde-dev-loop", task, callback=initial)
        self.assertEqual("blocked", first["status"], first)
        before = read_change(self.root, required=True)["targets"]["scope.bank"]
        cached = before["coordination"]["service.transfer"]
        self.assertTrue(cached["gaps"])
        request = {**task, "repair_task_scope": {"tasks_digest": digest(before["tasks"])}}
        def repair(stage, snapshot, data, cwd):
            if stage == "tasks" and snapshot["target_id"] == "scope.bank":
                data["tasks"][0]["id"] = "task.transfer.scope-repair"
        def rejected():
            history = read_change(self.root, required=True)["gap_history"]
            result = self.call_capability("concorde-dev-loop", request, callback=repair)
            self.assertNotEqual("succeeded", result["status"], result)
            self.assertIn("contract gaps before repairing its task boundary", str(result))
            state = read_change(self.root, required=True)
            parent = state["targets"]["scope.bank"]
            self.assertEqual(before["tasks"], parent["tasks"])
            self.assertEqual(before["coordination"], parent["coordination"])
            self.assertEqual(before.get("task_history", []), parent.get("task_history", []))
            self.assertEqual(history, state["gap_history"])
        rejected()  # The actual failed component left an open prerequisite.

        document = self.root / "specs/transfer/module.md"
        document.write_text(document.read_text() + "\nTransfer owns the daily-limit admission rule.\n")
        reviewed = self.call_capability("concorde-review", {
            "target_id": "service.transfer", "task": cached["task"], "review_mode": "spec"})
        self.assertEqual("succeeded", reviewed["status"], reviewed)
        resolved = read_change(self.root, required=True)["gap_history"]
        self.assertTrue(resolved)
        self.assertTrue(all(item["status"] == "resolved" for item in resolved))
        self.assertEqual(cached["gaps"],
                         read_change(self.root, required=True)["targets"]["scope.bank"]["coordination"]["service.transfer"]["gaps"])

        # Corrupt only isolated fixture history to prove unknown or unrelated evidence
        # cannot erase the real cached blocker. Restore the accepted Host history below.
        for mismatch in ("missing", "target_id", "task", "question", "context", "reopened"):
            with self.subTest(history=mismatch):
                state = read_change(self.root, required=True)
                history = deepcopy(resolved)
                if mismatch == "missing":
                    history = []
                elif mismatch in {"target_id", "task"}:
                    history[0][mismatch] = "unrelated"
                elif mismatch == "question":
                    history[0]["gap"]["question"] = "An unrelated question?"
                elif mismatch == "context":
                    history[0]["contexts"] = ["sha256:" + "f" * 64]
                else:
                    history[0]["status"] = "open"
                state["gap_history"] = history
                save_change(self.root, state)
                rejected()
        state = read_change(self.root, required=True)
        state["gap_history"] = resolved
        save_change(self.root, state)
        result = self.call_capability("concorde-dev-loop", request, callback=repair)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        state = read_change(self.root, required=True)
        parent = state["targets"]["scope.bank"]
        self.assertEqual(before["tasks"], parent["task_history"][-1]["tasks"])
        self.assertEqual(request["repair_task_scope"]["tasks_digest"], parent["task_history"][-1]["tasks_digest"])
        self.assertEqual(before["coordination"], parent["task_history"][-1]["coordination"])
        self.assertNotEqual(cached["task"], parent["coordination"]["service.transfer"]["task"])
        self.assertEqual(resolved, state["gap_history"])
        self.assertTrue(all(item["complete"] for item in parent["tasks"]))
        calls = [(call["snapshot"]["target_id"], call["stage"]) for call in self.model.calls]
        for phase in ("spec-review", "plan", "tasks", "implementation"):
            self.assertIn(("service.transfer", phase), calls)

    @verifies("scenario.development.task-scope-repair", "scenario.development.dev-loop-coordinated")
    def test_coordinated_scope_repair_preserves_state_on_rerouting_or_component_gap(self):
        from concorde.spec.repository import digest
        from concorde.harness.change_worktree import record_task_gaps
        task = {"target_id": "scope.bank", "task": "Implement the transfer contract"}
        def incomplete(stage, snapshot, data, cwd):
            if stage == "tasks" and snapshot["target_id"] == "scope.bank":
                data["tasks"][0]["acceptance"] += " Host validation must finish first."
            if stage == "implementation":
                for item in data["tasks"]:
                    item["complete"] = False
        self.call_capability("concorde-dev-loop", task, callback=incomplete)
        before = read_change(self.root, required=True)["targets"]["scope.bank"]
        request = {**task, "repair_task_scope": {"tasks_digest": digest(before["tasks"])}}
        def reroute(stage, snapshot, data, cwd):
            if stage == "tasks" and snapshot["target_id"] == "scope.bank":
                data["tasks"][0].update(id="task.repaired", target_id="module.ledger")
        failed = self.call_capability("concorde-dev-loop", request, callback=reroute)
        self.assertNotEqual("succeeded", failed["status"], failed)
        after = read_change(self.root, required=True)["targets"]["scope.bank"]
        self.assertEqual(before["tasks"], after["tasks"])
        self.assertEqual(before["coordination"], after["coordination"])
        self.assertFalse(after.get("task_history"))
        # Host-owned fixture evidence for a real prerequisite in the old child intent.
        record_task_gaps(self.root, "service.transfer", before["coordination"]["service.transfer"]["task"],
            "spec-review", [{**self.gap(), "target_id": "service.transfer", "context_id": "sha256:" + "b" * 64}],
            "sha256:" + "a" * 64, review_input_digest="sha256:" + "c" * 64)
        def repair(stage, snapshot, data, cwd):
            if stage == "tasks" and snapshot["target_id"] == "scope.bank":
                data["tasks"][0]["id"] = "task.repaired"
        failed = self.call_capability("concorde-dev-loop", request, callback=repair)
        self.assertNotEqual("succeeded", failed["status"], failed)
        after = read_change(self.root, required=True)["targets"]["scope.bank"]
        self.assertEqual(before["tasks"], after["tasks"])
        self.assertEqual(before["coordination"], after["coordination"])
        self.assertFalse(after.get("task_history"))
        self.assertEqual("open", read_change(self.root, required=True)["gap_history"][-1]["status"])

    @verifies("scenario.development.dev-loop-spec-gap", "scenario.development.standalone-review")
    def test_lifecycle_only_standalone_review_cannot_resolve_a_required_gap(self):
        first = self.call_capability("concorde-dev-loop", callback=self.missing("spec-review"))
        self.assertEqual("blocked", first["status"], first)
        original = read_change(self.root, required=True)["gap_history"][0]
        self.assertIn("review_input_digest", original)
        reviewed = self.review()
        self.assertEqual("succeeded", reviewed["status"], reviewed)
        actual = reviewed["output"]["data"]["reviews"][0]["data"]
        self.assertEqual(original["review_input_digest"], actual["input_digest"])
        self.assertNotEqual(original["gap"]["context_id"], actual["context_id"])
        self.assertEqual(original, read_change(self.root, required=True)["gap_history"][0])
        resumed = self.call_capability("concorde-dev-loop")
        self.assertNotEqual("succeeded", resumed["status"], resumed)
        self.assertFalse(any(call["stage"] == "spec-review" for call in self.model.calls))

    @verifies("scenario.development.dev-loop-spec-gap")
    def test_legacy_gap_identity_is_not_inferred_from_a_later_review(self):
        self.call_capability("concorde-dev-loop", callback=self.missing("spec-review"))
        state = read_change(self.root, required=True)
        state["gap_history"][0].pop("review_input_digest")
        save_change(self.root, state)  # legacy fixture, not a production migration
        original = read_change(self.root, required=True)["gap_history"][0]
        self.review()
        self.assertEqual(original, read_change(self.root, required=True)["gap_history"][0])
        document = self.root / "specs/transfer/module.md"
        document.write_text(document.read_text() + "\nTransfer owns the requested admission rule.\n")
        result = self.call_capability("concorde-dev-loop")
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("resolved", read_change(self.root, required=True)["gap_history"][0]["status"])

    @verifies("scenario.development.task-scope-repair", "scenario.development.dev-loop-coordinated")
    def test_coordinated_scope_repair_rebinds_changed_intent_without_redoing_unchanged_component(self):
        from concorde.spec.repository import digest
        task = {"target_id": "scope.bank", "task": "Implement transfer and ledger contracts"}
        ledger = {"id": "task.ledger", "target_id": "module.ledger", "description": "Implement ledger reads.",
                  "acceptance": "Return known balances and reject unknown accounts.", "complete": False}
        def initial(stage, snapshot, data, cwd):
            if stage == "tasks" and snapshot["target_id"] == "scope.bank":
                data["tasks"][0]["acceptance"] += " Host validation and commit must finish before task completion."
                data["tasks"].insert(0, dict(ledger))
            if stage == "implementation" and snapshot["target_id"] == "service.transfer":
                for item in data["tasks"]:
                    item["complete"] = False
        first = self.call_capability("concorde-dev-loop", task, callback=initial)
        self.assertNotEqual("succeeded", first["status"], first)
        before = read_change(self.root, required=True)["targets"]["scope.bank"]
        self.assertEqual("completed", before["coordination"]["module.ledger"]["implementation_status"])
        child_intent = before["coordination"]["service.transfer"]["task"]
        source_bytes = {p: (self.root / p).read_bytes() for p in (
            "specs/bank/module.md", "specs/transfer/module.md", "specs/transfer/promises.md", "specs/ledger/module.md")}
        def repair(stage, snapshot, data, cwd):
            if stage == "tasks" and snapshot["target_id"] == "scope.bank":
                data["tasks"][0]["id"] = "task.transfer.scope-repair"
                data["tasks"].insert(0, {**ledger, "id": "task.ledger.scope-repair"})
        result = self.call_capability("concorde-dev-loop", {**task,
            "repair_task_scope": {"tasks_digest": digest(before["tasks"])}}, callback=repair)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        state = read_change(self.root, required=True)
        parent = state["targets"]["scope.bank"]
        self.assertEqual(before["coordination"], parent["task_history"][-1]["coordination"])
        self.assertNotEqual(child_intent, parent["coordination"]["service.transfer"]["task"])
        self.assertEqual(parent["coordination"]["service.transfer"]["task"], state["targets"]["service.transfer"]["task"])
        calls = [(call["snapshot"]["target_id"], call["stage"]) for call in self.model.calls]
        self.assertIn(("service.transfer", "plan"), calls)
        self.assertIn(("service.transfer", "implementation"), calls)
        self.assertNotIn(("module.ledger", "implementation"), calls)
        self.assertFalse(any(stage == "specify" for _, stage in calls))
        for path, content in source_bytes.items():
            self.assertEqual(content, (self.root / path).read_bytes())

    @verifies("scenario.development.task-history-identities", "scenario.development.task-scope-repair",
              "scenario.planning.tasks-from-plan", "scenario.planning.tasks-id-conflict")
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
            tasks = read_change(self.root, required=True)["targets"]["service.transfer"]["tasks"]
            self.call_capability("concorde-dev-loop", {**self.task,
                "repair_task_scope": {"tasks_digest": digest(tasks)}}, callback=author)
        history = read_change(self.root, required=True)["targets"]["service.transfer"]["task_history"]
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
        state = read_change(self.root, required=True)["targets"]["service.transfer"]
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
        state = read_change(self.root, required=True)["targets"]["service.transfer"]
        self.assertEqual("task.round.2.replanned", state["tasks"][0]["id"])
        self.assertEqual(history, state["task_history"])

    @verifies("scenario.development.validate-blocked")
    def test_deferred_repository_verification_still_requires_passing_host_checks(self):
        # The programmer cannot read this repository-level dependency, but the Host must
        # still execute it after accepting the implementation's fulfilled tasks.
        (self.root / "host_regression.py").write_text("raise AssertionError('repository regression')\n")
        (self.root / "checks/transfer_check.py").write_text("import runpy\nrunpy.run_path('host_regression.py')\n")
        def deferred(stage, snapshot, data, cwd):
            if stage == "implementation":
                data["answer"] = "Implementation fulfilled; repository imports require deferred Host verification."
                self.assertNotIn("host_regression.py", [item["path"] for item in snapshot["implementation_files"]])
        result = self.call_capability("concorde-dev-loop", callback=deferred)
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
        result = self.call_capability("concorde-dev-loop", double=model)
        self.assertEqual("succeeded", result["status"], result)
        for call in model.calls:
            with self.subTest(stage=call["stage"]):
                if call["stage"] == "implementation":
                    self.assertIn("run_checks", call["launch"].tools)
                    report = call["checks"]()
                    self.assertEqual(["check.transfer"], [item["check_id"] for item in report["checks"]])
                    self.assertIn("output_tail", report["checks"][0])
                elif call["stage"] == "code-review":
                    self.assertNotIn("run_checks", call["launch"].tools)
                    self.assertIsNotNone(call["checks"])
                else:
                    self.assertIsNone(call["checks"])
                    self.assertNotIn("run_checks", call["launch"].tools)

    @verifies("scenario.harness.worker-selection")
    def test_each_worker_launches_on_its_own_model_and_thinking_level(self):
        self.configuration = typed("concorde-capability-configuration", {
            "model": "openai-codex/gpt-6-astra", "thinking": "medium",
            "workers": {"task_author": {"thinking": "high"},
                        "planner": {"model": "anthropic/claude-sonnet-5", "thinking": "low"},
                        "programmer": {"model": "openai-codex/gpt-5.6-sol", "timeout_seconds": 5400},
                        "programmer/verifier": {"thinking": "xhigh"}}})
        config_path = self.root / ".concorde/config.json"
        config = json.loads(config_path.read_text())
        config["capability_configuration"] = self.configuration
        config_path.write_text(json.dumps(config))
        result = self.call_capability("concorde-dev-loop")
        self.assertEqual("succeeded", result["status"], result)
        launched = {call["stage"]: (call["launch"].model, call["launch"].thinking) for call in self.model.calls}
        expected = {"plan": ("anthropic/claude-sonnet-5", "low"), "tasks": ("openai-codex/gpt-6-astra", "high"),
                    "implementation": ("openai-codex/gpt-5.6-sol", "medium"),
                    "code-review": ("openai-codex/gpt-6-astra", "medium")}
        self.assertEqual(expected, {stage: launched[stage] for stage in expected})
        programmer = next(call["launch"] for call in self.model.calls if call["stage"] == "implementation")
        self.assertEqual(5400, programmer.timeout_seconds)
        verifier = next(child for child in programmer.children if child.name == "verifier")
        self.assertTrue(verifier.definition.startswith("---\nmodel: openai-codex/gpt-5.6-sol\nthinking: xhigh\n"))
        described = {item["phase"]: (item["model"], item["thinking"]) for item in self.host.descriptions}
        self.assertEqual(expected, {stage: described[stage] for stage in expected if stage in described})

    @verifies("scenario.development.task-scope-repair")
    def test_invalid_scope_repair_cannot_replace_or_complete_original_tasks(self):
        from concorde.spec.repository import digest
        def incomplete(stage, snapshot, data, cwd):
            if stage == "implementation":
                for task in data["tasks"]:
                    task["complete"] = False
        self.call_capability("concorde-dev-loop", callback=incomplete)
        original = read_change(self.root, required=True)["targets"]["service.transfer"]["tasks"]
        request = {**self.task, "repair_task_scope": {"tasks_digest": digest(original)}}
        for invalid in ("completed", "reused_id"):
            def reject(stage, snapshot, data, cwd):
                if stage == "tasks" and invalid == "completed":
                    data["tasks"][0]["complete"] = True
            result = self.call_capability("concorde-dev-loop", request, callback=reject)
            self.assertNotEqual("succeeded", result["status"], result)
            state = read_change(self.root, required=True)["targets"]["service.transfer"]
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
        original = read_change(self.root, required=True)["targets"]["service.transfer"]["tasks"]
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
        state = read_change(self.root, required=True)
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
        self.registry["targets"][3]["references"].append({"kind":"document","id":"document.transfer.promises"})
        (self.root / ".concorde/specs.json").write_text(json.dumps(self.registry))
        update_document_declaration(self.root, "specs/transfer/promises.md",
            owner="service.transfer")
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
            self.assertEqual(["specs/transfer/module.md", "specs/transfer/module.md.json", "specs/transfer/promises.md", "specs/transfer/promises.md.json"], [source["path"] for source in snapshot["spec_resolution"]["sources"]])
            self.assertEqual(["specs/transfer/promises.md"], [x["path"] for x in snapshot["spec_resolution"]["sources"] if x["path"].endswith("promises.md")])
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
                self.assertTrue(all(p == "context.json" or p.startswith(("specs/", ".concorde/protocol/")) for p in policy["read_paths"]), policy["read_paths"])
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
        document = self.root / 'specs/transfer/module.md.json'
        metadata = json.loads(document.read_text())
        for entity in metadata['entities']:
            if entity['id'] == 'entity.transfer.check':
                entity['files'] = ['checks/']
        document.write_text(json.dumps(metadata, indent=2) + '\n')
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
        # A reviewer grant the compiler refuses is simulated at policy compilation.
        ensure_change(self.root, task=self.task, allow_primary=True)
        before = read_change(self.root)
        refused = PermissionPolicyError("simulated: the reviewer grant widens its declared effects")
        with patch("concorde.development.review.compile_policy", side_effect=refused):
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

    def test_failed_reviews_retain_usage_and_failure_privately(self):
        from concorde.harness.worker_executor import CapabilityExecutionError
        double = self.double()
        executor = double.executor
        spent = []
        def fail(invocation, **options):
            outcome = executor(invocation, **options)
            spent.append(outcome.usage)
            raise CapabilityExecutionError("private failed completion diagnostics", outcome="invalid_completion",
                                           usage=outcome.usage)
        double.executor = fail
        failed = self.review(double=double)
        self.assertEqual("failed", failed["status"], failed)
        def private(result):
            path = self.root / result["output"]["data"]["artifacts"][0]["path"]
            return json.loads(path.with_suffix(".execution.json").read_text())
        self.assertEqual(asdict(spent[0]), private(failed)["usage"])
        self.assertEqual("execution_failed", private(failed)["failure"]["code"])
        rejected = self.review(callback=lambda stage, snapshot, data, cwd:
            data.update(input_digest="sha256:" + "0" * 64))
        self.assertEqual("failed", rejected["status"], rejected)
        self.assertEqual(1200, private(rejected)["usage"]["input_tokens"])
        for result in (failed, rejected):
            self.assertNotIn("private failed completion diagnostics", json.dumps(result))
            self.assertNotIn("input_tokens", json.dumps(result))

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
                state = read_change(self.root, required=True)
                observed.append(state["status"])
                self.assertEqual("passed", state["targets"][self.task["target_id"]]["checks"][0]["status"])
        result = self.call_capability("concorde-dev-loop", callback=inspect)
        self.assertEqual("succeeded", result["status"], result)
        stages = [x["stage"] for x in self.model.calls]
        self.assertLess(stages.index("specify"), stages.index("spec-review"))
        self.assertLess(stages.index("spec-review"), stages.index("plan"))
        self.assertLess(stages.index("implementation"), stages.index("code-review"))
        self.assertNotIn("ready", observed)
        self.assertEqual("ready", read_change(self.root, required=True)["status"])
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
        from concorde.distribution.build import load_agent
        first = self.call_capability("concorde-dev-loop", callback=self.missing("spec-review"))
        self.assertEqual("blocked", first["status"], first)
        original = read_change(self.root, required=True)["gap_history"][0]
        self.call_capability("concorde-dev-loop")
        self.assertFalse(any(c["stage"] == "spec-review" for c in self.model.calls))
        rendered = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(rendered, ignore_errors=True))

        def revised(suffix, package_root, name):
            prompt = load_agent(package_root, name)
            if prompt.binding.agent != "spec_reviewer":
                return prompt
            # A rebuilt package's instructions: the rendered file and its binding change together.
            body = prompt.body + suffix
            instructions = rendered / f"spec-reviewer-{hashlib.sha256(body.encode()).hexdigest()}.md"
            instructions.write_text(body, encoding="utf-8")
            binding = replace(prompt.binding, instructions_path=str(instructions),
                instructions_digest="sha256:" + hashlib.sha256(body.encode()).hexdigest())
            return replace(prompt, body=body, binding=replace(binding, digest=binding_digest(binding)))

        def changed(package_root, name):
            return revised("\nClarified task relevance.\n", package_root, name)

        @contextmanager
        def instructions(loader):
            # Admit the test's new instruction binding through the same preflight as a rebuilt
            # package; the worker's effects and contract stay intact.
            resolve = agent_model.resolve_agent
            prompt = loader(PACKAGE, "concorde-spec-reviewer")
            def binding(package, name):
                return prompt.binding if agent_model.agent_key(name) == "spec_reviewer" else resolve(package, name)
            with patch("concorde.development.review.load_agent", side_effect=loader), \
                    patch("concorde.harness.agent_model.resolve_agent", side_effect=binding):
                yield

        def incomplete(stage, snapshot, data, cwd):
            if stage == "spec-review":
                data.update(status="incomplete", answer="Coverage could not be completed.")
        with instructions(changed):
            result = self.call_capability("concorde-dev-loop", callback=incomplete)
            self.assertEqual("failed", result["status"], result)
            self.assertTrue(any(c["stage"] == "spec-review" for c in self.model.calls))
            self.assertEqual(original, read_change(self.root, required=True)["gap_history"][0])

        # Another actual instruction revision permits a completed reassessment.
        # The Host preserves the reviewer's independent finding and old history.
        def changed_again(package_root, name):
            return revised("\nReassess coverage.\n", package_root, name)
        def advisory(stage, snapshot, data, cwd):
            if stage == "spec-review":
                self.missing(stage)(stage, snapshot, data, cwd)
                data["findings"][0]["severity"] = "advisory"
                data["gaps"] = []
        with instructions(changed_again):
            result = self.call_capability("concorde-dev-loop", callback=advisory)
        self.assertEqual("succeeded", result["status"], result)
        state = read_change(self.root, required=True)
        self.assertEqual("resolved", state["gap_history"][0]["status"])
        self.assertEqual(original["gap"], state["gap_history"][0]["gap"])
        self.assertEqual([], state["gaps"])

    @verifies("scenario.development.dev-loop-spec-gap")
    def test_gap_persists_deduplicates_and_requires_spec_repair_before_resume(self):
        result = self.call_capability("concorde-dev-loop", callback=self.missing("spec-review"))
        self.assertEqual("blocked", result["status"], result)
        self.assertNotIn("plan", [x["stage"] for x in self.model.calls])
        before = read_change(self.root, required=True)
        self.assertEqual(1, len(before["gap_history"]))
        retry = self.call_capability("concorde-dev-loop")
        self.assertEqual("blocked", retry["status"], retry)
        self.assertEqual(1, len(read_change(self.root, required=True)["gap_history"]))
        self.assertEqual(1, len(read_change(self.root, required=True)["gaps"]))
        self.assertEqual(before["gaps"][0]["context_id"], retry["output"]["data"]["gaps"][0]["context_id"])
        self.assertNotIn("plan", [x["stage"] for x in self.model.calls])
        spec = self.root / "specs/transfer/module.md"
        spec.write_text(spec.read_text() + "\nThe transfer capability owns a daily limit of 1000 units.\n")
        resumed = self.call_capability("concorde-dev-loop")
        self.assertEqual("succeeded", resumed["status"], resumed)
        state = read_change(self.root, required=True)
        self.assertEqual([], state["gaps"])
        self.assertEqual("resolved", state["gap_history"][0]["status"])
        self.assertEqual("ready", state["status"])
        self.assertNotIn("specify", [x["stage"] for x in self.model.calls])

    @verifies("scenario.development.dev-loop-spec-gap", "scenario.planning.assessment-gap")
    def test_real_task_phases_preserve_gaps_and_resume_after_repair(self):
        for phase in ("context-solve", "plan", "tasks", "implementation"):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as temporary:
                original_root = self.root
                self.root = Path(temporary)
                project(self.root)
                result = self.call_capability("concorde-dev-loop", callback=self.missing(phase))
                self.assertEqual("blocked", result["status"], result)
                self.assertEqual(phase, read_change(self.root, required=True)["gap_history"][0]["phase"])
                spec = self.root / "specs/transfer/module.md"
                spec.write_text(spec.read_text() + "\nThe transfer capability owns the necessary daily limit.\n")
                resumed = self.call_capability("concorde-dev-loop")
                self.assertEqual("succeeded", resumed["status"], resumed)
                self.assertEqual([], read_change(self.root, required=True)["gaps"])
                self.root = original_root

    def test_fast_loop_records_skips_and_cannot_downgrade_required_review(self):
        result = self.call_capability("concorde-dev-loop", {**self.task, "specify": False, "run_reviews": False})
        self.assertEqual("succeeded", result["status"], result)
        state = read_change(self.root, required=True)
        self.assertEqual({"skipped"}, {x["status"] for x in state["reviews"][self.task["target_id"]].values()})
        self.assertIn("spec=skipped", result["output"]["data"]["answer"])
        self.assertIn("code=skipped", result["output"]["data"]["answer"])
        self.assertEqual(2, len(result["output"]["data"]["artifacts"]))
        self.assertFalse(any("review" in x["stage"] for x in self.model.calls))
        result = self.call_capability("concorde-dev-loop", {**self.task, "specify": False, "run_reviews": True}, callback=self.missing("spec-review"))
        self.assertEqual("blocked", result["status"], result)
        retried = self.call_capability("concorde-dev-loop", {**self.task, "specify": False, "run_reviews": False})
        self.assertEqual("blocked", retried["status"], retried)
        self.assertTrue(read_change(self.root, required=True)["review_requirements"][self.task["target_id"]]["spec"])

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
        state = read_change(self.root, required=True)
        state["reviews"][self.task["target_id"]].pop("code")
        save_change(self.root, state)
        def incomplete(stage, snapshot, data, cwd):
            if stage == "code-review":
                data.update(status="incomplete", answer="Required review could not complete.")
        result = self.call_capability("concorde-dev-loop", {**self.task, "specify": False, "run_reviews": False}, callback=incomplete)
        self.assertEqual("failed", result["status"], result)
        self.assertNotEqual("ready", read_change(self.root, required=True)["status"])
        self.assertIsNone(read_change(self.root, required=True)["validated_tree"])

    @verifies("scenario.harness.execute-success")
    def test_reviewer_result_parameters_are_the_self_contained_wire_schema(self):
        from concorde.harness.worker_executor import result_parameters
        result = self.review()
        self.assertEqual("succeeded", result["status"], result)
        launch = self.model.calls[0]["launch"]
        self.assertEqual(result_parameters("concorde-review-stage-result"), launch.result_schema)
        self.assertNotIn("$ref", json.dumps(launch.result_schema))
        wire = DATA_SCHEMAS["concorde-review-stage-result"]["properties"]
        self.assertTrue(wire["representative_tasks"]["uniqueItems"])
        self.assertTrue(launch.result_schema["properties"]["representative_tasks"]["uniqueItems"])
        self.assertNotIn("context_id", wire["gaps"]["items"]["required"])
        self.assertEqual({"read", "grep", "find", "ls", "submit_result", "report_issue", "subagent"}, set(launch.tools))
        self.assertIsNotNone(launch.report_schema)
        self.assertNotIn("report_issue", launch.child_tools)

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
        tasks = read_change(self.root, required=True)["targets"][self.task["target_id"]]["tasks"]
        for capability in ("concorde-tasks", "concorde-implement"):
            result = self.call_capability(capability)
            self.assertEqual("blocked", result["status"], result)
            self.assertEqual("review_required", result["errors"][0]["code"])
            self.assertEqual([], self.model.calls)
            self.assertEqual(tasks, read_change(self.root, required=True)["targets"][self.task["target_id"]]["tasks"])

    @verifies("scenario.planning.assessment-sufficient", "scenario.planning.plan-current")
    def test_a_sufficient_assessment_admits_a_revision_bound_plan_and_no_task_list(self):
        from concorde.development.capability_host import _target_revision
        from concorde.spec.repository import SpecRepository

        self.assertEqual("succeeded", self.call_capability("concorde-dev-loop")["status"])
        documents = {path: path.read_bytes() for path in (self.root / "specs").rglob("*.md")}
        assessed = self.call_capability("concorde-context-solve")
        self.assertEqual("succeeded", assessed["status"], assessed)
        # A sufficient assessment concerns this task only: it authors nothing and admits planning.
        self.assertEqual("completed", assessed["output"]["data"]["outcome"])
        self.assertEqual([], assessed["output"]["data"]["gaps"])
        self.assertEqual(["context-solve"], [call["stage"] for call in self.model.calls])
        self.assertEqual(documents, {path: path.read_bytes() for path in (self.root / "specs").rglob("*.md")})
        planned = self.call_capability("concorde-plan")
        self.assertEqual("succeeded", planned["status"], planned)
        reference = planned["output"]["data"]["artifacts"][0]
        state = read_change(self.root, required=True)["targets"][self.task["target_id"]]
        self.assertEqual((self.root / reference["path"]).read_text(), state["plan"])
        repository = SpecRepository(self.root, PACKAGE)
        self.assertEqual(_target_revision(repository, repository.select(self.task["target_id"])), state["spec_digest"])
        self.assertEqual(([], [], None), (state["tasks"], state["checks"], state["implementation_digest"]))
        self.assertEqual(documents, {path: path.read_bytes() for path in (self.root / "specs").rglob("*.md")})

    @verifies("scenario.planning.plan-empty", "scenario.planning.plan-stale")
    def test_an_empty_or_stale_planner_result_preserves_the_accepted_plan(self):
        self.assertEqual("succeeded", self.call_capability("concorde-dev-loop")["status"])
        self.assertEqual("succeeded", self.call_capability("concorde-plan")["status"])
        accepted = read_change(self.root, required=True)["targets"][self.task["target_id"]]
        stored = (self.root / f"{WORK_PATH}/{self.task['target_id']}/plan.md").read_bytes()

        def empty(stage, snapshot, data, cwd):
            if stage == "plan":
                data["plan"] = ""

        def changed(stage, snapshot, data, cwd):
            if stage == "plan":
                spec = self.root / "specs/transfer/module.md"
                spec.write_text(spec.read_text() + "\nThe daily-limit owner is transfer.\n")

        for label, callback, code in (("empty", empty, "invalid_completion"), ("stale", changed, "stale_context")):
            with self.subTest(plan=label):
                result = self.call_capability("concorde-plan", callback=callback)
                self.assertNotEqual("succeeded", result["status"], result)
                self.assertEqual(code, result["errors"][0]["code"], result)
                current_state = read_change(self.root, required=True)["targets"][self.task["target_id"]]
                self.assertEqual(accepted["plan"], current_state["plan"])
                self.assertEqual(stored, (self.root / f"{WORK_PATH}/{self.task['target_id']}/plan.md").read_bytes())
                self.assertEqual([], current_state["tasks"])

    @verifies("scenario.planning.tasks-missing-plan", "scenario.implementation.missing-tasks")
    def test_task_authoring_and_implementation_refuse_their_missing_prerequisite(self):
        self.assertEqual("succeeded", self.call_capability("concorde-dev-loop")["status"])
        history = read_change(self.root, required=True)["targets"][self.task["target_id"]].get("task_history", [])
        self.assertEqual("succeeded", self.call_capability("concorde-plan")["status"])
        # The accepted plan alone admits no implementation; without it, task authoring never starts.
        for capability, code in (("concorde-implement", "missing_tasks"), ("concorde-tasks", "missing_plan")):
            with self.subTest(capability=capability):
                if capability == "concorde-tasks":
                    state = read_change(self.root, required=True)
                    state["targets"][self.task["target_id"]]["plan"] = ""
                    save_change(self.root, state)
                result = self.call_capability(capability)
                self.assertEqual("blocked", result["status"], result)
                self.assertEqual(code, result["errors"][0]["code"], result)
                self.assertEqual([], self.model.calls)
                current_state = read_change(self.root, required=True)["targets"][self.task["target_id"]]
                self.assertEqual([], current_state["tasks"])
                self.assertEqual(history, current_state.get("task_history", []))

    @verifies("scenario.implementation.incomplete-output")
    def test_an_incomplete_or_omitted_task_result_is_rejected_and_leaves_its_edits_inspectable(self):
        def incomplete(mode):
            def callback(stage, snapshot, data, cwd):
                if stage != "implementation" or not data["tasks"]:
                    return
                data["tasks"] = [] if mode == "omitted" else [{**data["tasks"][0], "complete": False}]
            return callback

        for mode in ("incomplete", "omitted"):
            with self.subTest(result=mode), tempfile.TemporaryDirectory() as directory:
                previous_root, self.root = self.root, Path(directory)
                try:
                    project(self.root)
                    self.assertEqual("succeeded", self.call_capability("concorde-dev-loop")["status"])
                    for capability in ("concorde-plan", "concorde-tasks"):
                        self.assertEqual("succeeded", self.call_capability(capability)["status"])
                    result = self.call_capability("concorde-implement", callback=incomplete(mode))
                    self.assertEqual("incomplete_tasks", result["errors"][0]["code"], result)
                    state = read_change(self.root, required=True)["targets"][self.task["target_id"]]
                    self.assertIsNone(state["implementation_digest"])
                    self.assertEqual([False], [task["complete"] for task in state["tasks"]])
                    # The programmer's authorized edits stay in the candidate for the next attempt.
                    self.assertIn("TRANSFER_IMPLEMENTATION_CODE", (self.root / "app/transfer.py").read_text())
                finally:
                    self.root = previous_root

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
                    gap = read_change(self.root, required=True)["gaps"][0]
                    for capability in ("concorde-tasks", "concorde-implement"):
                        result = self.call_capability(capability)
                        self.assertEqual("blocked", result["status"], result)
                        self.assertEqual([gap], result["output"]["data"]["gaps"])
                        self.assertEqual([], self.model.calls)
                    self.assertEqual("succeeded", self.call_capability("concorde-context-solve")["status"])
                    self.assertEqual("open", read_change(self.root, required=True)["gap_history"][0]["status"])
                    spec = self.root / "specs/transfer/module.md"
                    spec.write_text(spec.read_text() + "\nThe daily-limit owner is transfer.\n")
                    self.assertEqual("succeeded", self.call_capability("concorde-dev-loop")["status"])
                    self.assertEqual("resolved", read_change(self.root, required=True)["gap_history"][0]["status"])
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
        state = read_change(self.root, required=True)
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

    @verifies("scenario.development.dev-loop-spec-gap", "scenario.spec-authoring.invalid-output")
    def test_rejected_authoring_preserves_gaps_until_the_host_accepts_the_repair(self):
        result = self.call_capability("concorde-specify", callback=self.missing("specify"))
        self.assertEqual("blocked", result["status"], result)
        original = (self.root / "specs/transfer/module.md").read_bytes()
        gap = read_change(self.root, required=True)["gap_history"][0]
        def invalid(stage, snapshot, data, cwd):
            data["documents"] = [{"path": "specs/transfer/module.md", "content": "Missing document declaration"}]
        result = self.call_capability("concorde-specify", callback=invalid)
        self.assertNotEqual("succeeded", result["status"], result)
        state = read_change(self.root, required=True)
        self.assertEqual(gap, state["gap_history"][0])
        self.assertEqual([gap["gap"]], state["gaps"])
        self.assertEqual(original, (self.root / "specs/transfer/module.md").read_bytes())
        def repair(stage, snapshot, data, cwd):
            data["documents"] = [{"path": "specs/transfer/module.md", "content": original.decode() + "\nThe daily-limit owner is transfer.\n"}]
        self.assertEqual("succeeded", self.call_capability("concorde-specify", callback=repair)["status"])
        self.assertEqual("resolved", read_change(self.root, required=True)["gap_history"][0]["status"])

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
                    self.assertEqual("open", read_change(self.root, required=True)["gap_history"][0]["status"])
                    self.assertTrue(read_change(self.root, required=True)["gaps"])
                    self.assertEqual("succeeded", self.call_capability("concorde-dev-loop")["status"])
                    self.assertEqual("resolved", read_change(self.root, required=True)["gap_history"][0]["status"])
                finally:
                    self.root = previous_root

    @verifies("scenario.development.dev-loop-spec-gap", "scenario.concorde.develop-failure")
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
        self.assertEqual("open", read_change(self.root, required=True)["gap_history"][0]["status"])
        resumed = self.call_capability("concorde-dev-loop")
        self.assertEqual("succeeded", resumed["status"], resumed)
        self.assertIn("plan", [call["stage"] for call in self.model.calls])
        self.assertEqual("resolved", read_change(self.root, required=True)["gap_history"][0]["status"])

    @verifies("scenario.reflections.capture-gap", "scenario.reflections.repeat-capture-reuses-link",
              "scenario.reflections.list-open-gaps", "scenario.reflections.reject-invalid-gap-selection")
    def test_gap_capture_is_explicit_deduplicated_and_keeps_owner_and_blocker(self):
        unmanaged = {**self.task, "action": "status", "reflection_ids": []}
        self.assertEqual([], self.call_capability("concorde-reflections-triage", unmanaged)["output"]["data"]["gap_records"])
        result = self.call_capability("concorde-plan", callback=self.missing("context-solve"))
        self.assertEqual("blocked", result["status"])
        status = self.call_capability("concorde-reflections-triage", unmanaged)
        self.assertEqual("succeeded", status["status"], status)
        gap = status["output"]["data"]["gap_records"][0]
        blocked = read_change(self.root, required=True)["gap_history"][0]
        # The record carries the existing gap's selection metadata, not a second gap contract.
        self.assertEqual({key: blocked[key] for key in ("id", "target_id", "task", "phase", "gap", "status")}
                         | {"reflection_id": None}, gap)
        self.assertEqual(("service.transfer", self.task["task"], "context-solve", "open"),
                         (gap["target_id"], gap["task"], gap["phase"], gap["status"]))
        self.assertEqual(self.gap(), {key: gap["gap"][key] for key in self.gap()})
        request = {**self.task, "action": "record-gaps", "reflection_ids": [], "gap_ids": [gap["id"]]}
        result = self.call_capability("concorde-reflections-triage", request)
        self.assertEqual("succeeded", result["status"], result)
        reflection = result["output"]["data"]["reflections"][0]
        self.assertEqual("service.transfer", reflection["target_id"])
        self.assertEqual("open", read_change(self.root, required=True)["gap_history"][0]["status"])
        self.assertEqual([], self.model.calls)
        repeated = self.call_capability("concorde-reflections-triage", request)
        self.assertEqual(reflection["id"], repeated["output"]["data"]["reflections"][0]["id"])
        self.assertEqual(1, len(list((self.root / ".concorde/reflections/pending").glob("R-*.md"))))
        rejected = self.call_capability("concorde-reflections-triage", {**request, "target_id": "module.ledger"})
        self.assertEqual("permission_denied", rejected["errors"][0]["code"])
        for implicit in ({**request, "gap_ids": []}, {k: v for k, v in request.items() if k != "gap_ids"}):
            refused = self.call_capability("concorde-reflections-triage", implicit)
            self.assertEqual("invalid_input", refused["errors"][0]["code"], refused)
        state = read_change(self.root, required=True)
        state["gap_history"][0]["status"] = "resolved"
        save_change(self.root, state)
        stale = self.call_capability("concorde-reflections-triage", request)
        self.assertEqual("stale_reference", stale["errors"][0]["code"], stale)
        self.assertEqual(1, len(list((self.root / ".concorde/reflections/pending").glob("R-*.md"))))


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

    @verifies("scenario.development.task-history-identities", "scenario.development.dev-loop-repair",
              "scenario.planning.tasks-id-conflict")
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
        change = read_change(self.root, required=True)
        state = change["targets"]["service.transfer"]
        self.assertEqual([], state.get("task_history", []))
        self.assertTrue(all(t["complete"] for t in state["tasks"]))
        self.assertIsNotNone(change["graph"]["service.transfer"]["repair"])
        self.assertEqual(1, [c["stage"] for c in self.model.calls].count("implementation"))

    @verifies("scenario.development.dev-loop-repair", "scenario.implementation.admitted-work")
    def test_blocking_then_clean_repairs_once_and_reaches_ready(self):
        counter = [0]
        reviews = {"count": 0}
        checked_rounds = []
        def callback(stage, snapshot, data, cwd):
            if stage == "code-review":
                candidate = read_change(self.root, required=True)
                target = candidate["targets"]["service.transfer"]
                self.assertTrue(target["checks"])
                self.assertTrue(all(check["status"] == "passed" for check in target["checks"]))
                self.assertTrue(all(task["complete"] for task in target["tasks"]))
                checked_rounds.append([task["id"] for task in target["tasks"]])
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
        feedback = next(item for item in second_inputs if item["type_id"] == "concorde-review-result")
        self.assertEqual("code", feedback["data"]["review_mode"])
        self.assertEqual("findings", feedback["data"]["status"])
        self.assertEqual([self.finding()], feedback["data"]["findings"])
        self.assertEqual(feedback, next(item for item in implement_calls[1]["snapshot"]["stage_inputs"]
                                      if item["type_id"] == "concorde-review-result"))
        self.assertEqual([["task.transfer"], ["task.transfer.repair.2"]], checked_rounds)
        self.assertEqual(["tasks", "implementation", "code-review"] * 2,
                         [stage for stage in stages if stage in {"tasks", "implementation", "code-review"}])
        state = read_change(self.root, required=True)
        self.assertEqual(1, state["graph"]["service.transfer"]["repair_iteration"])
        self.assertEqual(2, state["graph"]["service.transfer"]["policy"]["max_repair_iterations"])
        transitions = state["graph"]["service.transfer"]["transitions"]
        repairs = [t for t in transitions if t["trigger"] == "ai-review" and t["to"] == "tasks"]
        self.assertEqual(1, len(repairs))
        self.assertEqual("model-driven", repairs[0]["source"])
        self.assertEqual(["daily-limit-check"], repairs[0]["finding_ids"])
        self.assertIsNotNone(repairs[0]["artifact"])
        self.assertEqual(1, len(state["targets"]["service.transfer"]["task_history"]))

    def _assert_stopped_repair_progress(self, state, rounds):
        target = state["targets"]["service.transfer"]
        self.assertTrue(target["plan"])
        self.assertTrue(all(task["complete"] for task in target["tasks"]))
        self.assertEqual(rounds, len(target["task_history"]))
        self.assertEqual(rounds + 1, [call["stage"] for call in self.model.calls].count("tasks"))
        final = state["graph"]["service.transfer"]["transitions"][-1]
        self.assertEqual(("review_code", "END", "code-driven", "conflicting", state["status"]),
                         (final["from"], final["to"], final["source"], final["outcome"], final["status"]))
        self.assertEqual(self.last_review_progress["plan"], target["plan"])
        self.assertEqual(self.last_review_progress["tasks"], target["tasks"])
        self.assertEqual(self.last_review_progress["task_history"], target["task_history"])
        self.assertEqual(self.last_review_bytes, (self.root / "app/transfer.py").read_bytes())

    def _capture_review_progress(self):
        self.last_review_progress = read_change(self.root, required=True)["targets"]["service.transfer"]
        self.last_review_bytes = (self.root / "app/transfer.py").read_bytes()

    def _reach_unchanged_feedback_waiting(self):
        counter = [0]
        def callback(stage, snapshot, data, cwd):
            if stage == "code-review":
                self._capture_review_progress()
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
        state = read_change(self.root, required=True)
        self.assertEqual("waiting", state["status"])
        self._assert_stopped_repair_progress(state, rounds=1)
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
                self._capture_review_progress()
                data.update(status="findings", gaps=[], findings=[self.finding(
                    problem=f"Distinct defect variant {review_counter[0]}.",
                    finding_id=f"defect-{review_counter[0]}")])
            if stage == "tasks":
                counter[0] += 1
                self.repair_tasks(counter, snapshot, data)
        result = self.call_capability("concorde-dev-loop", callback=callback)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("conflicting", result["output"]["data"]["outcome"])
        state = read_change(self.root, required=True)
        self.assertEqual("limit_exhausted", state["status"])
        self._assert_stopped_repair_progress(state, rounds=2)
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
        self.assertEqual("waiting", read_change(self.root, required=True)["status"])
        self.assertNotIn("plan", [c["stage"] for c in self.model.calls])

    def test_admitted_specify_spec_change_does_not_spuriously_reset_the_graph_record(self):
        def callback(stage, snapshot, data, cwd):
            if stage == "specify" and snapshot["target_id"] == "service.transfer":
                document = next(d for d in snapshot["spec_resolution"]["sources"] if d["path"] == "specs/transfer/module.md")
                data["documents"] = [{"path": "specs/transfer/module.md",
                    "content": (cwd / document["path"]).read_text() + "\nThe transfer capability documents an additional promise.\n"}]
        result = self.call_capability("concorde-dev-loop", callback=callback)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        self.assertIn("The transfer capability documents an additional promise.",
                      (self.root / "specs/transfer/module.md").read_text())
        self.assertEqual([], read_change(self.root, required=True)["graph"]["service.transfer"]["transitions"])
        # A second dev-loop resumes without re-authoring; the first run's own admitted Spec change
        # must not be mistaken for an out-of-band human edit and spuriously reset the record.
        second = self.call_capability("concorde-dev-loop")
        self.assertEqual("succeeded", second["status"], second)
        self.assertNotIn("specify", [c["stage"] for c in self.model.calls])
        record = read_change(self.root, required=True)["graph"]["service.transfer"]
        self.assertEqual([], [t for t in record["transitions"] if t["trigger"] == "human"])
        # A genuinely human Spec edit between runs still resets the record.
        spec = self.root / "specs/transfer/module.md"
        spec.write_text(spec.read_text() + "\nA human directly edited this Spec.\n")
        third = self.call_capability("concorde-dev-loop")
        self.assertEqual("succeeded", third["status"], third)
        record = read_change(self.root, required=True)["graph"]["service.transfer"]
        human_transitions = [t for t in record["transitions"] if t["trigger"] == "human"]
        self.assertEqual(1, len(human_transitions))
        self.assertEqual("spec_changed", human_transitions[0]["outcome"])

    @verifies("scenario.development.dev-loop-repair-exhausted")
    def test_human_implementation_edit_resets_the_repair_record(self):
        self._reach_unchanged_feedback_waiting()
        before = read_change(self.root, required=True)
        self.assertEqual(1, before["graph"]["service.transfer"]["repair_iteration"])
        code = self.root / "app/transfer.py"
        code.write_text(code.read_text() + "\n# a human edited this directly\n")
        review_count = [0]
        def callback(stage, snapshot, data, cwd):
            if stage == "code-review":
                review_count[0] += 1
                candidate = read_change(self.root, required=True)
                if review_count[0] == 1:
                    # The same feedback must be eligible again only after admission resets
                    # the old count and fingerprint for the intervening implementation edit.
                    self.assertEqual(0, candidate["graph"]["service.transfer"]["repair_iteration"])
                    self.assertEqual(before["targets"]["service.transfer"]["task_history"],
                                     candidate["targets"]["service.transfer"]["task_history"])
                    data.update(status="findings", findings=[self.finding()], gaps=[])
            if stage == "tasks":
                self.repair_tasks([3], snapshot, data)
        result = self.call_capability("concorde-dev-loop", callback=callback)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        stages = [call["stage"] for call in self.model.calls]
        self.assertNotIn("plan", stages)
        self.assertEqual(1, stages.count("tasks"))
        self.assertEqual(2, stages.count("code-review"))
        state = read_change(self.root, required=True)
        record = state["graph"]["service.transfer"]
        self.assertEqual(1, record["repair_iteration"])
        self.assertEqual(2, len(state["targets"]["service.transfer"]["task_history"]))
        human_transitions = [t for t in record["transitions"] if t["trigger"] == "human"]
        self.assertEqual(1, len(human_transitions))
        self.assertEqual("implementation_changed", human_transitions[0]["outcome"])

    def test_capability_execution_error_during_standalone_code_review_maps_to_execution_limit(self):
        from concorde.harness.worker_executor import CapabilityExecutionError
        from concorde.harness.change_worktree import ensure_change
        ensure_change(self.root, task=self.task, allow_primary=True)
        double = self.double()
        def fail(invocation, **options):
            raise CapabilityExecutionError("the worker ran past its 10s timeout", outcome="limit_exhausted")
        double.executor = fail
        result = self.call_capability("concorde-review", {**self.task, "review_mode": "code"}, double=double)
        self.assertEqual("failed", result["status"], result)
        reviewed = result["output"]["data"]["reviews"][0]["data"]
        self.assertEqual("incomplete", reviewed["status"])
        reference = result["output"]["data"]["artifacts"][0]
        private = json.loads((self.root / reference["path"]).with_suffix(".execution.json").read_text())
        self.assertEqual("execution_limit", private["failure"]["code"])
        self.assertIsNone(private["usage"])
        self.assertEqual("limit_exhausted", read_change(self.root, required=True)["status"])
