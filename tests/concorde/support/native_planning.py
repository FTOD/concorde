"""Domain-only adapter for existing injected stage doubles; NOT native integration evidence."""

from concorde.harness.host import OperationHost as RealHost


def domain_double(run):
    from types import MethodType

    from concorde.harness.change_worktree import progress
    from concorde.planning.plan import persist_plan_result
    from concorde.planning.tasks import persist_tasks, prepare_tasks, validate_tasks
    from concorde.review.review import require_spec_review
    from tests.concorde.support.legacy_stage import stage

    run.stage = MethodType(stage, run)
    if run.host.executor is None and run.host.mode != "describe-policy":
        raise AssertionError("domain fixture requires an injected executor")
    if run.operation in {"concorde-spec-review", "concorde-code-review"}:
        from tests.concorde.support.legacy_review import legacy_issue_review_scope

        return legacy_issue_review_scope(
            run, "spec" if run.operation == "concorde-spec-review" else "code"
        )
    if run.operation == "concorde-issues":
        from dataclasses import replace

        from concorde.harness.invocation import Invocation
        from concorde.issues.solve import IssueSolve
        from tests.concorde.support.legacy_review import legacy_issue_review_scope

        domain = IssueSolve(run)
        prepared = domain.prepare({})
        if prepared["route"] == "finish":
            return domain.finish({})["output"]
        while True:
            selected = domain.prepare_decision()
            if "selection" not in selected:
                return domain.finish({})["output"]
            result = run.stage("concorde-issues", inputs=(selected["selection"],))
            route = domain.accept_decision(result)["route"]
            if route == "finish":
                return domain.finish({})["output"]
            if route == "close":
                domain.close({})
                return domain.ready({})["output"]
            requests = domain.verification_requests()
            before = domain.current_inputs()
            outputs = []
            for mode, task in requests:
                child = Invocation(
                    "concorde-" + mode + "-review",
                    run.configuration,
                    task,
                    replace(run.host, coordinated=True, native_assessment=None),
                )
                outputs.append(legacy_issue_review_scope(child, mode))
                if outputs[-1]["data"]["outcome"] != "completed":
                    break
            route = domain.accept_verification(outputs, before)["route"]
            if route == "finish":
                return domain.finish({})["output"]
    if run.host.mode == "describe-policy":
        run.stage(run.operation)
        return run.response("described")
    if run.operation not in {
        "concorde-spec-review",
        "concorde-code-review",
        "concorde-context-solve",
    }:
        require_spec_review(run)
    if run.operation == "concorde-implement":
        from concorde.implementation.implement import (
            persist_implementation,
            prepare_implementation,
        )

        state, local, revisions, inputs, stopped = prepare_implementation(run)
        if stopped:
            return stopped
        if not local:
            return persist_implementation(
                run,
                {"tasks": [], "answer": "Components current"},
                state,
                local,
                revisions,
            )
        progress(
            run.repository.root,
            phase="implementation",
            status="active",
            invalidate=True,
        )
        value = run.stage(
            "concorde-implement", inputs=inputs, defer_gap_resolution=True
        )
        if value["outcome"] in {"completed", "sufficient"}:
            return persist_implementation(run, value, state, local, revisions)
    elif run.operation == "concorde-context-solve":
        value = run.stage(run.operation)
    elif run.operation == "concorde-plan":
        if not run.host.coordinated:
            progress(
                run.repository.root, phase="plan", status="active", invalidate=True
            )
        value = run.stage("concorde-context-solve")
        if value["outcome"] in {"completed", "sufficient"}:
            value = run.stage("concorde-plan", defer_gap_resolution=True)
            if (
                value["outcome"] in {"completed", "sufficient"}
                and run.host.mode != "describe-policy"
            ):
                return persist_plan_result(run, value)
    elif run.operation == "concorde-tasks":
        state, inputs, reserved, repair, scope = prepare_tasks(run)
        if not run.host.coordinated:
            progress(
                run.repository.root, phase="tasks", status="active", invalidate=True
            )
        value = run.stage("concorde-tasks", inputs=inputs, defer_gap_resolution=True)
        if (
            value["outcome"] in {"completed", "sufficient"}
            and run.host.mode != "describe-policy"
        ):
            validate_tasks(run, value, reserved)
            return persist_tasks(run, value, state, repair, scope)
    else:
        raise AssertionError("unsupported fixture operation")
    return run.response(
        "described"
        if run.host.mode == "describe-policy"
        else "completed"
        if value["outcome"] == "sufficient"
        else value["outcome"],
        value["answer"],
        blockers=value["blockers"],
    )


class OperationHost(RealHost):
    def __init__(self, *args, **kwargs):
        if (
            kwargs.get("executor") is not None
            or kwargs.get("mode") == "describe-policy"
        ) and "native_assessment" not in kwargs:
            kwargs["native_assessment"] = domain_double
        super().__init__(*args, **kwargs)
