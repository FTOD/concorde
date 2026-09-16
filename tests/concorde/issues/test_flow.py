"""End-to-end Issue operations with real host gates and a deterministic model-process double."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

from concorde.development.capability_service import CapabilityHost, run_capability
from concorde.harness.change_worktree import ensure_change, read_change, record_task_gaps, workspace_context
from concorde.issues.flow import copy_selection
from concorde.issues.store import read_issue, report_issue
from concorde.spec.repository import SpecError
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.issues.test_store import report, source
from tests.concorde.spec.support import PACKAGE, CONFIGURATION, ModelProcessDouble, project


class IssueFlowTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        project(self.root)
        self.ref = report_issue(self.root, report(type="bug", subtype=None,
            title="Transfer leaves balance unchanged", description="Transfer must subtract a valid amount.",
            owner_target_id="service.transfer", evidence=[]), source(target_id="service.transfer"))

    def call(self, action, callback=None, **extra):
        self.model = ModelProcessDouble(callback)
        host = CapabilityHost(self.root, PACKAGE, executor=self.model.executor, allow_primary_worktree=True)
        payload = {"action": action, **({"issue_id": self.ref["issue_id"]} if action != "list" else {}), **extra}
        return run_capability("concorde-issues", CONFIGURATION, typed("concorde-issues-request", payload), host_context=host)

    @verifies("scenario.issues.inspect", "scenario.concorde.issues")
    def test_inspection_does_not_create_a_candidate_or_launch_a_worker(self):
        before = read_issue(self.root, self.ref["issue_id"])
        for action in ("list", "show"):
            result = self.call(action)
            self.assertEqual("succeeded", result["status"], result)
            self.assertEqual([before[0]], result["output"]["data"]["issues"])
            self.assertEqual([], self.model.calls)
            self.assertFalse((self.root / ".concorde/worktree.json").exists())
        self.assertEqual(before, read_issue(self.root, self.ref["issue_id"]))

    @verifies("scenario.issues.solve-ready")
    def test_solve_uses_development_and_verifies_disposition_before_ready(self):
        result = self.call("solve")
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        self.assertEqual("resolved", result["output"]["data"]["decision"])
        record, revision = read_issue(self.root, self.ref["issue_id"])
        self.assertEqual("closed", record["status"])
        change = read_change(self.root, required=True)
        self.assertEqual("ready", change["status"])
        self.assertEqual(revision, change["issue_solutions"][record["id"]]["closed_revision"])
        stages = [call["stage"] for call in self.model.calls]
        self.assertIn("implementation", stages)
        self.assertGreaterEqual(stages.count("code-review"), 2)
        self.assertFalse((self.root / ".concorde/deliveries").exists())
        repeated = self.call("solve")
        self.assertEqual("succeeded", repeated["status"], repeated)
        self.assertEqual([], self.model.calls)

    @verifies("scenario.issues.solve-spec-repair")
    def test_every_solver_action_has_an_explicit_declared_route(self):
        from concorde.issues.flow import DECISION_ROUTES, NODES
        from concorde.spec.typed_data import DATA_SCHEMAS
        actions = DATA_SCHEMAS['concorde-agent-stage-result']['properties']['issue_decision']['properties']['action']['enum']
        self.assertEqual(set(actions), set(DECISION_ROUTES))
        self.assertLessEqual(set(DECISION_ROUTES.values()), set(NODES))
        self.assertEqual('repair_spec', DECISION_ROUTES['spec-repair'])

    @verifies("scenario.issues.solve-spec-repair")
    def test_spec_repair_enters_the_author_then_continues_development(self):
        def choose(stage, snapshot, data, cwd):
            if stage == 'issue-solve' and sum(c['stage'] == stage for c in self.model.calls) == 1:
                data['issue_decision']['action'] = 'spec-repair'
        result = self.call('solve', choose)
        self.assertEqual('succeeded', result['status'], result)
        self.assertEqual('ready', result['output']['data']['outcome'])
        stages = [call['stage'] for call in self.model.calls]
        self.assertEqual(['issue-solve', 'specify', 'issue-solve'], stages[:3])
        self.assertIn('implementation', stages)
        author = self.model.calls[1]['snapshot']
        self.assertIn('concorde-issue-intent', [value['type_id'] for value in author['stage_inputs']])
        self.assertNotIn('concorde-issue-selection', [value['type_id'] for value in author['stage_inputs']])
        self.assertEqual('closed', read_issue(self.root, self.ref['issue_id'])[0]['status'])

    @verifies("scenario.issues.solve-spec-repair")
    def test_code_free_spec_repair_can_continue_directly_to_verification(self):
        self.healthy_implementation()
        self.ref = report_issue(self.root, report(owner_target_id='scope.audit', evidence=[]),
                                source(target_id='scope.audit', invocation_id='spec-only-repair'))
        def choose(stage, snapshot, data, cwd):
            if stage == 'issue-solve':
                count = sum(call['stage'] == stage for call in self.model.calls)
                if count <= 2:
                    data['issue_decision']['action'] = 'spec-repair' if count == 1 else 'verify'
        result = self.call('solve', choose)
        self.assertEqual('succeeded', result['status'], result)
        self.assertEqual('ready', result['output']['data']['outcome'])
        stages = [call['stage'] for call in self.model.calls]
        self.assertEqual(['issue-solve', 'specify', 'issue-solve'], stages[:3])
        self.assertIn('spec-review', stages)
        self.assertNotIn('code-review', stages)
        self.assertNotIn('implementation', stages)

    @verifies("scenario.issues.solve-decision")
    def test_unsettled_design_stays_open_without_a_human_approval_gate_for_every_issue(self):
        def decision(stage, snapshot, data, cwd):
            if stage == "issue-solve":
                data["issue_decision"].update(action="needs-decision", rationale="Should transfers allow overdrafts?")
        result = self.call("solve", decision)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("needs-decision", result["output"]["data"]["decision"])
        self.assertEqual("open", read_issue(self.root, self.ref["issue_id"])[0]["status"])
        self.assertEqual(["issue-solve"], [call["stage"] for call in self.model.calls])

    @verifies("scenario.issues.solve-stale")
    def test_stale_selection_is_rejected_before_any_worker_runs(self):
        result = self.call("solve", expected_revision="sha256:" + "f" * 64)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("stale_issue", result["errors"][0]["code"])
        self.assertEqual([], self.model.calls)
        self.assertFalse((self.root / ".concorde/worktree.json").exists())

    @verifies("scenario.issues.solve-stale")
    def test_failed_final_validation_restores_only_the_own_disposition(self):
        def reject_disposition(stage, snapshot, data, cwd):
            if stage == "issue-solve":
                data["issue_decision"].update(action="not-actionable", rationale="Controlled disposition fixture.")
        # The initial fixture's transfer check fails. It must not produce a ready disposed candidate.
        before = read_issue(self.root, self.ref["issue_id"])
        result = self.call("solve", reject_disposition)
        self.assertEqual("failed", result["status"], result)
        self.assertEqual(before, read_issue(self.root, self.ref["issue_id"]))
        self.assertNotEqual("ready", read_change(self.root, required=True)["status"])

    @verifies("scenario.issues.solve-handoff")
    def test_selection_copy_preserves_uncommitted_bytes_and_no_unrelated_file(self):
        destination = self.root / "candidate"
        destination.mkdir()
        before, revision = read_issue(self.root, self.ref["issue_id"])
        (self.root / "unrelated.txt").write_text("private local edit")
        copy_selection(self.root, destination, {"issue_id": self.ref["issue_id"], "expected_revision": revision})
        self.assertEqual((before, revision), read_issue(destination, self.ref["issue_id"]))
        self.assertFalse((destination / "unrelated.txt").exists())
        with self.assertRaises(SpecError):
            copy_selection(self.root, destination, {"issue_id": self.ref["issue_id"], "expected_revision": "sha256:" + "f" * 64})

    @verifies("scenario.issues.blocker-history")
    def test_issue_identity_outlives_task_wording_and_released_dependencies(self):
        ensure_change(self.root, allow_primary=True)
        blocker = {**self.ref, "blocked_step": "Implement transfer"}
        record_task_gaps(self.root, "service.transfer", "Old task text", "plan", [blocker], "old", scope_id="module:service.transfer")
        original = read_change(self.root, required=True)["issue_blockers"][0]
        record_task_gaps(self.root, "service.transfer", "Replanned text", "plan", [blocker], "old", scope_id="module:service.transfer")
        self.assertEqual(original["id"], read_change(self.root, required=True)["issue_blockers"][0]["id"])
        self.assertEqual([], workspace_context(self.root, target_id="module.ledger")["blockers"])
        record_task_gaps(self.root, "service.transfer", "Replanned text", "plan", [], "new", scope_id="module:service.transfer")
        self.assertEqual("resolved", read_change(self.root, required=True)["issue_blockers"][0]["status"])
        self.assertEqual("open", read_issue(self.root, self.ref["issue_id"])[0]["status"])

    @verifies("scenario.issues.reference")
    def test_fabricated_blocker_reference_is_refused(self):
        def forged(stage, snapshot, data, cwd):
            if stage == "issue-solve":
                data.update(outcome="spec_incomplete", blockers=[{**self.ref, "blocked_step": "Unadmitted reference"}])
        result = self.call("solve", forged)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("permission_denied", result["errors"][0]["code"])
        self.assertEqual("open", read_issue(self.root, self.ref["issue_id"])[0]["status"])

    def healthy_implementation(self):
        (self.root / 'app/transfer.py').write_text('def transfer(balance, amount):\n'
            '    if amount <= 0 or amount > balance: raise ValueError("invalid")\n'
            '    return balance - amount\n')

    @verifies("scenario.issues.solve-ready")
    def test_duplicate_is_disposed_without_human_gate_and_keeps_the_canonical_issue(self):
        self.healthy_implementation()
        original, _ = read_issue(self.root, self.ref['issue_id'])
        duplicate = report_issue(self.root, original['reports'][0]['report'],
                                 source(target_id='service.transfer', invocation_id='duplicate-fixture'))
        def choose(stage, snapshot, data, cwd):
            if stage == 'issue-solve':
                self.assertIn(duplicate['issue_id'], [row['issue_id'] for row in snapshot['stage_inputs'][0]['data']['duplicates']])
                data['issue_decision'].update(action='duplicate', duplicate_of=duplicate['issue_id'],
                                              rationale='Both selected reports describe the same transfer observation.')
        result = self.call('solve', choose)
        self.assertEqual('succeeded', result['status'], result)
        record, _ = read_issue(self.root, self.ref['issue_id'])
        self.assertEqual('duplicate', record['dispositions'][-1]['reason'])
        self.assertEqual('open', read_issue(self.root, duplicate['issue_id'])[0]['status'])
        self.assertEqual(['issue-solve'], [item['stage'] for item in self.model.calls])

    @verifies("scenario.issues.solve-ready")
    def test_contract_grounded_non_actionable_disposition_needs_no_manual_approval(self):
        self.healthy_implementation()
        self.ref = report_issue(self.root, report(owner_target_id='service.transfer', evidence=[],
            description='The transfer contract is alleged to be absent.'),
            source(target_id='service.transfer', invocation_id='contract-report'))
        def choose(stage, snapshot, data, cwd):
            if stage == 'issue-solve':
                data['issue_decision'].update(action='not-actionable', rationale='The admitted transfer Spec supplies that contract.')
        result = self.call('solve', choose)
        self.assertEqual('succeeded', result['status'], result)
        self.assertEqual('not-actionable', result['output']['data']['decision'])
        self.assertEqual(['issue-solve'], [item['stage'] for item in self.model.calls])

    @verifies("scenario.issues.solve-decision")
    def test_explicit_clarification_resumes_a_waiting_solve(self):
        def wait(stage, snapshot, data, cwd):
            if stage == 'issue-solve':
                data['issue_decision'].update(action='needs-decision', rationale='Which transfer behavior is intended?')
        self.assertEqual('blocked', self.call('solve', wait)['status'])
        def observe(stage, snapshot, data, cwd):
            if stage == 'issue-solve':
                self.assertIn('Use the existing pure-transfer contract.', snapshot['stage_inputs'][0]['data']['feedback'])
        result = self.call('solve', observe, note='Use the existing pure-transfer contract.')
        self.assertEqual('succeeded', result['status'], result)
        self.assertEqual('ready', result['output']['data']['outcome'])

    @verifies("scenario.issues.inspect")
    def test_solving_an_already_closed_issue_does_not_prepare_a_worktree(self):
        from concorde.issues.store import dispose_issue
        _, revision = read_issue(self.root, self.ref['issue_id'])
        dispose_issue(self.root, self.ref['issue_id'], revision, reason='not-actionable',
                      note='Fixture disposition', evidence=['fixture'], actor='test')
        host = CapabilityHost(self.root, PACKAGE)  # no primary-write or candidate-creation override
        result = run_capability('concorde-issues', CONFIGURATION, typed('concorde-issues-request',
            {'action': 'solve', 'issue_id': self.ref['issue_id']}), host_context=host)
        self.assertEqual('succeeded', result['status'], result)
        self.assertFalse((self.root / '.concorde/worktree.json').exists())

    @verifies("scenario.issues.report-authority")
    def test_explicit_developer_report_can_cite_archived_evidence(self):
        archived = self.root / '.concorde/archive/reflections/pending/R-001.md'
        archived.parent.mkdir(parents=True)
        archived.write_text('Historical observation, not an active Issue.\n')
        payload = {'action': 'report', 'target_id': 'service.transfer', 'report': report(
            owner_target_id='service.transfer', evidence=[{'path': archived.relative_to(self.root).as_posix(),
            'description': 'Explicitly selected historical evidence'}])}
        result = run_capability('concorde-issues', CONFIGURATION, typed('concorde-issues-request', payload),
                               host_context=CapabilityHost(self.root, PACKAGE))
        self.assertEqual('succeeded', result['status'], result)
        self.assertFalse((self.root / '.concorde/worktree.json').exists())
