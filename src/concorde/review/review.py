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

from ..harness.change_worktree import (
    git,
    git_value,
    progress,
    read_change,
    save_change,
    snapshot_tree,
    workspace_identity,
)
from ..harness.invocation import Invocation
from ..harness.revisions import implementation_digest, target_revision
from ..harness.execution_error import OperationExecutionError
from ..harness.worker_profile import (
    ContractError,
    agent_definition,
    bind_agent,
    load_instructions,
)
from ..spec.boundaries import scope_roots
from ..planning.gaps import pending_gaps, record_gaps
from ..planning.records import targets
from ..planning.scope import change_scope
from .impact import review_impact
from .records import recorded, review_records
from ..spec.repository import SpecError, SpecRepository, bound_by, digest, read_file
from ..harness.status_store import (
    read_record,
    record_artifact,
    verify_record_artifacts,
)
from ..spec.typed_data import (
    canonical,
    typed,
    validate_typed,
)


def _changes(repository, target, mode, baseline) -> list[dict]:
    """Read history only for the current grant; never admit a project-wide diff."""
    spec_paths = repository.spec_context(target.id).paths
    # Directory entries scope history by their base path; only the files they bind are admitted.
    entries = spec_paths if mode == "spec" else repository.implementation_scope(target)
    roots = spec_paths if mode == "spec" else scope_roots(entries)
    current = set(spec_paths if mode == "spec" else repository.bound_files(target))
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


def inputs(run, mode: str) -> dict:
    """The review input of one reviewer: mode, input digest, revision and scoped changes."""
    repository = SpecRepository(run.repository.root, run.host.package_root)
    target = repository.module(run.target.id, run.task.get("focus_id"))
    if mode not in {"spec", "code"}:
        raise SpecError("review_mode must be spec or code", "invalid_input")
    if mode == "code" and not target.files:
        raise SpecError(
            "code review requires a Module whose entities list implementation files",
            "unsupported_target",
        )
    agent = review_agent(mode)
    binding = bind_agent(run.host.package_root, agent)
    instructions = load_instructions(run.host.package_root, binding)
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
        "instructions": instructions,
        "role_effects": agent_definition(agent).effects,
        "agent_binding_digest": binding.digest,
        "host_runtime": {
            path: digest(read_file(run.host.package_root, path))
            for path in HOST_RUNTIME
        },
        "configuration": run.configuration,
    }
    return {
        "review_mode": mode,
        "input_digest": digest(identity),
        "revision": revision,
        "changes": changes,
    }


# The Host runtime files that take part in a review: the review service's own realizations and
# the Host code it runs through. A change to any of them makes a recorded review stale.
HOST_RUNTIME = (
    "src/concorde/review/review.py",
    "src/concorde/review/native.py",
    "src/concorde/review/impact.py",
    "src/concorde/review/records.py",
    "pi/workflows/review.js",
    "pi/native-review-host.mjs",
    "pi/native-host-step.mjs",
    "pi/extensions/concorde-native-plan.ts",
    "pi/extensions/concorde-native-child.ts",
    "src/concorde/harness/native_driver.py",
    "src/concorde/harness/native_evidence.py",
    "src/concorde/harness/native_result.py",
    "src/concorde/harness/capsule.py",
    "src/concorde/harness/context.py",
    "src/concorde/harness/worker_profile.py",
    "src/concorde/harness/host.py",
    "src/concorde/harness/invocation.py",
    "src/concorde/harness/admission.py",
    "src/concorde/harness/entry.py",
    "src/concorde/harness/relay.py",
    "src/concorde/harness/checks.py",
    "src/concorde/harness/revisions.py",
    "src/concorde/harness/change_worktree.py",
    "src/concorde/operations/dispatch.py",
    "src/concorde/operations/catalog.py",
    "src/concorde/planning/gaps.py",
    "src/concorde/planning/records.py",
    "src/concorde/planning/plan.py",
    "src/concorde/planning/tasks.py",
    "src/concorde/planning/scope.py",
    "src/concorde/implementation/implement.py",
    "src/concorde/validation/validate.py",
    "src/concorde/spec/impact.py",
    "src/concorde/issues/reporting.py",
    "src/concorde/issues/references.py",
    "src/concorde/issues/store.py",
    "src/concorde/issues/shapes.py",
)


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


