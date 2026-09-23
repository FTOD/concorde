"""The Issue solver's Agent hook and the solve workflow hook of ``concorde-issues``.

Bookkeeping actions and the solve of an already closed Issue are served in place without a
Workflow (``bookkeeping.serve``). Solving an open Issue runs the solve workflow: at most six
iterations of a Host step that issues one solver slot, the solver, a Host step that admits its
decision and either finishes, closes and validates, or issues review slots, the reviewers, and a
Host step that admits every review of the iteration together. Every decision about state,
evidence and closure is Host code.
"""

from __future__ import annotations

import json
import re
import subprocess

from ..harness.invocation import Invocation, validate_stage_identity
from ..harness.native_driver import (
    StagePlan,
    WorkflowPlan,
    native_output_schema,
    stage_response,
    stop_plan,
)
from ..issues.store import read_issue
from .bookkeeping import MAX_DECISIONS, serve
from .solve import IssueSolve
from ..spec.repository import SpecError
from ..spec.typed_data import canonical

SLOT = re.compile(r"^(d-[0-5]|v-[0-5]-[0-3]-[0-9]+)$")
STEP = re.compile(r"^(next|decision|verified)-([0-5])$")
STEPS = tuple(
    f"{kind}-{index}"
    for index in range(MAX_DECISIONS)
    for kind in ("next", "decision", "verified")
)


class IssueSolverHook:
    """The Issue solver: its one stage input is the selection the solve workflow admitted."""

    def prepare(self, run, admitted):
        return StagePlan(stage_inputs=tuple(admitted or ()))

    def recheck(self, run, descriptor):
        selected = descriptor["stage_inputs"][0]["data"]
        if (
            read_issue(run.repository.root, selected["issue_id"])[1]
            != selected["revision"]
        ):
            raise SpecError("Issue changed during native decision", "stale_issue")

    def validate(self, run, snapshot, plan, data):
        validate_stage_identity(data, snapshot.id)

    def accept(self, run, snapshot, plan, data):
        run.completed.append("concorde-issues")
        return stage_response(run, data)


def _needs_workflow(task: dict) -> bool:
    return task["action"] == "solve" and not task.get("_issue_closed")


