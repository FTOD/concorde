"""Reflection coordination: code stays in a fresh implementation invocation."""
import importlib.util
import sys
from datetime import date
from pathlib import Path
from ..capabilities.operation_data import typed, artifact
from ..specification.repository import SpecError, read_file, digest
from .investigation import apply_investigation


def queue_module(package):
    name="concorde_reflections_queue_host"
    spec=importlib.util.spec_from_file_location(name,package/"scripts/reflections_queue.py")
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module


def triage(run):
    from ..capabilities.scoped_operations import run_operation, _implementation_digest
    root=run.repository.root;queue=queue_module(run.host.package_root)
    action=run.task["action"];ids=run.task["reflection_ids"]
    _,_,parsed,_,raw=queue._load_reflections(root,required=True)
    entries={entry.identifier:entry for entry in parsed.entries}
    local={run.target.id,*(x["id"] for x in (*run.target.features,*run.target.apis))}
    selected=ids or [entry.identifier for entry in parsed.entries if entry.feature in local]
    if any(i not in entries or entries[i].feature not in local for i in selected):
        raise SpecError("selected reflection does not belong to this target", "permission_denied")
    if action!="status" and not ids:
        raise SpecError("mutating triage requires explicit reflection_ids", "invalid_input")
    if action=="status":
        plans=queue._load_plans(root,queue.load_config(root));head=queue._head_or_none(root)
        result=run.response(answer="Selected reflection metadata.")
        result["data"]["reflections"]=[{"id":i,"target_id":run.target.id,"status":entries[i].status,
            "triage":entries[i].triage,"bucket":entries[i].bucket,
            "plan_status":plans[i]["status"] if i in plans else None,
            "verification":queue._verification_state(plans[i],head) if i in plans else None} for i in selected]
        return result
    if action in {"close","merge"}:
        (queue.remove_closed if action=="close" else queue.remove_merged)(root,ids)
        return run.response(answer="Eligible records removed; Git history retains their disposition.")
    if run.target.kind=="domain":
        return run.response("unsupported","Domain scopes do not own implementation code; select a participating Service or Module before investigation.")
    head=queue._captured_head(root);before=_implementation_digest(run.repository,run.target)
    selection=typed("concorde-reflection-selection",{"head":head,"records":[
        {"id":i,"path":entries[i].path,"digest":digest(raw[entries[i].path]),"content":raw[entries[i].path].decode()} for i in ids]})
    result=run.stage("concorde-implement",inputs=(selection,),readonly=True)
    if result["outcome"] not in {"completed","sufficient"}:
        return run.response(result["outcome"],result["answer"],gaps=result["gaps"])
    if _implementation_digest(run.repository,run.target)!=before:
        raise SpecError("read-only investigation modified code", "permission_denied")
    findings=result.get("reflection_findings",[])
    owned=set(run.repository.implementation_files(run.target))
    if any(path not in owned for f in findings for path in f["files"]):
        raise SpecError("reflection resolution crosses component ownership", "permission_denied")
    if any(read_file(root,entries[i].path)!=raw[entries[i].path] for i in ids):
        raise SpecError("reflection changed during investigation", "stale_reference")
    routes={f["route"] for f in findings}
    if action=="implement" and len(routes)!=1:
        raise SpecError("one implementation action requires a consistent resolution route", "incompatible_handoff")
    # The existing record parser/persistence contract remains host-private. None of these legacy
    # artifact adapters are admitted to the next Spec-only agent context.
    runtime={"data":{"head":head,"verified_on":date.today().isoformat(),
        "task":{"data":{"reflection_ids":ids,"action":action,"feature_path":run.target.documents[0],
                         "route":next(iter(routes),"blocked")}},
        "artifacts":[artifact(root,i,entries[i].path) for i in ids]}}
    apply_investigation(root,queue,runtime,typed("concorde-reflection-investigation-result",{"findings":findings}),
                        entries,concorde_project=(root/"concorde.json").is_file())
    if action=="implement":
        for f in findings:
            # Only intended behavior is a task input. Investigation prose, source, evidence and
            # logs must not contaminate specification/planning cognition.
            child=run_operation("concorde-standard-dev-loop",run.configuration,
                typed("concorde-standard-dev-loop-request",{"target_id":run.target.id,"task":f["resolution"]}),host_context=run.host)
            if child["status"]!="succeeded":
                if child["output"]:
                    data=child["output"]["data"]
                    return run.response(data["outcome"],data["answer"],gaps=data["gaps"],artifacts=data["artifacts"])
                raise SpecError("reflection implementation failed admission", "child_blocked")
            queue.update_plan(root,f["reflection_id"],["status=implemented"])
    return run.response(answer="Reflection investigation persisted"+(" and implementation delivered." if action=="implement" else "."))
