"""Linking a project's existing tests to the scenarios code_to_spec derived from them.

The code_to_spec worker never edits code. It names, for each scenario it wrote from a test, the
test as ``path::name`` or ``path::Class::name``; the host then adds a ``verifies`` decorator above
that test, so that the coverage check sees which test verifies which scenario. The decorator is
a two-line no-op the host defines in the test file itself: the scanner recognizes any decorator
named ``verifies``, so the project's tests never import Concorde and run the same in the
project's own environment. Only decorator lines and that definition, with the blank lines that
set it apart, are ever added: every byte already in the file, its line endings and blank lines
included, stays as it was. A test that cannot be found or is defined more than once, a file
outside the described Modules, one that would no longer parse, one that already binds
``verifies`` to something other than that helper or Concorde's decorator, or binds it only where
a decorator could not use it, and one that cannot be written are left as they were and reported.
"""

from __future__ import annotations

import ast
import errno
import os
import stat
import tempfile
from pathlib import Path

from ...spec.errors import SpecError
from ...spec.typed_data import checked_path
from ...spec.verification import DeclarationError, _declarations, parse_source

DECORATOR_MODULE = "concorde.spec.verification"
HELPER = (
    "def verifies(*scenarios):  # Concorde: names the scenarios a test verifies\n"
    "    return lambda test: test\n"
)
# The statements whose bodies are scopes of their own: a name bound there is no module-level
# binding, and a function defined in a function is a helper, never a test.
SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
# The parts of a statement that hold statements of their own.
BLOCKS = (ast.stmt, ast.excepthandler, ast.match_case)


def _statements(body: list[ast.stmt]):
    """Every statement of ``body`` and, in source order, every statement nested in its
    control-flow statements (``if``, ``try``, ``with``, loops, ``match``), but never one inside a
    function or class body."""
    for node in body:
        yield node
        if isinstance(node, SCOPES):
            continue
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.stmt):
                yield from _statements([child])
            elif isinstance(child, (ast.excepthandler, ast.match_case)):
                yield from _statements(
                    [
                        item
                        for item in ast.iter_child_nodes(child)
                        if isinstance(item, ast.stmt)
                    ]
                )


def _target(tree: ast.Module, qualified: list[str]):
    """The function node named by ``qualified`` (classes, then the function) and None, or None and
    why it cannot be told. A definition under a module-level or class-level ``if``, ``try`` or
    other control-flow statement counts; one inside a function never does."""
    body = tree.body
    for position, name in enumerate(qualified):
        last = position == len(qualified) - 1
        kinds = (ast.FunctionDef, ast.AsyncFunctionDef) if last else (ast.ClassDef,)
        found = [
            node
            for node in _statements(body)
            if isinstance(node, kinds) and node.name == name
        ]
        if not found:
            return None, f"has no test {'.'.join(qualified)}"
        if len(found) > 1:
            return None, (
                f"defines {'.'.join(qualified[: position + 1])} {len(found)} times (lines "
                f"{', '.join(str(node.lineno) for node in found)}), so which definition the "
                f"test {'.'.join(qualified)} is cannot be told"
            )
        if last:
            return found[0], None
        body = found[0].body
    return None, f"has no test {'.'.join(qualified)}"


def _bound_names(node: ast.AST) -> set[str]:
    """The names ``node`` binds in the module's scope itself: a definition's or import's names, an
    assignment's, loop's or ``with``'s targets, an ``except``'s name, an assignment expression's
    target and a pattern's captures, but not those of the statements, handlers and match cases
    nested in it, nor a lambda's or a comprehension's own variables."""
    names: set[str] = set()
    if isinstance(node, SCOPES):
        names.add(node.name)
    elif isinstance(node, (ast.Import, ast.ImportFrom)):
        names.update(alias.asname or alias.name.split(".")[0] for alias in node.names)
    elif isinstance(node, ast.ExceptHandler) and node.name:
        names.add(node.name)
    pending = list(ast.iter_child_nodes(node))
    while pending:
        item = pending.pop()
        if isinstance(item, BLOCKS):
            continue
        if isinstance(item, ast.Lambda):
            pending.append(item.args)
            continue
        if isinstance(item, ast.comprehension):
            pending += [item.iter, *item.ifs]
            continue
        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store):
            names.add(item.id)
        elif isinstance(item, (ast.MatchAs, ast.MatchStar)) and item.name:
            names.add(item.name)
        elif isinstance(item, ast.MatchMapping) and item.rest:
            names.add(item.rest)
        pending.extend(ast.iter_child_nodes(item))
    return names


