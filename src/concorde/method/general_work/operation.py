"""The ``general`` Operation: a worker does free-form work under a named task type's grant, and an
independent reviewer judges the result against the caller's instruction.

Steps (the step table of "How it is built" in the General work Module Spec):

1. ``read_instruction``: read ``--instruction`` or ``--instruction-file``, keep an exact copy as
   ``instruction.md`` in the run's trace node and record its digest; an unreadable or empty
   instruction fails the run.
2. ``record_before``: record the worktree as a Git tree, through a temporary index.
3. ``work``: the standard worker sequence for the ``--type`` grant with the worker ``worker``,
   writes withheld with ``--read-only``, no checks and no resume round.
4. ``record_after``: record the worktree again; keep the diff between the two trees as
   ``change.diff`` and the earlier content of every modified or deleted file under ``before/``.
5. ``review``: the standard worker sequence for the same type with the worker ``reviewer``, every
   writable level withheld, the kept diff and earlier files readable.
6. ``check_review``: the finding ids are distinct; derive the verdict and return the result.

The reviewer only reports: acting on a finding is the caller's decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from ...execution.context import Continue, RunContext, evidence
from ...spec.grants import TASK_TYPES
from ..prompts import load_prompt
from ..workers import operation, run_worker

NAME = "general"
WORKER = "worker"
REVIEWER = "reviewer"
INSTRUCTION_COPY = "instruction.md"
DIFF = "change.diff"
BEFORE = "before"
KINDS = ["instruction", "meaning", "scope", "error", "claim"]
# The diff is quoted in the reviewer's brief while it is at most this long; a longer one is read
# from its file.
DIFF_LIMIT = 150_000
_TEXT = {"type": "string", "minLength": 1}

# The worker's part of its worker result (``output``).
WORKER_OUTPUT: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["answer"],
    "properties": {"answer": _TEXT},
}

FINDING_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "severity", "kind", "locations", "description", "suggestion"],
    "properties": {
        "id": {"type": "string", "pattern": "^F[0-9]+$"},
        "severity": {"enum": ["blocking", "advisory"]},
        "kind": {"enum": KINDS},
        "locations": {"type": "array", "items": _TEXT},
        "description": _TEXT,
        "suggestion": _TEXT,
    },
}

# The reviewer's part of its worker result (``output``); its ``summary`` is the top-level one.
REVIEWER_OUTPUT: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["findings"],
    "properties": {"findings": {"type": "array", "items": FINDING_SCHEMA}},
}

# contract.general-work.result, version 1 (specs/concorde/method/general-work/contracts.md)
RESULT_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["type", "read_only", "instruction", "answer", "change", "review"],
    "properties": {
        "type": {"enum": list(TASK_TYPES)},
        "read_only": {"type": "boolean"},
        "instruction": {
            "type": "object",
            "additionalProperties": False,
            "required": ["file", "copy", "digest"],
            "properties": {
                "file": {"anyOf": [_TEXT, {"type": "null"}]},
                "copy": _TEXT,
                "digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
            },
        },
        "answer": _TEXT,
        "change": {
            "type": "object",
            "additionalProperties": False,
            "required": ["files", "diff", "before"],
            "properties": {
                "files": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["path", "change"],
                        "properties": {
                            "path": _TEXT,
                            "change": {"enum": ["added", "modified", "deleted"]},
                        },
                    },
                },
                "diff": _TEXT,
                "before": _TEXT,
            },
        },
        "review": {
            "type": "object",
            "additionalProperties": False,
            "required": ["summary", "findings", "verdict"],
            "properties": {
                "summary": _TEXT,
                "findings": {"type": "array", "items": FINDING_SCHEMA},
                "verdict": {"enum": ["accepted", "changes_required"]},
            },
        },
    },
}


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--type", required=True, choices=TASK_TYPES, dest="task_type")
    given = parser.add_mutually_exclusive_group(required=True)
    given.add_argument("--instruction")
    given.add_argument("--instruction-file")
    parser.add_argument("--read-only", action="store_true")


def fenced(text: str, language: str = "") -> str:
    """``text`` in a code fence longer than any backtick run it holds."""
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}{language}\n{text.rstrip(chr(10))}\n{fence}\n"


# --- step 1: the instruction -------------------------------------------------------------------


def read_instruction(ctx: RunContext):
    """Read the instruction, keep its copy in the run's trace node and record its digest."""
    arguments = ctx.arguments
    path, problem, data = None, None, b""
    if arguments.instruction_file is not None:
        given = Path(arguments.instruction_file)
        path = Path(
            os.path.normpath(given if given.is_absolute() else ctx.worktree / given)
        )
        try:
            data = path.read_bytes()
        except OSError as error:
            problem = f"the file {path} cannot be read: {error}"
    else:
        data = arguments.instruction.encode("utf-8")
    if problem is None:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as error:
            problem = f"the file {path} is not UTF-8 text: {error}"
        else:
            if not text.strip():
                problem = "it is empty"
    if problem:
        origin = (
            f"--instruction-file {arguments.instruction_file}"
            if path is not None
            else "--instruction"
        )
        return ctx.fail(
            "failed",
            "instruction_unreadable",
            f"The instruction cannot be used: {problem}.",
            f"{origin} gives no instruction general can hand to a worker, because {problem}; "
            "no worker was launched",
            reason="input",
            explanation="the instruction is the caller's, which the Operation only reads",
            evidence=[
                evidence(
                    "instruction", path.as_posix() if path else "--instruction", problem
                )
            ],
            options=[
                (
                    "give the instruction as non-empty UTF-8 text with --instruction or "
                    "--instruction-file"
                )
            ],
        )
    copy = ctx.run_dir / INSTRUCTION_COPY
    copy.parent.mkdir(parents=True, exist_ok=True)
    copy.write_bytes(data)
    digest = "sha256:" + hashlib.sha256(data).hexdigest()
    ctx.state["instruction"] = {
        "file": path.as_posix() if path is not None else None,
        "copy": copy.as_posix(),
        "digest": digest,
    }
    ctx.state["instruction_text"] = data.decode("utf-8")
    return Continue(
        evidence=[
            evidence(
                "instruction",
                digest,
                f"{path.as_posix() if path else '--instruction'}; kept as {copy}",
            )
        ]
    )


