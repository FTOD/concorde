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
from pathlib import Path, PurePosixPath

from .change_worktree import git, git_value, read_change, save_change, workspace_identity
from .typed_data import artifact, canonical, checked_path, typed, validate_typed, verify_artifacts
from .configuration import load_configuration
from .permissions import (EnforcementReceipt, CapabilityExecutionResult, PolicyBinding, build_launch_specification,
    compile_policy, render_claude_configuration, render_codex_configuration)
from .contracts import REVIEW_STAGES
from .build import load_role_prompt
from ..specification.context import resolve_context, recheck_context
from ..specification.repository import SpecError, SpecRepository, digest, read_file


def _under(path: str, roots) -> bool:
    candidate = PurePosixPath(path)
    return any(candidate == PurePosixPath(root) or PurePosixPath(root) in candidate.parents for root in roots)


def _changes(repository, target, mode, baseline) -> list[dict]:
    """Read history only for the current grant; never admit a project-wide diff."""
    roots = target.documents if mode == "spec" else target.implementation
    current = set(target.documents if mode == "spec" else repository.implementation_files(target))
    previous = {}
    if baseline and roots:
        tree = git_value(repository.root, "--literal-pathspecs", "ls-tree", "-r", "-z", baseline, "--", *roots)
        for entry in tree.split("\0"):
            if not entry:
                continue
            header, path = entry.split("\t", 1)
            _, kind, oid = header.split()
            if (kind == "blob" and _under(path, roots)
                    and not set(PurePosixPath(path).parts) & {"__pycache__", ".venv", "node_modules", ".git"}):
                previous[path] = oid
    changes = []
    for path in sorted(current | previous.keys()):
        after = read_file(repository.root, path) if path in current else b""
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
    repository = SpecRepository(run.repository.root, run.host.package_root)
    target = repository.select(run.target.id, run.task.get("focus_id"))
    if mode not in REVIEW_STAGES:
        raise SpecError("review_mode must be spec or code", "invalid_input")
    if mode == "code" and (target.kind == "domain" or not target.implementation):
        raise SpecError("code review requires a target with registered implementation files", "unsupported_target")
    phase, role = REVIEW_STAGES[mode]
    prompt = load_role_prompt(run.host.package_root, role)
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
        "host_runtime": {path: digest(read_file(run.host.package_root, path)) for path in (
            "src/concorde/host/review.py", "src/concorde/host/agent_executor.py",
            "src/concorde/host/permissions.py", "src/concorde/specification/context.py")},
        "configuration": run.configuration}
    return {"review_mode": mode, "input_digest": digest(identity), "revision": revision, "changes": changes}, prompt


def _empty(run, info, status, answer) -> dict:
    return typed("concorde-review-result", {"context_id": None, "input_digest": info["input_digest"],
        "review_mode": info["review_mode"], "status": status, "representative_tasks": [],
        "findings": [], "gaps": [], "answer": answer, "target_id": run.target.id,
        "focus_id": run.task.get("focus_id"), "revision": info["revision"],
        "semantic_completeness": "not_proven"})


