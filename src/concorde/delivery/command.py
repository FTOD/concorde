"""``concorde delivery``: validate a whole workspace, then commit it (see the Delivery Spec).

A recorded command of the bound workspace; it launches no worker. The delivery commits on the
bound branch are its only record: their subject and trailers name the workspace, the evidence
bundle and the run that decided the readiness.

1. Require that the workspace's head is its bound branch.
2. Stop ``ok`` when the head already is a delivery commit of the workspace and nothing waits.
3. Require new work: a commit since the base, or an uncommitted change.
4. Decide the readiness of the whole workspace with Validation's steps, as task-validation does.
5. Require that readiness to be ready, and every scenario changed with code to be verified.
6. Apply the readiness's confirmations through Validation.
7. Write the evidence bundle in the workspace.
8. Stage everything and create the delivery commit; undo steps 6 and 7 when Git refuses.
9. Verify the new head, its parent and a clean worktree.
10. Return the delivery commit as the output.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from ..execution.context import (
    Continue,
    RunContext,
    Stop,
    command,
    component,
    evidence,
)
from ..execution.runs import workspace_runs
from ..validation import confirmations as confirming
from ..validation.command import (
    READINESS_STEPS,
    measurement_failed,
    not_deliverable,
    readiness_of,
    require_bound_branch,
)
from ..validation.measurement import (
    MeasurementError,
    has_uncommitted,
    head_commit,
    special_paths,
)
from .bundle import (
    OUTPUT_SCHEMA,
    build_bundle,
    bundle_path,
    commit_message,
    delivery_commits,
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
    # The workspace's earlier delivery commits, read once from Git.
    previous: list[dict] | None = None


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
    explanation: str = "Git refused a change delivery needs; delivery undoes what it did and "
    "cannot repair it",
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
        f"git {command} in the workspace exited {result.returncode}: "
        + (output[-2000:] or "(no output)"),
        "environment",
        "Git refused the command",
    )


def _previous(ctx: RunContext) -> list[dict]:
    """The workspace's delivery commits on its branch since the base, oldest first."""
    state = _state(ctx)
    if state.previous is None:
        state.previous = delivery_commits(
            ctx.worktree, ctx.base_commit, state.head, ctx.workspace_name
        )
    return state.previous


def check_branch(ctx: RunContext):
    outcome = require_bound_branch(ctx)
    if isinstance(outcome, Stop):
        return outcome
    _state(ctx).head = head_commit(ctx.worktree)
    return Continue()


def delivered(ctx: RunContext):
    """Stop ``ok`` when the head already is a delivery commit and nothing waits to be delivered.

    A delivery commit is its own record, so delivering again what was delivered reports that
    commit instead of refusing, and a delivery interrupted after its commit needs no repair.
    """
    state = _state(ctx)
    try:
        changed = has_uncommitted(ctx.worktree)
    except MeasurementError as error:
        return measurement_failed(ctx, error)
    previous = _previous(ctx)
    if changed or not previous or previous[-1]["commit"] != state.head:
        return Continue()
    last = previous[-1]
    ctx.output = {
        "commit": state.head,
        "branch": ctx.branch,
        "bundle": last["bundle"],
        "sequence": len(previous),
        "confirmed": [],
        "recovered": True,
    }
    return Stop(
        "ok",
        f"{ctx.workspace_name} is already delivered as {state.head[:12]} on {ctx.branch}.",
        [
            evidence(
                "commit", state.head, "the head is a delivery commit; nothing waits"
            )
        ],
    )


