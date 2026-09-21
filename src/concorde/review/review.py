"""Independent, target-bound reviews and their existing-change lifecycle evidence.

Only the host reads Git objects, creates capsules and persists receipts. Reviewers
get immutable scoped inputs and zero project write authority in either mode.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import subprocess
import uuid
from dataclasses import asdict, replace

from ..distribution.build import ModelInstructions, load_model_instructions
from ..harness.change_worktree import (
    git,
    git_value,
    progress,
    read_change,
    save_change,
    workspace_identity,
)
from ..harness.context import (
    context_documents,
    recheck_context,
    resolve_context,
)
from ..harness.invocation import Invocation
from ..harness.launch import WorkerLaunch, launch_worker
from ..harness.revisions import implementation_digest, target_revision
from ..harness.worker_executor import OperationExecutionError, WorkerOutcome
from ..harness.worker_profile import ContractError, worker_profile
from ..spec.contracts import REVIEW_STAGES
from ..spec.repository import SpecError, SpecRepository, bound_by, digest, read_file
from ..spec.typed_data import (
    artifact,
    canonical,
    typed,
    validate_typed,
    verify_artifacts,
)


def _changes(repository, target, mode, baseline) -> list[dict]:
    """Read history only for the current grant; never admit a project-wide diff."""
    spec_paths = repository.spec_files(target.id)
    # Directory entries scope history by their base path; only the files they bind are admitted.
    entries = (
        spec_paths if mode == "spec" else repository.implementation_entries(target)
    )
    roots = spec_paths if mode == "spec" else repository.implementation_paths(target)
    current = set(
        spec_paths if mode == "spec" else repository.implementation_files(target)
    )
    previous = {}
    if baseline and roots:
        tree = git_value(
            repository.root,
            "--literal-pathspecs",
            "ls-tree",
            "-r",
            "-z",
            baseline,
            "--",
            *roots,
        )
        for entry in tree.split("\0"):
            if not entry:
                continue
            header, path = entry.split("\t", 1)
            _, kind, oid = header.split()
            if kind == "blob" and any(bound_by(item, path) for item in entries):
                previous[path] = oid
    changes = []
    for path in sorted(current | previous.keys()):
        after = (
            (
                repository.source_bytes(path)
                if mode == "spec"
                else read_file(repository.root, path)
            )
            if path in current
            else b""
        )
        oid = previous.get(path)
        if oid and path in current:
            git_digest = hashlib.new(
                "sha1" if len(oid) == 40 else "sha256",
                b"blob " + str(len(after)).encode() + b"\0" + after,
            ).hexdigest()
            if git_digest == oid:
                continue
        before = (
            subprocess.run(
                ("git", "cat-file", "blob", oid),
                cwd=repository.root,
                capture_output=True,
                check=True,
            ).stdout
            if oid
            else b""
        )
        if before == after and (path in current) == bool(oid):
            continue
        if b"\0" in before or b"\0" in after:
            patch = f"Binary change: {digest(before)} -> {digest(after)}"
        else:
            patch = "".join(
                difflib.unified_diff(
                    before.decode(errors="replace").splitlines(keepends=True),
                    after.decode(errors="replace").splitlines(keepends=True),
                    fromfile=path if oid else "/dev/null",
                    tofile=path if path in current else "/dev/null",
                )
            )
        changes.append(
            {"path": path, "patch": patch or "Empty file membership changed."}
        )
    return changes


def inputs(run, mode: str) -> tuple[dict, ModelInstructions]:
    repository = SpecRepository(run.repository.root, run.host.package_root)
    target = repository.select(run.target.id, run.task.get("focus_id"))
    if mode not in REVIEW_STAGES:
        raise SpecError("review_mode must be spec or code", "invalid_input")
    if mode == "code" and not target.files:
        raise SpecError(
            "code review requires a Module whose entities list implementation files",
            "unsupported_target",
        )
    phase, role = REVIEW_STAGES[mode]
    prompt = load_model_instructions(run.host.package_root, role)
    native = run.host.package_root / (
        "generated/native/" + role.replace("_", "-") + ".md"
    )
    if prompt.binding is None or prompt.effects is None:
        raise SpecError(
            "review requires a bound WorkerProfile with explicit effects",
            "permission_denied",
        )
    change = read_change(repository.root)
    _, current = workspace_identity(repository.root)
    head = current["head"] if current else None
    baseline = change["base_commit"] if change else head
    revision = {
        "spec_digest": target_revision(repository, target),
        "implementation_digest": implementation_digest(repository, target)
        if mode == "code"
        else None,
        "baseline": baseline,
        "head": head,
    }
    changes = _changes(repository, target, mode, baseline)
    identity = {
        "target_id": run.target.id,
        "focus_id": run.task.get("focus_id"),
        "project_root": str(repository.root),
        "branch": current["branch"] if current else None,
        "task": run.task["task"],
        "constraints": run.task.get("constraints", []),
        "change_id": run.change_id,
        "review_mode": mode,
        "revision": revision,
        "changes": changes,
        "instructions": {
            "legacy_issue": prompt.body,
            "native": native.read_text() if native.is_file() else None,
        },
        "role_effects": asdict(prompt.effects),
        "agent_binding_digest": prompt.binding.digest,
        "host_runtime": {
            path: digest(read_file(run.host.package_root, path))
            for path in (
                "src/concorde/review/review.py",
                "src/concorde/harness/host.py",
                "src/concorde/harness/invocation.py",
                "src/concorde/harness/admission.py",
                "src/concorde/harness/entry.py",
                "src/concorde/harness/relay.py",
                "src/concorde/harness/checks.py",
                "src/concorde/harness/revisions.py",
                "src/concorde/harness/operation_graph.py",
                "src/concorde/operations/dispatch.py",
                "src/concorde/operations/dispatch_graph.py",
                "src/concorde/operations/target_graph.py",
                "src/concorde/planning/plan.py",
                "src/concorde/planning/tasks.py",
                "src/concorde/implementation/implement.py",
                "src/concorde/validation/validate.py",
                "src/concorde/spec/project.py",
                "src/concorde/issues/reporting.py",
                "src/concorde/issues/references.py",
                "src/concorde/issues/store.py",
                "src/concorde/spec/issue_shapes.py",
                "src/concorde/harness/change_worktree.py",
                "src/concorde/harness/worker_executor.py",
                "src/concorde/harness/pi_worker.py",
                "src/concorde/harness/permissions.py",
                "src/concorde/harness/context.py",
                "src/concorde/harness/batch_graph.py",
            )
        },
        "configuration": run.configuration,
    }
    return {
        "review_mode": mode,
        "input_digest": digest(identity),
        "revision": revision,
        "changes": changes,
    }, prompt


def _empty(run, info, status, answer) -> dict:
    return typed(
        "concorde-review-result",
        {
            "context_id": None,
            "input_digest": info["input_digest"],
            "review_mode": info["review_mode"],
            "status": status,
            "representative_tasks": [],
            "issues": [],
            "answer": answer,
            "target_id": run.target.id,
            "focus_id": run.task.get("focus_id"),
            "revision": info["revision"],
            "semantic_completeness": "not_proven",
        },
    )


def _persist(run, value, *, execution=None, failure=None) -> dict:
    """Host run records are separate from the reviewer's empty write grant."""
    mode = value["data"]["review_mode"]
    path = f".concorde/runs/{run.host.invocation_id}/review-{run.target.id}-{mode}-{uuid.uuid4()}.json"
    from ..harness.status_store import run_path, write_run

    destination = run_path(run.repository.root, path)
    write_run(run.repository.root, path, (canonical(value) + "\n").encode())
    reference = artifact(run.repository.root, f"review.{run.target.id}.{mode}", path)
    if execution is not None or failure is not None:
        # The worker's reported usage and any execution failure stay host records beside the review.
        private = destination.with_suffix(".execution.json")
        private.write_text(
            canonical(
                {"usage": asdict(execution) if execution else None, "failure": failure}
            )
            + "\n"
        )
    state = read_change(run.repository.root)
    if state is not None:
        intent = {
            "task": run.task["task"],
            "focus_id": run.task.get("focus_id"),
            "constraints": run.task.get("constraints", []),
        }
        expected = state.get("review_intents", {}).get(run.target.id)
        if expected is not None and expected != intent:
            return reference
        state.setdefault("reviews", {}).setdefault(run.target.id, {})[mode] = {
            "artifact": reference,
            "input_digest": value["data"]["input_digest"],
            "status": value["data"]["status"],
            "task": run.task["task"],
            "focus_id": run.task.get("focus_id"),
            "constraints": run.task.get("constraints", []),
        }
        if state.get("review_requirements", {}).get(run.target.id, {}).get(mode):
            # Only lifecycle-required review supersedes the candidate's ready
            # receipt. Standalone queries may record unrelated review evidence.
            state["validated_tree"] = None
            if state["status"] == "ready":
                state.update(status="active", phase=mode + "-review", outcome=None)
        save_change(run.repository.root, state)
    return reference