# --- steps 2 and 4: the observed change --------------------------------------------------------


class GitFailure(Exception):
    """A Git command the Operation needs to observe the change failed."""


def _git(worktree: Path, *arguments: str, env: dict | None = None) -> bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=worktree,
        capture_output=True,
        check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", **(env or {})},
    )
    if completed.returncode != 0:
        raise GitFailure(
            f"git {' '.join(arguments)} exited {completed.returncode}: "
            + completed.stderr.decode("utf-8", "replace").strip()
        )
    return completed.stdout


def record_tree(worktree: Path) -> str:
    """The worktree's content as a Git tree, files Git ignores excluded, written through a
    temporary copy of the worktree's index so that neither ``HEAD`` nor the index changes."""
    index = Path(_git(worktree, "rev-parse", "--git-path", "index").decode().strip())
    if not index.is_absolute():
        index = worktree / index
    with tempfile.TemporaryDirectory(prefix="concorde-general-") as scratch:
        temporary = Path(scratch) / "index"
        if index.is_file():
            shutil.copyfile(index, temporary)
        env = {"GIT_INDEX_FILE": temporary.as_posix()}
        _git(worktree, "add", "--all", "--", ".", env=env)
        return _git(worktree, "write-tree", env=env).decode().strip()


def unobservable(ctx: RunContext, when: str, error: Exception):
    return ctx.fail(
        "failed",
        "change_unobservable",
        f"Git could not record the worktree {when} the worker.",
        f"general records the worktree {ctx.worktree} as a Git tree {when} the worker to "
        f"observe its change, and Git failed: {error}",
        reason="environment",
        explanation="the Operation observes the change only through Git and cannot repair "
        "the repository",
        evidence=[evidence("git", ctx.worktree.as_posix(), str(error))],
        options=["repair the repository named in the detail and run general again"],
    )


def record_before(ctx: RunContext):
    """Record the worktree as a Git tree before the worker launches."""
    try:
        ctx.state["tree_before"] = record_tree(ctx.worktree)
    except (GitFailure, OSError) as error:
        return unobservable(ctx, "before", error)
    return Continue(
        evidence=[evidence("tree-before", ctx.state["tree_before"], "worktree")]
    )


