"""Real host/context admission and recursive control; native decisions are explicit process doubles."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from concorde.host.agent_executor import AgentProcessExecutor
from concorde.host.agent_runtime import (AgentConstraints, AgentDefinition, AgentGrant, AgentLimits,
    AgentRuntime, AgentStep, Harness)
from concorde.host.capability_host import CapabilityHost
from concorde.host.native_agent import NativeAgentAdapter
from concorde.host.typed_data import canonical, decode, typed
from concorde.specification.context import resolve_context
from concorde.specification.repository import SpecRepository, digest
from tests.concorde.specification.support import PACKAGE, ModelProcessDouble, project


class AgentRuntimeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        project(self.root)
        self.spec = self.root / 'spec.md'
        self.spec.write_text('# Test Agent\nAnswer the admitted task; use only typed child feedback.')
        self.admissions = []

    def context(self, definition, input, grant):
        self.admissions.append((definition.id, input, grant))
        snapshot = resolve_context(SpecRepository(self.root, PACKAGE), input['data']['target_id'],
            task=input['data']['task'], instructions=self.spec.read_text())
        return typed('concorde-context-snapshot', snapshot.value)

    def definition(self, id, decide, children=(), targets=('service.transfer',), max_steps=8):
        configuration = canonical({'model_integration': 'test-mixed/v1', 'capabilities': [],
            'tools': [], 'skills': [], 'context_assembly': 'fixture-context/v1',
            'control_loop': 'recursive/v1', 'state_handling': 'local-feedback/v1',
            'system_environment': 'test-process/v1', 'implementation': 'test-callback/v1'})
        return AgentDefinition(id, self.spec, Harness(id + '-v1', decide, configuration),
            AgentConstraints(frozenset(targets), frozenset(children), max_steps),
            'concorde-agent-task', 'concorde-agent-answer')

    def task(self, task='answer', target='service.transfer'):
        return typed('concorde-agent-task', {'task': task, 'target_id': target})

    def done(self, answer='done', source='code-driven'):
        return AgentStep(source, 'complete', value=typed('concorde-agent-answer', {'answer': answer}))

    def invoke(self, definitions, *, agent='A', input=None, agents=None, targets=('service.transfer',), **options):
        runtime = AgentRuntime(definitions, self.context, **options)
        grant = AgentGrant(frozenset(targets), frozenset(agents or [d.id for d in definitions]))
        return runtime.invoke(agent, input or self.task(), grant)

    def test_nested_code_model_code_chain_and_private_fresh_frames(self):
        frames = []
        def callback(child=None, source='code-driven'):
            def decide(frame):
                frames.append(frame)
                if child and not frame.feedback:
                    return AgentStep(source, 'delegate', child, self.task('child task'))
                if frame.feedback:
                    self.assertNotIn('context_json', frame.feedback[0].wire())
                return self.done(source=source)
            return decide
        definitions = [self.definition('A', callback('B'), ['B']),
            self.definition('B', callback('C', 'model-driven'), ['C']),
            self.definition('C', callback())]
        run = self.invoke(definitions)
        self.assertEqual(run.result.outcome, 'completed')
        admitted = [e for e in run.events if e['event'] == 'admit']
        self.assertEqual([e['agent_id'] for e in admitted], ['A', 'B', 'C'])
        self.assertEqual(len({e['invocation_id'] for e in admitted}), 3)
        self.assertEqual([e['depth'] for e in admitted], [0, 1, 2])
        self.assertEqual(admitted[1]['parent_id'], admitted[0]['invocation_id'])
        self.assertEqual(admitted[2]['parent_id'], admitted[1]['invocation_id'])
        self.assertEqual([f.agent_id for f in frames], ['A', 'B', 'C', 'B', 'A'])
        self.assertEqual([len(f.feedback) for f in frames[:3]], [0, 0, 0])
        self.assertEqual([e['source'] for e in run.events if e['event']=='decision'],
                         ['code-driven', 'model-driven', 'code-driven', 'model-driven', 'code-driven'])

    def test_same_agent_can_be_leaf_or_recursive_parent(self):
        def decide(frame):
            if decode(frame.input_json)['data']['task']=='root' and not frame.feedback:
                return AgentStep('model-driven', 'delegate', 'A', self.task('leaf'))
            return self.done()
        definition = self.definition('A', decide, ['A'])
        self.assertEqual(len([e for e in self.invoke([definition]).events if e['event']=='admit']), 1)
        self.assertEqual(len([e for e in self.invoke([definition], input=self.task('root')).events if e['event']=='admit']), 2)

    def test_harness_configuration_is_inspectable_and_changes_binding_identity(self):
        definition = self.definition('A', lambda frame: self.done())
        first = self.invoke([definition]).events[0]
        configuration = decode(definition.harness.configuration_json)
        configuration['model_integration'] = 'another-integration/v2'
        changed = replace(definition, harness=replace(definition.harness,
            configuration_json=json.dumps(configuration)))
        second = self.invoke([changed]).events[0]
        self.assertEqual(first['harness_id'], second['harness_id'])
        self.assertNotEqual(first['binding_digest'], second['binding_digest'])
        self.assertEqual(decode(second['harness_configuration_json']), configuration)
        self.assertEqual(changed.harness.configuration_json, canonical(configuration))
        bounded = self.invoke([definition], limits=AgentLimits(max_calls=2)).events[0]
        self.assertNotEqual(first['binding_digest'], bounded['binding_digest'])

    def test_incomplete_harness_and_unidentified_injected_executor_are_rejected(self):
        definition = self.definition('A', lambda frame: self.fail('must not execute'))
        for configuration in ('{}', '[]', None):
            with self.subTest(configuration=configuration), self.assertRaises(ValueError):
                replace(definition.harness, configuration_json=configuration)
        from concorde.agents.reader import definition as reader_definition
        with self.assertRaisesRegex(ValueError, 'executor_reference'):
            reader_definition(PACKAGE, 'service.transfer', executor=lambda launch: None)

    def test_undeclared_self_call_is_denied_before_context_admission(self):
        def decide(frame):
            if frame.feedback:
                self.assertEqual(frame.feedback[0].error, 'delegation_denied')
                return self.done()
            return AgentStep('code-driven', 'delegate', 'A', self.task())
        run = self.invoke([self.definition('A', decide)])
        self.assertEqual(run.result.outcome, 'completed')
        self.assertEqual(len([e for e in run.events if e['event']=='admit']), 1)

    def test_host_allowlist_and_target_attenuation_prevent_child_effects(self):
        calls=[]
        def parent(frame):
            if frame.feedback:
                return self.done(frame.feedback[0].outcome)
            return AgentStep('model-driven', 'delegate', 'B', self.task(target='module.ledger'))
        a=self.definition('A',parent,['B'])
        b=self.definition('B',lambda f: calls.append(f) or self.done(),targets=('module.ledger',))
        for agents in (['A'], ['A','B']):
            with self.subTest(agents=agents):
                run=self.invoke([a,b],agents=agents,targets=('service.transfer','module.ledger'))
                self.assertEqual(decode(run.result.value_json)['data']['answer'],'rejected')
        self.assertEqual(calls,[])

    def test_invalid_child_input_is_typed_failure_feedback(self):
        def parent(frame):
            return (self.done(frame.feedback[0].error) if frame.feedback else
                AgentStep('code-driven','delegate','B',{'type_id':'unknown'}))
        run=self.invoke([self.definition('A',parent,['B']),self.definition('B',lambda f:self.done())])
        self.assertEqual(decode(run.result.value_json)['data']['answer'],'admission_failed')
        self.assertNotIn('B',[a[0] for a in self.admissions])

    def test_shared_limits_propagate_and_do_not_reset_in_children(self):
        recursive=self.definition('A',lambda f: AgentStep('model-driven','delegate','A',self.task()),['A'],max_steps=99)
        for limits in [AgentLimits(max_depth=0), AgentLimits(max_calls=2),
                       AgentLimits(max_decisions=2), AgentLimits(max_depth=20,max_calls=3)]:
            with self.subTest(limits=limits):
                run=self.invoke([recursive],limits=limits)
                self.assertEqual(run.result.outcome,'limit_exhausted')
                self.assertTrue(all(e['outcome']=='limit_exhausted' for e in run.events if e['event']=='return'))
                self.assertLessEqual(len([e for e in run.events if e['event']=='admit']),limits.max_calls)
        for kwargs in ({'max_calls':0},{'max_depth':-1},{'max_decisions':True},{'timeout_seconds':float('inf')}):
            with self.assertRaises(ValueError): AgentLimits(**kwargs)

    def test_cancellation_during_child_stops_ancestor_before_continuation(self):
        cancelled=[False]; calls=[]
        def child(frame):
            cancelled[0]=True
            return self.done()
        def parent(frame):
            calls.append(frame)
            return AgentStep('code-driven','delegate','B',self.task())
        run=self.invoke([self.definition('A',parent,['B']),self.definition('B',child)],cancelled=lambda:cancelled[0])
        self.assertEqual(run.result.outcome,'cancelled')
        self.assertEqual(len(calls),1)

    def test_deadline_overrides_late_success(self):
        now=[0.0]
        def decide(frame):
            now[0]=100.0
            return self.done()
        with patch('concorde.host.agent_runtime.monotonic',lambda:now[0]):
            run=self.invoke([self.definition('A',decide)],limits=AgentLimits(timeout_seconds=1))
        self.assertEqual(run.result.outcome,'limit_exhausted')

    def test_errors_are_sanitized_and_recovery_is_bounded(self):
        def fail(frame): raise RuntimeError('PRIVATE_CODE_AND_TRANSCRIPT')
        def parent(frame):
            if frame.feedback:
                self.assertEqual(frame.feedback[0].error,'execution_failed')
                return self.done()
            return AgentStep('code-driven','delegate','B',self.task())
        run=self.invoke([self.definition('A',parent,['B']),self.definition('B',fail)])
        self.assertEqual(run.result.outcome,'completed')
        self.assertNotIn('PRIVATE_CODE',canonical(run.events))

    def test_gap_and_waiting_keep_typed_provenance_and_reject_wrong_snapshot(self):
        for outcome in ('spec_incomplete','waiting'):
            def decide(frame):
                snapshot=decode(frame.context_json)['data']
                gap={'question':'Which limit?','needed_contract':'Limit owner','blocked_step':'Choose limit',
                     'target_id':snapshot['target_id'],'context_id':snapshot['context_id']}
                details=typed('concorde-agent-interruption',{'gaps':[gap] if outcome=='spec_incomplete' else [],
                    'decision':'Choose desired behavior' if outcome=='waiting' else None})
                return AgentStep('model-driven','complete',outcome=outcome,details=details)
            result=self.invoke([self.definition('A',decide)]).result
            self.assertEqual(result.outcome,outcome)
            self.assertIsNone(result.value_json)
            self.assertIsNotNone(result.details_json)
        result=self.invoke([self.definition('A',lambda f:AgentStep('code-driven','complete',outcome='spec_incomplete'))]).result
        self.assertEqual(result.error,'invalid_step')

    def test_invalid_completion_and_changed_context_fail_closed(self):
        wrong=self.definition('A',lambda f:AgentStep('code-driven','complete',value=self.task()))
        self.assertEqual(self.invoke([wrong]).result.error,'invalid_step')
        def changed(frame):
            (self.root/'specs/send-money.md').write_text((self.root/'specs/send-money.md').read_text()+'\nChanged contract.\n')
            return AgentStep('code-driven','delegate','A',self.task())
        # Change occurs during the child; parent's next decision must not receive revised context.
        def parent(frame):
            return AgentStep('code-driven','delegate','B',self.task())
        run=self.invoke([self.definition('A',parent,['B']),self.definition('B',lambda f: changed(f))])
        self.assertEqual(run.result.error,'stale_context')

    def test_missing_bindings_and_stale_spec_do_not_start(self):
        with self.assertRaises(ValueError):
            AgentRuntime([self.definition('A',lambda f:self.done(),['missing'])],self.context)
        definition=self.definition('A',lambda f:self.done())
        runtime=AgentRuntime([definition],self.context)
        self.spec.write_text('# Changed')
        self.assertEqual(runtime.invoke('A',self.task(),AgentGrant(frozenset({'service.transfer'}),frozenset({'A'}))).result.error,'admission_failed')

    def test_stop_during_context_resolution_never_starts_a_decision(self):
        for mode in ('cancelled', 'deadline', 'resolver_error'):
            with self.subTest(mode=mode):
                calls=[]; count=[0]; stopped=[False]; now=[0.0]
                def resolver(*args):
                    context=self.context(*args)
                    count[0]+=1
                    if count[0]==(1 if mode=='resolver_error' else 2):
                        if mode=='deadline': now[0]=10.0
                        else: stopped[0]=True
                        if mode=='resolver_error': raise RuntimeError('cancelled resolver')
                    return context
                with patch('concorde.host.agent_runtime.monotonic',lambda:now[0]):
                    runtime=AgentRuntime([self.definition('A',lambda f:calls.append(f) or self.done())],
                        resolver,limits=AgentLimits(timeout_seconds=1),cancelled=lambda:stopped[0])
                    result=runtime.invoke('A',self.task(),AgentGrant(frozenset({'service.transfer'}),frozenset({'A'}))).result
                self.assertEqual(result.outcome,'limit_exhausted' if mode=='deadline' else 'cancelled')
                self.assertEqual(calls,[])

    def test_reader_factory_uses_real_context_service_and_requires_host_grant(self):
        from concorde.agents.reader import runtime
        reader=runtime(self.root,PACKAGE,'service.transfer',executor=lambda launch, *, deadline: None,
                       executor_reference='test-null-executor/v1')
        result=reader.invoke('concorde-recursive-reader',self.task(target='module.ledger'),
            AgentGrant(frozenset({'service.transfer'}),frozenset({'concorde-recursive-reader'}))).result
        self.assertEqual(result.error,'admission_failed')
        result=reader.invoke('concorde-recursive-reader',self.task(),
            AgentGrant(frozenset({'service.transfer'}),frozenset())).result
        self.assertEqual(result.error,'agent_not_admitted')
        frames=[]
        with patch('concorde.host.native_agent.NativeAgentAdapter.__call__',
                   lambda adapter,frame: frames.append(frame) or self.done(source='model-driven')):
            result=reader.invoke('concorde-recursive-reader',self.task(),
                AgentGrant(frozenset({'service.transfer'}),frozenset({'concorde-recursive-reader'}))).result
        self.assertEqual(result.outcome,'completed')
        snapshot=decode(frames[0].context_json)['data']
        self.assertEqual(snapshot['document_order'],['specs/send-money.md','specs/transfer-promises.md'])
        self.assertEqual(snapshot['implementation_artifacts'],[])

    def test_native_codex_and_claude_yield_to_code_agent_and_continue_fresh(self):
        for integration in ('codex','claude'):
            with self.subTest(integration=integration):
                calls=[]
                bootstrap=ModelProcessDouble()
                self.addCleanup(bootstrap.runtime_directory.cleanup)
                def runner(argv,*,cwd,env,input_text):
                    runtime=json.loads((Path(cwd)/'context.json').read_text())['data']
                    calls.append((cwd,runtime,argv,input_text))
                    self.assertNotIn('PRIVATE_CODE_MUST_NOT_ENTER_SPEC_CONTEXT',input_text)
                    schema=(json.loads(Path(argv[argv.index('--output-schema')+1]).read_text()) if integration=='codex'
                            else json.loads(argv[argv.index('--json-schema')+1]))
                    properties=schema['properties']
                    payload={key:value['const'] for key,value in properties.items() if 'const' in value}
                    action='complete' if runtime['feedback'] else 'delegate'
                    value=typed('concorde-agent-answer',{'answer':'combined'}) if runtime['feedback'] else self.task('child')
                    payload.update(status='success',output='typed action',limitations='none',
                        gates=[{'name':'admission','status':'passed','evidence':'Explicit process double; host boundary is real.'}],
                        domain_output=typed('concorde-agent-loop-step',{'source':'model-driven','action':action,
                            'agent_id':'B' if action=='delegate' else None,'value_json':canonical(value),
                            'outcome':'completed','details':None}))
                    stdout=(json.dumps({'structured_output':payload}) if integration=='claude' else '\n'.join([
                        json.dumps({'type':'item.completed','item':{'type':'agent_message','text':json.dumps(payload)}}),
                        json.dumps({'type':'turn.completed'})]))
                    return subprocess.CompletedProcess(argv,0,stdout,'')
                executor=AgentProcessExecutor(runner=runner,version_probe=lambda *a:'test-client 9.2',
                    runtime_bootstrap_resolver=bootstrap.bootstrap)
                deadlines=[]
                def injected(launch, *, deadline):
                    deadlines.append(deadline)
                    return executor(launch)
                adapter=NativeAgentAdapter(integration,injected)
                runtime=AgentRuntime([self.definition('A',adapter,['B']),self.definition('B',lambda f:self.done())],self.context)
                host=CapabilityHost(self.root,PACKAGE)
                run=host.invoke_agent(runtime,'A',self.task(),AgentGrant(frozenset({'service.transfer'}),frozenset({'A','B'})))
                self.assertEqual(run.result.outcome,'completed')
                self.assertEqual(len(calls),2)
                self.assertEqual(len(deadlines), 2)
                self.assertEqual(deadlines[0], deadlines[1])
                self.assertNotEqual(calls[0][0],calls[1][0])
                self.assertEqual(calls[0][1]['invocation_id'],calls[1][1]['invocation_id'])
                self.assertEqual(calls[0][1]['feedback'],[])
                self.assertEqual(calls[1][1]['feedback'][0]['agent_id'],'B')
                self.assertTrue(host.evidence)
                for cwd,_,argv,_ in calls:
                    self.assertFalse(Path(cwd).exists())
                    if integration=='codex':
                        self.assertIn('features.multi_agent=false',argv)
                        self.assertIn('features.multi_agent_v2=false',argv)
                    else:
                        settings=json.loads(argv[argv.index('--settings')+1])
                        self.assertIn('Agent',settings['permissions']['deny'])
                        self.assertIn('Task',settings['permissions']['deny'])
                        self.assertEqual(settings['sandbox']['filesystem']['allowWrite'],[])

    def test_attested_malformed_native_decision_is_rejected_child_feedback(self):
        for source, value_json in (('model-driven', '{'),
                                   ('code-driven', canonical(typed('concorde-agent-answer', {'answer': 'bad source'})))):
            with self.subTest(source=source):
                bootstrap = ModelProcessDouble()
                self.addCleanup(bootstrap.runtime_directory.cleanup)
                def runner(argv, *, cwd, env, input_text):
                    schema = json.loads(Path(argv[argv.index('--output-schema') + 1]).read_text())
                    payload = {key: value['const'] for key, value in schema['properties'].items() if 'const' in value}
                    payload.update(status='success', output='malformed decision fixture', limitations='none',
                        gates=[{'name': 'fixture', 'status': 'passed', 'evidence': 'Attested process double.'}],
                        domain_output=typed('concorde-agent-loop-step', {'source': source, 'action': 'complete',
                            'agent_id': None, 'value_json': value_json, 'outcome': 'completed', 'details': None}))
                    stdout = '\n'.join([json.dumps({'type': 'item.completed', 'item': {
                        'type': 'agent_message', 'text': json.dumps(payload)}}), json.dumps({'type': 'turn.completed'})])
                    return subprocess.CompletedProcess(argv, 0, stdout, '')
                executor = AgentProcessExecutor(runner=runner, version_probe=lambda *args: 'test-client 9.2',
                    runtime_bootstrap_resolver=bootstrap.bootstrap)
                observed = []
                def parent(frame):
                    if not frame.feedback:
                        return AgentStep('code-driven', 'delegate', 'B', self.task('child'))
                    observed.extend(frame.feedback)
                    return self.done()
                run = self.invoke([self.definition('A', parent, ['B']),
                    self.definition('B', NativeAgentAdapter('codex',
                        lambda launch, *, deadline: executor(launch)))])
                self.assertEqual(run.result.outcome, 'completed')
                self.assertEqual(len(observed), 1)
                self.assertEqual((observed[0].outcome, observed[0].error), ('rejected', 'invalid_step'))
                self.assertIsNone(observed[0].value_json)


if __name__=='__main__':
    unittest.main()