def _validate(run, snapshot, info, data):
    if (
        data["context_id"] != snapshot.id
        or data["input_digest"] != info["input_digest"]
        or data["review_mode"] != info["review_mode"]
    ):
        raise SpecError(
            "review identities differ from admitted input", "incompatible_handoff"
        )
    findings = data["issues"]
    if not data["answer"].strip() or any(
        not task.strip() for task in data["representative_tasks"]
    ):
        raise SpecError(
            "review answer and covered tasks must be meaningful nonblank text",
            "invalid_completion",
        )
    if len({finding["issue_id"] for finding in findings}) != len(findings):
        raise SpecError("review finding IDs must be unique", "invalid_completion")
    if data["status"] == "no_findings" and findings:
        raise SpecError(
            "no_findings review cannot contain findings or gaps", "invalid_completion"
        )
    if data["status"] == "findings" and not findings:
        raise SpecError(
            "findings review requires concrete findings or gaps", "invalid_completion"
        )
    if data["status"] != "incomplete" and not data["representative_tasks"]:
        raise SpecError(
            "completed review requires representative task coverage",
            "invalid_completion",
        )
    # Report admission validates evidence locations and contract owners. The result references
    # those immutable observations instead of duplicating their text in findings and gaps.
    if any(not finding["affected_task"].strip() for finding in findings):
        raise SpecError("review Issue requires an affected task", "invalid_completion")


