"""Worker settings generated from one frozen grant: deny rules, the write hook and the Bash sandbox.

Claude Code applies ``Read`` deny rules to its file tools and also to the Bash sandbox, so the deny
rules are the one place that hides a path from a worker. They are generated from the grant and the
file tree:

- inside the task worktree, every path the grant gives no level or only ``names`` is denied for
  ``Read`` and ``Edit``, every ``ro`` path for ``Edit``; a directory holding nothing readable is
  denied as a whole;
- outside it, within the user's home and within the primary worktree, every sibling of the
  directories leading to the worktree, to the run's own directories and to the runtime paths is
  denied, so other projects, other task worktrees, the primary worktree and ``~/.claude`` stay
  hidden wherever the repository lies;
- the run's ``control/`` and ``config/`` directories and every Git administrative path Workers
  hands over (the common Git directory, the worktree's Git directory, every ``.git`` entry of the
  worktree and the Git directories they point to) are denied.

System directories and the declared runtime paths stay readable, because Bash needs them to run
anything. The write hook makes the grant's ``rw`` paths the only ones Edit and Write may change,
which deny rules cannot express. The sandbox confines Bash writes and network; its
``strictAllowlist`` makes an unlisted host a denial rather than a prompt, which
``bypassPermissions`` would otherwise approve.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from ..spec.grants import LEVELS

TOOL_SETS = {
    "understand": "Read,Glob,Grep",
    "review-spec": "Read,Glob,Grep",
    "review-code": "Read,Glob,Grep",
    "test": "Read,Glob,Grep",
    "specify": "Read,Glob,Grep,Edit,Write",
    "code-to-spec": "Read,Glob,Grep,Edit,Write",
    "implement": "Read,Glob,Grep,Edit,Write,Bash",
}
RANK = {"names": 1, "ro": 2, "rw": 3}
# The tool set of a grant with no writable path, whatever its task type.
READ_ONLY_TASK_TYPE = "understand"


def tool_set(tool_sets: dict, task_type: str, grant: dict | None) -> str:
    """The tool set of one backend for a task type, read-only when the grant writes nothing.

    A task type whose Protocol row writes no set gets the read-only set on every backend, which
    is how ``review-architecture`` gets the tools of ``review-spec`` without a row of its own. A harness may also give less than a
    task type assigns, such as a survey's ``code-to-spec`` grant with the Spec side withheld; such
    a worker gets no tool that changes files either.
    """
    if task_type in LEVELS and "rw" not in LEVELS[task_type].values():
        return tool_sets[READ_ONLY_TASK_TYPE]
    entries = grant.get("entries") if isinstance(grant, dict) else None
    if isinstance(entries, list) and not any(
        isinstance(entry, dict) and entry.get("level") == "rw" for entry in entries
    ):
        return tool_sets[READ_ONLY_TASK_TYPE]
    return tool_sets[task_type]


class SettingsError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class RunPaths:
    """The directories of one worker run: its runtime directory and its run directory.

    ``root`` is the runtime directory, a short private directory under ``/tmp`` that holds what
    the worker needs only while it runs and is removed when it ends: ``control/``, ``config/`` and
    the worker's own ``home/``, ``tmp/`` and ``work/``. Its path stays short because Claude Code's
    Bash sandbox creates Unix sockets below ``TMPDIR``, whose paths must stay under the kernel's
    108-byte limit. ``trace`` is the run directory, the worker run's trace node, which is kept.
    """

    root: Path
    trace: Path | None = None
    run_id: str = ""

    @property
    def control(self) -> Path:
        return self.root / "control"

    @property
    def config(self) -> Path:
        return self.root / "config"

    @property
    def home(self) -> Path:
        return self.root / "home"

    @property
    def tmp(self) -> Path:
        return self.root / "tmp"

    @property
    def work(self) -> Path:
        return self.root / "work"

    def own(self) -> tuple[Path, ...]:
        """The directories the worker itself uses, which no rule may hide."""
        return (self.work, self.home, self.tmp)


def entry_problem(entry) -> str | None:
    """What makes one grant entry malformed, or None for a well-formed one."""
    if not isinstance(entry, dict):
        return f"it is a {type(entry).__name__}, not an object"
    path, level = entry.get("path"), entry.get("level")
    if not isinstance(path, str) or not path:
        return "its path is missing or not a non-empty string"
    if path.startswith("/"):
        return f"its path {path!r} is absolute, not relative to the task worktree"
    if ".." in path.rstrip("/").split("/"):
        return f"its path {path!r} leaves the task worktree through '..'"
    if level not in RANK:
        return f"its level {level!r} is none of {', '.join(sorted(RANK))}"
    return None


class GrantView:
    """Levels of concrete paths under one frozen grant (project-relative entries).

    Raises ``SettingsError`` (``grant_malformed``) naming the first malformed entry and what is
    wrong with it, so nothing is generated from a grant whose entries cannot be read.
    """

    def __init__(self, entries):
        self.exact: dict[str, str] = {}
        self.directories: list[tuple[str, str]] = []
        if not isinstance(entries, list):
            raise SettingsError(
                "grant_malformed",
                f"the grant's entries are a {type(entries).__name__}, not a list of "
                "path and level entries",
            )
        for index, entry in enumerate(entries):
            problem = entry_problem(entry)
            if problem is not None:
                raise SettingsError(
                    "grant_malformed",
                    f"grant entry {index} ({json.dumps(entry, default=repr)}) is malformed: "
                    f"{problem}",
                )
            path, level = entry["path"], entry["level"]
            if path.endswith("/"):
                self.directories.append((path, level))
            else:
                self.exact[path] = level

    def level(self, relative: str) -> str | None:
        best = self.exact.get(relative)
        for directory, level in self.directories:
            if relative.startswith(directory) and (
                best is None or RANK[level] > RANK[best]
            ):
                best = level
        return best

    def paths(self, *levels: str) -> list[str]:
        return sorted(
            [path for path, level in self.exact.items() if level in levels]
            + [path for path, level in self.directories if level in levels]
        )

    def readable_below(self, directory: str) -> bool:
        """Whether any ``ro`` or ``rw`` path lies at or below ``directory`` (``a/b/``)."""
        for path, level in [*self.exact.items(), *self.directories]:
            if level in ("ro", "rw") and (
                path.startswith(directory) or directory.startswith(path)
            ):
                return True
        return False

    def directory_level(self, directory: str) -> str | None:
        """The level a directory entry gives every file below ``directory``, if any."""
        best = None
        for path, level in self.directories:
            if directory.startswith(path) and (
                best is None or RANK[level] > RANK[best]
            ):
                best = level
        return best


def grant_view(grant) -> GrantView:
    """The view of a frozen grant, or a ``SettingsError`` naming what makes it malformed."""
    if not isinstance(grant, dict) or "entries" not in grant:
        raise SettingsError(
            "grant_malformed",
            "the grant is not an object with an entries list"
            if not isinstance(grant, dict)
            else "the grant has no entries list",
        )
    return GrantView(grant["entries"])


def _rule(kind: str, path: Path, directory: bool) -> str:
    text = path.as_posix()
    return f"{kind}(/{text}/**)" if directory else f"{kind}(/{text})"


def _covers(path: Path, inner: Path) -> bool:
    return inner == path or path in inner.parents


def worktree_rules(
    worktree: Path, view: GrantView, keep: tuple[Path, ...]
) -> list[str]:
    """Deny rules inside the task worktree; ``keep`` paths (runtime) are left alone."""
    rules: list[str] = []

    def kept(path: Path) -> bool:
        return any(_covers(path, item) or _covers(item, path) for item in keep)

    def visit(directory: Path) -> None:
        for child in sorted(directory.iterdir(), key=lambda item: item.name):
            relative = child.relative_to(worktree).as_posix()
            if child.name == ".git":
                rules.extend(
                    [
                        _rule("Read", child, child.is_dir()),
                        _rule("Edit", child, child.is_dir()),
                    ]
                )
                continue
            if any(_covers(item, child) for item in keep):
                continue
            if child.is_dir() and not child.is_symlink():
                below = relative + "/"
                covering = view.directory_level(below)
                if covering == "rw":
                    continue
                if covering == "ro" and not any(
                    level == "rw" and path.startswith(below)
                    for path, level in view.exact.items()
                ):
                    rules.append(_rule("Edit", child, True))
                    continue
                if not view.readable_below(below) and not kept(child):
                    rules.extend(
                        [_rule("Read", child, True), _rule("Edit", child, True)]
                    )
                    continue
                visit(child)
                continue
            level = view.level(relative)
            if level == "rw":
                continue
            if level == "ro":
                rules.append(_rule("Edit", child, False))
            else:
                rules.extend([_rule("Read", child, False), _rule("Edit", child, False)])

    visit(worktree)
    return rules


def outside_rules(home: Path, keep: tuple[Path, ...]) -> list[str]:
    """Deny every entry of ``home`` that leads to none of the ``keep`` paths, recursively."""
    rules: list[str] = []
    if not home.is_dir():
        return rules
    inside = tuple(item for item in keep if _covers(home, item))

    def visit(directory: Path) -> None:
        for child in sorted(directory.iterdir(), key=lambda item: item.name):
            if any(_covers(item, child) for item in inside):
                continue  # a kept path or something below one
            if any(_covers(child, item) for item in inside):
                if child.is_dir() and not child.is_symlink():
                    visit(child)
                continue
            directory_entry = child.is_dir() and not child.is_symlink()
            rules.extend(
                [
                    _rule("Read", child, directory_entry),
                    _rule("Edit", child, directory_entry),
                ]
            )

    if inside:
        visit(home)
    else:
        rules.extend([_rule("Read", home, True), _rule("Edit", home, True)])
    return rules


def _boundaries(home: Path, primary: Path | None) -> list[Path]:
    """The directories hidden but for the paths leading to what the worker needs."""
    return [home] + ([primary] if primary is not None and primary != home else [])


def _git_rules(git: tuple[Path, ...]) -> list[str]:
    rules: list[str] = []
    for path in git:
        directory = path.is_dir() and not path.is_symlink()
        rules += [_rule("Read", path, directory), _rule("Edit", path, directory)]
    return rules


def deny_rules(
    worktree: Path,
    grant: dict,
    run: RunPaths,
    runtime: tuple[Path, ...] = (),
    home: Path | None = None,
    primary: Path | None = None,
    git: tuple[Path, ...] = (),
) -> list[str]:
    """Every deny rule of one worker (see the module docstring)."""
    worktree = Path(os.path.realpath(worktree))
    home = Path(os.path.realpath(home or Path.home()))
    primary = Path(os.path.realpath(primary)) if primary is not None else None
    view = grant_view(grant)
    runtime = tuple(Path(os.path.realpath(path)) for path in runtime)
    rules = worktree_rules(worktree, view, (*runtime, *run.own()))
    for boundary in _boundaries(home, primary):
        rules += outside_rules(boundary, (worktree, *run.own(), *runtime))
    rules += _git_rules(git)
    for directory in (run.control, run.config):
        rules += [_rule("Read", directory, True), _rule("Edit", directory, True)]
    return list(dict.fromkeys(rules))


def denied(rules: list[str], path: Path) -> bool:
    """Whether a ``Read`` rule in ``rules`` covers ``path``."""
    text = path.as_posix()
    for rule in rules:
        if not rule.startswith("Read(/"):
            continue
        target = rule[len("Read(/") : -1]
        if target.endswith("/**"):
            base = target[:-3]
            if text == base or text.startswith(base + "/"):
                return True
        elif text == target:
            return True
    return False


def sandbox_filesystem(
    worktree: Path,
    grant: dict,
    run: RunPaths,
    runtime: tuple[Path, ...] = (),
    home: Path | None = None,
    primary: Path | None = None,
    git: tuple[Path, ...] = (),
) -> dict:
    """The sandbox's filesystem lists of one worker, shared by both backends.

    Everything in the task worktree, the user's home and the primary worktree is hidden except the
    grant's ``ro`` and ``rw`` paths, the runtime paths and the run's own directories; only ``rw``
    paths and the run's own directories are writable; the run's ``control/`` and ``config/`` and
    every Git administrative path are hidden. A Git path inside a re-allowed ``ro`` or ``rw``
    directory stays hidden, since a narrower ``denyRead`` wins inside a wider ``allowRead``.
    """
    worktree = Path(os.path.realpath(worktree))
    home = Path(os.path.realpath(home or Path.home()))
    primary = Path(os.path.realpath(primary)) if primary is not None else None
    view = grant_view(grant)
    readable = [
        (worktree / path.rstrip("/")).as_posix() for path in view.paths("ro", "rw")
    ]
    writable = [(worktree / path.rstrip("/")).as_posix() for path in view.paths("rw")]
    own = [directory.as_posix() for directory in run.own()]
    return {
        "denyRead": list(
            dict.fromkeys(
                [
                    worktree.as_posix(),
                    *(boundary.as_posix() for boundary in _boundaries(home, primary)),
                    *(path.as_posix() for path in git),
                    run.control.as_posix(),
                    run.config.as_posix(),
                ]
            )
        ),
        "allowRead": sorted(
            set(
                readable
                + own
                + [Path(os.path.realpath(path)).as_posix() for path in runtime]
            )
        ),
        "allowWrite": sorted(set(writable + own)),
    }


def write_hook_source(worktree: Path, grant: dict) -> str:
    """The write hook script with the grant's lists embedded."""
    from . import write_hook

    view = grant_view(grant)
    data = {
        "worktree": Path(os.path.realpath(worktree)).as_posix(),
        "rw": view.paths("rw"),
        "ro": view.paths("ro"),
        "names": view.paths("names"),
    }
    source = Path(write_hook.__file__).read_text(encoding="utf-8")
    return source.replace(
        "GRANT: dict = {}", "GRANT: dict = " + json.dumps(data, sort_keys=True), 1
    )