def _persist(run, value, *, failure=None) -> dict:
    """Host run records are separate from the reviewer's empty write grant."""
    mode = value["data"]["review_mode"]
    path = f".concorde/runs/{run.host.invocation_id}/review-{run.target.id}-{mode}-{uuid.uuid4()}.json"
    from ..harness.status_store import run_path, write_run

    destination = run_path(run.repository.root, path)
    write_run(run.repository.root, path, (canonical(value) + "\n").encode())
    reference = record_artifact(
        run.repository.root, f"review.{run.target.id}.{mode}", path
    )
    if failure is not None:
        # An execution failure stays a host record beside the review.
        private = destination.with_suffix(".execution.json")
        private.write_text(canonical({"failure": failure}) + "\n")
    state = read_change(run.repository.root)
    if state is not None:
        intent = {
            "task": run.task["task"],
            "focus_id": run.task.get("focus_id"),
            "constraints": run.task.get("constraints", []),
        }
        records = review_records(state)
        expected = records["intents"].get(run.target.id)
        if expected is not None and expected != intent:
            return reference
        records["reviews"].setdefault(run.target.id, {})[mode] = {
            "artifact": reference,
            "input_digest": value["data"]["input_digest"],
            "status": value["data"]["status"],
            "task": run.task["task"],
            "focus_id": run.task.get("focus_id"),
            "constraints": run.task.get("constraints", []),
        }
        if records["requirements"].get(run.target.id, {}).get(mode) and (
            state["status"] == "ready"
        ):
            # Only lifecycle-required review withdraws the candidate's ready state.
            # Standalone queries may record unrelated review evidence.
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


def accept_review_result(run, snapshot, info, data):
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
    reference = _persist(run, reviewed)
    from ..issues.references import requires_contract_repair, review_blockers

    blockers = review_blockers(data["issues"])
    if data["status"] != "incomplete":
        record_gaps(run, phase, blockers, review_input_digest=info["input_digest"])
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


def _failed_review(run, info, error):
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
    reference = _persist(run, reviewed, failure=failure)
    return run.response(
        "failed", reviewed["data"]["answer"], artifacts=[reference], reviews=[reviewed]
    )


def changed_paths(root, baseline: str) -> tuple[str, ...]:
    """Every deliverable path that differs from a baseline commit, untracked files included.

    The candidate's deliverable tree excludes local control records and the Host's own worktree
    guidance, so neither counts as an edit of the change.
    """
    tree = snapshot_tree(root)
    if tree is None:
        return ()
    listed = git(
        root, "diff-tree", "-r", "--name-only", "--no-renames", "-z", baseline, tree
    ).stdout
    return tuple(sorted(path for path in listed.split("\0") if path))


def change_owner(run) -> bool:
    """Whether the run's Module is the Module the current managed change is about.

    The owner's review scope and validation cover every Module the whole candidate edits; any
    other Module's cover only its own documents and files.
    """
    state = read_change(run.repository.root)
    return state is not None and state.get("target_id") == run.target.id


def baseline_repository(run, baseline: str) -> SpecRepository | None:
    """The Spec graph at a baseline commit, read from Git objects only, or None without a registry.

    Git objects from this candidate's declared base are host-only inputs. Never inspect another
    worktree's project files to reconstruct old ownership or selection.
    """
    raw = git(
        run.repository.root,
        "show",
        f"{baseline}:{run.repository.registry_path}",
        check=False,
    )
    if raw.returncode != 0:
        return None
    from ..spec.typed_data import decode

    registry = decode(raw.stdout)
    if registry.get("schema_version") != 3 or not isinstance(
        registry.get("modules"), list
    ):
        raise SpecError(
            "review baseline registry is not a schema-3 registry",
            "unsupported_profile",
        )

    def baseline_bytes(path: str) -> bytes:
        return subprocess.run(
            ("git", "show", f"{baseline}:{path}"),
            cwd=run.repository.root,
            capture_output=True,
            check=True,
        ).stdout

    # The baseline's documents are those its entries own; the entries are the declaration site,
    # the registry only says which Modules existed and where their entries were.
    documents: set[str] = set()
    for record in registry["modules"]:
        block = decode(baseline_bytes(record["entry"] + ".json").decode()).get(
            "module", {}
        )
        documents.update(block.get("owns", ()) or (record["entry"],))
    overrides = {
        member: baseline_bytes(member)
        for document in documents
        for member in (document, document + ".json")
    }
    return SpecRepository(
        run.repository.root,
        run.host.package_root,
        registry_bytes=raw.stdout.encode(),
        document_overrides=overrides,
    )


