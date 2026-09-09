"""Installed source closure and both native completion adapters, with explicit process doubles."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from concorde.host.contracts import CAPABILITY_NAMES,INTERNAL_SKILLS
from concorde.host.package_validation import validate_package
from concorde.host.build import load_role_prompt
from concorde.host.typed_data import typed
from concorde.specification.repository import SpecRepository
from concorde.specification.validation import validate_repository
from .support import PACKAGE,CONFIGURATION,project,ModelProcessDouble

class DistributionTests(unittest.TestCase):
    def test_catalog_roles_and_exported_schemas_are_executable_package_contracts(self):
        self.assertEqual([],validate_package(PACKAGE))
        self.assertEqual(13,len(CAPABILITY_NAMES));self.assertEqual(9,len(INTERNAL_SKILLS))
        self.assertIn('concorde-main',CAPABILITY_NAMES);self.assertNotIn('concorde-ask',CAPABILITY_NAMES)
        self.assertIn('concorde-coordinator',INTERNAL_SKILLS);self.assertNotIn('concorde-main',INTERNAL_SKILLS)
        for role in INTERNAL_SKILLS:
            prompt=load_role_prompt(PACKAGE,role)
            self.assertEqual(role,prompt.name);self.assertTrue(prompt.body.strip());self.assertIsNotNone(prompt.effects)
    def test_self_architecture_separates_modules_and_reusable_implementations(self):
        repo=SpecRepository(PACKAGE);report=validate_repository(PACKAGE)
        self.assertEqual('success',report.status,report.findings)
        self.assertEqual(15,len(repo.targets));self.assertTrue(all(t.kind=='module' for t in repo.targets.values()))
        self.assertEqual(18,len(repo.implementations))
        self.assertEqual('module.concorde',repo.select('module.publication').parent)
        self.assertIn('scripts/run-viewer.py',repo.implementation_paths(repo.select('module.viewer')))
        self.assertGreater(len(repo.implementation_users['implementation.worktree-lifecycle']),1)
        text='\n'.join(d.body for d in repo.documents(repo.select('module.workflows')))
        for op in CAPABILITY_NAMES:self.assertIn(op+'-request',text)
    def test_launcher_refuses_a_stage_capability_name_and_accepts_a_public_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);project(root)
            launcher=str(PACKAGE/'scripts/run-capability.py')
            internal_command=[sys.executable,launcher,'concorde-plan']
            internal_value={'type_id':'concorde-capability-invocation','schema_version':3,'capability_id':'concorde-plan','mode':'execute','configuration':None,'input':typed('concorde-plan-request',{'target_id':'service.transfer','task':'Explain transfer'})}
            result=subprocess.run(internal_command,input=json.dumps(internal_value),capture_output=True,text=True,cwd=root)
            self.assertEqual(3,result.returncode,result.stdout+result.stderr)
            output=json.loads(result.stdout)
            self.assertEqual('blocked',output['status']);self.assertEqual('unknown_capability',output['errors'][0]['code'])
            public_command=[sys.executable,launcher,'concorde-validate']
            public_value={'type_id':'concorde-capability-invocation','schema_version':3,'capability_id':'concorde-validate','mode':'describe-policy','configuration':None,'input':typed('concorde-validate-request',{'target_id':'service.transfer','task':'Explain transfer'})}
            result=subprocess.run(public_command,input=json.dumps(public_value),capture_output=True,text=True,cwd=root)
            self.assertEqual(0,result.returncode,result.stdout+result.stderr)
            self.assertEqual('described',json.loads(result.stdout)['status'])
            result=subprocess.run(public_command+['--feature-path','specs/transfer/module.md'],input=json.dumps(public_value),capture_output=True,text=True,cwd=root)
            self.assertEqual(3,result.returncode);self.assertEqual('blocked',json.loads(result.stdout)['status'])
    def test_installed_framework_runs_complete_real_graph_and_checks_for_both_integrations(self):
        spec=importlib.util.spec_from_file_location('profile8_installer',PACKAGE/'scripts/install-concorde.py');module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
        package=module.load_package(PACKAGE)
        for integration in ('claude','codex'):
            with self.subTest(integration=integration),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                for path,(content,role) in module.desired_outputs(package,integration).items():
                    p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(content)
                driver=root/'driver.py';driver.write_text('''import importlib.util,json,sys
from pathlib import Path
root=Path.cwd();framework=root/'.concorde/framework';sys.path.insert(0,str(framework/'src'))
spec=importlib.util.spec_from_file_location('model_process_fixture',sys.argv[1]);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
helper.PACKAGE=framework
from concorde.host.typed_data import typed
helper.CONFIGURATION=typed('concorde-capability-configuration',{'integration':sys.argv[2],'enforcement':'native'})
helper.project(root)
from concorde.host.capability_service import CapabilityHost,run_capability
import concorde.host.capability_host as actual_host
model=helper.ModelProcessDouble();host=CapabilityHost(root,framework,executor=model.executor,allow_primary_worktree=True)
result=run_capability('concorde-dev-loop',None,typed('concorde-dev-loop-request',{'target_id':'service.transfer','task':'Implement transfer'}),host_context=host)
before=len(model.calls)
ask=run_capability('concorde-main',None,typed('concorde-main-request',{'task':'Explain transfer'}),host_context=host)
print(json.dumps({'result':result,'ask':ask,'module_source':actual_host.__file__,
  'stages':[c['stage'] for c in model.calls[:before]],'ask_stages':[c['stage'] for c in model.calls[before:]]}))
''')
                completed=subprocess.run([sys.executable,str(driver),str(PACKAGE/'tests/concorde/specification/support.py'),integration],cwd=root,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
                self.assertEqual(0,completed.returncode,completed.stderr);value=json.loads(completed.stdout)
                self.assertIn('.concorde/framework/src',value['module_source']);self.assertEqual('succeeded',value['result']['status'],value)
                self.assertEqual('ready',value['result']['output']['data']['outcome']);self.assertEqual('passed',value['result']['output']['data']['checks'][0]['status'])
                self.assertEqual('succeeded',value['ask']['status'],value);self.assertEqual(['route','route','ask','synthesize'],value['ask_stages'])
    def test_completion_from_previous_invocation_cannot_be_replayed(self):
        from concorde.host.capability_service import CapabilityHost,run_capability
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);project(root);model=ModelProcessDouble();saved=[];replay=[False]
            def executor(launch):
                if replay[0]:return saved[0]
                result=model.executor(launch)
                if not saved:saved.append(result)
                return result
            host=CapabilityHost(root,PACKAGE,executor=executor,allow_primary_worktree=True)
            task=typed('concorde-main-request',{'target_id':'service.transfer','task':'Explain transfer'})
            first=run_capability('concorde-main',CONFIGURATION,task,host_context=host);replay[0]=True
            second=run_capability('concorde-main',CONFIGURATION,task,host_context=host)
            self.assertEqual('succeeded',first['status']);self.assertEqual('blocked',second['status']);self.assertEqual('invalid_completion',second['errors'][0]['code'])
