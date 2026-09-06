import json
import tempfile
import unittest
from pathlib import Path
from concorde.capabilities.operation_data import typed
from concorde.capabilities.operation_service import OperationHost, run_operation
from concorde.specification.repository import SpecRepository, SpecError
from concorde.specification.context import (resolve_context, recheck_context,
    resolve_discovery_context, recheck_discovery_context)
from concorde.specification.validation import validate_repository
from .support import project, PACKAGE, CONFIGURATION, ModelProcessDouble

class ScopedProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.registry=project(self.root)
    def run_op(self, name, data, double=None, mode='execute'):
        self.host=OperationHost(self.root,PACKAGE,executor=double.executor if double else None,
            allow_primary_worktree=True,mode=mode)
        return run_operation(name,CONFIGURATION,typed(name+'-request',data),host_context=self.host)
    def test_independent_dimensions_and_complete_arbitrary_collections(self):
        repo=SpecRepository(self.root)
        target=repo.select('service.transfer','feature.transfer')
        self.assertEqual(('scope.bank','scope.audit'),target.participates_in)
        self.assertIsNone(target.component_parent)
        context=resolve_context(repo,target.id,focus_id='feature.transfer').value
        self.assertEqual(list(target.documents),[d['path'] for d in context['documents']])
        self.assertEqual(['protocol/principles.md','protocol/kinds/service.md'],[d['path'] for d in context['protocol']])
        text=json.dumps(context)
        self.assertNotIn('PRIVATE_CODE',text)
        self.assertNotIn('specs/audit-scope.md',text)
        self.assertNotIn('specs/ledger-api.md',text)
        self.assertEqual('success',validate_repository(self.root).status)
    def test_module_api_focus_is_local(self):
        repo=SpecRepository(self.root)
        self.assertEqual('module.ledger',repo.select('module.ledger','api.ledger').id)
        with self.assertRaises(SpecError): repo.select('module.ledger','feature.transfer')
        self.registry['entry_target']='module.ledger'
        (self.root/'.concorde/specs.json').write_text(json.dumps(self.registry))
        with self.assertRaisesRegex(SpecError,'Domain or Service'):SpecRepository(self.root)
    def test_main_discovers_domain_and_service_specs_then_starts_fresh_worker(self):
        double=ModelProcessDouble()
        result=self.run_op('concorde-ask',{'task':'Explain transfer'},double)
        self.assertEqual('succeeded',result['status'],result)
        data=result['output']['data']
        self.assertEqual(['scope.bank','service.transfer'],data['discovered_targets'])
        self.assertEqual(['service.transfer'],[route['target_id'] for route in data['routes']])
        self.assertEqual(['route','route','ask','synthesize'],[call['stage'] for call in double.calls])
        self.assertEqual(['concorde-main','concorde-main','concorde-reader','concorde-main'],
                         [call['capability'] for call in double.calls])
        first,second,worker,final=double.calls
        self.assertEqual(['scope.bank'],[item['target_id'] for item in first['snapshot']['targets']])
        self.assertEqual(['scope.bank','service.transfer'],[item['target_id'] for item in second['snapshot']['targets']])
        self.assertEqual('service.transfer',worker['snapshot']['target_id'])
        self.assertEqual(second['snapshot']['targets'],final['snapshot']['targets'])
        self.assertEqual(4,len({str(call['cwd']) for call in double.calls}))
        invocation_ids=[item.completion.invocation_id for item in self.host.evidence]
        self.assertEqual(4,len(invocation_ids));self.assertEqual(4,len(set(invocation_ids)))
        for call in (first,second,final):
            text=json.dumps(call['snapshot'])
            self.assertNotIn('# Ledger API',text)
            self.assertNotIn('PRIVATE_CODE',text)
    def test_main_can_route_module_worker_but_cannot_expand_module_spec(self):
        def route(stage,snapshot,data,cwd):
            if stage=='route':
                data.update(outcome='routed',expand_targets=[],gaps=[],routes=[{
                    'target_id':'module.ledger','focus_id':'api.ledger','task':'Explain ledger reads','constraints':[]}])
        double=ModelProcessDouble(route)
        result=self.run_op('concorde-ask',{'task':'Explain ledger reads'},double)
        self.assertEqual('succeeded',result['status'],result)
        self.assertEqual(['route','ask','synthesize'],[call['stage'] for call in double.calls])
        self.assertEqual('module.ledger',double.calls[1]['snapshot']['target_id'])
        self.assertTrue(all(item['kind']!='module' for call in (double.calls[0],double.calls[2])
                            for item in call['snapshot']['targets']))
        def expand(stage,snapshot,data,cwd):
            if stage=='route':data.update(outcome='expand',expand_targets=['module.ledger'],routes=[],gaps=[])
        blocked=self.run_op('concorde-ask',{'task':'Open the ledger Spec'},ModelProcessDouble(expand))
        self.assertEqual('blocked',blocked['status']);self.assertEqual('permission_denied',blocked['errors'][0]['code'])
    def test_main_can_split_one_request_into_separate_target_workers(self):
        def routes(stage,snapshot,data,cwd):
            if stage=='route':data.update(outcome='routed',expand_targets=[],gaps=[],routes=[
                {'target_id':'service.transfer','focus_id':'feature.transfer','task':'Explain transfer','constraints':[]},
                {'target_id':'module.ledger','focus_id':'api.ledger','task':'Explain ledger reads','constraints':[]}])
        double=ModelProcessDouble(routes)
        result=self.run_op('concorde-ask',{'task':'Explain transfer and ledger'},double)
        self.assertEqual('succeeded',result['status'],result)
        workers=[call for call in double.calls if call['capability']=='concorde-reader']
        self.assertEqual(['service.transfer','module.ledger'],[call['snapshot']['target_id'] for call in workers])
        self.assertEqual(2,len(result['output']['data']['worker_results']))
        main=[call for call in double.calls if call['capability']=='concorde-main']
        self.assertTrue(all(item['kind']!='module' for call in main for item in call['snapshot']['targets']))
    def test_main_reports_routing_and_worker_spec_gaps_without_hidden_context(self):
        def routing_gap(stage,snapshot,data,cwd):
            if stage=='route':data.update(outcome='spec_incomplete',answer='Routing facts are missing.',
                expand_targets=[],routes=[],gaps=[{'question':'Which target owns settlement?',
                'blocked_step':'Select a worker','needed_contract':'Settlement routing responsibility',
                'target_id':'scope.bank'}])
        blocked=self.run_op('concorde-ask',{'task':'Explain settlement'},ModelProcessDouble(routing_gap))
        self.assertEqual('blocked',blocked['status']);gap=blocked['output']['data']['gaps'][0]
        self.assertEqual('scope.bank',gap['target_id']);self.assertEqual(blocked['output']['data']['context_id'],gap['context_id'])
        def worker_gap(stage,snapshot,data,cwd):
            if stage=='route':data.update(outcome='routed',expand_targets=[],gaps=[],routes=[{
                'target_id':'module.ledger','focus_id':'api.ledger','task':'Explain settlement ledger','constraints':[]}])
            if stage=='ask':data.update(outcome='spec_incomplete',answer='Ledger settlement is unspecified.',gaps=[{
                'question':'When is settlement final?','blocked_step':'Explain settlement ledger',
                'needed_contract':'Settlement completion rule'}])
            if stage=='synthesize':
                gap=snapshot['worker_results'][0]['data']['gaps'][0]
                data.update(outcome='spec_incomplete',answer='The selected Module Spec is incomplete.',gaps=[gap])
        result=self.run_op('concorde-ask',{'task':'Explain settlement ledger'},ModelProcessDouble(worker_gap))
        self.assertEqual('blocked',result['status'],result);gap=result['output']['data']['gaps'][0]
        worker=result['output']['data']['worker_results'][0]['data']
        self.assertEqual('module.ledger',gap['target_id']);self.assertEqual(worker['context_id'],gap['context_id'])
    def test_main_selects_the_single_owner_before_a_non_ask_worker(self):
        double=ModelProcessDouble()
        result=self.run_op('concorde-plan',{'task':'Plan the transfer promise'},double)
        self.assertEqual('succeeded',result['status'],result)
        self.assertEqual('service.transfer',result['output']['data']['target_id'])
        self.assertEqual('concorde-main-route',result['output']['data']['completed_operations'][0])
        self.assertEqual(['route','route','context-solve','plan'],[call['stage'] for call in double.calls])
        self.assertEqual(['concorde-main','concorde-main','concorde-context-assessor','concorde-planner'],
                         [call['capability'] for call in double.calls])
    def test_non_ask_main_route_cannot_split_or_rewrite_user_intent(self):
        def split(stage,snapshot,data,cwd):
            if stage=='route':data.update(outcome='routed',expand_targets=[],gaps=[],routes=[
                {'target_id':'service.transfer','focus_id':None,'task':snapshot['task'],'constraints':snapshot['constraints']},
                {'target_id':'module.ledger','focus_id':None,'task':snapshot['task'],'constraints':snapshot['constraints']}])
        result=self.run_op('concorde-plan',{'task':'Plan transfer'},ModelProcessDouble(split))
        self.assertEqual('blocked',result['status']);self.assertEqual('ambiguous_route',result['errors'][0]['code'])
        def rewrite(stage,snapshot,data,cwd):
            if stage=='route':data.update(outcome='routed',expand_targets=[],gaps=[],routes=[
                {'target_id':'service.transfer','focus_id':None,'task':'Different intent','constraints':[]}])
        result=self.run_op('concorde-plan',{'task':'Plan transfer','constraints':['Keep API stable']},ModelProcessDouble(rewrite))
        self.assertEqual('blocked',result['status']);self.assertEqual('incompatible_handoff',result['errors'][0]['code'])
    def test_main_cannot_guess_an_unmentioned_discovery_or_route_target(self):
        (self.root/'specs/how-money-moves.md').write_text('# Banking\nNo downstream target is identified.\n')
        def expand(stage,snapshot,data,cwd):
            if stage=='route':data.update(outcome='expand',expand_targets=['service.transfer'],routes=[],gaps=[])
        result=self.run_op('concorde-ask',{'task':'Explain transfer'},ModelProcessDouble(expand))
        self.assertEqual('blocked',result['status']);self.assertEqual('incompatible_handoff',result['errors'][0]['code'])
        def route(stage,snapshot,data,cwd):
            if stage=='route':data.update(outcome='routed',expand_targets=[],gaps=[],routes=[{
                'target_id':'module.ledger','focus_id':None,'task':snapshot['task'],'constraints':[]}])
        result=self.run_op('concorde-ask',{'task':'Explain ledger'},ModelProcessDouble(route))
        self.assertEqual('blocked',result['status']);self.assertEqual('incompatible_handoff',result['errors'][0]['code'])
    def test_discovery_context_is_append_only_digest_bound_and_domain_service_only(self):
        repo=SpecRepository(self.root)
        first=resolve_discovery_context(repo,('scope.bank',),operation='concorde-ask',phase='route',task='Route transfer')
        second=resolve_discovery_context(repo,('scope.bank','service.transfer'),operation='concorde-ask',phase='route',task='Route transfer')
        self.assertNotEqual(first.id,second.id)
        self.assertEqual(['scope.bank','service.transfer'],[item['target_id'] for item in second.value['targets']])
        with self.assertRaisesRegex(SpecError,'cannot read module'):
            resolve_discovery_context(repo,('scope.bank','module.ledger'),operation='concorde-ask',phase='route',task='Route ledger')
        (self.root/'specs/send-money.md').write_text('# Changed service routing facts\n')
        with self.assertRaisesRegex(SpecError,'changed'):recheck_discovery_context(repo,second)
        self.registry['targets'][3]['documents'].append('specs/send-money.md')
        (self.root/'.concorde/specs.json').write_text(json.dumps(self.registry))
        with self.assertRaisesRegex(SpecError,'shares Module Spec'):
            resolve_discovery_context(SpecRepository(self.root),('scope.bank','service.transfer'),
                operation='concorde-ask',phase='route',task='Route transfer')
    def test_membership_changes_invalidate_snapshot(self):
        repo=SpecRepository(self.root); snapshot=resolve_context(repo,'service.transfer')
        self.registry['targets'][2]['documents'].reverse()
        (self.root/'.concorde/specs.json').write_text(json.dumps(self.registry))
        with self.assertRaisesRegex(SpecError,'membership'): recheck_context(repo,snapshot)
    def test_scope_cycle_rejected(self):
        self.registry['targets'][0]['scope_parent']='scope.audit'
        self.registry['targets'][1]['scope_parent']='scope.bank'
        (self.root/'.concorde/specs.json').write_text(json.dumps(self.registry))
        with self.assertRaisesRegex(SpecError,'cycle'): SpecRepository(self.root)
    def test_spec_symlink_rejected(self):
        (self.root/'specs/send-money.md').unlink()
        (self.root/'specs/send-money.md').symlink_to(self.root/'secret.py')
        with self.assertRaises(ValueError): resolve_context(SpecRepository(self.root),'service.transfer')
    def test_gap_blocks_planning_without_attempt(self):
        def gap(stage,snapshot,data,cwd):
            if stage=='context-solve':
                data.update(outcome='spec_incomplete',gaps=[{'question':'Who owns the daily limit?',
                    'blocked_step':'Decide transfer admission','needed_contract':'Daily limit ownership'}])
        double=ModelProcessDouble(gap)
        result=self.run_op('concorde-plan',{'target_id':'service.transfer','task':'Add a daily limit'},double)
        self.assertEqual('blocked',result['status'],result)
        self.assertEqual('spec_incomplete',result['output']['data']['outcome'])
        self.assertEqual(['route','context-solve'],[call['stage'] for call in double.calls])
        self.assertFalse((self.root/'.concorde/attempts').exists())
    def test_standard_loop_real_checks_and_delivery(self):
        double=ModelProcessDouble()
        result=self.run_op('concorde-standard-dev-loop',{'task':'Implement the transfer contract'},double)
        self.assertEqual('succeeded',result['status'],result)
        self.assertEqual('delivered',result['output']['data']['outcome'])
        self.assertEqual('passed',result['output']['data']['checks'][0]['status'])
        self.assertFalse(any((self.root/'.concorde/attempts').iterdir()))
        self.assertEqual(['route','route','specify','context-solve','plan','tasks','implementation'],[c['stage'] for c in double.calls])
        for call in double.calls:
            if call['stage']!='implementation':
                self.assertNotEqual(self.root,call['cwd'])
                self.assertNotIn('PRIVATE_CODE',call['prompt'])
                self.assertNotIn('app/transfer.py',call['prompt'])
        self.assertTrue(all(d['write_paths']==[] for d in self.host.descriptions if d['phase']!='implementation'))
    def test_failed_behavioral_check_prevents_delivery(self):
        def broken(stage,snapshot,data,cwd):
            if stage=='implementation': (cwd/'app/transfer.py').write_text('def transfer(balance,amount):\n    return 0\n')
        result=self.run_op('concorde-standard-dev-loop',{'target_id':'service.transfer','task':'Implement transfer'},ModelProcessDouble(broken))
        self.assertEqual('failed',result['status'],result)
        self.assertEqual('failed',result['output']['data']['checks'][0]['status'])
        self.assertTrue(any((self.root/'.concorde/attempts').iterdir()))
    def test_wrong_context_result_rejected(self):
        def wrong(stage,snapshot,data,cwd): data['context_id']='sha256:'+'0'*64
        result=self.run_op('concorde-ask',{'target_id':'service.transfer','task':'Explain transfer'},ModelProcessDouble(wrong))
        self.assertEqual('blocked',result['status'],result)
        self.assertEqual('incompatible_handoff',result['errors'][0]['code'])

if __name__=='__main__': unittest.main()