def review(run, mode: str) -> dict:
    """Run exactly one reviewer; no prior review, transcript or code crosses modes."""
    info, prompt = inputs(run, mode)
    if prompt.binding is None or prompt.effects is None:
        raise SpecError(
            "review requires a bound WorkerProfile with explicit effects",
            "permission_denied",
        )
    phase, role = REVIEW_STAGES[mode]
    agent = worker_profile(prompt.binding.agent)
    snapshot = resolve_context(
        run.repository,
        run.target.id,
        phase=phase,
        task=run.task["task"],
        focus_id=run.task.get("focus_id"),
        constraints=tuple(run.task.get("constraints", [])),
        instructions=prompt.body,
        agent=agent,
    )
    run.last_context = snapshot.id
    pending = run.pending_gaps(
        phase, snapshot, review_input_digest=info["input_digest"]
    )
    if pending and run.host.track_gaps:
        value = _empty(
            run,
            info,
            "not_run",
            "Repair the recorded necessary contracts before resuming review.",
        )
        reference = _persist(run, value)
        return run.response(
            "spec_incomplete",
            value["data"]["answer"],
            blockers=pending,
            artifacts=[reference],
            reviews=[value],
        )
    result: WorkerOutcome | None = None

    def admitted(outcome: WorkerOutcome) -> None:
        nonlocal result
        result = outcome

    def recheck() -> None:
        recheck_context(run.repository, snapshot)
        if inputs(run, mode)[0] != info:
            raise SpecError(
                "review inputs changed while the reviewer was running", "stale_context"
            )

    value = typed(
        "concorde-review-stage-context",
        {
            "snapshot": typed("concorde-context-snapshot", snapshot.value),
            "review": typed("concorde-review-input", info),
        },
    )
    try:
        data = launch_worker(
            run.host,
            run.configuration,
            run.repository,
            prompt,
            WorkerLaunch(
                operation=f"concorde-{mode}-review",
                stage=phase,
                role=role,
                snapshot=snapshot,
                granted=context_documents(run.repository, snapshot.value),
                value=value,
                index=canonical(value) + "\n",
                result_type="concorde-review-stage-result",
                receipt={
                    "target_id": run.target.id,
                    "input_digest": info["input_digest"],
                },
                described=run.response(
                    "described",
                    reviews=[
                        _empty(
                            run, info, "not_run", "Policy described; review not run."
                        )
                    ],
                ),
                validate=lambda data: _validate(run, snapshot, info, data),
                recheck=recheck,
                target=run.target,
                target_id=run.target.id,
                implementation=(
                    tuple(run.repository.implementation_files(run.target))
                    if agent.workspace == "project"
                    else None
                ),
                labels={"input_digest": info["input_digest"]},
                admitted=admitted,
                prefix="concorde-review-",
            ),
        )
        if run.host.mode == "describe-policy":
            return data
        if result is None:
            raise SpecError(
                "review completed without a worker receipt", "invalid_completion"
            )
        return accept_review_result(run, snapshot, info, data, execution=result.usage)
    except Exception as error:
        if run.host.mode != "execute":
            raise  # A preview has no persistence authority.
        return _failed_review(run, info, result, error)


