"""Consumer fixture and explicit model-process double for the Profile 12 boundary."""
import json
import re
import tempfile
import hashlib
import subprocess
from pathlib import Path
from concorde.spec.typed_data import typed
from concorde.harness.agent_executor import AgentProcessExecutor
from concorde.spec.initialize import project_proposal, apply_project_proposal, empty_target

PACKAGE = Path(__file__).resolve().parents[3]
CONFIGURATION = typed('concorde-capability-configuration', {'integration':'claude','enforcement':'native'})

def update_document_declaration(root, path, **updates):
    document=root/path;text=document.read_text()
    match=re.search(r'```concorde-document\s*\n(.*?)^```',text,re.M|re.S)
    if match is None:raise AssertionError(f'missing concorde-document block: {path}')
    value=json.loads(match.group(1));value.update(updates)
    document.write_text(text[:match.start()]+'```concorde-document\n'+json.dumps(value,indent=2)+
                        '\n```'+text[match.end():])

def block(name, value):
    return '```'+name+'\n'+json.dumps(value,indent=2)+'\n```\n'

def module_document(document_id, target_id, title, purpose, scenarios, entities, architecture,
                    diagram, dependencies=(), trailer='', requirements='No Module-level requirement is stated here.'):
    """One four-part reading entry: Purpose, Requirements, Scenarios and an Ontology whose
    Entities subsection declares the entities and whose Relationships subsection draws them."""
    text = (block('concorde-document', {'id':document_id,'owner': target_id,'main_visible':True})
        + f'\n# {title}\n\n## Purpose\n\n{purpose}\n\n## Requirements\n\n{requirements}\n\n'
          f'## Scenarios\n\n{scenarios}\n\n## Ontology\n\n### Entities\n\n{entities[0]}\n\n'
        + block('concorde-entities', entities[1])
        + f'\n### Relationships\n\n{architecture}\n\n```mermaid\n{diagram}\n```\n')
    if dependencies:
        text += '\n## Collaborators\n\nEach collaborator below is described from this Module\'s own perspective.\n\n'
        text += block('concorde-dependencies', list(dependencies))
    return text + trailer

def promise(peer):
    return {'target_id':peer,'responsibility':'Provide the locally described '+peer+' responsibility.',
        'selection_condition':'Select for work about '+peer+'.',
        'relied_upon_promises':['Transfer accepts positive affordable amounts; ledger reads return '
            'an integer or KeyError; audit records successful balance changes.']}

BANK = module_document('document.bank','scope.bank','Banking',
    'Banking coordinates money movement between customer accounts. It performs no calculation of\n'
    'its own: transfer admission and execution belong to the transfer Module, stored balances to\n'
    'the ledger Module, and audit outcomes to the audit Module.',
    '### scenario.bank.settlement — A completed transfer settles both accounts\n\n'
    '- GIVEN a sender account whose balance covers the requested amount\n'
    '- WHEN Banking accepts one transfer request\n'
    '- THEN the sender is debited and the receiver is credited\n'
    '- AND the audit Module receives the accepted balance change\n'
    '- AND a repeated request is treated as a new decision\n',
    ('Banking owns the request concept; every other entity stands for a Module it composes with.',
     [{'id':'entity.bank.request','title':'Transfer request','kind':'concept',
       'responsibility':'Carries the sender, the receiver and the requested amount.'},
      {'id':'entity.bank.transfer','title':'Transfer service','kind':'module',
       'responsibility':'Admits and executes one transfer.','target_id':'service.transfer'},
      {'id':'entity.bank.ledger','title':'Ledger','kind':'module',
       'responsibility':'Stores the account balances Banking settles against.','target_id':'module.ledger'},
      {'id':'entity.bank.audit','title':'Audit','kind':'module',
       'responsibility':'Describes the audit outcome of an accepted change.','target_id':'scope.audit'}]),
    'A transfer request is admitted by the transfer Module, which reads balances from the ledger\n'
    'Module. The audit Module observes the accepted change without owning either provider.',
    'flowchart TB\n'
    '    accTitle: Banking coordination\n'
    '    accDescr: A transfer request reaches the transfer service, which reads balances from the ledger and reports accepted changes to audit.\n'
    '    request["Transfer request"]\n    transfer["Transfer service"]\n'
    '    ledger["Ledger"]\n    audit["Audit"]\n'
    '    request -->|admitted by| transfer\n'
    '    transfer -->|reads balances from| ledger\n'
    '    transfer -->|reports accepted changes to| audit',
    [promise(peer) for peer in ('service.transfer','module.ledger','scope.audit')],
    requirements='### req.bank.retry — Repeated requests are new decisions\n\n'
    'Banking SHALL treat a repeated request as a new decision.\n')

