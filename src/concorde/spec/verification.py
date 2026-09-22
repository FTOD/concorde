"""Scenario verification declared by tests, never by Specs.

A test names the scenario it verifies with the ``verifies`` decorator in Python, or with a
``// verifies:`` comment above the test in TypeScript. The scanner reads those declarations from
the test files a Module's realizations bind without importing, compiling or executing them, so a
deterministic check can report which tests verify each scenario and which scenarios no test
declares. The Spec side stays free of test locations: the Protocol fixes only the direction of the
declaration and the scenario identity it names, leaving each language's syntax to this tool.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, TypeVar

from .typed_data import checked_path

DECORATOR = "verifies"
ATTRIBUTE = "concorde_scenarios"
TYPESCRIPT_SUFFIXES = (".ts", ".tsx", ".mts", ".cts")
# One own-line comment declares the scenarios of the test call that follows it.
TYPESCRIPT_DECLARATION = re.compile(r"^\s*//\s*verifies:(?P<ids>.*)$")
TYPESCRIPT_CALL = re.compile(r"\b(?:it|test|describe)(?:\.[A-Za-z_$][\w$]*)*\s*\(")
TYPESCRIPT_TABLE_END = re.compile(r"\)\s*\(")
TYPESCRIPT_STRING = re.compile(r"""(['"`])((?:\\.|(?!\1).)*)\1""")
F = TypeVar("F", bound=Callable)


def verifies(*scenario_ids: str) -> Callable[[F], F]:
    """Declare the scenario IDs a test verifies; the test itself is returned unchanged."""
    if not scenario_ids or any(
        not isinstance(item, str) or not item.startswith("scenario.")
        for item in scenario_ids
    ):
        raise ValueError(
            "verifies() takes one or more scenario IDs beginning with 'scenario.'"
        )

    def decorate(function: F) -> F:
        declared = tuple(getattr(function, ATTRIBUTE, ())) + tuple(scenario_ids)
        setattr(function, ATTRIBUTE, declared)
        return function

    return decorate


@dataclass(frozen=True)
class Verification:
    """One declaration: the test at ``path``:``line`` named ``name`` verifies ``scenario_id``."""

    scenario_id: str
    path: str
    line: int
    name: str


class DeclarationError(ValueError):
    """A listed test file cannot be read for declarations, or a declaration is malformed."""

    def __init__(self, path: str, line: int | None, message: str):
        self.path, self.line = path, line
        super().__init__(f"{path}:{line}: {message}" if line else f"{path}: {message}")


def _decorator_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _declarations(path: str, tree: ast.AST) -> list[Verification]:
    result: list[Verification] = []
    qualified: list[str] = []

    def visit(node: ast.AST) -> None:
        if isinstance(node, ast.ClassDef):
            qualified.append(node.name)
            for child in node.body:
                visit(child)
            qualified.pop()
            return
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = ".".join((*qualified, node.name))
            for decorator in node.decorator_list:
                if _decorator_name(decorator) != DECORATOR:
                    continue
                if (
                    not isinstance(decorator, ast.Call)
                    or not decorator.args
                    or decorator.keywords
                ):
                    raise DeclarationError(
                        path,
                        decorator.lineno,
                        "verifies() takes scenario ID string literals",
                    )
                for argument in decorator.args:
                    if not isinstance(argument, ast.Constant) or not isinstance(
                        argument.value, str
                    ):
                        raise DeclarationError(
                            path,
                            decorator.lineno,
                            "verifies() takes scenario ID string literals",
                        )
                    if not argument.value.startswith("scenario."):
                        raise DeclarationError(
                            path,
                            decorator.lineno,
                            f"not a scenario ID: {argument.value!r}",
                        )
                    result.append(
                        Verification(argument.value, path, decorator.lineno, name)
                    )
            # A function nested inside another function is a helper, never a test.
            return
        for child in ast.iter_child_nodes(node):
            visit(child)

    visit(tree)
    return result


def _typescript_title(lines: list[str], start: int) -> str | None:
    """The title of the first ``it``, ``test`` or ``describe`` call at or after ``lines[start]``.

    The title is the first string literal of the call, which a table-driven ``.each`` form writes
    after its table instead, and which either form may put on a later line than the opening
    parenthesis. The search stops at the next declaration, which belongs to another test.
    """
    for index in range(start, len(lines)):
        if TYPESCRIPT_DECLARATION.match(lines[index]):
            return None
        call = TYPESCRIPT_CALL.search(lines[index])
        if call is None:
            continue
        position, line = call.end(), index
        if ".each(" in call.group():
            while TYPESCRIPT_TABLE_END.search(lines[line], position) is None:
                line, position = line + 1, 0
                if line >= len(lines) or TYPESCRIPT_DECLARATION.match(lines[line]):
                    return lines[index].strip()
            position = TYPESCRIPT_TABLE_END.search(lines[line], position).end()
        literal = TYPESCRIPT_STRING.search(lines[line], position)
        while literal is None:
            line += 1
            if line >= len(lines) or TYPESCRIPT_DECLARATION.match(lines[line]):
                return lines[index].strip()
            literal = TYPESCRIPT_STRING.search(lines[line])
        return literal.group(2)
    return None


def _typescript_declarations(path: str, text: str) -> list[Verification]:
    """Read ``// verifies: <ids>`` comments, each naming the scenarios of the following test.

    TypeScript is read line by line rather than compiled: an own-line comment declares one or
    more scenario IDs, separated by commas or spaces, for the next ``it``, ``test`` or ``describe``
    call, whose title names the declaring test. A declaration that no test follows, and an
    argument that is not a scenario ID, are malformed.
    """
    result: list[Verification] = []
    lines = text.splitlines()
    for number, line in enumerate(lines, 1):
        declaration = TYPESCRIPT_DECLARATION.match(line)
        if declaration is None:
            continue
        identities = [
            item
            for item in re.split(r"[,\s]+", declaration.group("ids").strip())
            if item
        ]
        if not identities:
            raise DeclarationError(
                path, number, "verifies: takes one or more scenario IDs"
            )
        for identity in identities:
            if not identity.startswith("scenario."):
                raise DeclarationError(path, number, f"not a scenario ID: {identity!r}")
        name = _typescript_title(lines, number)
        if name is None:
            raise DeclarationError(path, number, "verifies: comment declares no test")
        result.extend(
            Verification(identity, path, number, name) for identity in identities
        )
    return result


def scan_declarations(root: Path, paths) -> tuple[Verification, ...]:
    """Every ``verifies`` declaration in the given project-relative test files, in path order.

    Files are read, never imported, compiled or executed. Python declarations are read from
    module-level functions and from the methods of classes at any nesting of classes; a function
    nested inside another function is a helper and is not scanned. TypeScript declarations are
    read from own-line ``// verifies:`` comments above a test call. A file in another language is
    skipped; a Python file that cannot be parsed raises DeclarationError, because its declarations
    cannot be known.
    """
    result: list[Verification] = []
    for relative in sorted(set(paths)):
        typescript = relative.endswith(TYPESCRIPT_SUFFIXES)
        if not relative.endswith(".py") and not typescript:
            continue
        target = checked_path(root, relative)
        if target.is_symlink() or not target.is_file():
            continue
        if typescript:
            result.extend(
                _typescript_declarations(
                    relative, target.read_text(encoding="utf-8", errors="replace")
                )
            )
            continue
        try:
            tree = ast.parse(target.read_bytes(), filename=relative)
        except (SyntaxError, ValueError) as error:
            raise DeclarationError(
                relative,
                getattr(error, "lineno", None),
                f"cannot parse Python source: {error.msg if hasattr(error, 'msg') else error}",
            ) from error
        result.extend(_declarations(relative, tree))
    return tuple(result)