def accept_review_result(run, snapshot, info, data, *, execution=None):
    _validate(run, snapshot, info, data)
    phase = info["review_mode"] + "-review"
    mode = info["review_mode"]
    reviewed = typed(
        "concorde-review-result",
        {
            **data,
            "target_id": run.target.id,
            "focus_id": run.task.get("focus_id"),
            "revision": info["revision"],
            "semantic_completeness": "not_proven",
        },
    )
    reference = _persist(run, reviewed, execution=execution)
    from ..issues.references import requires_contract_repair, review_blockers

    blockers = review_blockers(data["issues"])
    if data["status"] != "incomplete":
        run.record_gaps(phase, blockers, review_input_digest=info["input_digest"])
    run.completed.append(f"concorde-{mode}-review")
    outcome = (
        "failed"
        if data["status"] == "incomplete"
        else "spec_incomplete"
        if requires_contract_repair(run.repository.root, blockers)
        else "conflicting"
        if blockers
        else "completed"
    )
    return run.response(
        outcome,
        data["answer"],
        blockers=blockers,
        artifacts=[reference],
        reviews=[reviewed],
    )


def _failed_review(run, info, result, error):
    """Preserve execution failure without retracting already acknowledged Issue observations."""
    if isinstance(error, OperationExecutionError):
        code = error.code or (
            "execution_cancelled"
            if error.outcome == "cancelled"
            else "execution_limit"
            if error.outcome == "limit_exhausted"
            else "execution_failed"
        )
        lifecycle_status = (
            "cancelled"
            if error.outcome == "cancelled"
            else "limit_exhausted"
            if error.outcome == "limit_exhausted"
            else "failed"
        )
        run.host.lifecycle["status"] = lifecycle_status
        if lifecycle_status in {"cancelled", "limit_exhausted"}:
            run.host.lifecycle["execution_error"] = code
        try:
            progress(run.repository.root, status=lifecycle_status)
        except (ValueError, OSError) as persistence_error:
            run.host.lifecycle["persistence_error"] = (
                f"Could not persist reviewer execution status: {persistence_error}"
            )
    else:
        code = (
            error.code
            if isinstance(error, (SpecError, ContractError))
            else "execution_failed"
        )
    reviewed = _empty(run, info, "incomplete", f"Review could not complete ({code}).")
    failure = {"code": code, "message": str(error)}
    if run.host.lifecycle.get("persistence_error"):
        failure["persistence"] = run.host.lifecycle["persistence_error"]
    usage = (
        result.usage
        if isinstance(result, WorkerOutcome)
        else getattr(error, "usage", None)
    )
    reference = _persist(run, reviewed, execution=usage, failure=failure)
    return run.response(
        "failed", reviewed["data"]["answer"], artifacts=[reference], reviews=[reviewed]
    )


def spec_consumers(run) -> set[str]:
    """Current inclusion plus the retained old/candidate impact union."""
    state = read_change(run.repository.root) or {}
    selected = set(state.get("spec_context_impacts", {}).get(run.target.id, []))
    for path in run.target.documents:
        selected.update(
            run.repository.context_users(run.repository.document(path).document_id)
        )
    selected.update(state.get("shared_spec_reviews", {}).get(run.target.id, {}))
    baseline = state.get("base_commit")
    if baseline:
        # Git objects from this candidate's declared base are host-only inputs. Never inspect
        # another worktree's project files to reconstruct old ownership or inclusion.
        raw = git(
            run.repository.root,
            "show",
            f"{baseline}:{run.repository.registry_path}",
            check=False,
        )
        if raw.returncode == 0:
            from ..spec.typed_data import decode

            registry = decode(raw.stdout)
            if registry.get("schema_version") != 5:
                raise SpecError(
                    "review baseline uses a retired Spec format; migrate the candidate explicitly",
                    "unsupported_profile",
                )
            overrides = {}
            for path in {
                member
                for target in registry["targets"]
                for document in target["documents"]
                for member in (document, document + ".json")
            }:
                result = subprocess.run(
                    ("git", "show", f"{baseline}:{path}"),
                    cwd=run.repository.root,
                    capture_output=True,
                    check=True,
                )
                overrides[path] = result.stdout
            old = SpecRepository(
                run.repository.root,
                run.host.package_root,
                registry_bytes=raw.stdout.encode(),
                document_overrides=overrides,
            )
            if run.target.id in old.targets:
                for path in old.select(run.target.id).documents:
                    selected.update(old.context_users(old.document(path).document_id))
    return selected & run.repository.targets.keys() - {run.target.id}


def consumer_intent(task: str) -> str:
    """The one review intent a Spec consumer is asked under, before and after the change applies."""
    return "Review this Module's reliance on the changed canonical Spec. " + task


def consumer_task(run, target_id):
    return {
        "target_id": target_id,
        "task": consumer_intent(run.task["task"]),
        "constraints": run.task.get("constraints", []),
        "change_id": run.change_id,
    }


