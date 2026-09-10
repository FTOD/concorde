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
from ..harness.agent_model import (ModeContractError, agent_definition, binding_json,
    external_agent_name, mode_definition, validate_mode_output)
from ..harness.agent_executor import CapabilityExecutionError
from ..harness.permissions import (EnforcementReceipt, CapabilityExecutionResult, PermissionPolicyError, PolicyBinding,
    build_launch_specification, compile_policy, render_claude_configuration, render_codex_configuration)
from ..spec.contracts import REVIEW_STAGES
from ..distribution.build import load_role_prompt
from ..harness.context import resolve_context, recheck_context
from ..spec.repository import SpecError, SpecRepository, bound_by, digest, read_file


def _changes(repository, target, mode, baseline) -> list[dict]:
    """Read history only for the current grant; never admit a project-wide diff."""
    spec_paths = target.documents
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
    if mode == "code" and not target.files:
        raise SpecError("code review requires a Module whose entities list implementation files", "unsupported_target")
    phase, role = REVIEW_STAGES[mode]
    prompt = load_role_prompt(run.host.package_root, role, phase)
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
            "src/concorde/development/review.py", "src/concorde/harness/agent_executor.py",
            "src/concorde/harness/permissions.py", "src/concorde/harness/context.py")},
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
        instructions=prompt.body, mode=mode_definition(agent_definition(prompt.binding.agent), phase))
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
            project_workspace = agent_definition(prompt.binding.agent).harness.workspace == "project"
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
            roles = ({"spec-context": (relative,),
                      "implementation": tuple(run.repository.implementation_files(run.target))}
                     if project_workspace else {"spec-context": (relative,)})
            binding = PolicyBinding("concorde-review", phase, 0, role, role, write_roles=())
            try:
                policy = compile_policy(prompt.effects, binding, roles,
                    outer_sandbox_required=run.configuration["data"]["enforcement"] == "outer")
            except PermissionPolicyError as error:
                raise SpecError(str(error), "permission_denied") from error
            if policy.write_paths:
                raise SpecError("review role must have no write authority", "permission_denied")
            integration = run.configuration["data"]["integration"]
            renderer = render_codex_configuration if integration == "codex" else render_claude_configuration
            native = renderer(policy, native_enforcement=run.configuration["data"]["enforcement"] == "native",
                              outer_sandbox=run.host.outer_sandbox)
            invocation_id = str(uuid.uuid4())
            receipt = {"schema_version": 15, "target_id": run.target.id, "phase": phase,
                "context_id": snapshot.id, "source_digest": snapshot.id, "input_digest": info["input_digest"],
                "role_paths": {key: list(paths) for key, paths in roles.items()}}
            launch = build_launch_specification(capability="concorde-review", stage=phase, occurrence=0,
                role=role, integration=integration, agent=role, project_root=str(project),
                request=run.task["task"], prompt=prompt.body, prior_results=(),
                workspace_receipt_json=canonical(receipt), workspace_digest=snapshot.id,
                policy=policy, native_configuration=native, runtime_input_json=canonical(value),
                capability_configuration_json=canonical(run.configuration), invocation_id=invocation_id,
                agent_binding_json=binding_json(prompt.binding))
            run.host.descriptions.append({"capability": "concorde-review", "phase": phase,
                "context_id": snapshot.id, "input_digest": info["input_digest"],
                "project_root": str(project), "read_paths": list(policy.read_paths), "write_paths": [],
                "network": False, "fresh_session": True, "policy_digest": policy.digest,
                "agent": external_agent_name(prompt.binding.agent), "harness": prompt.binding.harness,
                "agent_binding_digest": prompt.binding.digest, "mode": prompt.binding.mode,
                "instructions_digest": prompt.binding.instructions_digest,
                "loop_timeout_seconds": prompt.binding.effective_loop.timeout_seconds})
            if run.host.mode == "describe-policy":
                return run.response("described", reviews=[_empty(run, info, "not_run", "Policy described; review not run.")])
            from ..harness.agent_executor import AgentProcessExecutor
            result = (run.host.executor or AgentProcessExecutor())(launch)
            if not isinstance(result, CapabilityExecutionResult):
                raise SpecError("review executor omitted native completion evidence", "invalid_completion")
            if (result.receipt.requested_launch_digest != launch.digest
                    or result.receipt.policy_digest != policy.digest or result.receipt.status != "success"
                    or result.completion.invocation_id != invocation_id
                    or result.completion.workspace_digest != snapshot.id
                    or result.receipt.agent_binding_digest != prompt.binding.digest):
                raise SpecError("review evidence is not bound to this launch", "invalid_completion")
            validate_mode_output(agent_definition(prompt.binding.agent), prompt.binding.mode, result.completion.domain_output)
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
        if isinstance(error, CapabilityExecutionError):
            code = error.code or ("execution_cancelled" if error.outcome == "cancelled" else
                   "execution_limit" if error.outcome == "limit_exhausted" else "execution_failed")
            lifecycle_status = ("cancelled" if error.outcome == "cancelled" else
                                "limit_exhausted" if error.outcome == "limit_exhausted" else "failed")
            run.host.lifecycle["status"] = lifecycle_status
            # concorde-review is never mutation-classified (record_progress excludes it), so a
            # standalone review's own executor failure would otherwise leave the change status
            # untouched; a cancelled/limit-exhausted executor outcome is host bookkeeping, not a
            # content judgment a read-only query should withhold.
            progress(run.repository.root, status=lifecycle_status)
        else:
            code = error.code if isinstance(error, (SpecError, ModeContractError)) else "execution_failed"
        reviewed = _empty(run, info, "incomplete", f"Review could not complete ({code}).")
        receipt = getattr(error, "receipt", None)
        reference = _persist(run, reviewed,
            execution=result if isinstance(result, CapabilityExecutionResult) else None,
            receipt=receipt if isinstance(receipt, EnforcementReceipt) else None,
            failure={"code": code, "message": str(error)})
        return run.response("failed", reviewed["data"]["answer"], artifacts=[reference], reviews=[reviewed])


