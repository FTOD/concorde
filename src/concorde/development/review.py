"""Independent, target-bound reviews and their existing-change lifecycle evidence.

Only the host reads Git objects, creates capsules and persists receipts. Reviewers
get immutable scoped inputs and zero project write authority in either mode.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import subprocess
import tempfile
import uuid
from dataclasses import asdict, replace
from pathlib import Path

from ..harness.change_worktree import git, git_value, progress, read_change, save_change, workspace_identity
from ..spec.typed_data import artifact, canonical, checked_path, typed, validate_typed, verify_artifacts
from .configuration import load_configuration
from ..harness.agent_model import ContractError, agent_definition
from ..harness.worker_executor import CapabilityExecutionError, WorkerOutcome
from ..harness.permissions import PermissionPolicyError, PolicyBinding, compile_policy
from ..spec.contracts import REVIEW_STAGES
from ..distribution.build import load_agent
from ..harness.context import (context_documents, materialize_documents, materialize_references,
                               recheck_context, reference_grants, resolve_context)
from ..harness.usage import record_usage
from ..spec.repository import SpecError, SpecRepository, bound_by, digest, read_file


def _changes(repository, target, mode, baseline) -> list[dict]:
    """Read history only for the current grant; never admit a project-wide diff."""
    spec_paths = repository.spec_files(target.id)
    # Directory entries scope history by their base path; only the files they bind are admitted.
    entries = spec_paths if mode == "spec" else repository.implementation_entries(target)
    roots = spec_paths if mode == "spec" else repository.implementation_paths(target)
    current = set(spec_paths if mode == "spec" else repository.implementation_files(target))
    previous = {}
    if baseline and roots:
        tree = git_value(repository.root, "--literal-pathspecs", "ls-tree", "-r", "-z", baseline, "--", *roots)
        for entry in tree.split("\0"):
            if not entry:
                continue
            header, path = entry.split("\t", 1)
            _, kind, oid = header.split()
            if kind == "blob" and any(bound_by(item, path) for item in entries):
                previous[path] = oid
    changes = []
    for path in sorted(current | previous.keys()):
        after = ((repository.document_overrides[path] if path in repository.document_overrides
                  else read_file(repository.root, path)) if path in current else b"")
        oid = previous.get(path)
        if oid and path in current:
            git_digest = hashlib.new("sha1" if len(oid) == 40 else "sha256",
                b"blob " + str(len(after)).encode() + b"\0" + after).hexdigest()
            if git_digest == oid:
                continue
        before = (subprocess.run(("git", "cat-file", "blob", oid), cwd=repository.root,
                  capture_output=True, check=True).stdout if oid else b"")
        if before == after and (path in current) == bool(oid):
            continue
        if b"\0" in before or b"\0" in after:
            patch = f"Binary change: {digest(before)} -> {digest(after)}"
        else:
            patch = "".join(difflib.unified_diff(before.decode(errors="replace").splitlines(keepends=True),
                after.decode(errors="replace").splitlines(keepends=True),
                fromfile=path if oid else "/dev/null", tofile=path if path in current else "/dev/null"))
        changes.append({"path": path, "patch": patch or "Empty file membership changed."})
    return changes


def inputs(run, mode: str) -> tuple[dict, object]:
    from .capability_host import _target_revision, _implementation_digest
    repository = (run.repository if getattr(run, "candidate_review", False) else
                  SpecRepository(run.repository.root, run.host.package_root))
    target = repository.select(run.target.id, run.task.get("focus_id"))
    if mode not in REVIEW_STAGES:
        raise SpecError("review_mode must be spec or code", "invalid_input")
    if mode == "code" and not target.files:
        raise SpecError("code review requires a Module whose entities list implementation files", "unsupported_target")
    phase, role = REVIEW_STAGES[mode]
    prompt = load_agent(run.host.package_root, role)
    change = read_change(repository.root)
    _, current = workspace_identity(repository.root)
    head = current["head"] if current else None
    baseline = change["base_commit"] if change else head
    revision = {"spec_digest": _target_revision(repository, target),
        "implementation_digest": _implementation_digest(repository, target) if mode == "code" else None,
        "baseline": baseline, "head": head}
    changes = _changes(repository, target, mode, baseline)
    identity = {"target_id": run.target.id, "focus_id": run.task.get("focus_id"),
        "project_root": str(repository.root), "branch": current["branch"] if current else None,
        "task": run.task["task"], "constraints": run.task.get("constraints", []),
        "change_id": run.change_id, "review_mode": mode, "revision": revision, "changes": changes,
        "instructions": prompt.body, "role_effects": asdict(prompt.effects),
        "agent_binding_digest": prompt.binding.digest,
        "host_runtime": {path: digest(read_file(run.host.package_root, path)) for path in (
            "src/concorde/development/review.py", "src/concorde/development/capability_host.py",
            "src/concorde/development/capability_flow.py", "src/concorde/development/dispatch_flow.py",
            "src/concorde/development/discovery_flow.py", "src/concorde/development/target_flow.py",
            "src/concorde/development/coordination_flow.py", "src/concorde/development/loop_flow.py",
            "src/concorde/development/specify_flow.py",
            "src/concorde/harness/worker_executor.py", "src/concorde/harness/pi_worker.py",
            "src/concorde/harness/permissions.py", "src/concorde/harness/context.py",
            "src/concorde/harness/batch_flow.py")},
        "configuration": run.configuration}
    return {"review_mode": mode, "input_digest": digest(identity), "revision": revision, "changes": changes}, prompt


def _empty(run, info, status, answer) -> dict:
    return typed("concorde-review-result", {"context_id": None, "input_digest": info["input_digest"],
        "review_mode": info["review_mode"], "status": status, "representative_tasks": [],
        "findings": [], "gaps": [], "answer": answer, "target_id": run.target.id,
        "focus_id": run.task.get("focus_id"), "revision": info["revision"],
        "semantic_completeness": "not_proven"})


def _persist(run, value, *, execution=None, failure=None) -> dict:
    """Host run records are separate from the reviewer's empty write grant."""
    mode = value["data"]["review_mode"]
    path = f".concorde/runs/{run.host.invocation_id}/review-{run.target.id}-{mode}-{uuid.uuid4()}.json"
    destination = checked_path(run.repository.root, path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(canonical(value) + "\n")
    reference = artifact(run.repository.root, f"review.{run.target.id}.{mode}", path)
    if execution is not None or failure is not None:
        # The worker's reported usage and any execution failure stay host records beside the review.
        private = destination.with_suffix(".execution.json")
        private.write_text(canonical({"usage": asdict(execution) if execution else None,
                                      "failure": failure}) + "\n")
    state = None if getattr(run, "candidate_review", False) else read_change(run.repository.root)
    if state is not None:
        intent = {"task": run.task["task"], "focus_id": run.task.get("focus_id"),
                  "constraints": run.task.get("constraints", [])}
        expected = state.get("review_intents", {}).get(run.target.id)
        if expected is not None and expected != intent:
            return reference
        state.setdefault("reviews", {}).setdefault(run.target.id, {})[mode] = {
            "artifact": reference, "input_digest": value["data"]["input_digest"],
            "status": value["data"]["status"], "task": run.task["task"],
            "focus_id": run.task.get("focus_id"), "constraints": run.task.get("constraints", [])}
        if state.get("review_requirements", {}).get(run.target.id, {}).get(mode):
            # Only lifecycle-required review supersedes the candidate's ready
            # receipt. Standalone queries may record unrelated review evidence.
            state["validated_tree"] = None
            if state["status"] == "ready":
                state.update(status="active", phase=mode + "-review", outcome=None)
        save_change(run.repository.root, state)
    return reference


def _validate(run, snapshot, info, data):
    if (data["context_id"] != snapshot.id or data["input_digest"] != info["input_digest"]
            or data["review_mode"] != info["review_mode"]):
        raise SpecError("review identities differ from admitted input", "incompatible_handoff")
    findings, gaps = data["findings"], data["gaps"]
    if not data["answer"].strip() or any(not task.strip() for task in data["representative_tasks"]):
        raise SpecError("review answer and covered tasks must be meaningful nonblank text", "invalid_completion")
    if len({finding["id"] for finding in findings}) != len(findings):
        raise SpecError("review finding IDs must be unique", "invalid_completion")
    if data["status"] == "no_findings" and (findings or gaps):
        raise SpecError("no_findings review cannot contain findings or gaps", "invalid_completion")
    if data["status"] == "findings" and not (findings or gaps):
        raise SpecError("findings review requires concrete findings or gaps", "invalid_completion")
    if data["status"] != "incomplete" and not data["representative_tasks"]:
        raise SpecError("completed review requires representative task coverage", "invalid_completion")
    spec_paths = set(run.repository.spec_files(run.target.id))
    allowed = set(spec_paths)
    if info["review_mode"] == "code":
        allowed.update(run.repository.implementation_files(run.target))
        allowed.update(item["path"] for item in info["changes"])
    for finding in findings:
        if any(not finding[key].strip() for key in ("id", "contract", "problem", "affected_task")):
            raise SpecError("review findings require nonblank evidence and an affected task", "invalid_completion")
        if (finding["document"] not in spec_paths
                or finding["target_id"] != run.repository.document(finding["document"]).owner
                or finding["location"]["path"] not in allowed):
            raise SpecError("review finding crosses target authority", "permission_denied")
        if (info["review_mode"] == "spec" and finding["severity"] == "blocking"
                and not any(gap["blocked_step"] == finding["affected_task"]
                            and gap["needed_contract"] == finding["contract"] for gap in gaps)):
            raise SpecError("blocking Spec finding requires its concrete gap", "invalid_completion")
    for gap in gaps:
        if any(not gap[key].strip() for key in ("question", "blocked_step", "needed_contract")):
            raise SpecError("review gaps require a concrete question, step and contract", "invalid_completion")
        if (gap.get("target_id", run.target.id) != run.target.id
                or gap.get("context_id", snapshot.id) != snapshot.id):
            raise SpecError("review gap provenance differs from context", "incompatible_handoff")
        gap.update(target_id=run.target.id, context_id=snapshot.id)


def review(run, mode: str) -> dict:
    """Run exactly one reviewer; no prior review, transcript or code crosses modes."""
    from .capability_host import (_check_service, _protocol_documents, _run_worker, _worker_description,
                                  _worker_invocation)
    info, prompt = inputs(run, mode)
    phase, role = REVIEW_STAGES[mode]
    agent = agent_definition(prompt.binding.agent)
    snapshot = resolve_context(run.repository, run.target.id, phase=phase, task=run.task["task"],
        focus_id=run.task.get("focus_id"), constraints=tuple(run.task.get("constraints", [])),
        instructions=prompt.body, agent=agent)
    run.last_context = snapshot.id
    pending = run.pending_gaps(phase, snapshot, review_input_digest=info["input_digest"])
    if pending and run.host.track_gaps:
        value = _empty(run, info, "not_run", "Repair the recorded necessary contracts before resuming review.")
        reference = _persist(run, value)
        return run.response("spec_incomplete", value["data"]["answer"], gaps=pending,
                            artifacts=[reference], reviews=[value])
    result = None
    try:
        with tempfile.TemporaryDirectory(prefix="concorde-review-") as directory:
            project_workspace = agent.workspace == "project"
            project = run.repository.root if project_workspace else Path(directory)
            relative = (f".concorde/runs/{run.host.invocation_id}/{uuid.uuid4()}/context.json"
                        if project_workspace else "context.json")
            capsule = checked_path(project, relative)
            value = typed("concorde-review-stage-context", {
                "snapshot": typed("concorde-context-snapshot", snapshot.value),
                "review": typed("concorde-review-input", info)})
            serialized = canonical(value) + "\n"
            if run.host.mode != "describe-policy":
                capsule.parent.mkdir(parents=True, exist_ok=True)
                capsule.write_text(serialized)
            granted = context_documents(run.repository, snapshot.value)
            if not project_workspace and run.host.mode != "describe-policy":
                materialize_documents(project, granted)
            roles = {"spec-context": (relative, *sorted(granted))}
            if project_workspace:
                roles["implementation"] = tuple(run.repository.implementation_files(run.target))
            if "references" in prompt.effects.reads:
                records = snapshot.value["external_references"]
                if not project_workspace and run.host.mode != "describe-policy":
                    materialize_references(run.repository, project, records)
                roles["references"] = reference_grants(records)
            binding = PolicyBinding("concorde-review", phase, 0, role, role, write_roles=())
            try:
                policy = compile_policy(prompt.effects, binding, roles)
            except PermissionPolicyError as error:
                raise SpecError(str(error), "permission_denied") from error
            if policy.write_paths:
                raise SpecError("review role must have no write authority", "permission_denied")
            receipt = {"schema_version": 15, "target_id": run.target.id, "phase": phase,
                "context_id": snapshot.id, "source_digest": snapshot.id, "input_digest": info["input_digest"],
                "role_paths": {key: list(paths) for key, paths in roles.items()}}
            invocation = _worker_invocation(run.configuration, capability="concorde-review", stage=phase,
                prompt=prompt, workspace=project, context_value=value, receipt=receipt, policy=policy,
                protocol=_protocol_documents(snapshot.value, granted))
            run.host.descriptions.append(_worker_description(prompt, invocation, policy,
                capability="concorde-review", phase=phase, context_id=snapshot.id,
                input_digest=info["input_digest"], project_root=str(project)))
            if run.host.mode == "describe-policy":
                return run.response("described", reviews=[_empty(run, info, "not_run", "Policy described; review not run.")])
            from ..harness.agent_node import AgentNode
            checks = _check_service(run.repository, run.target, run.host.invocation_id) if project_workspace else None

            def launch_reviewer(context):
                nonlocal result
                result, data = _run_worker(run.host, invocation, prompt, capability="concorde-review",
                                           stage=phase, target_id=run.target.id,
                                           result_type="concorde-review-stage-result", checks=checks)
                return data

            data = AgentNode(agent).invoke(value, launch_reviewer)
            _validate(run, snapshot, info, data)
            recheck_context(run.repository, snapshot)
            if inputs(run, mode)[0] != info or load_configuration(run.repository.root) != run.configuration:
                raise SpecError("review inputs changed while the reviewer was running", "stale_context")
            if capsule.read_text() != serialized:
                raise SpecError("review capsule changed", "stale_context")
            reviewed = typed("concorde-review-result", {**data, "target_id": run.target.id,
                "focus_id": run.task.get("focus_id"), "revision": info["revision"],
                "semantic_completeness": "not_proven"})
            reference = _persist(run, reviewed, execution=result.usage)
            if (data["status"] != "incomplete" and (data["gaps"]
                    or not any(f["severity"] == "blocking" for f in data["findings"]))):
                run.record_gaps(phase, data["gaps"], review_input_digest=info["input_digest"])
            run.host.evidence.append(result)
            run.completed.append("concorde-review")
            outcome = ("failed" if data["status"] == "incomplete" else
                       "spec_incomplete" if data["gaps"] else
                       "conflicting" if any(f["severity"] == "blocking" for f in data["findings"]) else "completed")
            return run.response(outcome, data["answer"], gaps=data["gaps"], artifacts=[reference], reviews=[reviewed])
    except Exception as error:
        if run.host.mode != "execute":
            # A failed preview has no execution or persistence authority.
            raise
        # Failures remain failures even when the model supplied no findings.
        if isinstance(error, CapabilityExecutionError):
            code = error.code or ("execution_cancelled" if error.outcome == "cancelled" else
                   "execution_limit" if error.outcome == "limit_exhausted" else "execution_failed")
            lifecycle_status = ("cancelled" if error.outcome == "cancelled" else
                                "limit_exhausted" if error.outcome == "limit_exhausted" else "failed")
            run.host.lifecycle["status"] = lifecycle_status
            if lifecycle_status in {"cancelled", "limit_exhausted"}:
                run.host.lifecycle["execution_error"] = code
            # concorde-review is never mutation-classified (record_progress excludes it), so a
            # standalone review's own executor failure would otherwise leave the change status
            # untouched; a cancelled/limit-exhausted executor outcome is host bookkeeping, not a
            # content judgment a read-only query should withhold.
            try:
                progress(run.repository.root, status=lifecycle_status)
            except (ValueError, OSError) as persistence_error:
                # The interruption evidence and the failed Review result still stand; the
                # enclosing capability reports the lost status write beside them.
                run.host.lifecycle["persistence_error"] = (
                    f"Could not persist reviewer execution status: {persistence_error}")
        else:
            code = error.code if isinstance(error, (SpecError, ContractError)) else "execution_failed"
        reviewed = _empty(run, info, "incomplete", f"Review could not complete ({code}).")
        failure = {"code": code, "message": str(error)}
        if run.host.lifecycle.get("persistence_error"):
            failure["persistence"] = run.host.lifecycle["persistence_error"]
        usage = result.usage if isinstance(result, WorkerOutcome) else getattr(error, "usage", None)
        reference = _persist(run, reviewed, execution=usage, failure=failure)
        return run.response("failed", reviewed["data"]["answer"], artifacts=[reference], reviews=[reviewed])


def spec_consumers(run) -> set[str]:
    """Current inclusion plus the retained old/candidate impact union."""
    state = read_change(run.repository.root) or {}
    selected = set(state.get("spec_context_impacts", {}).get(run.target.id, []))
    for path in run.target.documents:
        selected.update(run.repository.context_users(run.repository.document(path).document_id))
    selected.update(state.get("shared_spec_reviews", {}).get(run.target.id, {}))
    baseline = state.get("base_commit")
    if baseline:
        # Git objects from this candidate's declared base are host-only inputs. Never inspect
        # another worktree's project files to reconstruct old ownership or inclusion.
        raw = git(run.repository.root, "show", f"{baseline}:{run.repository.registry_path}", check=False)
        if raw.returncode == 0:
            from ..spec.typed_data import decode
            registry = decode(raw.stdout)
            overrides = {}
            for path in {path for target in registry["targets"] for path in target["documents"]}:
                result = subprocess.run(("git", "show", f"{baseline}:{path}"), cwd=run.repository.root,
                    capture_output=True, check=True)
                overrides[path] = result.stdout
            old = SpecRepository(run.repository.root, run.host.package_root,
                registry_bytes=raw.stdout.encode(), document_overrides=overrides)
            if run.target.id in old.targets:
                for path in old.select(run.target.id).documents:
                    selected.update(old.context_users(old.document(path).document_id))
    return selected & run.repository.targets.keys() - {run.target.id}


def consumer_intent(task: str) -> str:
    """The one review intent a Spec consumer is asked under, before and after the change applies."""
    return "Review this Module's reliance on the changed canonical Spec. " + task


def consumer_task(run, target_id):
    return {"target_id": target_id, "task": consumer_intent(run.task["task"]),
        "constraints": run.task.get("constraints", []), "change_id": run.change_id}


def changed_implementation_paths(run) -> list[str] | None:
    """The target's bound files that differ from the candidate base, or None when history is unknown."""
    change = read_change(run.repository.root)
    _, current = workspace_identity(run.repository.root)
    baseline = change.get("base_commit") if change else (current["head"] if current else None)
    if not baseline:
        return None
    return [item["path"] for item in _changes(run.repository, run.target, "code", baseline)]


def code_review_peers(run) -> tuple:
    """Modules whose entries cover a file of this target that actually changed in the candidate.

    P6 requires checks for every listing Module of a changed shared file, not of every shared
    file. Without a known base revision every covering Module is a peer.
    """
    changed = changed_implementation_paths(run)
    peers = (run.repository.covering_modules(run.target) if changed is None
             else run.repository.affected_modules(changed))
    return tuple(target for target in peers if target.id != run.target.id and target.files)


def _spec_scope_tasks(run, state, peers, *, include_components):
    """Derive both admitted Spec-scope variants from current caller/coordination intent."""
    coordination = ((state or {}).get("targets", {}).get(run.target.id, {}).get("coordination", {})
                    if include_components else {})
    tasks = {target_id: {**consumer_task(run, target_id), "task": record["task"]}
             for target_id, record in coordination.items()}
    for target_id in peers:
        tasks.setdefault(target_id, consumer_task(run, target_id))
    return tasks


def review_scope(run, mode: str) -> dict:
    """Review each using Module in a separate context after shared implementation changes."""
    change = read_change(run.repository.root)
    if mode == "spec":
        components = _spec_scope_tasks(run, change, spec_consumers(run),
                                       include_components=not run.host.track_gaps)
    else:
        work = (change or {}).get("targets", {}).get(run.target.id, {})
        components = dict(work.get("coordination", {}))
        for target in code_review_peers(run):
            components.setdefault(target.id, {"task":
                "Check this Module's own contract against the shared implementation change. " + run.task["task"]})
    outputs = []
    from .capability_host import invoke_capability
    affected_ids = {target.id for target in code_review_peers(run)}
    allowed = {run.target.id, *run.target.uses, *affected_ids, *spec_consumers(run),
               *(target.id for target in run.repository.covering_modules(run.target)),
               *(child.id for child in run.repository.children(run.target))}
    retained = ((change or {}).get("shared_spec_reviews", {}).get(run.target.id, {}) if mode == "spec"
                else (change or {}).get("shared_implementation_reviews", {}).get(run.target.id, {}))
    def review_module(item):
        if item is None:
            if not components or mode == "spec" or run.target.files:
                output = review(run, mode)["data"]
                outputs.append(output)
                if output["outcome"] not in {"completed", "described"}:
                    return output
            return None
        target_id, record = item
        if target_id == run.target.id:
            return None
        target = run.repository.select(target_id)
        if target.id not in allowed:
            raise SpecError("review target is outside declared composition, dependencies and implementation impact", "permission_denied")
        if mode == "code" and not target.files:
            return None
        task = {"target_id": target_id, "task": record["task"], "review_mode": mode,
                "change_id": run.change_id, "constraints": run.task.get("constraints", [])}
        child_host = replace(run.host, routed_target=target_id, coordinated=True,
                             evidence=[], descriptions=run.host.descriptions)
        # Call a single target reviewer directly: recursive impact expansion would review A/B forever.
        from .capability_host import Invocation
        child = Invocation("concorde-review", run.configuration, task, child_host)
        previous = retained.get(target_id)
        # Only a flow-composed continuation (track_gaps) reuses evidence; an explicit standalone
        # review is always fresh for the owner and every consumer.
        if (previous is not None and run.host.mode == "execute" and run.host.track_gaps
                and previous.get("task") == task["task"] and previous.get("constraints") == task["constraints"]):
            value = _current_artifact(child, mode, previous.get("artifact"))
            if value is not None:
                # Same consumer, same intent, same admitted input: the revision-bound review stands.
                outputs.append(child.response("completed", "Current " + mode + " review retained for "
                    + target_id + ".", artifacts=[previous["artifact"]], reviews=[value])["data"])
                return None
        result = review(child, mode)
        run.host.evidence.extend(child_host.evidence)
        outputs.append(result["data"])
        if result["data"]["outcome"] not in {"completed", "described"}:
            return result["data"]
    from ..harness.batch_flow import run_batch_flow
    run_batch_flow([None, *components.items()], review_module,
                   name="scope_review_flow", item_node="review_module")
    outcomes = {output["outcome"] for output in outputs}
    outcome = next((value for value in ("failed", "spec_incomplete", "conflicting", "unsupported", "described")
                    if value in outcomes), "completed")
    run.completed = [name for output in outputs for name in output["completed_capabilities"]]
    if mode == "spec" and run.host.mode == "execute":
        state = read_change(run.repository.root)
        if state is not None:
            peers = spec_consumers(run)
            # Keep unvisited applicable peers on interruption, but retire obsolete
            # membership. Historical report and execution artifacts remain intact.
            records = {key: value for key, value in
                       state.get("shared_spec_reviews", {}).get(run.target.id, {}).items()
                       if key in peers}
            for output in outputs:
                for value in output["reviews"]:
                    target_id = value["data"]["target_id"]
                    if target_id in peers:
                        reference = next(ref for ref in output["artifacts"] if ref["id"] == f"review.{target_id}.spec")
                        records[target_id] = {"artifact": reference, "task": components[target_id]["task"],
                                              "constraints": run.task.get("constraints", [])}
            state.setdefault("shared_spec_reviews", {})[run.target.id] = records
            save_change(run.repository.root, state)
    if mode == "code" and run.host.mode == "execute":
        state = read_change(run.repository.root)
        if state is not None:
            records = {key: value for key, value in
                       state.get("shared_implementation_reviews", {}).get(run.target.id, {}).items()
                       if key in affected_ids and key != run.target.id}
            for output in outputs:
                for value in output["reviews"]:
                    data = value["data"]
                    key = data["target_id"]
                    if key == run.target.id or key not in affected_ids:
                        continue
                    reference = next((ref for ref in output["artifacts"]
                                      if ref["id"] == f"review.{key}.code"), None)
                    if reference is not None:
                        records[key] = {"artifact": reference, "task": components[key]["task"],
                                        "constraints": run.task.get("constraints", [])}
            state.setdefault("shared_implementation_reviews", {})[run.target.id] = records
            save_change(run.repository.root, state)
    return run.response(outcome, "\n\n".join(output["answer"] for output in outputs),
        gaps=[gap for output in outputs for gap in output["gaps"]],
        artifacts=[ref for output in outputs for ref in output["artifacts"]],
        reviews=[value for output in outputs for value in output["reviews"]])


def skip(run, mode: str) -> dict:
    info, _ = inputs(run, mode)
    result = _empty(run, info, "skipped", "Fast-loop review is explicitly disabled.")
    _persist(run, result)
    return result


def _current_artifact(run, mode: str, reference: dict) -> dict | None:
    """The same revision-bound evidence rules apply to owners and Spec consumers."""
    try:
        verify_artifacts(run.repository.root, reference)
        value = validate_typed(json.loads(read_file(run.repository.root, reference["path"])),
                               "concorde-review-result")
        data = value["data"]
        if (data["input_digest"] != inputs(run, mode)[0]["input_digest"]
                or data["target_id"] != run.target.id or data["review_mode"] != mode
                or data["focus_id"] != run.task.get("focus_id") or not data["context_id"]
                or data["status"] not in {"no_findings", "findings"}
                or not data["representative_tasks"]
                or any(not task.strip() for task in data["representative_tasks"])
                or not data["answer"].strip()
                or data["gaps"] or any(f["severity"] == "blocking" for f in data["findings"])):
            return None
        # Cached evidence must pass the same attributed prerequisite admission as a
        # fresh reviewer, including authoring gaps recorded after this artifact.
        if run.pending_gaps(mode + "-review", review_input_digest=data["input_digest"]):
            return None
        return value
    except (ValueError, OSError, KeyError, TypeError):
        return None


def current(run, mode: str, *, required: bool = False) -> dict | None:
    """Validate version, intent and artifact integrity before reusing any result."""
    state = read_change(run.repository.root) or {}
    record = state.get("reviews", {}).get(run.target.id, {}).get(mode)
    value = _current_artifact(run, mode, record.get("artifact")) if record else None
    if value is not None and (record.get("status") != value["data"]["status"]
                             or record.get("input_digest") != value["data"]["input_digest"]):
        value = None
    if required and value is None:
        raise SpecError(f"required {mode} review is missing, incomplete, blocking, or stale", "review_required")
    return value


def _spec_consumer_artifacts(run, state: dict) -> list[dict] | None:
    from .capability_host import Invocation
    peers = spec_consumers(run)
    records = state.get("shared_spec_reviews", {}).get(run.target.id, {})
    if set(records) != peers:
        return None
    # A standalone scope may legitimately review an overlapping component under its
    # current component task. Continuation scopes use the consumer task. Both expectations
    # come from the same producer policy and live state, not the receipt's historical text.
    variants = [_spec_scope_tasks(run, state, peers, include_components=include)
                for include in (False, True)]
    references = []
    for target_id in sorted(peers):
        record = records[target_id]
        task = next((tasks[target_id] for tasks in variants
                     if record.get("task") == tasks[target_id]["task"]
                     and record.get("constraints") == tasks[target_id]["constraints"]), None)
        if task is None:
            return None
        reviewer = Invocation("concorde-review", run.configuration, task,
            replace(run.host, routed_target=target_id, coordinated=True))
        if _current_artifact(reviewer, "spec", record.get("artifact")) is None:
            return None
        references.append(record["artifact"])
    return references


def current_spec_scope(run) -> list[dict] | None:
    """Continuation may reuse a complete Spec scope without requiring later code review."""
    if current(run, "spec") is None:
        return None
    state = read_change(run.repository.root, required=True)
    consumers = _spec_consumer_artifacts(run, state)
    if consumers is None:
        return None
    return [state["reviews"][run.target.id]["spec"]["artifact"], *consumers]


def _code_peer_artifacts(run, state: dict) -> list[dict] | None:
    """Current code reviews of every peer that shares a changed file, each under its own intent."""
    from .capability_host import Invocation
    peers = code_review_peers(run)
    records = state.get("shared_implementation_reviews", {}).get(run.target.id, {})
    if set(records) != {target.id for target in peers}:
        return None
    references = []
    for target in peers:
        record = records[target.id]
        task = {"target_id": target.id, "task": record["task"],
                "constraints": record["constraints"], "change_id": run.change_id}
        reviewer = Invocation("concorde-review", run.configuration, task,
            replace(run.host, routed_target=target.id, coordinated=True))
        try:
            verify_artifacts(run.repository.root, record["artifact"])
            value = validate_typed(json.loads(read_file(run.repository.root,
                record["artifact"]["path"]).decode()), "concorde-review-result")["data"]
            valid = (value["target_id"] == target.id and value["review_mode"] == "code"
                and value["input_digest"] == inputs(reviewer, "code")[0]["input_digest"]
                and value["status"] in {"no_findings", "findings"} and not value["gaps"]
                and not any(item["severity"] == "blocking" for item in value["findings"]))
        except (ValueError, OSError, KeyError):
            valid = False
        if not valid:
            return None
        references.append(record["artifact"])
    return references


def current_code_scope(run) -> list[dict] | None:
    """The owner's current code review plus every changed-file peer's, or None if any is stale."""
    if current(run, "code") is None:
        return None
    state = read_change(run.repository.root, required=True)
    peers = _code_peer_artifacts(run, state)
    if peers is None:
        return None
    return [state["reviews"][run.target.id]["code"]["artifact"], *peers]


def require_reviews(run, enabled: bool, *, modes=None) -> None:
    state = read_change(run.repository.root, required=True)
    state.setdefault("review_intents", {})[run.target.id] = {"task": run.task["task"],
        "focus_id": run.task.get("focus_id"), "constraints": run.task.get("constraints", [])}
    requirements = state.setdefault("review_requirements", {}).setdefault(run.target.id, {})
    for mode in modes if modes is not None else (("spec", "code") if run.target.files else ("spec",)):
        # A resumed fast loop cannot silently downgrade previously required review.
        requirements[mode] = bool(enabled or requirements.get(mode))
    save_change(run.repository.root, state)


def verify_required(run) -> None:
    state = read_change(run.repository.root, required=True)
    if state.get("review_requirements", {}).get(run.target.id, {}).get("spec"):
        if _spec_consumer_artifacts(run, state) is None:
            raise SpecError("required Spec consumer reviews are missing, incomplete, blocking, or stale",
                            "review_required")
    if state["targets"]:
        for mode, required in state.get("review_requirements", {}).get(run.target.id, {}).items():
            if required:
                current(run, mode, required=True)
        if state.get("review_requirements", {}).get(run.target.id, {}).get("code"):
            # Each consumer review keeps its own intent and Module context. It is not replaced
            # by another consumer's current review or a later unrelated review of the same Module.
            if _code_peer_artifacts(run, state) is None:
                raise SpecError("required shared implementation consumer reviews are missing, failed or stale",
                                "review_required")
    else:
        # Directly authored candidates have no invented target plans. Their
        # explicitly required reviews still apply to every selected target.
        from .capability_host import Invocation
        for target_id, modes in state.get("review_requirements", {}).items():
            intent = state.get("review_intents", {}).get(target_id)
            if any(modes.values()) and intent is None:
                raise SpecError("required review has no bound intent", "review_required")
            if intent is None:
                continue
            task = {**intent, "target_id": target_id, "change_id": run.change_id}
            reviewer = Invocation("concorde-review", run.configuration, task,
                replace(run.host, routed_target=target_id, coordinated=True))
            for mode, required in modes.items():
                if required:
                    current(reviewer, mode, required=True)
