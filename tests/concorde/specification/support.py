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
    files={'specs/how-money-moves.md':'# Banking\nA Transfer moves money between Accounts. The transfer Service checks positive amount and sufficient funds. Ledger stores balances. A completed transfer debits the sender and credits the receiver. Duplicate requests require a new decision; unspecified retries are a Spec gap.\n',
      'specs/audit-scope.md':'# Audit\nThe transfer Service participates here to explain successful balance changes. Audit does not own the implementation.\n',
      'specs/send-money.md':'# Transfer money\n## feature.transfer\ntransfer(balance, amount) returns balance minus amount when amount is positive and balance is sufficient. It raises ValueError otherwise. Calls are pure and do not alter stored balances.\n',
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
        value=json.JSONDecoder().raw_decode(input_text.split('Complete admitted context and task:\n',1)[1])[0]
        snapshot=value['data']['snapshot']['data']
        self.calls.append({'stage':stage,'snapshot':snapshot,'cwd':Path(cwd),'prompt':input_text,'argv':argv})
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