AUDIT = module_document('document.audit','scope.audit','Audit',
    'Audit describes the outcome an accepted balance change must produce. It owns no transfer\n'
    'calculation and no stored balance of its own.',
    '### scenario.audit.record — An accepted transfer becomes one audit record\n\n'
    '- GIVEN a transfer the transfer Module reports as successful\n'
    '- WHEN Audit receives that accepted balance change\n'
    '- THEN one audit record describes the sender, the receiver and the amount\n',
    ('Audit owns its record concept and observes the transfer Module.',
     [{'id':'entity.audit.transfer','title':'Transfer service','kind':'module',
       'responsibility':'Reports successful balance changes.','target_id':'service.transfer'},
      {'id':'entity.audit.record','title':'Audit record','kind':'concept',
       'responsibility':'Describes one accepted balance change.'}]),
    'The transfer Module produces the accepted change that Audit turns into a record.',
    'flowchart TB\n'
    '    accTitle: Audit outcomes\n'
    '    accDescr: The transfer service produces the accepted balance change that becomes one audit record.\n'
    '    transfer["Transfer service"]\n    record["Audit record"]\n'
    '    transfer -->|produces| record',
    [promise('service.transfer')])

TRANSFER = module_document('document.transfer.feature','service.transfer','Transfer money',
    'The transfer Module admits one money movement and computes its result. Calls are pure: the\n'
    'Module reads stored balances through the ledger Module and stores nothing itself.',
    '### scenario.transfer.debit — A valid amount debits the sender\n\n'
    '- GIVEN a sender balance of 100\n'
    '- WHEN transfer(100, 20) is called\n'
    '- THEN it returns 80\n'
    '- AND no stored balance changes\n\n'
    '### scenario.transfer.reject — An unaffordable or non-positive amount is rejected\n\n'
    '- GIVEN a sender balance of 10\n'
    '- WHEN transfer(10, 20) is called\n'
    '- THEN it raises ValueError\n'
    '- AND no balance changes\n',
    ('The calculation and its executable check are the Module\'s own code; the ledger Module\n'
     'supplies stored balances.',
     [{'id':'entity.transfer.calculation','title':'Transfer calculation','kind':'function',
       'responsibility':'Computes the remaining balance, or rejects the requested amount.',
       'files':['app/transfer.py']},
      {'id':'entity.transfer.check','title':'Transfer check','kind':'executable check',
       'responsibility':'Exercises one accepted amount and every rejected amount.',
       'files':['checks/transfer_check.py']},
      {'id':'entity.transfer.ledger','title':'Ledger','kind':'module',
       'responsibility':'Supplies stored balances through read(account_id).','target_id':'module.ledger'}]),
    'The check exercises the calculation, which reads stored balances from the ledger Module.\n'
    'Ledger API tasks are separately bound to that Module.',
    'flowchart TB\n'
    '    accTitle: Transfer money\n'
    '    accDescr: The transfer check exercises the transfer calculation, which reads stored balances from the ledger.\n'
    '    check["Transfer check"]\n    calculation["Transfer calculation"]\n    ledger["Ledger"]\n'
    '    check -->|exercises| calculation\n'
    '    calculation -->|reads balances from| ledger',
    [promise('module.ledger')],
    requirements='### req.transfer.pure — Transfers store nothing\n\n'
    'transfer SHALL NOT alter any stored balance.\n')

LEDGER = module_document('document.ledger.api','module.ledger','Ledger API',
    'The ledger Module stores account balances and answers one read per account identity.',
    '### scenario.ledger.read — A stored account returns its balance\n\n'
    '- GIVEN an account with a stored balance\n'
    '- WHEN read(account_id) is called\n'
    '- THEN it returns that integer balance\n\n'
    '### scenario.ledger.unknown — An unknown identity is an explicit failure\n\n'
    '- GIVEN no stored balance for the requested identity\n'
    '- WHEN read(account_id) is called\n'
    '- THEN it raises KeyError\n',
    ('Accounts map to integer balances held by the balance store.',
     [{'id':'entity.ledger.account','title':'Account','kind':'concept',
       'responsibility':'Identifies exactly one stored balance.'},
      {'id':'entity.ledger.store','title':'Balance store','kind':'data store',
       'responsibility':'Maps account identities to integer balances and rejects unknown ones.',
       'files':['app/ledger.py']}]),
    'An account identity indexes the balance store. Unknown identity is an explicit lookup failure.',
    'flowchart TB\n'
    '    accTitle: Ledger API\n'
    '    accDescr: An account identity indexes the balance store, which answers with an integer balance or an explicit failure.\n'
    '    account["Account"]\n    store["Balance store"]\n'
    '    account -->|indexes| store')

