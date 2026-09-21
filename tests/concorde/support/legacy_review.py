"""Only staged-double domain regressions use this historical worker adapter."""

from dataclasses import replace

from concorde.harness.context import context_documents, recheck_context, resolve_context
from concorde.harness.launch import WorkerLaunch, launch_worker
from concorde.harness.worker_executor import WorkerOutcome
from concorde.harness.worker_profile import worker_profile
from concorde.review import review as current_review
from concorde.review.review import (
    REVIEW_STAGES,
    SpecError,
    _empty,
    _failed_review,
    _persist,
    _validate,
    accept_review_result,
    canonical,
    inputs,
    typed,
)


def legacy_issue_review_scope(run, mode: str) -> dict:
    """Review each using Module in a separate context after shared implementation changes."""
    change = current_review.read_change(run.repository.root)
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
            current_review.require_reviews(run, True, modes=(mode,))
    if mode == "spec":
        components = current_review._spec_scope_tasks(
            run,
            change,
            current_review.spec_consumers(run),
            include_components=not run.host.track_gaps,
        )
    else:
        components = current_review._code_scope_tasks(run, change)
    scope_identity = (
        current_review._code_scope_identity(run)
        if mode == "code" and run.host.mode == "execute"
        else None
    )
    outputs = []

    affected_ids = set(components) if mode == "code" else set()
    allowed = {
        run.target.id,
        *run.target.uses,
        *affected_ids,
        *current_review.spec_consumers(run),
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

        child = current_review.Invocation(
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
            value = current_review._current_artifact(
                child, mode, previous.get("artifact")
            )
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

    from tests.concorde.support.legacy_graphs.batch_graph import run_batch_graph

    run_batch_graph(
        [None, *components.items()],
        review_module,
        name="scope_review_graph",
        item_node="review_module",
    )
    return current_review.aggregate_scope(
        run, mode, components, scope_identity, outputs
    )


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
