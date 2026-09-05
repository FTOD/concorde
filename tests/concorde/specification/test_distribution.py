"""Installed source closure and both native completion adapters, with explicit process doubles."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from concorde.capabilities.protocol_contracts import OPERATIONS,INTERNAL_SKILLS
from concorde.capabilities.profile8_validation import validate_package
from concorde.capabilities.skill_assets import render_capabilities,load_skill_prompt
from concorde.capabilities.operation_data import typed
from concorde.specification.repository import SpecRepository
from concorde.specification.validation import validate_repository
from .support import PACKAGE,CONFIGURATION,project,ModelProcessDouble

class DistributionTests(unittest.TestCase):
    def test_catalog_roles_and_exported_schemas_are_executable_package_contracts(self):
        self.assertEqual([],validate_package(PACKAGE))
        self.assertEqual(22,len(OPERATIONS));self.assertEqual(6,len(INTERNAL_SKILLS))
        for role in INTERNAL_SKILLS:self.assertEqual('internal',load_skill_prompt(PACKAGE,role).exposure)
    def test_source_public_projections_match_canonical_pairs(self):
        for integration in ('claude','codex'):
            for path,content in render_capabilities(PACKAGE,integration,"").items():self.assertEqual(content,(PACKAGE/path).read_text(),path)
    def test_self_architecture_uses_two_axes_and_local_operation_registry(self):
        repo=SpecRepository(PACKAGE);self.assertEqual('success',validate_repository(PACKAGE).status)
        self.assertEqual({'domain':4,'service':5,'module':8},{kind:sum(t.kind==kind for t in repo.targets.values()) for kind in ('domain','service','module')})
        text='\n'.join(d.body for d in repo.documents(repo.select('service.workflow-host')))
        for op in OPERATIONS:self.assertIn(op+'-request',text)
    def test_paired_cli_accepts_only_typed_stdin_and_rejects_old_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);project(root)
            command=[sys.executable,str(PACKAGE/'operations/concorde-context/operation.py')]
            value={'type_id':'concorde-operation-invocation','schema_version':2,'operation_id':'concorde-context','mode':'execute','configuration':None,'input':typed('concorde-context-request',{'target_id':'service.transfer','task':'Explain transfer'})}
            result=subprocess.run(command,input=json.dumps(value),capture_output=True,text=True,cwd=root)
            self.assertEqual(0,result.returncode,result.stdout+result.stderr);self.assertEqual(2,len(json.loads(result.stdout)['output']['data']['snapshot']['data']['documents']))
            result=subprocess.run(command+['--feature-path','specs/send-money.md'],input=json.dumps(value),capture_output=True,text=True,cwd=root)
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
from concorde.capabilities.operation_data import typed
helper.CONFIGURATION=typed('concorde-operation-configuration',{'integration':sys.argv[2],'enforcement':'native'})
helper.project(root)
from concorde.capabilities.operation_service import OperationHost,run_operation
import concorde.capabilities.scoped_operations as actual_host
model=helper.ModelProcessDouble();host=OperationHost(root,framework,executor=model.executor,allow_primary_worktree=True)
result=run_operation('concorde-standard-dev-loop',None,typed('concorde-standard-dev-loop-request',{'target_id':'service.transfer','task':'Implement transfer'}),host_context=host)
print(json.dumps({'result':result,'module_source':actual_host.__file__,'stages':[c['stage'] for c in model.calls]}))
''')
                completed=subprocess.run([sys.executable,str(driver),str(PACKAGE/'tests/concorde/specification/support.py'),integration],cwd=root,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
                self.assertEqual(0,completed.returncode,completed.stderr);value=json.loads(completed.stdout)
                self.assertIn('.concorde/framework/src',value['module_source']);self.assertEqual('succeeded',value['result']['status'],value)
                self.assertEqual('delivered',value['result']['output']['data']['outcome']);self.assertEqual('passed',value['result']['output']['data']['checks'][0]['status'])
    def test_completion_from_previous_invocation_cannot_be_replayed(self):
        from concorde.capabilities.operation_service import OperationHost,run_operation
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);project(root);model=ModelProcessDouble();saved=[]
            def executor(launch):
                if saved:return saved[0]
                result=model.executor(launch);saved.append(result);return result
            host=OperationHost(root,PACKAGE,executor=executor,allow_primary_worktree=True)
            task=typed('concorde-ask-request',{'target_id':'service.transfer','task':'Explain transfer'})
            first=run_operation('concorde-ask',CONFIGURATION,task,host_context=host);second=run_operation('concorde-ask',CONFIGURATION,task,host_context=host)
            self.assertEqual('succeeded',first['status']);self.assertEqual('blocked',second['status']);self.assertEqual('invalid_completion',second['errors'][0]['code'])
