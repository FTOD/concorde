#!/usr/bin/env python3
"""Check out Concorde's vendored external references (git submodules) without their media, and
link the rendered skills where Claude Code finds them.

A Module may declare third-party documentation or source as an ``includes`` of kind ``external``,
vendored under ``references/`` as a git submodule pinned to a fixed revision. A plain
``git submodule update --init`` would download the upstream repositories' media as well. This script performs the checkout the
Framework expects instead: a partial clone (``--filter=blob:none``) whose sparse-checkout
patterns, recorded in ``.gitmodules`` under ``submodule.<name>.concorde-sparse``, exclude media by
suffix, checked out at exactly the commit the superproject records.

    python3 scripts/development/init-references.py            # every submodule in .gitmodules
    python3 scripts/development/init-references.py --check    # report without cloning

Run it once in a fresh clone (after ``python3 scripts/concorde.py build``); with no submodule in
``.gitmodules`` it does nothing. A reference counts as checked out only when its clone is at the
recorded commit: one that is not, as a clone whose fetch of that commit failed is left, is
completed in place on the next run, which names the commit it found.

The submodules' registration (``submodule.<name>.url`` and ``.active``) lives in the repository's
shared ``.git/config``, which every worktree reads. A registered submodule is not registered again,
so preparing another worktree only reads that file: writing it needs its lock, ``config.lock``,
which another Git command writing that configuration — one of another worktree's preparation, for
instance — holds meanwhile.

Claude Code finds the ``concorde`` and ``concorde-development`` skills of this checkout through
``.claude/skills/<name>``, links into ``generated/skills/`` that Git does not track. The script
creates each missing link, replaces a link that points elsewhere and leaves a real file or
directory in its place as it is, saying so. ``--check`` reports them without linking.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ("concorde", "concorde-development")


def git(
    *arguments: str, cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *arguments),
        cwd=cwd or ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def submodules() -> list[dict[str, str]]:
    if not (ROOT / ".gitmodules").is_file():
        return []
    entries: dict[str, dict[str, str]] = {}
    listing = git("config", "-f", ".gitmodules", "--list").stdout
    for line in listing.splitlines():
        key, _, value = line.partition("=")
        if not key.startswith("submodule."):
            continue
        name, field = key[len("submodule.") :].rsplit(".", 1)
        entries.setdefault(name, {"name": name})[field] = value
    return [entry for entry in entries.values() if "path" in entry and "url" in entry]


def recorded_commit(path: str) -> str | None:
    listing = git("ls-files", "--stage", "--", path, check=False).stdout.split()
    return listing[1] if len(listing) >= 4 and listing[0] == "160000" else None


def config_value(key: str) -> str | None:
    found = git("config", "--get", key, check=False)
    return found.stdout.strip() if found.returncode == 0 else None


def registered(entry: dict[str, str]) -> bool:
    """Whether ``git submodule init`` would leave the shared configuration as it is.

    It writes ``submodule.<name>.active`` unless the submodule is active, its ``url`` unless one
    is set and its ``update`` when ``.gitmodules`` gives one that is not set. Without
    ``submodule.<name>.active`` or ``submodule.active`` a submodule is active when its ``url`` is
    set; a ``submodule.active`` pathspec is left to Git by reporting the entry unregistered.
    """
    name = entry["name"]
    if config_value(f"submodule.{name}.url") is None:
        return False
    active = git("config", "--bool", "--get", f"submodule.{name}.active", check=False)
    if active.returncode == 0:
        if active.stdout.strip() != "true":
            return False
    elif config_value("submodule.active") is not None:
        return False
    return "update" not in entry or config_value(f"submodule.{name}.update") is not None


def register(entry: dict[str, str]) -> None:
    """Register the submodule in the shared configuration unless it already is."""
    if registered(entry):
        return
    path = entry["path"]
    config = (
        Path(
            git(
                "rev-parse", "--path-format=absolute", "--git-common-dir"
            ).stdout.strip()
        )
        / "config"
    )
    lock = config.with_name("config.lock")
    busy = (
        f"{lock} exists, so Git cannot write {config}: a Git command is writing the shared "
        "configuration now, such as another worktree's preparation registering its own "
        "submodules. Wait until that command ends and run this script again; never delete "
        "the lock"
    )
    if lock.exists():
        raise SystemExit(f"cannot register the submodule {path} in {config}: {busy}")
    done = git("submodule", "init", "--", path, check=False)
    if done.returncode or not registered(entry):
        said = done.stderr.strip() or done.stdout.strip() or "no output"
        cause = busy if lock.exists() or "lock" in said else "see Git's output"
        raise SystemExit(
            f"cannot register the submodule {path} in {config}: git submodule init exited "
            f"{done.returncode} ({said}) and left it unregistered; {cause}"
        )


def cloned(path: str) -> bool:
    """Whether the reference has a clone of its own, checked out or not."""
    directory = ROOT / path
    return directory.is_dir() and (directory / ".git").exists()


def head(path: str) -> str | None:
    """The commit the reference's clone has checked out, or None without one."""
    if not cloned(path):
        return None
    found = git(
        "rev-parse", "--verify", "--quiet", "HEAD", cwd=ROOT / path, check=False
    )
    return found.stdout.strip() or None if found.returncode == 0 else None


def checked_out(path: str) -> bool:
    """Whether the reference is checked out at exactly the commit the superproject records.

    A clone whose fetch of that commit failed is left on the remote's default branch with
    nothing checked out, and is no more checked out than a missing one."""
    commit = recorded_commit(path)
    return commit is not None and head(path) == commit


