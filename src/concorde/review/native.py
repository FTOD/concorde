"""The reviewers' Agent hooks and the review workflow hook.

A reviewer's stage adds one typed review input to its Module's frozen context. The review workflow
prepares one reviewer per scope member, checks every member before the reviewers run, and accepts
the whole scope only after every member's proposal was independently admitted and every input
rechecked. A partially run scope is never accepted as complete.
"""

from __future__ import annotations


from ..harness.context import ContextSnapshot, recheck_context
from ..harness.invocation import Invocation
from ..harness.native_driver import (
    StagePlan,
    WorkflowPlan,
    candidate_input_digest,
    stop_plan,
)
from ..spec.repository import SpecError
from ..spec.typed_data import canonical
from .review import (
    _failed_review,
    _validate,
    accept_review_result,
    aggregate_scope,
    inputs,
    review_agent,
    scope_members,
)


class ReviewerHook:
    """One reviewer of one Module: its stage is the Module's context plus the review input."""

    def __init__(self, mode: str):
        self.mode = mode

    def prepare(self, run, admitted):
        return StagePlan(review_input=inputs(run, self.mode))

    def recheck(self, run, descriptor):
        return None

    def validate(self, run, snapshot, plan, data):
        _validate(run, snapshot, plan.review_input, data)

    def accept(self, run, snapshot, plan, data):
        return accept_review_result(run, snapshot, plan.review_input, data)


def member_keys(scope: dict) -> list[str]:
    return list(scope["keys"])


def scope_record(run, mode, components, identity, members, keys) -> dict:
    """The saved review scope a later step rechecks and accepts."""
    return {
        "operation": run.operation,
        "mode": mode,
        "parent_task": run.task,
        "configuration": run.configuration,
        "components": components,
        "scope_identity": identity,
        "members": members,
        "keys": keys,
        "candidate_digest": candidate_input_digest(run.repository.root),
        "parent_spec": run.repository.spec_context(run.target.id).value,
    }


def _member(run, scope, task) -> Invocation:
    return Invocation(
        scope["operation"],
        scope["configuration"],
        task,
        run.host,
    )


def current(run, scope: dict, driver, *, check_members: bool = False) -> None:
    """Refuse with ``stale_context`` when the scope, or any member's input, changed."""
    from ..harness.configuration import load_configuration

    if load_configuration(run.repository.root) != scope["configuration"]:
        raise SpecError("review configuration changed", "configuration_mismatch")
    components, identity, members = scope_members(run, scope["mode"])
    if (
        components != scope["components"]
        or identity != scope["scope_identity"]
        or members != scope["members"]
        or run.repository.spec_context(run.target.id).value != scope["parent_spec"]
        or candidate_input_digest(run.repository.root) != scope["candidate_digest"]
    ):
        raise SpecError("native aggregate review scope changed", "stale_context")
    if check_members:
        for task, key in zip(scope["members"], scope["keys"], strict=True):
            slot = driver.slot(key)
            child = _member(run, scope, task)
            recheck_context(
                child.repository, ContextSnapshot(canonical(slot["snapshot"]))
            )
            if inputs(child, scope["mode"]) != slot["review_input"]:
                raise SpecError(
                    "review member changed before aggregate acceptance", "stale_context"
                )


def failed_scope(run, scope: dict, error) -> dict:
    """An ``incomplete`` result for every member, aggregated."""
    outputs = []
    for task in scope["members"]:
        child = _member(run, scope, task)
        outputs.append(
            _failed_review(child, inputs(child, scope["mode"]), error)["data"]
        )
    return aggregate_scope(
        run, scope["mode"], scope["components"], scope["scope_identity"], outputs
    )