def changed_implementation_paths(run) -> list[str] | None:
    """The target's bound files that differ from the candidate base, or None when history is unknown."""
    change = read_change(run.repository.root)
    _, current = workspace_identity(run.repository.root)
    baseline = (
        change.get("base_commit") if change else (current["head"] if current else None)
    )
    if not baseline:
        return None
    return [
        item["path"] for item in _changes(run.repository, run.target, "code", baseline)
    ]


def code_review_peers(run) -> tuple:
    """Modules whose entries cover a file of this target that actually changed in the candidate.

    P6 requires checks for every listing Module of a changed shared file, not of every shared
    file. Without a known base revision every covering Module is a peer.
    """
    changed = changed_implementation_paths(run)
    peers = (
        run.repository.covering_modules(run.target)
        if changed is None
        else run.repository.affected_modules(changed)
    )
    return tuple(
        target for target in peers if target.id != run.target.id and target.files
    )


def _component_tasks(run, state):
    """Read explicit completed component selections; never resume legacy orchestration."""
    from ..implementation.implement import component_intent

    work = (state or {}).get("targets", {}).get(run.target.id, {})
    allowed = {
        *run.target.uses,
        *(child.id for child in run.repository.children(run.target)),
    }
    tasks = {}
    for target_id in work.get("component_revisions", {}):
        selected = [
            item for item in work.get("tasks", []) if item["target_id"] == target_id
        ]
        if target_id not in allowed or not selected:
            raise SpecError(
                "recorded component is outside the accepted task scope",
                "permission_denied",
            )
        tasks[target_id] = {
            **consumer_task(run, target_id),
            "task": component_intent(selected),
        }
    return tasks


def _spec_scope_tasks(run, state, peers, *, include_components):
    """Derive admitted Spec scope from current caller and explicit component intent."""
    tasks = _component_tasks(run, state) if include_components else {}
    for target_id in peers:
        tasks.setdefault(target_id, consumer_task(run, target_id))
    return tasks


def _code_scope_tasks(run, state):
    tasks = {
        key: value
        for key, value in _component_tasks(run, state).items()
        if run.repository.select(key).files
    }
    for target in code_review_peers(run):
        tasks.setdefault(
            target.id,
            {
                **consumer_task(run, target.id),
                "task": "Check this Module's own contract against the shared implementation change. "
                + run.task["task"],
            },
        )
    return tasks


def _code_scope_identity(run):
    """Bind aggregation to the parent's complete current contract and review question."""
    repository = SpecRepository(run.repository.root, run.host.package_root)
    target = repository.select(run.target.id, run.task.get("focus_id"))
    return digest(
        {
            "spec_digest": target_revision(repository, target),
            "target_id": target.id,
            "task": run.task["task"],
            "focus_id": run.task.get("focus_id"),
            "constraints": run.task.get("constraints", []),
        }
    )


def review_scope(run, mode: str):
    if run.host.native_assessment is not None:
        return run.host.native_assessment(run)
    if run.host.issue_intent and run.host.depth > 1:
        # TEMPORARY: Issue solving's internal verification only; remove with its native migration.
        return legacy_issue_review_scope(run, mode)
    raise SpecError("Public review requires its native Pi workflow", "native_required")


def scope_members(run, mode, *, initialize=False):
    change = read_change(run.repository.root)
    if initialize and change and run.host.mode == "execute":
        intent = (
            change
            if change.get("target_id") == run.target.id
            else change["targets"].get(run.target.id, {})
        )
        if all(
            intent.get(k, [] if k == "constraints" else None)
            == run.task.get(k, [] if k == "constraints" else None)
            for k in ("task", "focus_id", "constraints")
        ):
            require_reviews(run, True, modes=(mode,))
            change = read_change(run.repository.root)
    components = (
        _spec_scope_tasks(run, change, spec_consumers(run), include_components=True)
        if mode == "spec"
        else _code_scope_tasks(run, change)
    )
    components = dict(sorted(components.items()))
    allowed = {
        run.target.id,
        *run.target.uses,
        *components,
        *spec_consumers(run),
        *(t.id for t in run.repository.covering_modules(run.target)),
        *(t.id for t in run.repository.children(run.target)),
    }
    members = []
    if not components or mode == "spec" or run.target.files:
        members.append(dict(run.task))
    for target_id, record in components.items():
        if target_id == run.target.id:
            continue
        target = run.repository.select(target_id)
        if target_id not in allowed:
            raise SpecError("review target outside scope", "permission_denied")
        if mode == "code" and not target.files:
            continue
        members.append(
            {
                "target_id": target_id,
                "task": record["task"],
                "change_id": run.change_id,
                "constraints": run.task.get("constraints", []),
            }
        )
    return components, _code_scope_identity(run) if mode == "code" else None, members