class IssuesWorkflowHook:
    """The solve workflow of ``concorde-issues``."""

    SCRIPT = "pi/workflows/issues.js"
    HOST = "pi/native-issue-host.mjs"
    HELPERS = ("pi/issue-call.mjs",)

    def serve_in_place(self, request) -> dict | None:
        """Bookkeeping needs no Workflow; a solve of an open Issue does."""
        if _needs_workflow(request.data):
            return None
        return serve(request)

    def prepare(self, run, driver):
        if run.host.mode == "describe-policy":
            return stop_plan(
                run.response(
                    "described",
                    "Native bounded Issue decisions and reviews with a journaled Host "
                    "disposition; no child ran.",
                )
            )
        domain = IssueSolve(run)
        if domain.prepare({})["route"] == "finish":
            return stop_plan(domain.finish({})["output"], accepted=True)
        driver.save(
            "issue-session",
            {
                "domain": domain.dump(),
                "iteration": 0,
                "phase": "next",
                "inventory": [],
                "groups": [],
            },
        )
        return WorkflowPlan(
            script=self.SCRIPT,
            host=self.HOST,
            steps=STEPS,
            helpers=self.HELPERS,
            expansion=_schemas() | {"directory": str(driver.directory)},
        )

    def on_failure(self, run, driver, native_state):
        return None

    def step(self, run, driver, name):
        match = STEP.fullmatch(name)
        if not match:
            raise SpecError("unknown Issue Host step", "invalid_input")
        step, index = match[1], int(match[2])
        state = driver.state("issue-session")
        if index != state["iteration"] or step != state["phase"]:
            raise SpecError("duplicate/stale Issue workflow step", "invalid_completion")
        domain = IssueSolve(run, state["domain"])
        domain.assert_current()
        layout = _layout(driver)
        driver.save("issue-layout", layout)
        route, counts, output = "decide", [0, 0, 0, 0], None
        if step == "next":
            route, output = self._next(run, driver, domain, state, layout, index)
        elif step == "decision":
            route, output, counts = self._decision(
                run, driver, domain, state, layout, index
            )
        else:
            route, output = self._verified(run, driver, domain, state)
        state["domain"] = domain.dump()
        if route == "finished":
            state["phase"] = "finished"
            driver.receipt({"state": "accepted", "accepted": True, "output": output})
            from ..harness.status_store import write_run

            write_run(
                run.repository.root,
                f".concorde/runs/{run.host.invocation_id}/native-issue.json",
                canonical(
                    {"descriptor": driver.descriptor, "state": state, "output": output}
                ).encode(),
            )
        driver.save("issue-session", state)
        return {
            "schema_version": 1,
            "ticket": driver.ticket,
            "iteration": index,
            "route": route,
            "groups": counts,
        }

    def _next(self, run, driver, domain, state, layout, index):
        prepared = domain.prepare_decision()
        if "selection" not in prepared:
            return "finished", domain.finish({})["output"]
        task = {
            **driver.descriptor["envelope"]["input"]["data"],
            "target_id": run.target.id,
            "task": run.task["task"],
            "change_id": run.change_id,
            "expected_revision": domain.solution["revision"],
        }
        key = f"d-{index}"
        _issue(
            driver,
            layout,
            key,
            "issue_solver",
            task,
            operation="concorde-issues",
            stage_inputs=(prepared["selection"],),
        )
        state["inventory"].append(key)
        state["phase"] = "decision"
        return "decide", None

    def _decision(self, run, driver, domain, state, layout, index):
        from ..review.native import scope_record
        from ..review.review import scope_members

        counts = [0, 0, 0, 0]
        driver.coverage(state["inventory"])
        value = driver.admit(f"d-{index}")
        _running(driver)
        decision = domain.accept_decision(value["proposal"]["result"]["data"])
        route = decision["route"]
        if route == "close":
            _running(driver)
            domain.close({})
            return "finished", domain.ready({})["output"], counts
        if route == "finish":
            return "finished", domain.finish({})["output"], counts
        if route != "verify":
            raise SpecError(
                f"unknown Issue decision route {route!r}", "invalid_completion"
            )
        requests = domain.verification_requests()
        state["verification_before"] = domain.current_inputs()
        state["groups"] = []
        for group, (mode, task) in enumerate(requests):
            # Fixed group indices keep spec/code and Issue-specific/ordinary identities.
            group_index = group if len(requests) == 4 else group * 2
            child = Invocation(
                "concorde-" + mode + "-review",
                run.configuration,
                task,
                run.host,
            )
            components, identity, members = scope_members(child, mode, initialize=True)
            keys = []
            for member, selected in enumerate(members):
                key = f"v-{index}-{group_index}-{member}"
                _issue(
                    driver,
                    layout,
                    key,
                    "spec_reviewer" if mode == "spec" else "code_reviewer",
                    selected,
                    operation=child.operation,
                )
                keys.append(key)
                state["inventory"].append(key)
            state["groups"].append(
                {
                    "scope": scope_record(
                        child, mode, components, identity, members, keys
                    )
                }
            )
            counts[group_index] = len(keys)
        state["phase"] = "verified"
        return "verify", None, counts

    def _verified(self, run, driver, domain, state):
        from ..review.native import commit_scope, current

        driver.coverage(state["inventory"])
        admitted = []
        for group in state["groups"]:
            scope = group["scope"]
            child = Invocation(
                scope["operation"],
                run.configuration,
                scope["parent_task"],
                run.host,
            )
            current(child, scope, driver, check_members=True)
            admitted.append(
                (child, scope, [driver.admit(key) for key in scope["keys"]])
            )
        # Recheck every input before publishing any scope.
        for child, scope, _ in admitted:
            current(child, scope, driver, check_members=True)
        outputs = []
        for child, scope, values in admitted:
            _running(driver)
            outputs.append(commit_scope(child, scope, values, driver))
        result = domain.accept_verification(outputs, state["verification_before"])
        if result["route"] == "finish":
            return "finished", domain.finish({})["output"]
        state["iteration"] += 1
        state["phase"] = "next"
        if state["iteration"] >= MAX_DECISIONS:
            domain.stop(
                "conflicting",
                "Issue solving reached its bounded decision limit; progress is retained.",
                "limit-exhausted",
            )
            return "finished", domain.finish({})["output"]
        return "decide", None


def _schemas() -> dict:
    return {
        "stageSchema": native_output_schema("concorde-agent-stage-result"),
        "reviewSchema": native_output_schema("concorde-review-stage-result"),
    }


def _layout(driver) -> dict:
    """What ``pi/issue-call.mjs`` builds a slot's call from, as the script receives it."""
    return {
        **_schemas(),
        "directory": str(driver.directory),
        "ticket": driver.ticket,
        "slot_gate": driver.slot_gate,
    }


def _running(driver) -> None:
    if driver.stopped():
        raise SpecError("Issue workflow stopped", "execution_cancelled")


def _issue(driver, layout, key, agent, task, *, operation, stage_inputs=()):
    """Issue one slot with the call ``pi/issue-call.mjs`` builds for its key."""
    if not SLOT.fullmatch(key):
        raise SpecError("invalid Issue slot index", "invalid_input")
    from pathlib import Path

    module = (Path(driver.package_root) / "pi/issue-call.mjs").as_uri()
    code = (
        "import {issueCall} from "
        + json.dumps(module)
        + ";console.log(JSON.stringify(issueCall("
        + canonical(layout)
        + ","
        + json.dumps(key)
        + ")))"
    )
    call = json.loads(
        subprocess.check_output(
            [driver.node, "--input-type=module", "-e", code], text=True
        )
    )
    return driver.issue_slot(
        key, agent, task, stage_inputs=stage_inputs, operation=operation, call=call
    )


issue_solver = IssueSolverHook()
issues_workflow = IssuesWorkflowHook()