def commit_scope(run, scope: dict, admitted: list[dict], driver) -> dict:
    """Accept every admitted member's result and aggregate the scope."""
    outputs = []
    for task, key, value in zip(scope["members"], scope["keys"], admitted, strict=True):
        slot = driver.slot(key)
        child = _member(run, scope, task)
        snapshot = ContextSnapshot(canonical(slot["snapshot"]))
        child.last_context = snapshot.id
        outputs.append(
            accept_review_result(
                child,
                snapshot,
                slot["review_input"],
                value["proposal"]["result"]["data"],
            )["data"]
        )
    return aggregate_scope(
        run, scope["mode"], scope["components"], scope["scope_identity"], outputs
    )


def issue_members(driver, run, mode: str, prefix: str, *, initialize=True):
    """Issue one reviewer slot per scope member, keyed ``<prefix><index>``."""
    components, identity, members = scope_members(run, mode, initialize=initialize)
    agent = review_agent(mode)
    keys, calls = [], []
    for index, task in enumerate(members):
        key = f"{prefix}{index}"
        calls.append(
            driver.issue_slot(
                key,
                agent,
                {k: v for k, v in task.items() if v is not None},
                operation=run.operation,
            )
        )
        keys.append(key)
    return scope_record(run, mode, components, identity, members, keys), calls


class ReviewWorkflowHook:
    """The review workflow of both reviews."""

    SCRIPT = "pi/workflows/review.js"
    HOST = "pi/native-review-host.mjs"
    STEPS = ("bind", "finalize")

    @staticmethod
    def mode(run) -> str:
        return "spec" if run.operation == "concorde-spec-review" else "code"

    def prepare(self, run, driver):
        mode = self.mode(run)
        if run.host.mode == "describe-policy":
            _, _, members = scope_members(run, mode, initialize=True)
            return stop_plan(
                run.response(
                    "described",
                    "Fresh native reviewers with a prompt-level read-only file policy for: "
                    + ", ".join(task["target_id"] for task in members)
                    + "; no reviewer ran.",
                )
            )
        _, _, members = scope_members(run, mode, initialize=True)
        if not members:
            raise SpecError(
                "review scope contains no executable reviewer", "unsupported_target"
            )
        scope, calls = issue_members(driver, run, mode, "review-", initialize=False)
        driver.save("review-scope", scope)
        return WorkflowPlan(
            script=self.SCRIPT,
            host=self.HOST,
            steps=self.STEPS,
            expansion={
                "schema": calls[0]["outputSchema"],
                "members": [
                    {
                        "ticket": driver.slot(key)["ticket"],
                        "call": {k: v for k, v in call.items() if k != "outputSchema"},
                    }
                    for key, call in zip(scope["keys"], calls, strict=True)
                ],
            },
        )

    def step(self, run, driver, name):
        scope = driver.state("review-scope")
        current(run, scope, driver)
        if name == "bind":
            for key in scope["keys"]:
                driver.check(key)
            return {"state": "ready"}
        driver.coverage(scope["keys"])
        admitted = [driver.admit(key) for key in scope["keys"]]
        # Recheck every member after the individual admissions, so none went stale meanwhile.
        current(run, scope, driver, check_members=True)
        driver.reserve("aggregate-terminal")
        output = commit_scope(run, scope, admitted, driver)
        from ..harness.status_store import write_run

        write_run(
            run.repository.root,
            f".concorde/runs/{run.host.invocation_id}/native-reviews.json",
            canonical(
                {"scope": scope, "admitted": admitted, "output": output}
            ).encode(),
        )
        driver.receipt({"state": "accepted", "accepted": True, "output": output})
        return {
            "state": "finished",
            "accepted": True,
            "outcome": output["data"]["outcome"],
            "reviewers": len(admitted),
        }

    def on_failure(self, run, driver, native_state):
        scope = driver.state("review-scope")
        current(run, scope, driver)
        output = failed_scope(
            run,
            scope,
            SpecError(
                "native scope failed or did not cover every reviewer",
                "execution_failed",
            ),
        )
        return {"state": "failed", "accepted": False, "output": output}


spec_reviewer = ReviewerHook("spec")
code_reviewer = ReviewerHook("code")
review_workflow = ReviewWorkflowHook()
