"""The throwaway checkout an unbound run works in.

An unbound run never works in the worktree it starts in, such as the primary worktree, where main
sessions merge tasks while it runs: a merge there would change the Specs and code under its workers
and fail their audit. The runner checks out that worktree's ``HEAD`` detached as
``.claude/worktrees/unbound-<run-id>`` of the repository's primary worktree with ``git worktree add
--detach``, which shares the repository's objects and costs no clone, and the run's steps and
workers work there: every worktree a worker runs in lies in ``.claude/worktrees/``, where Workers
knows the repository's Git metadata to hide. A run identity always holds an upper-case ``T``, which
no task name may, so the name never clashes with a task worktree. Each submodule the starting worktree
has checked out at the commit ``HEAD`` records, such as a vendored external reference, is checked
out the same way from its own repository, with the same sparse patterns. The environments the
project configuration names as runtime paths and Git ignores, such as ``.venv`` and
``node_modules``, are never part of a commit, so they are linked from the starting worktree for the
run's checks to use; nothing in the run writes them. However the run ends, the links, the
submodule checkouts and the checkout itself are removed, and a removal Git refuses is reported as
host evidence.

Nothing here writes a file of the starting worktree or its index: ``git worktree add`` and
``git worktree remove`` change only the repository's administrative files, and the checkout lies
in a directory Git ignores, which the runner checks before it creates anything.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from ..kernel.errors import evidence
from ..worker_harness.models import DEFAULT_RUNTIME, ModelConfigError, load, runtime
from .runs import RunError

# Git never runs a hook of the repository for the checkout: it is the runner's, not a checkout a
# developer made.
GIT = ("git", "-c", "core.hooksPath=/dev/null")
# Where the checkout lies, relative to the primary worktree, and the prefix of its name.
WORKTREES = ".claude/worktrees"
PREFIX = "unbound-"


def _git(cwd: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*GIT, *arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )


def _said(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stderr or result.stdout).strip() or "no output"


@dataclass
class Checkout:
    """A detached checkout of ``commit`` at ``path``, for the run started in ``origin``."""

    origin: Path
    path: Path
    commit: str
    # The submodule paths checked out from the origin's own checkouts, in the order they were.
    submodules: list[str] = field(default_factory=list)
    # The links to the origin's ignored environments.
    links: list[Path] = field(default_factory=list)
    # What the checkout provides or lacks, as host evidence of the run.
    evidence: list[dict] = field(default_factory=list)
    closed: bool = False

    def close(self) -> list[dict]:
        """Remove the links, the submodule checkouts and the checkout, once; evidence of each
        removal Git refused, after removing the files and the administrative entry directly."""
        if self.closed:
            return []
        self.closed = True
        problems = []
        for link in self.links:
            try:
                link.unlink(missing_ok=True)
            except OSError as error:
                problems.append(
                    evidence("checkout-not-removed", link.as_posix(), str(error))
                )
        for path in reversed(self.submodules):
            problems += _remove(self.origin / path, self.path / path)
        problems += _remove(self.origin, self.path)
        shutil.rmtree(self.path, ignore_errors=True)
        return problems


def _remove(repository: Path, path: Path) -> list[dict]:
    removed = _git(repository, "worktree", "remove", "--force", path.as_posix())
    if removed.returncode == 0:
        return []
    # A checkout Git no longer knows, or cannot remove, goes directly; pruning then drops the
    # administrative entry of every worktree whose directory is gone.
    shutil.rmtree(path, ignore_errors=True)
    _git(repository, "worktree", "prune")
    return [
        evidence(
            "checkout-not-removed",
            path.as_posix(),
            f"git worktree remove --force in {repository} exited {removed.returncode}: "
            f"{_said(removed)}; the directory was deleted and the worktree list pruned",
        )
    ]


def _primary(origin: Path) -> Path:
    """The primary worktree of ``origin``'s repository: the first worktree Git lists."""
    listed = _git(origin, "worktree", "list", "--porcelain")
    first = listed.stdout.splitlines()[:2]
    if (
        listed.returncode != 0
        or not first
        or not first[0].startswith("worktree ")
        or "bare" in first[1:]
    ):
        raise RunError(
            "checkout_unavailable",
            f"the repository of {origin} has no primary worktree to hold the checkout of an "
            f"unbound run in its {WORKTREES}/ (git worktree list --porcelain exited "
            f"{listed.returncode}: {_said(listed)})",
        )
    return Path(os.path.realpath(first[0][len("worktree ") :]))