def spec_consumers(run) -> set[str]:
    """The other Modules a required Spec review of this Module must cover (Framework P6).

    Inside a managed change the baseline and the candidate are compared at promise level
    (``review_impact``): a Module is a consumer when it selects a changed document without
    narrowing or references a changed node. For the change's own Module the changed documents
    are those of the whole candidate, so every Module the change edits is covered; for any
    other Module they are its own documents. Without a baseline every Module selecting one of
    its documents is a consumer. Consumers already recorded for this Module stay members.
    """
    state = read_change(run.repository.root) or {}
    selected = set(recorded(state, "shared_spec_reviews").get(run.target.id, {}))
    baseline = state.get("base_commit")
    old = baseline_repository(run, baseline) if baseline else None
    if old is None:
        for path in run.target.documents:
            selected.update(
                run.repository.selected_by(run.repository.document(path).document_id)
            )
    else:
        paths = None
        if not change_owner(run):
            paths = set(run.target.documents)
            if run.target.id in old.modules:
                paths.update(old.module(run.target.id).documents)
        selected.update(review_impact(old, run.repository, paths))
    return selected & run.repository.modules.keys() - {run.target.id}


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
    if change and change.get("target_id") == run.target.id:
        # The change's own Module answers for every file the candidate changed.
        return [
            path
            for path in changed_paths(run.repository.root, baseline)
            if run.repository.implemented_by(path)
        ]
    return [
        item["path"] for item in _changes(run.repository, run.target, "code", baseline)
    ]


def code_review_peers(run) -> tuple:
    """Modules that bind a file that actually changed in the candidate (``implemented-by``).

    For the change's own Module every changed file of the candidate counts, so the code review
    covers every Module whose code the change edits; for any other Module only its own files.
    P6 requires checks for every binding Module of a changed shared file, not of every shared
    file. Without a known base revision every Module sharing one of its files is a peer.
    """
    changed = changed_implementation_paths(run)
    peers = (
        tuple(run.repository.shared_files(run.target))
        if changed is None
        else run.repository.impact(paths=changed)
    )
    return tuple(
        run.repository.modules[module_id]
        for module_id in peers
        if module_id != run.target.id and run.repository.modules[module_id].files
    )


def _component_tasks(run, state):
    """Read explicit completed component selections; never resume legacy orchestration."""
    from ..planning.scope import component_intent

    work = targets(state).get(run.target.id, {})
    allowed = set(change_scope(run.repository, run.target.id)) - {run.target.id}
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
        if run.repository.module(key).files
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
    target = repository.module(run.target.id, run.task.get("focus_id"))
    return digest(
        {
            "spec_digest": target_revision(repository, target),
            "target_id": target.id,
            "task": run.task["task"],
            "focus_id": run.task.get("focus_id"),
            "constraints": run.task.get("constraints", []),
        }
    )


def review_agent(mode: str) -> str:
    """The reviewer Agent the catalog declares for the ``spec`` or ``code`` review."""
    from ..operations.catalog import operation

    return operation(f"concorde-{mode}-review").agents[0][0]