CHANGES = {"A": "added", "M": "modified", "T": "modified", "D": "deleted"}


def changed_files(worktree: Path, before: str, after: str) -> list[dict]:
    """Every path that differs between the two trees, with how it changed, sorted by path."""
    output = _git(
        worktree, "diff", "--no-renames", "--name-status", "-z", before, after
    ).split(b"\0")
    files = []
    for status, path in zip(output[0::2], output[1::2]):
        if not status:
            continue
        files.append(
            {
                "path": path.decode("utf-8", "surrogateescape"),
                "change": CHANGES.get(status.decode()[:1], "modified"),
            }
        )
    return sorted(files, key=lambda item: item["path"])


def keep_earlier(worktree: Path, tree: str, path: str, folder: Path) -> None:
    """Write the content ``path`` had in ``tree`` below ``folder``; a submodule is skipped."""
    listing = _git(worktree, "ls-tree", "-z", tree, "--", path).split(b"\0")[0]
    if not listing or listing.split(b" ", 2)[1] != b"blob":
        return
    target = folder / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(_git(worktree, "cat-file", "blob", f"{tree}:{path}"))


def record_after(ctx: RunContext):
    """Record the worktree again; keep the diff and the earlier content of each changed file."""
    ctx.state["answer"] = (ctx.output or {}).get("answer") or ""
    # Only an ok run carries an output; the final one is assembled after the review.
    ctx.output = None
    before = ctx.state["tree_before"]
    diff = ctx.run_dir / DIFF
    folder = ctx.run_dir / BEFORE
    try:
        after = record_tree(ctx.worktree)
        files = changed_files(ctx.worktree, before, after)
        text = _git(
            ctx.worktree,
            "diff",
            "--no-color",
            "--no-ext-diff",
            "--no-renames",
            before,
            after,
        )
        diff.write_bytes(text)
        folder.mkdir(parents=True, exist_ok=True)
        for item in files:
            if item["change"] != "added":
                keep_earlier(ctx.worktree, before, item["path"], folder)
    except (GitFailure, OSError) as error:
        return unobservable(ctx, "after", error)
    ctx.state["change"] = {
        "files": files,
        "diff": diff.as_posix(),
        "before": folder.as_posix(),
    }
    ctx.state["diff_text"] = text.decode("utf-8", "replace")
    listed = ", ".join(f"{item['path']} ({item['change']})" for item in files)
    return Continue(
        evidence=[
            evidence("tree-after", after, "worktree"),
            evidence(
                "change",
                diff.as_posix(),
                f"{len(files)} file(s) changed: {listed or 'none'}; earlier content in "
                f"{folder}",
            ),
        ]
    )


# --- steps 3 and 5: the workers ----------------------------------------------------------------


def grant_line(ctx: RunContext, read_only: bool) -> str:
    withheld = " (every writable level lowered to read)" if read_only else ""
    return f"Task type of your boundary: {ctx.arguments.task_type}{withheld}\n\n"


def inputs_material(ctx: RunContext) -> str:
    if not ctx.inputs:
        return ""
    return (
        "\n## Admitted inputs\n\nOutputs of earlier ok runs, given as material:\n\n"
        + fenced(json.dumps(ctx.inputs, indent=2), "json")
    )


def worker_instructions(ctx: RunContext) -> str:
    return (
        load_prompt("general").strip()
        + "\n\n## This run\n\n"
        + grant_line(ctx, ctx.arguments.read_only)
        + f"Bound Modules: {', '.join(ctx.modules)}\n\n"
        + f"The workspace's goal: {ctx.goal or '(none: an unbound run)'}\n\n"
        + "## The instruction\n\n"
        + fenced(ctx.state["instruction_text"], "markdown")
        + inputs_material(ctx)
    )


def work(ctx: RunContext):
    """Step 3: run the worker once under the named type's grant."""
    return run_worker(
        ctx,
        worker_instructions(ctx),
        task_type=ctx.arguments.task_type,
        output_schema=WORKER_OUTPUT,
        worker=WORKER,
        read_only=ctx.arguments.read_only,
        checks=False,
        rounds=0,
    )


