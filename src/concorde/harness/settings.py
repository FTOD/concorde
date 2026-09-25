"""Worker settings generated from one frozen grant: deny rules, the write hook and the Bash sandbox.

Claude Code applies ``Read`` deny rules to its file tools and also to the Bash sandbox, so the deny
rules are the one place that hides a path from a worker. They are generated from the grant and the
file tree:

- inside the task worktree, every path the grant gives no level or only ``names`` is denied for
  ``Read`` and ``Edit``, every ``ro`` path for ``Edit``; a directory holding nothing readable is
  denied as a whole;
- outside it, within the user's home, every sibling of the directories leading to the worktree,
  to the run's own directories and to the runtime paths is denied, so other projects, other task
  worktrees and ``~/.claude`` stay hidden;
- the run's ``control/`` and ``config/`` directories and the worktree's Git metadata are denied.

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

    A harness may give less than a task type assigns, such as a survey's ``code-to-spec`` grant
    with the Spec side withheld; such a worker gets no tool that changes files.
    """
    if grant is not None and not any(
        entry.get("level") == "rw" for entry in grant.get("entries") or []
    ):
        return tool_sets[READ_ONLY_TASK_TYPE]
    return tool_sets[task_type]


class SettingsError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class RunPaths:
    """The directories of one run (see the run directory layout).

    ``short_tmp`` replaces ``<run>/tmp`` as ``TMPDIR`` when set: Claude Code's Bash sandbox creates
    Unix sockets below ``TMPDIR``, whose paths must stay under the kernel's 108-byte limit.
    """

    root: Path
    short_tmp: Path | None = None

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
        return self.short_tmp or self.root / "tmp"

    @property
    def work(self) -> Path:
        return self.root / "work"

    @property
    def checks(self) -> Path:
        return self.root / "checks"

    def own(self) -> tuple[Path, ...]:
        """The directories the worker itself uses, which no rule may hide."""
        return (self.work, self.home, self.tmp)


class GrantView:
    """Levels of concrete paths under one frozen grant (project-relative entries)."""

    def __init__(self, entries):
        self.exact: dict[str, str] = {}
        self.directories: list[tuple[str, str]] = []
        for entry in entries:
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
            if child.name == ".git" and directory == worktree:
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


def deny_rules(
    worktree: Path,
    grant: dict,
    run: RunPaths,
    runtime: tuple[Path, ...] = (),
    home: Path | None = None,
) -> list[str]:
    """Every deny rule of one worker (see the module docstring)."""
    worktree = Path(os.path.realpath(worktree))
    home = Path(os.path.realpath(home or Path.home()))
    view = GrantView(grant["entries"])
    runtime = tuple(Path(os.path.realpath(path)) for path in runtime)
    rules = worktree_rules(worktree, view, (*runtime, *run.own()))
    rules += outside_rules(home, (worktree, *run.own(), *runtime))
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
) -> dict:
    """The sandbox's filesystem lists of one worker, shared by both backends.

    Everything in the task worktree and the user's home is hidden except the grant's ``ro`` and
    ``rw`` paths, the runtime paths and the run's own directories; only ``rw`` paths and the run's
    own directories are writable; the run's ``control/`` and ``config/`` are hidden.
    """
    worktree = Path(os.path.realpath(worktree))
    home = Path(os.path.realpath(home or Path.home()))
    view = GrantView(grant["entries"])
    readable = [
        (worktree / path.rstrip("/")).as_posix() for path in view.paths("ro", "rw")
    ]
    writable = [(worktree / path.rstrip("/")).as_posix() for path in view.paths("rw")]
    own = [directory.as_posix() for directory in run.own()]
    return {
        "denyRead": [
            worktree.as_posix(),
            home.as_posix(),
            run.control.as_posix(),
            run.config.as_posix(),
        ],
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

    view = GrantView(grant["entries"])
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
) -> dict:
    """The complete ``settings.json`` of one worker."""
    worktree = Path(os.path.realpath(worktree))
    home = Path(os.path.realpath(home or Path.home()))
    rules = deny_rules(worktree, grant, run, runtime, home)
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
            "filesystem": sandbox_filesystem(worktree, grant, run, runtime, home),
            "network": {"allowedDomains": [], "strictAllowlist": True},
        },
    }


__all__ = [
    "RunPaths",
    "SettingsError",
    "TOOL_SETS",
    "deny_rules",
    "denied",
    "sandbox_filesystem",
    "worker_settings",
    "write_hook_source",
]
