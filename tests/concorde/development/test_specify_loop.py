"""Spec completion can stand alone and feed the development loop in the same change."""
import json
import unittest
from unittest.mock import patch

from concorde.harness.change_worktree import read_change, save_change
from concorde.spec.typed_data import artifact, canonical
from concorde.spec.verification import verifies
from tests.concorde.development import test_review as fixtures


class SpecifyLoopTests(unittest.TestCase):
    setUp = fixtures.ReviewTests.setUp
    double = fixtures.ReviewTests.double
    call_capability = fixtures.ReviewTests.call_capability
    missing = fixtures.ReviewTests.missing
    gap = staticmethod(fixtures.ReviewTests.gap)

    def add_spec_consumer(self):
        path = self.root / '.concorde/specs.json'
        registry = json.loads(path.read_text())
        bank = next(t for t in registry['targets'] if t['id'] == 'scope.bank')
        bank['references'].append({'kind': 'module', 'id': 'service.transfer'})
        path.write_text(json.dumps(registry))

    def spec_review_targets(self):
        return [c['snapshot']['target_id'] for c in self.model.calls if c['stage'] == 'spec-review']

    @staticmethod
    def consumer_finding(severity):
        return {'id': 'consumer-note', 'severity': severity, 'target_id': 'scope.bank',
                'document': 'specs/bank/module.md', 'contract': 'The bank contract',
                'location': {'path': 'specs/bank/module.md', 'line': 1},
                'problem': 'Controlled consumer review finding.', 'affected_task': 'Review bank reliance'}

    @verifies('scenario.development.specify-loop')
    def test_unchanged_spec_scope_reuses_owner_and_consumers_but_explicit_review_is_fresh(self):
        self.add_spec_consumer()
        task = {**self.task, 'specify': False, 'run_reviews': True}
        def advisory(stage, snapshot, data, cwd):
            if stage == 'spec-review' and snapshot['target_id'] == 'scope.bank':
                data.update(status='findings', findings=[self.consumer_finding('advisory')])
        first = self.call_capability('concorde-specify-loop', task, callback=advisory)
        self.assertEqual('succeeded', first['status'], first)
        self.assertCountEqual(['service.transfer', 'scope.bank'], self.spec_review_targets())
        second = self.call_capability('concorde-specify-loop', task)
        self.assertEqual('succeeded', second['status'], second)
        self.assertEqual([], self.spec_review_targets())
        self.assertEqual(first['output']['data']['artifacts'], second['output']['data']['artifacts'])
        fresh = self.call_capability('concorde-review', {**self.task, 'review_mode': 'spec'})
        self.assertEqual('succeeded', fresh['status'], fresh)
        self.assertCountEqual(['service.transfer', 'scope.bank'], self.spec_review_targets())

    @verifies('scenario.development.specify-loop')
    def test_candidate_consumer_reviews_are_reused_by_the_review_stage(self):
        self.add_spec_consumer()
        task = {**self.task, 'specify': True, 'run_reviews': True}
        original = (self.root / 'specs/transfer/module.md').read_text()

        def author(stage, snapshot, data, cwd):
            if stage == 'specify':
                data['documents'] = [{'path': 'specs/transfer/module.md',
                                      'content': original + '\nTransfer rounds every amount to cents.\n'}]
        first = self.call_capability('concorde-specify-loop', task, callback=author)
        self.assertEqual('succeeded', first['status'], first)
        # The consumer was reviewed once against the candidate bytes before they were applied; the
        # review stage then reviewed only the owner and reused that consumer evidence.
        self.assertEqual(['scope.bank', 'service.transfer'], self.spec_review_targets())
        state = read_change(self.root)
        record = state['shared_spec_reviews']['service.transfer']['scope.bank']
        self.assertEqual("Review this Module's reliance on the changed canonical Spec. " + self.task['task'],
                         record['task'])
        artifacts = {ref['id']: ref for ref in first['output']['data']['artifacts']}
        self.assertEqual(record['artifact'], artifacts['review.scope.bank.spec'])
        self.assertEqual({'service.transfer', 'scope.bank'},
                         {value['data']['target_id'] for value in
                          [json.loads((self.root / ref['path']).read_text()) for ref in artifacts.values()
                           if ref['id'].startswith('review.')]})
        second = self.call_capability('concorde-specify-loop', task, callback=author)
        self.assertEqual('succeeded', second['status'], second)
        self.assertEqual([], self.spec_review_targets())
        # An explicit standalone review never reuses flow evidence.
        fresh = self.call_capability('concorde-review', {**self.task, 'review_mode': 'spec'})
        self.assertEqual('succeeded', fresh['status'], fresh)
        self.assertCountEqual(['service.transfer', 'scope.bank'], self.spec_review_targets())

    @verifies('scenario.development.specify-loop', 'scenario.development.dev-loop-ready')
    def test_current_spec_scope_continues_into_development_before_code_review_exists(self):
        self.add_spec_consumer()
        task = {**self.task, 'specify': False, 'run_reviews': True}
        first = self.call_capability('concorde-specify-loop', task)
        self.assertEqual('succeeded', first['status'], first)
        self.assertNotIn('code', read_change(self.root)['reviews']['service.transfer'])
        result = self.call_capability('concorde-dev-loop', task)
        self.assertEqual('succeeded', result['status'], result)
        self.assertEqual('ready', result['output']['data']['outcome'])
        self.assertEqual([], self.spec_review_targets())
        self.assertIn('implementation', [c['stage'] for c in self.model.calls])
        self.assertIn('code-review', [c['stage'] for c in self.model.calls])

    @verifies('scenario.development.specify-loop')
    def test_changed_consumer_contract_requires_a_fresh_scope_review(self):
        self.add_spec_consumer()
        task = {**self.task, 'specify': False, 'run_reviews': True}
        self.assertEqual('succeeded', self.call_capability('concorde-specify-loop', task)['status'])
        path = self.root / 'specs/bank/module.md'
        path.write_text(path.read_text() + '\nConsumer clarification.\n')
        result = self.call_capability('concorde-specify-loop', task)
        self.assertEqual('succeeded', result['status'], result)
        self.assertIn('scope.bank', self.spec_review_targets())

    @verifies('scenario.development.specify-loop')
    def test_missing_corrupt_or_incomplete_consumer_evidence_cannot_be_reused(self):
        for defect in ('missing_record', 'missing_file', 'corrupt', 'incomplete', 'skipped',
                       'empty_coverage', 'blocking', 'gaps', 'old_task', 'old_constraints'):
            with self.subTest(defect=defect):
                fixture = SpecifyLoopTests()
                fixture.setUp()
                try:
                    fixture.add_spec_consumer()
                    task = {**fixture.task, 'specify': False, 'run_reviews': True}
                    first = fixture.call_capability('concorde-specify-loop', task)
                    self.assertEqual('succeeded', first['status'], first)
                    state = read_change(fixture.root)
                    records = state['shared_spec_reviews']['service.transfer']
                    record = records['scope.bank']
                    reference = record['artifact']
                    path = fixture.root / reference['path']
                    if defect == 'missing_record':
                        records.pop('scope.bank')
                    elif defect == 'missing_file':
                        path.unlink()
                    elif defect == 'corrupt':
                        path.write_text(path.read_text() + '\n')
                    elif defect == 'old_task':
                        record['task'] = 'A different consumer task'
                    elif defect == 'old_constraints':
                        record['constraints'] = ['A different constraint']
                    else:
                        value = json.loads(path.read_text())
                        if defect == 'empty_coverage':
                            value['data']['representative_tasks'] = []
                        elif defect == 'blocking':
                            value['data'].update(status='findings',
                                                 findings=[self.consumer_finding('blocking')])
                        elif defect == 'gaps':
                            value['data'].update(status='findings', gaps=[{
                                'question': 'Which consumer promise applies?',
                                'blocked_step': 'Review bank reliance', 'needed_contract': 'Bank promise',
                                'target_id': 'scope.bank', 'context_id': value['data']['context_id']}])
                        else:
                            value['data']['status'] = defect
                        path.write_text(canonical(value) + '\n')
                        record['artifact'] = artifact(fixture.root, reference['id'], reference['path'])
                    save_change(fixture.root, state)  # Corrupt only isolated fixture evidence.
                    result = fixture.call_capability('concorde-specify-loop', task)
                    self.assertEqual('succeeded', result['status'], result)
                    self.assertIn('scope.bank', fixture.spec_review_targets())
                finally:
                    fixture.doCleanups()

    @verifies('scenario.development.specify-loop')
    def test_failed_consumer_review_is_retried_and_only_success_can_be_reused(self):
        from concorde.harness.worker_executor import CapabilityExecutionError
        self.add_spec_consumer()
        task = {**self.task, 'specify': False, 'run_reviews': True}
        # Use the fixture callback to fail after the owner has produced its review.
        def fail(stage, snapshot, data, cwd):
            if stage == 'spec-review' and snapshot['target_id'] == 'scope.bank':
                raise CapabilityExecutionError('controlled failed consumer')
        first = self.call_capability('concorde-specify-loop', task, callback=fail)
        self.assertNotEqual('succeeded', first['status'], first)
        retry = self.call_capability('concorde-specify-loop', task)
        self.assertEqual('succeeded', retry['status'], retry)
        self.assertIn('scope.bank', self.spec_review_targets())
        repeat = self.call_capability('concorde-specify-loop', task)
        self.assertEqual('succeeded', repeat['status'], repeat)
        self.assertEqual([], self.spec_review_targets())

    @verifies('scenario.development.specify-loop')
    def test_current_component_consumer_overlap_is_valid_for_reuse_and_readiness(self):
        from concorde.development.capability_host import Invocation
        from concorde.development.review import current_spec_scope, verify_required
        from concorde.spec.repository import SpecError
        path = self.root / '.concorde/specs.json'
        registry = json.loads(path.read_text())
        transfer = next(t for t in registry['targets'] if t['id'] == 'service.transfer')
        transfer['references'].append({'kind': 'module', 'id': 'scope.bank'})
        path.write_text(json.dumps(registry))
        task = {'target_id': 'scope.bank', 'task': 'Implement the transfer promise',
                'specify': False, 'run_reviews': True}
        developed = self.call_capability('concorde-dev-loop', task)
        self.assertEqual('succeeded', developed['status'], developed)
        fresh = self.call_capability('concorde-review', {
            'target_id': task['target_id'], 'task': task['task'], 'review_mode': 'spec'})
        self.assertEqual('succeeded', fresh['status'], fresh)
        state = read_change(self.root)
        peer = state['shared_spec_reviews']['scope.bank']['service.transfer']
        component = state['targets']['scope.bank']['coordination']['service.transfer']
        self.assertEqual(component['task'], peer['task'])
        run = Invocation('concorde-review', fixtures.CONFIGURATION,
                         {'target_id': 'scope.bank', 'task': task['task'],
                          'change_id': state['change_id']}, self.host)
        verify_required(run)
        self.assertIsNotNone(current_spec_scope(run))
        repeated = self.call_capability('concorde-specify-loop', task)
        self.assertEqual('succeeded', repeated['status'], repeated)
        self.assertEqual([], self.spec_review_targets())
        # Simulate a newly admitted component intent in this isolated fixture. The old
        # receipt must not authorize it merely because that receipt's bytes are intact.
        state = read_change(self.root)
        state['targets']['scope.bank']['coordination']['service.transfer']['task'] += ' Revised local work.'
        save_change(self.root, state)
        self.assertIsNone(current_spec_scope(run))
        with self.assertRaises(SpecError):
            verify_required(run)

    @verifies('scenario.development.specify-loop')
    def test_same_task_author_gap_blocks_cached_review_until_admitted_author_repairs_it(self):
        task = {**self.task, 'specify': False, 'run_reviews': True}
        first = self.call_capability('concorde-specify-loop', task)
        self.assertEqual('succeeded', first['status'], first)
        paths = ['specs/transfer/module.md', 'specs/transfer/promises.md']
        before = {p: (self.root / p).read_bytes() for p in paths}
        author = self.call_capability('concorde-specify', self.task, callback=self.missing('specify'))
        self.assertEqual('spec_incomplete', author['output']['data']['outcome'])
        history = read_change(self.root)['gap_history']
        self.assertEqual(before, {p: (self.root / p).read_bytes() for p in paths})
        result = self.call_capability('concorde-specify-loop', task)
        self.assertEqual('blocked', result['status'], result)
        self.assertEqual('spec_incomplete', result['output']['data']['outcome'])
        self.assertEqual([], self.model.calls)
        self.assertEqual(history, read_change(self.root)['gap_history'])
        def repair(stage, snapshot, data, cwd):
            if stage == 'specify':
                # The author reads the granted document from its capsule; no body is inline.
                data['documents'] = [{'path': paths[0], 'content': (cwd / paths[0]).read_text()
                    + '\nTransfer owns the requested daily-limit admission rule.\n'}]
        admitted = self.call_capability('concorde-specify', self.task, callback=repair)
        self.assertEqual('completed', admitted['output']['data']['outcome'], admitted)
        self.assertTrue(all(g['status'] == 'resolved' for g in read_change(self.root)['gap_history']))
        resumed = self.call_capability('concorde-specify-loop', task)
        self.assertEqual('succeeded', resumed['status'], resumed)

    @verifies('scenario.development.specify-loop')
    def test_consumer_prerequisite_gap_is_task_attributed_for_reuse_and_readiness(self):
        from dataclasses import replace
        from concorde.development.capability_host import Invocation, run_capability
        from concorde.development.review import current_spec_scope, verify_required
        from concorde.spec.repository import SpecError
        from concorde.spec.typed_data import typed
        for related in (False, True):
            with self.subTest(related=related):
                fixture = SpecifyLoopTests()
                fixture.setUp()
                try:
                    fixture.add_spec_consumer()
                    task = {**fixture.task, 'specify': False, 'run_reviews': True}
                    first = fixture.call_capability('concorde-specify-loop', task)
                    self.assertEqual('succeeded', first['status'], first)
                    state = read_change(fixture.root)
                    peer = state['shared_spec_reviews']['service.transfer']['scope.bank']
                    double = fixture.double(fixture.missing('specify'))
                    author_task = {'target_id': 'scope.bank', 'task': peer['task']
                        + ('' if related else ' An unrelated task.'),
                        'constraints': peer['constraints'], 'change_id': state['change_id']}
                    author = run_capability('concorde-specify', fixture.configuration,
                        typed('concorde-specify-request', author_task), host_context=replace(
                            fixture.host, routed_target='scope.bank', coordinated=True, executor=double.executor))
                    self.assertEqual('spec_incomplete', author['output']['data']['outcome'], author)
                    history = read_change(fixture.root)['gap_history']
                    run = Invocation('concorde-review', fixture.configuration, {
                        **fixture.task, 'change_id': state['change_id']}, fixture.host)
                    if related:
                        self.assertIsNone(current_spec_scope(run))
                        with self.assertRaises(SpecError):
                            verify_required(run)
                    else:
                        self.assertIsNotNone(current_spec_scope(run))
                        verify_required(run)
                    result = fixture.call_capability('concorde-specify-loop', task)
                    self.assertEqual('blocked' if related else 'succeeded', result['status'], result)
                    self.assertNotIn('scope.bank', fixture.spec_review_targets())
                    if not related:
                        self.assertEqual([], fixture.model.calls)
                    self.assertEqual(history, read_change(fixture.root)['gap_history'])
                finally:
                    fixture.doCleanups()

    @verifies("scenario.development.specify-loop")
    def test_standalone_authors_and_reviews_without_implementation_or_readiness(self):
        result = self.call_capability("concorde-specify-loop")
        self.assertEqual("succeeded", result["status"], result)
        data = result["output"]["data"]
        self.assertEqual("completed", data["outcome"])
        self.assertEqual(["specify", "spec-review"], [item["stage"] for item in self.model.calls])
        state = read_change(self.root)
        self.assertNotEqual("ready", state["status"])
        self.assertEqual({"spec": True}, state["review_requirements"][self.task["target_id"]])
        self.assertFalse(state["targets"].get(self.task["target_id"], {}).get("plan"))
        self.assertTrue(data["artifacts"])
        self.assertFalse(data["checks"])
        self.assertIn("concorde-specify", data["completed_capabilities"])

    @verifies("scenario.development.specify-loop", "scenario.development.dev-loop-ready")
    def test_development_composes_specify_loop_and_resumes_its_evidence(self):
        from concorde.development import capability_host
        first = self.call_capability("concorde-specify-loop")
        self.assertEqual("succeeded", first["status"], first)
        with patch.object(capability_host, "invoke_capability", wraps=capability_host.invoke_capability) as invoke:
            result = self.call_capability("concorde-dev-loop")
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        self.assertEqual(first["output"]["data"]["change_id"], result["output"]["data"]["change_id"])
        stages = [item["stage"] for item in self.model.calls]
        self.assertNotIn("specify", stages)
        self.assertNotIn("spec-review", stages)
        self.assertIn("plan", stages)
        self.assertIn(("concorde-dev-loop", "concorde-specify-loop"),
                      [call.args[:2] for call in invoke.call_args_list])

    @verifies("scenario.development.specify-loop")
    def test_skip_options_record_only_spec_evidence(self):
        result = self.call_capability("concorde-specify-loop",
                                     {**self.task, "specify": False, "run_reviews": False})
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual([], self.model.calls)
        state = read_change(self.root)
        self.assertEqual({"spec": False}, state["review_requirements"][self.task["target_id"]])
        self.assertEqual({"spec"}, set(state["reviews"][self.task["target_id"]]))
        self.assertEqual("skipped", state["reviews"][self.task["target_id"]]["spec"]["status"])

    @verifies("scenario.development.specify-loop", "scenario.development.dev-loop-spec-gap")
    def test_gap_stops_and_required_review_cannot_be_disabled_on_resume(self):
        first = self.call_capability("concorde-specify-loop", callback=self.missing("spec-review"))
        self.assertEqual("blocked", first["status"], first)
        self.assertEqual("spec_incomplete", first["output"]["data"]["outcome"])
        self.assertEqual("waiting", read_change(self.root)["status"])
        second = self.call_capability("concorde-specify-loop", {**self.task, "run_reviews": False},
                                      callback=self.missing("spec-review"))
        self.assertEqual("blocked", second["status"], second)
        self.assertTrue(read_change(self.root)["review_requirements"][self.task["target_id"]]["spec"])
        self.assertNotEqual("skipped", read_change(self.root)["reviews"][self.task["target_id"]]["spec"]["status"])
        document = self.root / "specs/transfer/module.md"
        document.write_text(document.read_text() + "\nTransfer owns the daily-limit admission rule.\n")
        resumed = self.call_capability("concorde-specify-loop")
        self.assertEqual("succeeded", resumed["status"], resumed)
        self.assertEqual([], read_change(self.root)["gaps"])

    @verifies("scenario.development.specify-loop")
    def test_policy_preview_contains_only_spec_agents_and_does_not_create_change(self):
        result = self.call_capability("concorde-specify-loop", mode="describe-policy")
        self.assertEqual("described", result["status"], result)
        self.assertEqual("described", result["output"]["data"]["outcome"])
        self.assertEqual([], self.model.calls)
        self.assertIsNone(read_change(self.root))
        self.assertEqual(["specify", "spec-review"], [item["phase"] for item in self.host.descriptions])

    @verifies("scenario.development.specify-loop", "scenario.development.flow-execution")
    def test_rejected_author_preserves_the_error_and_never_reaches_review(self):
        def foreign_document(stage, snapshot, data, cwd):
            if stage == "specify":
                data["documents"] = [{"path": "specs/audit/module.md", "content": "Foreign Spec"}]
        result = self.call_capability("concorde-specify-loop", callback=foreign_document)
        self.assertEqual("blocked", result["status"], result)
        self.assertIsNone(result["output"])
        self.assertEqual("child_blocked", result["errors"][0]["code"])
        self.assertIn("permission_denied", result["errors"][0]["message"])
        self.assertEqual(["specify"], [item["stage"] for item in self.model.calls])

    @verifies("scenario.development.specify-loop", "scenario.development.flow-execution")
    def test_studio_exposes_independent_spec_flow_and_development_composition(self):
        from concorde.harness.studio import build_studio_flow
        from tests.concorde.spec.support import PACKAGE
        spec = build_studio_flow("concorde-specify-loop", self.root, PACKAGE).get_graph(xray=True)
        self.assertTrue(any(name.endswith(":specify_loop:specify") for name in spec.nodes))
        self.assertTrue(any(name.endswith(":specify_loop:review_spec") for name in spec.nodes))
        self.assertFalse(any(name.endswith(":plan") or name.endswith(":ready") for name in spec.nodes))
        dev = build_studio_flow("concorde-dev-loop", self.root, PACKAGE).get_graph(xray=True)
        self.assertTrue(any(name.endswith(":development_loop:specify_loop") for name in dev.nodes))
        self.assertFalse(any(name.endswith(":development_loop:review_spec") for name in dev.nodes))
