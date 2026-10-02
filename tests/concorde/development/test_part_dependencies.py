"""Every part imports only the parts it depends on (req.concorde.part-dependencies).

Each part's code is one directory of ``src/concorde/``. The allowed directions are read from the
root's parts table; every ``concorde.*`` import of ``src/concorde/`` (module-level and
function-level, absolute and relative, and the ``"module:attribute"`` strings a catalog imports
by name) is checked against them. Today's violations are listed below as known exceptions, each
under the later code task expected to remove it; the check fails on an import neither allowed nor
listed, and on a listed exception that no longer occurs, so the list can only shrink.
"""

from __future__ import annotations

import ast
import re
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT

SOURCE = REPOSITORY_ROOT / "src"
PACKAGE = SOURCE / "concorde"
PARTS_TABLE = REPOSITORY_ROOT / "specs/concorde/module.md"

# Part (as the root's parts table names it) -> its directory under src/concorde/.
PART_DIRECTORIES = {
    "spec": "spec",
    "kernel": "kernel",
    "worker harness": "worker_harness",
    "execution": "execution",
    "workflow": "workflows",
    "issues": "issues",
    "coordination": "coordination",
    "method": "method",
    "distribution": "distribution",
}
# Code under src/concorde/ that is no part: it depends on no part and no part depends on it.
NOT_PARTS = {"dogfooding": "Dogfooding, a developer Module"}
# Files at the package root: `python -m concorde` is Distribution's command; the package marker
# belongs to no part.
ROOT_FILES = {"__main__.py": "distribution", "__init__.py": None}
# Reliances outside the table that are optional integrations.
OPTIONAL_INTEGRATIONS = {("method", "issues")}