def change_material(ctx: RunContext) -> str:
    change = ctx.state["change"]
    if not change["files"]:
        return "The host observed no change in the worktree.\n"
    parts = ["The host observed these changes in the worktree:\n\n"]
    parts.extend(f"- `{item['path']}`: {item['change']}\n" for item in change["files"])
    parts.append(
        f"\nThe earlier content of every modified or deleted file is in `{change['before']}`, "
        "at the same relative path. The new content is in the worktree.\n\n"
    )
    text = ctx.state["diff_text"]
    if len(text) <= DIFF_LIMIT:
        parts.append(
            f"The diff (also in `{change['diff']}`):\n\n" + fenced(text, "diff")
        )
    else:
        parts.append(
            f"The diff is too long to quote here ({len(text)} characters). Read it in "
            f"`{change['diff']}`.\n"
        )
    return "".join(parts)


def reviewer_instructions(ctx: RunContext) -> str:
    return (
        load_prompt("general-review").strip()
        + "\n\n## This review\n\n"
        + grant_line(ctx, True)
        + f"Bound Modules: {', '.join(ctx.modules)}\n\n"
        + "## The instruction\n\n"
        + fenced(ctx.state["instruction_text"], "markdown")
        + "\n## The change\n\n"
        + change_material(ctx)
        + "\n## The worker's answer\n\nThis is the worker's claim. Check it against the "
        "change.\n\n" + fenced(ctx.state["answer"] or "(no answer)", "text")
    )


def review(ctx: RunContext):
    """Step 5: run the reviewer once, read-only, with the kept change readable."""
    change = ctx.state["change"]
    return run_worker(
        ctx,
        reviewer_instructions(ctx),
        task_type=ctx.arguments.task_type,
        output_schema=REVIEWER_OUTPUT,
        worker=REVIEWER,
        read_only=True,
        readable=(Path(change["diff"]), Path(change["before"])),
        checks=False,
        rounds=0,
    )


# --- step 6: the result ------------------------------------------------------------------------


def check_review(ctx: RunContext):
    """Step 6: the finding ids are distinct; derive the verdict and return the result."""
    findings = list((ctx.output or {}).get("findings") or [])
    ctx.output = None
    ids = [item["id"] for item in findings]
    repeated = sorted({identity for identity in ids if ids.count(identity) > 1})
    if repeated:
        return ctx.fail(
            "failed",
            "inconsistent_review",
            "The review gives the same id to more than one finding: "
            + ", ".join(repeated)
            + ".",
            "the reviewer's findings repeat the id(s) "
            + ", ".join(repeated)
            + ", so the review is discarded; the worker's change stays in the worktree",
            reason="capability",
            explanation="the host checks the review but never corrects it or relaunches the "
            "reviewer",
            evidence=[
                evidence("inconsistent-review", identity, "") for identity in repeated
            ],
            options=[
                "run general again",
                "read the reviewer's answer in `worker`",
            ],
        )
    blocking = sum(item["severity"] == "blocking" for item in findings)
    verdict = "changes_required" if blocking else "accepted"
    result = {
        "type": ctx.arguments.task_type,
        "read_only": bool(ctx.arguments.read_only),
        "instruction": ctx.state["instruction"],
        "answer": ctx.state["answer"] or "(no answer)",
        "change": ctx.state["change"],
        "review": {
            "summary": (ctx.worker or {}).get("summary") or "reviewed",
            "findings": findings,
            "verdict": verdict,
        },
    }
    return Continue(
        output=result,
        evidence=[
            evidence(
                "verdict",
                verdict,
                f"{len(findings)} finding(s), {blocking} blocking",
            )
        ],
    )


GENERAL = operation(
    name=NAME,
    task_type=None,
    writes=True,
    steps=(read_instruction, record_before, work, record_after, review, check_review),
    output_schema=RESULT_SCHEMA,
    add_arguments=add_arguments,
    binding="optional",
    workers=(WORKER, REVIEWER),
)

__all__ = [
    "GENERAL",
    "RESULT_SCHEMA",
    "REVIEWER_OUTPUT",
    "WORKER_OUTPUT",
]
