import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from concorde.capabilities.operation_service import OperationHost,run_operation
from concorde.capabilities.operation_data import typed
from concorde.reflections.scoped_triage import queue_module
from .support import PACKAGE,CONFIGURATION,project,ModelProcessDouble

class ScopeReflectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);project(self.root)
    def run_op(self,op,data,callback=None):
        self.double=ModelProcessDouble(callback);self.host=OperationHost(self.root,PACKAGE,executor=self.double.executor,allow_primary_worktree=True)
        return run_operation(op,CONFIGURATION,typed(op+'-request',data),host_context=self.host)
    def test_domain_coordinates_separate_component_contexts(self):
        def cb(stage,snapshot,data,cwd):
            if stage=='tasks' and snapshot['kind']=='domain':
                data['tasks'][0]['target_id']='service.transfer'
        result=self.run_op('concorde-standard-dev-loop',{'target_id':'scope.bank','task':'Implement the banking transfer promise'},cb)
        self.assertEqual('succeeded',result['status'],result)
        domain=[c for c in self.double.calls if c['snapshot']['kind']=='domain']
        self.assertTrue(domain);self.assertTrue(any(c['snapshot']['target_id']=='service.transfer' for c in self.double.calls))
        self.assertFalse(any(c['stage']=='implementation' for c in domain))
        self.assertTrue(all('specs/send-money.md' not in json.dumps(c['snapshot']) for c in domain))
    def test_domain_rejects_component_outside_its_scope(self):
        registry=json.loads((self.root/'.concorde/specs.json').read_text());registry['targets'][2]['participates_in']=['scope.audit'];(self.root/'.concorde/specs.json').write_text(json.dumps(registry))
        def cb(stage,snap,data,cwd):
            if stage=='tasks':data['tasks'][0]['target_id']='service.transfer'
        result=self.run_op('concorde-standard-dev-loop',{'target_id':'scope.bank','task':'Implement transfer'},cb)
        self.assertNotEqual('succeeded',result['status']);self.assertFalse(any(c['stage']=='implementation' for c in self.double.calls))
    def test_domain_retains_component_gap_and_stops_before_code(self):
        def cb(stage,snapshot,data,cwd):
            if stage=='tasks' and snapshot['kind']=='domain':data['tasks'][0]['target_id']='service.transfer'
            if stage=='specify' and snapshot['target_id']=='service.transfer':
                data.update(outcome='spec_incomplete',gaps=[{'question':'Which retry key identifies a transfer?','blocked_step':'Specify retries','needed_contract':'Idempotency ownership'}])
        result=self.run_op('concorde-standard-dev-loop',{'target_id':'scope.bank','task':'Implement transfer retries'},cb)
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
triage: pending
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
    def test_investigation_is_readonly_and_preserves_user_report(self):
        self.record();before=(self.root/'app/transfer.py').read_bytes()
        result=self.run_op('concorde-reflections-triage',self.task('investigate'),self.finding)
        self.assertEqual('succeeded',result['status'],result);self.assertEqual(before,(self.root/'app/transfer.py').read_bytes())
        self.assertEqual([[]],[d['write_paths'] for d in self.host.descriptions]);text=(self.root/'.concorde/reflections/planned/R-001.md').read_text()
        self.assertIn('Keep this user comment intact.',text);self.assertIn('PRIVATE_REFLECTION_DETAIL_FOR_IMPLEMENTATION',text)
    def test_investigation_rejects_wrong_head(self):
        self.record()
        def cb(*args):self.finding(*args);args[2]['reflection_findings'][0]['verified_commit']='0'*40
        result=self.run_op('concorde-reflections-triage',self.task('investigate'),cb)
        self.assertNotEqual('succeeded',result['status']);self.assertTrue((self.root/'.concorde/reflections/pending/R-001.md').exists())
    def test_reflection_implementation_restarts_spec_cognition_and_marks_plan(self):
        self.record();result=self.run_op('concorde-reflections-triage',self.task('implement'),self.finding)
        self.assertEqual('succeeded',result['status'],result)
        for call in self.double.calls:
            if call['stage']!='implementation':self.assertNotIn('PRIVATE_REFLECTION',call['prompt']);self.assertNotIn('Current transfer returns',call['prompt'])
        queue=queue_module(PACKAGE);plans=queue._load_plans(self.root,queue.load_config(self.root))
        self.assertEqual('implemented',plans['R-001']['status'])
