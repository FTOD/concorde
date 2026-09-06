"""Consumer fixture and explicit model-process double for the Profile 8 boundary."""
import json
import sys
import tempfile
import hashlib
import subprocess
from pathlib import Path
from concorde.capabilities.operation_data import typed
from concorde.capabilities.operation_executor import AgentProcessExecutor
from concorde.specification.initialize import project_proposal, apply_project_proposal, empty_target

PACKAGE = Path(__file__).resolve().parents[3]
CONFIGURATION = typed('concorde-operation-configuration', {'integration':'claude','enforcement':'native'})

def project(root):
    apply_project_proposal(root, PACKAGE, project_proposal(root, PACKAGE, 'Bank', CONFIGURATION, 'scope.bank'))
    targets=[empty_target('scope.bank','domain','Bank',['specs/how-money-moves.md']),
             empty_target('scope.audit','domain','Audit',['specs/audit-scope.md']),
             empty_target('service.transfer','service','Transfers',['specs/send-money.md','specs/transfer-promises.md']),
             empty_target('module.ledger','module','Ledger',['specs/ledger-api.md'])]
    targets[2].update(participates_in=['scope.bank','scope.audit'], implementation=['app/transfer.py','checks/transfer_check.py'],
       features=[{'id':'feature.transfer','title':'Transfer money','document':'specs/send-money.md'}],checks=['check.transfer'])
    targets[3].update(component_parent='service.transfer', participates_in=['scope.bank'], implementation=['app/ledger.py'],
       apis=[{'id':'api.ledger','title':'Read account','document':'specs/ledger-api.md'}])
    registry={'schema_version':1,'project_id':'project.bank','entry_target':'scope.bank','targets':targets,
      'checks':[{'id':'check.transfer','target_id':'service.transfer','argv':['{python}','checks/transfer_check.py'],'timeout_seconds':10}]}
    (root/'.concorde/specs.json').write_text(json.dumps(registry))
    files={'specs/how-money-moves.md':'# Banking\nA Transfer moves money between Accounts. The registered service.transfer Service handles transfer admission and execution; inspect its Service Spec when a task concerns that consumer capability. The module.ledger Module stores balances and is selected only after an admitted Domain or Service identifies a ledger API task. A completed transfer debits the sender and credits the receiver. The scope.audit Domain explains audit-specific outcomes. Duplicate requests require a new decision; unspecified retries are a Spec gap.\n',
      'specs/audit-scope.md':'# Audit\nThe registered service.transfer Service participates here to explain successful balance changes. Audit does not own the implementation.\n',
      'specs/send-money.md':'# Transfer money\n## feature.transfer\ntransfer(balance, amount) returns balance minus amount when amount is positive and balance is sufficient. It raises ValueError otherwise. Calls are pure and do not alter stored balances. The module.ledger target owns stored-balance reads; route ledger API questions to that Module without loading its Spec into main discovery.\n',
      'specs/transfer-promises.md':'# Local promises\nBalance and amount are integers. No network, persistence, retry, or collaborator is required. This complete two-document collection defines all facts required to implement and test transfer.\n',
      'specs/ledger-api.md':'# Ledger API\n## api.ledger\nread(account_id: str) returns an integer balance or raises KeyError. It has no side effects.\n',
      'app/transfer.py':'def transfer(balance, amount):\n    return balance\n',
      'app/ledger.py':'def read(account_id):\n    raise KeyError(account_id)\n',
      'checks/transfer_check.py':'import sys\nfrom pathlib import Path\nsys.path.insert(0,str(Path.cwd()))\nfrom app.transfer import transfer\nassert transfer(100,20)==80\nfor balance,amount in [(10,20),(10,0),(10,-1)]:\n    try: transfer(balance,amount)\n    except ValueError: pass\n    else: raise AssertionError("invalid transfer accepted")\n',
      'secret.py':'PRIVATE_CODE_MUST_NOT_ENTER_SPEC_CONTEXT = True\n'}
    for path,content in files.items():
        file=root/path; file.parent.mkdir(parents=True,exist_ok=True); file.write_text(content)
    return registry