def legacy_issue_review_scope(run, mode: str) -> dict:
    """Review each using Module in a separate context after shared implementation changes."""
    change = read_change(run.repository.root)
    if change and run.host.mode == "execute":
        intent = (
            change
            if change.get("target_id") == run.target.id
            else change["targets"].get(run.target.id, {})
        )
        if (
            intent.get("task") == run.task["task"]
            and intent.get("focus_id") == run.task.get("focus_id")
            and intent.get("constraints", []) == run.task.get("constraints", [])
        ):
            require_reviews(run, True, modes=(mode,))
    if mode == "spec":
        components = _spec_scope_tasks(
            run, change, spec_consumers(run), include_components=not run.host.track_gaps
        )
    else:
        components = _code_scope_tasks(run, change)
    scope_identity = (
        _code_scope_identity(run)
        if mode == "code" and run.host.mode == "execute"
        else None
    )
    outputs = []

    affected_ids = set(components) if mode == "code" else set()
    allowed = {
        run.target.id,
        *run.target.uses,
        *affected_ids,
        *spec_consumers(run),
        *(target.id for target in run.repository.covering_modules(run.target)),
        *(child.id for child in run.repository.children(run.target)),
    }
    retained = (
        (change or {}).get("shared_spec_reviews", {}).get(run.target.id, {})
        if mode == "spec"
        else (change or {})
        .get("shared_implementation_reviews", {})
        .get(run.target.id, {})
    )

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
            raise SpecError(
                "review target is outside declared composition, dependencies and implementation impact",
                "permission_denied",
            )
        if mode == "code" and not target.files:
            return None
        task = {
            "target_id": target_id,
            "task": record["task"],
            "change_id": run.change_id,
            "constraints": run.task.get("constraints", []),
        }
        child_host = replace(
            run.host,
            coordinated=True,
            evidence=[],
            descriptions=run.host.descriptions,
        )
        # Call a single target reviewer directly: recursive impact expansion would review A/B forever.

        child = Invocation(
            f"concorde-{mode}-review", run.configuration, task, child_host
        )
        previous = retained.get(target_id)
        # Only a graph-composed continuation (track_gaps) reuses evidence; an explicit standalone
        # review is always fresh for the owner and every consumer.
        if (
            previous is not None
            and run.host.mode == "execute"
            and run.host.track_gaps
            and previous.get("task") == task["task"]
            and previous.get("constraints") == task["constraints"]
        ):
            value = _current_artifact(child, mode, previous.get("artifact"))
            if value is not None:
                # Same consumer, same intent, same admitted input: the revision-bound review stands.
                outputs.append(
                    child.response(
                        "completed",
                        "Current " + mode + " review retained for " + target_id + ".",
                        artifacts=[previous["artifact"]],
                        reviews=[value],
                    )["data"]
                )
                return None
        result = review(child, mode)
        run.host.evidence.extend(child_host.evidence)
        outputs.append(result["data"])
        if result["data"]["outcome"] not in {"completed", "described"}:
            return result["data"]

    from ..harness.batch_graph import run_batch_graph

    run_batch_graph(
        [None, *components.items()],
        review_module,
        name="scope_review_graph",
        item_node="review_module",
    )
    return aggregate_scope(run, mode, components, scope_identity, outputs)


def aggregate_scope(run, mode, components, scope_identity, outputs):
    affected_ids = set(components) if mode == "code" else set()
    outcomes = {output["outcome"] for output in outputs}
    outcome = next(
        (
            value
            for value in (
                "failed",
                "spec_incomplete",
                "conflicting",
                "unsupported",
                "described",
            )
            if value in outcomes
        ),
        "completed",
    )
    run.completed = [
        name for output in outputs for name in output["completed_operations"]
    ]
    if mode == "spec" and run.host.mode == "execute":
        state = read_change(run.repository.root)
        if state is not None:
            peers = spec_consumers(run)
            # Keep unvisited applicable peers on interruption, but retire obsolete
            # membership. Historical report and execution artifacts remain intact.
            records = {
                key: value
                for key, value in state.get("shared_spec_reviews", {})
                .get(run.target.id, {})
                .items()
                if key in peers
            }
            for output in outputs:
                for value in output["reviews"]:
                    target_id = value["data"]["target_id"]
                    if target_id in peers:
                        reference = next(
                            ref
                            for ref in output["artifacts"]
                            if ref["id"] == f"review.{target_id}.spec"
                        )
                        records[target_id] = {
                            "artifact": reference,
                            "task": components[target_id]["task"],
                            "constraints": run.task.get("constraints", []),
                        }
            state.setdefault("shared_spec_reviews", {})[run.target.id] = records
            save_change(run.repository.root, state)
    if mode == "code" and run.host.mode == "execute":
        if _code_scope_identity(run) != scope_identity:
            raise SpecError("aggregate review parent context changed", "stale_context")
        state = read_change(run.repository.root)
        if state is not None:
            records = {
                key: value
                for key, value in state.get("shared_implementation_reviews", {})
                .get(run.target.id, {})
                .items()
                if key in affected_ids and key != run.target.id
            }
            for output in outputs:
                for value in output["reviews"]:
                    data = value["data"]
                    key = data["target_id"]
                    if key == run.target.id or key not in affected_ids:
                        continue
                    reference = next(
                        (
                            ref
                            for ref in output["artifacts"]
                            if ref["id"] == f"review.{key}.code"
                        ),
                        None,
                    )
                    if reference is not None:
                        records[key] = {
                            "artifact": reference,
                            "task": components[key]["task"],
                            "constraints": run.task.get("constraints", []),
                            "scope_digest": scope_identity,
                        }
            state.setdefault("shared_implementation_reviews", {})[run.target.id] = (
                records
            )
            save_change(run.repository.root, state)
    return run.response(
        outcome,
        "\n\n".join(output["answer"] for output in outputs),
        blockers=[gap for output in outputs for gap in output["blockers"]],
        artifacts=[ref for output in outputs for ref in output["artifacts"]],
        reviews=[value for output in outputs for value in output["reviews"]],
    )


