"""Reflection coordination: code stays in a fresh implementation invocation."""
import importlib.util
import json
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path
from ..spec.typed_data import typed, artifact, canonical
from ..spec.repository import SpecError, read_file, digest
from .investigation import apply_investigation


def queue_module(package):
    name="concorde_reflections_queue_host"
    spec=importlib.util.spec_from_file_location(name,package/"scripts/reflections_queue.py")
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module


def triage(run):
    from ..development.capability_host import Invocation, invoke_capability, _implementation_digest
    from ..harness.change_worktree import progress, read_change, target_state
    root=run.repository.root;queue=queue_module(run.host.package_root)
    action=run.task["action"];ids=run.task["reflection_ids"]
    if action == "record-gaps":
        return record_gaps(run, queue)
    if run.task.get("gap_ids"):
        raise SpecError("gap_ids are only accepted by record-gaps", "invalid_input")
    _,_,parsed,_,raw=queue._load_reflections(root,required=True)
    entries={entry.identifier:entry for entry in parsed.entries}
    # A reflection is attributed to a Module or one of its scenarios; entities and requirements
    # locate text inside a Module and are not separate attribution identities.
    local={run.target.id,*(scenario.id for scenario in run.repository.scenarios(run.target))}
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
        result["data"]["gap_records"] = gap_records(run)
        return result
    if action in {"close","merge"}:
        (queue.remove_closed if action=="close" else queue.remove_merged)(root,ids)
        return run.response(answer="Eligible records removed; Git history retains their disposition.")
    progress(root, phase="reflection_investigation", status="active", invalidate=True)
    if not run.target.files:
        return run.response("unsupported","Select a Module whose entities list implementation files before code investigation.")
    head=queue._captured_head(root);before=_implementation_digest(run.repository,run.target)
    selection=typed("concorde-reflection-selection",{"head":head,"records":[
        {"id":i,"path":entries[i].path,"digest":digest(raw[entries[i].path]),"content":raw[entries[i].path].decode()} for i in ids]})
    result=run.stage("concorde-implement",inputs=(selection,),mode="investigation",readonly=True,defer_gap_resolution=True)
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
    run.record_gaps("implementation", [])
    if action=="implement":
        for f in findings:
            # Only intended behavior is a task input. Investigation prose, source, evidence and
            # logs must not contaminate specification/planning cognition.
            child_host=replace(run.host,routed_target=run.target.id,coordinated=True)
            child=invoke_capability(run.capability,"concorde-dev-loop",run.configuration,
                typed("concorde-dev-loop-request",{"target_id":run.target.id,"task":f["resolution"],
                    "specify":True}),child_host)
            if child["status"]!="succeeded":
                if child["output"]:
                    data=child["output"]["data"]
                    return run.response(data["outcome"],data["answer"],gaps=data["gaps"],artifacts=data["artifacts"])
                raise SpecError("reflection implementation failed admission", "child_blocked")
            queue.update_plan(root,f["reflection_id"],["status=implemented"])
        change = read_change(root, required=True)
        state = target_state(root, run.target.id, run.task.get("focus_id"))
        payload = {"target_id": run.target.id, "task": state["task"],
                   "constraints": state.get("constraints", []), "change_id": change["change_id"]}
        if run.task.get("focus_id"):
            payload["focus_id"] = run.task["focus_id"]
        verified = Invocation("concorde-validate", run.configuration, payload,
                              replace(run.host, coordinated=False)).validate()
        data = verified["data"]
        return run.response(data["outcome"], "Reflection implementation completed in the candidate worktree. "
                            + data["answer"], checks=data["checks"], gaps=data["gaps"])
    return run.response(answer="Reflection investigation persisted"+(" and component implementation completed in the candidate worktree." if action=="implement" else "."))