class ModelProcessDouble:
    def __init__(self, callback=None):
        self.calls=[]; self.callback=callback
        self.runtime_directory=tempfile.TemporaryDirectory()
        self.runtime_executable=Path(self.runtime_directory.name)/"codex"
        self.runtime_executable.write_bytes(b"\x7fELFfixture-model-process")
        self.runtime_executable.chmod(0o755)
        self.executor=AgentProcessExecutor(runner=self.run, version_probe=lambda *args:'test-client 4.2', runtime_bootstrap_resolver=self.bootstrap)
    def bootstrap(self,integration,*args):
        if integration!='codex':return ()
        from concorde.capabilities.operation_permissions import runtime_bootstrap_file
        path=self.runtime_executable;info=path.stat()
        return (runtime_bootstrap_file(path=str(path),sha256='sha256:'+hashlib.sha256(path.read_bytes()).hexdigest(),size=info.st_size,mode=info.st_mode & 0o777,owner=info.st_uid),)
    def run(self, argv, *, cwd, env, input_text):
        schema=json.loads(argv[argv.index('--json-schema')+1]) if '--json-schema' in argv else json.loads(Path(argv[argv.index('--output-schema')+1]).read_text()); properties=schema['properties']
        stage=properties['stage']['const']
        markers=('Complete admitted discovery context and task:\n','Complete provisional target context:\n','Complete admitted context and task:\n')
        marker=next(item for item in markers if item in input_text)
        value=json.JSONDecoder().raw_decode(input_text.split(marker,1)[1])[0]
        snapshot=(value['data']['snapshot']['data'] if value['type_id'] in {
            'concorde-main-stage-context','concorde-agent-stage-context'} else value['data'])
        capability=properties['capability']['const']
        self.calls.append({'stage':stage,'capability':capability,'snapshot':snapshot,'cwd':Path(cwd),'prompt':input_text,'argv':argv})
        if value['type_id']=='concorde-topology-author-context':
            current={item['path']:item['content'] for item in snapshot['current_documents']}
            target=snapshot['target']
            documents=[{'path':path,'content':current.get(path,
                f"# {target['title']}\n\nStable target ID: {target['id']}.\n\n{snapshot['task']}\n")}
                for path in target['documents']]
            data={'context_id':snapshot['context_id'],'target_id':target['id'],'outcome':'completed',
                  'answer':'Target-local Spec authored.','gaps':[],'documents':documents}
            if self.callback:self.callback(stage,snapshot,data,Path(cwd))
            payload={key:item['const'] for key,item in properties.items() if 'const' in item}
            payload.update(status='success',output='Explicit topology-author double.',limitations='none',
              gates=[{'name':'bounded-topology-author','status':'passed','evidence':'Target-local author process is substituted; host validation is real.'}],
              domain_output=typed('concorde-topology-author-result',data))
            stdout=json.dumps({'structured_output':payload}) if '--json-schema' in argv else '\n'.join(json.dumps(event) for event in [{'type':'item.completed','item':{'type':'agent_message','text':json.dumps(payload)}},{'type':'turn.completed'}])
            return subprocess.CompletedProcess(argv,0,stdout,'')
        if value['type_id']=='concorde-main-stage-context':
            data={'context_id':snapshot['context_id'],'outcome':'completed','answer':'Main synthesized bounded worker results.',
                  'expand_targets':[],'routes':[],'gaps':[],'topology_design':None}
            if stage=='route':
                hint=snapshot['target_hint']
                discovered=[item['target_id'] for item in snapshot['targets']]
                if hint:
                    data.update(outcome='routed',routes=[{'target_id':hint,'focus_id':snapshot['focus_hint'],
                        'task':snapshot['task'],'constraints':snapshot['constraints']}])
                elif 'service.transfer' not in discovered:
                    data.update(outcome='expand',expand_targets=['service.transfer'])
                else:
                    data.update(outcome='routed',routes=[{'target_id':'service.transfer','focus_id':None,
                        'task':snapshot['task'],'constraints':snapshot['constraints']}])
            if self.callback:self.callback(stage,snapshot,data,Path(cwd))
            payload={key:item['const'] for key,item in properties.items() if 'const' in item}
            payload.update(status='success',output='Explicit main-process double.',limitations='none',
              gates=[{'name':'bounded-main-role','status':'passed','evidence':'Main process is substituted; discovery admission and host routing are real.'}],
              domain_output=typed('concorde-main-stage-result',data))
            stdout=json.dumps({'structured_output':payload}) if '--json-schema' in argv else '\n'.join(json.dumps(event) for event in [{'type':'item.completed','item':{'type':'agent_message','text':json.dumps(payload)}},{'type':'turn.completed'}])
            return subprocess.CompletedProcess(argv,0,stdout,'')
        data={'context_id':snapshot['context_id'],'outcome':'completed','answer':'Bounded role completed.',
              'gaps':[],'documents':[],'plan':'','tasks':[]}
        if stage=='context-solve': data['outcome']='sufficient'
        if stage=='plan': data['plan']='Implement the pure transfer contract, then check valid and rejected amounts.'
        if stage=='tasks': data['tasks']=[{'id':'task.transfer','target_id':snapshot['target_id'],
            'description':'Implement the transfer promise.','acceptance':'Valid transfer subtracts; invalid amount or insufficient funds raises ValueError.','complete':False}]
        if stage=='implementation' and snapshot['stage_inputs'][0]['type_id']=='concorde-implementation-task':
            (Path(cwd)/'app/transfer.py').write_text('def transfer(balance, amount):\n    if amount <= 0 or amount > balance:\n        raise ValueError("invalid transfer")\n    return balance - amount\n')
            task_input=snapshot['stage_inputs'][0]['data']
            data['tasks']=[{**task,'complete':True} for task in task_input['tasks']]
        if self.callback: self.callback(stage, snapshot, data, Path(cwd))
        payload={key:item['const'] for key,item in properties.items() if 'const' in item}
        payload.update(status='success',output='Explicit model-process double.',limitations='none',
          gates=[{'name':'bounded-role','status':'passed','evidence':'Model process is substituted; host, checks and completion validation are real.'}],
          domain_output=typed('concorde-agent-stage-result',data))
        stdout=json.dumps({'structured_output':payload}) if '--json-schema' in argv else '\n'.join(json.dumps(event) for event in [{'type':'item.completed','item':{'type':'agent_message','text':json.dumps(payload)}},{'type':'turn.completed'}])
        return subprocess.CompletedProcess(argv,0,stdout,'')