def require_new_work(ctx: RunContext):
    """Continue when the head moved past the base or a change waits."""
    state = _state(ctx)
    try:
        changed = has_uncommitted(ctx.worktree)
    except MeasurementError as error:
        return measurement_failed(ctx, error)
    if changed or state.head != ctx.base_commit:
        return Continue()
    return _blocked(
        ctx,
        "nothing_to_deliver",
        "The workspace has no commit or change since its base (nothing_to_deliver).",
        f"{ctx.worktree} is clean and its head {state.head} is the base commit of workspace "
        f"{ctx.workspace_name}, so its branch holds nothing to deliver",
        ["do work in the workspace, or end its task"],
        explanation="delivery validates and commits new work only, and the workspace has "
        "none; whether to do work or end the task is the task level's decision",
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
        f"The workspace is not ready: {len(blocking)} blocking finding(s) (not_ready); "
        "nothing was delivered.",
        f"validating workspace {ctx.workspace_name} as a whole found {len(blocking)} blocking "
        "finding(s): "
        + "; ".join(
            f"{item['kind']} {item['ref']}: {item['detail']}" for item in blocking
        ),
        [
            "repair each blocking finding in the workspace and run delivery again",
            "run specify for a Spec finding, implement for a code or check finding",
        ],
        explanation="delivery validates the whole workspace before it commits and never "
        "repairs a finding; each needs a Spec or code change the task level chooses",
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
    """A workspace that changes code delivers only when every scenario it added or changed is
    verified by a test; an adoption delivery (``--adoption``), which describes code as it is, is
    exempt."""
    from ..spec.repository import SpecRepository
    from ..spec.repository_base import bound_by
    from ..spec.validation import validate_repository

    if ctx.arguments.adoption:
        return Continue(
            evidence=[
                evidence(
                    "scenario-tests",
                    "exempt",
                    "an adoption delivery describes existing code; linking its tests is best "
                    "effort",
                )
            ]
        )
    base = ctx.base_commit or ""
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
            evidence=[
                evidence("scenario-tests", "no-code", "the workspace changed no code")
            ]
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
        f"{len(unverified)} scenario(s) the workspace added or changed have no test "
        "(unverified_scenarios); nothing was delivered.",
        f"workspace {ctx.workspace_name} changes code ({', '.join(code[:5])}"
        + (", ..." if len(code) > 5 else "")
        + ") while no test declares that it verifies these scenarios it added or changed: "
        + listing,
        [
            "run implement to add a test for each named scenario, in a file its Module binds, "
            "declaring the scenario it verifies",
            "if a scenario should not change, restore it with specify",
        ],
        explanation="delivery accepts a code change only when every promise the workspace added or "
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
    previous = _previous(ctx)
    state.sequence = len(previous) + 1
    state.bundle = bundle_path(ctx.workspace_name, state.sequence)
    target = ctx.worktree / state.bundle
    if target.exists():
        undo(ctx)
        return _failed(
            ctx,
            "bundle_exists",
            f"The evidence bundle {state.bundle} already exists; nothing was committed.",
            [evidence("git", state.bundle, "bundle path taken")],
            f"the evidence bundle {state.bundle} already exists in {ctx.worktree} although "
            f"the branch holds {state.sequence - 1} delivery commit(s) of the workspace",
            ["inspect the branch and the evidence directory"],
            reason="decision",
            explanation="delivery never overwrites evidence; reconciling the branch and its "
            "evidence is the task level's decision",
        )
    since = previous[-1]["readiness_run"] if previous else None
    value = build_bundle(
        ctx.workspace,
        ctx.records,
        workspace_runs(ctx.records, ctx.workspace_name),
        since=since,
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
    # workspace and would make git add refuse the whole delivery.
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
    message = commit_message(ctx.workspace, state.bundle, state.readiness_run)
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
            f"git commit refused the delivery commit of workspace {ctx.workspace_name} in "
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
    if branch != f"refs/heads/{ctx.branch}":
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
            f"the delivery commit {state.commit} on {ctx.branch} does not verify: "
            + "; ".join(problems),
            ["inspect the bound branch"],
            reason="decision",
            explanation="delivery never rewrites a commit it made; repairing the branch is the "
            "task level's decision",
        )
    return Continue()


def output(ctx: RunContext):
    state = _state(ctx)
    ctx.output = {
        "commit": state.commit,
        "branch": ctx.branch,
        "bundle": state.bundle,
        "sequence": state.sequence,
        "confirmed": [item["entry"] for item in state.readiness["confirmations"]],
        "recovered": False,
    }
    return Stop(
        "ok",
        f"Delivered {ctx.workspace_name} as {state.commit[:12]} on {ctx.branch} "
        f"with {state.bundle}.",
    )


def add_arguments(parser) -> None:
    parser.add_argument(
        "--adoption",
        action="store_true",
        help="deliver a description of existing code: scenarios changed with code need no "
        "verifying test",
    )


DELIVERY = command(
    "delivery",
    (
        check_branch,
        delivered,
        require_new_work,
        *READINESS_STEPS,
        decide,
        require_verified_scenarios,
        apply_confirmations,
        write_bundle,
        commit,
        verify,
        output,
    ),
    writes=True,
    output_schema=OUTPUT_SCHEMA,
    add_arguments=add_arguments,
    # Validation's steps diagnose Specs that cannot be loaded, as task-validation does.
    requires_loaded_specs=False,
)


__all__ = ["DELIVERY"]