def worker_settings(
    worktree: Path,
    grant: dict,
    run: RunPaths,
    *,
    python: str,
    runtime: tuple[Path, ...] = (),
    home: Path | None = None,
    primary: Path | None = None,
    git: tuple[Path, ...] = (),
) -> dict:
    """The complete ``settings.json`` of one worker."""
    worktree = Path(os.path.realpath(worktree))
    home = Path(os.path.realpath(home or Path.home()))
    rules = deny_rules(worktree, grant, run, runtime, home, primary, git)
    for directory in run.own():
        if denied(rules, directory):
            raise SettingsError(
                "run_directory_denied",
                f"a generated deny rule covers the worker's own directory {directory}",
            )
    return {
        "permissions": {"deny": rules},
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Edit|Write|MultiEdit|NotebookEdit",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"{python} {(run.control / 'write_hook.py').as_posix()}",
                        }
                    ],
                }
            ]
        },
        "sandbox": {
            "enabled": True,
            "autoAllowBashIfSandboxed": True,
            "allowUnsandboxedCommands": False,
            "filesystem": sandbox_filesystem(
                worktree, grant, run, runtime, home, primary, git
            ),
            "network": {"allowedDomains": [], "strictAllowlist": True},
        },
    }


__all__ = [
    "RunPaths",
    "SettingsError",
    "TOOL_SETS",
    "deny_rules",
    "denied",
    "grant_view",
    "sandbox_filesystem",
    "worker_settings",
    "write_hook_source",
]
