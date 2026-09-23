"""The programmer's Agent hook.

It supplies the programmer's stage inputs, stops before any Agent starts when a check decides the
outcome (a pending gap, missing component work, or no local task left), validates the answer and
records task completion. The programmer call is bound to the admitted snapshot: its own files may
change during the run, while every other input must stay as prepared.
"""

from __future__ import annotations

from ..harness.change_worktree import progress
from ..harness.invocation import validate_stage_identity
from ..harness.native_driver import StagePlan, stage_response
from ..planning.gaps import record_gaps
from ..planning.hooks import with_issue_context
from .implement import (
    persist_implementation,
    prepare_implementation,
    validate_implementation,
)

SUCCESS = {"completed", "sufficient"}


class ProgrammerHook:
    def prepare(self, run, admitted):
        work, local, revisions, inputs, stopped = prepare_implementation(
            run, admitted_inputs=None if admitted is None else list(admitted)
        )
        if stopped is not None:
            return StagePlan(stop=stopped)
        if admitted is None:
            inputs = with_issue_context(run, inputs)
            if not local and run.host.mode == "execute":
                # Only current component work: completion is recorded without a programmer.
                return StagePlan(
                    stop=persist_implementation(
                        run,
                        {
                            "tasks": [],
                            "answer": "Separately completed components are current; "
                            "checks and reviews remain separate.",
                        },
                        work,
                        local,
                        revisions,
                    ),
                    stop_accepted=True,
                )
            if run.host.mode == "execute" and not run.host.coordinated:
                progress(
                    run.repository.root,
                    phase="implementation",
                    status="active",
                    invalidate=True,
                )
        return StagePlan(stage_inputs=tuple(inputs), bind_admitted_snapshot=True)

    def recheck(self, run, descriptor):
        return None

    def validate(self, run, snapshot, plan, data):
        validate_stage_identity(data, snapshot.id)
        if data["outcome"] in SUCCESS:
            local = prepare_implementation(
                run, admitted_inputs=list(plan.stage_inputs)
            )[1]
            validate_implementation(run, data, local)

    def accept(self, run, snapshot, plan, data):
        run.completed.append("concorde-implement")
        if data["outcome"] in SUCCESS:
            state, local, revisions, _, _ = prepare_implementation(
                run, admitted_inputs=list(plan.stage_inputs)
            )
            return persist_implementation(run, data, state, local, revisions)
        if data["blockers"]:
            record_gaps(run, "implementation", data["blockers"])
        return stage_response(run, data)


programmer = ProgrammerHook()
