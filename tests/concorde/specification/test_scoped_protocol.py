import json
import tempfile
import unittest
from pathlib import Path
from concorde.capabilities.operation_data import typed
from concorde.capabilities.operation_service import OperationHost, run_operation
from concorde.specification.repository import SpecRepository, SpecError
from concorde.specification.context import resolve_context, recheck_context
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
        self.assertEqual(1,len(double.calls))
        self.assertFalse((self.root/'.concorde/attempts').exists())
    def test_standard_loop_real_checks_and_delivery(self):
        double=ModelProcessDouble()
        result=self.run_op('concorde-standard-dev-loop',{'target_id':'service.transfer','task':'Implement the transfer contract'},double)
        self.assertEqual('succeeded',result['status'],result)
        self.assertEqual('delivered',result['output']['data']['outcome'])
        self.assertEqual('passed',result['output']['data']['checks'][0]['status'])
        self.assertFalse(any((self.root/'.concorde/attempts').iterdir()))
        self.assertEqual(['specify','context-solve','plan','tasks','implementation'],[c['stage'] for c in double.calls])
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