def initialize(entry: dict[str, str]) -> None:
    path, url = entry["path"], entry["url"]
    commit = recorded_commit(path)
    if commit is None:
        raise SystemExit(f"{path} is not a submodule of this checkout")
    # A linked worktree has a .git *file*. Git resolves a worktree-local
    # administrative path, keeping this checkout's submodules independent.
    module_dir = Path(
        git(
            "rev-parse", "--path-format=absolute", "--git-path", f"modules/{path}"
        ).stdout.strip()
    )
    if module_dir.exists():
        raise SystemExit(
            f"{module_dir} already exists; remove it or finish the checkout by hand"
        )
    module_dir.parent.mkdir(parents=True, exist_ok=True)
    git(
        "clone",
        "--quiet",
        "--filter=blob:none",
        "--no-checkout",
        "--separate-git-dir",
        str(module_dir),
        url,
        str(ROOT / path),
    )
    patterns = entry.get("concorde-sparse")
    if patterns:
        git(
            "sparse-checkout",
            "set",
            "--no-cone",
            *shlex.split(patterns),
            cwd=ROOT / path,
        )
    fetch = git(
        "fetch",
        "--quiet",
        "--depth",
        "1",
        "origin",
        commit,
        cwd=ROOT / path,
        check=False,
    )
    if fetch.returncode:
        raise SystemExit(f"cannot fetch {commit} for {path}: {fetch.stderr.strip()}")
    git("checkout", "--quiet", "--detach", commit, cwd=ROOT / path)


def complete(entry: dict[str, str]) -> None:
    """Check out the recorded commit in a clone that is not at it, fetching it when the clone
    lacks it, as a run whose fetch failed leaves it."""
    path = entry["path"]
    commit = recorded_commit(path)
    if commit is None:
        raise SystemExit(f"{path} is not a submodule of this checkout")
    present = git(
        "cat-file", "-e", f"{commit}^{{commit}}", cwd=ROOT / path, check=False
    )
    if present.returncode:
        fetch = git(
            "fetch",
            "--quiet",
            "--depth",
            "1",
            "origin",
            commit,
            cwd=ROOT / path,
            check=False,
        )
        if fetch.returncode:
            raise SystemExit(
                f"cannot fetch {commit} for {path}: {fetch.stderr.strip()}"
            )
    done = git("checkout", "--quiet", "--detach", commit, cwd=ROOT / path, check=False)
    if done.returncode:
        raise SystemExit(
            f"cannot check out {commit} in {path}, whose clone is at {head(path) or 'no commit'}: "
            f"{done.stderr.strip() or done.stdout.strip()}"
        )


def skill_target(name: str) -> str:
    """The text of the link ``.claude/skills/<name>``: the skill's folder of the build's output."""
    return (Path("../../generated/skills") / name).as_posix()


def link_skills(check: bool) -> int:
    """Link ``.claude/skills/<name>`` to ``generated/skills/<name>`` for every skill; return how
    many are not linked. A link pointing elsewhere is replaced, a real file or directory is never
    touched, and ``check`` only reports."""
    unlinked = 0
    for name in SKILLS:
        link = ROOT / ".claude" / "skills" / name
        shown = link.relative_to(ROOT).as_posix()
        target = skill_target(name)
        if link.is_symlink():
            found = os.readlink(link)
            if found == target:
                print(f"{shown}: linked to {target}")
                continue
            if check:
                unlinked += 1
                print(f"{shown}: links to {found}, not {target}")
                continue
            link.unlink()
            link.symlink_to(target)
            print(f"{shown}: relinked to {target} (was {found})")
        elif link.exists():
            unlinked += 1
            kind = "directory" if link.is_dir() else "file"
            print(
                f"{shown}: a {kind} stands where the link to {target} goes and is left as it "
                f"is, so Claude Code reads it instead of the rendered skill; move it away and "
                "run this script again to link the skill",
                file=sys.stderr,
            )
        elif check:
            unlinked += 1
            print(f"{shown}: missing, not linked to {target}")
        else:
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(target)
            print(f"{shown}: linked to {target}")
    return unlinked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report the state of every reference without cloning",
    )
    arguments = parser.parse_args(argv)
    unlinked = link_skills(arguments.check)
    entries = submodules()
    if not entries:
        print("no submodules declared in .gitmodules")
        return 1 if arguments.check and unlinked else 0
    if not arguments.check:
        # Register every missing submodule before cloning any, so that a busy configuration lock
        # stops the script before it leaves some references checked out and others not.
        for entry in entries:
            if not cloned(entry["path"]):
                register(entry)
    missing = 0
    for entry in entries:
        path = entry["path"]
        commit = recorded_commit(path) or "?"
        if checked_out(path):
            print(f"{path}: checked out @ {commit}")
            continue
        found = head(path) if cloned(path) else None
        if arguments.check:
            missing += 1
            state = (
                f"not at the recorded commit (at {found or 'no commit'})"
                if cloned(path)
                else "missing"
            )
            print(f"{path}: {state} @ {commit}")
            continue
        if cloned(path):
            complete(entry)
            print(f"{path}: completed @ {commit} (was at {found or 'no commit'})")
        else:
            initialize(entry)
            print(f"{path}: initialized @ {commit}")
    return 1 if arguments.check and (missing or unlinked) else 0


if __name__ == "__main__":
    sys.exit(main())
