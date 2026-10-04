"""Linking existing tests to scenarios: only decorators and the no-op helper are added."""

from __future__ import annotations

import ast
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from concorde.method.adoption import test_links
from concorde.method.adoption.test_links import link_file, link_tests
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

    @verifies("scenario.adoption.foreign-verifies")
    def test_a_file_with_its_own_verifies_stays_as_it_is(self):
        link = [("scenario.calc.other", "test_other")]
        for binding, line in (
            ("from tests.support import verifies\n", 6),
            ("verifies = pytest.mark.verifies\n", 6),
            (
                "try:\n    from tests.support import check as verifies\n"
                "except ImportError:\n    pass\n",
                7,
            ),
            ("import concorde.spec.verification as verifies\n", 6),
        ):
            with self.subTest(binding=binding):
                source = SOURCE.replace("import pytest\n", f"import pytest\n{binding}")
                self.path.write_text(source)
                linked, undone = link_file(self.path, "tests/test_calc.py", link)
                self.assertEqual([], linked)
                self.assertEqual(link, [item[0] for item in undone])
                self.assertIn(f"binds verifies at line {line} ", undone[0][1])
                self.assertEqual(source, self.path.read_text())
        # Concorde's own helper, however formatted, and its decorator are kept and used.
        for binding in (
            'def verifies(*ids):\n    """No-op."""\n    return lambda f: f\n',
            "from concorde.spec.verification import scan_declarations, verifies\n",
        ):
            with self.subTest(binding=binding):
                source = SOURCE.replace("import pytest\n", f"import pytest\n{binding}")
                self.path.write_text(source)
                linked, undone = link_file(self.path, "tests/test_calc.py", link)
                self.assertEqual((link, []), (linked, undone))
                self.assertEqual(
                    source.replace(
                        "def test_other",
                        '@verifies("scenario.calc.other")\ndef test_other',
                    ),
                    self.path.read_text(),
                )

    @verifies("scenario.adoption.tests-linked")
    def test_existing_bytes_line_endings_and_blank_lines_are_kept(self):
        source = (
            b'"""Tests."""\r\n'
            b"import pytest\r\n"
            b"\r\n"
            b"\r\n"
            b"\r\n"
            b"def test_other():\r\n"
            b"\tassert True  \r\n"
            b"\r\n"
            b"\r\n"
            b"\r\n"
            b"\r\n"
            b"class TestAdd:\r\n"
            b"\tdef test_small(self):\r\n"
            b"\t\tpass\r\n"
        )
        self.path.write_bytes(source)
        linked, undone = link_file(
            self.path,
            "tests/test_calc.py",
            [
                ("scenario.calc.other", "test_other"),
                ("scenario.calc.add", "TestAdd.test_small"),
            ],
        )
        self.assertEqual(([], 2), (undone, len(linked)))
        changed = self.path.read_bytes()
        # Only the helper and the decorators were inserted, in the file's own line endings and
        # indentation; every byte that was there is there still, in order.
        self.assertEqual(
            source.replace(
                b"def test_other",
                b"def verifies(*scenarios):  # Concorde: names the scenarios a test verifies"
                b"\r\n    return lambda test: test\r\n\r\n\r\n"
                b'@verifies("scenario.calc.other")\r\ndef test_other',
            ).replace(
                b"\tdef test_small",
                b'\t@verifies("scenario.calc.add")\r\n\tdef test_small',
            ),
            changed,
        )
        # One blank line after the imports gets a second one, and none is ever removed.
        self.path.write_bytes(b"import pytest\n\ndef test_other():\n    pass\n")
        link_file(
            self.path, "tests/test_calc.py", [("scenario.calc.other", "test_other")]
        )
        self.assertEqual(
            b"import pytest\n\n\n"
            + test_links.HELPER.encode()
            + b'\n\n@verifies("scenario.calc.other")\ndef test_other():\n    pass\n',
            self.path.read_bytes(),
        )
        # A file that begins with code keeps its interpreter line and encoding above the helper.
        self.path.write_bytes(
            b"#!/usr/bin/env python\n# -*- coding: utf-8 -*-\ndef test_other():\n    pass\n"
        )
        link_file(
            self.path, "tests/test_calc.py", [("scenario.calc.other", "test_other")]
        )
        self.assertTrue(
            self.path.read_bytes().startswith(
                b"#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n\n\ndef verifies("
            )
        )

    @verifies("scenario.adoption.tests-linked")
    def test_a_link_named_twice_adds_one_decorator(self):
        link = ("scenario.calc.other", "test_other")
        linked, undone = link_file(self.path, "tests/test_calc.py", [link, link])
        self.assertEqual(([link], []), (linked, undone))
        self.assertEqual(
            1, self.path.read_text().count('@verifies("scenario.calc.other")')
        )
        promise = {
            "id": "scenario.calc.other",
            "kind": "scenario",
            "tests": ["tests/test_calc.py::test_other"] * 2,
        }
        self.path.write_text(SOURCE)
        linked, unlinked = link_tests(
            self.root, [promise, promise], {"scenario.calc.other"}, lambda path: True
        )
        self.assertEqual(
            [
                {
                    "scenario": "scenario.calc.other",
                    "test": "tests/test_calc.py::test_other",
                }
            ],
            linked,
        )
        self.assertEqual([], unlinked)

    @verifies("scenario.adoption.foreign-verifies")
    def test_every_module_level_binding_of_verifies_is_found(self):
        link = [("scenario.calc.other", "test_other")]
        for binding, line in (
            ("for verifies in [pytest.mark.skip]:\n    pass\n", 6),
            ("with open(__file__) as verifies:\n    pass\n", 6),
            ("try:\n    pass\nexcept ImportError as verifies:\n    pass\n", 8),
            ("if (verifies := pytest.mark.skip):\n    pass\n", 6),
            ("PICKED = [(verifies := item) for item in [1]]\n", 6),
            ("match 1:\n    case verifies:\n        pass\n", 7),
            ("match {}:\n    case {**verifies}:\n        pass\n", 7),
            ("verifies, other = pytest.mark.skip, 1\n", 6),
        ):
            with self.subTest(binding=binding):
                source = SOURCE.replace("import pytest\n", f"import pytest\n{binding}")
                self.path.write_text(source)
                linked, undone = link_file(self.path, "tests/test_calc.py", link)
                self.assertEqual([], linked)
                self.assertIn(f"binds verifies at line {line} ", undone[0][1])
                self.assertEqual(source, self.path.read_text())
        # Names a comprehension, a lambda or a subscript uses bind nothing at module level.
        for harmless in (
            "NAMES = [verifies for verifies in [1]]\n",
            "PICK = lambda verifies: verifies\n",
            "TABLE = {}\nTABLE[verifies] = 1\n",
        ):
            with self.subTest(harmless=harmless):
                source = SOURCE.replace("import pytest\n", f"import pytest\n{harmless}")
                self.path.write_text(source)
                linked, undone = link_file(self.path, "tests/test_calc.py", link)
                self.assertEqual((link, []), (linked, undone))

    @verifies("scenario.adoption.tests-linked")
    def test_a_test_defined_under_a_condition_is_linked_once_it_is_unique(self):
        conditional = SOURCE.replace(
            "def test_other():\n    pass\n",
            "if True:\n    def test_other():\n        pass\n"
            "try:\n    import json\nexcept ImportError:\n    pass\nelse:\n"
            "    class TestJson:\n        if True:\n            def test_dump(self):\n"
            "                pass\n",
        )
        self.path.write_text(conditional)
        linked, undone = link_file(
            self.path,
            "tests/test_calc.py",
            [
                ("scenario.calc.other", "test_other"),
                ("scenario.calc.dump", "TestJson.test_dump"),
            ],
        )
        self.assertEqual(([], 2), (undone, len(linked)))
        changed = self.path.read_text()
        self.assertIn(
            '    @verifies("scenario.calc.other")\n    def test_other', changed
        )
        self.assertIn(
            '            @verifies("scenario.calc.dump")\n            def test_dump',
            changed,
        )
        self.assertEqual(
            {
                ("scenario.calc.other", "test_other"),
                ("scenario.calc.dump", "TestJson.test_dump"),
            },
            {
                (item.scenario_id, item.name)
                for item in scan_declarations(self.root, ["tests/test_calc.py"])
            },
        )
        # A test defined twice cannot be told apart: the link is reported, the file kept.
        twice = SOURCE.replace(
            "def test_other():\n    pass\n",
            "if True:\n    def test_other():\n        pass\nelse:\n"
            "    def test_other():\n        pass\n",
        )
        self.path.write_text(twice)
        linked, undone = link_file(
            self.path, "tests/test_calc.py", [("scenario.calc.other", "test_other")]
        )
        self.assertEqual([], linked)
        self.assertIn("defines test_other 2 times (lines 15, 18)", undone[0][1])
        self.assertEqual(twice, self.path.read_text())
        # A function inside a function is a helper, never a test.
        nested = SOURCE.replace(
            "def test_other():\n    pass\n",
            "def factory():\n    def test_inner():\n        pass\n",
        )
        self.path.write_text(nested)
        _, undone = link_file(
            self.path, "tests/test_calc.py", [("scenario.calc.other", "test_inner")]
        )
        self.assertEqual("tests/test_calc.py has no test test_inner", undone[0][1])

    @verifies("scenario.adoption.foreign-verifies")
    def test_a_helper_bound_after_the_test_is_no_use_to_it(self):
        link = [("scenario.calc.other", "test_other")]
        for source in (
            SOURCE + "\n\ndef verifies(*ids):\n    return lambda f: f\n",
            SOURCE.replace(
                "import pytest\n",
                "import pytest\nif pytest:\n"
                "    from concorde.spec.verification import verifies\n",
            ),
        ):
            with self.subTest(source=source):
                self.path.write_text(source)
                linked, undone = link_file(self.path, "tests/test_calc.py", link)
                self.assertEqual([], linked)
                self.assertIn(
                    "but not at its top level before test_other", undone[0][1]
                )
                self.assertEqual(source, self.path.read_text())

    @verifies("scenario.adoption.test-file-unwritable")
    def test_a_file_that_cannot_be_written_is_reported_and_the_next_is_linked(self):
        other = self.root / "tests/test_more.py"
        other.write_text(SOURCE)
        promises = [
            {
                "id": "scenario.calc.other",
                "kind": "scenario",
                "tests": [
                    "tests/test_calc.py::test_other",
                    "tests/test_calc.py::test_gone",
                    "tests/test_more.py::test_other",
                ],
            }
        ]
        real = os.replace

        def failing(source, destination):
            if Path(destination).name == "test_calc.py":
                raise OSError(28, "No space left on device")
            return real(source, destination)

        with mock.patch.object(test_links.os, "replace", side_effect=failing):
            linked, unlinked = link_tests(
                self.root, promises, {"scenario.calc.other"}, lambda path: True
            )
        self.assertEqual(
            [
                {
                    "scenario": "scenario.calc.other",
                    "test": "tests/test_more.py::test_other",
                }
            ],
            linked,
        )
        reasons = {item["test"]: item["reason"] for item in unlinked}
        self.assertEqual(
            {"tests/test_calc.py::test_other", "tests/test_calc.py::test_gone"},
            set(reasons),
        )
        self.assertIn(
            "could not be written and was left as it was",
            reasons["tests/test_calc.py::test_other"],
        )
        self.assertIn(
            "No space left on device", reasons["tests/test_calc.py::test_other"]
        )
        self.assertIn("has no test test_gone", reasons["tests/test_calc.py::test_gone"])
        # The file that could not be written is as it was, and no temporary file is left.
        self.assertEqual(SOURCE, self.path.read_text())
        self.assertEqual(
            ["test_calc.py", "test_more.py"],
            sorted(path.name for path in (self.root / "tests").iterdir()),
        )
        self.assertIn('@verifies("scenario.calc.other")', other.read_text())

    @unittest.skipIf(os.geteuid() == 0, "root writes a read-only file all the same")
    @verifies("scenario.adoption.test-file-unwritable")
    def test_a_read_only_test_file_is_reported(self):
        self.path.chmod(0o444)
        self.addCleanup(self.path.chmod, 0o644)
        linked, undone = link_file(
            self.path, "tests/test_calc.py", [("scenario.calc.other", "test_other")]
        )
        self.assertEqual([], linked)
        self.assertIn("could not be written", undone[0][1])
        self.assertEqual(SOURCE, self.path.read_text())


if __name__ == "__main__":
    unittest.main()
