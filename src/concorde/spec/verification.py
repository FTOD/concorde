"""Scenario verification declared by tests, never by Specs.

A test names the scenario it verifies with the ``verifies`` decorator. The scanner reads those
declarations from the Python files a Module's entities bind without importing or executing them,
so a deterministic check can report which tests verify each scenario and which scenarios no test
declares. The Spec side stays free of test locations: the Protocol fixes only the direction of the
declaration and the scenario identity it names.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, TypeVar

from .typed_data import checked_path

DECORATOR = "verifies"
ATTRIBUTE = "concorde_scenarios"
F = TypeVar("F", bound=Callable)


def verifies(*scenario_ids: str) -> Callable[[F], F]:
    """Declare the scenario IDs a test verifies; the test itself is returned unchanged."""
    if not scenario_ids or any(not isinstance(item, str) or not item.startswith("scenario.") for item in scenario_ids):
        raise ValueError("verifies() takes one or more scenario IDs beginning with 'scenario.'")

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
    """A listed Python file cannot be read for declarations, or a declaration is malformed."""

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
                if not isinstance(decorator, ast.Call) or not decorator.args or decorator.keywords:
                    raise DeclarationError(path, decorator.lineno, "verifies() takes scenario ID string literals")
                for argument in decorator.args:
                    if not isinstance(argument, ast.Constant) or not isinstance(argument.value, str):
                        raise DeclarationError(path, decorator.lineno, "verifies() takes scenario ID string literals")
                    if not argument.value.startswith("scenario."):
                        raise DeclarationError(path, decorator.lineno, f"not a scenario ID: {argument.value!r}")
                    result.append(Verification(argument.value, path, decorator.lineno, name))
            # A function nested inside another function is a helper, never a test.
            return
        for child in ast.iter_child_nodes(node):
            visit(child)

    visit(tree)
    return result


def scan_declarations(root: Path, paths) -> tuple[Verification, ...]:
    """Every ``verifies`` declaration in the given project-relative Python files, in path order.

    Files are parsed, not imported. Declarations are read from module-level functions and from
    the methods of classes at any nesting of classes; a function nested inside another function
    is a helper and is not scanned. A file that is not Python is skipped; a Python file that
    cannot be parsed raises DeclarationError, because its declarations cannot be known.
    """
    result: list[Verification] = []
    for relative in sorted(set(paths)):
        if not relative.endswith(".py"):
            continue
        target = checked_path(root, relative)
        if target.is_symlink() or not target.is_file():
            continue
        try:
            tree = ast.parse(target.read_bytes(), filename=relative)
        except (SyntaxError, ValueError) as error:
            raise DeclarationError(relative, getattr(error, "lineno", None), f"cannot parse Python source: {error.msg if hasattr(error, 'msg') else error}") from error
        result.extend(_declarations(relative, tree))
    return tuple(result)