PROMISES = (block('concorde-document', {'id':'document.transfer.promises',
    'owner': 'service.transfer','main_visible':True})
    + '\n# Local promises\n\nBalance and amount are integers. No network, persistence or implicit\n'
      'retry is performed by transfer. This complete collection defines all facts required to\n'
      'implement and test transfer.\n')


def project(root):
    apply_project_proposal(root, PACKAGE, project_proposal(root, PACKAGE, 'Bank', CONFIGURATION, 'scope.bank'))
    targets=[empty_target('scope.bank','module','Banking',['specs/bank/module.md']),
             empty_target('scope.audit','module','Audit',['specs/audit/module.md']),
             empty_target('service.transfer','module','Transfers',['specs/transfer/module.md','specs/transfer/promises.md']),
             empty_target('module.ledger','module','Ledger',['specs/ledger/module.md'])]
    targets[0]['uses']=['service.transfer','module.ledger','scope.audit']
    targets[1]['uses']=['service.transfer']
    targets[2].update(uses=['module.ledger'], files=['app/transfer.py','checks/transfer_check.py'],
                      checks=['check.transfer'])
    targets[3].update(files=['app/ledger.py'])
    registry={'schema_version':4,'project_id':'project.bank','entry_target':'scope.bank','targets':targets,
      'checks':[{'id':'check.transfer','target_id':'service.transfer',
                 'argv':['{python}','checks/transfer_check.py'],'timeout_seconds':10}]}
    (root/'.concorde/specs.json').write_text(json.dumps(registry))
    files={'specs/bank/module.md':BANK,
      'specs/audit/module.md':AUDIT,
      'specs/transfer/module.md':TRANSFER,
      'specs/transfer/promises.md':PROMISES,
      'specs/ledger/module.md':LEDGER,
      'app/transfer.py':'# TRANSFER_IMPLEMENTATION_CODE\ndef transfer(balance, amount):\n    return balance\n',
      'app/ledger.py':'# LEDGER_IMPLEMENTATION_CODE\ndef read(account_id):\n    raise KeyError(account_id)\n',
      'checks/transfer_check.py':'import sys\nfrom pathlib import Path\nsys.path.insert(0,str(Path.cwd()))\nfrom app.transfer import transfer\nassert transfer(100,20)==80\nfor balance,amount in [(10,20),(10,0),(10,-1)]:\n    try: transfer(balance,amount)\n    except ValueError: pass\n    else: raise AssertionError("invalid transfer accepted")\n',
      'secret.py':'PRIVATE_CODE_MUST_NOT_ENTER_SPEC_CONTEXT = True\n'}
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
        from concorde.harness.permissions import runtime_bootstrap_file
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
                     for item in snapshot['spec_resolution']['sources']}
            target=snapshot['target']
            candidate={path:target['id'] for path in target['documents']}
            def initial(path):
                document_id='document.'+re.sub(r'[^a-z0-9.-]+','-',path.lower().removesuffix('.md').replace('/','.'))
                local=target['id'].split('.')[-1]
                entities=[{'id':f'entity.{local}.boundary','title':'Provisional boundary','kind':'concept',
                           'responsibility':'Holds the provisional responsibility of '+target['id']+'.'},
                          {'id':f'entity.{local}.developer','title':'Developer','kind':'external actor',
                           'responsibility':'Supplies the intended behavior of '+target['id']+'.'}]
                entities.extend({'id':f'entity.{local}.uses-'+peer.split('.')[-1],'title':peer,
                    'kind':'module','responsibility':'Supplies the capability '+target['id']+' relies on.',
                    'target_id':peer} for peer in target['uses'])
                lines=[f'    n{index}["{item["title"]}"]' for index,item in enumerate(entities)]
                lines.append('    n1 -->|specifies| n0')
                lines.extend(f'    n0 -->|depends on| n{index}' for index in range(2,len(entities)))
                diagram=('flowchart TB\n    accTitle: '+target['title']+'\n'
                    '    accDescr: The developer specifies the provisional boundary of this target and its declared providers.\n'
                    + '\n'.join(lines))
                dependencies=[{'target_id':peer,
                    'responsibility':'Supplies the capability '+target['id']+' relies on.',
                    'selection_condition':'Select for work about '+peer+'.',
                    'relied_upon_promises':['The provider keeps the promises its own Spec states.']}
                    for peer in target['uses']]
                return module_document(document_id,target['id'],target['title'],
                    'Stable target ID: '+target['id']+'. '+snapshot['task'],
                    f'### scenario.{local}.provisional — The provisional boundary is recorded\n\n'
                    '- GIVEN the accepted topology change\n'
                    '- WHEN the developer supplies this target\n'
                    '- THEN its provisional boundary is recorded without inventing behavior\n',
                    ('The provisional boundary and its declared providers are the only known entities.', entities),
                    'The developer specifies the provisional boundary; declared providers remain external.',
                    diagram, dependencies).replace(
                        json.dumps({'id':document_id,'owner':target['id'],'main_visible':True},indent=2),
                        json.dumps({'id':document_id,'owner':candidate[path],'main_visible':True},indent=2))
            documents=[{'path':path,'content':current.get(path,initial(path))}
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
            data={'context_id':snapshot['context_id'],'outcome':'completed','answer':'Main answered from complete Spec contexts.',
                  'expand_targets':[],'routes':[],'gaps':[],'topology_design':None}
            if stage=='route':
                hint=snapshot['target_hint']
                discovered=[item['target_id'] for item in snapshot['targets']]
                if snapshot['action']=='ask':
                    target=hint or 'service.transfer'
                    if target not in discovered:
                        data.update(outcome='expand',expand_targets=[target])
                elif hint:
                    data.update(outcome='routed',routes=[{'target_id':hint,'focus_id':snapshot['focus_hint'],
                        'task':snapshot['task'],'constraints':snapshot['constraints']}])
                elif 'service.transfer' not in discovered:
                    data.update(outcome='expand',expand_targets=['service.transfer'])
                else:
                    data.update(outcome='routed',routes=[{'target_id':'service.transfer','focus_id':None,
                        'task':snapshot['task'],'constraints':snapshot['constraints']}])
            if snapshot['capability'] != 'concorde-main':
                data['routes'] = [{k: v for k, v in route.items() if k in ('target_id', 'focus_id')}
                                  for route in data['routes']]
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
                    for item in snapshot['spec_resolution']['sources'])
                dependencies=re.search(r'```concorde-dependencies\s*\n(.*?)^```',body,re.M|re.S)
                if dependencies is None:raise AssertionError('Module task fixture requires local participant declarations')
                task_target=json.loads(dependencies.group(1))[0]['target_id']
            data['tasks']=[{'id':'task.transfer','target_id':task_target,
            'description':'Implement the transfer promise.','acceptance':'Valid transfer subtracts; invalid amount or insufficient funds raises ValueError.','complete':False}]
        if stage=='implementation' and snapshot['stage_inputs'][0]['type_id']=='concorde-implementation-task':
            if snapshot['target_id']=='module.ledger':
                (Path(cwd)/'app/ledger.py').write_text('# LEDGER_IMPLEMENTATION_CODE\ndef read(account_id):\n    balances = {"known": 100}\n    return balances[account_id]\n')
            else:
                (Path(cwd)/'app/transfer.py').write_text('# TRANSFER_IMPLEMENTATION_CODE\ndef transfer(balance, amount):\n    if amount <= 0 or amount > balance:\n        raise ValueError("invalid transfer")\n    return balance - amount\n')
            task_input=snapshot['stage_inputs'][0]['data']
            data['tasks']=[{**task,'complete':True} for task in task_input['tasks']]
        if self.callback: self.callback(stage, snapshot, data, Path(cwd))
        payload={key:item['const'] for key,item in properties.items() if 'const' in item}
        payload.update(status='success',output='Explicit model-process double.',limitations='none',
          gates=[{'name':'bounded-role','status':'passed','evidence':'Model process is substituted; host, checks and completion validation are real.'}],
          domain_output=typed('concorde-agent-stage-result',data))
        stdout=json.dumps({'structured_output':payload}) if '--json-schema' in argv else '\n'.join(json.dumps(event) for event in [{'type':'item.completed','item':{'type':'agent_message','text':json.dumps(payload)}},{'type':'turn.completed'}])
        return subprocess.CompletedProcess(argv,0,stdout,'')