def review_scope(run, mode: str) -> dict:
    """Review each using Module in a separate context after shared implementation changes."""
    change = read_change(run.repository.root)
    work = (change or {}).get("targets", {}).get(run.target.id, {})
    components = dict(work.get("coordination", {}))
    if mode == "code":
        affected = run.repository.covering_modules(run.target)
        for target in affected:
            if target.id != run.target.id:
                components.setdefault(target.id, {"task":
                    "Check this Module's own contract against the shared implementation change. " + run.task["task"]})
    if not components or (mode == "spec" and run.host.track_gaps):
        return review(run, mode)
    outputs = [review(run, mode)["data"]] if mode == "spec" or run.target.files else []
    from .capability_host import invoke_capability
    affected_ids = {target.id for target in run.repository.covering_modules(run.target)}
    allowed = {run.target.id, *run.target.uses, *affected_ids,
               *(child.id for child in run.repository.children(run.target))}
    for target_id, record in components.items():
        if target_id == run.target.id:
            continue
        target = run.repository.select(target_id)
        if target.id not in allowed:
            raise SpecError("review target is outside declared composition, dependencies and implementation impact", "permission_denied")
        if mode == "code" and not target.files:
            continue
        task = {"target_id": target_id, "task": record["task"], "review_mode": mode,
                "change_id": run.change_id, "constraints": run.task.get("constraints", [])}
        child_host = replace(run.host, routed_target=target_id, coordinated=True,
                             evidence=[], descriptions=run.host.descriptions)
        # Call a single target reviewer directly: recursive impact expansion would review A/B forever.
        from .capability_host import Invocation
        child = Invocation("concorde-review", run.configuration, task, child_host)
        result = review(child, mode)
        run.host.evidence.extend(child_host.evidence)
        outputs.append(result["data"])
    outcomes = {output["outcome"] for output in outputs}
    outcome = next((value for value in ("failed", "spec_incomplete", "conflicting", "unsupported", "described")
                    if value in outcomes), "completed")
    run.completed = [name for output in outputs for name in output["completed_capabilities"]]
    if mode == "code" and run.host.mode == "execute":
        state = read_change(run.repository.root)
        if state is not None:
            records = {}
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
    for mode in ("spec", "code") if run.target.files else ("spec",):
        # A resumed fast loop cannot silently downgrade previously required review.
        requirements[mode] = bool(enabled or requirements.get(mode))
    save_change(run.repository.root, state)


def verify_required(run) -> None:
    state = read_change(run.repository.root, required=True)
    if state["targets"]:
        for mode, required in state.get("review_requirements", {}).get(run.target.id, {}).items():
            if required:
                current(run, mode, required=True)
        if state.get("review_requirements", {}).get(run.target.id, {}).get("code"):
            # Each consumer review keeps its own intent and Module context. It is not replaced
            # by another consumer's current review or a later unrelated review of the same Module.
            from .capability_host import Invocation
            peers = [target for target in run.repository.covering_modules(run.target)
                     if target.id != run.target.id]
            records = state.get("shared_implementation_reviews", {}).get(run.target.id, {})
            if set(records) != {target.id for target in peers}:
                raise SpecError("required shared implementation consumer reviews are missing", "review_required")
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
                    raise SpecError(f"shared implementation review is failed or stale for {target.id}", "review_required")
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
