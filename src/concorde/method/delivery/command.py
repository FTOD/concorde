"""``concorde delivery``: validate a whole workspace, then commit it (see the Delivery Spec).

An execution command of the bound workspace; it launches no worker. The delivery commits on the
bound branch are its only record: their subject names the workspace.

1. Require that the workspace's head is its bound branch.
2. Note the head when it already is a delivery commit of the workspace and nothing waits, after
   verifying that it has exactly one parent (``failed``, ``commit_unverified``, when it has not).
3. Require new work: a commit since the base, or an uncommitted change.
4. Decide the readiness of the whole workspace with Validation's steps, as task-validation does.
5. Require that readiness to be ready, and every scenario changed with code to be verified.
6. Stop ``ok``, ``recovered``, when step 2 noted a delivery commit: it validated again.
7. Record the index with Git (its tree, intent-to-add paths and skip-worktree and
   assume-unchanged flags).
8. Stage everything, record the staged tree and create the delivery commit; when staging or the
   commit fails, give the recorded index back.
9. Verify the new head, its tree (the staged one, which a commit hook may have changed), its
   parent and a clean worktree; take a commit that does not verify off the branch again.
10. Return the delivery commit as the output.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from ...execution.context import (
    Continue,
    RunContext,
    Stop,
    command,
    component,
    evidence,
)
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
from ...kernel import delivery as delivery_commit
from ...kernel.refusal import KernelError

COMMIT = {"type": "string", "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"}

# The output of a delivery run: the delivery commit it created or found on the branch.
OUTPUT_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["commit", "branch", "sequence", "recovered"],
    "properties": {
        "commit": COMMIT,
        "branch": {"type": "string", "minLength": 1},
        "sequence": {"type": "integer", "minimum": 1},
        "recovered": {"type": "boolean"},
    },
}


@dataclass
class IndexRecord:
    """The index the readiness examined, as Git itself can give it back."""

    # ``git write-tree`` of the index; ``git read-tree`` restores its entries.
    tree: str
    # Intent-to-add entries (``git add -N``), which a tree cannot hold.
    intent_to_add: list[str]
    # Entry flags, which a tree cannot hold either.
    skip_worktree: list[str]
    assume_unchanged: list[str]


class _IndexRefused(Exception):
    """A Git command recording or restoring the index failed; ``link`` is its component link."""

    def __init__(self, link: dict):
        super().__init__(link["detail"])
        self.link = link


@dataclass
class Undone:
    """What undoing a failed delivery could not restore: a short name and a cause for each."""

    failed: list[tuple[str, dict]] = field(default_factory=list)

    @property
    def causes(self) -> list[dict]:
        return [link for _, link in self.failed]

    def __str__(self) -> str:
        if not self.failed:
            return "the workspace and its index were restored as the readiness examined them"
        names = [name for name, _ in self.failed]
        listed = (
            ", ".join(names[:-1]) + " and " + names[-1] if len(names) > 1 else names[0]
        )
        return (
            f"restoring {listed} failed, so the workspace "
            "is not as the readiness examined it (see the causes); everything else was restored"
        )


@dataclass
class State:
    head: str = ""
    readiness_run: str = ""
    readiness: dict = field(default_factory=dict)
    index: IndexRecord | None = None
    sequence: int = 0
    commit: str = ""
    # ``git write-tree`` of the index once everything was staged, which the commit must hold.
    staged_tree: str = ""
    # The workspace's earlier delivery commits, read once from Git.
    previous: list[dict] | None = None
    # The delivery commit found at the head with nothing waiting, reported once it validates.
    found: str = ""


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


def _index_git(worktree: Path, *arguments: str, stdin: bytes | None = None) -> bytes:
    """Run one Git command on the index; raise ``_IndexRefused`` with its output when it fails.

    Bytes, not text, so that any path Git stores survives the round trip.
    """
    result = subprocess.run(
        ["git", *arguments], cwd=worktree, input=stdin, capture_output=True, check=False
    )
    if result.returncode != 0:
        output = (result.stdout + result.stderr).decode("utf-8", "replace").strip()
        raise _IndexRefused(
            component(
                f"git {' '.join(arguments)}",
                "git_failed",
                f"git {' '.join(arguments)} in {worktree} exited {result.returncode}: "
                + (output[-2000:] or "(no output)"),
                "environment",
                "Git refused the command",
            )
        )
    return result.stdout


def _split(raw: bytes) -> list[str]:
    return [item for item in raw.decode("utf-8", "surrogateescape").split("\0") if item]


def _joined(paths: list[str]) -> bytes:
    return b"".join(path.encode("utf-8", "surrogateescape") + b"\0" for path in paths)


def record_index(worktree: Path) -> IndexRecord:
    """Record the index with Git's own means, so that ``restore_index`` gives it back exactly."""
    tree = _index_git(worktree, "write-tree").decode().strip()
    in_tree = set(
        _split(
            _index_git(
                worktree, "ls-tree", "-r", "-z", "--name-only", "--full-tree", tree
            )
        )
    )
    # ``ls-files -v`` tags each entry: ``S`` or ``s`` skip-worktree, lower case assume-unchanged.
    entries = [
        (item[0], item[2:])
        for item in _split(_index_git(worktree, "ls-files", "-v", "-z"))
    ]
    return IndexRecord(
        tree=tree,
        intent_to_add=[path for _, path in entries if path not in in_tree],
        skip_worktree=[path for tag, path in entries if tag in "Ss"],
        assume_unchanged=[path for tag, path in entries if tag.islower()],
    )