def _binding_nodes(node: ast.AST):
    if "verifies" in _bound_names(node):
        # A match case has no line of its own; its pattern has.
        yield node.pattern if isinstance(node, ast.match_case) else node
    if isinstance(node, SCOPES):
        return
    for child in ast.iter_child_nodes(node):
        if isinstance(child, BLOCKS):
            yield from _binding_nodes(child)


def _bindings(body: list[ast.stmt]):
    """Every statement, ``except`` clause or match pattern that binds the name ``verifies`` at
    module level in ``body``, including those inside a top-level ``if``, ``try``, ``with``, loop
    or ``match``, but never inside a function or class body."""
    for node in body:
        yield from _binding_nodes(node)


def _is_helper(node: ast.AST) -> bool:
    """Whether ``node`` is Concorde's no-op helper: ``def verifies(*names)`` returning a lambda
    that returns its one argument, however it is formatted or commented."""
    if not isinstance(node, ast.FunctionDef) or node.decorator_list:
        return False
    arguments = node.args
    if (
        arguments.vararg is None
        or arguments.posonlyargs
        or arguments.args
        or arguments.kwonlyargs
        or arguments.kwarg
    ):
        return False
    body = node.body
    if (
        len(body) == 2
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    if len(body) != 1 or not isinstance(body[0], ast.Return):
        return False
    function = body[0].value
    if not isinstance(function, ast.Lambda):
        return False
    parameters = function.args
    return (
        len(parameters.args) == 1
        and not (
            parameters.posonlyargs
            or parameters.vararg
            or parameters.kwonlyargs
            or parameters.kwarg
        )
        and isinstance(function.body, ast.Name)
        and function.body.id == parameters.args[0].arg
    )


def _is_decorator_import(node: ast.AST) -> bool:
    """Whether ``node`` imports Concorde's own ``verifies`` decorator under its own name."""
    return (
        isinstance(node, ast.ImportFrom)
        and node.level == 0
        and node.module == DECORATOR_MODULE
        and all(
            alias.name == "verifies"
            for alias in node.names
            if (alias.asname or alias.name) == "verifies"
        )
    )


def _allowed(node: ast.AST) -> bool:
    return _is_helper(node) or _is_decorator_import(node)


def _foreign_binding(tree: ast.Module) -> ast.AST | None:
    """The first module-level binding of ``verifies`` that is neither Concorde's helper nor an
    import of its decorator, or None."""
    return next((node for node in _bindings(tree.body) if not _allowed(node)), None)


def _usable_before(tree: ast.Module, line: int) -> bool:
    """Whether a binding of ``verifies`` to Concorde's helper or decorator stands at the module's
    top level, outside every branch, and ends before ``line``, so that a decorator there finds
    it when the module is imported."""
    return any(
        _allowed(node)
        and "verifies" in _bound_names(node)
        and (node.end_lineno or node.lineno) < line
        for node in tree.body
    )


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


def _newline(lines: list[bytes]) -> bytes:
    """The line ending the file uses, read from its first line that has one."""
    for line in lines:
        for ending in (b"\r\n", b"\n", b"\r"):
            if line.endswith(ending):
                return ending
    return b"\n"


def _helper_block(lines: list[bytes], tree: ast.Module, newline: bytes):
    """Where the helper goes, as a 0-based line index, and the bytes inserted there: the helper
    after the docstring and the leading imports, set apart by two blank lines on each side
    counting the blank lines already there, none of which is removed."""
    at = _helper_line(tree)
    if at == 0:
        # A file that begins with code keeps its leading comments, such as an interpreter line
        # or an encoding declaration, above the helper.
        while at < len(lines) and lines[at].lstrip().startswith(b"#"):
            at += 1
    index, blank = at, 0
    while index < len(lines) and not lines[index].strip():
        index += 1
        blank += 1
    block = [newline] * max(0, 2 - blank) if at else []
    block.append(HELPER.encode("utf-8").replace(b"\n", newline))
    if index < len(lines):
        block += [newline, newline]
    return index, block


def _replace(path: Path, data: bytes) -> None:
    """Replace the file's bytes through a new file in its directory, so that a write that fails
    leaves the original as it was; a file the project made read-only is not replaced."""
    if not os.access(path, os.W_OK):
        raise PermissionError(errno.EACCES, "the file is not writable", str(path))
    mode = stat.S_IMODE(path.stat().st_mode)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".concorde"
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def link_file(path: Path, relative: str, links: list[tuple[str, str]]):
    """Add ``verifies`` decorators to one test file; ``links`` are (scenario, test name) pairs.
    Returns the linked pairs and the (pair, reason) of every link left undone, each pair once."""
    links = list(dict.fromkeys(links))
    try:
        data = path.read_bytes()
        tree = parse_source(data, relative)
    except (OSError, SyntaxError, ValueError) as error:
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
    # A decorator would call the project's own `verifies`, whatever that does.
    foreign = _foreign_binding(tree)
    conflict = foreign and (
        f"{relative} binds verifies at line {foreign.lineno} to something other than "
        "Concorde's helper or its verifies decorator"
    )
    bound = next(_bindings(tree.body), None)
    lines = data.splitlines(keepends=True)
    newline = _newline(lines)
    inserts: dict[int, list[bytes]] = {}
    linked, scheduled, undone = [], [], []
    for scenario, name in links:
        pair = (scenario, name)
        if pair in declared:
            linked.append(pair)
            continue
        if conflict:
            undone.append((pair, conflict))
            continue
        node, problem = _target(tree, name.split("."))
        if node is None:
            undone.append((pair, f"{relative} {problem}"))
            continue
        first = min([node.lineno, *(item.lineno for item in node.decorator_list)])
        if bound is not None and not _usable_before(tree, first):
            undone.append(
                (
                    pair,
                    (
                        f"{relative} binds verifies at line {bound.lineno} to Concorde's "
                        f"helper or decorator, but not at its top level before {name} at "
                        f"line {first}, so a decorator there could not use it"
                    ),
                )
            )
            continue
        line = lines[first - 1]
        indent = line[: len(line) - len(line.lstrip(b" \t\f"))]
        inserts.setdefault(first - 1, []).append(
            indent + f'@verifies("{scenario}")'.encode() + newline
        )
        linked.append(pair)
        scheduled.append(pair)
    if not scheduled:
        return linked, undone
    if bound is None:
        index, block = _helper_block(lines, tree, newline)
        inserts.setdefault(index, [])[:0] = block
    changed = b"".join(
        [
            text
            for index, line in enumerate(lines)
            for text in (*inserts.get(index, []), line)
        ]
        + inserts.get(len(lines), [])
    )
    kept = [pair for pair in linked if pair not in scheduled]
    try:
        parse_source(changed, relative)
    except (SyntaxError, ValueError) as error:
        return kept, undone + [
            (pair, f"{relative} would not parse once decorated: {error}")
            for pair in scheduled
        ]
    try:
        _replace(path, changed)
    except OSError as error:
        return kept, undone + [
            (pair, f"{relative} could not be written and was left as it was: {error}")
            for pair in scheduled
        ]
    return linked, undone


def link_tests(
    worktree: Path, promises: list[dict], scenarios: set[str], owned
) -> tuple[list[dict], list[dict]]:
    """Link every test the scenario promises name; ``scenarios`` are the scenario identities that
    exist and ``owned(path)`` tells whether a path is a project implementation file. A link named
    more than once is linked or reported once; a file that cannot be linked is reported and the
    next file is linked all the same."""
    by_file: dict[str, list[tuple[str, str]]] = {}
    unlinked: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for promise in promises:
        tests = promise.get("tests") or []
        if not tests:
            continue
        scenario = promise.get("id")
        for test in tests:
            if (scenario, test) in seen:
                continue
            seen.add((scenario, test))
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
                else:
                    try:
                        exists = checked_path(worktree, relative).is_file()
                    except SpecError as error:
                        # The coverage check reads no file through a symbolic link either.
                        reason = f"{relative} is not a file the coverage check reads: {error}"
                    else:
                        if not exists:
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
