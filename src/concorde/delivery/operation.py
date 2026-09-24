"""The ``delivery`` Operation: commit a validated task worktree (see the Delivery Spec).

1. Require that the task worktree's head is the task branch.
2. Record a delivery commit at the branch head that the task record lacks, and stop.
3. Load the readiness of the task's latest ``validate`` run and require it to be ready.
4. Measure the inputs again through Validation and compare the input digest.
5. Require at least one uncommitted change.
6. Apply the readiness's confirmations through Validation.
7. Write the evidence bundle in the task worktree.
8. Stage everything and create the delivery commit; undo steps 6 and 7 when Git refuses.
9. Verify the new head, its parent and a clean worktree.
10. Record the delivery in the task record.
11. Return the delivery commit as the output.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from ..operations.provider import (
    Continue,
    Provider,
    RunContext,
    Stop,
    evidence,
    host_escalation,
)
from ..tasks import store
from ..validation import confirmations as confirming
from ..validation.measurement import (
    MeasurementError,
    has_uncommitted,
    head_commit,
    measure,
)
from ..validation.operation import measurement_failed, require_task_branch
from .bundle import (
    OUTPUT_SCHEMA,
    SUBJECT,
    build_bundle,
    bundle_path,
    commit_message,
    sequence_of,
)


@dataclass
class State:
    head: str = ""
    readiness_run: str = ""
    readiness: dict = field(default_factory=dict)
    backups: dict[str, bytes] = field(default_factory=dict)
    bundle: str = ""
    sequence: int = 0
    created: list[Path] = field(default_factory=list)
    commit: str = ""


def _state(ctx: RunContext) -> State:
    if not hasattr(ctx, "delivery"):
        ctx.delivery = State()
    return ctx.delivery


def _git(worktree: Path, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *arguments], cwd=worktree, capture_output=True, text=True, check=False
    )


def _blocked(code: str, summary: str, detail: str, options, kind="readiness") -> Stop:
    return Stop(
        "blocked",
        summary,
        [evidence(kind, code, detail)],
        host_escalation(
            f"{code}: {detail}",
            options=list(options),
            recommendation=options[0],
        ),
    )


def _failed(summary: str, found: list[dict], problem: str, options=()) -> Stop:
    return Stop(
        "failed", summary, found, host_escalation(problem, options=list(options))
    )


def check_branch(ctx: RunContext):
    outcome = require_task_branch(ctx)
    if isinstance(outcome, Stop):
        return outcome
    _state(ctx).head = head_commit(ctx.worktree)
    return Continue()


def _trailer(worktree: Path, commit: str, key: str) -> str:
    value = _git(
        worktree, "log", "-1", f"--format=%(trailers:key={key},valueonly)", commit
    ).stdout.strip()
    return value.splitlines()[-1].strip() if value else ""


def recover(ctx: RunContext):
    """Record a delivery commit of this task at the head that the task record lacks."""
    state = _state(ctx)
    task = store.load_task(ctx.primary, ctx.task["id"])
    if state.head in {item["commit"] for item in task["deliveries"]}:
        return Continue()
    subject = _git(ctx.worktree, "log", "-1", "--format=%s", state.head).stdout.strip()
    if subject != SUBJECT.format(task=ctx.task["id"]):
        return Continue()
    if _trailer(ctx.worktree, state.head, "Concorde-Task") != ctx.task["id"]:
        return Continue()
    bundle = _trailer(ctx.worktree, state.head, "Concorde-Evidence")
    readiness_run = _trailer(ctx.worktree, state.head, "Concorde-Readiness")
    sequence = sequence_of(bundle)
    if not bundle or not readiness_run or sequence is None:
        return Continue()
    found = [
        evidence(
            "commit", state.head, "delivery commit at the branch head, not recorded"
        )
    ]
    try:
        store.record_delivery(
            ctx.primary, ctx.task["id"], ctx.run_id, state.head, bundle, readiness_run
        )
    except store.TaskError as error:
        return _failed(
            f"The unrecorded delivery commit {state.head} could not be recorded "
            f"({error.code}).",
            found + [evidence("record", error.code, str(error))],
            f"the task record cannot be written: {error}",
            ["repair the task record and run delivery again"],
        )
    ctx.output = {
        "commit": state.head,
        "branch": ctx.task["branch"],
        "bundle": bundle,
        "sequence": sequence,
        "confirmed": [],
        "recovered": True,
    }
    return Stop(
        "ok",
        f"Recovered the delivery commit {state.head[:12]} that the task record lacked.",
        found + [evidence("record", ctx.task["id"], "delivery recorded")],
    )


def load_readiness(ctx: RunContext):
    state = _state(ctx)
    task = store.load_task(ctx.primary, ctx.task["id"])
    runs = [run for run in task["runs"] if run["operation"] == "validate"]
    options = [
        "run validate on the task",
        "fix the blocking findings and validate again",
    ]
    if not runs:
        return _blocked(
            "no_readiness",
            "The task has no validate run (no_readiness); nothing was delivered.",
            f"task {ctx.task['id']} has no validate run",
            options,
        )
    latest = runs[-1]["run_id"]
    path = ctx.primary / ".concorde/runs" / latest / "result.json"
    try:
        result = json.loads(path.read_text())
    except (OSError, ValueError):
        result = {}
    # A ready readiness ends ok; a not-ready one ends blocked and still carries the readiness.
    readiness = (
        result.get("output") if result.get("status") in ("ok", "blocked") else None
    )
    if not isinstance(readiness, dict) or readiness.get("task") != ctx.task["id"]:
        return _blocked(
            "no_readiness",
            f"The latest validate run {latest} produced no readiness (no_readiness); "
            "nothing was delivered.",
            f"{latest} ended {result.get('status', runs[-1]['status'])} without a readiness",
            options,
        )
    if not readiness.get("ready"):
        blocking = readiness.get("blocking") or []
        return _blocked(
            "not_ready",
            f"The latest readiness ({latest}) is not ready (not_ready); nothing was "
            "delivered.",
            f"{latest}: {len(blocking)} blocking finding(s): "
            + "; ".join(f"{item['kind']} {item['ref']}" for item in blocking[:10]),
            ["fix the blocking findings and run validate again"],
        )
    state.readiness_run, state.readiness = latest, readiness
    return Continue(evidence=[evidence("readiness", latest, "ready")])


def compare_inputs(ctx: RunContext):
    state = _state(ctx)
    try:
        now = measure(ctx.worktree, ctx.task["base_commit"])
    except MeasurementError as error:
        return measurement_failed(ctx, error)
    recorded = state.readiness["inputs"]["digest"]
    if now["digest"] != recorded:
        before = {
            item["path"]: item["digest"]
            for item in state.readiness["inputs"]["changed"]
        }
        after = {item["path"]: item["digest"] for item in now["changed"]}
        moved = sorted(
            path
            for path in before.keys() | after.keys()
            if before.get(path) != after.get(path)
        )
        detail = f"readiness {state.readiness_run} has input digest {recorded}, now {now['digest']}"
        if moved:
            detail += "; changed since: " + ", ".join(moved[:20])
        elif now["head"] != state.readiness["inputs"]["head"]:
            detail += f"; the head moved to {now['head']}"
        return _blocked(
            "stale_readiness",
            "The task worktree changed since its readiness (stale_readiness); nothing was "
            "delivered.",
            detail,
            ["run validate again, then delivery"],
        )
    return Continue(
        evidence=[evidence("readiness", recorded, "input digest unchanged")]
    )


def require_changes(ctx: RunContext):
    try:
        changed = has_uncommitted(ctx.worktree)
    except MeasurementError as error:
        return measurement_failed(ctx, error)
    if not changed:
        return _blocked(
            "nothing_to_deliver",
            "The task worktree has no uncommitted change (nothing_to_deliver).",
            f"{ctx.worktree} is clean at {_state(ctx).head}",
            ["do more work on the task, or close it"],
            kind="git",
        )
    return Continue()


def apply_confirmations(ctx: RunContext):
    state = _state(ctx)
    listed = state.readiness["confirmations"]
    try:
        state.backups = confirming.apply(ctx.worktree, listed)
    except confirming.ConfirmationRefused as error:
        return _failed(
            f"The confirmations could not be applied ({error.code}); nothing was committed.",
            [evidence("readiness", error.code, str(error))],
            f"confirmations of {state.readiness_run} refused: {error}",
            ["run validate again, then delivery"],
        )
    return Continue(
        evidence=[
            evidence("readiness", item["entry"], f"confirmed in {item['metadata']}")
            for item in listed
        ]
    )


def write_bundle(ctx: RunContext):
    state = _state(ctx)
    task = store.load_task(ctx.primary, ctx.task["id"])
    state.sequence = len(task["deliveries"]) + 1
    state.bundle = bundle_path(ctx.task["id"], state.sequence)
    target = ctx.worktree / state.bundle
    if target.exists():
        undo(ctx)
        return _failed(
            f"The evidence bundle {state.bundle} already exists; nothing was committed.",
            [evidence("git", state.bundle, "bundle path taken")],
            f"{state.bundle} exists although the task record lists "
            f"{state.sequence - 1} deliveries",
            ["inspect the task branch and the task record"],
        )
    value = build_bundle(
        ctx.primary,
        task,
        run_id=ctx.run_id,
        sequence=state.sequence,
        parent=state.head,
        readiness_run=state.readiness_run,
        readiness=state.readiness,
        confirmations=state.readiness["confirmations"],
    )
    for directory in reversed(target.parents):
        if directory.is_relative_to(ctx.worktree) and not directory.exists():
            directory.mkdir()
            state.created.append(directory)
    target.write_text(json.dumps(value, indent=2) + "\n")
    state.created.append(target)
    return Continue()


def undo(ctx: RunContext) -> None:
    """Restore the confirmed metadata, remove the bundle and reset the index to the head."""
    state = _state(ctx)
    confirming.restore(ctx.worktree, state.backups)
    for path in reversed(state.created):
        if path.is_dir():
            try:
                path.rmdir()
            except OSError:
                pass
        else:
            path.unlink(missing_ok=True)
    _git(ctx.worktree, "reset", "-q")


def commit(ctx: RunContext):
    state = _state(ctx)
    found = []
    staged = _git(ctx.worktree, "add", "-A")
    if staged.returncode == 0:
        staged = _git(ctx.worktree, "add", "-f", "--", state.bundle)
    if staged.returncode != 0:
        undo(ctx)
        return _failed(
            "Git could not stage the delivery; the worktree was restored.",
            [evidence("git", "add", staged.stderr.strip())],
            f"git add failed: {staged.stderr.strip()}",
        )
    message = commit_message(ctx.task, state.bundle, state.readiness_run)
    result = subprocess.run(
        ["git", "commit", "-q", "--cleanup=verbatim", "-F", "-"],
        cwd=ctx.worktree,
        input=message,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        output = (result.stdout + result.stderr).strip()
        undo(ctx)
        return _failed(
            "Git refused the delivery commit; the confirmations and the bundle were undone "
            "and the index reset.",
            found
            + [
                evidence("git", "commit", output[-4000:] or f"exit {result.returncode}")
            ],
            f"git commit failed: {output[-1000:]}",
            ["fix the commit hook or the author identity, then run delivery again"],
        )
    state.commit = head_commit(ctx.worktree)
    return Continue(evidence=[evidence("commit", state.commit, f"parent {state.head}")])


def verify(ctx: RunContext):
    state = _state(ctx)
    problems = []
    branch = _git(ctx.worktree, "symbolic-ref", "-q", "HEAD").stdout.strip()
    if branch != f"refs/heads/{ctx.task['branch']}":
        problems.append(f"head is {branch or 'detached'}")
    parents = _git(
        ctx.worktree, "rev-list", "--parents", "-n", "1", state.commit
    ).stdout.split()
    if parents[1:] != [state.head]:
        problems.append(f"parents {parents[1:]} instead of {state.head}")
    if head_commit(ctx.worktree) != state.commit:
        problems.append("the new commit is not the branch head")
    if has_uncommitted(ctx.worktree):
        problems.append("the worktree is not clean after the commit")
    if problems:
        return _failed(
            f"The delivery commit {state.commit} does not verify.",
            [evidence("git", state.commit, "; ".join(problems))],
            "; ".join(problems),
            ["inspect the task branch"],
        )
    return Continue()


def record(ctx: RunContext):
    state = _state(ctx)
    try:
        store.record_delivery(
            ctx.primary,
            ctx.task["id"],
            ctx.run_id,
            state.commit,
            state.bundle,
            state.readiness_run,
        )
    except store.TaskError as error:
        return _failed(
            f"The delivery commit {state.commit} was made but not recorded ({error.code}); "
            "the next delivery run records it.",
            [evidence("record", error.code, str(error))],
            f"the task record cannot be written: {error}",
            ["run delivery again to record the commit"],
        )
    return Continue(evidence=[evidence("record", ctx.task["id"], "delivery recorded")])


def output(ctx: RunContext):
    state = _state(ctx)
    ctx.output = {
        "commit": state.commit,
        "branch": ctx.task["branch"],
        "bundle": state.bundle,
        "sequence": state.sequence,
        "confirmed": [item["entry"] for item in state.readiness["confirmations"]],
        "recovered": False,
    }
    return Stop(
        "ok",
        f"Delivered {ctx.task['id']} as {state.commit[:12]} on {ctx.task['branch']} "
        f"with {state.bundle}.",
    )


DELIVERY = Provider(
    name="delivery",
    task_type=None,
    writes=False,
    steps=(
        check_branch,
        recover,
        load_readiness,
        compare_inputs,
        require_changes,
        apply_confirmations,
        write_bundle,
        commit,
        verify,
        record,
        output,
    ),
    output_schema=OUTPUT_SCHEMA,
)


__all__ = ["DELIVERY"]