def restore_index(worktree: Path, record: IndexRecord) -> list[tuple[str, dict]]:
    """Give the recorded index back; name and explain each part Git refused to restore."""
    try:
        _index_git(worktree, "read-tree", record.tree)
    except _IndexRefused as error:
        # Nothing further applies to an index that was not read back.
        return [("the index", error.link)]
    failed = []
    parts = [
        (
            "the intent-to-add entries",
            record.intent_to_add,
            ["--literal-pathspecs", "add", "-N", "-f", "--pathspec-from-file=-"]
            + ["--pathspec-file-nul"],
        ),
        (
            "the skip-worktree flags",
            record.skip_worktree,
            ["update-index", "--skip-worktree", "-z", "--stdin"],
        ),
        (
            "the assume-unchanged flags",
            record.assume_unchanged,
            ["update-index", "--assume-unchanged", "-z", "--stdin"],
        ),
    ]
    for name, paths, arguments in parts:
        if not paths:
            continue
        try:
            _index_git(worktree, *arguments, stdin=_joined(paths))
        except _IndexRefused as error:
            failed.append((name, error.link))
    # read-tree drops the cached file stats; refreshing them lets Git see unchanged files as
    # such. It exits non-zero whenever a file differs from the index, which is expected here.
    _git(worktree, "update-index", "-q", "--refresh")
    return failed


def _previous(ctx: RunContext) -> list[dict]:
    """The workspace's delivery commits on its branch since the base, oldest first, each with
    its ``mismatches``, as the Kernel's convention recognizes them; ``MeasurementError`` when Git
    cannot list them."""
    state = _state(ctx)
    if state.previous is None:
        try:
            state.previous = delivery_commit.deliveries(
                ctx.worktree, state.head, ctx.base_commit, ctx.workspace_name
            )
        except KernelError as error:
            raise MeasurementError(error.code, str(error)) from error
    return state.previous


def check_branch(ctx: RunContext):
    outcome = require_bound_branch(ctx)
    if isinstance(outcome, Stop):
        return outcome
    _state(ctx).head = head_commit(ctx.worktree)
    return Continue()


