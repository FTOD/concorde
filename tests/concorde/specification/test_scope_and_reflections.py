import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from concorde.host.capability_service import CapabilityHost,run_capability
from concorde.host.typed_data import typed
from concorde.reflections.scoped_triage import queue_module
from concorde.specification.validation import validate_repository
from .support import PACKAGE,CONFIGURATION,project,ModelProcessDouble

class ScopeReflectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);project(self.root)
    def run_op(self,op,data,callback=None):
        self.double=ModelProcessDouble(callback);self.host=CapabilityHost(self.root,PACKAGE,executor=self.double.executor,allow_primary_worktree=True)
        return run_capability(op,CONFIGURATION,typed(op+'-request',data),host_context=self.host)
    def test_domain_coordinates_separate_component_contexts(self):
        result=self.run_op('concorde-dev-loop',{'target_id':'scope.bank','task':'Implement the banking transfer promise'})
        self.assertEqual('succeeded',result['status'],result)
        task_call=next(call for call in self.double.calls if call['stage']=='tasks')
        self.assertIn('"target_id": "service.transfer"',
                      '\n'.join(item['content'] for section in ('target_spec','shared_specs')
                                for item in task_call['snapshot'][section]))
        domain=[c for c in self.double.calls if c['capability']!='concorde-coordinator' and c['snapshot']['target_id']=='scope.bank']
        self.assertTrue(domain);self.assertTrue(any(c['capability']!='concorde-coordinator' and
            c['snapshot']['target_id']=='service.transfer' for c in self.double.calls))
        self.assertFalse(any(c['stage']=='implementation' for c in domain))
        self.assertTrue(all('specs/transfer/module.md' not in json.dumps(c['snapshot']) for c in domain))
    def test_domain_rejects_component_outside_its_scope(self):
        registry=json.loads((self.root/'.concorde/specs.json').read_text());registry['targets'][0]['uses']=['scope.audit'];(self.root/'.concorde/specs.json').write_text(json.dumps(registry))
        def cb(stage,snap,data,cwd):
            if stage=='tasks':data['tasks'][0]['target_id']='service.transfer'
        result=self.run_op('concorde-dev-loop',{'target_id':'scope.bank','task':'Implement transfer'},cb)
        self.assertNotEqual('succeeded',result['status']);self.assertFalse(any(c['stage']=='implementation' for c in self.double.calls))
    def test_domain_retains_component_gap_and_stops_before_code(self):
        def cb(stage,snapshot,data,cwd):
            if stage=='tasks' and snapshot['target_id']=='scope.bank':data['tasks'][0]['target_id']='service.transfer'
            if stage=='specify' and snapshot['target_id']=='service.transfer':
                data.update(outcome='spec_incomplete',gaps=[{'question':'Which retry key identifies a transfer?','blocked_step':'Specify retries','needed_contract':'Idempotency ownership'}])
        result=self.run_op('concorde-dev-loop',{'target_id':'scope.bank','task':'Implement transfer retries'},cb)
        self.assertEqual('blocked',result['status'],result)
        gap=result['output']['data']['gaps'][0]
        self.assertEqual('service.transfer',gap['target_id']);self.assertTrue(gap['context_id'].startswith('sha256:'))
        self.assertFalse(any(c['stage']=='implementation' for c in self.double.calls))
    def record(self):
        root=self.root
        index=root/'.concorde/reflections/index.json';index.write_text(json.dumps({'schema_version':1,'high_water':'R-001'}))
        p=root/'.concorde/reflections/pending/R-001.md';p.parent.mkdir(parents=True)
        p.write_text('''---
id: R-001
title: Transfer promise is not implemented
phase: implement
date: 2026-09-05
feature: feature.transfer
kind: implementation
concerns: app/transfer.py
status: open
---

# R-001 · Transfer promise is not implemented

## Context

A consumer calls transfer.

## Expected

Valid amounts are subtracted and invalid amounts rejected.

## Observed

Balance is returned unchanged.

## Impact

The API promise fails.

## Evidence

PRIVATE_REFLECTION_DETAIL_FOR_IMPLEMENTATION

## Triage Analysis

## Proposed Resolution

## Intervention Rationale

## User Comments

Keep this user comment intact.

## Occurrences

- 2026-09-05: observed the incorrect balance.
''')
        subprocess.run(['git','init','-q'],cwd=root,check=True)
        subprocess.run(['git','add','.'],cwd=root,check=True)
        subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','fixture'],cwd=root,check=True)
    def finding(self,stage,snap,data,cwd):
        if stage!='implementation' or snap['stage_inputs'][0]['type_id']!='concorde-reflection-selection':return
        data['reflection_findings']=[{'reflection_id':'R-001','verified_commit':snap['stage_inputs'][0]['data']['head'],
          'observed_state':'reproduced','verification':'Current transfer returns the input balance.','analysis':'The promised arithmetic is absent.',
          'resolution':'Fulfil the specified pure transfer behavior.','intervention_rationale':'The local contract defines the outcome.',
          'human_intervention':'not-required','route':'fast-loop','effort':'small','files':['app/transfer.py'],
          'steps':'Subtract accepted amounts and reject invalid values.','validation':'Run the configured transfer check.',
          'risks':'No persistent side effects.','protocol_change':False}]
    def task(self,action):return {'target_id':'service.transfer','task':'Investigate the transfer promise','action':action,'reflection_ids':['R-001']}
    def test_status_exposes_metadata_without_record_body_or_code(self):
        self.record();result=self.run_op('concorde-reflections-triage',self.task('status'))
        self.assertEqual('succeeded',result['status'],result);self.assertEqual([],self.double.calls)
        self.assertEqual('R-001',result['output']['data']['reflections'][0]['id']);self.assertNotIn('PRIVATE_REFLECTION',json.dumps(result))
    def test_candidate_overlay_validates_reflections_against_candidate_ids(self):
        self.record();registry=json.loads((self.root/'.concorde/specs.json').read_text())
        registry['targets'][2]['features']=[]
        report=validate_repository(self.root,package_root=PACKAGE,registry_bytes=json.dumps(registry).encode())
        self.assertEqual('invalid',report.status)
        self.assertIn('CONCORDE-REFLECT-004',{finding.rule_id for finding in report.findings})
    def test_investigation_is_readonly_and_preserves_user_report(self):
        self.record();before=(self.root/'app/transfer.py').read_bytes()
        result=self.run_op('concorde-reflections-triage',self.task('investigate'),self.finding)
        self.assertEqual('succeeded',result['status'],result);self.assertEqual(before,(self.root/'app/transfer.py').read_bytes())
        snapshot=next(call['snapshot'] for call in self.double.calls if call['stage']=='implementation')
        self.assertEqual([],snapshot['implementation_specs'])
        self.assertNotIn('INTERNAL_TRANSFER_IMPLEMENTATION_SPEC',json.dumps(snapshot))
        self.assertFalse(any('specs/implementations/' in path for description in self.host.descriptions for path in description['read_paths']))
        self.assertEqual([[]],[d['write_paths'] for d in self.host.descriptions]);text=(self.root/'.concorde/reflections/planned/R-001.md').read_text()
        self.assertIn('Keep this user comment intact.',text);self.assertIn('PRIVATE_REFLECTION_DETAIL_FOR_IMPLEMENTATION',text)
    def test_investigation_rejects_wrong_head(self):
        self.record()
        def cb(*args):self.finding(*args);args[2]['reflection_findings'][0]['verified_commit']='0'*40
        result=self.run_op('concorde-reflections-triage',self.task('investigate'),cb)
        self.assertNotEqual('succeeded',result['status']);self.assertTrue((self.root/'.concorde/reflections/pending/R-001.md').exists())
    def test_rejected_investigation_preserves_its_gap_until_host_acceptance(self):
        self.record()
        def missing(stage,snap,data,cwd):
            if stage=='implementation':
                data.update(outcome='spec_incomplete',gaps=[{'question':'Who owns admission?',
                    'blocked_step':'Investigate transfer admission','needed_contract':'Admission ownership'}])
        task=self.task('investigate')
        self.assertEqual('blocked',self.run_op('concorde-reflections-triage',task,missing)['status'])
        path=self.root/'specs/transfer/module.md';path.write_text(path.read_text()+'\nTransfer owns admission.\n')
        def invalid(*args):self.finding(*args);args[2]['reflection_findings'][0]['verified_commit']='0'*40
        result=self.run_op('concorde-reflections-triage',task,invalid)
        self.assertNotEqual('succeeded',result['status'],result)
        state=json.loads((self.root/'.concorde/worktree.json').read_text())
        self.assertEqual('open',state['gap_history'][0]['status']);self.assertTrue(state['gaps'])
        self.assertEqual('succeeded',self.run_op('concorde-reflections-triage',task,self.finding)['status'])
        self.assertEqual('resolved',json.loads((self.root/'.concorde/worktree.json').read_text())['gap_history'][0]['status'])
    def test_reflection_implementation_restarts_spec_cognition_and_marks_plan(self):
        self.record();result=self.run_op('concorde-reflections-triage',self.task('implement'),self.finding)
        self.assertEqual('succeeded',result['status'],result)
        self.assertEqual('ready',json.loads((self.root/'.concorde/worktree.json').read_text())['status'])
        for call in self.double.calls:
            if call['stage']!='implementation':self.assertNotIn('PRIVATE_REFLECTION',call['prompt']);self.assertNotIn('Current transfer returns',call['prompt'])
        queue=queue_module(PACKAGE);plans=queue._load_plans(self.root,queue.load_config(self.root))
        self.assertEqual('implemented',plans['R-001']['status'])
