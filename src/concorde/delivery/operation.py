"""The ``delivery`` Operation: validate a whole task, then commit it (see the Delivery Spec).

1. Require that the task worktree's head is the task branch.
2. Record a delivery commit at the branch head that the task record lacks, and stop.
3. Require new work: a commit since the previous delivery (or the base), or an uncommitted change.
4. Decide the readiness of the whole task with Validation's steps, as ``validate`` does.
5. Require that readiness to be ready.
6. Apply the readiness's confirmations through Validation.
7. Write the evidence bundle in the task worktree.
8. Stage everything and create the delivery commit; undo steps 6 and 7 when Git refuses.
9. Verify the new head, its parent and a clean worktree.
10. Record the delivery in the task record.
11. Return the delivery commit as the output.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from ..operations.provider import (
    Continue,
    Provider,
    RunContext,
    Stop,
    component,
    evidence,
)
from ..tasks import store
from ..validation import confirmations as confirming
from ..validation.measurement import (
    MeasurementError,
    has_uncommitted,
    head_commit,
    special_paths,
)
from ..validation.operation import (
    READINESS_STEPS,
    measurement_failed,
    not_deliverable,
    readiness_of,
    require_task_branch,
)
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


def _blocked(
    ctx: RunContext,
    code: str,
    summary: str,
    detail: str,
    options,
    *,
    explanation: str,
    kind="readiness",
    causes=(),
) -> Stop:
    """Stop ``blocked`` without writing anything; ``explanation`` says why for this code."""
    return ctx.fail(
        "blocked",
        code,
        summary,
        detail,
        reason="decision",
        explanation=explanation,
        evidence=[evidence(kind, code, detail)],
        causes=causes,
        options=list(options),
    )


def _failed(
    ctx: RunContext,
    code: str,
    summary: str,
    found: list[dict],
    detail: str,
    options=(),
    *,
    reason: str = "environment",
    explanation: str = "Git or the task record refused a change delivery needs; delivery "
    "undoes what it did and cannot repair either",
    causes=(),
) -> Stop:
    return ctx.fail(
        "failed",
        code,
        summary,
        detail,
        reason=reason,
        explanation=explanation,
        evidence=found,
        causes=causes,
        options=list(options),
    )


def _git_link(command: str, result: subprocess.CompletedProcess) -> dict:
    output = ((result.stdout or "") + (result.stderr or "")).strip()
    return component(
        f"git {command}",
        "git_failed",
        f"git {command} in the task worktree exited {result.returncode}: "
        + (output[-2000:] or "(no output)"),
        "environment",
        "Git refused the command",
    )


def _record_link(error: store.TaskError) -> dict:
    return component(
        "Tasks",
        error.code,
        str(error),
        "environment",
        "the task record could not be changed",
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
            ctx,
            "record_failed",
            f"The unrecorded delivery commit {state.head} could not be recorded "
            f"({error.code}).",
            found + [evidence("record", error.code, str(error))],
            f"the delivery commit {state.head} at the head of {ctx.task['branch']} is missing "
            f"from the task record, and recording it failed: {error.code}: {error}",
            ["repair the task record and run delivery again"],
            causes=[_record_link(error)],
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


def require_new_work(ctx: RunContext):
    """Continue when the head moved past the previous delivery (or the base) or a change waits."""
    state = _state(ctx)
    task = store.load_task(ctx.primary, ctx.task["id"])
    try:
        changed = has_uncommitted(ctx.worktree)
    except MeasurementError as error:
        return measurement_failed(ctx, error)
    if task["deliveries"]:
        since, what = task["deliveries"][-1]["commit"], "the previous delivery commit"
    else:
        since, what = ctx.task["base_commit"], "the task's base commit"
    if changed or state.head != since:
        return Continue()
    return _blocked(
        ctx,
        "nothing_to_deliver",
        "The task has no commit or change since "
        + ("its previous delivery" if task["deliveries"] else "its base")
        + " (nothing_to_deliver).",
        f"{ctx.worktree} is clean and its head {state.head} is {what}, so the task branch "
        "holds nothing that was not delivered",
        ["do more work on the task, or close it"],
        explanation="delivery validates and commits new work only, and the task has none; "
        "whether to do more work or close the task is the main agent's decision",
        kind="git",
    )


def decide(ctx: RunContext):
    """Take the readiness Validation's steps decided; stop ``blocked`` when it is not ready."""
    state = _state(ctx)
    readiness, found = readiness_of(ctx)
    state.readiness_run, state.readiness = ctx.run_id, readiness
    if readiness["ready"]:
        return Continue(evidence=found)
    blocking = readiness["blocking"]
    stop = _blocked(
        ctx,
        "not_ready",
        f"The task is not ready: {len(blocking)} blocking finding(s) (not_ready); nothing "
        "was delivered.",
        f"validating task {ctx.task['id']} as a whole found {len(blocking)} blocking "
        "finding(s): "
        + "; ".join(
            f"{item['kind']} {item['ref']}: {item['detail']}" for item in blocking
        ),
        [
            "repair each blocking finding in the task worktree and run delivery again",
            "run specify for a Spec finding, implement for a code or check finding",
        ],
        explanation="delivery validates the whole task before it commits and never repairs a "
        "finding; each needs a Spec or code change the main agent chooses",
        causes=[not_deliverable(ctx)],
    )
    stop.evidence[:0] = found
    return stop


