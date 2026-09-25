"""Linking a project's existing tests to the scenarios code_to_spec derived from them.

The code_to_spec worker never edits code. It names, for each scenario it wrote from a test, the
test as ``path::name`` or ``path::Class::name``; the host then adds a ``verifies`` decorator above
that test, so that the coverage check sees which test verifies which scenario. The decorator is
a two-line no-op the host defines in the test file itself: the scanner recognizes any decorator
named ``verifies``, so the project's tests never import Concorde and run the same in the
project's own environment. Only decorator lines and that definition are ever added; a test that
cannot be found, a file outside the described Modules or one that would no longer parse is left
as it was and reported.
"""

from __future__ import annotations

import ast
from pathlib import Path

from ..spec.verification import DeclarationError, _declarations

HELPER = (
    "def verifies(*scenarios):  # Concorde: names the scenarios a test verifies\n"
    "    return lambda test: test\n"
)


def _target(tree: ast.Module, qualified: list[str]):
    """The function node named by ``qualified`` (classes, then the function), or None."""
    body = tree.body
    for position, name in enumerate(qualified):
        last = position == len(qualified) - 1
        kinds = (ast.FunctionDef, ast.AsyncFunctionDef) if last else (ast.ClassDef,)
        found = next(
            (node for node in body if isinstance(node, kinds) and node.name == name),
            None,
        )
        if found is None:
            return None
        if last:
            return found
        body = found.body
    return None


def _defines_verifies(tree: ast.Module) -> bool:
    """Whether the module already binds the name ``verifies`` at its top level."""
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names = [node.name]
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.asname or alias.name for alias in node.names]
        elif isinstance(node, ast.Assign):
            names = [
                target.id for target in node.targets if isinstance(target, ast.Name)
            ]
        else:
            names = []
        if "verifies" in names:
            return True
    return False


def _helper_line(tree: ast.Module) -> int:
    """The 0-based line after the module docstring and the leading imports."""
    line = 0
    for position, node in enumerate(tree.body):
        docstring = (
            position == 0
            and isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        )
        if docstring or isinstance(node, (ast.Import, ast.ImportFrom)):
            line = node.end_lineno or node.lineno
            continue
        break
    return line


def link_file(path: Path, relative: str, links: list[tuple[str, str]]):
    """Add ``verifies`` decorators to one test file; ``links`` are (scenario, test name) pairs.
    Returns the linked pairs and the (pair, reason) of every link left undone."""
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=relative)
    except (OSError, UnicodeError, SyntaxError, ValueError) as error:
        return [], [
            (link, f"{relative} cannot be read as Python: {error}") for link in links
        ]
    try:
        declared = {
            (item.scenario_id, item.name) for item in _declarations(relative, tree)
        }
    except DeclarationError as error:
        return [], [
            (link, f"{relative} has a malformed verifies declaration: {error}")
            for link in links
        ]
    lines = source.splitlines(keepends=True)
    inserts: dict[int, list[str]] = {}
    linked, undone = [], []
    for scenario, name in links:
        if (scenario, name) in declared:
            linked.append((scenario, name))
            continue
        node = _target(tree, name.split("."))
        if node is None:
            undone.append(((scenario, name), f"{relative} has no test {name}"))
            continue
        first = min([node.lineno, *(item.lineno for item in node.decorator_list)])
        indent = " " * node.col_offset
        inserts.setdefault(first - 1, []).append(f'{indent}@verifies("{scenario}")\n')
        linked.append((scenario, name))
    if not inserts:
        return linked, undone
    for index in sorted(inserts, reverse=True):
        lines[index:index] = inserts[index]
    if not _defines_verifies(tree):
        at = _helper_line(tree)
        lines[at:at] = ["\n\n" if at else "", HELPER, "\n\n"]
    changed = "".join(lines)
    try:
        ast.parse(changed, filename=relative)
    except SyntaxError as error:
        return [], [
            (link, f"{relative} would not parse once decorated: {error}")
            for link in links
        ]
    path.write_text(changed, encoding="utf-8")
    return linked, undone


def link_tests(
    worktree: Path, promises: list[dict], scenarios: set[str], owned
) -> tuple[list[dict], list[dict]]:
    """Link every test the scenario promises name; ``scenarios`` are the scenario identities that
    exist and ``owned(path)`` tells whether a path is a project implementation file."""
    by_file: dict[str, list[tuple[str, str]]] = {}
    unlinked: list[dict] = []
    for promise in promises:
        tests = promise.get("tests") or []
        if not tests:
            continue
        scenario = promise.get("id")
        for test in tests:
            reason = None
            if promise.get("kind") != "scenario" or scenario not in scenarios:
                reason = f"{scenario!r} is not a scenario of the described Modules"
            elif "::" not in test:
                reason = "a test is named path::name or path::Class::name"
            else:
                relative, name = test.split("::", 1)
                if not relative.endswith(".py"):
                    reason = "only Python tests are linked"
                elif not owned(relative):
                    reason = f"{relative} is not an implementation file of any Module"
                elif not (worktree / relative).is_file():
                    reason = f"{relative} does not exist"
            if reason:
                unlinked.append({"scenario": scenario, "test": test, "reason": reason})
                continue
            by_file.setdefault(relative, []).append((scenario, name.replace("::", ".")))
    linked: list[dict] = []
    for relative, links in sorted(by_file.items()):
        done, undone = link_file(worktree / relative, relative, links)
        linked += [
            {"scenario": s, "test": f"{relative}::{n.replace('.', '::')}"}
            for s, n in done
        ]
        unlinked += [
            {
                "scenario": s,
                "test": f"{relative}::{n.replace('.', '::')}",
                "reason": reason,
            }
            for (s, n), reason in undone
        ]
    return linked, unlinked


__all__ = ["HELPER", "link_file", "link_tests"]
