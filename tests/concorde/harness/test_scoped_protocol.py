import copy
import json
import re
import tempfile
import unittest
from pathlib import Path
from concorde.spec.typed_data import typed, TypedDataError
from concorde.spec.verification import verifies
from concorde.development.capability_service import CapabilityHost, run_capability
from concorde.spec.repository import SpecRepository, SpecError
from concorde.harness.context import (resolve_context, recheck_context,
    resolve_discovery_context, recheck_discovery_context)
from concorde.spec.validation import validate_repository
from tests.concorde.spec.support import (project, PACKAGE, CONFIGURATION, ModelProcessDouble,
    module_document, update_document_declaration)

class ScopedProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.registry=project(self.root)
    def call_capability(self, name, data, double=None, mode='execute'):
        self.host=CapabilityHost(self.root,PACKAGE,executor=double.executor if double else None,
            allow_primary_worktree=True,mode=mode)
        return run_capability(name,CONFIGURATION,typed(name+'-request',data),host_context=self.host)
    @verifies("scenario.harness.context-freeze")
    def test_module_dependencies_and_complete_arbitrary_collections(self):
        repo=SpecRepository(self.root)
        target=repo.select('service.transfer','scenario.transfer.debit')
        self.assertEqual(('module.ledger',),target.uses)
        self.assertIsNone(target.parent)
        context=resolve_context(repo,target.id,focus_id='scenario.transfer.debit').value
        self.assertEqual(list(target.documents),context['document_order'])
        self.assertEqual(list(target.documents),[d['path'] for section in ('target_spec','shared_specs')
                                                  for d in context[section]])
        self.assertEqual(['generated/protocol/principles.md','generated/protocol/kinds/module.md'],[d['path'] for d in context['protocol']])
        text=json.dumps(context)
        self.assertNotIn('PRIVATE_CODE',text)
        self.assertNotIn('specs/audit/module.md',text)
        self.assertNotIn('specs/ledger/module.md',text)
        self.assertEqual('success',validate_repository(self.root).status)
        participants=repo.dependencies(repo.select('scope.bank'))
        self.assertEqual(['service.transfer','module.ledger','scope.audit'],[item['target_id'] for item in participants])
        self.assertTrue(all(item['relied_upon_promises'] for item in participants))
    def test_protocol_handoff_rules_are_bound_context_and_old_binding_is_rejected(self):
        (self.root / 'AGENTS.md').write_text('UNTRUSTED_AMBIENT_GUIDANCE')
        (self.root / 'CLAUDE.md').write_text('UNTRUSTED_AMBIENT_GUIDANCE')
        context = resolve_context(SpecRepository(self.root), 'service.transfer').value
        self.assertIn('### P10. Explicit session handoffs', context['protocol'][0]['content'])
        self.assertNotIn('UNTRUSTED_AMBIENT_GUIDANCE', json.dumps(context))
        path = self.root / '.concorde/config.json'
        config = json.loads(path.read_text())
        config['protocol']['version'] = '1.0.0'
        path.write_text(json.dumps(config))
        with self.assertRaises(SpecError) as failure:
            SpecRepository(self.root)
        self.assertEqual('protocol_mismatch', failure.exception.code)
        self.assertEqual('1.0.0', json.loads(path.read_text())['protocol']['version'])

    def test_document_identity_and_membership_are_validated(self):
        paths=['specs/transfer/module.md','specs/transfer/promises.md','specs/ledger/module.md']
        original={path:(self.root/path).read_text() for path in paths}
        update_document_declaration(self.root,'specs/transfer/module.md',
                                    targets=['service.transfer','module.ledger'])
        with self.assertRaisesRegex(SpecError,'differs from registry'):
            resolve_context(SpecRepository(self.root),'service.transfer')
        report=validate_repository(self.root)
        self.assertIn('CONCORDE-DOCUMENT-001',{finding.rule_id for finding in report.findings})
        for path,text in original.items():(self.root/path).write_text(text)
        update_document_declaration(self.root,'specs/ledger/module.md',id='document.transfer.feature')
        report=validate_repository(self.root)
        self.assertIn('CONCORDE-DOCUMENT-002',{finding.rule_id for finding in report.findings})
        for path,text in original.items():(self.root/path).write_text(text)
    @verifies("scenario.harness.context-gap")
    def test_missing_module_dependency_is_validated_and_stops_context_solving(self):
        path=self.root/'specs/bank/module.md';path.write_text(path.read_text().split('```concorde-dependencies',1)[0])
        report=validate_repository(self.root)
        self.assertEqual('invalid',report.status)
        self.assertIn('CONCORDE-DEPENDENCY-001',{finding.rule_id for finding in report.findings})
        for peer in ('service.transfer','module.ledger','scope.audit'):
            self.assertTrue(any(peer in finding.message for finding in report.findings))
        double=ModelProcessDouble()
        result=self.call_capability('concorde-plan',{'target_id':'scope.bank','task':'Plan a banking change'},double)
        self.assertEqual('blocked',result['status'],result)
        self.assertEqual('spec_incomplete',result['output']['data']['outcome'])
        self.assertEqual([],[call['stage'] for call in double.calls])
        self.assertTrue(all(gap['target_id']=='scope.bank' and gap['context_id']==result['output']['data']['context_id']
                            for gap in result['output']['data']['gaps']))
        self.assertFalse((self.root/'.concorde/attempts').exists())
    @verifies("scenario.harness.context-gap")
    def test_duplicate_and_unrelated_dependency_declarations_are_rejected(self):
        path=self.root/'specs/bank/module.md';original=path.read_text()
        prefix,rest=original.split('```concorde-dependencies\n',1);payload,suffix=rest.split('\n```',1)
        participants=json.loads(payload)
        cases=[(participants+[copy.deepcopy(participants[0])],'CONCORDE-DEPENDENCY-001'),
               ([{**participants[0],'target_id':'module.unknown'},*participants[1:]],'CONCORDE-DEPENDENCY-001')]
        for value,rule in cases:
            with self.subTest(rule=rule):
                path.write_text(prefix+'```concorde-dependencies\n'+json.dumps(value,indent=2)+'\n```'+suffix)
                report=validate_repository(self.root)
                self.assertEqual('invalid',report.status)
                self.assertIn(rule,{finding.rule_id for finding in report.findings})
        double=ModelProcessDouble()
        result=self.call_capability('concorde-plan',{'target_id':'scope.bank','task':'Plan a banking change'},double)
        self.assertEqual('conflicting',result['output']['data']['outcome'])
        self.assertEqual([],result['output']['data']['gaps'])
        self.assertEqual([],[call['stage'] for call in double.calls])
        path.write_text(original)
    def test_module_scenario_focus_is_local(self):
        repo=SpecRepository(self.root)
        self.assertEqual('module.ledger',repo.select('module.ledger','scenario.ledger.read').id)
        with self.assertRaises(SpecError): repo.select('module.ledger','scenario.transfer.debit')
        self.registry['entry_target']='module.ledger'
        (self.root/'.concorde/specs.json').write_text(json.dumps(self.registry))
        self.assertEqual('module.ledger',SpecRepository(self.root).entry_target)
    @verifies("scenario.development.answer-question")
    def test_main_answers_directly_from_complete_injected_contexts(self):
        double=ModelProcessDouble()
        result=self.call_capability('concorde-main',{'task':'Explain transfer'},double)
        self.assertEqual('succeeded',result['status'],result)
        data=result['output']['data']
        self.assertEqual(['scope.bank','service.transfer'],data['discovered_targets'])
        self.assertEqual([],data['routes'])
        self.assertNotIn('worker_results',data)
        self.assertEqual(['route','route'],[call['stage'] for call in double.calls])
        self.assertEqual(['concorde-coordinator']*2,[call['capability'] for call in double.calls])
        first,second=double.calls
        self.assertEqual(['scope.bank'],[item['target_id'] for item in first['snapshot']['targets']])
        self.assertEqual(['scope.bank','service.transfer'],[item['target_id'] for item in second['snapshot']['targets']])
        source={item['path']:item['content'] for item in second['snapshot']['documents']}
        for path in ('specs/transfer/module.md','specs/transfer/promises.md'):
            self.assertEqual((self.root/path).read_text(),source[path])
        self.assertEqual(2,len({str(call['cwd']) for call in double.calls}))
        self.assertEqual(['generated/protocol/principles.md','generated/protocol/kinds/module.md'],
            [item['path'] for item in first['snapshot']['protocol']])
        invocation_ids=[item.completion.invocation_id for item in self.host.evidence]
        self.assertEqual(2,len(invocation_ids));self.assertEqual(2,len(set(invocation_ids)))
        for call in double.calls:
            text=json.dumps(call['snapshot'])
            self.assertNotIn('# Ledger API',text)
            self.assertNotIn('PRIVATE_CODE',text)

    @verifies("scenario.development.topology-design", "scenario.development.topology-accept", "scenario.development.topology-apply", "scenario.development.topology-stale")
    def test_main_design_accept_and_exact_apply_create_topology_atomically(self):
        def callback(stage,snapshot,data,cwd):
            if stage=='route' and snapshot['action']=='design-topology':
                discovered=[item['target_id'] for item in snapshot['targets']]
                if 'scope.audit' not in discovered:
                    data.update(outcome='expand',expand_targets=['scope.audit','module.ledger'],routes=[],gaps=[],topology_design=None)
                else:
                    registry=copy.deepcopy(snapshot['topology'])
                    registry['targets'][3]={**registry['targets'][3],'title':'Account ledger'}
                    registry['targets'].append({'id':'service.audit-report','kind':'module','title':'Audit reports',
                        'documents':['specs/audit-report/module.md'],'parent':None,'uses':[],
                        'files':[],'checks':[]})
                    registry['targets'][1]['uses'].append('service.audit-report')
                    design=typed('concorde-topology-design',{'summary':'Add an audit reporting Service.',
                        'registry':registry,'spec_tasks':[
                          {'target_id':'scope.audit','task':'Add service.audit-report (kind service): responsibility Publish the audit reporting view; selection condition audit report generation or retrieval; relied-upon promise Audit reports expose the accepted audit records.'},
                          {'target_id':'module.ledger','task':'Keep the Ledger API complete under its clarified title.'},
                          {'target_id':'service.audit-report','task':'Define the self-contained audit reporting boundary.'}],
                        'migration_constraints':[],'acceptance':['The new Service is registered and routable.']})
                    data.update(outcome='topology_proposed',answer='Audit reporting topology designed.',
                        expand_targets=[],routes=[],gaps=[],topology_design=design)
            if stage=='topology-author' and snapshot['target']['id']=='scope.audit':
                participants=[
                    {'target_id':'service.transfer',
                     'responsibility':'Supply successful transfer outcomes to the audit Domain.',
                     'selection_condition':'Select when audit behavior depends on a completed transfer.',
                     'relied_upon_promises':['A successful transfer reports the accepted balance change.']},
                    {'target_id':'service.audit-report',
                     'responsibility':'Publish the audit reporting view.',
                     'selection_condition':'Select for audit report generation or retrieval.',
                     'relied_upon_promises':['Audit reports expose the accepted audit records.']}]
                entities=[{'id':'entity.audit.transfer','title':'Transfer service','kind':'module',
                     'responsibility':'Reports successful balance changes.','target_id':'service.transfer'},
                    {'id':'entity.audit.reports','title':'Audit reports','kind':'module',
                     'responsibility':'Publishes the audit reporting view.','target_id':'service.audit-report'},
                    {'id':'entity.audit.record','title':'Audit record','kind':'concept',
                     'responsibility':'Describes one accepted balance change.'}]
                diagram=('flowchart TB\n    accTitle: Audit outcomes\n'
                    '    accDescr: The transfer service produces the accepted change that becomes one audit record, which the reporting Module publishes.\n'
                    '    transfer["Transfer service"]\n    record["Audit record"]\n    reports["Audit reports"]\n'
                    '    transfer -->|produces| record\n    record -->|published by| reports')
                data['documents']=[{'path':'specs/audit/module.md','content':module_document(
                    'document.audit','scope.audit','Audit',
                    'Audit describes the outcome an accepted balance change must produce and routes its\n'
                    'reporting view to service.audit-report.',
                    '### scenario.audit.record — An accepted transfer becomes one audit record\n\n'
                    '- GIVEN a transfer the transfer Module reports as successful\n'
                    '- WHEN Audit receives that accepted balance change\n'
                    '- THEN one audit record describes the sender, the receiver and the amount\n',
                    ('Audit owns its record concept and routes reporting to service.audit-report.',entities),
                    'Route audit reporting to service.audit-report.',diagram,participants)}]
        double=ModelProcessDouble(callback)
        design=self.call_capability('concorde-main',{'action':'design-topology','task':'Add audit reports'},double)
        self.assertEqual('topology_proposed',design['output']['data']['outcome']);proposal=design['output']['data']['topology_proposal']
        self.assertFalse((self.root/'specs/audit-report/module.md').exists())
        prepared=self.call_capability('concorde-main',{'action':'accept-topology','topology_proposal':proposal},double)
        self.assertIsNotNone(prepared['output'],prepared)
        self.assertEqual('topology_prepared',prepared['output']['data']['outcome']);application=prepared['output']['data']['application']
        self.assertEqual({'id','path','digest'},set(application))
        self.assertNotIn('# Audit reports',json.dumps(prepared));self.assertNotIn('# Ledger API',json.dumps(prepared))
        self.assertTrue((self.root/application['path']).is_file());self.assertFalse((self.root/'specs/audit-report/module.md').exists())
        tampered={**application,'digest':'sha256:'+'0'*64}
        rejected=self.call_capability('concorde-main',{'action':'apply-topology','application':tampered},double)
        self.assertEqual('blocked',rejected['status']);self.assertTrue((self.root/application['path']).is_file())
        applied=self.call_capability('concorde-main',{'action':'apply-topology','application':application},double)
        self.assertEqual('topology_applied',applied['output']['data']['outcome']);self.assertFalse((self.root/application['path']).exists())
        repository=SpecRepository(self.root);self.assertIn('service.audit-report',repository.targets)
        self.assertTrue((self.root/'specs/audit-report/module.md').is_file())
        authors=[call for call in double.calls if call['stage']=='topology-author']
        self.assertEqual(['scope.audit','module.ledger','service.audit-report'],
                         [call['snapshot']['target']['id'] for call in authors])
        module_author=next(call for call in authors if call['snapshot']['target']['id']=='module.ledger')
        self.assertIn('# Ledger API',json.dumps(module_author['snapshot']))
        main=[call for call in double.calls if call['capability']=='concorde-coordinator']
        self.assertTrue(any('# Ledger API' in json.dumps(call['snapshot']) for call in main))
        self.assertTrue(all('LEDGER_IMPLEMENTATION_CODE' not in json.dumps(call['snapshot']) for call in main))
    @verifies("scenario.development.topology-design", "scenario.development.topology-accept", "scenario.development.topology-apply", "scenario.development.topology-stale")
    def test_shared_truth_change_requires_all_references_and_identical_bytes(self):
        def design_callback(stage,snapshot,data,cwd):
            if stage!='route' or snapshot['action']!='design-topology':return
            if 'service.transfer' not in [item['target_id'] for item in snapshot['targets']]:
                data.update(outcome='expand',expand_targets=['service.transfer','module.ledger'],routes=[],gaps=[],topology_design=None)
                return
            registry=copy.deepcopy(snapshot['topology'])
            registry['targets'][3]['documents'].append('specs/transfer/promises.md')
            design=typed('concorde-topology-design',{'summary':'Share canonical transfer promises.',
                'registry':registry,'spec_tasks':[
                    {'target_id':'service.transfer','task':'Share document.transfer.promises with module.ledger and preserve its canonical truth.'},
                    {'target_id':'module.ledger','task':'Reference document.transfer.promises and agree to its canonical truth.'}],
                'migration_constraints':[],'acceptance':['Both targets resolve the same shared document once.']})
            data.update(outcome='topology_proposed',answer='Designed.',expand_targets=[],routes=[],gaps=[],topology_design=design)
        def missing_reference_task(stage,snapshot,data,cwd):
            design_callback(stage,snapshot,data,cwd)
            if data['outcome']=='topology_proposed':
                data['topology_design']['data']['spec_tasks']=data['topology_design']['data']['spec_tasks'][1:]
        invalid=self.call_capability('concorde-main',{'action':'design-topology','task':'Share transfer promises'},ModelProcessDouble(missing_reference_task))
        self.assertEqual('blocked',invalid['status'],invalid)
        self.assertIn('every retained referencing target task',invalid['errors'][0]['message'])
        designed=self.call_capability('concorde-main',{'action':'design-topology','task':'Share transfer promises'},ModelProcessDouble(design_callback))
        proposal=designed['output']['data']['topology_proposal']
        def reconcile(stage,snapshot,data,cwd,conflict=False):
            if stage!='topology-author':return
            item=next((item for item in data['documents'] if item['path']=='specs/transfer/promises.md'),None)
            if item is None:return
            match=re.search(r'```concorde-document\s*\n(.*?)^```',item['content'],re.M|re.S)
            declaration=json.loads(match.group(1));declaration['targets']=['service.transfer','module.ledger']
            item['content']=(item['content'][:match.start()]+'```concorde-document\n'+
                json.dumps(declaration,indent=2)+'\n```'+item['content'][match.end():])
            if conflict and snapshot['target']['id']=='module.ledger':item['content']+='\nConflicting Module proposal.\n'
        conflict=ModelProcessDouble(lambda *args:reconcile(*args,conflict=True))
        rejected=self.call_capability('concorde-main',{'action':'accept-topology','topology_proposal':proposal},conflict)
        self.assertEqual('blocked',rejected['status'],rejected)
        self.assertEqual('conflicting',rejected['output']['data']['outcome'])
        self.assertIn('conflicting shared truth',rejected['output']['data']['answer'])
        self.assertEqual([],list((self.root/'.concorde/topology-proposals').glob('*.json')))
        consensus=ModelProcessDouble(reconcile)
        prepared=self.call_capability('concorde-main',{'action':'accept-topology','topology_proposal':proposal},consensus)
        application=prepared['output']['data']['application']
        applied=self.call_capability('concorde-main',{'action':'apply-topology','application':application},consensus)
        self.assertEqual('topology_applied',applied['output']['data']['outcome'])
        repository=SpecRepository(self.root)
        service=resolve_context(repository,'service.transfer').value
        module=resolve_context(repository,'module.ledger').value
        self.assertEqual(['specs/transfer/promises.md'],[item['path'] for item in service['shared_specs']])
        self.assertEqual(['specs/transfer/promises.md'],[item['path'] for item in module['shared_specs']])
        self.assertNotIn('# Ledger API',json.dumps(service));self.assertNotIn('# Transfer money',json.dumps(module))
    @verifies("scenario.development.topology-accept", "scenario.development.topology-stale")
    def test_topology_acceptance_stops_before_writes_on_gap_or_stale_design(self):
        def design_callback(stage,snapshot,data,cwd):
            if stage=='route' and snapshot['action']=='design-topology':
                if 'service.transfer' not in [item['target_id'] for item in snapshot['targets']]:
                    data.update(outcome='expand',expand_targets=['service.transfer'],routes=[],gaps=[],topology_design=None)
                    return
                registry=copy.deepcopy(snapshot['topology'])
                registry['targets'][2]={**registry['targets'][2],'title':'Transfer service'}
                design=typed('concorde-topology-design',{'summary':'Rename the transfer Service.',
                    'registry':registry,'spec_tasks':[{'target_id':'service.transfer','task':'Explain the renamed Service.'}],
                    'migration_constraints':[],'acceptance':['The Service title and Spec agree.']})
                data.update(outcome='topology_proposed',answer='Designed.',expand_targets=[],routes=[],gaps=[],topology_design=design)
        design_double=ModelProcessDouble(design_callback)
        designed=self.call_capability('concorde-main',{'action':'design-topology','task':'Rename transfers'},design_double)
        proposal=designed['output']['data']['topology_proposal'];before=(self.root/'.concorde/specs.json').read_bytes()
        def gap(stage,snapshot,data,cwd):
            design_callback(stage,snapshot,data,cwd)
            if stage=='topology-author':data.update(outcome='spec_incomplete',answer='Naming promise missing.',documents=[],gaps=[{
                'question':'What consumer name is promised?','blocked_step':'Author the Service Spec','needed_contract':'Service naming rule'}])
        blocked=self.call_capability('concorde-main',{'action':'accept-topology','topology_proposal':proposal},ModelProcessDouble(gap))
        self.assertEqual('blocked',blocked['status']);self.assertEqual(before,(self.root/'.concorde/specs.json').read_bytes())
        (self.root/'.concorde/specs.json').write_text((self.root/'.concorde/specs.json').read_text()+'\n')
        stale=self.call_capability('concorde-main',{'action':'accept-topology','topology_proposal':proposal},ModelProcessDouble())
        self.assertEqual('blocked',stale['status']);self.assertEqual('stale_proposal',stale['errors'][0]['code'])
    @verifies("scenario.development.describe-policy")
    def test_topology_policy_description_is_read_only_at_both_acceptance_gates(self):
        def callback(stage,snapshot,data,cwd):
            if stage=='route' and snapshot['action']=='design-topology':
                discovered=[item['target_id'] for item in snapshot['targets']]
                if 'service.transfer' not in discovered:
                    data.update(outcome='expand',expand_targets=['service.transfer'],routes=[],gaps=[],topology_design=None)
                    return
                registry=copy.deepcopy(snapshot['topology'])
                registry['targets'][2]={**registry['targets'][2],'title':'Transfer boundary'}
                design=typed('concorde-topology-design',{'summary':'Clarify the transfer Service title.',
                    'registry':registry,'spec_tasks':[{'target_id':'service.transfer','task':'Keep the complete transfer Spec under the clarified title.'}],
                    'migration_constraints':[],'acceptance':['The title changes without changing behavior.']})
                data.update(outcome='topology_proposed',answer='Designed.',expand_targets=[],routes=[],gaps=[],topology_design=design)
        double=ModelProcessDouble(callback)
        designed=self.call_capability('concorde-main',{'action':'design-topology','task':'Clarify transfer title'},double)
        proposal=designed['output']['data']['topology_proposal']
        before_registry=(self.root/'.concorde/specs.json').read_bytes()
        before_specs={path.relative_to(self.root).as_posix():path.read_bytes() for path in (self.root/'specs').rglob('*.md')}
        described=self.call_capability('concorde-main',{'action':'accept-topology','topology_proposal':proposal},mode='describe-policy')
        self.assertEqual('described',described['status'],described)
        self.assertEqual(before_registry,(self.root/'.concorde/specs.json').read_bytes())
        self.assertEqual(before_specs,{path.relative_to(self.root).as_posix():path.read_bytes() for path in (self.root/'specs').rglob('*.md')})
        self.assertEqual([],list((self.root/'.concorde/topology-proposals').glob('*.json')))
        self.assertTrue(self.host.descriptions);self.assertTrue(all(not item['write_paths'] for item in self.host.descriptions))
        prepared=self.call_capability('concorde-main',{'action':'accept-topology','topology_proposal':proposal},double)
        application=prepared['output']['data']['application'];artifact_before=(self.root/application['path']).read_bytes()
        described=self.call_capability('concorde-main',{'action':'apply-topology','application':application},mode='describe-policy')
        self.assertEqual('described',described['status'],described)
        self.assertEqual(before_registry,(self.root/'.concorde/specs.json').read_bytes())
        self.assertEqual(artifact_before,(self.root/application['path']).read_bytes())
    def test_main_rejects_invalid_candidate_topology_before_acceptance(self):
        def callback(stage,snapshot,data,cwd):
            if stage=='route' and snapshot['action']=='design-topology':
                registry=copy.deepcopy(snapshot['topology']);registry['entry_target']='module.unknown'
                design=typed('concorde-topology-design',{'summary':'Invalid entry target.',
                    'registry':registry,'spec_tasks':[{'target_id':'module.ledger','task':'Retain the Module Spec.'}],
                    'migration_constraints':[],'acceptance':['The invalid entry would be selected.']})
                data.update(outcome='topology_proposed',answer='Designed.',expand_targets=[],routes=[],gaps=[],topology_design=design)
        double=ModelProcessDouble(callback)
        result=self.call_capability('concorde-main',{'action':'design-topology','task':'Select a Module entry'},double)
        self.assertEqual('blocked',result['status'],result);self.assertEqual('invalid_proposal',result['errors'][0]['code'])
        self.assertFalse(any(call['stage']=='topology-author' for call in double.calls))
        self.assertEqual([],list((self.root/'.concorde/topology-proposals').glob('*.json')))
    def test_topology_dependency_change_requires_affected_module_task(self):
        def callback(stage,snapshot,data,cwd):
            if stage=='route' and snapshot['action']=='design-topology':
                registry=copy.deepcopy(snapshot['topology'])
                registry['targets'].append({'id':'service.audit-report','kind':'module','title':'Audit reports',
                    'documents':['specs/audit-report/module.md'],'parent':None,'uses':[],
                    'files':[],'checks':[]})
                registry['targets'][1]['uses'].append('service.audit-report')
                design=typed('concorde-topology-design',{'summary':'Add audit reports without its Domain view.',
                    'registry':registry,'spec_tasks':[{'target_id':'service.audit-report','task':'Define audit reports.'}],
                    'migration_constraints':[],'acceptance':['The Service is registered.']})
                data.update(outcome='topology_proposed',answer='Designed.',expand_targets=[],routes=[],gaps=[],topology_design=design)
        result=self.call_capability('concorde-main',{'action':'design-topology','task':'Add audit reports'},ModelProcessDouble(callback))
        self.assertEqual('blocked',result['status'],result)
        self.assertEqual('invalid_proposal',result['errors'][0]['code'])
        self.assertIn('Module tasks',result['errors'][0]['message'])
    @verifies("scenario.development.answer-question")
    def test_main_can_admit_modules_and_answer_but_not_read_implementation_code(self):
        double=ModelProcessDouble()
        result=self.call_capability('concorde-main',{'task':'Explain ledger reads',
            'target_id':'module.ledger','focus_id':'scenario.ledger.read'},double)
        self.assertEqual('succeeded',result['status'],result)
        self.assertEqual(['route','route'],[call['stage'] for call in double.calls])
        snapshot=double.calls[-1]['snapshot']
        self.assertEqual('scenario.ledger.read',snapshot['focus_hint'])
        self.assertIn('# Ledger API',json.dumps(snapshot))
        self.assertNotIn('LEDGER_IMPLEMENTATION_CODE',json.dumps(snapshot))
        self.assertTrue(all(item['kind']=='module' for call in double.calls
                            for item in call['snapshot']['targets']))
        with self.assertRaises(SpecError):
            resolve_discovery_context(SpecRepository(self.root),('entity.ledger.store',),
                capability='concorde-main',phase='route',task='Read one entity')

    @verifies("scenario.development.answer-question")
    def test_main_combines_original_sources_from_multiple_target_contexts(self):
        def answer(stage,snapshot,data,cwd):
            discovered={item['target_id'] for item in snapshot['targets']}
            needed=['service.transfer','module.ledger']
            missing=[target for target in needed if target not in discovered]
            if missing:
                data.update(outcome='expand',expand_targets=missing,routes=[])
            else:
                sources={item['path']:item['content'] for item in snapshot['documents']}
                self.assertIn('# Ledger API',sources['specs/ledger/module.md'])
                self.assertEqual((self.root/'specs/transfer/promises.md').read_text(),
                                 sources['specs/transfer/promises.md'])
                data.update(outcome='completed',answer='Transfer and ledger explained from their original Specs.',
                            expand_targets=[],routes=[])
        double=ModelProcessDouble(answer)
        result=self.call_capability('concorde-main',{'task':'Explain transfer and ledger'},double)
        self.assertEqual('succeeded',result['status'],result)
        self.assertEqual(2,len(double.calls))
        self.assertTrue(all(call['capability']=='concorde-coordinator' for call in double.calls))
        self.assertEqual(['scope.bank','service.transfer','module.ledger'],
                         result['output']['data']['discovered_targets'])
        self.assertEqual('Transfer and ledger explained from their original Specs.',
                         result['output']['data']['answer'])

    @verifies("scenario.development.answer-gap")
    def test_main_reports_gaps_with_owning_module_and_complete_context_identity(self):
        def routing_gap(stage,snapshot,data,cwd):
            data.update(outcome='spec_incomplete',answer='Routing facts are missing.',
                expand_targets=[],routes=[],gaps=[{'question':'Which target owns settlement?',
                'blocked_step':'Select a context','needed_contract':'Settlement routing responsibility',
                'target_id':'scope.bank'}])
        blocked=self.call_capability('concorde-main',{'task':'Explain settlement'},ModelProcessDouble(routing_gap))
        self.assertEqual('blocked',blocked['status'])
        gap=blocked['output']['data']['gaps'][0]
        self.assertEqual('scope.bank',gap['target_id'])
        self.assertEqual(blocked['output']['data']['context_id'],gap['context_id'])
        def contract_gap(stage,snapshot,data,cwd):
            if 'module.ledger' not in [item['target_id'] for item in snapshot['targets']]:
                data.update(outcome='expand',expand_targets=['module.ledger'],routes=[])
            else:
                data.update(outcome='spec_incomplete',answer='Ledger settlement is unspecified.',
                    expand_targets=[],routes=[],gaps=[{'question':'When is settlement final?',
                    'blocked_step':'Explain settlement ledger','needed_contract':'Settlement completion rule',
                    'target_id':'module.ledger'}])
        result=self.call_capability('concorde-main',{'task':'Explain settlement ledger'},ModelProcessDouble(contract_gap))
        self.assertEqual('blocked',result['status'],result)
        gap=result['output']['data']['gaps'][0]
        self.assertEqual('module.ledger',gap['target_id'])
        self.assertEqual(result['output']['data']['context_id'],gap['context_id'])

    @verifies("scenario.development.answer-question")
    def test_main_questions_reject_worker_routes(self):
        def route(stage,snapshot,data,cwd):
            data.update(outcome='routed',expand_targets=[],routes=[{
                'target_id':'module.ledger','focus_id':None,'task':snapshot['task'],'constraints':[]}])
        result=self.call_capability('concorde-main',{'task':'Explain ledger'},ModelProcessDouble(route))
        self.assertEqual('blocked',result['status'])
        self.assertEqual('invalid_completion',result['errors'][0]['code'])

    def test_global_loop_routes_once_before_its_first_internal_stage(self):
        double=ModelProcessDouble()
        result=self.call_capability('concorde-dev-loop',{'task':'Plan the transfer promise','specify':False,'run_reviews':False},double)
        self.assertEqual('succeeded',result['status'],result)
        self.assertEqual('service.transfer',result['output']['data']['target_id'])
        self.assertEqual('concorde-coordinator-route',result['output']['data']['completed_capabilities'][0])
        self.assertEqual(['route','route','context-solve'],[call['stage'] for call in double.calls][:3])
        self.assertEqual(['concorde-coordinator','concorde-coordinator','concorde-spec-engineer'],
                         [call['capability'] for call in double.calls][:3])
    @verifies("scenario.harness.typed-reject")
    def test_internal_stage_capability_requires_target_id_at_the_top_level(self):
        with self.assertRaises(TypedDataError) as caught:
            typed('concorde-plan-request',{'task':'Plan the transfer promise'})
        self.assertEqual('invalid_field',caught.exception.code)
        self.assertIn('target_id',caught.exception.field)
    def test_non_ask_main_route_cannot_split_or_rewrite_user_intent(self):
        def split(stage,snapshot,data,cwd):
            if stage=='route':data.update(outcome='routed',expand_targets=[],gaps=[],routes=[
                {'target_id':'service.transfer','focus_id':None,'task':snapshot['task'],'constraints':snapshot['constraints']},
                {'target_id':'module.ledger','focus_id':None,'task':snapshot['task'],'constraints':snapshot['constraints']}])
        result=self.call_capability('concorde-dev-loop',{'task':'Plan transfer','specify':False,'run_reviews':False},ModelProcessDouble(split))
        self.assertEqual('blocked',result['status']);self.assertEqual('ambiguous_route',result['errors'][0]['code'])
        def rewrite(stage,snapshot,data,cwd):
            if stage=='route':data.update(outcome='routed',expand_targets=[],gaps=[],routes=[
                {'target_id':'service.transfer','focus_id':None,'task':'Different intent','constraints':[]}])
        result=self.call_capability('concorde-dev-loop',{'task':'Plan transfer','constraints':['Keep API stable'],'specify':False,'run_reviews':False},ModelProcessDouble(rewrite))
        self.assertEqual('blocked',result['status']);self.assertEqual('incompatible_handoff',result['errors'][0]['code'])
    def test_main_cannot_guess_an_unmentioned_discovery_or_route_target(self):
        path=self.root/'specs/bank/module.md';declaration=path.read_text().split('# Banking',1)[0]
        path.write_text(declaration+'# Banking\nNo downstream target is identified.\n')
        def expand(stage,snapshot,data,cwd):
            if stage=='route':data.update(outcome='expand',expand_targets=['service.transfer'],routes=[],gaps=[])
        result=self.call_capability('concorde-main',{'task':'Explain transfer'},ModelProcessDouble(expand))
        self.assertEqual('blocked',result['status']);self.assertEqual('incompatible_handoff',result['errors'][0]['code'])
        def route(stage,snapshot,data,cwd):
            if stage=='route':data.update(outcome='expand',expand_targets=['module.ledger'],gaps=[],routes=[])
        result=self.call_capability('concorde-main',{'task':'Explain ledger'},ModelProcessDouble(route))
        self.assertEqual('blocked',result['status']);self.assertEqual('incompatible_handoff',result['errors'][0]['code'])
    @verifies("scenario.harness.context-discovery", "scenario.harness.context-stale-recheck")
    def test_discovery_context_is_digest_bound_and_module_only(self):
        repo=SpecRepository(self.root)
        first=resolve_discovery_context(repo,('scope.bank',),capability='concorde-main',phase='route',task='Route transfer')
        second=resolve_discovery_context(repo,('scope.bank','service.transfer'),capability='concorde-main',phase='route',task='Route transfer')
        self.assertNotEqual(first.id,second.id)
        self.assertEqual(['scope.bank','service.transfer'],[item['target_id'] for item in second.value['targets']])
        third=resolve_discovery_context(repo,('scope.bank','module.ledger'),capability='concorde-main',phase='route',task='Route ledger')
        self.assertIn('# Ledger API',third.serialized)
        self.assertNotIn('LEDGER_IMPLEMENTATION_CODE',third.serialized)
        with self.assertRaises(SpecError):
            resolve_discovery_context(repo,('entity.ledger.store',),capability='concorde-main',phase='route',task='Read one entity')
        path=self.root/'specs/transfer/module.md';declaration=path.read_text().split('# Transfer money',1)[0]
        path.write_text(declaration+'# Changed service routing facts\n')
        with self.assertRaisesRegex(SpecError,'changed'):recheck_discovery_context(repo,second)
    @verifies("scenario.harness.context-discovery", "scenario.harness.context-freeze")
    def test_main_reads_complete_admitted_modules_without_implicit_peer_expansion(self):
        path='specs/transfer/promises.md'
        self.registry['targets'][3]['documents'].append(path)
        (self.root/'.concorde/specs.json').write_text(json.dumps(self.registry))
        update_document_declaration(self.root,path,targets=['service.transfer','module.ledger'],main_visible=False)
        visible=resolve_discovery_context(SpecRepository(self.root),('scope.bank','service.transfer'),
            capability='concorde-main',phase='route',task='Route transfer').value
        transfer=visible['targets'][1]
        self.assertEqual([path],[item['path'] for item in transfer['shared_specs']])
        self.assertIn('specs/transfer/module.md',transfer['document_order'])
        self.assertNotIn('# Ledger API',json.dumps(transfer))
        self.assertNotIn('TRANSFER_IMPLEMENTATION_CODE',json.dumps(visible))
        worker=resolve_context(SpecRepository(self.root),'service.transfer').value
        self.assertEqual(worker['document_order'],transfer['document_order'])
    @verifies("scenario.harness.context-discovery")
    def test_global_context_deduplicates_complete_sources_and_preserves_each_membership(self):
        shared='specs/transfer/promises.md'
        self.registry['targets'][3]['documents'].append(shared)
        (self.root/'.concorde/specs.json').write_text(json.dumps(self.registry))
        update_document_declaration(self.root,shared,
            targets=['service.transfer','module.ledger'],main_visible=False)
        snapshot=resolve_discovery_context(SpecRepository(self.root),
            ('scope.bank','service.transfer','module.ledger'),
            capability='concorde-main',phase='route',action='ask',task='Compare contracts')
        typed('concorde-discovery-context',snapshot.value)
        value=snapshot.value
        paths=[document['path'] for document in value['documents']]
        self.assertEqual(sorted(set(paths)),paths)
        self.assertEqual(1,paths.count(shared))
        for document in value['documents']:
            self.assertEqual((self.root/document['path']).read_text(),document['content'])
        modules={target['target_id']:target for target in value['targets']}
        for target_id in ('service.transfer','module.ledger'):
            refs=modules[target_id]['shared_specs']
            self.assertEqual([shared],[document['path'] for document in refs])
            self.assertFalse(refs[0]['main_visible'])
            self.assertNotIn('content',refs[0])
        self.assertNotIn('specs/audit/module.md',paths)
        self.assertNotIn('PRIVATE_CODE',snapshot.serialized)

    @verifies("scenario.harness.context-stale-recheck")
    def test_global_context_rechecks_registered_document_bytes_and_membership(self):
        repository=SpecRepository(self.root)
        snapshot=resolve_discovery_context(repository,('scope.bank',),
            capability='concorde-main',phase='route',task='Explain architecture')
        path=self.root/'specs/bank/module.md'
        original=path.read_bytes()
        path.write_bytes(original+b'\nAn added architectural fact.\n')
        with self.assertRaisesRegex(SpecError,'changed'):
            recheck_discovery_context(repository,snapshot)
        path.write_bytes(original)
        self.registry['targets'][0]['documents'].append('specs/transfer/promises.md')
        (self.root/'.concorde/specs.json').write_text(json.dumps(self.registry))
        update_document_declaration(self.root,'specs/transfer/promises.md',
                                    targets=['service.transfer','scope.bank'])
        with self.assertRaisesRegex(SpecError,'changed'):
            recheck_discovery_context(repository,snapshot)

    def test_global_context_rejects_unavailable_required_source(self):
        (self.root/'specs/bank/module.md').unlink()
        with self.assertRaises(SpecError):
            resolve_discovery_context(SpecRepository(self.root),('scope.bank',),
                capability='concorde-main',phase='route',task='Explain architecture')

    @verifies("scenario.development.answer-question")
    def test_main_can_answer_from_initial_spec_context_in_one_invocation(self):
        def answer(stage,snapshot,data,cwd):
            self.assertIn('# Banking',snapshot['documents'][0]['content'])
            data.update(outcome='completed',answer='Banking coordinates transfer, ledger and audit.',
                        expand_targets=[],routes=[])
        double=ModelProcessDouble(answer)
        result=self.call_capability('concorde-main',{'task':'What does Banking coordinate?'},double)
        self.assertEqual('succeeded',result['status'],result)
        self.assertEqual(1,len(double.calls))
        self.assertEqual(['scope.bank'],result['output']['data']['discovered_targets'])

    @verifies("scenario.harness.context-stale-recheck")
    def test_membership_changes_invalidate_snapshot(self):
        repo=SpecRepository(self.root); snapshot=resolve_context(repo,'service.transfer')
        self.registry['targets'][2]['documents'].reverse()
        (self.root/'.concorde/specs.json').write_text(json.dumps(self.registry))
        with self.assertRaisesRegex(SpecError,'membership'): recheck_context(repo,snapshot)
    @verifies("scenario.harness.context-stale-recheck")
    def test_another_targets_new_reference_reclassifies_and_invalidates_context(self):
        repo=SpecRepository(self.root);snapshot=resolve_context(repo,'service.transfer')
        self.registry['targets'][3]['documents'].append('specs/transfer/promises.md')
        (self.root/'.concorde/specs.json').write_text(json.dumps(self.registry))
        update_document_declaration(self.root,'specs/transfer/promises.md',
                                    targets=['service.transfer','module.ledger'])
        with self.assertRaisesRegex(SpecError,'classification'):recheck_context(repo,snapshot)
    def test_module_parent_cycle_rejected(self):
        self.registry['targets'][0]['parent']='scope.audit'
        self.registry['targets'][1]['parent']='scope.bank'
        (self.root/'.concorde/specs.json').write_text(json.dumps(self.registry))
        with self.assertRaisesRegex(SpecError,'cycle'): SpecRepository(self.root)
    def test_spec_symlink_rejected(self):
        (self.root/'specs/transfer/module.md').unlink()
        (self.root/'specs/transfer/module.md').symlink_to(self.root/'secret.py')
        with self.assertRaises(ValueError): resolve_context(SpecRepository(self.root),'service.transfer')
    def test_gap_is_recorded_without_creating_a_target_plan(self):
        def gap(stage,snapshot,data,cwd):
            if stage=='context-solve':
                data.update(outcome='spec_incomplete',gaps=[{'question':'Who owns the daily limit?',
                    'blocked_step':'Decide transfer admission','needed_contract':'Daily limit ownership'}])
        double=ModelProcessDouble(gap)
        result=self.call_capability('concorde-plan',{'target_id':'service.transfer','task':'Add a daily limit'},double)
        self.assertEqual('blocked',result['status'],result)
        self.assertEqual('spec_incomplete',result['output']['data']['outcome'])
        self.assertEqual(['context-solve'],[call['stage'] for call in double.calls])
        self.assertFalse((self.root/'.concorde/attempts').exists())
        state=json.loads((self.root/'.concorde/worktree.json').read_text())
        self.assertEqual('blocked',state['status']);self.assertEqual({},state['targets'])
    @verifies("scenario.development.dev-loop-ready", "scenario.harness.context-freeze")
    def test_standard_loop_real_checks_leave_a_ready_change(self):
        double=ModelProcessDouble()
        result=self.call_capability('concorde-dev-loop',{'task':'Implement the transfer contract'},double)
        self.assertEqual('succeeded',result['status'],result)
        self.assertEqual('ready',result['output']['data']['outcome'])
        self.assertEqual('passed',result['output']['data']['checks'][0]['status'])
        self.assertFalse((self.root/'.concorde/attempts').exists())
        state=json.loads((self.root/'.concorde/worktree.json').read_text())
        self.assertEqual('ready',state['status'])
        self.assertEqual(['route','route','specify','spec-review','context-solve','plan','tasks','implementation','code-review'],[c['stage'] for c in double.calls])
        for call in double.calls:
            if call['stage'] not in {'implementation','code-review'}:
                self.assertNotEqual(self.root,call['cwd'])
                self.assertNotIn('PRIVATE_CODE',call['prompt'])
                self.assertNotIn('TRANSFER_IMPLEMENTATION_CODE',call['prompt'])
            if call['stage'] in {'plan','tasks'}:
                self.assertEqual(['app/transfer.py','checks/transfer_check.py'],
                                 [item['path'] for item in call['snapshot']['implementation_files']])
                self.assertEqual([],call['snapshot']['implementation_artifacts'])
        self.assertTrue(all(d['write_paths']==[] for d in self.host.descriptions if d['phase']!='implementation'))
    @verifies("scenario.development.validate-blocked")
    def test_failed_behavioral_check_prevents_delivery(self):
        def broken(stage,snapshot,data,cwd):
            if stage=='implementation': (cwd/'app/transfer.py').write_text('def transfer(balance,amount):\n    return 0\n')
        result=self.call_capability('concorde-dev-loop',{'target_id':'service.transfer','task':'Implement transfer'},ModelProcessDouble(broken))
        self.assertEqual('failed',result['status'],result)
        self.assertEqual('failed',result['output']['data']['checks'][0]['status'])
        state=json.loads((self.root/'.concorde/worktree.json').read_text())
        self.assertEqual('failed',state['status'])
    def test_wrong_context_result_rejected(self):
        def wrong(stage,snapshot,data,cwd): data['context_id']='sha256:'+'0'*64
        result=self.call_capability('concorde-main',{'target_id':'service.transfer','task':'Explain transfer'},ModelProcessDouble(wrong))
        self.assertEqual('blocked',result['status'],result)
        self.assertEqual('incompatible_handoff',result['errors'][0]['code'])

if __name__=='__main__': unittest.main()
