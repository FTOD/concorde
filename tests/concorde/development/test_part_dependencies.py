"""Every part imports only the parts it depends on (req.concorde.part-dependencies), and
reaches Distribution only through its registration (req.distribution.registration-only).

Each part's code is one directory of ``src/concorde/``. The allowed directions are read from the
root's parts table; every ``concorde.*`` import of ``src/concorde/`` (module-level and
function-level, absolute and relative, and the ``"module:attribute"`` strings a catalog imports
by name) is checked against them, with no exception. Each part's registration names the part and
the dependencies the table gives it, and every entry it names lies in the part's own directory, so
that Distribution, which imports a part's code only through those entries, never reaches one part's
code through another's registration.
"""

from __future__ import annotations

import ast
import importlib
import json
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
# Reliances outside the table that are optional integrations: none imports code, each reaches the
# other part only through its command or a file format its Spec defines.
OPTIONAL_INTEGRATIONS: set[tuple[str, str]] = set()

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

    def test_every_import_follows_the_part_dependencies(self):
        found = violations()
        self.assertEqual(
            [],
            sorted(where for places in found.values() for where in places),
            "imports a part may not rely on: depend only on the parts the root's parts table "
            "lists, or reach another part through an optional integration",
        )

    def test_every_part_registers_itself_with_its_dependencies(self):
        table = parts_table()
        for part, directory in PART_DIRECTORIES.items():
            with self.subTest(part=part):
                path = PACKAGE / directory / "registration.json"
                registration = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(part, registration["part"])
                self.assertEqual(table[part], set(registration["depends_on"]))
        for directory in NOT_PARTS:
            self.assertFalse((PACKAGE / directory / "registration.json").exists())

    def test_every_registration_entry_lies_in_its_own_part(self):
        for part, directory in PART_DIRECTORIES.items():
            registration = json.loads(
                (PACKAGE / directory / "registration.json").read_text(encoding="utf-8")
            )
            install = registration["install"]
            entries = [
                *(item["entry"] for item in registration["commands"]),
                *(item["entry"] for item in registration["mcp_tools"]),
                *(
                    registration[field]
                    for field in (
                        "mcp_definitions",
                        "renders",
                        "idle_check",
                        "after_update",
                    )
                ),
                install["prepare"],
                install["bind"],
            ]
            modules = [*registration["loads"]] + [
                entry.split(":", 1)[0] for entry in entries if entry is not None
            ]
            for module in modules:
                with self.subTest(part=part, module=module):
                    self.assertFalse(module.startswith("."), "an entry leaves its part")
                    target = module_file(f"concorde.{directory}.{module}")
                    self.assertIsNotNone(
                        target, f"{module} is no module of the {part} part"
                    )
                    self.assertEqual(part, owner(target))
            for entry in entries:
                if entry is None:
                    continue
                with self.subTest(part=part, entry=entry):
                    module, attribute = entry.split(":", 1)
                    loaded = importlib.import_module(f"concorde.{directory}.{module}")
                    self.assertTrue(
                        hasattr(loaded, attribute), f"{entry} names nothing"
                    )


if __name__ == "__main__":
    unittest.main()
