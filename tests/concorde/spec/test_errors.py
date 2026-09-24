"""Spec tooling's own error type: registered codes, detailed records, and no Framework imports."""

from __future__ import annotations

import ast
import json
import tempfile
import unittest
from pathlib import Path

from concorde.spec.errors import CODES, ERROR_SCHEMA, SpecError, system_cause
from concorde.spec.repository import SpecRepository
from concorde.spec.schema import admit, validate
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.spec_project import PACKAGE, SpecProject, write_json

SOURCE = REPOSITORY_ROOT / "src/concorde"
# The packages of Spec tooling's Modules: Spec core, the Spec MCP server and Views.
SPEC_TOOLING = ("spec", "spec_mcp", "views")
# Error classes whose first positional argument is the code, and the rest whose second is.
CODE_FIRST = {"TypedDataError", "ToolError"}
ERROR_CLASSES = {"SpecError", "TypedDataError", "ToolError", "CheckError", "IssueError"}


def literal_codes(path: Path) -> set[str]:
    """Every literal code a file passes to a Spec tooling error class or its subclass."""
    codes = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if name not in ERROR_CLASSES:
            continue
        position = 0 if name in CODE_FIRST else 1
        argument = next(
            (item.value for item in node.keywords if item.arg == "code"),
            node.args[position] if len(node.args) > position else None,
        )
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
            codes.add(argument.value)
    return codes


def spec_tooling_files():
    for package in SPEC_TOOLING:
        yield from sorted((SOURCE / package).glob("*.py"))


class SpecErrorTests(unittest.TestCase):
    @verifies("scenario.spec.error-registered")
    def test_every_code_spec_tooling_raises_has_a_reason_and_a_remedy(self):
        used = set().union(*(literal_codes(path) for path in spec_tooling_files()))
        self.assertTrue(used)
        self.assertEqual(set(), used - CODES.keys(), "unregistered Spec tooling codes")
        for code, (reason, remediation) in CODES.items():
            self.assertTrue(reason.strip() and remediation.strip(), code)

    def test_other_modules_register_the_codes_of_their_own_subclasses(self):
        from concorde.harness.checks import CheckError
        from concorde.issues.store import IssueError

        for error_class, path in (
            (CheckError, SOURCE / "harness/checks.py"),
            (IssueError, SOURCE / "issues/store.py"),
        ):
            unregistered = literal_codes(path) - error_class.CODES.keys() - CODES.keys()
            self.assertEqual(set(), unregistered, path.name)

    @verifies("scenario.spec.error-independent")
    def test_spec_tooling_imports_no_framework_error_type(self):
        forbidden = (
            "concorde.errors",
            "concorde.harness",
            "concorde.operations",
            "concorde.tasks",
        )
        for path in spec_tooling_files():
            package = "concorde." + path.parent.name
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.ImportFrom):
                    base = package.rsplit(".", node.level - 1)[0] if node.level else ""
                    name = (base + "." if base and node.module else base) + (
                        node.module or ""
                    )
                    names = [name] + [f"{name}.{alias.name}" for alias in node.names]
                elif isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                else:
                    continue
                for name in names:
                    self.assertFalse(
                        name.startswith(forbidden),
                        f"{path.relative_to(REPOSITORY_ROOT)} imports {name}",
                    )

    def test_a_record_carries_location_reason_remediation_and_causes(self):
        admit(ERROR_SCHEMA)
        cause = system_cause(FileNotFoundError(2, "No such file", "specs/a.md"))
        error = SpecError(
            "the entry of module.a cannot be read",
            "missing_source",
            path="specs/a/module.md.json",
            subject="module.a",
            causes=[cause],
        )
        record = error.record()
        validate(record, ERROR_SCHEMA)
        self.assertEqual("specs/a/module.md.json", record["location"]["path"])
        self.assertEqual(CODES["missing_source"][0], record["reason"])
        self.assertEqual("system_error", record["causes"][0]["code"])
        self.assertEqual("specs/a.md", record["causes"][0]["location"]["path"])
        text = error.describe()
        for fragment in (
            "missing_source:",
            "at specs/a/module.md.json",
            "why:",
            "to fix:",
            "caused by:",
        ):
            self.assertIn(fragment, text)

    @verifies("scenario.spec.error-contract")
    def test_the_record_schema_and_codes_are_the_contract(self):
        text = (
            REPOSITORY_ROOT / "specs/concorde/spec-tooling/spec/errors.md"
        ).read_text()
        fence = text.split("```concorde-contract\n", 1)[1].split("```", 1)[0]
        self.assertEqual(ERROR_SCHEMA, json.loads(fence)["schema"])
        table = {
            line.split("|")[1].strip().strip("`"): (
                line.split("|")[2].strip(),
                line.split("|")[3].strip(),
            )
            for line in text.split("## Codes", 1)[1].splitlines()
            if line.startswith("| `")
        }
        self.assertEqual(CODES, table)


class LoadingTests(unittest.TestCase):
    @verifies("scenario.spec.error-every-cause")
    def test_a_refused_load_names_every_fatal_problem(self):
        with tempfile.TemporaryDirectory() as directory:
            project = SpecProject(directory)
            write_json(
                project.root,
                ".concorde/specs.json",
                {
                    "schema_version": 3,
                    "modules": [
                        {
                            "id": f"module.{name}",
                            "title": name.upper(),
                            "entry": f"specs/{name}/module.md",
                            "owns": [f"specs/{name}/module.md"],
                            "contains": [],
                            "uses": [],
                            "includes": [],
                            "participates": [],
                        }
                        for name in ("a", "b")
                    ],
                },
            )
            with self.assertRaises(SpecError) as raised:
                SpecRepository(project.root, PACKAGE)
        error = raised.exception
        validate(error.record(), ERROR_SCHEMA)
        self.assertEqual(6, len(error.causes), error.describe())
        self.assertIn("6 fatal problem(s)", str(error))
        paths = {cause.path for cause in error.causes}
        self.assertEqual(
            {
                f"specs/{name}/module.md{suffix}"
                for name in "ab"
                for suffix in ("", ".json")
            },
            paths,
        )
        self.assertTrue(
            all(
                "CHK.document.pair requires: Both members exist" in cause.reason
                for cause in error.causes
            )
        )


if __name__ == "__main__":
    unittest.main()