def repair_feedback(run, reference: dict) -> dict:
    """Admit only the selected current host-recorded blocking code review."""
    state = read_change(run.repository.root, required=True)
    record = state.get("reviews", {}).get(run.target.id, {}).get("code", {})
    if record.get("artifact") != reference:
        raise SpecError(
            "repair requires the current recorded code review", "stale_evidence"
        )
    verify_artifacts(run.repository.root, reference)
    value = validate_typed(
        json.loads(read_file(run.repository.root, reference["path"])),
        "concorde-review-result",
    )
    data = value["data"]
    if (
        data["input_digest"] != inputs(run, "code")[0]["input_digest"]
        or record.get("input_digest") != data["input_digest"]
    ):
        raise SpecError(
            "repair review is stale for the selected intent", "stale_evidence"
        )
    if (
        data["review_mode"] != "code"
        or data["target_id"] != run.target.id
        or data["focus_id"] != run.task.get("focus_id")
        or data["status"] != "findings"
        or record.get("status") != data["status"]
        or not data["context_id"]
        or not data["representative_tasks"]
        or any(not task.strip() for task in data["representative_tasks"])
        or not data["answer"].strip()
        or not any(item["severity"] == "blocking" for item in data["issues"])
    ):
        raise SpecError(
            "repair requires completed blocking code-review evidence",
            "incompatible_handoff",
        )
    from ..issues.references import receipt
    from ..issues.store import resolve_report

    for judgment in data["issues"]:
        resolve_report(run.repository.root, receipt(judgment))
    return value


def _current_artifact(run, mode: str, reference: dict) -> dict | None:
    """The same revision-bound evidence rules apply to owners and Spec consumers."""
    try:
        verify_artifacts(run.repository.root, reference)
        value = validate_typed(
            json.loads(read_file(run.repository.root, reference["path"])),
            "concorde-review-result",
        )
        data = value["data"]
        from ..issues.references import receipt
        from ..issues.store import resolve_report

        for judgment in data["issues"]:
            resolve_report(run.repository.root, receipt(judgment))
        if (
            data["input_digest"] != inputs(run, mode)[0]["input_digest"]
            or data["target_id"] != run.target.id
            or data["review_mode"] != mode
            or data["focus_id"] != run.task.get("focus_id")
            or not data["context_id"]
            or data["status"] not in {"no_findings", "findings"}
            or not data["representative_tasks"]
            or any(not task.strip() for task in data["representative_tasks"])
            or not data["answer"].strip()
            or any(f["severity"] == "blocking" for f in data["issues"])
        ):
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
    if value is not None and (
        record.get("status") != value["data"]["status"]
        or record.get("input_digest") != value["data"]["input_digest"]
    ):
        value = None
    if required and value is None:
        raise SpecError(
            f"required {mode} review is missing, incomplete, blocking, or stale",
            "review_required",
        )
    return value