# The later code tasks, in their order.
CODE_TASKS = (
    "issues",
    "worker harness",
    "execution",
    "workflow",
    "method",
    "coordination",
    "distribution",
)
# Code task -> (importing file under src/concorde/, imported module under concorde.) it removes.
KNOWN_EXCEPTIONS = {
    "issues": [
        ("issues/command.py", "spec.repository"),
        ("issues/store.py", "coordination.tasks.store"),
        ("issues/store.py", "spec.repository"),
    ],
    "execution": [
        ("execution/checks/checks.py", "spec.repository"),
        ("execution/checks/checks.py", "spec.repository_base"),
        ("execution/checks/checks.py", "spec.verification"),
        ("execution/commands/catalog.py", "method.delivery.command"),
        ("execution/commands/catalog.py", "method.scaffold.command"),
        ("execution/commands/catalog.py", "method.validation.command"),
        ("execution/context.py", "spec.errors"),
        ("execution/operations/catalog.py", "method.adoption.code_to_spec"),
        ("execution/operations/catalog.py", "method.adoption.survey"),
        ("execution/operations/catalog.py", "method.code_review.operation"),
        ("execution/operations/catalog.py", "method.implementation.operation"),
        ("execution/operations/catalog.py", "method.spec_review.operation"),
        ("execution/operations/catalog.py", "method.spec_review.panel"),
        ("execution/operations/catalog.py", "method.specification.operation"),
        ("execution/operations/catalog.py", "method.understanding.operation"),
        ("execution/operations/catalog.py", "method.understanding.plan_review"),
        ("execution/operations/review_issues.py", "issues.command"),
        ("execution/operations/review_issues.py", "issues.store"),
        ("execution/runner.py", "spec.repository"),
        ("execution/runner.py", "spec.repository_base"),
    ],
    "coordination": [
        ("coordination/tasks/cli.py", "execution.runs"),
        ("coordination/tasks/merge.py", "issues.store"),
        ("coordination/tasks/session.py", "issues.store"),
        ("coordination/tasks/store.py", "execution.runs"),
        ("coordination/tasks/store.py", "issues.command"),
        ("coordination/tasks/store.py", "issues.store"),
        ("coordination/tasks/store.py", "spec.repository"),
        ("coordination/tasks/store.py", "spec.repository_base"),
    ],
    # Distribution depends on no part and no part imports it: it reaches the parts only through
    # their registrations.
    "distribution": [
        ("coordination/tasks/merge.py", "distribution.install"),
        ("distribution/build.py", "spec.typed_data"),
        ("distribution/build.py", "workflows.catalog"),
        ("distribution/cli.py", "coordination.tasks.cli"),
        ("distribution/cli.py", "execution.commands.catalog"),
        ("distribution/cli.py", "execution.runner"),
        ("distribution/cli.py", "kernel.tracing.command"),
        ("distribution/cli.py", "spec.diagnostics"),
        ("distribution/cli.py", "spec.errors"),
        ("distribution/cli.py", "spec.grants"),
        ("distribution/cli.py", "spec.initialize"),
        ("distribution/cli.py", "spec.mcp.server"),
        ("distribution/cli.py", "spec.model"),
        ("distribution/cli.py", "spec.registry"),
        ("distribution/cli.py", "spec.repository"),
        ("distribution/cli.py", "spec.validation"),
        ("distribution/cli.py", "spec.views.docsite_scaffold"),
        ("distribution/cli.py", "workflows.cli"),
        ("distribution/install.py", "dogfooding.develop"),
        ("distribution/install.py", "kernel.errors"),
        ("distribution/install.py", "kernel.tracing.layout"),
        ("distribution/install.py", "kernel.tracing.locks"),
        ("distribution/install.py", "spec.errors"),
        ("distribution/install.py", "spec.initialize"),
        ("distribution/install.py", "spec.views.docsite_template"),
        ("distribution/project_defaults.py", "spec.repository"),
        ("distribution/project_defaults.py", "spec.typed_data"),
        ("distribution/project_mcp/calls.py", "kernel.errors"),
        ("distribution/project_mcp/server.py", "coordination.tasks.store"),
        ("distribution/project_mcp/server.py", "kernel.errors"),
        ("distribution/project_mcp/tools.py", "coordination.tasks.cli"),
        ("distribution/project_mcp/tools.py", "coordination.tasks.merge"),
        ("distribution/project_mcp/tools.py", "coordination.tasks.store"),
        ("distribution/project_mcp/tools.py", "coordination.tasks.wait"),
        ("distribution/project_mcp/tools.py", "issues.command"),
        ("distribution/project_mcp/tools.py", "kernel.errors"),
        ("distribution/project_mcp/tools.py", "kernel.binding"),
        ("distribution/project_mcp/tools.py", "kernel.refusal"),
        ("distribution/project_mcp/tools.py", "kernel.tracing.layout"),
        ("distribution/project_mcp/tools.py", "kernel.tracing.locks"),
        ("distribution/project_mcp/tools.py", "kernel.tracing.reader"),
        ("distribution/project_mcp/tools.py", "spec.schema"),
        ("distribution/project_mcp/tools.py", "workflows.step"),
        ("distribution/prompt_resolver.py", "spec.frontmatter"),
    ],
}

CATALOG_ENTRY = re.compile(r"concorde(?:\.\w+)+(?::\w+)?")


def parts_table() -> dict[str, set[str]]:
    """Each part of the root's parts table with the parts it depends on."""
    text = PARTS_TABLE.read_text(encoding="utf-8")
    section = text.split("\n### The parts\n", 1)[1].split("\n#", 1)[0]
    table = {}
    for line in section.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4 or cells[0] in ("Part", "") or set(cells[0]) <= {"-", " "}:
            continue
        depends = cells[3].split(":", 1)[0].strip()
        table[cells[0]] = (
            set()
            if depends == "nothing"
            else {name.strip() for name in depends.split(",")}
        )
    return table