SCENARIO_HEADING = re.compile(r"^### (scenario\.[a-z0-9][a-z0-9.-]*)\b", re.MULTILINE)
NEXT_HEADING = re.compile(r"^#{1,3} ", re.MULTILINE)


def scenario_blocks(text: str) -> dict[str, str]:
    """Each scenario of a reading document with its heading and steps, by identity."""
    blocks = {}
    for match in SCENARIO_HEADING.finditer(text):
        following = NEXT_HEADING.search(text, match.end())
        end = following.start() if following else len(text)
        blocks[match.group(1)] = text[match.start() : end].strip()
    return blocks


def require_verified_scenarios(ctx: RunContext):
    """A task that changes code delivers only when every scenario it added or changed is
    verified by a test; an adoption task, which describes code as it is, is exempt."""
    from ..spec.repository import SpecRepository
    from ..spec.repository_base import bound_by
    from ..spec.validation import validate_repository

    workflow = ctx.task.get("workflow")
    if isinstance(workflow, dict) and workflow.get("name") == "brownfield":
        return Continue(
            evidence=[
                evidence(
                    "scenario-tests",
                    "exempt",
                    "an adoption task describes existing code; linking its tests is best effort",
                )
            ]
        )
    base = ctx.task.get("base_commit") or ""
    changed = sorted(
        {
            *_git(ctx.worktree, "diff", "--name-only", base).stdout.split(),
            *_git(
                ctx.worktree, "ls-files", "--others", "--exclude-standard"
            ).stdout.split(),
        }
    )
    repository = SpecRepository(ctx.worktree)
    entries = [
        entry
        for module in repository.modules
        for entry in repository.implementation_scope(module)
    ]
    code = [
        path
        for path in changed
        if not path.startswith(("specs/", ".concorde/"))
        and any(bound_by(entry, path) for entry in entries)
    ]
    if not code:
        return Continue(
            evidence=[evidence("scenario-tests", "no-code", "the task changed no code")]
        )
    touched: dict[str, str] = {}
    for path in changed:
        if not path.endswith(".md") or not (ctx.worktree / path).is_file():
            continue
        before = _git(ctx.worktree, "show", f"{base}:{path}").stdout
        now = scenario_blocks((ctx.worktree / path).read_text(encoding="utf-8"))
        earlier = scenario_blocks(before)
        for identity, block in now.items():
            if earlier.get(identity) != block:
                touched[identity] = path
    unverified = sorted(
        {
            finding.subject_id
            for finding in validate_repository(ctx.worktree).findings
            if finding.rule_id == "CONCORDE-COVERAGE-001"
            and finding.subject_id in touched
        }
    )
    if not unverified:
        return Continue(
            evidence=[
                evidence(
                    "scenario-tests",
                    "verified",
                    f"{len(touched)} added or changed scenario(s), each verified by a test",
                )
            ]
        )
    listing = "; ".join(f"{identity} ({touched[identity]})" for identity in unverified)
    return _blocked(
        ctx,
        "unverified_scenarios",
        f"{len(unverified)} scenario(s) the task added or changed have no test "
        "(unverified_scenarios); nothing was delivered.",
        f"task {ctx.task['id']} changes code ({', '.join(code[:5])}"
        + (", ..." if len(code) > 5 else "")
        + ") while no test declares that it verifies these scenarios it added or changed: "
        + listing,
        [
            "run implement to add a test for each named scenario, in a file its Module binds, "
            "declaring the scenario it verifies",
            "if a scenario should not change, restore it with specify",
        ],
        explanation="delivery accepts a code change only when every promise the task added or "
        "changed is checked by a test, so that no scenario ships unverified",
        kind="scenario-tests",
    )