def delivered(ctx: RunContext):
    """Note the head when it already is a delivery commit and nothing waits to be delivered.

    A delivery commit is its own record, so delivering again what was delivered reports that
    commit instead of refusing, and a delivery interrupted after its commit needs no repair. Its
    subject proves nothing about what it holds, so the readiness steps validate it first, as they
    would new work, and ``report_found`` reports it only once they let it through.
    """
    state = _state(ctx)
    try:
        changed = has_uncommitted(ctx.worktree)
        previous = _previous(ctx)
    except MeasurementError as error:
        return measurement_failed(ctx, error)
    if changed or not previous or previous[-1]["commit"] != state.head:
        return Continue()
    last = previous[-1]
    problems = last["mismatches"]
    if problems:
        return _unverified(
            ctx,
            f"The head {state.head} looks like a delivery commit of {ctx.workspace_name} but "
            "does not verify (commit_unverified); nothing was committed.",
            f"the head {state.head} of {ctx.branch} has the subject of a delivery commit of "
            f"workspace {ctx.workspace_name} but does not verify: "
            + "; ".join(problems),
            problems,
            state.head,
        )
    state.found = state.head
    return Continue(
        evidence=[
            evidence(
                "commit",
                state.head,
                "the head is a delivery commit with one parent and nothing waits; it is "
                "validated again before it is reported",
            )
        ]
    )


