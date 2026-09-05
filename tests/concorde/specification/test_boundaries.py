"""Behavioral regression gates replacing Profile 7 ambient/ancestor context contracts."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from concorde.capabilities.operation_data import typed,validate_typed,OperationDataError
from concorde.capabilities.operation_service import OperationHost,run_operation
from concorde.specification.repository import SpecRepository,SpecError
from concorde.specification.context import resolve_context,recheck_context
from concorde.specification.changes import file_change,apply_files
from concorde.specification.initialize import migration_proposal,apply_project_proposal
from concorde.specification.schema import admit,ContractError
from .support import project,PACKAGE,CONFIGURATION,ModelProcessDouble

class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.registry=project(self.root);self.task={'target_id':'service.transfer','task':'Implement the specified transfer'}
    def save(self): (self.root/'.concorde/specs.json').write_text(json.dumps(self.registry))
    def run_op(self,name,data=None,callback=None,mode='execute'):
        double=ModelProcessDouble(callback);self.double=double
        self.host=OperationHost(self.root,PACKAGE,executor=double.executor,allow_primary_worktree=True,mode=mode)
        return run_operation(name,CONFIGURATION,typed(name+'-request',data or self.task),host_context=self.host)
    def attempt(self):
        result=self.run_op('concorde-plan');self.assertEqual('succeeded',result['status'],result)
        return {**self.task,'change_id':result['output']['data']['change_id']}
    def test_shared_physical_markdown_requires_explicit_membership(self):
        self.registry['targets'][3]['documents'].append('specs/transfer-promises.md');self.save()
        snap=resolve_context(SpecRepository(self.root),'module.ledger').value
        self.assertEqual(2,len(snap['documents']))
        self.assertNotIn('specs/send-money.md',json.dumps(snap))
    def test_overlapping_code_ownership_rejected(self):
        self.registry['targets'][3]['implementation']=['app'];self.save()
        with self.assertRaises(SpecError):SpecRepository(self.root)
    def test_control_files_cannot_be_implementation_grants(self):
        self.registry['targets'][2]['implementation']=['.concorde'];self.save()
        with self.assertRaises(SpecError):SpecRepository(self.root)
    def test_target_and_focus_share_global_identity_namespace(self):
        self.registry['targets'][2]['features'][0]['id']='module.ledger';self.save()
        with self.assertRaises(SpecError):SpecRepository(self.root)
    def test_code_is_digest_only_and_only_in_implementation_snapshot(self):
        repo=SpecRepository(self.root)
        plain=resolve_context(repo,'service.transfer').value;impl=resolve_context(repo,'service.transfer',phase='implementation').value
        self.assertEqual([],plain['implementation_artifacts']);self.assertTrue(impl['implementation_artifacts'])
        self.assertNotIn('def transfer',json.dumps(impl))
    def test_unknown_stage_input_cannot_be_a_hidden_read_channel(self):
        with self.assertRaises(ValueError):resolve_context(SpecRepository(self.root),'service.transfer',stage_inputs=({'type_id':'opaque','schema_version':1,'data':{'code':'secret'}},))
    def test_protocol_tampering_invalidates_binding(self):
        package=self.root/'package';shutil.copytree(PACKAGE/'protocol',package/'protocol')
        (package/'protocol/kinds/service.md').write_text('changed')
        with self.assertRaises(SpecError):SpecRepository(self.root,package)
    def test_configuration_cannot_replace_initialized_authority(self):
        other=typed('concorde-operation-configuration',{'integration':'codex','enforcement':'native'})
        result=run_operation('concorde-ask',other,typed('concorde-ask-request',self.task),host_context=OperationHost(self.root,PACKAGE))
        self.assertEqual('configuration_mismatch',result['errors'][0]['code'])
    def test_wrong_version_and_extra_fields_are_rejected(self):
        for value in [dict(typed('concorde-ask-request',self.task),schema_version=True),dict(typed('concorde-ask-request',self.task),schema_version=7),{'type_id':'concorde-ask-request','schema_version':1,'data':{**self.task,'read_paths':['secret.py']}}]:
            with self.subTest(value=value),self.assertRaises(OperationDataError):validate_typed(value,'concorde-ask-request')
    def test_unsupported_is_not_spec_incomplete(self):
        def cb(stage,snapshot,data,cwd):data.update(outcome='unsupported',answer='The Spec prohibits this use.')
        result=self.run_op('concorde-plan',callback=cb)
        self.assertEqual('unsupported',result['output']['data']['outcome']);self.assertEqual([],result['output']['data']['gaps']);self.assertFalse((self.root/'.concorde/attempts').exists())
    def test_describe_policy_launches_no_model_and_lists_exact_capsule(self):
        result=self.run_op('concorde-standard-dev-loop',mode='describe-policy')
        self.assertEqual('described',result['status']);self.assertEqual([],self.double.calls)
        for policy in self.host.descriptions:
            if policy['phase']!='implementation':self.assertEqual(['context.json'],policy['read_paths']);self.assertEqual([],policy['write_paths'])
    def test_changed_spec_requires_a_new_attempt(self):
        task=self.attempt();p=self.root/'specs/send-money.md';p.write_text(p.read_text()+'\nChanged obligations.\n')
        self.assertEqual('blocked',self.run_op('concorde-tasks',task)['status']);self.assertEqual([],self.double.calls)
    def test_changed_intent_cannot_reuse_attempt(self):
        task=self.attempt();task['task']='Different behavior'
        self.assertEqual('blocked',self.run_op('concorde-tasks',task)['status'])
    def test_spec_author_cannot_edit_provider_or_registry(self):
        def cb(stage,snap,data,cwd):data['documents']=[{'path':'specs/ledger-api.md','content':'Changed'}]
        old=(self.root/'specs/ledger-api.md').read_bytes();result=self.run_op('concorde-specify',callback=cb)
        self.assertEqual('blocked',result['status']);self.assertEqual(old,(self.root/'specs/ledger-api.md').read_bytes())
    def test_planner_cannot_emit_spec_replacements(self):
        def cb(stage,snap,data,cwd):
            if stage=='plan':data['documents']=[{'path':'specs/send-money.md','content':'Changed'}]
        self.assertEqual('blocked',self.run_op('concorde-plan',callback=cb)['status'])
    def test_delivery_requires_real_current_checks(self):
        task=self.attempt();self.run_op('concorde-tasks',task);self.run_op('concorde-implement',task)
        result=self.run_op('concorde-deliver',task);self.assertEqual('blocked',result['status'])
        self.assertEqual('succeeded',self.run_op('concorde-validate',task)['status'])
        (self.root/'checks/transfer_check.py').write_text('raise AssertionError("new expectation")')
        self.assertEqual('blocked',self.run_op('concorde-deliver',task)['status'])
    def test_separate_check_inputs_invalidate_evidence(self):
        check=self.registry['checks'][0];check['inputs']=['acceptance.json'];self.save();(self.root/'acceptance.json').write_text('{}')
        task=self.attempt();self.run_op('concorde-tasks',task);self.run_op('concorde-implement',task);self.run_op('concorde-validate',task)
        (self.root/'acceptance.json').write_text('{"revision":2}')
        self.assertEqual('blocked',self.run_op('concorde-deliver',task)['status'])
    def test_issue_drafts_are_local_exact_authored_tasks(self):
        task=self.attempt();self.run_op('concorde-tasks',task);result=self.run_op('concorde-taskstoissues',task)
        self.assertEqual('succeeded',result['status']);self.assertEqual([],self.double.calls)
        artifact=result['output']['data']['artifacts'][0];issues=json.loads((self.root/artifact['path']).read_text())
        self.assertEqual('task.transfer',issues['issues'][0]['task_id'])
    def test_atomic_replacements_rollback_after_failed_verification(self):
        original=(self.root/'specs/send-money.md').read_bytes()
        changes=[file_change(self.root,'specs/send-money.md','changed'),file_change(self.root,'new.md','new')]
        def reject():raise ValueError('invalid target')
        with self.assertRaises(ValueError):apply_files(self.root,changes,{'specs/send-money.md','new.md'},verify=reject)
        self.assertEqual(original,(self.root/'specs/send-money.md').read_bytes());self.assertFalse((self.root/'new.md').exists())
    def test_stale_file_proposal_never_overwrites_newer_content(self):
        change=file_change(self.root,'specs/send-money.md','proposed');(self.root/'specs/send-money.md').write_text('user change')
        with self.assertRaises(ValueError):apply_files(self.root,[change],{'specs/send-money.md'})
        self.assertEqual('user change',(self.root/'specs/send-money.md').read_text())
    def test_unsupported_and_malformed_contract_schemas_fail_admission(self):
        for schema in [{'type':'object','unevaluatedProperties':False},{'$ref':'https://example.invalid/schema'},{'minLength':True},{'enum':[]},{'minimum':3,'maximum':1}]:
            with self.subTest(schema=schema),self.assertRaises(ContractError):admit(schema)
    def migrate(self):
        config=json.loads((self.root/'.concorde/config.json').read_text());config={'profile_version':7,'specification_root':'specs','root_module_id':'module.old','operation_configuration':config['operation_configuration']}
        (self.root/'.concorde/config.json').write_text(json.dumps(config))
        return migration_proposal(self.root,PACKAGE,self.registry,[])
    def test_explicit_migration_preserves_code_and_record_allocation(self):
        code=(self.root/'secret.py').read_bytes();index=(self.root/'.concorde/reflections/index.json').read_bytes()
        proposal=self.migrate();apply_project_proposal(self.root,PACKAGE,proposal)
        self.assertEqual(code,(self.root/'secret.py').read_bytes());self.assertEqual(index,(self.root/'.concorde/reflections/index.json').read_bytes());SpecRepository(self.root)
    def test_migration_rejects_stale_base(self):
        proposal=self.migrate();p=self.root/'.concorde/config.json';p.write_text(p.read_text()+'\n')
        with self.assertRaises(SpecError):apply_project_proposal(self.root,PACKAGE,proposal)
    def test_migration_rejects_active_attempt(self):
        proposal=self.migrate();p=self.root/'.concorde/attempts/active';p.mkdir(parents=True)
        with self.assertRaises(SpecError):apply_project_proposal(self.root,PACKAGE,proposal)
    def test_profile7_cannot_be_silently_used_by_new_agent_runtime(self):
        self.migrate();result=self.run_op('concorde-ask');self.assertEqual('blocked',result['status']);self.assertEqual([],self.double.calls)