def owner(path) -> str | None:
    """The part, or the code that is no part, a file of src/concorde/ belongs to."""
    relative = path.relative_to(PACKAGE).parts
    if len(relative) == 1:
        if relative[0] not in ROOT_FILES:
            raise AssertionError(f"src/concorde/{relative[0]} belongs to no part")
        return ROOT_FILES[relative[0]]
    for part, directory in PART_DIRECTORIES.items():
        if relative[0] == directory:
            return part
    if relative[0] in NOT_PARTS:
        return relative[0]
    raise AssertionError(f"src/concorde/{relative[0]}/ is the directory of no part")


def module_file(name: str):
    """The file of the module or package ``name``, or None when it is not Concorde's code."""
    path = SOURCE.joinpath(*name.split("."))
    if path.with_suffix(".py").is_file():
        return path.with_suffix(".py")
    if path.is_dir():
        return path / "__init__.py"
    return None


def imported_modules(path):
    """Every ``concorde.*`` module the file imports, each with the line of its import."""
    relative = path.relative_to(SOURCE).with_suffix("").parts
    package = relative[:-1]
    found = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom):
            if node.level:
                if node.level > len(package):
                    raise AssertionError(
                        f"{path}:{node.lineno} imports beyond the package"
                    )
                base = ".".join(
                    [
                        *package[: len(package) - node.level + 1],
                        *filter(None, [node.module]),
                    ]
                )
            else:
                base = node.module or ""
            if base.split(".")[0] != "concorde":
                continue
            for alias in node.names:
                full = f"{base}.{alias.name}"
                found.append((full if module_file(full) else base, node.lineno))
        elif isinstance(node, ast.Import):
            found += [
                (alias.name, node.lineno)
                for alias in node.names
                if alias.name.split(".")[0] == "concorde"
            ]
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if CATALOG_ENTRY.fullmatch(node.value):
                name = node.value.split(":")[0]
                if module_file(name):
                    found.append((name, node.lineno))
    return found


def violations() -> dict[tuple[str, str], list[str]]:
    """Each import of a part that its part may not rely on, with where it occurs."""
    allowed = parts_table()
    found: dict[tuple[str, str], list[str]] = {}
    for path in sorted(PACKAGE.rglob("*.py")):
        source = owner(path)
        for name, line in imported_modules(path):
            target = module_file(name)
            if target is None:
                raise AssertionError(
                    f"{path}:{line} imports {name}, which does not exist"
                )
            imported = owner(target)
            if imported == source:
                continue
            if source in allowed and (
                imported in allowed[source]
                or (source, imported) in OPTIONAL_INTEGRATIONS
            ):
                continue
            key = (path.relative_to(PACKAGE).as_posix(), name.removeprefix("concorde."))
            found.setdefault(key, []).append(
                f"src/concorde/{key[0]}:{line} ({source} -> {imported})"
            )
    return found


class PartDependencyTests(unittest.TestCase):
    def test_the_parts_table_names_the_part_directories(self):
        self.assertEqual(set(PART_DIRECTORIES), set(parts_table()))

    def test_every_file_belongs_to_a_part_or_is_named(self):
        for path in PACKAGE.rglob("*.py"):
            owner(path)

    def test_exceptions_name_a_later_code_task_once(self):
        self.assertLessEqual(set(KNOWN_EXCEPTIONS), set(CODE_TASKS))
        listed = [entry for entries in KNOWN_EXCEPTIONS.values() for entry in entries]
        self.assertEqual(len(listed), len(set(listed)), "an exception is listed twice")

    def test_every_import_follows_the_part_dependencies(self):
        found = violations()
        listed = {entry for entries in KNOWN_EXCEPTIONS.values() for entry in entries}
        unexpected = sorted(
            where for key in found.keys() - listed for where in found[key]
        )
        self.assertEqual(
            [],
            unexpected,
            "imports a part may not rely on: depend only on the parts the root's parts table "
            "lists, or reach another part through an optional integration",
        )
        gone = sorted(f"{file} -> {module}" for file, module in listed - found.keys())
        self.assertEqual(
            [],
            gone,
            "known exceptions that no longer occur: remove them from KNOWN_EXCEPTIONS",
        )


if __name__ == "__main__":
    unittest.main()