def _persist(run, value, *, execution=None, receipt=None, failure=None) -> dict:
    """Host run records are separate from the reviewer's empty write grant."""
    mode = value["data"]["review_mode"]
    path = f".concorde/runs/{run.host.invocation_id}/review-{run.target.id}-{mode}.json"
    destination = checked_path(run.repository.root, path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(canonical(value) + "\n")
    reference = artifact(run.repository.root, f"review.{run.target.id}.{mode}", path)
    if execution is not None or receipt is not None or failure is not None:
        private = destination.with_suffix(".execution.json")
        private.write_text(canonical({"execution": asdict(execution) if execution else None,
                                      "receipt": asdict(receipt) if receipt else None,
                                      "failure": failure}) + "\n")
    state = read_change(run.repository.root)
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
    allowed = set(run.target.documents)
    if info["review_mode"] == "code":
        allowed.update(run.repository.implementation_files(run.target))
        allowed.update(item["path"] for item in info["changes"])
    for finding in findings:
        if any(not finding[key].strip() for key in ("id", "contract", "problem", "affected_task")):
            raise SpecError("review findings require nonblank evidence and an affected task", "invalid_completion")
        if (finding["target_id"] != run.target.id or finding["document"] not in run.target.documents
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
    info, prompt = inputs(run, mode)
    phase, role = REVIEW_STAGES[mode]
    snapshot = resolve_context(run.repository, run.target.id, phase=phase, task=run.task["task"],
        focus_id=run.task.get("focus_id"), constraints=tuple(run.task.get("constraints", [])),
        instructions=prompt.body)
    run.last_context = snapshot.id
    pending = run.pending_gaps(phase, snapshot)
    if pending and run.host.track_gaps:
        value = _empty(run, info, "not_run", "Repair the recorded necessary contracts before resuming review.")
        reference = _persist(run, value)
        return run.response("spec_incomplete", value["data"]["answer"], gaps=pending,
                            artifacts=[reference], reviews=[value])
    result = None
    try:
        with tempfile.TemporaryDirectory(prefix="concorde-review-") as directory:
            project = run.repository.root if mode == "code" else Path(directory)
            relative = (f".concorde/runs/{run.host.invocation_id}/{uuid.uuid4()}/context.json"
                        if mode == "code" else "context.json")
            capsule = checked_path(project, relative)
            value = typed("concorde-review-stage-context", {
                "snapshot": typed("concorde-context-snapshot", snapshot.value),
                "review": typed("concorde-review-input", info)})
            serialized = canonical(value) + "\n"
            if run.host.mode != "describe-policy":
                capsule.parent.mkdir(parents=True, exist_ok=True)
                capsule.write_text(serialized)
            roles = {"spec-context": (relative,),
                     "implementation": tuple(run.repository.implementation_files(run.target)) if mode == "code" else ()}
            binding = PolicyBinding("concorde-review", phase, 0, role, role, write_roles=())
            policy = compile_policy(prompt.effects, binding, roles,
                outer_sandbox_required=run.configuration["data"]["enforcement"] == "outer")
            if policy.write_paths:
                raise SpecError("review role must have no write authority", "permission_denied")
            integration = run.configuration["data"]["integration"]
            renderer = render_codex_configuration if integration == "codex" else render_claude_configuration
            native = renderer(policy, native_enforcement=run.configuration["data"]["enforcement"] == "native",
                              outer_sandbox=run.host.outer_sandbox)
            invocation_id = str(uuid.uuid4())
            receipt = {"schema_version": 14, "target_id": run.target.id, "phase": phase,
                "context_id": snapshot.id, "source_digest": snapshot.id, "input_digest": info["input_digest"],
                "role_paths": {key: list(paths) for key, paths in roles.items()}}
            launch = build_launch_specification(capability="concorde-review", stage=phase, occurrence=0,
                role=role, integration=integration, agent=role, project_root=str(project),
                request=run.task["task"], prompt=prompt.body, prior_results=(),
                workspace_receipt_json=canonical(receipt), workspace_digest=snapshot.id,
                policy=policy, native_configuration=native, runtime_input_json=canonical(value),
                capability_configuration_json=canonical(run.configuration), invocation_id=invocation_id)
            run.host.descriptions.append({"operation": "concorde-review", "phase": phase,
                "context_id": snapshot.id, "input_digest": info["input_digest"],
                "project_root": str(project), "read_paths": list(policy.read_paths), "write_paths": [],
                "network": False, "fresh_session": True, "policy_digest": policy.digest})
            if run.host.mode == "describe-policy":
                return run.response("described", reviews=[_empty(run, info, "not_run", "Policy described; review not run.")])
            from .agent_executor import AgentProcessExecutor
            result = (run.host.executor or AgentProcessExecutor())(launch)
            if not isinstance(result, CapabilityExecutionResult):
                raise SpecError("review executor omitted native completion evidence", "invalid_completion")
            if (result.receipt.requested_launch_digest != launch.digest
                    or result.receipt.policy_digest != policy.digest or result.receipt.status != "success"
                    or result.completion.invocation_id != invocation_id
                    or result.completion.workspace_digest != snapshot.id):
                raise SpecError("review evidence is not bound to this launch", "invalid_completion")
            data = validate_typed(result.completion.domain_output, "concorde-review-stage-result")["data"]
            _validate(run, snapshot, info, data)
            recheck_context(run.repository, snapshot)
            if inputs(run, mode)[0] != info or load_configuration(run.repository.root) != run.configuration:
                raise SpecError("review inputs changed while the reviewer was running", "stale_context")
            if capsule.read_text() != serialized:
                raise SpecError("review capsule changed", "stale_context")
            reviewed = typed("concorde-review-result", {**data, "target_id": run.target.id,
                "focus_id": run.task.get("focus_id"), "revision": info["revision"],
                "semantic_completeness": "not_proven"})
            reference = _persist(run, reviewed, execution=result)
            if data["status"] != "incomplete":
                run.record_gaps(phase, data["gaps"])
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
        code = error.code if isinstance(error, SpecError) else "execution_failed"
        reviewed = _empty(run, info, "incomplete", f"Review could not complete ({code}).")
        receipt = getattr(error, "receipt", None)
        reference = _persist(run, reviewed,
            execution=result if isinstance(result, CapabilityExecutionResult) else None,
            receipt=receipt if isinstance(receipt, EnforcementReceipt) else None,
            failure={"code": code, "message": str(error)})
        return run.response("failed", reviewed["data"]["answer"], artifacts=[reference], reviews=[reviewed])


def review_scope(run, mode: str) -> dict:
    """Aggregate only separately bound results for a Domain's recorded component work."""
    if run.target.kind != "domain" or (mode == "spec" and run.host.track_gaps):
        return review(run, mode)
    change = read_change(run.repository.root)
    work = (change or {}).get("targets", {}).get(run.target.id, {})
    components = work.get("coordination", {})
    if mode == "code" and not components:
        return run.response("unsupported", "This Domain has no recorded component work to route for code review.")
    outputs = [review(run, mode)["data"]] if mode == "spec" else []
    from .capability_host import invoke_capability
    for target_id, record in components.items():
        target = run.repository.select(target_id)
        scopes = set(target.participates_in)
        for scope in tuple(scopes):
            parent = run.repository.targets[scope].scope_parent
            while parent:
                scopes.add(parent)
                parent = run.repository.targets[parent].scope_parent
        if target.kind == "domain" or run.target.id not in scopes:
            raise SpecError("Domain review component is outside its participating scope", "permission_denied")
        task = {"target_id": target_id, "task": record["task"], "review_mode": mode,
                "change_id": run.change_id, "constraints": run.task.get("constraints", [])}
        child_host = replace(run.host, routed_target=target_id, coordinated=True,
                             evidence=[], descriptions=run.host.descriptions)
        result = invoke_capability(run.capability, "concorde-review", run.configuration,
                                   typed("concorde-review-request", task), child_host)
        run.host.evidence.extend(child_host.evidence)
        if result["output"] is None:
            outputs.append({"outcome": "failed", "answer": f"Review admission failed for {target_id}.",
                            "gaps": [], "reviews": [], "artifacts": [], "completed_capabilities": []})
        else:
            outputs.append(result["output"]["data"])
    outcomes = {output["outcome"] for output in outputs}
    outcome = next((value for value in ("failed", "spec_incomplete", "conflicting", "unsupported", "described")
                    if value in outcomes), "completed")
    run.completed = [name for output in outputs for name in output["completed_capabilities"]]
    return run.response(outcome, "\n\n".join(output["answer"] for output in outputs),
        gaps=[gap for output in outputs for gap in output["gaps"]],
        artifacts=[ref for output in outputs for ref in output["artifacts"]],
        reviews=[value for output in outputs for value in output["reviews"]])


def skip(run, mode: str) -> dict:
    info, _ = inputs(run, mode)
    result = _empty(run, info, "skipped", "Fast-loop review is explicitly disabled.")
    _persist(run, result)
    return result


def current(run, mode: str, *, required: bool = False) -> dict | None:
    """Validate version, intent and artifact integrity before reusing any result."""
    state = read_change(run.repository.root)
    record = state.get("reviews", {}).get(run.target.id, {}).get(mode) if state else None
    value = None
    if record:
        try:
            verify_artifacts(run.repository.root, record["artifact"])
            value = validate_typed(json.loads(read_file(run.repository.root,
                record["artifact"]["path"])), "concorde-review-result")
            data = value["data"]
            if (data["input_digest"] != inputs(run, mode)[0]["input_digest"]
                    or data["target_id"] != run.target.id or data["review_mode"] != mode
                    or data["status"] not in {"no_findings", "findings"}
                    or data["gaps"] or any(f["severity"] == "blocking" for f in data["findings"])):
                value = None
            if any(item["status"] == "open" and item["target_id"] == run.target.id
                    and item["task"] == run.task["task"] and item["phase"] == mode + "-review"
                    for item in state.get("gap_history", [])):
                value = None
        except (ValueError, OSError, KeyError):
            value = None
    if required and value is None:
        raise SpecError(f"required {mode} review is missing, incomplete, blocking, or stale", "review_required")
    return value


def require_reviews(run, enabled: bool) -> None:
    state = read_change(run.repository.root, required=True)
    state.setdefault("review_intents", {})[run.target.id] = {"task": run.task["task"],
        "focus_id": run.task.get("focus_id"), "constraints": run.task.get("constraints", [])}
    requirements = state.setdefault("review_requirements", {}).setdefault(run.target.id, {})
    for mode in ("spec", "code") if run.target.implementation else ("spec",):
        # A resumed fast loop cannot silently downgrade previously required review.
        requirements[mode] = bool(enabled or requirements.get(mode))
    save_change(run.repository.root, state)


def verify_required(run) -> None:
    state = read_change(run.repository.root, required=True)
    if state["targets"]:
        for mode, required in state.get("review_requirements", {}).get(run.target.id, {}).items():
            if required:
                current(run, mode, required=True)
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