def scope_members(run, mode, *, initialize=False):
    change = read_change(run.repository.root)
    if initialize and change and run.host.mode == "execute":
        intent = (
            change
            if change.get("target_id") == run.target.id
            else targets(change).get(run.target.id, {})
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
        *change_scope(run.repository, run.target.id),
        *components,
        *spec_consumers(run),
    }
    members = []
    if not components or mode == "spec" or run.target.files:
        members.append(dict(run.task))
    for target_id, record in components.items():
        if target_id == run.target.id:
            continue
        target = run.repository.module(target_id)
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
                for key, value in recorded(state, "shared_spec_reviews")
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
            review_records(state)["shared_spec_reviews"][run.target.id] = records
            save_change(run.repository.root, state)
    if mode == "code" and run.host.mode == "execute":
        if _code_scope_identity(run) != scope_identity:
            raise SpecError("aggregate review parent context changed", "stale_context")
        state = read_change(run.repository.root)
        if state is not None:
            records = {
                key: value
                for key, value in recorded(state, "shared_implementation_reviews")
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
            review_records(state)["shared_implementation_reviews"][run.target.id] = (
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
    record = recorded(state, "reviews").get(run.target.id, {}).get("code", {})
    if record.get("artifact") != reference:
        raise SpecError(
            "repair requires the current recorded code review", "stale_evidence"
        )
    verify_record_artifacts(run.repository.root, reference)
    value = validate_typed(
        json.loads(read_record(run.repository.root, reference["path"])),
        "concorde-review-result",
    )
    data = value["data"]
    if (
        data["input_digest"] != inputs(run, "code")["input_digest"]
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
        verify_record_artifacts(run.repository.root, reference)
        value = validate_typed(
            json.loads(read_record(run.repository.root, reference["path"])),
            "concorde-review-result",
        )
        data = value["data"]
        from ..issues.references import receipt
        from ..issues.store import resolve_report

        for judgment in data["issues"]:
            resolve_report(run.repository.root, receipt(judgment))
        if (
            data["input_digest"] != inputs(run, mode)["input_digest"]
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
        if pending_gaps(
            run, mode + "-review", review_input_digest=data["input_digest"]
        ):
            return None
        return value
    except (ValueError, OSError, KeyError, TypeError):
        return None


def current(run, mode: str, *, required: bool = False) -> dict | None:
    """Validate version, intent and artifact integrity before reusing any result."""
    state = read_change(run.repository.root) or {}
    record = recorded(state, "reviews").get(run.target.id, {}).get(mode)
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
    records = recorded(state, "shared_spec_reviews").get(run.target.id, {})
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
            run.host,
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
    return [
        recorded(state, "reviews")[run.target.id]["spec"]["artifact"],
        *consumers,
    ]


def _code_peer_artifacts(run, state: dict) -> list[dict] | None:
    """Every explicit component and changed-file peer needs current exact-intent evidence."""
    tasks = _code_scope_tasks(run, state)
    records = recorded(state, "shared_implementation_reviews").get(run.target.id, {})
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
            run.host,
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
        local.append(recorded(state, "reviews")[run.target.id]["code"]["artifact"])
    elif not _code_scope_tasks(run, state):
        return None
    peers = _code_peer_artifacts(run, state)
    if peers is None:
        return None
    return [*local, *peers]


def require_reviews(run, enabled: bool, *, modes=None) -> None:
    state = read_change(run.repository.root, required=True)
    records = review_records(state)
    records["intents"][run.target.id] = {
        "task": run.task["task"],
        "focus_id": run.task.get("focus_id"),
        "constraints": run.task.get("constraints", []),
    }
    requirements = records["requirements"].setdefault(run.target.id, {})
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
    requirements = recorded(state, "requirements")
    if (
        requirements.get(run.target.id, {}).get("spec")
        and _spec_consumer_artifacts(run, state) is None
    ):
        raise SpecError(
            "required Spec consumer reviews are missing, incomplete, blocking, or stale",
            "review_required",
        )
    if targets(state):
        for mode, required in requirements.get(run.target.id, {}).items():
            if required and mode != "code":
                current(run, mode, required=True)
        # Each consumer review keeps its own intent and Module context. It is not replaced
        # by another consumer's current review or a later unrelated review of the same Module.
        if (
            requirements.get(run.target.id, {}).get("code")
            and current_code_scope(run) is None
        ):
            raise SpecError(
                "required shared implementation consumer reviews are missing, failed or stale",
                "review_required",
            )
    else:
        # Directly authored candidates have no invented target plans. Their
        # explicitly required reviews still apply to every selected target.

        for target_id, modes in requirements.items():
            intent = recorded(state, "intents").get(target_id)
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
                        run.host,
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
    if recorded(change, "requirements").get(run.target.id, {}).get("spec"):
        if current_spec_scope(run) is None:
            raise SpecError(
                "required Spec scope review is missing, incomplete, blocking, or stale",
                "review_required",
            )
