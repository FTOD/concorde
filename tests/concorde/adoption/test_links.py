"""Linking existing tests to scenarios: only decorators and the no-op helper are added."""

from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path

from concorde.adoption.test_links import link_file
from concorde.spec.verification import scan_declarations
from concorde.spec.verification import verifies

SOURCE = """\"\"\"Tests of the calculator.\"\"\"

from __future__ import annotations

import pytest


class TestAdd:
    @pytest.mark.slow
    def test_small(self):
        assert 1 + 1 == 2


def test_other():
    pass
"""


class LinkFileTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "tests").mkdir()
        self.path = self.root / "tests/test_calc.py"
        self.path.write_text(SOURCE)

    @verifies("scenario.adoption.tests-linked")
    def test_only_decorators_and_the_helper_are_added(self):
        linked, undone = link_file(
            self.path,
            "tests/test_calc.py",
            [
                ("scenario.calc.add", "TestAdd.test_small"),
                ("scenario.calc.other", "test_other"),
                ("scenario.calc.none", "TestAdd.test_gone"),
            ],
        )
        self.assertEqual(
            [
                ("scenario.calc.add", "TestAdd.test_small"),
                ("scenario.calc.other", "test_other"),
            ],
            linked,
        )
        self.assertEqual(
            [("scenario.calc.none", "TestAdd.test_gone")], [u[0] for u in undone]
        )
        changed = self.path.read_text()
        added = [
            line
            for line in changed.splitlines()
            if line not in SOURCE.splitlines() and line.strip()
        ]
        self.assertEqual(
            [
                "def verifies(*scenarios):  # Concorde: names the scenarios a test verifies",
                "    return lambda test: test",
                '    @verifies("scenario.calc.add")',
                '@verifies("scenario.calc.other")',
            ],
            added,
        )
        # The helper comes after the docstring and the imports, above the first use.
        tree = ast.parse(changed)
        names = [type(node).__name__ for node in tree.body]
        self.assertEqual(["Expr", "ImportFrom", "Import", "FunctionDef"], names[:4])
        self.assertEqual(
            {
                ("scenario.calc.add", "TestAdd.test_small"),
                ("scenario.calc.other", "test_other"),
            },
            {
                (item.scenario_id, item.name)
                for item in scan_declarations(self.root, ["tests/test_calc.py"])
            },
        )
        self.assertNotIn("\n\n\n\n", changed)
        self.assertIn("import pytest\n\n\ndef verifies(", changed)
        self.assertIn("return lambda test: test\n\n\nclass TestAdd:", changed)
        # Linking again adds nothing.
        link_file(
            self.path,
            "tests/test_calc.py",
            [("scenario.calc.add", "TestAdd.test_small")],
        )
        self.assertEqual(changed, self.path.read_text())


if __name__ == "__main__":
    unittest.main()