def _not_reported(ctx: RunContext, stop: Stop) -> Stop:
    """Say in a blocked stop that the delivery commit found at the head is not reported."""
    found = _state(ctx).found
    if found and stop.status == "blocked":
        note = (
            f"the delivery commit {found} at the head of {ctx.branch} is not reported as "
            "delivered, since the workspace it holds does not validate"
        )
        stop.summary += (
            f" The delivery commit {found[:12]} at the head is not reported."
        )
        stop.error["detail"] += f"; {note}"
    return stop


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
    return _not_reported(ctx, stop)


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
    from ...spec.repository import SpecRepository
    from ...spec.repository_base import bound_by
    from ...spec.validation import validate_repository

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
    stop = _blocked(
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
    return _not_reported(ctx, stop)


def report_found(ctx: RunContext):
    """Stop ``ok``, ``recovered``, when the head was a delivery commit that validated again."""
    state = _state(ctx)
    if not state.found:
        return Continue()
    ctx.output = {
        "commit": state.found,
        "branch": ctx.branch,
        "sequence": len(_previous(ctx)),
        "recovered": True,
    }
    # An earlier run created the commit; this run's node leads to it as found.
    ctx.references.append(("found_commit", state.found))
    return Stop(
        "ok",
        f"{ctx.workspace_name} is already delivered as {state.found[:12]} on {ctx.branch}.",
        [
            evidence(
                "commit",
                state.found,
                "the delivery commit at the head validated again; nothing was committed",
            )
        ],
    )


def keep_index(ctx: RunContext):
    """Record the index before anything changes, so a failed delivery can give it back exactly,
    staged changes included, rather than resetting it to the head."""
    try:
        _state(ctx).index = record_index(ctx.worktree)
    except _IndexRefused as error:
        return _index_unrecorded(ctx, error.link)
    return Continue()


def _index_unrecorded(ctx: RunContext, cause: dict) -> Stop:
    unmerged = sorted(
        {
            line.split("\t", 1)[1]
            for line in _git(ctx.worktree, "ls-files", "-u").stdout.splitlines()
            if "\t" in line
        }
    )
    if unmerged:
        return _failed(
            ctx,
            "index_unrecorded",
            f"The index has {len(unmerged)} unmerged path(s), which Git cannot record; "
            "nothing was changed.",
            [evidence("git", "unmerged", ", ".join(unmerged))],
            f"the index of {ctx.worktree} holds unmerged paths ({', '.join(unmerged)}), so "
            "git write-tree cannot record it and a failed delivery could not restore it; "
            "nothing was changed",
            [
                "resolve the unmerged paths and stage them, then run delivery again",
                "abort the merge, then run delivery again",
            ],
            reason="decision",
            explanation="an unfinished merge is the task level's to resolve or abort; delivery "
            "never commits an index it could not give back",
            causes=[cause],
        )
    return _failed(
        ctx,
        "index_unrecorded",
        "Git could not record the index; nothing was changed.",
        [evidence("git", "index", cause["detail"])],
        f"the index of {ctx.worktree} could not be recorded, so a failed delivery could not "
        f"restore it; nothing was changed: {cause['detail']}",
        ["repair the worktree's Git state, then run delivery again"],
        explanation="delivery records the index before it changes anything and cannot repair "
        "Git",
        causes=[cause],
    )


def undo(ctx: RunContext) -> Undone:
    """Give the recorded index back.

    A failure is named with its cause, so the caller's result says exactly what is not as the
    readiness examined it.
    """
    state = _state(ctx)
    undone = Undone()
    if state.index is not None:
        undone.failed.extend(restore_index(ctx.worktree, state.index))
    return undone


def commit(ctx: RunContext):
    state = _state(ctx)
    state.sequence = len(_previous(ctx)) + 1
    found = []
    # New paths Git cannot version, such as a sandbox's /dev/null mounts, are no content of the
    # workspace and would make git add refuse the whole delivery.
    try:
        special = special_paths(ctx.worktree)
    except MeasurementError as error:
        undone = undo(ctx)
        failure = measurement_failed(ctx, error)
        failure.summary += f" Nothing was committed and {undone}."
        failure.error["detail"] += f"; nothing was committed and {undone}"
        failure.error["causes"].extend(undone.causes)
        return failure
    excluded = [f":(exclude,literal){path}" for path in special]
    staged = _git(ctx.worktree, "add", "-A", "--", ".", *excluded)
    if staged.returncode != 0:
        undone = undo(ctx)
        return _failed(
            ctx,
            "stage_failed",
            f"Git could not stage the delivery; nothing was committed and {undone}.",
            [evidence("git", "add", staged.stderr.strip())],
            f"git add failed in {ctx.worktree}, so nothing was committed and {undone}: "
            f"{staged.stderr.strip()}",
            ["repair the worktree's Git state, then run delivery again"],
            causes=[_git_link("add", staged), *undone.causes],
        )
    # What the commit must hold; a commit hook may still change it, which verify names.
    tree = _git(ctx.worktree, "write-tree")
    if tree.returncode != 0:
        undone = undo(ctx)
        return _failed(
            ctx,
            "stage_failed",
            f"Git could not record the staged index; nothing was committed and {undone}.",
            [evidence("git", "write-tree", tree.stderr.strip())],
            f"git write-tree failed in {ctx.worktree} after staging, so the tree the commit "
            f"must hold is unknown; nothing was committed and {undone}: "
            f"{tree.stderr.strip()}",
            ["repair the worktree's Git state, then run delivery again"],
            causes=[_git_link("write-tree", tree), *undone.causes],
        )
    state.staged_tree = tree.stdout.strip()
    message = delivery_commit.message(ctx.workspace_name, ctx.workspace["goal"])
    result = subprocess.run(
        ["git", "commit", "-q", "--allow-empty", "--cleanup=verbatim", "-F", "-"],
        cwd=ctx.worktree,
        input=message,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        output = (result.stdout + result.stderr).strip()
        undone = undo(ctx)
        return _failed(
            ctx,
            "commit_failed",
            f"Git refused the delivery commit; {undone}.",
            found
            + [
                evidence("git", "commit", output[-4000:] or f"exit {result.returncode}")
            ],
            f"git commit refused the delivery commit of workspace {ctx.workspace_name} in "
            f"{ctx.worktree}; {undone}: {output[-1000:] or f'exit {result.returncode}'}",
            ["fix the commit hook or the author identity, then run delivery again"],
            causes=[_git_link("commit", result), *undone.causes],
        )
    state.commit = head_commit(ctx.worktree)
    # The run's trace node leads to what was committed.
    ctx.references.append(("commit", state.commit))
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
    committed = _git(
        ctx.worktree, "rev-parse", f"{state.commit}^{{tree}}"
    ).stdout.strip()
    if committed != state.staged_tree:
        changed = _git(
            ctx.worktree,
            "diff-tree",
            "-r",
            "--name-status",
            state.staged_tree,
            committed,
        ).stdout.split("\n")
        listed = ", ".join(
            " ".join(line.split("\t")) for line in changed if line.strip()
        )
        problems.append(
            f"its tree {committed} is not the staged tree {state.staged_tree}, so a commit "
            f"hook changed what was committed: {listed or 'no path listed'}"
        )
    if head_commit(ctx.worktree) != state.commit:
        problems.append("the new commit is not the branch head")
    if has_uncommitted(ctx.worktree):
        problems.append("the worktree is not clean after the commit")
    if not problems:
        return Continue()
    detail = (
        f"the delivery commit {state.commit} on {ctx.branch} does not verify: "
        + "; ".join(problems)
    )
    if parents[1:] != [state.head]:
        # Not the commit this run made on the validated head, such as one a hook made on top.
        return _unverified(
            ctx,
            f"The delivery commit {state.commit} does not verify (commit_unverified); it stays "
            f"on {ctx.branch}.",
            detail
            + f"; the commit stays, since Delivery takes off {ctx.branch} only a commit whose "
            f"only parent is the validated head {state.head}",
            problems,
            state.commit,
        )
    # A rejected commit must not stay where its subject would mark it as a delivery.
    removed = _git(
        ctx.worktree,
        "update-ref",
        "-m",
        f"concorde: take the rejected delivery commit of {ctx.workspace_name} off the branch",
        f"refs/heads/{ctx.branch}",
        state.head,
        state.commit,
    )
    if removed.returncode == 0:
        return _unverified(
            ctx,
            f"The delivery commit {state.commit} does not verify (commit_unverified); it was "
            f"taken off {ctx.branch}, whose head is again {state.head}.",
            detail
            + f"; Delivery took the commit off {ctx.branch}, whose head is again the validated "
            f"head {state.head}, and left the index and the worktree as the commit left them",
            problems,
            state.commit,
            options=[
                "inspect the staged changes, which hold what the commit held, and the commit "
                "hook that changed them",
                "repair the hook or the changes, then run delivery again",
            ],
        )
    return _unverified(
        ctx,
        f"The delivery commit {state.commit} does not verify (commit_unverified); it stays on "
        f"{ctx.branch}, which no longer points at it.",
        detail
        + f"; the commit stays, since {ctx.branch} no longer points at it and Delivery moves "
        "the branch back only from its own commit",
        problems,
        state.commit,
        causes=[_git_link("update-ref", removed)],
    )


def _unverified(
    ctx: RunContext,
    summary: str,
    detail: str,
    problems: list[str],
    commit: str,
    options=(
        "inspect the bound branch and the commit's content",
        "revert or remove the commit that does not verify, then run delivery again",
    ),
    causes=(),
) -> Stop:
    """Fail ``commit_unverified``; what to do with a commit that does not hold what it claims
    is the task level's decision."""
    return _failed(
        ctx,
        "commit_unverified",
        summary,
        [evidence("git", commit, "; ".join(problems))],
        detail,
        options,
        reason="decision",
        explanation="delivery reports only a delivery commit it can show holds what was "
        "validated, and takes off the branch only a commit it created in the same run; what "
        "to do with the branch or the changes is the task level's decision",
        causes=causes,
    )


def output(ctx: RunContext):
    state = _state(ctx)
    ctx.output = {
        "commit": state.commit,
        "branch": ctx.branch,
        "sequence": state.sequence,
        "recovered": False,
    }
    return Stop(
        "ok",
        f"Delivered {ctx.workspace_name} as {state.commit[:12]} on {ctx.branch}.",
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
        report_found,
        keep_index,
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
