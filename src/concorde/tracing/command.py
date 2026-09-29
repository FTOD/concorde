"""``concorde trace show|list|prune``: read traces, and remove what retention allows.

``show`` and ``list`` write nothing. Each prints one JSON value (``contract.tracing.view``), or
with ``--format tree`` the same as an indented text tree; ``prune`` prints the folders it removed.
Exit status 0 on success, 1 for a refusal printed as ``{"error": <link>}``, 2 for a malformed
command line.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .. import errors
from . import layout, reader, retention

ACTOR = "Tracing (concorde trace)"


class UsageError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(f"{self.prog}: {message}")


def parser() -> argparse.ArgumentParser:
    command = _Parser(prog="concorde trace")
    sub = command.add_subparsers(dest="command", required=True, parser_class=_Parser)
    show = sub.add_parser("show")
    show.add_argument("node", nargs="?")
    show.add_argument("--depth", type=int)
    show.add_argument("--format", choices=["json", "tree"], default="json")
    listed = sub.add_parser("list")
    listed.add_argument("--history", action="store_true")
    listed.add_argument("--unbound", action="store_true")
    listed.add_argument("--format", choices=["json", "tree"], default="json")
    prune = sub.add_parser("prune")
    prune.add_argument("--dry-run", action="store_true")
    return command


def _refuse(code: str, detail: str, reason: str, explanation: str, options=()) -> int:
    link = errors.link(
        "component",
        ACTOR,
        code,
        detail,
        reason=reason,
        explanation=explanation,
        options=list(options),
    )
    sys.stdout.write(json.dumps({"error": link}, indent=2) + "\n")
    sys.stderr.write(errors.render(link) + "\n")
    return 1


def _bound_workspace(here: Path) -> list[Path]:
    worktree = reader._toplevel(here)
    binding = reader._binding(worktree) if worktree else None
    if binding and isinstance(binding.get("traces"), str):
        return [Path(binding["traces"])]
    return []


def show(arguments, here: Path) -> int:
    searched = reader.roots(here)
    workspaces = _bound_workspace(here)
    if arguments.node is None:
        if not workspaces:
            return _refuse(
                "no_node",
                f"concorde trace show was given no node, and {here} holds no workspace binding "
                "whose task it could show",
                "input",
                "the reader shows the node it is given or the current worktree's task",
                ["name a task, a run or worker run identity or a node's folder"],
            )
        workspace = workspaces[0]
        target = (
            workspace.parent
            if (workspace.parent / layout.TRACE).is_file()
            else workspace
        )
        concorde = next(
            (root for root in searched if reader._inside(target, root)), searched[0]
        )
    else:
        try:
            target, concorde = reader.locate(arguments.node, searched, workspaces)
        except reader.ReadError as error:
            return _refuse(
                error.code,
                str(error),
                "input",
                "the reader shows only nodes it finds and never guesses another",
                ["run `concorde trace list --history --unbound` to see what exists"],
            )
    try:
        value = reader.view(target, concorde, depth=arguments.depth)
    except reader.ReadError as error:
        return _refuse(
            error.code, str(error), "input", "the node's record cannot be read"
        )
    _print(value if arguments.format == "json" else None, reader.render(value))
    return 0


def _print(value, text: str) -> None:
    if value is not None:
        sys.stdout.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(text + "\n")


def listing(arguments, here: Path) -> int:
    searched = reader.roots(here)
    nodes = []
    seen = set()
    for root in searched:
        for item in reader.listing(
            root, history=arguments.history, unbound=arguments.unbound
        ):
            if item["path"] not in seen:
                seen.add(item["path"])
                nodes.append(item)
    if arguments.format == "json":
        _print(nodes, "")
    else:
        _print(None, "\n".join(reader.render(item) for item in nodes) or "(no traces)")
    return 0


def prune(arguments, here: Path) -> int:
    primary = layout.primary_worktree(here)
    concorde = layout.concorde_of(primary or here)
    try:
        removed = retention.prune(concorde, dry_run=arguments.dry_run)
    except retention.ConfigError as error:
        return _refuse(
            error.code,
            str(error),
            "input",
            "retention reads only a Tracing configuration that satisfies its contract",
            [f"correct or remove {concorde / layout.CONFIGURATION}"],
        )
    _print({"removed": removed, "dry_run": arguments.dry_run}, "")
    return 0


def main(words, here: Path | None = None) -> int:
    here = Path(here or Path.cwd())
    try:
        arguments = parser().parse_args(list(words))
    except UsageError as error:
        sys.stderr.write(f"{error}\n")
        return 2
    if arguments.command == "show":
        if arguments.depth is not None and arguments.depth < 0:
            sys.stderr.write(
                f"concorde trace show: --depth {arguments.depth} is negative\n"
            )
            return 2
        return show(arguments, here)
    if arguments.command == "list":
        return listing(arguments, here)
    return prune(arguments, here)


__all__ = ["main", "parser"]