def open_checkout(origin: Path, run_id: str) -> Checkout:
    """Check out ``origin``'s ``HEAD`` detached as ``.claude/worktrees/unbound-<run_id>`` of the
    repository's primary worktree.

    Each relative runtime path of the checked-out worker configuration (``runtime`` of
    ``.concorde/workers.json``, by default ``.venv`` and ``node_modules``) that exists in ``origin`` and that Git ignores is linked
    into the checkout. ``RunError`` ``checkout_unavailable`` when ``HEAD`` names no commit, the
    primary worktree's Git does not ignore the checkout's place, the place is taken or Git
    refuses the checkout, which is then left nowhere.
    """
    head = _git(origin, "rev-parse", "--verify", "--quiet", "HEAD^{commit}")
    if head.returncode != 0:
        raise RunError(
            "checkout_unavailable",
            f"the worktree {origin} has no commit at HEAD to check out for an unbound run "
            f"(git rev-parse --verify HEAD^{{commit}} exited {head.returncode}: {_said(head)})",
        )
    commit = head.stdout.strip()
    primary = _primary(origin)
    relative = f"{WORKTREES}/{PREFIX}{run_id}"
    path = primary / relative
    ignored = _git(primary, "check-ignore", "--quiet", relative + "/")
    if ignored.returncode != 0:
        raise RunError(
            "checkout_unavailable",
            f"the checkout of {commit} for an unbound run belongs at {path}, but Git does not "
            f"ignore {relative}/ in the primary worktree {primary} (git check-ignore exited "
            f"{ignored.returncode}), so it would appear there as untracked files; add "
            f"{WORKTREES}/ to .gitignore",
        )
    if os.path.lexists(path):
        raise RunError(
            "checkout_unavailable",
            f"the place {path} of the checkout of {commit} for the unbound run {run_id} is "
            "already taken",
        )
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise RunError(
            "checkout_unavailable",
            f"the directory {path.parent} for the checkout of {commit} cannot be created: "
            f"{error}",
        ) from error
    added = _git(
        origin, "worktree", "add", "--detach", "--quiet", path.as_posix(), commit
    )
    if added.returncode != 0:
        shutil.rmtree(path, ignore_errors=True)
        _git(origin, "worktree", "prune")
        raise RunError(
            "checkout_unavailable",
            f"git worktree add --detach {path} {commit} in {origin} exited "
            f"{added.returncode}: {_said(added)}",
        )
    checkout = Checkout(origin, path, commit)
    try:
        _submodules(checkout)
        _environments(checkout, _runtime(path))
    except BaseException:
        checkout.close()
        raise
    return checkout


def _gitlinks(checkout: Path) -> list[tuple[str, str]]:
    """The submodule paths of the checkout's index with the commit each records."""
    listed = _git(checkout, "ls-files", "--stage", "-z")
    found = []
    for record in listed.stdout.split("\0"):
        head, _, path = record.partition("\t")
        fields = head.split()
        if len(fields) == 3 and fields[0] == "160000" and fields[2] == "0":
            found.append((path, fields[1]))
    return found


def _submodules(checkout: Checkout) -> None:
    """Check out every submodule the origin has checked out and holding the recorded commit."""
    for path, commit in _gitlinks(checkout.path):
        source = checkout.origin / path
        target = checkout.path / path
        if not (source / ".git").exists():
            checkout.evidence.append(
                evidence(
                    "submodule-absent",
                    path,
                    f"{checkout.origin} has not checked out the submodule {path}, so the "
                    "checkout leaves it empty",
                )
            )
            continue
        if _git(source, "cat-file", "-e", f"{commit}^{{commit}}").returncode != 0:
            checkout.evidence.append(
                evidence(
                    "submodule-absent",
                    path,
                    f"the submodule {path} of {checkout.origin} does not hold the commit {commit} "
                    f"that {checkout.commit} records, so the checkout leaves it empty",
                )
            )
            continue
        added = _git(
            source,
            "worktree",
            "add",
            "--detach",
            "--no-checkout",
            "--quiet",
            target.as_posix(),
            commit,
        )
        if added.returncode != 0:
            checkout.evidence.append(
                evidence(
                    "submodule-absent",
                    path,
                    f"git worktree add --detach {target} {commit} in {source} exited "
                    f"{added.returncode}: {_said(added)}; the checkout leaves it empty",
                )
            )
            continue
        checkout.submodules.append(path)
        steps = []
        if (
            _git(source, "config", "--bool", "core.sparseCheckout").stdout.strip()
            == "true"
        ):
            patterns = _git(source, "sparse-checkout", "list").stdout.split()
            steps.append(("sparse-checkout", "set", "--no-cone", *patterns))
        steps.append(("read-tree", "-mu", "HEAD"))
        for step in steps:
            done = _git(target, *step)
            if done.returncode != 0:
                checkout.evidence.append(
                    evidence(
                        "submodule-absent",
                        path,
                        f"git {' '.join(step[:2])} in the checkout of {path} exited "
                        f"{done.returncode}: {_said(done)}; the submodule may be incomplete",
                    )
                )
                break
        else:
            checkout.evidence.append(
                evidence("submodule", path, f"checked out at {commit} from {source}")
            )


def _runtime(checkout: Path) -> list:
    """``runtime`` of the checkout's worker configuration, or the default.

    An unreadable or invalid configuration links the default here; the run's first worker launch
    reports it in full.
    """
    try:
        return list(runtime(load(checkout)))
    except ModelConfigError:
        return list(DEFAULT_RUNTIME)


def _environments(checkout: Checkout, environments) -> None:
    """Link each relative runtime path the origin has and Git ignores into the checkout."""
    for entry in environments:
        if not isinstance(entry, str) or not entry.strip() or os.path.isabs(entry):
            continue
        relative = entry.strip().strip("/")
        source = checkout.origin / relative
        target = checkout.path / relative
        if not source.exists() or os.path.lexists(target) or not target.parent.is_dir():
            continue
        # The link does not exist yet, so a directory is named as one for ``dir/`` patterns.
        asked = relative + "/" if source.is_dir() else relative
        if _git(checkout.path, "check-ignore", "--quiet", asked).returncode != 0:
            checkout.evidence.append(
                evidence(
                    "environment-not-linked",
                    relative,
                    f"Git does not ignore {relative}, so the checkout of {checkout.commit} "
                    f"keeps its own and does not link {source}",
                )
            )
            continue
        target.symlink_to(source, target_is_directory=source.is_dir())
        checkout.links.append(target)
        checkout.evidence.append(
            evidence(
                "environment",
                relative,
                f"linked from {source}, which the run only reads",
            )
        )


__all__ = ["PREFIX", "Checkout", "open_checkout"]