def apply_confirmations(ctx: RunContext):
    state = _state(ctx)
    listed = state.readiness["confirmations"]
    try:
        state.backups = confirming.apply(ctx.worktree, listed)
    except confirming.ConfirmationRefused as error:
        return _failed(
            ctx,
            "confirmations_refused",
            f"The confirmations could not be applied ({error.code}); nothing was committed.",
            [evidence("readiness", error.code, str(error))],
            f"the pending confirmations of readiness {state.readiness_run} could not be "
            f"applied: {error.code}: {error}",
            ["run delivery again"],
            reason="input",
            explanation="delivery applies exactly the confirmations its readiness lists and "
            "never recomputes them",
            causes=[
                component(
                    "Validation confirmations",
                    error.code,
                    str(error),
                    "input",
                    "the metadata no longer matches what the readiness confirmed",
                )
            ],
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
            ctx,
            "bundle_exists",
            f"The evidence bundle {state.bundle} already exists; nothing was committed.",
            [evidence("git", state.bundle, "bundle path taken")],
            f"the evidence bundle {state.bundle} already exists in {ctx.worktree} although "
            f"the task record lists {state.sequence - 1} deliveries",
            ["inspect the task branch and the task record"],
            reason="decision",
            explanation="delivery never overwrites evidence; reconciling the branch and the "
            "task record is the main agent's decision",
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
    # New paths Git cannot version, such as a sandbox's /dev/null mounts, are no content of the
    # task and would make git add refuse the whole delivery.
    try:
        special = special_paths(ctx.worktree)
    except MeasurementError as error:
        undo(ctx)
        return measurement_failed(ctx, error)
    excluded = [f":(exclude,literal){path}" for path in special]
    staged = _git(ctx.worktree, "add", "-A", "--", ".", *excluded)
    if staged.returncode == 0:
        staged = _git(ctx.worktree, "add", "-f", "--", state.bundle)
    if staged.returncode != 0:
        undo(ctx)
        return _failed(
            ctx,
            "stage_failed",
            "Git could not stage the delivery; the worktree was restored.",
            [evidence("git", "add", staged.stderr.strip())],
            f"git add failed in {ctx.worktree}, so nothing was committed; the confirmations "
            f"and the bundle were undone: {staged.stderr.strip()}",
            ["repair the worktree's Git state, then run delivery again"],
            causes=[_git_link("add", staged)],
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
            ctx,
            "commit_failed",
            "Git refused the delivery commit; the confirmations and the bundle were undone "
            "and the index reset.",
            found
            + [
                evidence("git", "commit", output[-4000:] or f"exit {result.returncode}")
            ],
            f"git commit refused the delivery commit of task {ctx.task['id']} in "
            f"{ctx.worktree}; the confirmations and the bundle were undone and the index "
            f"reset: {output[-1000:] or f'exit {result.returncode}'}",
            ["fix the commit hook or the author identity, then run delivery again"],
            causes=[_git_link("commit", result)],
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
            ctx,
            "commit_unverified",
            f"The delivery commit {state.commit} does not verify.",
            [evidence("git", state.commit, "; ".join(problems))],
            f"the delivery commit {state.commit} on {ctx.task['branch']} does not verify: "
            + "; ".join(problems),
            ["inspect the task branch"],
            reason="decision",
            explanation="delivery never rewrites a commit it made; repairing the branch is the "
            "main agent's decision",
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
            ctx,
            "record_failed",
            f"The delivery commit {state.commit} was made but not recorded ({error.code}); "
            "the next delivery run records it.",
            [evidence("record", error.code, str(error))],
            f"the delivery commit {state.commit} was made on {ctx.task['branch']} but the task "
            f"record could not be written: {error.code}: {error}",
            ["run delivery again to record the commit"],
            causes=[_record_link(error)],
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
        require_new_work,
        *READINESS_STEPS,
        decide,
        require_verified_scenarios,
        apply_confirmations,
        write_bundle,
        commit,
        verify,
        record,
        output,
    ),
    output_schema=OUTPUT_SCHEMA,
    # Validation's steps diagnose Specs that cannot be loaded, as validate does.
    requires_loaded_specs=False,
)


__all__ = ["DELIVERY"]
