"""Consumer fixture and explicit model-process double for the Profile 9 boundary."""
import json
import re
import sys
import tempfile
import hashlib
import subprocess
from pathlib import Path
from concorde.host.typed_data import typed
from concorde.host.agent_executor import AgentProcessExecutor
from concorde.specification.initialize import project_proposal, apply_project_proposal, empty_target, initial_overview

PACKAGE = Path(__file__).resolve().parents[3]
CONFIGURATION = typed('concorde-capability-configuration', {'integration':'claude','enforcement':'native'})

def update_document_declaration(root, path, **updates):
    document=root/path;text=document.read_text()
    match=re.search(r'```concorde-document\s*\n(.*?)^```',text,re.M|re.S)
    if match is None:raise AssertionError(f'missing concorde-document block: {path}')
    value=json.loads(match.group(1));value.update(updates)
    document.write_text(text[:match.start()]+'```concorde-document\n'+json.dumps(value,indent=2)+
                        '\n```'+text[match.end():])

def project(root):
    apply_project_proposal(root, PACKAGE, project_proposal(root, PACKAGE, 'Bank', CONFIGURATION, 'scope.bank'))
    targets=[empty_target('scope.bank','module','Bank',['specs/bank/module.md']),
             empty_target('scope.audit','module','Audit',['specs/audit/module.md']),
             empty_target('service.transfer','module','Transfers',['specs/transfer/module.md','specs/transfer/promises.md']),
             empty_target('module.ledger','module','Ledger',['specs/ledger/module.md'])]
    targets[0]['uses']=['service.transfer','module.ledger','scope.audit']
    targets[1]['uses']=['service.transfer']
    targets[2].update(uses=['module.ledger'], implementations=['implementation.transfer'],
       features=[{'id':'feature.transfer','title':'Transfer money','document':'specs/transfer/module.md'}],
       interfaces=[{'id':'interface.transfer','title':'transfer(balance, amount)','document':'specs/transfer/module.md'}],checks=['check.transfer'])
    targets[3].update(implementations=['implementation.ledger'],
       features=[{'id':'feature.ledger','title':'Read account','document':'specs/ledger/module.md'}],
       interfaces=[{'id':'api.ledger','title':'Read account','document':'specs/ledger/module.md'}])
    for target,folder in zip(targets[:2], ('bank','audit')):
        target['diagrams']=[{'source':f'specs/{folder}/diagrams/overview.json','kind':'architecture','title':target['title'],'recipe':'system-overview'}]
    registry={'schema_version':2,'project_id':'project.bank','entry_target':'scope.bank','targets':targets,
      'implementations':[
        {'id':'implementation.transfer','title':'Transfer implementation','documents':['specs/implementations/transfer.md'],'files':['app/transfer.py','checks/transfer_check.py']},
        {'id':'implementation.ledger','title':'Ledger implementation','documents':['specs/implementations/ledger.md'],'files':['app/ledger.py']}],
      'checks':[{'id':'check.transfer','target_id':'service.transfer','argv':['{python}','checks/transfer_check.py'],'timeout_seconds':10}]}
    (root/'.concorde/specs.json').write_text(json.dumps(registry))
    files={'specs/bank/module.md':'# Banking\n## Architecture\nA Transfer moves money between Accounts. service.transfer handles transfer admission and execution; module.ledger stores balances. scope.audit defines audit outcomes. A completed transfer debits the sender and credits the receiver. Duplicate requests require a new decision; unspecified retries are a Spec gap.\n',
      'specs/audit/module.md':'# Audit\n## Architecture\nservice.transfer supplies successful balance changes. Audit describes its own outcomes without owning that Module or its implementation.\n',
      'specs/transfer/module.md':'# Transfer money\n## feature.transfer\ntransfer(balance, amount) returns balance minus amount when amount is positive and balance is sufficient. It raises ValueError otherwise. Calls are pure and do not alter stored balances.\n## interface.transfer\ntransfer accepts two integers and returns an integer or raises ValueError.\n## Architecture\nmodule.ledger provides stored-balance reads through read(account_id: str), returning an integer or raising KeyError. Ledger API tasks are separately bound to that Module.\n',
      'specs/transfer/promises.md':'# Local promises\nBalance and amount are integers. No network, persistence or implicit retry is performed by transfer. This complete collection defines all facts required to implement and test transfer.\n',
      'specs/ledger/module.md':'# Ledger API\n## feature.ledger\nRead a stored account balance.\n## api.ledger\nread(account_id: str) returns an integer balance or raises KeyError. It has no side effects.\n## Architecture\nAccounts map to integer balances. Unknown identity is an explicit lookup failure.\n',
      'specs/implementations/transfer.md':'# Transfer implementation\nBind app/transfer.py and checks/transfer_check.py. Implement the pure integer calculation and invalid-input rejection. INTERNAL_TRANSFER_IMPLEMENTATION_SPEC\n',
      'specs/implementations/ledger.md':'# Ledger implementation\nBind app/ledger.py. Preserve integer balances and explicit KeyError for unknown accounts. INTERNAL_LEDGER_IMPLEMENTATION_SPEC\n',
      'app/transfer.py':'def transfer(balance, amount):\n    return balance\n',
      'app/ledger.py':'def read(account_id):\n    raise KeyError(account_id)\n',
      'checks/transfer_check.py':'import sys\nfrom pathlib import Path\nsys.path.insert(0,str(Path.cwd()))\nfrom app.transfer import transfer\nassert transfer(100,20)==80\nfor balance,amount in [(10,20),(10,0),(10,-1)]:\n    try: transfer(balance,amount)\n    except ValueError: pass\n    else: raise AssertionError("invalid transfer accepted")\n',
      'secret.py':'PRIVATE_CODE_MUST_NOT_ENTER_SPEC_CONTEXT = True\n'}
    for target in targets:
        for path in target['documents']:
            declaration={'id':{'specs/bank/module.md':'document.bank','specs/audit/module.md':'document.audit','specs/transfer/module.md':'document.transfer.feature','specs/transfer/promises.md':'document.transfer.promises','specs/ledger/module.md':'document.ledger.api'}[path],'targets':[target['id']],'main_visible':True}
            files[path]='```concorde-document\n'+json.dumps(declaration,indent=2)+'\n```\n\n'+files[path]
        if target['uses']:
            entries=[{'target_id':peer,'responsibility':'Provide the locally described '+peer+' responsibility.',
                'selection_condition':'Select for work about '+peer+'.',
                'relied_upon_promises':['Transfer accepts positive affordable amounts; ledger reads return an integer or KeyError; audit records successful balance changes.']} for peer in target['uses']]
            files[target['documents'][0]]+='\n```concorde-dependencies\n'+json.dumps(entries,indent=2)+'\n```\n'
        for diagram in target['diagrams']:
            files[diagram['source']]=json.dumps(initial_overview(target['title'], '../../../generated/diagrams/'+target['id']+'.html'))
    for implementation in registry['implementations']:
        for path in implementation['documents']:
            declaration={'id':'document.'+implementation['id'],'targets':[implementation['id']],'main_visible':False}
            files[path]='```concorde-document\n'+json.dumps(declaration,indent=2)+'\n```\n\n'+files[path]
    for path,content in files.items():
        file=root/path;file.parent.mkdir(parents=True,exist_ok=True);file.write_text(content)
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
        from concorde.host.permissions import runtime_bootstrap_file
        path=self.runtime_executable;info=path.stat()
        return (runtime_bootstrap_file(path=str(path),sha256='sha256:'+hashlib.sha256(path.read_bytes()).hexdigest(),size=info.st_size,mode=info.st_mode & 0o777,owner=info.st_uid),)
    def run(self, argv, *, cwd, env, input_text, timeout=None):
        schema=json.loads(argv[argv.index('--json-schema')+1]) if '--json-schema' in argv else json.loads(Path(argv[argv.index('--output-schema')+1]).read_text()); properties=schema['properties']
        stage=properties['stage']['const']
        markers=('Complete admitted discovery context and task:\n','Complete provisional target context:\n','Complete admitted context and task:\n')
        marker=next(item for item in markers if item in input_text)
        value=json.JSONDecoder().raw_decode(input_text.split(marker,1)[1])[0]
        snapshot=(value['data']['snapshot']['data'] if value['type_id'] in {
            'concorde-main-stage-context','concorde-agent-stage-context','concorde-review-stage-context'} else value['data'])
        capability=properties['role']['const']
        self.calls.append({'stage':stage,'capability':capability,'snapshot':snapshot,'cwd':Path(cwd),'prompt':input_text,'argv':argv,'timeout':timeout})
        if value['type_id']=='concorde-review-stage-context':
            review=value['data']['review']['data']
            self.calls[-1]['review']=review
            data={'context_id':snapshot['context_id'],'input_digest':review['input_digest'],
                  'review_mode':review['review_mode'],'status':'no_findings',
                  'representative_tasks':[snapshot['task']],'findings':[],'gaps':[],
                  'answer':'Explicit process double completed; model effectiveness is not measured.'}
            if self.callback:self.callback(stage,snapshot,data,Path(cwd))
            payload={key:item['const'] for key,item in properties.items() if 'const' in item}
            payload.update(status='success',output='Explicit review-process double.',limitations='none',
              gates=[{'name':'bounded-review','status':'passed','evidence':'Review process is substituted; host admission is real.'}],
              domain_output=typed('concorde-review-stage-result',data))
            stdout=json.dumps({'structured_output':payload}) if '--json-schema' in argv else '\n'.join(json.dumps(event) for event in [{'type':'item.completed','item':{'type':'agent_message','text':json.dumps(payload)}},{'type':'turn.completed'}])
            return subprocess.CompletedProcess(argv,0,stdout,'')
        if value['type_id']=='concorde-topology-author-context':
            current={item['path']:item['content']
                     for section in ('target_spec','shared_specs') for item in snapshot[section]}
            target=snapshot['target']
            candidate={item['path']:item['targets'] for item in snapshot['candidate_document_references']}
            def initial(path):
                document_id='document.'+re.sub(r'[^a-z0-9.-]+','-',path.lower().removesuffix('.md').replace('/','.'))
                declaration={'id':document_id,'targets':candidate[path],
                             'main_visible':True}
                return ('```concorde-document\n'+json.dumps(declaration,indent=2)+'\n```\n\n'
                    f"# {target['title']}\n\n"+"## Architecture\n\n"+f"Stable target ID: {target['id']}.\n\n{snapshot['task']}\n")
            documents=[{'path':path,'content':current.get(path,initial(path))}
                       for path in target['documents']]
            current_diagrams={item['path']:item['content'] for item in snapshot['diagram_sources']}
            diagrams=[{'path':d['source'],'content':current_diagrams.get(d['source'],json.dumps(initial_overview(d['title'],'../../../generated/diagrams/new-domain.html')))} for d in target['diagrams']]
            data={'context_id':snapshot['context_id'],'target_id':target['id'],'outcome':'completed',
                  'answer':'Target-local Spec authored.','gaps':[],'documents':documents,'diagrams':diagrams}
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
        if stage=='tasks':
            task_target=snapshot['target_id']
            if snapshot['target_id'] in {'scope.bank','scope.audit'}:
                body='\n'.join(item['content']
                    for section in ('target_spec','shared_specs') for item in snapshot[section])
                block=re.search(r'```concorde-dependencies\s*\n(.*?)^```',body,re.M|re.S)
                if block is None:raise AssertionError('Module task fixture requires local participant declarations')
                task_target=json.loads(block.group(1))[0]['target_id']
            data['tasks']=[{'id':'task.transfer','target_id':task_target,
            'description':'Implement the transfer promise.','acceptance':'Valid transfer subtracts; invalid amount or insufficient funds raises ValueError.','complete':False}]
        if stage=='implementation' and snapshot['stage_inputs'][0]['type_id']=='concorde-implementation-task':
            if snapshot['target_id']=='module.ledger':
                (Path(cwd)/'app/ledger.py').write_text('def read(account_id):\n    balances = {"known": 100}\n    return balances[account_id]\n')
            else:
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