def record_gaps(run, queue):
    """Explicitly promote selected existing gaps, preserving their actual owners."""
    from ..harness.change_worktree import read_change, save_change
    from ..spec.changes import apply_files, file_change
    from .reflections import parse_reflection_document
    ids = run.task.get("gap_ids", [])
    if not ids or run.task["reflection_ids"]:
        raise SpecError("record-gaps requires explicit gap_ids and empty reflection_ids", "invalid_input")
    root = run.repository.root
    state = read_change(root, required=True)
    gaps = {item["id"]: item for item in state.get("gap_history", [])}
    selected = []
    for identifier in ids:
        item = gaps.get(identifier)
        if not item or item["status"] != "open":
            raise SpecError("selected gap is missing or resolved", "stale_reference")
        target = run.repository.select(item["target_id"])
        allowed = {run.target.id, *run.target.uses,
                   *(child.id for child in run.repository.children(run.target))}
        if target.id not in allowed:
            raise SpecError("selected gap belongs to another target", "permission_denied")
        selected.append((item, target))
    _, _, parsed, _, _ = queue._load_reflections(root, required=True)
    entries = {entry.identifier: entry for entry in parsed.entries}
    reflections = []
    for item, target in selected:
        identifier = item.get("reflection_id")
        if identifier:
            if identifier not in entries or entries[identifier].feature != target.id:
                raise SpecError("linked reflection is missing or has a different owner", "stale_reference")
            entry = entries[identifier]
            reflections.append({"id": identifier, "target_id": target.id, "status": entry.status,
                "triage": entry.triage, "bucket": entry.bucket, "plan_status": None, "verification": None})
            continue
        allocated = queue.allocate_id(root)
        identifier = allocated["allocated_id"]
        path = allocated["reflection_path"]
        gap = item["gap"]
        phase = {"implementation": "implement", "spec-review": "analyze", "code-review": "analyze",
                 "specify": "analyze", "context-solve": "analyze"}.get(item["phase"], item["phase"])
        title = "Missing contract: " + gap["needed_contract"].replace("\n", " ")[:180]
        today = date.today().isoformat()
        metadata = {"id": identifier, "title": title, "phase": phase, "date": today,
            "feature": target.id, "kind": "specification", "concerns": target.primary_document,
            "status": "open"}
        front = "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items())
        content = (f"---\n{front}\n---\n\n# {identifier} · {title}\n\n"
            f"## Context\n\nTask for {target.id}: {item['task']}\n\n"
            f"## Expected\n\nThe admitted collection supplies: {gap['needed_contract']}\n\n"
            f"## Observed\n\n{gap['question']}\n\n"
            f"## Impact\n\nThe dependent step remains paused: {gap['blocked_step']}\n\n"
            f"## Evidence\n\nCaptured gap {item['id']} from context {gap['context_id']}, "
            f"phase {item['phase']}, change {state['change_id']}. This is a reported gap awaiting investigation.\n\n"
            + "Source ownership and inclusion evidence: " + canonical(item.get("context_evidence", {})) + "\n\n"
            "## Triage Analysis\n\n## Proposed Resolution\n\n## Intervention Rationale\n\n"
            "## User Comments\n\n## Occurrences\n\n"
            f"- {phase} {today} {target.id} — {gap['blocked_step']}\n")
        _, problems = parse_reflection_document(content, path)
        if problems:
            raise SpecError("captured gap does not form a valid reflection", "invalid_completion")
        apply_files(root, [file_change(root, path, content)], {path})
        item["reflection_id"] = identifier
        # Save each link before another allocation, so retries retain identity.
        state["validated_tree"] = None
        state["validation"] = None
        save_change(root, state)
        reflections.append({"id": identifier, "target_id": target.id, "status": "open",
            "triage": "pending", "bucket": "pending", "plan_status": None, "verification": None})
    result = run.response(answer="Selected gaps recorded in the existing Reflection queue; dependent steps remain paused.")
    result["data"]["reflections"] = reflections
    result["data"]["gap_records"] = gap_records(run)
    return result


def gap_records(run):
    """Public selection metadata around the existing gap contract, without source reads."""
    from ..harness.change_worktree import read_change
    state = read_change(run.repository.root)
    result = []
    for item in (state or {}).get("gap_history", []):
        target = run.repository.select(item["target_id"])
        allowed = {run.target.id, *run.target.uses,
                   *(child.id for child in run.repository.children(run.target))}
        if target.id in allowed:
            result.append({key: item[key] for key in ("id", "target_id", "task", "phase", "gap", "status")}
                          | {"reflection_id": item.get("reflection_id")})
    return result