def _spec_consumer_artifacts(run, state: dict) -> list[dict] | None:

    peers = spec_consumers(run)
    records = state.get("shared_spec_reviews", {}).get(run.target.id, {})
    if set(records) != peers:
        return None
    # A standalone scope may legitimately review an overlapping component under its
    # current component task. Continuation scopes use the consumer task. Both expectations
    # come from the same producer policy and live state, not the receipt's historical text.
    variants = [
        _spec_scope_tasks(run, state, peers, include_components=include)
        for include in (False, True)
    ]
    references = []
    for target_id in sorted(peers):
        record = records[target_id]
        task = next(
            (
                tasks[target_id]
                for tasks in variants
                if record.get("task") == tasks[target_id]["task"]
                and record.get("constraints") == tasks[target_id]["constraints"]
            ),
            None,
        )
        if task is None:
            return None
        reviewer = Invocation(
            "concorde-spec-review",
            run.configuration,
            task,
            replace(run.host, coordinated=True),
        )
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
    """Every explicit component and changed-file peer needs current exact-intent evidence."""
    tasks = _code_scope_tasks(run, state)
    records = state.get("shared_implementation_reviews", {}).get(run.target.id, {})
    if set(records) != set(tasks):
        return None
    references = []
    for target_id, task in tasks.items():
        record = records[target_id]
        if (
            record.get("task") != task["task"]
            or record.get("constraints") != task["constraints"]
            or record.get("scope_digest") != _code_scope_identity(run)
        ):
            return None
        reviewer = Invocation(
            "concorde-code-review",
            run.configuration,
            task,
            replace(run.host, coordinated=True),
        )
        if _current_artifact(reviewer, "code", record.get("artifact")) is None:
            return None
        references.append(record["artifact"])
    return references


def current_code_scope(run) -> list[dict] | None:
    """Local code, if any, plus separately admitted components and changed-file peers."""
    state = read_change(run.repository.root, required=True)
    local = []
    if run.target.files:
        if current(run, "code") is None:
            return None
        local.append(state["reviews"][run.target.id]["code"]["artifact"])
    elif not _code_scope_tasks(run, state):
        return None
    peers = _code_peer_artifacts(run, state)
    if peers is None:
        return None
    return [*local, *peers]


def require_reviews(run, enabled: bool, *, modes=None) -> None:
    state = read_change(run.repository.root, required=True)
    state.setdefault("review_intents", {})[run.target.id] = {
        "task": run.task["task"],
        "focus_id": run.task.get("focus_id"),
        "constraints": run.task.get("constraints", []),
    }
    requirements = state.setdefault("review_requirements", {}).setdefault(
        run.target.id, {}
    )
    for mode in (
        modes
        if modes is not None
        else (("spec", "code") if run.target.files else ("spec",))
    ):
        # A later call cannot silently downgrade a previously selected requirement.
        requirements[mode] = bool(enabled or requirements.get(mode))
    save_change(run.repository.root, state)


def verify_required(run) -> None:
    state = read_change(run.repository.root, required=True)
    if (
        state.get("review_requirements", {}).get(run.target.id, {}).get("spec")
        and _spec_consumer_artifacts(run, state) is None
    ):
        raise SpecError(
            "required Spec consumer reviews are missing, incomplete, blocking, or stale",
            "review_required",
        )
    if state["targets"]:
        for mode, required in (
            state.get("review_requirements", {}).get(run.target.id, {}).items()
        ):
            if required and mode != "code":
                current(run, mode, required=True)
        # Each consumer review keeps its own intent and Module context. It is not replaced
        # by another consumer's current review or a later unrelated review of the same Module.
        if (
            state.get("review_requirements", {}).get(run.target.id, {}).get("code")
            and current_code_scope(run) is None
        ):
            raise SpecError(
                "required shared implementation consumer reviews are missing, failed or stale",
                "review_required",
            )
    else:
        # Directly authored candidates have no invented target plans. Their
        # explicitly required reviews still apply to every selected target.

        for target_id, modes in state.get("review_requirements", {}).items():
            intent = state.get("review_intents", {}).get(target_id)
            if any(modes.values()) and intent is None:
                raise SpecError(
                    "required review has no bound intent", "review_required"
                )
            if intent is None:
                continue
            task = {**intent, "target_id": target_id, "change_id": run.change_id}
            for mode, required in modes.items():
                if required:
                    reviewer = Invocation(
                        f"concorde-{mode}-review",
                        run.configuration,
                        task,
                        replace(run.host, coordinated=True),
                    )
                    if mode == "code":
                        if current_code_scope(reviewer) is None:
                            raise SpecError(
                                "required code review scope is missing or stale",
                                "review_required",
                            )
                    else:
                        current(reviewer, mode, required=True)


def require_spec_review(run) -> None:
    if run.host.mode != "execute":
        return
    change = read_change(run.repository.root)
    if change and change.get("review_requirements", {}).get(run.target.id, {}).get(
        "spec"
    ):
        if current_spec_scope(run) is None:
            raise SpecError(
                "required Spec scope review is missing, incomplete, blocking, or stale",
                "review_required",
            )
